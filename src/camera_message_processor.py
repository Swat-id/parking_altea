#!/usr/bin/env python3
"""
CameraMessageProcessor - Procesador de mensajes de cámaras con gestión total de concurrencia
Sistema optimizado para procesar mensajes simultáneos sin bloqueos

Características principales:
- Gestión completa de concurrencia con ThreadPoolExecutor
- Detección inteligente de reinicios de cámaras
- Validación reforzada de deltas con múltiples criterios
- Actualización atómica de ocupación para evitar condiciones de carrera
- Cache thread-safe para detección de duplicados
- Sistema de estadísticas integrado para monitoreo
"""

import time
import threading
import logging
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models import Access, Parking, CameraParking, OccupancyHistory
from config import DB_URL

# Configurar logging específico para el procesador
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de un mensaje"""
    status: str
    message_id: str
    processing_time_ms: float
    updated_parkings: List[Dict]
    reset_detected: bool
    error: Optional[str] = None
    validations: Optional[List[str]] = None


@dataclass
class ResetInfo:
    """Información sobre detección de reinicio de cámara"""
    is_reset: bool
    criteria_met: Dict[str, bool]
    confidence: float
    previous_in: int
    previous_out: int
    new_in: int
    new_out: int
    reason: str


@dataclass
class DeltaValidation:
    """Resultado de validación de deltas"""
    valid: bool
    delta_in: int
    delta_out: int
    validations: List[str]
    reason: str


class CameraMessageProcessor:
    """
    Procesador principal de mensajes de cámaras con gestión total de concurrencia
    """
    
    def __init__(self, max_workers: int = 10, cache_duration: int = 300):
        """
        Inicializar el procesador de mensajes
        
        Args:
            max_workers: Número máximo de workers para procesamiento concurrente
            cache_duration: Duración del cache de duplicados en segundos (default: 5min)
        """
        self.max_workers = max_workers
        self.cache_duration = cache_duration
        
        # Configuración de base de datos
        self.engine = create_engine(
            DB_URL, 
            pool_pre_ping=True, 
            pool_recycle=3600,
            pool_size=20,  # Pool más grande para concurrencia
            max_overflow=30
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # ThreadPoolExecutor para procesamiento concurrente
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Cache thread-safe para detección de duplicados
        self._message_cache: Dict[str, float] = {}
        self._cache_lock = threading.Lock()
        
        # Estadísticas de procesamiento thread-safe
        self._stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'duplicates_detected': 0,
            'resets_detected': 0,
            'concurrent_messages': 0,
            'processing_times': [],
            'errors': 0,
            'validations_failed': 0
        }
        self._stats_lock = threading.Lock()
        
        logger.info(f"CameraMessageProcessor inicializado - Workers: {max_workers}, Cache: {cache_duration}s")
    
    def process_message_async(self, message_data: Dict[str, Any]) -> Future[ProcessingResult]:
        """
        Procesar mensaje de forma asíncrona y no bloqueante
        
        Args:
            message_data: Datos del mensaje de cámara
            
        Returns:
            Future con el resultado del procesamiento
        """
        # Incrementar contador de mensajes concurrentes
        with self._stats_lock:
            self._stats['messages_received'] += 1
            self._stats['concurrent_messages'] += 1
        
        # Enviar a worker pool para procesamiento
        future = self.executor.submit(self._process_single_message, message_data)
        return future
    
    def _process_single_message(self, message_data: Dict[str, Any]) -> ProcessingResult:
        """
        Procesar un único mensaje con gestión completa de concurrencia
        
        Args:
            message_data: Datos del mensaje
            
        Returns:
            ProcessingResult con el resultado del procesamiento
        """
        start_time = time.time()
        message_id = self._generate_message_id(message_data)
        
        try:
            # 1. VALIDACIÓN Y DETECCIÓN DE DUPLICADOS
            if self._is_duplicate_message_threadsafe(message_data):
                with self._stats_lock:
                    self._stats['duplicates_detected'] += 1
                
                return ProcessingResult(
                    status='duplicate',
                    message_id=message_id,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    updated_parkings=[],
                    reset_detected=False,
                    error='Mensaje duplicado detectado'
                )
            
            # Crear sesión independiente para este hilo
            session = self.Session()
            
            try:
                # 2. BÚSQUEDA DE CÁMARAS CON VALIDACIÓN
                cameras = self._find_cameras_with_validation(session, message_data)
                if not cameras:
                    return ProcessingResult(
                        status='camera_not_found',
                        message_id=message_id,
                        processing_time_ms=(time.time() - start_time) * 1000,
                        updated_parkings=[],
                        reset_detected=False,
                        error=f"Cámara no encontrada: device={message_data.get('device')}, line={message_data.get('line')}"
                    )
                
                # 3. DETECCIÓN INTELIGENTE DE REINICIOS
                reset_info = self._detect_reset_intelligent(cameras[0], message_data)
                
                # 4. CÁLCULO Y VALIDACIÓN DE DELTAS
                delta_result = self._calculate_and_validate_deltas(
                    cameras[0], message_data, reset_info
                )
                
                if not delta_result.valid:
                    with self._stats_lock:
                        self._stats['validations_failed'] += 1
                    
                    logger.warning(f"Delta inválido para mensaje {message_id}: {delta_result.reason}")
                    
                    return ProcessingResult(
                        status='invalid_delta',
                        message_id=message_id,
                        processing_time_ms=(time.time() - start_time) * 1000,
                        updated_parkings=[],
                        reset_detected=reset_info.is_reset,
                        error=delta_result.reason,
                        validations=delta_result.validations
                    )
                
                # 5. ACTUALIZACIÓN ATÓMICA DE OCUPACIÓN
                updated_parkings = self._update_occupancy_atomic(
                    session, cameras, delta_result.delta_in, delta_result.delta_out, reset_info
                )
                
                # 6. ACTUALIZAR CONTADORES DE CÁMARAS
                self._update_camera_counters(session, cameras, message_data)
                
                # 7. LOG DE PROCESAMIENTO
                self._log_message_processing(session, message_data, delta_result, updated_parkings, reset_info)
                
                # COMMIT FINAL
                session.commit()
                
                # Actualizar estadísticas
                processing_time = (time.time() - start_time) * 1000
                with self._stats_lock:
                    self._stats['messages_processed'] += 1
                    self._stats['processing_times'].append(processing_time)
                    if reset_info.is_reset:
                        self._stats['resets_detected'] += 1
                
                logger.info(f"Mensaje procesado exitosamente en {processing_time:.2f}ms - ID: {message_id}")
                
                return ProcessingResult(
                    status='success',
                    message_id=message_id,
                    processing_time_ms=processing_time,
                    updated_parkings=updated_parkings,
                    reset_detected=reset_info.is_reset
                )
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error procesando mensaje {message_id}: {e}")
                
                with self._stats_lock:
                    self._stats['errors'] += 1
                
                return ProcessingResult(
                    status='error',
                    message_id=message_id,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    updated_parkings=[],
                    reset_detected=False,
                    error=str(e)
                )
            
            finally:
                session.close()
                
        finally:
            # Decrementar contador de mensajes concurrentes
            with self._stats_lock:
                self._stats['concurrent_messages'] -= 1
    
    def _generate_message_id(self, message_data: Dict[str, Any]) -> str:
        """Generar ID único para el mensaje"""
        device = message_data.get('device', 'unknown')
        line = message_data.get('line', 0)
        timestamp = int(time.time() * 1000)  # Milliseconds para unicidad
        return f"{device}_{line}_{timestamp}"
    
    def _is_duplicate_message_threadsafe(self, message_data: Dict[str, Any]) -> bool:
        """
        Verificar si un mensaje es duplicado de forma thread-safe
        
        Args:
            message_data: Datos del mensaje
            
        Returns:
            True si es duplicado, False si no
        """
        # Crear clave única para el mensaje
        device = message_data.get('device', '')
        line = message_data.get('line', 0)
        vehicle_in = message_data.get('vehicle_in', 0)
        vehicle_out = message_data.get('vehicle_out', 0)
        
        cache_key = f"{device}_{line}_{vehicle_in}_{vehicle_out}"
        current_time = time.time()
        
        with self._cache_lock:
            # Limpiar entradas antiguas del cache
            expired_keys = [
                key for key, timestamp in self._message_cache.items()
                if current_time - timestamp > self.cache_duration
            ]
            for key in expired_keys:
                del self._message_cache[key]
            
            # Verificar si ya existe este mensaje
            if cache_key in self._message_cache:
                logger.warning(f"Mensaje duplicado detectado: {cache_key}")
                return True
            
            # Registrar este mensaje en el cache
            self._message_cache[cache_key] = current_time
            return False
    
    def _find_cameras_with_validation(self, session: Session, message_data: Dict[str, Any]) -> List[Access]:
        """
        Buscar cámaras en la base de datos con validación
        
        Args:
            session: Sesión de base de datos
            message_data: Datos del mensaje
            
        Returns:
            Lista de objetos Access (cámaras) encontrados
        """
        device = message_data.get('device', '')
        line = message_data.get('line', 0)
        
        if not device:
            logger.error("Device name vacío en mensaje")
            return []
        
        try:
            # Buscar por name y line
            cameras = session.query(Access).filter(
                Access.name == device,
                Access.line == line
            ).all()
            
            if cameras:
                logger.debug(f"Encontradas {len(cameras)} cámaras para device={device}, line={line}")
                return cameras
            
            # Buscar solo por name si no se encuentra por line
            cameras = session.query(Access).filter(
                Access.name == device
            ).all()
            
            if cameras:
                logger.warning(f"Cámaras encontradas solo por device name (line {line} no coincide): {len(cameras)}")
                return cameras[:1]  # Tomar solo la primera si hay ambigüedad
            
            logger.error(f"No se encontraron cámaras para device={device}, line={line}")
            return []
            
        except Exception as e:
            logger.error(f"Error buscando cámaras: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del procesador de forma thread-safe
        
        Returns:
            Diccionario con estadísticas actuales
        """
        with self._stats_lock:
            stats = self._stats.copy()
            
            # Calcular estadísticas adicionales
            if stats['processing_times']:
                stats['avg_processing_time'] = sum(stats['processing_times']) / len(stats['processing_times'])
                stats['max_processing_time'] = max(stats['processing_times'])
                stats['min_processing_time'] = min(stats['processing_times'])
            else:
                stats['avg_processing_time'] = 0
                stats['max_processing_time'] = 0
                stats['min_processing_time'] = 0
            
            # Limpiar lista de tiempos para evitar memory leak
            if len(stats['processing_times']) > 1000:
                self._stats['processing_times'] = self._stats['processing_times'][-500:]
            
            return stats
    
    def shutdown(self):
        """Cerrar el procesador de forma limpia"""
        logger.info("Cerrando CameraMessageProcessor...")
        self.executor.shutdown(wait=True)
        self.engine.dispose()
        logger.info("CameraMessageProcessor cerrado correctamente")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


    # =================== MÉTODOS DE DETECCIÓN Y VALIDACIÓN ===================
    
    def _detect_reset_intelligent(self, camera: Access, message_data: Dict[str, Any]) -> ResetInfo:
        """Detección inteligente de reinicios - delegado a CameraDetectionMethods"""
        from camera_detection_methods import CameraDetectionMethods
        return CameraDetectionMethods.detect_reset_intelligent(camera, message_data)
    
    def _calculate_and_validate_deltas(self, camera: Access, message_data: Dict[str, Any], 
                                     reset_info: ResetInfo) -> DeltaValidation:
        """Cálculo y validación de deltas - delegado a CameraDetectionMethods"""
        from camera_detection_methods import CameraDetectionMethods
        return CameraDetectionMethods.calculate_and_validate_deltas(camera, message_data, reset_info)
    
    # =================== MÉTODOS DE OPERACIONES ATÓMICAS ===================
    
    def _update_occupancy_atomic(self, session: Session, cameras: List[Access], 
                               delta_in: int, delta_out: int, reset_info: ResetInfo) -> List[Dict[str, Any]]:
        """Actualización atómica de ocupación - delegado a CameraAtomicOperations"""
        from camera_atomic_operations import CameraAtomicOperations
        return CameraAtomicOperations.update_occupancy_atomic(session, cameras, delta_in, delta_out, reset_info)
    
    def _update_camera_counters(self, session: Session, cameras: List[Access], message_data: Dict[str, Any]):
        """Actualización de contadores de cámaras - delegado a CameraAtomicOperations"""
        from camera_atomic_operations import CameraAtomicOperations
        return CameraAtomicOperations.update_camera_counters(session, cameras, message_data)
    
    def _log_message_processing(self, session: Session, message_data: Dict[str, Any], 
                              delta_result: DeltaValidation, updated_parkings: List[Dict[str, Any]], 
                              reset_info: ResetInfo):
        """Logging de procesamiento - delegado a CameraAtomicOperations"""
        from camera_atomic_operations import CameraAtomicOperations
        return CameraAtomicOperations.log_message_processing(
            session, message_data, delta_result, updated_parkings, reset_info
        )
