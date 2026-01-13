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
            # Hacer rollback para limpiar la transacción en caso de error
            try:
                self.db_session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error haciendo rollback: {rollback_error}")
            return {'success': False, 'error': str(e)}
    
    async def _update_window_async(
        self,
        protocol_service,
        panel: Panel,
        parking: Parking,
        window_id: int
    ) -> Dict[str, Any]:
        """
        Actualiza una ventana específica de forma asíncrona
        
        Args:
            protocol_service: Servicio de protocolo
            panel: Objeto Panel
            parking: Objeto Parking
            window_id: ID de la ventana
            
        Returns:
            Dict con resultado de la actualización de la ventana
        """
        try:
            # Obtener asignación de la ventana
            logger.debug(f"Panel {panel.id} ({panel.name}), ventana {window_id}: Buscando asignación...")
            assignment = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel.id,
                    ParkingPanelWindow.window_id == window_id,
                    ParkingPanelWindow.is_active == True
                )
            ).first()
            
            if not assignment:
                logger.debug(f"Panel {panel.id} ({panel.name}), ventana {window_id}: Sin asignación configurada")
                return {'success': False, 'skipped': True}
            
            logger.info(
                f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                f"Asignación encontrada - Tipo: {assignment.display_type}, "
                f"Parking: {assignment.parking_id}, Sensor: {assignment.sensor_type}"
            )
            
            # Obtener contenido según el tipo de asignación
            message = None
            color = 2  # Verde por defecto
            
            if assignment.display_type == 'parking':
                # Ventana con datos del parking (plazas libres totales)
                free_spaces = parking.max_capacity - parking.current_occupancy
                message = str(free_spaces)
                color = 2  # Verde para plazas libres
                logger.info(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Parking - Capacidad: {parking.max_capacity}, Ocupación: {parking.current_occupancy}, "
                    f"Libres: {free_spaces}, Mensaje: '{message}'"
                )
            elif assignment.display_type == 'status' or assignment.sensor_type == '__STATUS__':
                # Ventana con estado del parking (LIBRE/DENSO/COMPLETO)
                free_spaces = parking.max_capacity - parking.current_occupancy
                
                # Obtener umbrales del parking
                threshold_dense = getattr(parking, 'threshold_dense', 10)
                threshold_full = getattr(parking, 'threshold_full', 4)
                
                # Determinar estado
                if free_spaces <= threshold_full:
                    status = 'COMPLETO'
                    color = 1  # Rojo
                elif free_spaces <= threshold_dense:
                    status = 'DENSO'
                    color = 3  # Amarillo
                else:
                    status = 'LIBRE'
                    color = 2  # Verde
                
                # Determinar idioma (texto_fijo_previo guarda 'castellano' o 'valenciano')
                language = assignment.texto_fijo_previo or 'valenciano'
                
                # Traducir según idioma
                if language.lower() == 'castellano':
                    status_texts = {'LIBRE': 'LIBRE', 'DENSO': 'DENSO', 'COMPLETO': 'COMPLETO'}
                else:
                    status_texts = {'LIBRE': 'LLIURE', 'DENSO': 'DENS', 'COMPLETO': 'COMPLET'}
                
                message = status_texts.get(status, status)
                
                logger.info(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Estado - Libres: {free_spaces}, Umbral denso: {threshold_dense}, Umbral completo: {threshold_full}, "
                    f"Estado: {status}, Idioma: {language}, Mensaje: '{message}', Color: {color}"
                )
            elif assignment.display_type == 'sensor_group' and assignment.sensor_type:
                # Ventana con datos de sensores agrupados (ej: PMR)
                logger.debug(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Obteniendo datos de sensores tipo '{assignment.sensor_type}' para parking {assignment.parking_id}"
                )
                from panel_window_service import PanelWindowService
                window_service = PanelWindowService(self.db_session)
                sensor_data = window_service.get_sensor_data_for_window(panel.id, window_id)
                
                if sensor_data:
                    # CORRECCIÓN: La clave es 'free_sensors', no 'free'
                    free_count = sensor_data.get('free_sensors', 0)
                    total_count = sensor_data.get('total_sensors', 0)
                    # Para Tipo 3, NO usar texto_fijo_previo (solo valores numéricos)
                    message = str(free_count)
                    
                    logger.info(
                        f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                        f"Sensores {assignment.sensor_type} - Total: {total_count}, Libres: {free_count}, "
                        f"Mensaje: '{message}'"
                    )
                    
                    # Usar color de la asignación si está configurado
                    if assignment.color:
                        color = assignment.color
                        logger.debug(f"Panel {panel.id} ({panel.name}), ventana {window_id}: Usando color {color} de asignación")
                    else:
                        color = 2  # Verde por defecto
                else:
                    message = "0"  # Sin datos disponibles
                    logger.warning(
                        f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                        f"No se encontraron datos de sensores para tipo '{assignment.sensor_type}' "
                        f"en parking {assignment.parking_id}"
                    )
            else:
                logger.warning(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Tipo de asignación no reconocido - display_type: '{assignment.display_type}', "
                    f"sensor_type: '{assignment.sensor_type}'"
                )
                return {'success': False, 'skipped': True}
            
            if not message:
                logger.warning(f"Panel {panel.id} ({panel.name}), ventana {window_id}: Mensaje vacío, omitiendo")
                return {'success': False, 'skipped': True}
            
            logger.info(
                f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                f"Preparado para enviar - Mensaje: '{message}', Color: {color}"
            )
            
            # Enviar mensaje al panel usando protocolo v4 (asíncrono)
            try:
                # Lanzar tarea asíncrona (no esperar respuesta inmediatamente)
                logger.debug(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Enviando mensaje '{message}' a {panel.ip}:{panel.port or 5200}"
                )
                task_id = await protocol_service.send_text_v4(
                    panel_ip=panel.ip,
                    panel_port=panel.port or 5200,
                    window_id=window_id,
                    text=message,
                    color=color,
                    font_size=2,  # Tamaño medio
                    effect=0,  # Sin efecto
                    alignment=0,  # Izquierda arriba
                    wait_for_response=False  # NO esperar respuesta inmediatamente
                )
                
                logger.debug(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Tarea {task_id} creada, esperando resultado (timeout: 30.0s)"
                )
                
                # Obtener el resultado de la tarea (con timeout aumentado para mayor latencia)
                result = await protocol_service.get_task_result(task_id, timeout=30.0)
                
                if result and result.get('success'):
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
                    
                    return {
                        'success': True,
                        'window_id': window_id,
                        'message': message
                    }
                else:
                    if result is None:
                        error_msg = 'No result received from protocol service (timeout o tarea cancelada)'
                    elif isinstance(result, dict):
                        error_msg = result.get('error', result.get('error_message', 'Unknown error'))
                        if not error_msg or error_msg == 'Unknown error':
                            # Intentar obtener más información del resultado
                            if 'success' in result and not result['success']:
                                error_msg = f"Panel returned error: {result.get('return_value', 'unknown')}"
                            else:
                                error_msg = f"Task failed: {result}"
                    else:
                        error_msg = f"Unexpected result type: {type(result).__name__}"
                    
                    logger.warning(
                        f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                        f"Error en resultado - {error_msg}"
                    )
                    logger.debug(f"Resultado completo: {result}")
                    return {
                        'success': False,
                        'window_id': window_id,
                        'error': error_msg
                    }
            except asyncio.TimeoutError as e:
                # Si el paquete se envió correctamente pero no hay respuesta,
                # considerar como éxito parcial (el panel puede haber procesado el mensaje)
                logger.warning(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Timeout esperando respuesta del panel (30s), pero el paquete se envió correctamente. "
                    f"Considerando como éxito parcial (el panel puede haber procesado el mensaje sin enviar respuesta)."
                )
                
                # Actualizar último mensaje en la tabla Panel (éxito parcial)
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
                    f"actualizada (éxito parcial, sin respuesta): {message}"
                )
                
                return {
                    'success': True,  # Considerar como éxito aunque no haya respuesta
                    'window_id': window_id,
                    'message': message,
                    'no_response': True  # Indicar que no hubo respuesta
                }
            except Exception as e:
                import traceback
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else f"{error_type} (sin mensaje)"
                full_error = f"{error_type}: {error_msg}"
                logger.error(
                    f"Panel {panel.id} ({panel.name}), ventana {window_id}: "
                    f"Error enviando mensaje - {full_error}"
                )
                logger.error(f"Traceback completo:\n{traceback.format_exc()}")
                return {
                    'success': False,
                    'window_id': window_id,
                    'error': full_error
                }
        except Exception as e:
            import traceback
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else f"{error_type} (sin mensaje)"
            full_error = f"{error_type}: {error_msg}"
            logger.error(f"Error actualizando ventana {window_id} del panel {panel.id} ({panel.name}): {full_error}")
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            # Hacer rollback para limpiar la transacción en caso de error
            try:
                self.db_session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error haciendo rollback: {rollback_error}")
            return {
                'success': False,
                'window_id': window_id,
                'error': full_error
            }
    
    async def update_type3_panel_async(self, panel_id: int) -> Dict[str, Any]:
        """
        Actualiza un panel Tipo 3 (2 ventanas con valores numéricos simples) de forma asíncrona
        Procesa ambas ventanas en paralelo
        
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
            
            # Inicializar servicio de protocolo con timeouts aumentados para procesamiento paralelo
            protocol_service = PanelProtocolService(
                max_concurrent_tasks=20,  # Aumentar para procesar más paneles en paralelo
                max_connections_per_panel=5,
                connection_timeout=10.0,  # Aumentado para mayor latencia
                read_timeout=30.0  # Aumentado significativamente para mayor latencia
            )
            
            # Actualizar ambas ventanas EN PARALELO usando asyncio.gather
            window_tasks = [
                self._update_window_async(protocol_service, panel, parking, 0),
                self._update_window_async(protocol_service, panel, parking, 1)
            ]
            
            # Esperar todas las ventanas en paralelo
            window_results = await asyncio.gather(*window_tasks, return_exceptions=True)
            
            # Procesar resultados
            windows_updated = 0
            errors = []
            
            logger.info(f"Panel {panel_id} ({panel.name}): Procesando resultados de {len(window_results)} ventanas")
            for i, result in enumerate(window_results):
                if isinstance(result, Exception):
                    error_msg = str(result)
                    logger.error(f"Panel {panel_id} ({panel.name}), ventana {i}: Excepción - {error_msg}")
                    errors.append({
                        'window_id': i,
                        'error': error_msg
                    })
                elif result.get('success'):
                    windows_updated += 1
                    logger.info(
                        f"Panel {panel_id} ({panel.name}), ventana {result.get('window_id', i)}: "
                        f"Actualizada exitosamente - Mensaje: '{result.get('message', 'N/A')}'"
                    )
                elif result.get('skipped'):
                    logger.debug(f"Panel {panel_id} ({panel.name}), ventana {i}: Omitida (sin asignación)")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.warning(
                        f"Panel {panel_id} ({panel.name}), ventana {result.get('window_id', i)}: "
                        f"Error - {error_msg}"
                    )
                    errors.append({
                        'window_id': result.get('window_id', i),
                        'error': error_msg
                    })
            
            logger.info(
                f"Panel {panel_id} ({panel.name}): "
                f"Actualización completada - {windows_updated}/2 ventanas actualizadas, "
                f"{len(errors)} errores"
            )
            
            return {
                'success': windows_updated > 0,
                'windows_updated': windows_updated,
                'total_windows': 2,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error en update_type3_panel_async {panel_id}: {e}")
            # Hacer rollback para limpiar la transacción en caso de error
            try:
                self.db_session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error haciendo rollback: {rollback_error}")
            return {'success': False, 'error': str(e)}
    
    def update_type3_panel(self, panel_id: int) -> Dict[str, Any]:
        """
        Actualiza un panel Tipo 3 (2 ventanas con valores numéricos simples)
        Wrapper síncrono que ejecuta la versión asíncrona
        
        Args:
            panel_id: ID del panel
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            # Ejecutar versión asíncrona en un nuevo event loop
            return asyncio.run(self.update_type3_panel_async(panel_id))
        except Exception as e:
            logger.error(f"Error ejecutando update_type3_panel {panel_id}: {e}")
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
            protocol_service = PanelProtocolService(
                max_concurrent_tasks=20,  # Aumentar para procesar más paneles en paralelo
                max_connections_per_panel=5,
                connection_timeout=5.0,
                read_timeout=15.0  # Aumentar timeout de lectura para procesamiento paralelo
            )
            
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
                    # Hacer rollback para limpiar la transacción en caso de error
                    try:
                        self.db_session.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Error haciendo rollback: {rollback_error}")
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
            logger.error(f"Error en update_type4_panel {panel_id}: {e}")
            # Hacer rollback para limpiar la transacción en caso de error
            try:
                self.db_session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error haciendo rollback: {rollback_error}")
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

