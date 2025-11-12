#!/usr/bin/env python3
"""
PanelType3And4Worker - Worker independiente para actualización de paneles Tipo 3 y Tipo 4
Sistema separado que actualiza paneles Tipo 3 (2 ventanas) y Tipo 4 (16 ventanas)
usando PanelType3And4UpdateService

Características principales:
- Worker independiente con threading propio
- Actualización periódica según intervalos de UserPanelConfig
- Usa PanelType3And4UpdateService para actualización especializada
- Respeta configuraciones de rotación y ventanas
- Gestión de errores por panel sin afectar otros
- Sistema de estadísticas integrado
- Shutdown graceful con manejo de señales
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Panel, PanelType, UserPanelConfig, UserParking
from config import DB_URL

# Configurar logging específico para el worker
logger = logging.getLogger(__name__)


class PanelType3And4Worker:
    """
    Worker independiente para actualización de paneles Tipo 3 y Tipo 4
    """
    
    def __init__(self, base_update_interval: int = 120):
        """
        Inicializar el worker de paneles Tipo 3 y 4
        
        Args:
            base_update_interval: Intervalo base en segundos (default: 120s = 2min)
        """
        self.base_update_interval = base_update_interval
        self.update_interval = base_update_interval
        
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
        
        # Estadísticas del worker thread-safe
        self._stats = {
            'cycles_completed': 0,
            'panels_processed': 0,
            'panels_updated': 0,
            'panels_failed': 0,
            'windows_updated': 0,
            'type3_panels_updated': 0,
            'type4_panels_updated': 0,
            'last_update': None,
            'average_cycle_time': 0.0,
            'errors': 0,
            'uptime_start': None
        }
        self._stats_lock = threading.Lock()
        
        # Cache de configuraciones de usuarios y última actualización por usuario
        self._user_configs = {}  # {user_id: panel_update_interval_seconds}
        self._last_update_by_user = {}  # {user_id: datetime}
        self._user_configs_lock = threading.Lock()
        self._last_config_reload = datetime.now()
        
        # Cargar configuraciones de usuarios al inicializar
        self._load_user_configs()
        
        logger.info(f"PanelType3And4Worker inicializado - Intervalo base: {base_update_interval}s")
    
    def _load_user_configs(self):
        """Cargar configuraciones de intervalos de actualización de usuarios"""
        session = self.Session()
        try:
            # Obtener todas las configuraciones de usuarios activas
            configs = session.query(UserPanelConfig).filter(
                UserPanelConfig.is_active == True
            ).all()
            
            with self._user_configs_lock:
                self._user_configs = {}
                min_interval = None
                
                for config in configs:
                    interval = config.panel_update_interval_seconds
                    self._user_configs[config.user_id] = interval
                    # Inicializar última actualización si no existe
                    if config.user_id not in self._last_update_by_user:
                        self._last_update_by_user[config.user_id] = None
                    
                    # Calcular intervalo mínimo
                    if min_interval is None or interval < min_interval:
                        min_interval = interval
                
                # Si hay configuraciones, actualizar el intervalo del worker al mínimo
                # (pero no menos de 30 segundos para evitar sobrecarga)
                if min_interval is not None:
                    recommended_interval = max(30, min_interval // 2)
                    if recommended_interval < self.update_interval:
                        logger.info(f"Ajustando intervalo del worker a {recommended_interval}s (mínimo configurado: {min_interval}s)")
                        self.update_interval = recommended_interval
            
            logger.info(f"Cargadas {len(self._user_configs)} configuraciones de usuarios para Tipo 3/4")
            
            # Si no hay configuraciones, usar valor por defecto para todos
            if not self._user_configs:
                logger.warning("No hay configuraciones de usuarios, usando intervalo por defecto (120s)")
                
        except Exception as e:
            logger.error(f"Error cargando configuraciones de usuarios: {e}")
            with self._user_configs_lock:
                self._user_configs = {}
        finally:
            session.close()
    
    def _get_user_update_interval(self, user_id: int) -> int:
        """
        Obtener intervalo de actualización para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Intervalo en segundos (por defecto 120 si no existe)
        """
        with self._user_configs_lock:
            return self._user_configs.get(user_id, 120)
    
    def _should_update_user_panels(self, user_id: int) -> bool:
        """
        Verificar si se debe actualizar los paneles de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si debe actualizarse, False en caso contrario
        """
        with self._user_configs_lock:
            interval = self._user_configs.get(user_id, 120)
            last_update = self._last_update_by_user.get(user_id)
            
            if last_update is None:
                # Primera vez, actualizar
                return True
            
            # Verificar si ha pasado el tiempo suficiente
            time_since_update = (datetime.now() - last_update).total_seconds()
            return time_since_update >= interval
    
    def _mark_user_updated(self, user_id: int):
        """
        Marcar que se ha actualizado un usuario
        
        Args:
            user_id: ID del usuario
        """
        with self._user_configs_lock:
            self._last_update_by_user[user_id] = datetime.now()
    
    def start(self):
        """Iniciar el worker en un hilo separado"""
        if self.running:
            logger.warning("Panel Type 3/4 worker ya está ejecutándose")
            return
        
        self.running = True
        
        # Actualizar estadísticas de inicio
        with self._stats_lock:
            self._stats['uptime_start'] = datetime.now()
        
        # Crear e iniciar hilo del worker
        self.worker_thread = threading.Thread(
            target=self._worker_loop, 
            daemon=True,
            name="PanelType3And4Worker"
        )
        self.worker_thread.start()
        
        logger.info(f"Panel Type 3/4 Worker iniciado - Intervalo: {self.update_interval}s")
    
    def stop(self):
        """Detener el worker de forma limpia"""
        logger.info("Deteniendo Panel Type 3/4 Worker...")
        self.running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
            
            if self.worker_thread.is_alive():
                logger.warning("Worker thread no se detuvo en el tiempo esperado")
            else:
                logger.info("Worker thread detenido correctamente")
        
        # Cerrar conexiones de base de datos
        self.engine.dispose()
        
        logger.info("Panel Type 3/4 Worker detenido")
    
    def _worker_loop(self):
        """Bucle principal del worker"""
        logger.info("Iniciando bucle principal del worker Tipo 3/4")
        
        while self.running:
            cycle_start = time.time()
            
            try:
                # Ejecutar ciclo de actualización
                self._update_all_type3_and_type4_panels()
                
                # Actualizar estadísticas del ciclo
                cycle_time = time.time() - cycle_start
                with self._stats_lock:
                    self._stats['cycles_completed'] += 1
                    self._stats['last_update'] = datetime.now()
                    
                    # Calcular tiempo promedio de ciclo
                    cycles = self._stats['cycles_completed']
                    current_avg = self._stats['average_cycle_time']
                    self._stats['average_cycle_time'] = (current_avg * (cycles - 1) + cycle_time) / cycles
                
                logger.info(f"Ciclo de actualización Tipo 3/4 completado en {cycle_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error en ciclo de actualización de paneles Tipo 3/4: {e}")
                with self._stats_lock:
                    self._stats['errors'] += 1
            
            # Esperar hasta el próximo ciclo
            sleep_time = self.update_interval
            while sleep_time > 0 and self.running:
                time.sleep(min(sleep_time, 1))
                sleep_time -= 1
        
        logger.info("Bucle principal del worker Tipo 3/4 terminado")
    
    def _update_all_type3_and_type4_panels(self):
        """Actualizar todos los paneles Tipo 3 y Tipo 4 del sistema"""
        session = self.Session()
        
        try:
            # Recargar configuraciones periódicamente (cada 5 minutos)
            if (datetime.now() - self._last_config_reload).total_seconds() > 300:
                self._load_user_configs()
                self._last_config_reload = datetime.now()
            
            # Obtener todos los paneles Tipo 3 y Tipo 4 agrupados por usuario
            panels_by_user = self._get_type3_and_type4_panels_by_user(session)
            
            if not panels_by_user:
                logger.debug("No hay paneles Tipo 3 o Tipo 4 para actualizar")
                return
            
            logger.info(f"Procesando paneles Tipo 3/4 para {len(panels_by_user)} usuarios")
            
            # Procesar paneles por usuario
            updated_users = set()
            for user_id, panels in panels_by_user.items():
                # Verificar si debe actualizarse según el intervalo del usuario
                if not self._should_update_user_panels(user_id):
                    logger.debug(f"Usuario {user_id}: omitiendo actualización (intervalo no cumplido)")
                    continue
                
                try:
                    # Actualizar paneles del usuario usando el servicio especializado
                    from panel_type4_update_service import PanelType3And4UpdateService
                    update_service = PanelType3And4UpdateService(session)
                    
                    # Actualizar solo los paneles del usuario actual EN PARALELO
                    user_stats = {
                        'panels_processed': 0,
                        'panels_updated': 0,
                        'panels_failed': 0,
                        'windows_updated': 0,
                        'type3_panels': 0,
                        'type4_panels': 0,
                        'errors': []
                    }
                    
                    # Procesar todos los paneles en paralelo usando asyncio
                    async def update_panel_async(panel):
                        """Actualiza un panel de forma asíncrona"""
                        try:
                            # Determinar tipo de panel
                            is_type3 = panel.panel_type and panel.panel_type.windows_count == 2
                            is_type4 = panel.panel_type and panel.panel_type.windows_count == 16
                            
                            # Usar la versión asíncrona si está disponible
                            if is_type3:
                                result = await update_service.update_type3_panel_async(panel.id)
                            elif is_type4:
                                # Para Tipo 4, aún no tenemos versión asíncrona, usar la síncrona
                                result = update_service.update_type4_panel(panel.id)
                            else:
                                result = {'success': False, 'error': 'Tipo de panel no soportado'}
                            
                            return {
                                'panel_id': panel.id,
                                'panel_name': panel.name,
                                'is_type3': is_type3,
                                'is_type4': is_type4,
                                'result': result
                            }
                        except Exception as e:
                            logger.error(f"Error actualizando panel {panel.id}: {e}")
                            return {
                                'panel_id': panel.id,
                                'panel_name': panel.name,
                                'is_type3': False,
                                'is_type4': False,
                                'result': {'success': False, 'error': str(e)}
                            }
                    
                    # Ejecutar todas las actualizaciones en paralelo
                    panel_tasks = [update_panel_async(panel) for panel in panels]
                    panel_results = asyncio.run(asyncio.gather(*panel_tasks, return_exceptions=True))
                    
                    # Procesar resultados
                    for panel_result in panel_results:
                        if isinstance(panel_result, Exception):
                            user_stats['panels_processed'] += 1
                            user_stats['panels_failed'] += 1
                            user_stats['errors'].append({
                                'panel_id': None,
                                'panel_name': 'Unknown',
                                'error': str(panel_result)
                            })
                        else:
                            user_stats['panels_processed'] += 1
                            
                            if panel_result['is_type3']:
                                user_stats['type3_panels'] += 1
                            elif panel_result['is_type4']:
                                user_stats['type4_panels'] += 1
                            
                            result = panel_result['result']
                            if result['success']:
                                user_stats['panels_updated'] += 1
                                user_stats['windows_updated'] += result.get('windows_updated', 0)
                            else:
                                user_stats['panels_failed'] += 1
                                user_stats['errors'].append({
                                    'panel_id': panel_result['panel_id'],
                                    'panel_name': panel_result['panel_name'],
                                    'error': result.get('error', 'Unknown error')
                                })
                    
                    stats = user_stats
                    
                    # Actualizar estadísticas globales
                    with self._stats_lock:
                        self._stats['panels_processed'] += stats['panels_processed']
                        self._stats['panels_updated'] += stats['panels_updated']
                        self._stats['panels_failed'] += stats['panels_failed']
                        self._stats['windows_updated'] += stats['windows_updated']
                        self._stats['type3_panels_updated'] += stats['type3_panels']
                        self._stats['type4_panels_updated'] += stats['type4_panels']
                        
                        if stats['errors']:
                            self._stats['errors'] += len(stats['errors'])
                    
                    # Marcar usuario como actualizado si hubo éxito
                    if stats['panels_updated'] > 0:
                        updated_users.add(user_id)
                        logger.info(
                            f"Usuario {user_id}: {stats['panels_updated']}/{stats['panels_processed']} "
                            f"paneles actualizados (Tipo 3: {stats['type3_panels']}, Tipo 4: {stats['type4_panels']})"
                        )
                    
                    if stats['panels_failed'] > 0:
                        logger.warning(
                            f"Usuario {user_id}: {stats['panels_failed']} paneles fallaron. "
                            f"Errores: {[e.get('error', 'Unknown') for e in stats['errors'][:3]]}"
                        )
                
                except Exception as e:
                    logger.error(f"Error actualizando paneles Tipo 3/4 para usuario {user_id}: {e}")
                    with self._stats_lock:
                        self._stats['errors'] += 1
            
            # Marcar usuarios como actualizados
            for user_id in updated_users:
                self._mark_user_updated(user_id)
                logger.debug(f"Usuario {user_id} marcado como actualizado (Tipo 3/4)")
        
        except Exception as e:
            logger.error(f"Error en actualización masiva de paneles Tipo 3/4: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
        
        finally:
            session.close()
    
    def _get_type3_and_type4_panels_by_user(self, session: Session) -> Dict[int, List[Panel]]:
        """
        Obtener paneles Tipo 3 y Tipo 4 agrupados por usuario
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Diccionario {user_id: [panels]}
        """
        try:
            # Obtener todos los paneles Tipo 3 y Tipo 4 activos
            panels = session.query(Panel).join(PanelType).filter(
                Panel.is_active == True,
                Panel.panel_type_id == PanelType.id,
                PanelType.windows_count.in_([2, 16])  # Tipo 3 = 2, Tipo 4 = 16
            ).all()
            
            # Agrupar por usuario a través de UserParking
            panels_by_user = {}
            for panel in panels:
                if not panel.parking_id:
                    continue
                
                # Obtener usuario del parking
                user_parking = session.query(UserParking).filter(
                    UserParking.parking_id == panel.parking_id
                ).first()
                
                user_id = user_parking.user_id if user_parking else None
                
                # Si no hay usuario, usar None como clave
                if user_id not in panels_by_user:
                    panels_by_user[user_id] = []
                
                panels_by_user[user_id].append(panel)
            
            logger.debug(f"Encontrados {len(panels)} paneles Tipo 3/4 para {len(panels_by_user)} usuarios")
            return panels_by_user
            
        except Exception as e:
            logger.error(f"Error obteniendo paneles Tipo 3/4: {e}")
            return {}
    
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
                stats['uptime_formatted'] = str(uptime).split('.')[0]
            
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
        
        logger.info("Forzando ciclo de actualización Tipo 3/4 inmediato")
        
        start_time = time.time()
        
        try:
            self._update_all_type3_and_type4_panels()
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

