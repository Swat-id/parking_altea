#!/usr/bin/env python3
"""
Métodos de actualización de paneles para PanelUpdateWorker
Incluye lógica de programaciones activas y envío paralelo a paneles
"""

import time
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Panel, PanelSchedule
from panel_update_worker import PanelUpdateResult, ParkingUpdateResult

logger = logging.getLogger(__name__)


class PanelUpdateMethods:
    """Métodos de actualización para el worker de paneles"""
    
    @staticmethod
    def update_parking_panels(worker_instance, parking_data: Dict[str, Any]) -> Optional[ParkingUpdateResult]:
        """
        Actualizar paneles de un parking específico
        
        Args:
            worker_instance: Instancia del worker (para acceder a panel_service)
            parking_data: Datos del parking
            
        Returns:
            ParkingUpdateResult con resultado de la actualización
        """
        session = worker_instance.Session()
        start_time = time.time()
        
        try:
            parking_id = parking_data['id']
            parking_name = parking_data['name']
            
            logger.debug(f"Actualizando paneles del parking {parking_name} (ID: {parking_id})")
            
            # 1. Verificar programaciones activas
            active_schedule = PanelUpdateMethods._get_active_schedule(session, parking_id)
            
            if active_schedule:
                # Enviar mensaje de programación
                message = active_schedule['message']
                color = active_schedule['color']
                effect_str = active_schedule['effect']
                message_type = 'schedule'
                
                # Convertir efecto string a código numérico
                # El código se convertirá según el protocolo del panel en send_custom_text
                effect_map = {
                    'static': 2,      # Se mapeará a 11 (scroll) para protocolo nuevo
                    'center': 2,
                    'fijo': 2,
                    'scroll_left': 14,  # Continuous scroll left para protocolo nuevo
                    'scroll_right': 15, # Continuous scroll right para protocolo nuevo
                    'scroll': 14
                }
                effect = effect_map.get(effect_str, 2)  # Por defecto fijo
                
                logger.info(f"[SCHEDULE] Enviando programación activa a {parking_name}: '{message}' (efecto: {effect_str} -> {effect})")
                
            elif parking_data['fixed_message_flag']:
                # Mantener mensaje actual si está fijado
                logger.debug(f"Parking {parking_name} tiene mensaje fijo - omitiendo actualización")
                return ParkingUpdateResult(
                    parking_id=parking_id,
                    parking_name=parking_name,
                    message_type='fixed',
                    message_sent='(mensaje fijo mantenido)',
                    panels_total=0,
                    panels_updated=0,
                    panels_failed=0,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
            else:
                # Enviar estado de ocupación
                message, color = PanelUpdateMethods._calculate_occupancy_message(parking_data)
                effect = 2  # Fijo
                message_type = 'occupancy'
                
                logger.debug(f"Enviando estado de ocupación a {parking_name}: '{message}' ({parking_data['status']})")
            
            # 2. Obtener paneles del parking (todos los activos, independientemente del estado)
            # EXCLUIR Tipo 3 (2 ventanas) y Tipo 4 (16 ventanas) - tienen worker separado
            from models import PanelType
            from sqlalchemy import or_
            
            # Obtener paneles que NO son Tipo 3 ni Tipo 4
            # Incluir: Tipo 1, Tipo 2, y paneles sin tipo asignado (compatibilidad)
            panels = session.query(Panel).outerjoin(PanelType, Panel.panel_type_id == PanelType.id).filter(
                Panel.parking_id == parking_id,
                Panel.is_active == True,  # Solo paneles activos en configuración
                or_(
                    Panel.panel_type_id.is_(None),  # Paneles sin tipo (compatibilidad)
                    ~PanelType.windows_count.in_([2, 16])  # Excluir Tipo 3 (2 ventanas) y Tipo 4 (16 ventanas)
                )
            ).all()
            
            if not panels:
                logger.warning(f"No hay paneles activos en configuración para el parking {parking_name}")
                return ParkingUpdateResult(
                    parking_id=parking_id,
                    parking_name=parking_name,
                    message_type=message_type,
                    message_sent=message,
                    panels_total=0,
                    panels_updated=0,
                    panels_failed=0,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # 3. Actualizar paneles en paralelo
            panel_results = PanelUpdateMethods._send_to_panels_parallel(
                worker_instance.panel_service, panels, message, color, effect, 
                max_workers=worker_instance.max_panel_workers
            )
            
            # 4. Actualizar estado de paneles en BD
            PanelUpdateMethods._update_panel_status_in_db(session, panel_results, message)
            
            # 5. Commit de cambios
            session.commit()
            
            # Calcular estadísticas del resultado
            successful_panels = sum(1 for r in panel_results if r.success)
            failed_panels = len(panel_results) - successful_panels
            execution_time = (time.time() - start_time) * 1000
            
            # Preparar errores si los hay
            errors = [r.error for r in panel_results if not r.success and r.error] if failed_panels > 0 else None
            
            logger.info(f"Parking {parking_name}: {successful_panels}/{len(panels)} paneles actualizados ({message_type})")
            
            if failed_panels > 0:
                logger.warning(f"Parking {parking_name}: {failed_panels} paneles fallaron")
            
            return ParkingUpdateResult(
                parking_id=parking_id,
                parking_name=parking_name,
                message_type=message_type,
                message_sent=message,
                panels_total=len(panels),
                panels_updated=successful_panels,
                panels_failed=failed_panels,
                execution_time_ms=execution_time,
                active_schedule=active_schedule,
                errors=errors
            )
            
        except Exception as e:
            session.rollback()
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Error actualizando paneles del parking {parking_data['name']}: {e}")
            
            return ParkingUpdateResult(
                parking_id=parking_data['id'],
                parking_name=parking_data['name'],
                message_type='error',
                message_sent='',
                panels_total=0,
                panels_updated=0,
                panels_failed=1,
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
        
        finally:
            session.close()
    
    @staticmethod
    def _get_active_schedule(session: Session, parking_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener programación activa para un parking
        
        Args:
            session: Sesión de base de datos
            parking_id: ID del parking
            
        Returns:
            Diccionario con datos de la programación activa o None
        """
        try:
            # Usar zona horaria Europa/Madrid consistente
            from timezone_utils import get_madrid_now, get_weekday_field
            
            now = get_madrid_now()
            current_time = now.time()
            current_day_column = get_weekday_field(now)
            
            # Construir consulta SQL dinámica para el día actual
            query = text(f"""
                SELECT id, name, message, color, effect, priority
                FROM panel_schedules
                WHERE parking_id = :parking_id
                AND is_active = true
                AND (start_date IS NULL OR start_date <= :current_date)
                AND (end_date IS NULL OR end_date >= :current_date)
                AND (start_time IS NULL OR start_time::time <= :current_time)
                AND (end_time IS NULL OR end_time::time >= :current_time)
                AND {current_day_column} = true
                ORDER BY priority DESC, id ASC
                LIMIT 1
            """)
            
            result = session.execute(query, {
                'parking_id': parking_id,
                'current_date': now.date(),
                'current_time': current_time
            }).fetchone()
            
            if result:
                schedule = {
                    'id': result[0],
                    'name': result[1],
                    'message': result[2],
                    'color': result[3],
                    'effect': result[4],
                    'priority': result[5]
                }
                
                logger.debug(f"Programación activa encontrada para parking {parking_id}: '{schedule['name']}'")
                return schedule
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo programación activa para parking {parking_id}: {e}")
            return None
    
    @staticmethod
    def _calculate_occupancy_message(parking_data: Dict[str, Any]) -> tuple[str, int]:
        """
        Calcular mensaje y color según configuración del parking con validación robusta
        
        Args:
            parking_data: Datos del parking
            
        Returns:
            Tupla (mensaje, color_code)
        """
        occupancy = parking_data['current_occupancy']
        max_capacity = parking_data['max_capacity']
        status = parking_data['status']
        message_type = parking_data.get('message_type', 'ESTADO')  # NUEVO: Configuración por parking
        
        # VALIDACIÓN ROBUSTA DE DATOS
        # Asegurar que max_capacity sea positivo
        if max_capacity <= 0:
            logger.warning(f"Parking {parking_data.get('name', 'unknown')} tiene max_capacity inválido: {max_capacity}")
            max_capacity = 1  # Valor mínimo para evitar división por cero
        
        # Asegurar que occupancy esté en rango válido [0, max_capacity]
        original_occupancy = occupancy
        occupancy = max(0, min(occupancy, max_capacity))
        
        if original_occupancy != occupancy:
            logger.warning(f"Parking {parking_data.get('name', 'unknown')}: occupancy corregido de {original_occupancy} a {occupancy} (max: {max_capacity})")
        
        # Calcular plazas libres con validación
        free_spaces = max_capacity - occupancy
        
        # Doble validación de seguridad para plazas libres
        free_spaces = max(0, min(free_spaces, max_capacity))
        
        if message_type == 'PLAZAS_LIBRES':
            # Opción: Solo número de plazas libres
            if status == 'COMPLETO' or free_spaces <= 0:
                return "0", 1  # ROJO
            elif status == 'DENSO':
                return str(free_spaces), 3  # AMARILLO
            else:  # LIBRE
                return str(free_spaces), 2  # VERDE
        else:
            # Opción: Estado en valenciano (por defecto)
            if status == 'COMPLETO' or free_spaces <= 0:
                return "COMPLET", 1  # ROJO
            elif status == 'DENSO':
                return "DENS", 3  # AMARILLO
            else:  # LIBRE
                return "LLIURE", 2  # VERDE
    
    @staticmethod
    def _verify_panel_connectivity(panel: Panel) -> bool:
        """
        Verificar conectividad de panel antes de enviar mensaje
        
        Args:
            panel: Panel a verificar
            
        Returns:
            True si el panel está online, False si está offline
        """
        try:
            from panel_client import ping_panel
            
            # Realizar ping al panel
            is_online = ping_panel(panel.ip)
            
            # Actualizar estado si cambió
            current_status_online = (panel.status == 'ONLINE')
            
            if is_online != current_status_online:
                logger.info(f"Panel {panel.id} ({panel.ip}) cambió estado: {panel.status} → {'ONLINE' if is_online else 'OFFLINE'}")
                
                # Actualizar estado en base de datos
                from config import DB_URL
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                
                engine = create_engine(DB_URL)
                Session = sessionmaker(bind=engine)
                session = Session()
                
                try:
                    session.execute(text("""
                        UPDATE panels 
                        SET status = :status, last_update = NOW()
                        WHERE id = :panel_id
                    """), {
                        'status': 'ONLINE' if is_online else 'OFFLINE',
                        'panel_id': panel.id
                    })
                    session.commit()
                    
                    # Actualizar el objeto panel en memoria
                    panel.status = 'ONLINE' if is_online else 'OFFLINE'
                    
                except Exception as e:
                    logger.error(f"Error actualizando estado de panel {panel.id}: {e}")
                    session.rollback()
                finally:
                    session.close()
            
            return is_online
            
        except Exception as e:
            logger.error(f"Error verificando conectividad panel {panel.id} ({panel.ip}): {e}")
            return False
    
    @staticmethod
    def _send_to_panels_parallel(panel_service, panels: List[Panel], message: str, 
                               color: int, effect: int, max_workers: int = 10, 
                               timeout_per_panel: int = 45) -> List[PanelUpdateResult]:
        """
        Enviar mensaje a paneles en paralelo con timeouts individuales
        
        Args:
            panel_service: Servicio de comunicación con paneles
            panels: Lista de paneles
            message: Mensaje a enviar
            color: Código de color
            effect: Código de efecto
            max_workers: Máximo workers paralelos
            timeout_per_panel: Timeout en segundos por panel
            
        Returns:
            Lista de PanelUpdateResult
        """
        def send_to_single_panel(panel: Panel) -> PanelUpdateResult:
            """Enviar mensaje a un panel individual"""
            start_time = time.time()
            
            try:
                result = panel_service.send_custom_text(
                    panel_ip=panel.ip,
                    text=message,
                    color=color,
                    font_size=2,  # Tamaño estándar
                    effect=effect
                )
                
                response_time = (time.time() - start_time) * 1000
                
                return PanelUpdateResult(
                    panel_id=panel.id,
                    panel_ip=panel.ip,
                    success=result.get('success', False),
                    message=result.get('message', ''),
                    response_time_ms=response_time,
                    error=None if result.get('success', False) else result.get('message', 'Unknown error')
                )
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                
                return PanelUpdateResult(
                    panel_id=panel.id,
                    panel_ip=panel.ip,
                    success=False,
                    message='',
                    response_time_ms=response_time,
                    error=str(e)
                )
        
        # NUEVA LÓGICA: Verificar conectividad antes de enviar
        results = []
        online_panels = []
        offline_panels = []
        
        logger.info(f"Verificando conectividad de {len(panels)} paneles antes de enviar mensaje...")
        
        # Verificar conectividad de todos los paneles primero
        for panel in panels:
            if PanelUpdateMethods._verify_panel_connectivity(panel):
                online_panels.append(panel)
            else:
                offline_panels.append(panel)
                # Crear resultado de fallo para panel offline
                results.append(PanelUpdateResult(
                    panel_id=panel.id,
                    panel_ip=panel.ip,
                    success=False,
                    message='Panel offline - ping failed',
                    response_time_ms=0,
                    error='Panel not reachable via ping'
                ))
        
        logger.info(f"Paneles online: {len(online_panels)}, offline: {len(offline_panels)}")
        
        # Continuar solo con paneles online
        if not online_panels:
            logger.warning("No hay paneles online para actualizar")
            return results
        
        # Enviar solo a paneles online
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear futures solo para paneles online
            futures = {executor.submit(send_to_single_panel, panel): panel for panel in online_panels}
            
            # Recoger resultados con timeout total
            total_timeout = timeout_per_panel + 5  # Timeout total un poco mayor
            
            for future in as_completed(futures, timeout=total_timeout):
                try:
                    result = future.result(timeout=1)  # Timeout para obtener resultado
                    results.append(result)
                    
                    if result.success:
                        logger.debug(f"Panel {result.panel_ip} actualizado OK ({result.response_time_ms:.0f}ms)")
                    else:
                        logger.warning(f"Panel {result.panel_ip} falló: {result.error}")
                
                except FutureTimeoutError:
                    panel = futures[future]
                    logger.error(f"Timeout enviando a panel {panel.ip}")
                    
                    results.append(PanelUpdateResult(
                        panel_id=panel.id,
                        panel_ip=panel.ip,
                        success=False,
                        message='',
                        response_time_ms=timeout_per_panel * 1000,
                        error=f"Timeout after {timeout_per_panel}s"
                    ))
                
                except Exception as e:
                    panel = futures[future]
                    logger.error(f"Error inesperado enviando a panel {panel.ip}: {e}")
                    
                    results.append(PanelUpdateResult(
                        panel_id=panel.id,
                        panel_ip=panel.ip,
                        success=False,
                        message='',
                        response_time_ms=0,
                        error=str(e)
                    ))
        
        return results
    
    @staticmethod
    def _update_panel_status_in_db(session: Session, panel_results: List[PanelUpdateResult], 
                                 message_sent: str):
        """
        Actualizar estado de paneles en base de datos
        
        Args:
            session: Sesión de base de datos
            panel_results: Resultados de envío a paneles
            message_sent: Mensaje que se envió
        """
        try:
            for result in panel_results:
                if result.panel_id:
                    # Determinar nuevo estado del panel
                    if result.success:
                        new_status = 'ONLINE'
                        # Actualizar panel con nuevo mensaje y estado
                        session.execute(text("""
                            UPDATE panels 
                            SET last_message = :message,
                                last_update = NOW(),
                                status = :status
                            WHERE id = :panel_id
                        """), {
                            'message': message_sent[:255],  # Limitar longitud del mensaje
                            'status': new_status,
                            'panel_id': result.panel_id
                        })
                    else:
                        new_status = 'OFFLINE'
                        # Solo actualizar estado y timestamp, preservar último mensaje válido
                        session.execute(text("""
                            UPDATE panels 
                            SET last_update = NOW(),
                                status = :status
                            WHERE id = :panel_id
                        """), {
                            'status': new_status,
                            'panel_id': result.panel_id
                        })
                    
                    logger.debug(f"Panel {result.panel_id} estado actualizado: {new_status}")
        
        except Exception as e:
            logger.error(f"Error actualizando estado de paneles en BD: {e}")
            # No hacer rollback aquí - se maneja en nivel superior
