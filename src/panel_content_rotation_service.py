#!/usr/bin/env python3
"""
Servicio de rotación de contenido para ventanas de paneles Tipo 4
Gestiona la rotación de contenido según porcentajes y tiempos configurados
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import (
    PanelWindowConfiguration, ParkingPanelWindow, Parking, ParkingSensorSummary, Panel
)

logger = logging.getLogger(__name__)


class PanelContentRotationService:
    """Servicio para gestionar rotación de contenido en ventanas de paneles"""
    
    def __init__(self, db_session: Session):
        """
        Inicializa el servicio
        
        Args:
            db_session: Sesión de base de datos
        """
        self.db_session = db_session
    
    def get_content_for_window(
        self,
        panel_id: int,
        window_id: int,
        current_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determina qué contenido mostrar en una ventana según la configuración de rotación
        
        Args:
            panel_id: ID del panel
            window_id: ID de la ventana (0-15)
            current_time: Tiempo actual (por defecto ahora)
            
        Returns:
            Dict con el contenido a mostrar o None si no hay configuración
        """
        try:
            if current_time is None:
                current_time = datetime.utcnow()
            
            # Obtener asignaciones de la ventana
            assignments = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.window_id == window_id,
                    ParkingPanelWindow.is_active == True
                )
            ).order_by(ParkingPanelWindow.priority).all()
            
            if not assignments:
                return None
            
            # Obtener configuración de rotación (usar la primera asignación para buscar config)
            first_assignment = assignments[0]
            config = self.db_session.query(PanelWindowConfiguration).filter(
                and_(
                    PanelWindowConfiguration.panel_id == panel_id,
                    PanelWindowConfiguration.window_id == window_id,
                    PanelWindowConfiguration.parking_id == first_assignment.parking_id,
                    PanelWindowConfiguration.is_active == True
                )
            ).first()
            
            # Si no hay configuración o rotación deshabilitada, usar la primera asignación
            if not config or not config.rotation_enabled or not config.rotation_order:
                return self._get_content_for_assignment(first_assignment)
            
            # Calcular qué contenido mostrar según rotación
            return self._calculate_rotated_content(
                assignments,
                config,
                current_time
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo contenido para ventana: {e}")
            return None
    
    def _get_content_for_assignment(
        self,
        assignment: ParkingPanelWindow
    ) -> Dict[str, Any]:
        """
        Obtiene el contenido para una asignación específica
        
        Args:
            assignment: Asignación de ventana
            
        Returns:
            Dict con contenido
        """
        if assignment.sensor_type is None:
            # Ocupación general del parking
            parking = self.db_session.query(Parking).filter(
                Parking.id == assignment.parking_id
            ).first()
            
            if not parking:
                return None
            
            return {
                'type': 'parking',
                'parking_id': parking.id,
                'parking_name': parking.name,
                'content': {
                    'current_occupancy': parking.current_occupancy,
                    'max_capacity': parking.max_capacity,
                    'free_spaces': parking.max_capacity - parking.current_occupancy,
                    'status': parking.status
                },
                'message': f"Parking {parking.name}: {parking.max_capacity - parking.current_occupancy}/{parking.max_capacity} libres"
            }
        else:
            # Sensores agrupados
            sensor_summary = self.db_session.query(ParkingSensorSummary).filter(
                and_(
                    ParkingSensorSummary.parking_id == assignment.parking_id,
                    ParkingSensorSummary.sensor_type == assignment.sensor_type
                )
            ).first()
            
            if not sensor_summary:
                return None
            
            parking = self.db_session.query(Parking).filter(
                Parking.id == assignment.parking_id
            ).first()
            
            # Usar texto_fijo_previo de la asignación si existe, o el tipo de sensor como fallback
            prefix_text = assignment.texto_fijo_previo if assignment.texto_fijo_previo else assignment.sensor_type
            
            return {
                'type': 'sensor_group',
                'parking_id': parking.id if parking else None,
                'parking_name': parking.name if parking else None,
                'sensor_type': assignment.sensor_type,
                'texto_fijo_previo': assignment.texto_fijo_previo,
                'content': {
                    'total_sensors': sensor_summary.total_sensors,
                    'free_sensors': sensor_summary.free_sensors,
                    'busy_sensors': sensor_summary.busy_sensors,
                    'error_sensors': sensor_summary.error_sensors
                },
                'message': f"{prefix_text}: {sensor_summary.free_sensors}/{sensor_summary.total_sensors} libres"
            }
    
    def _calculate_rotated_content(
        self,
        assignments: List[ParkingPanelWindow],
        config: PanelWindowConfiguration,
        current_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula qué contenido mostrar según la configuración de rotación
        
        Args:
            assignments: Lista de asignaciones
            config: Configuración de rotación
            current_time: Tiempo actual
            
        Returns:
            Dict con contenido a mostrar
        """
        try:
            if not config.rotation_order or not isinstance(config.rotation_order, list):
                # Si no hay rotation_order, usar primera asignación
                if assignments:
                    return self._get_content_for_assignment(assignments[0])
                return None
            
            # Calcular tiempo transcurrido en el ciclo actual
            cycle_duration = config.refresh_time_seconds
            # Asegurar que el ciclo es múltiplo de 30 segundos
            cycle_duration = ((cycle_duration + 29) // 30) * 30
            
            # Trabajar con bloques de 30 segundos
            BLOCK_SIZE = 30
            time_in_cycle = (current_time.timestamp() % cycle_duration)
            
            # Calcular en qué bloque de 30s estamos
            current_block = int(time_in_cycle // BLOCK_SIZE)
            time_in_block = time_in_cycle % BLOCK_SIZE
            
            # Calcular distribución dentro del bloque de 30s según porcentajes
            cumulative_time = 0.0
            
            for rotation_item in config.rotation_order:
                if not isinstance(rotation_item, dict):
                    continue
                
                item_type = rotation_item.get('type')  # 'parking' o 'sensor_group'
                percentage = rotation_item.get('percentage', 0)
                sensor_type = rotation_item.get('sensor_type')
                
                # Calcular tiempo de visualización para este elemento dentro del bloque de 30s
                item_duration = (percentage / 100.0) * BLOCK_SIZE
                
                if time_in_block >= cumulative_time and time_in_block < cumulative_time + item_duration:
                    # Este es el elemento que debe mostrarse ahora
                    content = self._get_content_for_rotation_item(
                        assignments,
                        item_type,
                        sensor_type
                    )
                    # Agregar texto_fijo_previo si existe en rotation_item
                    if content and 'texto_fijo_previo' in rotation_item:
                        content['texto_fijo_previo'] = rotation_item['texto_fijo_previo']
                    return content
                
                cumulative_time += item_duration
            
            # Si no se encontró (por redondeo), usar el último elemento
            if config.rotation_order:
                last_item = config.rotation_order[-1]
                return self._get_content_for_rotation_item(
                    assignments,
                    last_item.get('type'),
                    last_item.get('sensor_type')
                )
            
            # Fallback: primera asignación
            if assignments:
                return self._get_content_for_assignment(assignments[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando contenido rotado: {e}")
            # Fallback: primera asignación
            if assignments:
                return self._get_content_for_assignment(assignments[0])
            return None
    
    def _get_content_for_rotation_item(
        self,
        assignments: List[ParkingPanelWindow],
        item_type: str,
        sensor_type: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene contenido para un elemento específico de rotación
        
        Args:
            assignments: Lista de asignaciones
            item_type: Tipo de elemento ('parking' o 'sensor_group')
            sensor_type: Tipo de sensor si aplica
            
        Returns:
            Dict con contenido
        """
        if item_type == 'parking':
            # Buscar asignación con sensor_type = None (parking general)
            for assignment in assignments:
                if assignment.sensor_type is None:
                    return self._get_content_for_assignment(assignment)
        elif item_type == 'sensor_group' and sensor_type:
            # Buscar asignación con sensor_type específico
            for assignment in assignments:
                if assignment.sensor_type == sensor_type:
                    return self._get_content_for_assignment(assignment)
        
        # Si no se encuentra, usar primera asignación
        if assignments:
            return self._get_content_for_assignment(assignments[0])
        
        return None
    
    def get_all_windows_content(
        self,
        panel_id: int,
        current_time: Optional[datetime] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Obtiene el contenido para todas las ventanas de un panel
        
        Args:
            panel_id: ID del panel
            current_time: Tiempo actual (por defecto ahora)
            
        Returns:
            Dict con window_id como clave y contenido como valor
        """
        try:
            if current_time is None:
                current_time = datetime.utcnow()
            
            # Obtener todas las ventanas con asignaciones activas
            assignments = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.is_active == True
                )
            ).all()
            
            # Agrupar por window_id
            windows_content = {}
            window_ids = set(assignment.window_id for assignment in assignments)
            
            for window_id in window_ids:
                content = self.get_content_for_window(panel_id, window_id, current_time)
                if content:
                    windows_content[window_id] = content
            
            return windows_content
            
        except Exception as e:
            logger.error(f"Error obteniendo contenido de todas las ventanas: {e}")
            return {}
    
    def format_message_for_panel(
        self,
        content: Dict[str, Any],
        parking_message_type: str = 'ESTADO'  # 'ESTADO' o 'PLAZAS_LIBRES'
    ) -> str:
        """
        Formatea el contenido como mensaje para el panel
        
        Args:
            content: Dict con contenido
            parking_message_type: Tipo de mensaje para parking ('ESTADO' o 'PLAZAS_LIBRES')
            
        Returns:
            String formateado para mostrar en el panel
        """
        if not content:
            return ""
        
        if content.get('type') == 'parking':
            parking_data = content.get('content', {})
            free_spaces = parking_data.get('free_spaces', 0)
            max_capacity = parking_data.get('max_capacity', 0)
            status = parking_data.get('status', 'LIBRE')
            parking_name = content.get('parking_name', 'Parking')
            
            if parking_message_type == 'PLAZAS_LIBRES':
                # Mostrar número de plazas libres
                return f"{parking_name}: {free_spaces}/{max_capacity} libres"
            else:
                # Mostrar estado (LIBRE, DENSO, COMPLETO)
                return f"{parking_name}: {status}"
        
        elif content.get('type') == 'sensor_group':
            sensor_data = content.get('content', {})
            free_sensors = sensor_data.get('free_sensors', 0)
            total_sensors = sensor_data.get('total_sensors', 0)
            # Usar texto_fijo_previo si existe, sino usar sensor_type
            prefix_text = content.get('texto_fijo_previo') or content.get('sensor_type', 'Sensores')
            
            # Para sensores siempre mostrar número de plazas libres
            return f"{prefix_text}: {free_sensors}/{total_sensors} libres"
        
        return content.get('message', '')

