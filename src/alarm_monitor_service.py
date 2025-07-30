#!/usr/bin/env python3
"""
Servicio de monitorización de alarmas para el sistema v3.2.0_alarms
Verifica periódicamente el estado de equipos y genera alarmas según configuraciones
"""

import logging
import time
import subprocess
import threading
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from config import DB_URL
from models import (
    AlarmConfiguration, AlarmConfigurationTarget, AlarmConfigurationThreshold,
    Panel, Access, Parking, User
)
from alarm_service import AlarmService
from email_service import EmailService

logger = logging.getLogger(__name__)

class AlarmMonitorService:
    """Servicio de monitorización continua de equipos"""
    
    def __init__(self, check_interval: int = 300):  # 5 minutos por defecto
        self.check_interval = check_interval
        self.engine = create_engine(DB_URL)
        self.running = False
        self.monitor_thread = None
        self.alarm_service = None
        self.email_service = None
        
        # Cache para evitar verificaciones excesivas
        self.last_ping_results = {}
        self.ping_cache_duration = 60  # 1 minuto de cache
    
    def start_monitoring(self):
        """Iniciar monitorización continua"""
        if self.running:
            logger.warning("Monitorización ya está ejecutándose")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Monitorización de alarmas iniciada (intervalo: {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Detener monitorización"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Monitorización de alarmas detenida")
    
    def _monitor_loop(self):
        """Bucle principal de monitorización"""
        while self.running:
            try:
                self._check_all_alarm_conditions()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error en bucle de monitorización: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def _check_all_alarm_conditions(self):
        """Verificar todas las condiciones de alarmas activas"""
        try:
            logger.info("🔍 Iniciando verificación de condiciones de alarmas...")
            with Session(self.engine) as session:
                self.alarm_service = AlarmService(session)
                self.email_service = EmailService()
                
                # Obtener todas las configuraciones activas
                configurations = session.query(AlarmConfiguration).filter(
                    AlarmConfiguration.status == 'active'
                ).all()
                
                logger.info(f"📋 Encontradas {len(configurations)} configuraciones activas")
                
                for config in configurations:
                    try:
                        logger.info(f"🔍 Verificando configuración {config.id} ({config.name}) - Tipo: {config.alarm_type}")
                        self._check_configuration_conditions(config, session)
                    except Exception as e:
                        logger.error(f"Error verificando configuración {config.id}: {e}")
                
                logger.info("✅ Verificación de condiciones completada")
                        
        except Exception as e:
            logger.error(f"Error en verificación de condiciones: {e}")
    
    def _check_configuration_conditions(self, config: AlarmConfiguration, session: Session):
        """Verificar condiciones para una configuración específica"""
        if config.alarm_type == 'panel':
            self._check_panel_alarms(config, session)
        elif config.alarm_type == 'camera':
            self._check_camera_alarms(config, session)
        elif config.alarm_type == 'parking':
            self._check_parking_alarms(config, session)
    
    def _check_panel_alarms(self, config: AlarmConfiguration, session: Session):
        """Verificar alarmas de paneles"""
        try:
            logger.info(f"🔍 Verificando alarmas de paneles para configuración {config.id}")
            
            # Obtener objetivos de la configuración
            targets = session.query(AlarmConfigurationTarget).filter(
                AlarmConfigurationTarget.alarm_configuration_id == config.id
            ).all()
            
            # Obtener umbrales ordenados por severidad
            thresholds = session.query(AlarmConfigurationThreshold).filter(
                AlarmConfigurationThreshold.alarm_configuration_id == config.id
            ).order_by(AlarmConfigurationThreshold.threshold_value).all()
            
            logger.info(f"📋 Encontrados {len(targets)} objetivos y {len(thresholds)} umbrales")
            
            if not targets or not thresholds:
                logger.warning("⚠️ No hay objetivos o umbrales configurados")
                return
            
            affected_panels = []
            
            for target in targets:
                panel = session.query(Panel).filter(Panel.id == target.target_id).first()
                if not panel:
                    logger.warning(f"⚠️ Panel {target.target_id} no encontrado")
                    continue
                
                logger.info(f"🔍 Verificando panel {panel.name} ({panel.ip})")
                
                # Verificar conectividad del panel
                is_online = self._check_panel_connectivity(panel)
                logger.info(f"📡 Panel {panel.name}: {'ONLINE' if is_online else 'OFFLINE'}")
                
                if not is_online:
                    # Calcular tiempo de desconexión
                    disconnect_time = self._calculate_disconnect_time(panel)
                    logger.warning(f"⚠️ Panel {panel.name} desconectado por {disconnect_time} minutos")
                    
                    # Determinar severidad basada en umbrales
                    severity = self._determine_severity(disconnect_time, thresholds)
                    
                    if severity:
                        logger.warning(f"🚨 Panel {panel.name} cumple criterio de severidad: {severity}")
                        affected_panels.append({
                            'id': panel.id,
                            'name': panel.name,
                            'ip': panel.ip,
                            'disconnect_time': disconnect_time,
                            'severity': severity
                        })
            
            # Generar alarmas si hay paneles afectados
            if affected_panels:
                logger.warning(f"🚨 Generando {len(affected_panels)} alarmas de paneles")
                self._generate_panel_alarms(config, affected_panels, session)
            else:
                logger.info("✅ No hay paneles afectados")
                
        except Exception as e:
            logger.error(f"Error verificando alarmas de paneles para configuración {config.id}: {e}")
    
    def _check_camera_alarms(self, config: AlarmConfiguration, session: Session):
        """Verificar alarmas de cámaras"""
        try:
            # Obtener objetivos de la configuración
            targets = session.query(AlarmConfigurationTarget).filter(
                AlarmConfigurationTarget.alarm_configuration_id == config.id
            ).all()
            
            # Obtener umbrales ordenados por severidad
            thresholds = session.query(AlarmConfigurationThreshold).filter(
                AlarmConfigurationThreshold.alarm_configuration_id == config.id
            ).order_by(AlarmConfigurationThreshold.threshold_value).all()
            
            if not targets or not thresholds:
                return
            
            affected_cameras = []
            
            for target in targets:
                camera = session.query(Access).filter(Access.id == target.target_id).first()
                if not camera:
                    continue
                
                # Verificar conectividad de la cámara
                is_online = self._check_camera_connectivity(camera)
                
                if not is_online:
                    # Calcular tiempo de desconexión
                    disconnect_time = self._calculate_disconnect_time(camera)
                    
                    # Determinar severidad basada en umbrales
                    severity = self._determine_severity(disconnect_time, thresholds)
                    
                    if severity:
                        affected_cameras.append({
                            'id': camera.id,
                            'name': camera.name,
                            'ip': camera.ip,
                            'disconnect_time': disconnect_time,
                            'severity': severity
                        })
            
            # Generar alarmas si hay cámaras afectadas
            if affected_cameras:
                self._generate_camera_alarms(config, affected_cameras, session)
                
        except Exception as e:
            logger.error(f"Error verificando alarmas de cámaras para configuración {config.id}: {e}")
    
    def _check_parking_alarms(self, config: AlarmConfiguration, session: Session):
        """Verificar alarmas de aparcamientos"""
        try:
            # Obtener objetivos de la configuración
            targets = session.query(AlarmConfigurationTarget).filter(
                AlarmConfigurationTarget.alarm_configuration_id == config.id
            ).all()
            
            # Obtener umbrales
            thresholds = session.query(AlarmConfigurationThreshold).filter(
                AlarmConfigurationThreshold.alarm_configuration_id == config.id
            ).all()
            
            if not targets or not thresholds:
                return
            
            affected_parkings = []
            
            for target in targets:
                parking = session.query(Parking).filter(Parking.id == target.target_id).first()
                if not parking:
                    continue
                
                # Verificar diferentes tipos de alarmas de aparcamiento
                parking_issues = self._check_parking_issues(parking, thresholds, session)
                
                if parking_issues:
                    affected_parkings.extend(parking_issues)
            
            # Generar alarmas si hay aparcamientos afectados
            if affected_parkings:
                self._generate_parking_alarms(config, affected_parkings, session)
                
        except Exception as e:
            logger.error(f"Error verificando alarmas de aparcamientos para configuración {config.id}: {e}")
    
    def _check_panel_connectivity(self, panel: Panel) -> bool:
        """Verificar conectividad de un panel mediante ping"""
        try:
            # Usar cache para evitar pings excesivos
            cache_key = f"panel_{panel.id}"
            current_time = datetime.now(timezone.utc)
            
            if cache_key in self.last_ping_results:
                last_check, last_result = self.last_ping_results[cache_key]
                if (current_time - last_check).seconds < self.ping_cache_duration:
                    return last_result
            
            # Realizar ping
            result = self._ping_host(panel.ip)
            
            # Actualizar cache
            self.last_ping_results[cache_key] = (current_time, result)
            
            # Actualizar estado en base de datos
            panel.status = 'ONLINE' if result else 'OFFLINE'
            panel.last_ping_check = current_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error verificando conectividad de panel {panel.id}: {e}")
            return False
    
    def _check_camera_connectivity(self, camera: Access) -> bool:
        """Verificar conectividad de una cámara mediante ping"""
        try:
            # Usar cache para evitar pings excesivos
            cache_key = f"camera_{camera.id}"
            current_time = datetime.now(timezone.utc)
            
            if cache_key in self.last_ping_results:
                last_check, last_result = self.last_ping_results[cache_key]
                if (current_time - last_check).seconds < self.ping_cache_duration:
                    return last_result
            
            # Realizar ping
            result = self._ping_host(camera.ip)
            
            # Actualizar cache
            self.last_ping_results[cache_key] = (current_time, result)
            
            # Actualizar estado en base de datos
            camera.status = 'ONLINE' if result else 'OFFLINE'
            camera.last_ping_check = current_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error verificando conectividad de cámara {camera.id}: {e}")
            return False
    
    def _ping_host(self, ip: str) -> bool:
        """Realizar ping a una IP específica"""
        try:
            # Usar rutas completas para ping en sistemas Unix
            ping_paths = ["/bin/ping", "/usr/bin/ping", "/sbin/ping"]
            ping_cmd = None
            
            for path in ping_paths:
                try:
                    import os
                    if os.path.exists(path):
                        ping_cmd = path
                        break
                except:
                    continue
            
            if not ping_cmd:
                # Si no encontramos ping, intentar con el PATH
                ping_cmd = "ping"
            
            # Usar ping con timeout de 5 segundos
            result = subprocess.run(
                [ping_cmd, '-c', '1', '-W', '5', ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error realizando ping a {ip}: {e}")
            return False
    
    def _calculate_disconnect_time(self, equipment) -> int:
        """Calcular tiempo de desconexión en minutos"""
        try:
            if not equipment.last_ping_check:
                return 999  # Valor alto si nunca se ha verificado
            
            disconnect_duration = datetime.now(timezone.utc) - equipment.last_ping_check
            return int(disconnect_duration.total_seconds() / 60)
        except Exception as e:
            logger.error(f"Error calculando tiempo de desconexión: {e}")
            return 0
    
    def _determine_severity(self, disconnect_time: int, thresholds: List[AlarmConfigurationThreshold]) -> Optional[str]:
        """Determinar severidad basada en tiempo de desconexión y umbrales"""
        try:
            for threshold in thresholds:
                if disconnect_time >= threshold.threshold_value:
                    return threshold.severity
            return None
        except Exception as e:
            logger.error(f"Error determinando severidad: {e}")
            return None
    
    def _check_parking_issues(self, parking: Parking, thresholds: List[AlarmConfigurationThreshold], session: Session) -> List[Dict]:
        """Verificar problemas en un aparcamiento"""
        issues = []
        
        try:
            # Verificar ocupación fuera de rangos
            occupancy_percentage = (parking.current_occupancy / parking.max_capacity) * 100
            
            for threshold in thresholds:
                if threshold.threshold_type == 'occupancy_high' and occupancy_percentage >= threshold.threshold_value:
                    issues.append({
                        'type': 'occupancy_high',
                        'parking_id': parking.id,
                        'parking_name': parking.name,
                        'current_occupancy': parking.current_occupancy,
                        'max_capacity': parking.max_capacity,
                        'percentage': occupancy_percentage,
                        'severity': threshold.severity
                    })
                elif threshold.threshold_type == 'occupancy_low' and occupancy_percentage <= threshold.threshold_value:
                    issues.append({
                        'type': 'occupancy_low',
                        'parking_id': parking.id,
                        'parking_name': parking.name,
                        'current_occupancy': parking.current_occupancy,
                        'max_capacity': parking.max_capacity,
                        'percentage': occupancy_percentage,
                        'severity': threshold.severity
                    })
            
            # Verificar disponibilidad de información
            info_issues = self._check_parking_information_availability(parking, session)
            if info_issues:
                issues.extend(info_issues)
                
        except Exception as e:
            logger.error(f"Error verificando problemas del aparcamiento {parking.id}: {e}")
        
        return issues
    
    def _check_parking_information_availability(self, parking: Parking, session: Session) -> List[Dict]:
        """Verificar disponibilidad de información del aparcamiento"""
        issues = []
        
        try:
            # Verificar cámaras del aparcamiento
            cameras = session.query(Access).join(Access.camera_parkings).filter(
                Access.camera_parkings.any(parking_id=parking.id)
            ).all()
            
            offline_cameras = []
            for camera in cameras:
                if not self._check_camera_connectivity(camera):
                    offline_cameras.append(camera)
            
            # Verificar paneles del aparcamiento
            panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
            
            offline_panels = []
            for panel in panels:
                if not self._check_panel_connectivity(panel):
                    offline_panels.append(panel)
            
            # Crear issues si hay equipos offline
            if offline_cameras or offline_panels:
                issues.append({
                    'type': 'information_unavailable',
                    'parking_id': parking.id,
                    'parking_name': parking.name,
                    'offline_cameras': [{'id': c.id, 'name': c.name, 'ip': c.ip} for c in offline_cameras],
                    'offline_panels': [{'id': p.id, 'name': p.name, 'ip': p.ip} for p in offline_panels],
                    'severity': 'GRAVE' if len(offline_cameras) + len(offline_panels) > 2 else 'NORMAL'
                })
                
        except Exception as e:
            logger.error(f"Error verificando disponibilidad de información del aparcamiento {parking.id}: {e}")
        
        return issues
    
    def _generate_panel_alarms(self, config: AlarmConfiguration, affected_panels: List[Dict], session: Session):
        """Generar alarmas para paneles afectados"""
        try:
            for panel_info in affected_panels:
                message = f"Panel {panel_info['name']} ({panel_info['ip']}) desconectado por {panel_info['disconnect_time']} minutos"
                
                alarm = self.alarm_service.create_alarm(
                    configuration_id=config.id,
                    severity=panel_info['severity'],
                    message=message,
                    affected_targets=[{
                        'id': panel_info['id'],
                        'name': panel_info['name'],
                        'type': 'panel',
                        'ip': panel_info['ip']
                    }]
                )
                
                if alarm:
                    # Enviar notificación por email
                    self._send_alarm_notification(alarm, config)
                    
        except Exception as e:
            logger.error(f"Error generando alarmas de paneles: {e}")
    
    def _generate_camera_alarms(self, config: AlarmConfiguration, affected_cameras: List[Dict], session: Session):
        """Generar alarmas para cámaras afectadas"""
        try:
            for camera_info in affected_cameras:
                message = f"Cámara {camera_info['name']} ({camera_info['ip']}) desconectada por {camera_info['disconnect_time']} minutos"
                
                alarm = self.alarm_service.create_alarm(
                    configuration_id=config.id,
                    severity=camera_info['severity'],
                    message=message,
                    affected_targets=[{
                        'id': camera_info['id'],
                        'name': camera_info['name'],
                        'type': 'camera',
                        'ip': camera_info['ip']
                    }]
                )
                
                if alarm:
                    # Enviar notificación por email
                    self._send_alarm_notification(alarm, config)
                    
        except Exception as e:
            logger.error(f"Error generando alarmas de cámaras: {e}")
    
    def _generate_parking_alarms(self, config: AlarmConfiguration, affected_parkings: List[Dict], session: Session):
        """Generar alarmas para aparcamientos afectados"""
        try:
            for parking_info in affected_parkings:
                if parking_info['type'] == 'occupancy_high':
                    message = f"Aparcamiento {parking_info['parking_name']} con ocupación alta: {parking_info['current_occupancy']}/{parking_info['max_capacity']} ({parking_info['percentage']:.1f}%)"
                elif parking_info['type'] == 'occupancy_low':
                    message = f"Aparcamiento {parking_info['parking_name']} con ocupación baja: {parking_info['current_occupancy']}/{parking_info['max_capacity']} ({parking_info['percentage']:.1f}%)"
                elif parking_info['type'] == 'information_unavailable':
                    offline_equipment = []
                    if parking_info['offline_cameras']:
                        offline_equipment.append(f"{len(parking_info['offline_cameras'])} cámaras")
                    if parking_info['offline_panels']:
                        offline_equipment.append(f"{len(parking_info['offline_panels'])} paneles")
                    
                    message = f"Aparcamiento {parking_info['parking_name']} sin información válida: {' y '.join(offline_equipment)} offline"
                
                alarm = self.alarm_service.create_alarm(
                    configuration_id=config.id,
                    severity=parking_info['severity'],
                    message=message,
                    affected_targets=[{
                        'id': parking_info['parking_id'],
                        'name': parking_info['parking_name'],
                        'type': 'parking',
                        'issue_type': parking_info['type']
                    }]
                )
                
                if alarm:
                    # Enviar notificación por email
                    self._send_alarm_notification(alarm, config)
                    
        except Exception as e:
            logger.error(f"Error generando alarmas de aparcamientos: {e}")
    
    def _send_alarm_notification(self, alarm: Any, config: AlarmConfiguration):
        """Enviar notificación por email"""
        try:
            if self.email_service:
                # Obtener información del usuario
                user = self.alarm_service.session.query(User).filter(User.id == alarm.user_id).first()
                if user and user.email:
                    self.email_service.send_alarm_notification(user.email, {
                        'alarm_id': alarm.id,
                        'severity': alarm.severity,
                        'message': alarm.message,
                        'configuration_name': config.name,
                        'created_at': alarm.created_at.isoformat()
                    })
        except Exception as e:
            logger.error(f"Error enviando notificación de alarma: {e}")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y ejecutar el servicio
    monitor_service = AlarmMonitorService()
    
    try:
        monitor_service.start_monitoring()
        
        # Mantener el servicio ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Deteniendo servicio de monitorización...")
        monitor_service.stop_monitoring() 