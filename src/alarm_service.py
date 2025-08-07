#!/usr/bin/env python3
"""
Servicio de gestión de alarmas para el sistema v3.2.0_alarms
Maneja la lógica de negocio para alarmas de paneles, cámaras y aparcamientos
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models import (
    AlarmConfiguration, AlarmConfigurationTarget, AlarmConfigurationThreshold,
    Alarm, AlarmHistory, User, Panel, Access, Parking
)

logger = logging.getLogger(__name__)

class AlarmService:
    """Servicio principal para gestión de alarmas"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_user_alarm_configurations(self, user_id: int) -> List[AlarmConfiguration]:
        """Obtener todas las configuraciones de alarmas de un usuario"""
        try:
            configurations = self.session.query(AlarmConfiguration).filter(
                AlarmConfiguration.user_id == user_id
            ).all()
            return configurations
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones de alarmas para usuario {user_id}: {e}")
            return []
    
    def get_alarm_configuration(self, config_id: int, user_id: int) -> Optional[AlarmConfiguration]:
        """Obtener una configuración específica de alarma"""
        try:
            configuration = self.session.query(AlarmConfiguration).filter(
                and_(
                    AlarmConfiguration.id == config_id,
                    AlarmConfiguration.user_id == user_id
                )
            ).first()
            return configuration
        except Exception as e:
            logger.error(f"Error obteniendo configuración {config_id}: {e}")
            return None
    
    def create_alarm_configuration(self, user_id: int, data: Dict[str, Any]) -> Optional[AlarmConfiguration]:
        """Crear una nueva configuración de alarma"""
        try:
            # Crear la configuración principal
            configuration = AlarmConfiguration(
                user_id=user_id,
                name=data['name'],
                description=data.get('description', ''),
                alarm_type=data['alarm_type'],
                status='active'
            )
            self.session.add(configuration)
            self.session.flush()  # Para obtener el ID
            
            # Crear los objetivos
            for target_id in data.get('targets', []):
                target = AlarmConfigurationTarget(
                    alarm_configuration_id=configuration.id,
                    target_type=data['alarm_type'],
                    target_id=target_id
                )
                self.session.add(target)
            
            # Crear los umbrales
            for threshold_data in data.get('thresholds', []):
                threshold = AlarmConfigurationThreshold(
                    alarm_configuration_id=configuration.id,
                    severity=threshold_data['severity'],
                    threshold_value=threshold_data['threshold_value'],
                    threshold_type=threshold_data['threshold_type']
                )
                self.session.add(threshold)
            
            self.session.commit()
            logger.info(f"Configuración de alarma creada: {configuration.id}")
            return configuration
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creando configuración de alarma: {e}")
            return None
    
    def update_alarm_configuration(self, config_id: int, user_id: int, data: Dict[str, Any]) -> bool:
        """Actualizar una configuración de alarma existente"""
        try:
            configuration = self.get_alarm_configuration(config_id, user_id)
            if not configuration:
                return False
            
            # Actualizar campos básicos
            if 'name' in data:
                configuration.name = data['name']
            if 'description' in data:
                configuration.description = data['description']
            if 'status' in data:
                configuration.status = data['status']
            
            # Actualizar umbrales si se proporcionan
            if 'thresholds' in data:
                # Eliminar umbrales existentes
                self.session.query(AlarmConfigurationThreshold).filter(
                    AlarmConfigurationThreshold.alarm_configuration_id == config_id
                ).delete()
                
                # Crear nuevos umbrales
                for threshold_data in data['thresholds']:
                    threshold = AlarmConfigurationThreshold(
                        alarm_configuration_id=config_id,
                        severity=threshold_data['severity'],
                        threshold_value=threshold_data['threshold_value'],
                        threshold_type=threshold_data['threshold_type']
                    )
                    self.session.add(threshold)
            
            # Actualizar objetivos si se proporcionan
            if 'targets' in data:
                # Eliminar objetivos existentes
                self.session.query(AlarmConfigurationTarget).filter(
                    AlarmConfigurationTarget.alarm_configuration_id == config_id
                ).delete()
                
                # Crear nuevos objetivos
                for target_id in data['targets']:
                    target = AlarmConfigurationTarget(
                        alarm_configuration_id=config_id,
                        target_type=configuration.alarm_type,
                        target_id=target_id
                    )
                    self.session.add(target)
            
            self.session.commit()
            logger.info(f"Configuración de alarma actualizada: {config_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error actualizando configuración de alarma {config_id}: {e}")
            return False
    
    def delete_alarm_configuration(self, config_id: int, user_id: int) -> bool:
        """Eliminar una configuración de alarma"""
        try:
            configuration = self.get_alarm_configuration(config_id, user_id)
            if not configuration:
                return False
            
            self.session.delete(configuration)
            self.session.commit()
            logger.info(f"Configuración de alarma eliminada: {config_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error eliminando configuración de alarma {config_id}: {e}")
            return False
    
    def get_active_alarms(self, user_id: Optional[int] = None) -> List[Alarm]:
        """Obtener alarmas activas"""
        try:
            query = self.session.query(Alarm).filter(Alarm.status == 'active')
            if user_id:
                query = query.filter(Alarm.user_id == user_id)
            
            alarms = query.order_by(Alarm.created_at.desc()).all()
            return alarms
        except Exception as e:
            logger.error(f"Error obteniendo alarmas activas: {e}")
            return []
    
    def get_alarm_history(self, user_id: Optional[int] = None, filters: Dict[str, Any] = None) -> List[Alarm]:
        """Obtener histórico de alarmas con filtros opcionales"""
        try:
            query = self.session.query(Alarm)
            
            if user_id:
                query = query.filter(Alarm.user_id == user_id)
            
            if filters:
                if 'severity' in filters:
                    query = query.filter(Alarm.severity == filters['severity'])
                if 'status' in filters:
                    query = query.filter(Alarm.status == filters['status'])
                if 'alarm_type' in filters:
                    query = query.join(AlarmConfiguration).filter(
                        AlarmConfiguration.alarm_type == filters['alarm_type']
                    )
                if 'date_from' in filters:
                    query = query.filter(Alarm.created_at >= filters['date_from'])
                if 'date_to' in filters:
                    query = query.filter(Alarm.created_at <= filters['date_to'])
            
            alarms = query.order_by(Alarm.created_at.desc()).all()
            return alarms
        except Exception as e:
            logger.error(f"Error obteniendo histórico de alarmas: {e}")
            return []
    
    def check_duplicate_alarm(self, configuration_id: int, severity: str, target_id: str = None, target_type: str = None) -> bool:
        """Verificar si ya existe una alarma activa para el mismo equipo específico"""
        try:
            # Si no se especifica target, usar lógica antigua (por configuración+severidad)
            if not target_id or not target_type:
                existing_alarm = self.session.query(Alarm).filter(
                    and_(
                        Alarm.alarm_configuration_id == configuration_id,
                        Alarm.severity == severity,
                        Alarm.status == 'active'
                    )
                ).first()
                return existing_alarm is not None
            
            # Nueva lógica: buscar alarma activa para el equipo específico
            existing_alarms = self.session.query(Alarm).filter(
                and_(
                    Alarm.alarm_configuration_id == configuration_id,
                    Alarm.status == 'active'
                )
            ).all()
            
            # Verificar si alguna alarma activa afecta al mismo equipo
            for alarm in existing_alarms:
                if alarm.affected_targets:
                    for target in alarm.affected_targets:
                        if (target.get('id') == int(target_id) if str(target_id).isdigit() else target.get('id') == target_id) and target.get('type') == target_type:
                            logger.info(f"Alarma duplicada encontrada para {target_type} {target_id} (alarma {alarm.id})")
                            return True
            
            return False
        except Exception as e:
            logger.error(f"Error verificando alarma duplicada: {e}")
            return False
    
    def create_alarm(self, configuration_id: int, severity: str, message: str, affected_targets: List[Dict]) -> Optional[Alarm]:
        """Crear una nueva alarma"""
        try:
            # Verificar si ya existe una alarma activa para el equipo específico
            if affected_targets and len(affected_targets) > 0:
                target = affected_targets[0]  # Usar el primer target para verificar duplicados
                target_id = str(target.get('id'))
                target_type = target.get('type')
                
                if self.check_duplicate_alarm(configuration_id, severity, target_id, target_type):
                    logger.info(f"Alarma duplicada detectada para {target_type} {target_id}")
                    return None
            else:
                # Fallback a lógica antigua si no hay targets específicos
                if self.check_duplicate_alarm(configuration_id, severity):
                    logger.info(f"Alarma duplicada detectada para configuración {configuration_id}, severidad {severity}")
                    return None
            
            # Obtener la configuración para obtener el user_id
            configuration = self.session.query(AlarmConfiguration).filter(
                AlarmConfiguration.id == configuration_id
            ).first()
            
            if not configuration:
                logger.error(f"Configuración de alarma no encontrada: {configuration_id}")
                return None
            
            # Crear la alarma
            alarm = Alarm(
                alarm_configuration_id=configuration_id,
                user_id=configuration.user_id,
                severity=severity,
                status='active',
                message=message,
                affected_targets=json.dumps(affected_targets)
            )
            
            self.session.add(alarm)
            self.session.flush()  # Para obtener el ID
            
            # Crear entrada en el histórico
            history_entry = AlarmHistory(
                alarm_id=alarm.id,
                action='created',
                description=f"Alarma {severity} creada: {message}"
            )
            self.session.add(history_entry)
            
            self.session.commit()
            logger.info(f"Alarma creada: {alarm.id} - {severity} - {message}")
            return alarm
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creando alarma: {e}")
            return None
    
    def resolve_alarm(self, alarm_id: int, user_id: int, resolution_description: str) -> bool:
        """Resolver una alarma existente"""
        try:
            alarm = self.session.query(Alarm).filter(
                and_(
                    Alarm.id == alarm_id,
                    Alarm.user_id == user_id,
                    Alarm.status == 'active'
                )
            ).first()
            
            if not alarm:
                logger.warning(f"Alarma no encontrada o ya resuelta: {alarm_id}")
                return False
            
            # Marcar como resuelta
            alarm.status = 'resolved'
            alarm.resolved_at = datetime.utcnow()
            alarm.resolution_description = resolution_description
            
            # Crear entrada en el histórico
            history_entry = AlarmHistory(
                alarm_id=alarm.id,
                action='resolved',
                description=f"Alarma resuelta: {resolution_description}"
            )
            self.session.add(history_entry)
            
            self.session.commit()
            logger.info(f"Alarma resuelta: {alarm_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error resolviendo alarma {alarm_id}: {e}")
            return False
    
    def escalate_alarm(self, alarm_id: int, new_severity: str) -> bool:
        """Escalar una alarma a mayor gravedad"""
        try:
            alarm = self.session.query(Alarm).filter(
                and_(
                    Alarm.id == alarm_id,
                    Alarm.status == 'active'
                )
            ).first()
            
            if not alarm:
                return False
            
            old_severity = alarm.severity
            alarm.severity = new_severity
            
            # Crear entrada en el histórico
            history_entry = AlarmHistory(
                alarm_id=alarm.id,
                action='escalated',
                description=f"Alarma escalada de {old_severity} a {new_severity}"
            )
            self.session.add(history_entry)
            
            self.session.commit()
            logger.info(f"Alarma escalada: {alarm_id} de {old_severity} a {new_severity}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error escalando alarma {alarm_id}: {e}")
            return False
    
    def get_alarm_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtener estadísticas de alarmas"""
        try:
            query = self.session.query(Alarm)
            if user_id:
                query = query.filter(Alarm.user_id == user_id)
            
            # Total de alarmas
            total_alarms = query.count()
            
            # Alarmas por estado
            active_alarms = query.filter(Alarm.status == 'active').count()
            resolved_alarms = query.filter(Alarm.status == 'resolved').count()
            
            # Alarmas por severidad
            leve_alarms = query.filter(Alarm.severity == 'LEVE').count()
            normal_alarms = query.filter(Alarm.severity == 'NORMAL').count()
            grave_alarms = query.filter(Alarm.severity == 'GRAVE').count()
            
            # Alarmas por tipo
            panel_alarms = query.join(AlarmConfiguration).filter(
                AlarmConfiguration.alarm_type == 'panel'
            ).count()
            
            camera_alarms = query.join(AlarmConfiguration).filter(
                AlarmConfiguration.alarm_type == 'camera'
            ).count()
            
            parking_alarms = query.join(AlarmConfiguration).filter(
                AlarmConfiguration.alarm_type == 'parking'
            ).count()
            
            return {
                'total_alarms': total_alarms,
                'active_alarms': active_alarms,
                'resolved_alarms': resolved_alarms,
                'by_severity': {
                    'LEVE': leve_alarms,
                    'NORMAL': normal_alarms,
                    'GRAVE': grave_alarms
                },
                'by_type': {
                    'panel': panel_alarms,
                    'camera': camera_alarms,
                    'parking': parking_alarms
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de alarmas: {e}")
            return {} 