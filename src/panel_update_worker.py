#!/usr/bin/env python3
"""
PanelUpdateWorker - Worker independiente para actualización periódica de paneles
Sistema separado que actualiza paneles cada 2 minutos independientemente del flujo de mensajes

Características principales:
- Worker independiente con threading propio
- Actualización periódica cada 2 minutos (configurable)
- Verificación de programaciones activas
- Envío paralelo a paneles con timeouts individuales
- Gestión de errores por panel sin afectar otros
- Sistema de estadísticas integrado
- Shutdown graceful con manejo de señales
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models import Parking, Panel, PanelSchedule
from config import DB_URL

# Configurar logging específico para el worker
logger = logging.getLogger(__name__)

@dataclass
class PanelUpdateResult:
    """Resultado de actualización de un panel"""
    panel_id: int
    panel_ip: str
    success: bool
    message: str
    response_time_ms: float
    error: Optional[str] = None


@dataclass
class ParkingUpdateResult:
    """Resultado de actualización de un parking completo"""
    parking_id: int
    parking_name: str
    message_type: str  # 'schedule' | 'occupancy'
    message_sent: str
    panels_total: int
    panels_updated: int
    panels_failed: int
    execution_time_ms: float
    active_schedule: Optional[Dict] = None
    errors: Optional[List[str]] = None


class PanelUpdateWorker:
    """
    Worker independiente para actualización periódica de paneles
    """
    
    def __init__(self, update_interval: int = 120, max_panel_workers: int = 10):
        """
        Inicializar el worker de paneles
        
        Args:
            update_interval: Intervalo en segundos para actualización (default: 120s = 2min)
            max_panel_workers: Máximo workers para envío paralelo a paneles
        """
        self.update_interval = update_interval
        self.max_panel_workers = max_panel_workers
        
        # Configuración de base de datos
        self.engine = create_engine(
            DB_URL, 
            pool_pre_ping=True, 
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # Control del worker
        self.running = False
        self.worker_thread = None
        
        # Panel communication service
        self.panel_service = None
        self._init_panel_service()
        
        # Estadísticas del worker thread-safe
        self._stats = {
            'cycles_completed': 0,
            'panels_updated': 0,
            'panels_failed': 0,
            'parkings_processed': 0,
            'last_update': None,
            'average_cycle_time': 0.0,
            'active_schedules_processed': 0,
            'occupancy_updates_sent': 0,
            'errors': 0,
            'uptime_start': None
        }
        self._stats_lock = threading.Lock()
        
        logger.info(f"PanelUpdateWorker inicializado - Intervalo: {update_interval}s, Workers: {max_panel_workers}")
    
    def _init_panel_service(self):
        """Inicializar servicio de comunicación con paneles"""
        try:
            from panel_communication_service import PanelCommunicationService
            # URL del servicio Java de paneles (puerto 8888)
            self.panel_service = PanelCommunicationService("http://localhost:8888/api/v1/panels/send")
            logger.info("Servicio de comunicación con paneles inicializado")
        except Exception as e:
            logger.error(f"Error inicializando servicio de paneles: {e}")
            self.panel_service = None
    
    def start(self):
        """Iniciar el worker en un hilo separado"""
        if self.running:
            logger.warning("Panel worker ya está ejecutándose")
            return
        
        self.running = True
        
        # Actualizar estadísticas de inicio
        with self._stats_lock:
            self._stats['uptime_start'] = datetime.now()
        
        # Crear e iniciar hilo del worker
        self.worker_thread = threading.Thread(
            target=self._worker_loop, 
            daemon=True,
            name="PanelUpdateWorker"
        )
        self.worker_thread.start()
        
        logger.info(f"Panel Update Worker iniciado - Intervalo: {self.update_interval}s")
    
    def stop(self):
        """Detener el worker de forma limpia"""
        logger.info("Deteniendo Panel Update Worker...")
        self.running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)  # Esperar máximo 10 segundos
            
            if self.worker_thread.is_alive():
                logger.warning("Worker thread no se detuvo en el tiempo esperado")
            else:
                logger.info("Worker thread detenido correctamente")
        
        # Cerrar conexiones de base de datos
        self.engine.dispose()
        
        logger.info("Panel Update Worker detenido")
    
    def _worker_loop(self):
        """Bucle principal del worker"""
        logger.info("Iniciando bucle principal del worker")
        
        while self.running:
            cycle_start = time.time()
            
            try:
                # Ejecutar ciclo de actualización
                self._update_all_panels()
                
                # Actualizar estadísticas del ciclo
                cycle_time = time.time() - cycle_start
                with self._stats_lock:
                    self._stats['cycles_completed'] += 1
                    self._stats['last_update'] = datetime.now()
                    
                    # Calcular tiempo promedio de ciclo
                    cycles = self._stats['cycles_completed']
                    current_avg = self._stats['average_cycle_time']
                    self._stats['average_cycle_time'] = (current_avg * (cycles - 1) + cycle_time) / cycles
                
                logger.info(f"Ciclo de actualización completado en {cycle_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error en ciclo de actualización de paneles: {e}")
                with self._stats_lock:
                    self._stats['errors'] += 1
            
            # Esperar hasta el próximo ciclo
            # Usar bucle con sleeps cortos para poder parar más rápido
            sleep_time = self.update_interval
            while sleep_time > 0 and self.running:
                time.sleep(min(sleep_time, 1))  # Dormir máximo 1 segundo a la vez
                sleep_time -= 1
        
        logger.info("Bucle principal del worker terminado")
    
    def _update_all_panels(self):
        """Actualizar todos los paneles del sistema"""
        if not self.panel_service:
            logger.error("Servicio de paneles no disponible - omitiendo actualización")
            return
        
        session = self.Session()
        
        try:
            # Obtener todos los parkings con sus paneles
            parkings_data = self._get_parkings_data(session)
            
            if not parkings_data:
                logger.info("No hay parkings con paneles para actualizar")
                return
            
            logger.info(f"Procesando {len(parkings_data)} parkings")
            
            # Actualizar estadísticas
            with self._stats_lock:
                self._stats['parkings_processed'] += len(parkings_data)
            
            # Procesar parkings en paralelo (máximo 5 parkings simultáneos)
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Crear futures para cada parking
                futures = {
                    executor.submit(self._update_parking_panels, parking_data): parking_data['id']
                    for parking_data in parkings_data
                }
                
                # Procesar resultados con timeout total de 90 segundos
                for future in as_completed(futures, timeout=90):
                    parking_id = futures[future]
                    
                    try:
                        result = future.result(timeout=15)  # 15s por parking
                        
                        if result and result.panels_updated > 0:
                            with self._stats_lock:
                                self._stats['panels_updated'] += result.panels_updated
                                if result.message_type == 'schedule':
                                    self._stats['active_schedules_processed'] += 1
                                else:
                                    self._stats['occupancy_updates_sent'] += 1
                        
                        if result and result.panels_failed > 0:
                            with self._stats_lock:
                                self._stats['panels_failed'] += result.panels_failed
                        
                        logger.debug(f"Parking {result.parking_name}: {result.panels_updated}/{result.panels_total} paneles actualizados")
                        
                    except FutureTimeoutError:
                        logger.error(f"Timeout actualizando parking {parking_id}")
                        with self._stats_lock:
                            self._stats['errors'] += 1
                    
                    except Exception as e:
                        logger.error(f"Error actualizando parking {parking_id}: {e}")
                        with self._stats_lock:
                            self._stats['errors'] += 1
        
        except Exception as e:
            logger.error(f"Error en actualización masiva de paneles: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
        
        finally:
            session.close()
    
    def _get_parkings_data(self, session: Session) -> List[Dict[str, Any]]:
        """
        Obtener datos de todos los parkings con paneles
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Lista de diccionarios con datos de parkings
        """
        try:
            # Consulta optimizada que obtiene parkings con al menos un panel activo
            result = session.execute(text("""
                SELECT DISTINCT 
                    p.id, p.name, p.current_occupancy, p.max_capacity, p.status,
                    p.threshold_dense, p.threshold_full, p.fixed_message_flag,
                    p.message_type,
                    COUNT(pan.id) as panel_count
                FROM parkings p
                INNER JOIN panels pan ON pan.parking_id = p.id
                WHERE pan.status != 'OFFLINE'
                GROUP BY p.id, p.name, p.current_occupancy, p.max_capacity, p.status,
                         p.threshold_dense, p.threshold_full, p.fixed_message_flag, p.message_type
                HAVING COUNT(pan.id) > 0
                ORDER BY p.id
            """)).fetchall()
            
            parkings_data = []
            for row in result:
                parking_data = {
                    'id': row[0],
                    'name': row[1],
                    'current_occupancy': row[2],
                    'max_capacity': row[3],
                    'status': row[4],
                    'threshold_dense': row[5],
                    'threshold_full': row[6],
                    'fixed_message_flag': row[7],
                    'message_type': row[8],  # NUEVO: Campo message_type
                    'panel_count': row[9]   # Ajustado índice
                }
                parkings_data.append(parking_data)
            
            logger.debug(f"Obtenidos {len(parkings_data)} parkings con paneles activos")
            return parkings_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de parkings: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del worker de forma thread-safe
        
        Returns:
            Diccionario con estadísticas actuales
        """
        with self._stats_lock:
            stats = self._stats.copy()
            
            # Calcular estadísticas adicionales
            if stats['uptime_start']:
                uptime = datetime.now() - stats['uptime_start']
                stats['uptime_seconds'] = uptime.total_seconds()
                stats['uptime_formatted'] = str(uptime).split('.')[0]  # Sin microsegundos
            
            # Calcular tasas
            if stats['cycles_completed'] > 0:
                stats['panels_per_cycle'] = stats['panels_updated'] / stats['cycles_completed']
                stats['errors_per_cycle'] = stats['errors'] / stats['cycles_completed']
            else:
                stats['panels_per_cycle'] = 0
                stats['errors_per_cycle'] = 0
            
            # Estado del worker
            stats['is_running'] = self.running
            stats['worker_thread_alive'] = self.worker_thread.is_alive() if self.worker_thread else False
            
            return stats
    
    def force_update_cycle(self) -> Dict[str, Any]:
        """
        Forzar un ciclo de actualización inmediato (para testing/debugging)
        
        Returns:
            Resultado del ciclo forzado
        """
        if not self.running:
            return {'success': False, 'error': 'Worker no está ejecutándose'}
        
        logger.info("Forzando ciclo de actualización inmediato")
        
        start_time = time.time()
        
        try:
            self._update_all_panels()
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'execution_time_ms': execution_time * 1000,
                'message': 'Ciclo forzado completado exitosamente'
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error en ciclo forzado: {e}")
            
            return {
                'success': False,
                'execution_time_ms': execution_time * 1000,
                'error': str(e)
            }
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


    # =================== MÉTODOS DE ACTUALIZACIÓN DE PANELES ===================
    
    def _update_parking_panels(self, parking_data: Dict[str, Any]) -> Optional[ParkingUpdateResult]:
        """Actualizar paneles de un parking - delegado a PanelUpdateMethods"""
        from panel_update_methods import PanelUpdateMethods
        return PanelUpdateMethods.update_parking_panels(self, parking_data)
