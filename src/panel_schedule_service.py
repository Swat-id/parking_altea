#!/usr/bin/env python3
"""
Servicio para gestionar programaciones de paneles
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from models import PanelSchedule, PanelScheduleLog, Parking, Panel
import threading
import concurrent.futures
from panel_communication_service import PanelCommunicationService

logger = logging.getLogger(__name__)

class PanelScheduleService:
    def __init__(self, session: Session, panel_service_url: str = None):
        self.session = session
        # Usar URL por defecto si no se proporciona
        if panel_service_url is None:
            panel_service_url = "http://localhost:8888/api/v1/panels/send"
        self.panel_communication_service = PanelCommunicationService(panel_service_url)
    
    def create_schedule(self, schedule_data: dict) -> dict:
        """Crear una nueva programación"""
        try:
            # Validar datos requeridos
            required_fields = ['parking_id', 'name', 'start_date', 'end_date', 'start_time', 'end_time', 'message']
            for field in required_fields:
                if field not in schedule_data or not schedule_data[field]:
                    return {'success': False, 'error': f'Campo requerido faltante o vacío: {field}'}
            
            # Asegurar que las fechas tengan zona horaria
            start_date = schedule_data.get('start_date')
            end_date = schedule_data.get('end_date')
            
            try:
                if isinstance(start_date, str):
                    # Manejar diferentes formatos de fecha
                    if 'T' in start_date:
                        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    else:
                        start_date = datetime.strptime(start_date, '%Y-%m-%d')
                        start_date = start_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
                
                if isinstance(end_date, str):
                    # Manejar diferentes formatos de fecha
                    if 'T' in end_date:
                        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    else:
                        end_date = datetime.strptime(end_date, '%Y-%m-%d')
                        end_date = end_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
            except ValueError as e:
                return {'success': False, 'error': f'Formato de fecha inválido: {str(e)}'}
            
            # Validar que al menos un día de la semana esté seleccionado
            weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            if not any(schedule_data.get(day, False) for day in weekdays):
                return {'success': False, 'error': 'Debe seleccionar al menos un día de la semana'}
            
            # Validar que la fecha de inicio no sea posterior a la fecha de fin
            if start_date > end_date:
                return {'success': False, 'error': 'La fecha de inicio no puede ser posterior a la fecha de fin'}
            
            # Crear la programación
            schedule = PanelSchedule(
                parking_id=schedule_data['parking_id'],
                user_id=schedule_data.get('user_id', 1),
                name=schedule_data['name'],
                description=schedule_data.get('description', ''),
                start_date=start_date,
                end_date=end_date,
                start_time=schedule_data['start_time'],
                end_time=schedule_data['end_time'],
                monday=schedule_data.get('monday', False),
                tuesday=schedule_data.get('tuesday', False),
                wednesday=schedule_data.get('wednesday', False),
                thursday=schedule_data.get('thursday', False),
                friday=schedule_data.get('friday', False),
                saturday=schedule_data.get('saturday', False),
                sunday=schedule_data.get('sunday', False),
                message=schedule_data['message'],
                color=schedule_data.get('color', 2),
                font_size=schedule_data.get('font_size', 16),
                effect=schedule_data.get('effect', 'static'),
                is_active=schedule_data.get('is_active', True),
                priority=schedule_data.get('priority', 1)
            )
            
            self.session.add(schedule)
            self.session.commit()
            
            logger.info(f"Programación creada: {schedule.id} - {schedule.name}")
            
            # VERIFICAR SI LA PROGRAMACIÓN DEBE EJECUTARSE INMEDIATAMENTE
            # Si la programación está activa y es operativa en el momento actual, ejecutarla
            if schedule.is_active:
                current_time = datetime.now().replace(tzinfo=start_date.tzinfo)
                current_time_str = current_time.strftime('%H:%M')
                current_weekday = current_time.weekday()
                
                # Mapear weekday a campos de la base de datos
                weekday_fields = {
                    0: 'monday',
                    1: 'tuesday', 
                    2: 'wednesday',
                    3: 'thursday',
                    4: 'friday',
                    5: 'saturday',
                    6: 'sunday'
                }
                
                current_weekday_field = weekday_fields.get(current_weekday, 'monday')
                
                # Verificar si debe ejecutarse ahora
                should_execute_now = (
                    schedule.start_date <= current_time <= schedule.end_date and
                    getattr(schedule, current_weekday_field, False) and
                    schedule.start_time <= current_time_str <= schedule.end_time
                )
                
                if should_execute_now:
                    logger.info(f"Programación {schedule.id} es operativa ahora, ejecutando automáticamente")
                    execution_result = self.execute_schedule(schedule)
                    
                    if execution_result['success']:
                        logger.info(f"Programación {schedule.id} ejecutada automáticamente: {execution_result['panels_affected']} paneles afectados")
                        return {
                            'success': True, 
                            'schedule_id': schedule.id,
                            'auto_executed': True,
                            'panels_affected': execution_result['panels_affected']
                        }
                    else:
                        logger.error(f"Error ejecutando programación {schedule.id} automáticamente: {execution_result['error']}")
                        return {
                            'success': True, 
                            'schedule_id': schedule.id,
                            'auto_executed': False,
                            'execution_error': execution_result['error']
                        }
                else:
                    logger.info(f"Programación {schedule.id} no es operativa ahora, se ejecutará en su horario programado")
            
            return {'success': True, 'schedule_id': schedule.id, 'auto_executed': False}
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creando programación: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_schedules(self, parking_id: int = None, active_only: bool = True) -> dict:
        """Obtener programaciones"""
        try:
            query = self.session.query(PanelSchedule)
            
            if parking_id:
                query = query.filter(PanelSchedule.parking_id == parking_id)
            
            if active_only:
                query = query.filter(PanelSchedule.is_active == True)
            
            schedules = query.order_by(PanelSchedule.priority.desc(), PanelSchedule.created_at.desc()).all()
            
            result = []
            for schedule in schedules:
                result.append({
                    'id': schedule.id,
                    'parking_id': schedule.parking_id,
                    'user_id': schedule.user_id,
                    'name': schedule.name,
                    'description': schedule.description,
                    'start_date': schedule.start_date.isoformat(),
                    'end_date': schedule.end_date.isoformat(),
                    'start_time': schedule.start_time,
                    'end_time': schedule.end_time,
                    'monday': schedule.monday,
                    'tuesday': schedule.tuesday,
                    'wednesday': schedule.wednesday,
                    'thursday': schedule.thursday,
                    'friday': schedule.friday,
                    'saturday': schedule.saturday,
                    'sunday': schedule.sunday,
                    'message': schedule.message,
                    'color': schedule.color,
                    'font_size': schedule.font_size,
                    'effect': schedule.effect,
                    'is_active': schedule.is_active,
                    'priority': schedule.priority,
                    'created_at': schedule.created_at.isoformat(),
                    'updated_at': schedule.updated_at.isoformat()
                })
            
            return {'success': True, 'schedules': result}
            
        except Exception as e:
            logger.error(f"Error obteniendo programaciones: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_schedule(self, schedule_id: int, schedule_data: dict) -> dict:
        """Actualizar una programación"""
        try:
            schedule = self.session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
            if not schedule:
                return {'success': False, 'error': 'Programación no encontrada'}
            
            # Actualizar campos
            for field, value in schedule_data.items():
                if hasattr(schedule, field):
                    if field in ['start_date', 'end_date'] and isinstance(value, str):
                        setattr(schedule, field, datetime.fromisoformat(value))
                    else:
                        setattr(schedule, field, value)
            
            schedule.updated_at = datetime.now()
            self.session.commit()
            
            logger.info(f"Programación actualizada: {schedule_id}")
            
            # AUTO-EJECUTAR: Si la programación está activa, ejecutarla inmediatamente
            if schedule.is_active:
                execution_result = self.execute_schedule(schedule)
                if execution_result['success']:
                    logger.info(f"Programación {schedule_id} ejecutada automáticamente después de actualizar")
                    return {
                        'success': True, 
                        'auto_executed': True,
                        'panels_affected': execution_result.get('panels_affected', 0)
                    }
                else:
                    logger.warning(f"Error auto-ejecutando programación {schedule_id}: {execution_result.get('error')}")
                    return {
                        'success': True, 
                        'auto_executed': False,
                        'execution_error': execution_result.get('error')
                    }
            
            return {'success': True, 'auto_executed': False}
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error actualizando programación: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_schedule_thread_safe(self, schedule: PanelSchedule) -> dict:
        """Ejecutar una programación de forma thread-safe"""
        try:
            # Crear nueva sesión para este hilo
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from config import DB_URL
            
            engine = create_engine(DB_URL)
            SessionLocal = sessionmaker(bind=engine)
            local_session = SessionLocal()
            
            try:
                # Obtener paneles del parking (solo los ONLINE para eficiencia)
                panels = local_session.query(Panel).filter(
                    and_(
                        Panel.parking_id == schedule.parking_id,
                        Panel.status == 'ONLINE'  # Solo paneles online para evitar timeouts
                    )
                ).all()
                
                if not panels:
                    return {'success': False, 'error': 'No hay paneles online para este parking'}
                
                # Crear servicio de comunicación con timeout optimizado
                panel_service = PanelCommunicationService(timeout=3, retry_attempts=1)
                
                success_count = 0
                for panel in panels:
                    try:
                        result = panel_service.send_custom_text(
                            panel_ip=panel.ip,
                            text=schedule.message,
                            color=schedule.color,
                            font_size=2,
                            effect=self._get_effect_code(schedule.effect)
                        )
                        if result.get('success'):
                            success_count += 1
                            # Actualizar panel en sesión local
                            panel.last_message = schedule.message
                            panel.last_update = datetime.now()
                    except Exception as e:
                        logger.warning(f"Error enviando a panel {panel.id}: {e}")
                
                # Registrar log
                log = PanelScheduleLog(
                    schedule_id=schedule.id,
                    parking_id=schedule.parking_id,
                    execution_type='started',
                    message_sent=schedule.message,
                    panels_affected=success_count
                )
                local_session.add(log)
                local_session.commit()
                
                return {
                    'success': True,
                    'panels_affected': success_count,
                    'schedule_id': schedule.id,
                    'schedule_name': schedule.name
                }
                
            finally:
                local_session.close()
                
        except Exception as e:
            logger.error(f"Error ejecutando programación {schedule.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'schedule_id': schedule.id,
                'schedule_name': schedule.name
            }

    def execute_all_active_schedules(self) -> dict:
        """Ejecutar todas las programaciones activas en paralelo"""
        try:
            # Obtener todas las programaciones activas
            active_schedules = self.session.query(PanelSchedule).filter(
                PanelSchedule.is_active == True
            ).all()
            
            if not active_schedules:
                return {'success': True, 'message': 'No hay programaciones activas para ejecutar', 'schedules_executed': 0}
            
            logger.info(f"🚀 Iniciando ejecución paralela de {len(active_schedules)} programaciones")
            
            # Ejecutar en paralelo con máximo 5 hilos concurrentes
            executed_count = 0
            failed_count = 0
            total_panels_affected = 0
            execution_details = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Enviar todas las tareas
                future_to_schedule = {
                    executor.submit(self._execute_schedule_thread_safe, schedule): schedule 
                    for schedule in active_schedules
                }
                
                # Recoger resultados con timeout de 15 segundos por programación
                for future in concurrent.futures.as_completed(future_to_schedule, timeout=120):
                    try:
                        result = future.result(timeout=15)  # 15s max por programación
                        
                        if result['success']:
                            executed_count += 1
                            panels_affected = result.get('panels_affected', 0)
                            total_panels_affected += panels_affected
                            execution_details.append({
                                'schedule_id': result['schedule_id'],
                                'schedule_name': result['schedule_name'],
                                'status': 'success',
                                'panels_affected': panels_affected
                            })
                            logger.info(f"✅ Programación '{result['schedule_name']}' ejecutada ({panels_affected} paneles)")
                        else:
                            failed_count += 1
                            execution_details.append({
                                'schedule_id': result['schedule_id'],
                                'schedule_name': result['schedule_name'],
                                'status': 'failed',
                                'error': result.get('error', 'Error desconocido')
                            })
                            logger.warning(f"⚠️ Error programación '{result['schedule_name']}': {result.get('error')}")
                            
                    except concurrent.futures.TimeoutError:
                        schedule = future_to_schedule[future]
                        failed_count += 1
                        execution_details.append({
                            'schedule_id': schedule.id,
                            'schedule_name': schedule.name,
                            'status': 'failed',
                            'error': 'Timeout de 15 segundos excedido'
                        })
                        logger.error(f"⏰ Timeout programación '{schedule.name}'")
                    except Exception as e:
                        schedule = future_to_schedule[future]
                        failed_count += 1
                        execution_details.append({
                            'schedule_id': schedule.id,
                            'schedule_name': schedule.name,
                            'status': 'failed',
                            'error': str(e)
                        })
                        logger.error(f"❌ Excepción ejecutando programación '{schedule.name}': {e}")
            
            logger.info(f"🔄 Ejecución masiva completada: {executed_count} exitosas, {failed_count} fallidas, {total_panels_affected} paneles afectados")
            
            return {
                'success': True,
                'schedules_executed': executed_count,
                'schedules_failed': failed_count,
                'total_schedules': len(active_schedules),
                'total_panels_affected': total_panels_affected,
                'execution_details': execution_details
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando todas las programaciones: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_schedule(self, schedule_id: int) -> dict:
        """Eliminar una programación"""
        try:
            schedule = self.session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
            if not schedule:
                return {'success': False, 'error': 'Programación no encontrada'}
            
            self.session.delete(schedule)
            self.session.commit()
            
            logger.info(f"Programación eliminada: {schedule_id}")
            return {'success': True}
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error eliminando programación: {e}")
            return {'success': False, 'error': str(e)}
    
    def toggle_schedule(self, schedule_id: int) -> dict:
        """Activar/desactivar una programación"""
        try:
            schedule = self.session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
            if not schedule:
                return {'success': False, 'error': 'Programación no encontrada'}
            
            schedule.is_active = not schedule.is_active
            schedule.updated_at = datetime.now()
            self.session.commit()
            
            status = "activada" if schedule.is_active else "desactivada"
            logger.info(f"Programación {status}: {schedule_id}")
            return {'success': True, 'is_active': schedule.is_active}
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cambiando estado de programación: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_active_schedules_for_parking(self, parking_id: int) -> list:
        """Obtener programaciones activas para un parking en el momento actual"""
        try:
            now = datetime.now().astimezone()
            current_time = now.strftime('%H:%M')
            current_weekday = now.weekday()  # 0=lunes, 6=domingo
            
            # Mapear weekday a campos de la base de datos
            weekday_fields = {
                0: PanelSchedule.monday,
                1: PanelSchedule.tuesday,
                2: PanelSchedule.wednesday,
                3: PanelSchedule.thursday,
                4: PanelSchedule.friday,
                5: PanelSchedule.saturday,
                6: PanelSchedule.sunday
            }
            
            current_weekday_field = weekday_fields.get(current_weekday, PanelSchedule.monday)
            
            # Obtener programaciones y filtrar por zona horaria después
            schedules = self.session.query(PanelSchedule).filter(
                and_(
                    PanelSchedule.parking_id == parking_id,
                    PanelSchedule.is_active == True,
                    current_weekday_field == True,
                    PanelSchedule.start_time <= current_time,
                    PanelSchedule.end_time >= current_time
                )
            ).order_by(PanelSchedule.priority.desc()).all()
            
            # Filtrar por fechas con zona horaria
            active_schedules = []
            for schedule in schedules:
                try:
                    # Asegurar que las fechas tengan zona horaria
                    start_date = schedule.start_date
                    end_date = schedule.end_date
                    
                    if start_date.tzinfo is None:
                        start_date = start_date.replace(tzinfo=now.tzinfo)
                    if end_date.tzinfo is None:
                        end_date = end_date.replace(tzinfo=now.tzinfo)
                    
                    if start_date <= now <= end_date:
                        active_schedules.append(schedule)
                except Exception as e:
                    logger.error(f"Error verificando fechas de programación {schedule.id}: {e}")
                    continue
            
            return active_schedules
            
        except Exception as e:
            logger.error(f"Error obteniendo programaciones activas: {e}")
            return []
    
    def execute_schedule(self, schedule: PanelSchedule) -> dict:
        """Ejecutar una programación enviando el mensaje a los paneles"""
        try:
            # Obtener paneles del parking (todos, no solo los online)
            panels = self.session.query(Panel).filter(
                Panel.parking_id == schedule.parking_id
            ).all()
            
            if not panels:
                return {'success': False, 'error': 'No hay paneles configurados para este parking'}
            
            # Enviar mensaje a todos los paneles
            success_count = 0
            for panel in panels:
                try:
                    result = self.panel_communication_service.send_custom_text(
                        panel_ip=panel.ip,
                        text=schedule.message,
                        color=schedule.color,
                        font_size=2,  # Código 2 = 16 píxeles (valor correcto para el protocolo)
                        effect=self._get_effect_code(schedule.effect)
                    )
                    if result.get('success'):
                        success_count += 1
                        # Actualizar el último mensaje del panel
                        panel.last_message = schedule.message
                        panel.last_update = datetime.now()
                        panel.status = 'ONLINE'
                except Exception as e:
                    logger.error(f"Error enviando mensaje a panel {panel.id}: {e}")
            
            # Registrar log de ejecución
            log = PanelScheduleLog(
                schedule_id=schedule.id,
                parking_id=schedule.parking_id,
                execution_type='started',
                message_sent=schedule.message,
                panels_affected=success_count
            )
            self.session.add(log)
            self.session.commit()
            
            logger.info(f"Programación ejecutada: {schedule.id} - {success_count}/{len(panels)} paneles")
            return {'success': True, 'panels_affected': success_count}
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error ejecutando programación: {e}")
            return {'success': False, 'error': str(e)}
    
    def end_schedule(self, schedule: PanelSchedule) -> dict:
        """Finalizar una programación restaurando el estado del parking"""
        try:
            # Obtener paneles del parking (todos, no solo los online)
            panels = self.session.query(Panel).filter(
                Panel.parking_id == schedule.parking_id
            ).all()
            
            if not panels:
                return {'success': False, 'error': 'No hay paneles configurados para este parking'}
            
            # Obtener estado actual del parking
            parking = self.session.query(Parking).filter(Parking.id == schedule.parking_id).first()
            if not parking:
                return {'success': False, 'error': 'Parking no encontrado'}
            
            # CORRECCIÓN: Usar la misma lógica que camera_server.py
            occ = parking.current_occupancy
            free = parking.max_capacity - occ
            
            if free < 0 or occ > parking.max_capacity:
                message = "COMPLET"
                color = 1  # Rojo
            elif free <= parking.threshold_full:
                message = "COMPLET"
                color = 1  # Rojo
            elif free <= parking.threshold_dense:
                message = "DENS"
                color = 3  # Amarillo
            else:
                message = "LLIURE"
                color = 2  # Verde
            
            # Enviar mensaje de estado a todos los paneles
            success_count = 0
            for panel in panels:
                try:
                    result = self.panel_communication_service.send_custom_text(
                        panel_ip=panel.ip,
                        text=message,
                        color=color,
                        font_size=2,  # Código 2 = 16 píxeles
                        effect=2  # Efecto estático (valor correcto)
                    )
                    if result.get('success'):
                        success_count += 1
                        # Actualizar el último mensaje del panel con el estado
                        panel.last_message = message
                        panel.last_update = datetime.now()
                        panel.status = 'ONLINE'
                except Exception as e:
                    logger.error(f"Error enviando mensaje de estado a panel {panel.id}: {e}")
            
            # Registrar log de finalización
            log = PanelScheduleLog(
                schedule_id=schedule.id,
                parking_id=schedule.parking_id,
                execution_type='ended',
                message_sent=message,
                panels_affected=success_count
            )
            self.session.add(log)
            self.session.commit()
            
            logger.info(f"Programación finalizada: {schedule.id} - {success_count}/{len(panels)} paneles")
            return {'success': True, 'panels_affected': success_count}
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error finalizando programación: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_effect_code(self, effect: str) -> int:
        """Convertir efecto de texto a código numérico"""
        effect_codes = {
            'static': 2,  # Fijo para protocolo antiguo
            'scroll_left': 12,  # Scroll para protocolo antiguo
            'scroll_right': 12,  # Scroll para protocolo antiguo
            'center': 2,  # Fijo para protocolo antiguo
            'fijo': 2,  # Fijo para protocolo antiguo
            'scroll': 12  # Scroll para protocolo antiguo
        }
        return effect_codes.get(effect, 2)  # Fijo por defecto
    
    def get_schedule_logs(self, schedule_id: int = None, parking_id: int = None, limit: int = 100) -> dict:
        """Obtener logs de programaciones"""
        try:
            query = self.session.query(PanelScheduleLog)
            
            if schedule_id:
                query = query.filter(PanelScheduleLog.schedule_id == schedule_id)
            
            if parking_id:
                query = query.filter(PanelScheduleLog.parking_id == parking_id)
            
            logs = query.order_by(PanelScheduleLog.executed_at.desc()).limit(limit).all()
            
            result = []
            for log in logs:
                result.append({
                    'id': log.id,
                    'schedule_id': log.schedule_id,
                    'parking_id': log.parking_id,
                    'execution_type': log.execution_type,
                    'message_sent': log.message_sent,
                    'panels_affected': log.panels_affected,
                    'executed_at': log.executed_at.isoformat()
                })
            
            return {'success': True, 'logs': result}
            
        except Exception as e:
            logger.error(f"Error obteniendo logs de programaciones: {e}")
            return {'success': False, 'error': str(e)} 