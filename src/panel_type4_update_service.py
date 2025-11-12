#!/usr/bin/env python3
"""
Servicio de actualización de paneles Tipo 3 y Tipo 4
- Tipo 3: Actualiza ventanas 0 y 1 con valores numéricos simples (plazas libres, PMR)
- Tipo 4: Actualiza hasta 16 ventanas con contenido rotado según configuración
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Panel, PanelType, Parking, ParkingPanelWindow, PanelWindowConfiguration

logger = logging.getLogger(__name__)


class PanelType3And4UpdateService:
    """Servicio para actualizar paneles Tipo 3 y Tipo 4"""
    
    def __init__(self, db_session: Session):
        """
        Inicializa el servicio
        
        Args:
            db_session: Sesión de base de datos
        """
        self.db_session = db_session
    
    def update_all_type3_and_type4_panels(self) -> Dict[str, Any]:
        """
        Actualiza todos los paneles Tipo 3 y Tipo 4 con su contenido configurado
        
        Returns:
            Dict con estadísticas de actualización
        """
        try:
            # Obtener todos los paneles Tipo 3 y Tipo 4 activos
            type3_and_4_panels = self.db_session.query(Panel).join(PanelType).filter(
                and_(
                    Panel.is_active == True,
                    Panel.panel_type_id == PanelType.id,
                    PanelType.windows_count.in_([2, 16])  # Tipo 3 = 2 ventanas, Tipo 4 = 16 ventanas
                )
            ).all()
            
            stats = {
                'panels_processed': 0,
                'panels_updated': 0,
                'panels_failed': 0,
                'windows_updated': 0,
                'type3_panels': 0,
                'type4_panels': 0,
                'errors': []
            }
            
            for panel in type3_and_4_panels:
                try:
                    # Determinar tipo de panel
                    is_type3 = panel.panel_type and panel.panel_type.windows_count == 2
                    is_type4 = panel.panel_type and panel.panel_type.windows_count == 16
                    
                    if is_type3:
                        stats['type3_panels'] += 1
                    elif is_type4:
                        stats['type4_panels'] += 1
                    
                    result = self.update_panel(panel.id)
                    stats['panels_processed'] += 1
                    if result['success']:
                        stats['panels_updated'] += 1
                        stats['windows_updated'] += result.get('windows_updated', 0)
                    else:
                        stats['panels_failed'] += 1
                        stats['errors'].append({
                            'panel_id': panel.id,
                            'panel_name': panel.name,
                            'error': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    logger.error(f"Error actualizando panel {panel.id}: {e}")
                    stats['panels_failed'] += 1
                    stats['errors'].append({
                        'panel_id': panel.id,
                        'panel_name': panel.name,
                        'error': str(e)
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en update_all_type3_and_type4_panels: {e}")
            return {
                'panels_processed': 0,
                'panels_updated': 0,
                'panels_failed': 0,
                'windows_updated': 0,
                'type3_panels': 0,
                'type4_panels': 0,
                'errors': [{'error': str(e)}]
            }
    
    # Mantener método anterior para compatibilidad
    def update_all_type4_panels(self) -> Dict[str, Any]:
        """Método de compatibilidad - redirige a update_all_type3_and_type4_panels"""
        return self.update_all_type3_and_type4_panels()
    
    def update_panel(self, panel_id: int) -> Dict[str, Any]:
        """
        Actualiza un panel Tipo 3 o Tipo 4 específico (detecta automáticamente el tipo)
        
        Args:
            panel_id: ID del panel
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            # Obtener el panel
            panel = self.db_session.query(Panel).filter(Panel.id == panel_id).first()
            if not panel:
                return {'success': False, 'error': 'Panel no encontrado'}
            
            # Detectar tipo de panel
            if not panel.panel_type:
                return {'success': False, 'error': 'Panel no tiene tipo asignado'}
            
            windows_count = panel.panel_type.windows_count
            
            # Tipo 3: 2 ventanas
            if windows_count == 2:
                return self.update_type3_panel(panel_id)
            # Tipo 4: 16 ventanas
            elif windows_count == 16:
                return self.update_type4_panel(panel_id)
            else:
                return {'success': False, 'error': f'Panel tipo no soportado (windows_count: {windows_count})'}
        except Exception as e:
            logger.error(f"Error en update_panel {panel_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_type3_panel(self, panel_id: int) -> Dict[str, Any]:
        """
        Actualiza un panel Tipo 3 (2 ventanas con valores numéricos simples)
        
        Args:
            panel_id: ID del panel
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            from panel_protocol.panel_protocol_service import PanelProtocolService
            
            # Obtener el panel
            panel = self.db_session.query(Panel).filter(Panel.id == panel_id).first()
            if not panel:
                return {'success': False, 'error': 'Panel no encontrado'}
            
            # Verificar que es Tipo 3
            if not panel.panel_type or panel.panel_type.windows_count != 2:
                return {'success': False, 'error': 'Panel no es Tipo 3'}
            
            # Obtener parking
            parking = self.db_session.query(Parking).filter(
                Parking.id == panel.parking_id
            ).first()
            
            if not parking:
                return {'success': False, 'error': 'Parking no encontrado'}
            
            # Inicializar servicio de protocolo
            protocol_service = PanelProtocolService()
            
            windows_updated = 0
            errors = []
            
            # Actualizar ventanas 0 y 1
            for window_id in [0, 1]:
                try:
                    # Obtener asignación de la ventana
                    assignment = self.db_session.query(ParkingPanelWindow).filter(
                        and_(
                            ParkingPanelWindow.panel_id == panel_id,
                            ParkingPanelWindow.window_id == window_id,
                            ParkingPanelWindow.is_active == True
                        )
                    ).first()
                    
                    if not assignment:
                        logger.debug(f"Panel {panel_id}, ventana {window_id}: Sin asignación configurada")
                        continue
                    
                    # Obtener contenido según el tipo de asignación
                    message = None
                    color = 2  # Verde por defecto
                    
                    if assignment.display_type == 'parking':
                        # Ventana con datos del parking (plazas libres totales)
                        free_spaces = parking.max_capacity - parking.current_occupancy
                        message = str(free_spaces)
                        color = 2  # Verde para plazas libres
                    elif assignment.display_type == 'sensor_group' and assignment.sensor_type:
                        # Ventana con datos de sensores agrupados (ej: PMR)
                        from panel_window_service import PanelWindowService
                        window_service = PanelWindowService(self.db_session)
                        sensor_data = window_service.get_sensor_data_for_window(panel_id, window_id)
                        
                        if sensor_data:
                            free_count = sensor_data.get('free', 0)
                            # Para Tipo 3, NO usar texto_fijo_previo (solo valores numéricos)
                            message = str(free_count)
                            
                            # Usar color de la asignación si está configurado
                            if assignment.color:
                                color = assignment.color
                            else:
                                color = 2  # Verde por defecto
                        else:
                            message = "0"  # Sin datos disponibles
                    else:
                        logger.warning(f"Panel {panel_id}, ventana {window_id}: Tipo de asignación no reconocido")
                        continue
                    
                    if not message:
                        continue
                    
                    # Enviar mensaje al panel usando protocolo v4 (síncrono)
                    try:
                        # Ejecutar la corrutina de forma síncrona
                        task_id = asyncio.run(
                            protocol_service.send_text_v4(
                                panel_ip=panel.ip,
                                panel_port=panel.port or 5200,
                                window_id=window_id,
                                text=message,
                                color=color,
                                font_size=2,  # Tamaño medio
                                effect=0,  # Sin efecto
                                alignment=0,  # Izquierda arriba
                                wait_for_response=True  # Esperar respuesta
                            )
                        )
                        
                        # Obtener el resultado de la tarea
                        result = asyncio.run(
                            protocol_service.get_task_result(task_id, timeout=10.0)
                        )
                        
                        if result and result.get('success'):
                            windows_updated += 1
                            # Actualizar último mensaje en la tabla Panel
                            if window_id == 0:
                                panel.last_message = message
                                panel.last_message_window_0 = message
                                panel.last_update_window_0 = datetime.utcnow()
                            elif window_id == 1:
                                panel.last_message_window_1 = message
                                panel.last_update_window_1 = datetime.utcnow()
                                if not panel.last_message:
                                    panel.last_message = message
                            
                            panel.last_update = datetime.utcnow()
                            self.db_session.commit()
                            
                            logger.info(
                                f"Ventana {window_id} del panel {panel.id} ({panel.name}) "
                                f"actualizada: {message}"
                            )
                        else:
                            errors.append({
                                'window_id': window_id,
                                'error': result.get('error', 'Unknown error') if result else 'No result received'
                            })
                    except Exception as e:
                        logger.error(f"Error enviando mensaje a ventana {window_id} del panel {panel_id}: {e}")
                        errors.append({
                            'window_id': window_id,
                            'error': str(e)
                        })
                except Exception as e:
                    logger.error(f"Error actualizando ventana {window_id} del panel {panel_id}: {e}")
                    errors.append({
                        'window_id': window_id,
                        'error': str(e)
                    })
            
            return {
                'success': windows_updated > 0,
                'windows_updated': windows_updated,
                'total_windows': 2,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error en update_type3_panel {panel_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_type4_panel(self, panel_id: int) -> Dict[str, Any]:
        """
        Actualiza un panel Tipo 4 específico (contenido rotado)
        
        Args:
            panel_id: ID del panel
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            from panel_content_rotation_service import PanelContentRotationService
            from panel_protocol.panel_protocol_service import PanelProtocolService
            
            # Obtener el panel
            panel = self.db_session.query(Panel).filter(Panel.id == panel_id).first()
            if not panel:
                return {'success': False, 'error': 'Panel no encontrado'}
            
            # Verificar que es Tipo 4
            if not panel.panel_type or panel.panel_type.windows_count != 16:
                return {'success': False, 'error': 'Panel no es Tipo 4'}
            
            # Obtener parking para message_type
            parking = self.db_session.query(Parking).filter(
                Parking.id == panel.parking_id
            ).first()
            
            if not parking:
                return {'success': False, 'error': 'Parking no encontrado'}
            
            message_type = parking.message_type or 'ESTADO'
            
            # Inicializar servicios
            rotation_service = PanelContentRotationService(self.db_session)
            protocol_service = PanelProtocolService()
            
            windows_updated = 0
            errors = []
            
            # Actualizar cada ventana del panel
            for window_id in range(panel.windows_count or 16):
                try:
                    # Obtener contenido para la ventana
                    content = rotation_service.get_content_for_window(
                        panel_id=panel.id,
                        window_id=window_id
                    )
                    
                    if not content:
                        continue  # No hay contenido configurado para esta ventana
                    
                    # Obtener configuración de status si existe
                    status_config = content.get('status_config')
                    
                    # Formatear mensaje y obtener color
                    message, color = rotation_service.format_message_for_panel(
                        content,
                        parking_message_type=message_type,
                        status_config=status_config
                    )
                    
                    if not message:
                        continue
                    
                    # Enviar mensaje al panel usando protocolo v4 (síncrono)
                    try:
                        # Ejecutar la corrutina de forma síncrona
                        task_id = asyncio.run(
                            protocol_service.send_text_v4(
                                panel_ip=panel.ip,
                                panel_port=panel.port or 5200,
                                window_id=window_id,
                                text=message,
                                color=color,  # Color dinámico según configuración
                                font_size=2,  # Tamaño medio
                                effect=0,  # Sin efecto
                                alignment=0,  # Izquierda arriba
                                wait_for_response=True  # Esperar respuesta
                            )
                        )
                        
                        # Obtener el resultado de la tarea
                        result = asyncio.run(
                            protocol_service.get_task_result(task_id, timeout=10.0)
                        )
                        
                        if result and result.get('success'):
                            windows_updated += 1
                            # Actualizar último mensaje en la tabla Panel
                            # Para ventana 0, actualizar last_message general
                            # Para otras ventanas, actualizar last_message general con el mensaje más reciente
                            if window_id == 0:
                                panel.last_message = message
                                panel.last_message_window_0 = message
                                panel.last_update_window_0 = datetime.utcnow()
                            elif window_id == 1:
                                panel.last_message_window_1 = message
                                panel.last_update_window_1 = datetime.utcnow()
                                # Si no hay mensaje en ventana 0, usar el de ventana 1
                                if not panel.last_message:
                                    panel.last_message = message
                            
                            # Actualizar last_update general con la fecha actual
                            panel.last_update = datetime.utcnow()
                            
                            # Guardar cambios en la base de datos
                            self.db_session.commit()
                            
                            logger.info(
                                f"Ventana {window_id} del panel {panel.id} ({panel.name}) "
                                f"actualizada: {message}"
                            )
                        else:
                            errors.append({
                                'window_id': window_id,
                                'error': result.get('error', 'Unknown error') if result else 'No result received'
                            })
                    except Exception as e:
                        logger.error(f"Error enviando mensaje a ventana {window_id} del panel {panel_id}: {e}")
                        errors.append({
                            'window_id': window_id,
                            'error': str(e)
                        })
                except Exception as e:
                    logger.error(f"Error actualizando ventana {window_id} del panel {panel_id}: {e}")
                    errors.append({
                        'window_id': window_id,
                        'error': str(e)
                    })
            
            return {
                'success': windows_updated > 0,
                'windows_updated': windows_updated,
                'total_windows': panel.windows_count or 16,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error en update_panel {panel_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_next_changes(self, panel_id: int, window_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los próximos cambios programados para una ventana
        
        Args:
            panel_id: ID del panel
            window_id: ID de la ventana
            
        Returns:
            Lista de próximos cambios con tiempos
        """
        try:
            from panel_content_rotation_service import PanelContentRotationService
            
            # Obtener asignaciones y configuración
            assignments = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.window_id == window_id,
                    ParkingPanelWindow.is_active == True
                )
            ).all()
            
            if not assignments:
                return []
            
            first_assignment = assignments[0]
            config = self.db_session.query(PanelWindowConfiguration).filter(
                and_(
                    PanelWindowConfiguration.panel_id == panel_id,
                    PanelWindowConfiguration.window_id == window_id,
                    PanelWindowConfiguration.parking_id == first_assignment.parking_id,
                    PanelWindowConfiguration.is_active == True
                )
            ).first()
            
            if not config or not config.rotation_enabled or not config.rotation_order:
                return []
            
            rotation_service = PanelContentRotationService(self.db_session)
            current_time = datetime.utcnow()
            
            # Calcular ciclo
            cycle_duration = ((config.refresh_time_seconds + 29) // 30) * 30
            BLOCK_SIZE = 30
            
            # Calcular próximos cambios en los próximos 2 ciclos
            changes = []
            for cycle_offset in range(2):
                cycle_start = current_time + timedelta(seconds=cycle_offset * cycle_duration)
                
                cumulative_time = 0.0
                for rotation_item in config.rotation_order:
                    if not isinstance(rotation_item, dict):
                        continue
                    
                    percentage = rotation_item.get('percentage', 0)
                    item_duration = (percentage / 100.0) * BLOCK_SIZE
                    
                    change_time = cycle_start + timedelta(seconds=cumulative_time)
                    changes.append({
                        'time': change_time,
                        'content_type': rotation_item.get('type'),
                        'sensor_type': rotation_item.get('sensor_type'),
                        'texto_fijo_previo': rotation_item.get('texto_fijo_previo'),
                        'duration_seconds': item_duration,
                        'percentage': percentage
                    })
                    
                    cumulative_time += item_duration
                    
                    # Agregar cambios para cada bloque de 30s en el ciclo
                    for block in range(1, cycle_duration // BLOCK_SIZE):
                        block_start = cycle_start + timedelta(seconds=block * BLOCK_SIZE)
                        change_time = block_start + timedelta(seconds=cumulative_time - (block * BLOCK_SIZE))
                        if change_time > current_time:
                            changes.append({
                                'time': change_time,
                                'content_type': rotation_item.get('type'),
                                'sensor_type': rotation_item.get('sensor_type'),
                                'texto_fijo_previo': rotation_item.get('texto_fijo_previo'),
                                'duration_seconds': item_duration,
                                'percentage': percentage
                            })
            
            # Ordenar por tiempo y limitar a los próximos 10 cambios
            changes.sort(key=lambda x: x['time'])
            return changes[:10]
            
        except Exception as e:
            logger.error(f"Error obteniendo próximos cambios: {e}")
            return []

