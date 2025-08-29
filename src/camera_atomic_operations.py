#!/usr/bin/env python3
"""
Operaciones atómicas para CameraMessageProcessor
Incluye actualización atómica de ocupación y logging de transacciones
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Access, Parking, CameraParking, OccupancyHistory, CameraLog
from camera_detection_methods import CameraDetectionMethods
from camera_message_processor import ResetInfo, DeltaValidation

logger = logging.getLogger(__name__)


class CameraAtomicOperations:
    """Operaciones atómicas para el procesador de mensajes de cámaras"""
    
    @staticmethod
    def update_occupancy_atomic(session: Session, cameras: List[Access], delta_in: int, 
                              delta_out: int, reset_info: ResetInfo) -> List[Dict[str, Any]]:
        """
        Actualización atómica de ocupación con bloqueo de filas para evitar condiciones de carrera
        
        Args:
            session: Sesión de base de datos
            cameras: Lista de cámaras afectadas
            delta_in: Delta de entradas
            delta_out: Delta de salidas
            reset_info: Información sobre reinicio
            
        Returns:
            Lista de parkings actualizados con información de cambios
        """
        updated_parkings = []
        
        for camera in cameras:
            # Obtener parkings asociados a esta cámara
            camera_parkings = session.query(CameraParking).filter_by(camera_id=camera.id).all()
            
            for camera_parking in camera_parkings:
                parking_id = camera_parking.parking_id
                
                try:
                    # BLOQUEO ATÓMICO DE LA FILA DEL PARKING
                    # Usar FOR UPDATE para bloquear la fila y evitar condiciones de carrera
                    result = session.execute(
                        text("""
                            SELECT id, name, current_occupancy, max_capacity, status,
                                   threshold_dense, threshold_full, fixed_message_flag
                            FROM parkings 
                            WHERE id = :parking_id 
                            FOR UPDATE
                        """),
                        {"parking_id": parking_id}
                    ).fetchone()
                    
                    if not result:
                        logger.error(f"Parking {parking_id} no encontrado durante actualización atómica")
                        continue
                    
                    # Extraer datos del parking
                    parking_name = result[1]
                    current_occupancy = result[2]
                    max_capacity = result[3]
                    current_status = result[4]
                    threshold_dense = result[6]
                    threshold_full = result[7]
                    fixed_message_flag = result[8]
                    
                    previous_occupancy = current_occupancy
                    
                    # Aplicar delta solo si no es reinicio
                    if not reset_info.is_reset:
                        new_occupancy = current_occupancy + (delta_in - delta_out)
                        change_reason = f"camera_delta_in_{delta_in}_out_{delta_out}"
                    else:
                        new_occupancy = current_occupancy  # Mantener ocupación en reinicios
                        change_reason = f"camera_reset_detected_confidence_{reset_info.confidence}"
                    
                    # VALIDACIÓN FINAL A NIVEL DE PARKING
                    validation_result = CameraDetectionMethods.validate_parking_occupancy(
                        new_occupancy, max_capacity, current_occupancy, delta_in, delta_out
                    )
                    
                    if not validation_result['valid']:
                        logger.warning(f"Ocupación inválida para parking {parking_name}: {validation_result['reason']}")
                        
                        # Aplicar corrección si es necesaria
                        if validation_result['needs_correction']:
                            new_occupancy = validation_result['corrected_occupancy']
                            change_reason += f"_corrected_to_{new_occupancy}"
                    
                    # Calcular nuevo estado del parking
                    new_status = CameraAtomicOperations._calculate_parking_status(
                        new_occupancy, max_capacity, threshold_dense, threshold_full, fixed_message_flag
                    )
                    
                    # ACTUALIZACIÓN ATÓMICA
                    session.execute(
                        text("""
                            UPDATE parkings 
                            SET current_occupancy = :new_occupancy, 
                                status = :new_status
                            WHERE id = :parking_id
                        """),
                        {
                            "new_occupancy": new_occupancy,
                            "new_status": new_status,
                            "parking_id": parking_id
                        }
                    )
                    
                    # Registrar en histórico de ocupación
                    CameraAtomicOperations._create_occupancy_history(
                        session, parking_id, new_occupancy, 'camera', delta_in, delta_out, 
                        previous_occupancy, change_reason
                    )
                    
                    updated_parkings.append({
                        'parking_id': parking_id,
                        'name': parking_name,
                        'previous_occupancy': previous_occupancy,
                        'new_occupancy': new_occupancy,
                        'change': new_occupancy - previous_occupancy,
                        'status': new_status,
                        'previous_status': current_status,
                        'validation': validation_result,
                        'reset_detected': reset_info.is_reset
                    })
                    
                    logger.info(f"Parking {parking_name} actualizado: {previous_occupancy} → {new_occupancy} ({new_status})")
                    
                    if validation_result['validations']:
                        logger.warning(f"Validaciones para {parking_name}: {validation_result['validations']}")
                
                except Exception as e:
                    logger.error(f"Error en actualización atómica del parking {parking_id}: {e}")
                    # No hacer rollback aquí - se maneja en el nivel superior
                    continue
        
        return updated_parkings
    
    @staticmethod
    def _calculate_parking_status(occupancy: int, max_capacity: int, threshold_dense: int, 
                                threshold_full: int, fixed_message_flag: bool) -> str:
        """
        Calcular estado del parking basado en ocupación y umbrales
        
        Args:
            occupancy: Ocupación actual
            max_capacity: Capacidad máxima
            threshold_dense: Umbral para estado DENSO
            threshold_full: Umbral para estado COMPLETO
            fixed_message_flag: Si el mensaje está fijado
            
        Returns:
            Estado del parking ('LIBRE', 'DENSO', 'COMPLETO')
        """
        if fixed_message_flag:
            # Si el mensaje está fijado, no cambiar el estado
            # El estado actual se mantendrá
            return None  # Indicar que no se debe cambiar
        
        free_spaces = max_capacity - occupancy
        
        # Casos especiales para ocupación anómala
        if free_spaces < 0:
            # Ocupación excede capacidad (descuadre negativo)
            return 'COMPLETO'
        elif occupancy > max_capacity:
            # Ocupación excede capacidad directamente
            return 'COMPLETO'
        elif free_spaces <= threshold_full:
            return 'COMPLETO'
        elif free_spaces <= threshold_dense:
            return 'DENSO'
        else:
            return 'LIBRE'
    
    @staticmethod
    def _create_occupancy_history(session: Session, parking_id: int, occupancy: int, 
                                source: str, delta_in: int, delta_out: int,
                                previous_occupancy: int, change_reason: str):
        """
        Crear entrada en el histórico de ocupación
        
        Args:
            session: Sesión de base de datos
            parking_id: ID del parking
            occupancy: Nueva ocupación
            source: Fuente del cambio ('camera', 'manual', etc.)
            delta_in: Delta de entradas
            delta_out: Delta de salidas
            previous_occupancy: Ocupación anterior
            change_reason: Razón del cambio
        """
        try:
            history_entry = OccupancyHistory(
                parking_id=parking_id,
                occupancy=occupancy,
                source=source,
                previous_occupancy=previous_occupancy,
                change_amount=occupancy - previous_occupancy,
                metadata=json.dumps({
                    'delta_in': delta_in,
                    'delta_out': delta_out,
                    'change_reason': change_reason,
                    'timestamp': datetime.now().isoformat()
                })
            )
            session.add(history_entry)
            
        except Exception as e:
            logger.error(f"Error creando entrada de histórico para parking {parking_id}: {e}")
    
    @staticmethod
    def update_camera_counters(session: Session, cameras: List[Access], message_data: Dict[str, Any]):
        """
        Actualizar contadores de las cámaras
        
        Args:
            session: Sesión de base de datos
            cameras: Lista de cámaras a actualizar
            message_data: Datos del mensaje recibido
        """
        new_in = message_data.get('vehicle_in', 0)
        new_out = message_data.get('vehicle_out', 0)
        
        for camera in cameras:
            try:
                # Actualizar contadores y timestamp
                camera.last_vehicle_in = new_in
                camera.last_vehicle_out = new_out
                camera.last_message_received = datetime.now()
                camera.status = 'ONLINE'  # Marcar como online al recibir mensaje
                
                logger.debug(f"Contadores actualizados para cámara {camera.id}: IN={new_in}, OUT={new_out}")
                
            except Exception as e:
                logger.error(f"Error actualizando contadores de cámara {camera.id}: {e}")
    
    @staticmethod
    def log_message_processing(session: Session, message_data: Dict[str, Any], 
                             delta_result: DeltaValidation, updated_parkings: List[Dict[str, Any]], 
                             reset_info: ResetInfo):
        """
        Registrar log detallado del procesamiento del mensaje
        
        Args:
            session: Sesión de base de datos
            message_data: Datos del mensaje original
            delta_result: Resultado de validación de deltas
            updated_parkings: Parkings actualizados
            reset_info: Información sobre reinicio
        """
        try:
            # Determinar estado del procesamiento
            if not delta_result.valid:
                status = 'invalid_delta'
                error_message = delta_result.reason
            elif reset_info.is_reset:
                status = 'reset_processed'
                error_message = f"Reset detectado: {reset_info.reason}"
            else:
                status = 'processed'
                error_message = None
            
            # Preparar metadata del log
            log_metadata = {
                'delta_in': delta_result.delta_in,
                'delta_out': delta_result.delta_out,
                'reset_info': {
                    'is_reset': reset_info.is_reset,
                    'confidence': reset_info.confidence,
                    'criteria': reset_info.criteria_met,
                    'reason': reset_info.reason
                },
                'validation_result': {
                    'valid': delta_result.valid,
                    'validations': delta_result.validations
                },
                'updated_parkings': len(updated_parkings),
                'parkings_details': [
                    {
                        'parking_id': p['parking_id'],
                        'name': p['name'],
                        'change': p['change'],
                        'new_occupancy': p['new_occupancy']
                    } for p in updated_parkings
                ]
            }
            
            # Crear entrada de log de cámara
            camera_log = CameraLog(
                camera_ip=message_data.get('source_ip', 'unknown'),
                camera_line=message_data.get('line', 0),
                camera_name=message_data.get('device', 'unknown'),
                raw_message=message_data.get('raw_data', ''),
                vehicle_in=message_data.get('vehicle_in', 0),
                vehicle_out=message_data.get('vehicle_out', 0),
                status=status,
                error_message=error_message,
                previous_vehicle_in=reset_info.previous_in,
                previous_vehicle_out=reset_info.previous_out,
                delta_in=delta_result.delta_in,
                delta_out=delta_result.delta_out,
                metadata=json.dumps(log_metadata)
            )
            
            session.add(camera_log)
            
        except Exception as e:
            logger.error(f"Error registrando log de procesamiento: {e}")
            # No fallar el procesamiento por errores de logging
