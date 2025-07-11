#!/usr/bin/env python3
"""
Servicio de monitorización para ejecutar automáticamente las programaciones de paneles
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import PanelSchedule, PanelScheduleLog, Parking, Panel
from panel_schedule_service import PanelScheduleService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schedule_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScheduleMonitorService:
    def __init__(self, check_interval: int = 60):
        """
        Inicializar el servicio de monitorización
        
        Args:
            check_interval: Intervalo en segundos para verificar programaciones (default: 60)
        """
        self.check_interval = check_interval
        self.engine = create_engine(DB_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.running = False
        self.thread = None
        self.executed_schedules = set()  # Para evitar ejecuciones duplicadas
        
        logger.info(f"ScheduleMonitorService inicializado con intervalo de {check_interval} segundos")
    
    def start(self):
        """Iniciar el servicio de monitorización"""
        if self.running:
            logger.warning("El servicio ya está ejecutándose")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Servicio de monitorización iniciado")
    
    def stop(self):
        """Detener el servicio de monitorización"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Servicio de monitorización detenido")
    
    def _monitor_loop(self):
        """Bucle principal de monitorización"""
        logger.info("Iniciando bucle de monitorización")
        
        while self.running:
            try:
                # Verificar y ejecutar programaciones activas
                self._check_and_execute_schedules()
                
                # Verificar programaciones que han terminado y restaurar estado
                self.check_schedule_endings()
                
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error en bucle de monitorización: {e}")
                time.sleep(self.check_interval)
    
    def _check_and_execute_schedules(self):
        """Verificar y ejecutar programaciones activas"""
        try:
            session = self.Session()
            schedule_service = PanelScheduleService(session)
            
            # Obtener todas las programaciones activas
            result = schedule_service.get_schedules(active_only=True)
            
            if not result['success']:
                logger.error(f"Error obteniendo programaciones: {result['error']}")
                session.close()
                return
            
            current_time = datetime.now().astimezone()
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
            
            for schedule_data in result['schedules']:
                try:
                    # Verificar si la programación debe ejecutarse ahora
                    if self._should_execute_schedule(schedule_data, current_time, current_time_str, current_weekday_field):
                        schedule_id = schedule_data['id']
                        
                        # Evitar ejecuciones duplicadas en el mismo minuto
                        execution_key = f"{schedule_id}_{current_time.strftime('%Y%m%d_%H%M')}"
                        
                        if execution_key not in self.executed_schedules:
                            logger.info(f"Ejecutando programación: {schedule_data['name']} (ID: {schedule_id})")
                            
                            # Obtener el objeto schedule completo
                            schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
                            if schedule:
                                # Ejecutar la programación
                                execution_result = schedule_service.execute_schedule(schedule)
                                
                                if execution_result['success']:
                                    logger.info(f"Programación {schedule_id} ejecutada exitosamente: {execution_result['panels_affected']} paneles afectados")
                                    self.executed_schedules.add(execution_key)
                                else:
                                    logger.error(f"Error ejecutando programación {schedule_id}: {execution_result['error']}")
                            
                            # Limpiar ejecuciones antiguas (más de 1 hora)
                            self._cleanup_old_executions(current_time)
                
                except Exception as e:
                    logger.error(f"Error procesando programación {schedule_data.get('id', 'unknown')}: {e}")
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error en verificación de programaciones: {e}")
            if 'session' in locals():
                session.close()
    
    def _should_execute_schedule(self, schedule_data, current_time, current_time_str, current_weekday_field):
        """Verificar si una programación debe ejecutarse en el momento actual"""
        try:
            # Verificar fechas de vigencia
            start_date_str = schedule_data['start_date']
            end_date_str = schedule_data['end_date']
            
            # Manejar diferentes formatos de fecha
            try:
                if 'T' in start_date_str:
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                else:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    start_date = start_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
                
                if 'T' in end_date_str:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                else:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    end_date = end_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
            except ValueError as e:
                logger.error(f"Error parseando fechas de programación {schedule_data.get('id', 'unknown')}: {e}")
                return False
            
            # Asegurar que current_time tenga zona horaria
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=start_date.tzinfo)
            
            # Verificar que esté dentro del rango de fechas
            if not (start_date <= current_time <= end_date):
                return False
            
            # Verificar día de la semana
            if not schedule_data.get(current_weekday_field, False):
                return False
            
            # Verificar horario
            start_time = schedule_data['start_time']
            end_time = schedule_data['end_time']
            
            if not (start_time <= current_time_str <= end_time):
                return False
            
            # Verificar que esté activa
            if not schedule_data.get('is_active', False):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando programación {schedule_data.get('id', 'unknown')}: {e}")
            return False
    
    def _cleanup_old_executions(self, current_time):
        """Limpiar ejecuciones antiguas del cache"""
        cutoff_time = current_time - timedelta(hours=1)
        cutoff_key = cutoff_time.strftime('%Y%m%d_%H%M')
        
        # Eliminar ejecuciones más antiguas que 1 hora
        old_executions = [key for key in self.executed_schedules if key.split('_')[-2:] < cutoff_key.split('_')[-2:]]
        for old_key in old_executions:
            self.executed_schedules.discard(old_key)
    
    def check_schedule_endings(self):
        """Verificar programaciones que han terminado y restaurar estado normal"""
        try:
            session = self.Session()
            schedule_service = PanelScheduleService(session)
            
            current_time = datetime.now().astimezone()
            current_time_str = current_time.strftime('%H:%M')
            current_weekday = current_time.weekday()
            
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
            
            # Buscar programaciones que acaban de terminar
            result = schedule_service.get_schedules(active_only=True)
            
            if not result['success']:
                logger.error(f"Error obteniendo programaciones para verificar finalizaciones: {result['error']}")
                session.close()
                return
            
            for schedule_data in result['schedules']:
                try:
                    # Verificar si la programación acaba de terminar
                    if self._schedule_just_ended(schedule_data, current_time, current_time_str, current_weekday_field):
                        schedule_id = schedule_data['id']
                        logger.info(f"Programación terminada: {schedule_data['name']} (ID: {schedule_id})")
                        
                        # Obtener el objeto schedule completo
                        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
                        if schedule:
                            # Finalizar la programación y restaurar estado normal
                            end_result = schedule_service.end_schedule(schedule)
                            
                            if end_result['success']:
                                logger.info(f"Programación {schedule_id} finalizada exitosamente: {end_result['panels_affected']} paneles actualizados")
                            else:
                                logger.error(f"Error finalizando programación {schedule_id}: {end_result['error']}")
                
                except Exception as e:
                    logger.error(f"Error procesando finalización de programación {schedule_data.get('id', 'unknown')}: {e}")
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error verificando finalizaciones de programaciones: {e}")
            if 'session' in locals():
                session.close()
    
    def _schedule_just_ended(self, schedule_data, current_time, current_time_str, current_weekday_field):
        """Verificar si una programación acaba de terminar (hace menos de 1 minuto)"""
        try:
            # Verificar fechas de vigencia
            start_date = datetime.fromisoformat(schedule_data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(schedule_data['end_date'].replace('Z', '+00:00'))
            
            # Asegurar que current_time tenga zona horaria
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=start_date.tzinfo)
            
            if not (start_date <= current_time <= end_date):
                return False
            
            # Verificar día de la semana
            if not schedule_data.get(current_weekday_field, False):
                return False
            
            # Verificar si el horario acaba de terminar (hace menos de 1 minuto)
            end_time = schedule_data['end_time']
            
            # Calcular el tiempo de finalización de hoy
            end_hour, end_minute = map(int, end_time.split(':'))
            today_end = current_time.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            # Verificar si acabó hace menos de 1 minuto
            time_diff = current_time - today_end
            if 0 <= time_diff.total_seconds() <= 60:  # Entre 0 y 60 segundos después de terminar
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando finalización de programación {schedule_data.get('id', 'unknown')}: {e}")
            return False
    
    def get_status(self):
        """Obtener estado del servicio de monitorización"""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'executed_schedules_count': len(self.executed_schedules),
            'last_check': datetime.now().isoformat()
        }

def main():
    """Función principal para ejecutar el servicio como script independiente"""
    import signal
    import sys
    
    # Configurar manejo de señales para parada graceful
    def signal_handler(signum, frame):
        logger.info(f"Recibida señal {signum}, parando servicio...")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Crear e iniciar el servicio
    monitor = ScheduleMonitorService(check_interval=60)  # Verificar cada minuto
    
    try:
        logger.info("Iniciando servicio de monitorización de programaciones...")
        monitor.start()
        
        # Mantener el servicio ejecutándose
        while monitor.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupción del teclado, parando servicio...")
    except Exception as e:
        logger.error(f"Error en el servicio principal: {e}")
    finally:
        monitor.stop()
        logger.info("Servicio de monitorización terminado")

if __name__ == "__main__":
    main() 