#!/usr/bin/env python3
"""
Servicio de gestión de ventanas de paneles (Panel Tipo 4)
Gestiona asignaciones de parkings/sensores a ventanas y configuraciones de rotación
"""

import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import (
    ParkingPanelWindow, PanelWindowConfiguration, Panel, Parking, 
    ParkingSensorSummary, PanelType
)

logger = logging.getLogger(__name__)


class PanelWindowService:
    """Servicio para gestionar ventanas de paneles Tipo 4"""
    
    def __init__(self, db_session: Session):
        """
        Inicializa el servicio
        
        Args:
            db_session: Sesión de base de datos
        """
        self.db_session = db_session
    
    def assign_parking_to_window(
        self,
        panel_id: int,
        window_id: int,
        parking_id: int,
        sensor_type: Optional[str] = None,
        texto_fijo_previo: Optional[str] = None,
        color: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Asigna un parking o grupo de sensores a una ventana
        
        Args:
            panel_id: ID del panel
            window_id: ID de la ventana (0-15)
            parking_id: ID del parking
            sensor_type: Tipo de sensor ('PMR', 'Electrico', 'Caravanas', etc.) o None para parking general
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que el panel existe
            panel = self.db_session.query(Panel).filter(Panel.id == panel_id).first()
            if not panel:
                return {'success': False, 'error': f'Panel {panel_id} no encontrado'}
            
            # Verificar que el panel es Tipo 3 o Tipo 4
            if panel.panel_type_id:
                panel_type = self.db_session.query(PanelType).filter(
                    PanelType.id == panel.panel_type_id
                ).first()
                if not panel_type or panel_type.windows_count not in [2, 16]:
                    return {
                        'success': False,
                        'error': f'El panel {panel_id} no es Tipo 3 o Tipo 4 (soporta {panel_type.windows_count if panel_type else 0} ventanas, se requieren 2 o 16)'
                    }
                
                # Validar window_id según el tipo de panel
                if panel_type.windows_count == 2:
                    # Tipo 3: solo ventanas 0 y 1
                    if window_id < 0 or window_id > 1:
                        return {
                            'success': False,
                            'error': f'window_id debe ser 0 o 1 para paneles Tipo 3, recibido: {window_id}'
                        }
                elif panel_type.windows_count == 16:
                    # Tipo 4: ventanas 0 a 15
                    if window_id < 0 or window_id > 15:
                        return {
                            'success': False,
                            'error': f'window_id debe estar entre 0 y 15 para paneles Tipo 4, recibido: {window_id}'
                        }
            else:
                # Si no tiene tipo, validar genéricamente
                if window_id < 0 or window_id > 15:
                    return {
                        'success': False,
                        'error': f'window_id debe estar entre 0 y 15, recibido: {window_id}'
                    }
            
            # Verificar que el parking existe
            parking = self.db_session.query(Parking).filter(Parking.id == parking_id).first()
            if not parking:
                return {'success': False, 'error': f'Parking {parking_id} no encontrado'}
            
            # Si se especifica sensor_type, verificar que existe en el parking
            if sensor_type:
                sensor_summary = self.db_session.query(ParkingSensorSummary).filter(
                    and_(
                        ParkingSensorSummary.parking_id == parking_id,
                        ParkingSensorSummary.sensor_type == sensor_type
                    )
                ).first()
                if not sensor_summary:
                    return {
                        'success': False,
                        'error': f'No se encontraron sensores de tipo {sensor_type} en el parking {parking_id}'
                    }
            
            # Verificar si ya existe la asignación
            existing = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.window_id == window_id,
                    ParkingPanelWindow.parking_id == parking_id,
                    ParkingPanelWindow.sensor_type == sensor_type
                )
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'error': 'La asignación ya existe',
                    'assignment_id': existing.id
                }
            
            # Determinar display_type
            display_type = 'sensor_group' if sensor_type else 'parking'
            
            # Crear nueva asignación
            assignment = ParkingPanelWindow(
                panel_id=panel_id,
                window_id=window_id,
                parking_id=parking_id,
                sensor_type=sensor_type,
                display_type=display_type,
                texto_fijo_previo=texto_fijo_previo,
                color=color,
                is_active=True
            )
            
            self.db_session.add(assignment)
            self.db_session.commit()
            
            logger.info(
                f"Asignación creada: Panel {panel_id}, Ventana {window_id}, "
                f"Parking {parking_id}, Sensor Type: {sensor_type or 'parking general'}"
            )
            
            return {
                'success': True,
                'assignment_id': assignment.id,
                'message': 'Asignación creada exitosamente'
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error asignando parking a ventana: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    def get_window_assignments(self, panel_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las asignaciones de un panel
        
        Args:
            panel_id: ID del panel
            
        Returns:
            Lista de asignaciones
        """
        try:
            assignments = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.is_active == True
                )
            ).order_by(ParkingPanelWindow.window_id, ParkingPanelWindow.priority).all()
            
            result = []
            for assignment in assignments:
                result.append({
                    'id': assignment.id,
                    'panel_id': assignment.panel_id,
                    'window_id': assignment.window_id,
                    'parking_id': assignment.parking_id,
                    'parking_name': assignment.parking.name if assignment.parking else None,
                    'sensor_type': assignment.sensor_type,
                    'display_type': assignment.display_type,
                    'texto_fijo_previo': assignment.texto_fijo_previo,
                    'color': assignment.color,
                    'priority': assignment.priority,
                    'is_active': assignment.is_active,
                    'created_at': assignment.created_at.isoformat() if assignment.created_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo asignaciones de ventanas: {e}")
            return []
    
    def get_parking_windows(self, parking_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las ventanas asignadas a un parking
        
        Args:
            parking_id: ID del parking
            
        Returns:
            Lista de asignaciones de ventanas
        """
        try:
            assignments = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.parking_id == parking_id,
                    ParkingPanelWindow.is_active == True
                )
            ).order_by(ParkingPanelWindow.panel_id, ParkingPanelWindow.window_id).all()
            
            result = []
            for assignment in assignments:
                result.append({
                    'id': assignment.id,
                    'panel_id': assignment.panel_id,
                    'panel_name': assignment.panel.name if assignment.panel else None,
                    'panel_ip': assignment.panel.ip if assignment.panel else None,
                    'window_id': assignment.window_id,
                    'sensor_type': assignment.sensor_type,
                    'display_type': assignment.display_type,
                    'priority': assignment.priority,
                    'is_active': assignment.is_active
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo ventanas del parking: {e}")
            return []
    
    def remove_window_assignment(
        self,
        panel_id: int,
        window_id: int,
        parking_id: int,
        sensor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elimina una asignación específica
        
        Args:
            panel_id: ID del panel
            window_id: ID de la ventana
            parking_id: ID del parking
            sensor_type: Tipo de sensor o None
            
        Returns:
            Dict con resultado
        """
        try:
            assignment = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.window_id == window_id,
                    ParkingPanelWindow.parking_id == parking_id,
                    ParkingPanelWindow.sensor_type == sensor_type
                )
            ).first()
            
            if not assignment:
                return {
                    'success': False,
                    'error': 'Asignación no encontrada'
                }
            
            assignment.is_active = False
            self.db_session.commit()
            
            logger.info(f"Asignación eliminada: Panel {panel_id}, Ventana {window_id}, Parking {parking_id}")
            
            return {
                'success': True,
                'message': 'Asignación eliminada exitosamente'
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error eliminando asignación: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    def get_parking_sensor_types(self, parking_id: int) -> List[str]:
        """
        Obtiene los tipos de sensores disponibles en un parking
        
        Args:
            parking_id: ID del parking
            
        Returns:
            Lista de tipos de sensores disponibles
        """
        try:
            sensor_summaries = self.db_session.query(ParkingSensorSummary).filter(
                and_(
                    ParkingSensorSummary.parking_id == parking_id,
                    ParkingSensorSummary.total_sensors > 0
                )
            ).all()
            
            return [summary.sensor_type for summary in sensor_summaries]
            
        except Exception as e:
            logger.error(f"Error obteniendo tipos de sensores: {e}")
            return []
    
    def get_sensor_data_for_window(
        self,
        panel_id: int,
        window_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de sensores agrupados para una ventana específica
        desde parking_sensor_summary
        
        Args:
            panel_id: ID del panel
            window_id: ID de la ventana
            
        Returns:
            Dict con datos de sensores o None si no hay asignación
        """
        try:
            # Obtener asignación
            assignment = self.db_session.query(ParkingPanelWindow).filter(
                and_(
                    ParkingPanelWindow.panel_id == panel_id,
                    ParkingPanelWindow.window_id == window_id,
                    ParkingPanelWindow.is_active == True,
                    ParkingPanelWindow.sensor_type.isnot(None)  # Solo sensores, no parking general
                )
            ).first()
            
            if not assignment or not assignment.sensor_type:
                return None
            
            # Obtener datos de sensores desde parking_sensor_summary
            sensor_summary = self.db_session.query(ParkingSensorSummary).filter(
                and_(
                    ParkingSensorSummary.parking_id == assignment.parking_id,
                    ParkingSensorSummary.sensor_type == assignment.sensor_type
                )
            ).first()
            
            if not sensor_summary:
                return None
            
            return {
                'parking_id': assignment.parking_id,
                'parking_name': assignment.parking.name if assignment.parking else None,
                'sensor_type': assignment.sensor_type,
                'total_sensors': sensor_summary.total_sensors,
                'free_sensors': sensor_summary.free_sensors,
                'busy_sensors': sensor_summary.busy_sensors,
                'error_sensors': sensor_summary.error_sensors,
                'last_update': sensor_summary.last_update.isoformat() if sensor_summary.last_update else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de sensores para ventana: {e}")
            return None
    
    def update_window_configuration(
        self,
        panel_id: int,
        window_id: int,
        parking_id: int,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza la configuración de rotación para una ventana
        
        Args:
            panel_id: ID del panel (puede ser 0 o None si el panel no existe aún - configuración preparatoria)
            window_id: ID de la ventana
            parking_id: ID del parking
            config: Dict con configuración (rotation_enabled, rotation_order, refresh_time_seconds, company_id)
            
        Returns:
            Dict con resultado
        """
        try:
            company_id = config.get('company_id')
            
            # Si panel_id es 0 o None, es una configuración preparatoria a nivel de empresa
            # Buscar por company_id, parking_id y window_id (solo una por empresa)
            if not panel_id or panel_id == 0:
                if not company_id:
                    return {
                        'success': False,
                        'error': 'company_id es requerido para configuraciones preparatorias'
                    }
                
                config_obj = self.db_session.query(PanelWindowConfiguration).filter(
                    and_(
                        PanelWindowConfiguration.company_id == company_id,
                        PanelWindowConfiguration.window_id == window_id,
                        PanelWindowConfiguration.parking_id == parking_id,
                        or_(
                            PanelWindowConfiguration.panel_id.is_(None),
                            PanelWindowConfiguration.panel_id == 0
                        )
                    )
                ).first()
                
                if not config_obj:
                    # Crear nueva configuración preparatoria
                    config_obj = PanelWindowConfiguration(
                        panel_id=None,  # NULL para configuraciones preparatorias
                        window_id=window_id,
                        parking_id=parking_id,
                        company_id=company_id,
                        is_active=True
                    )
                    self.db_session.add(config_obj)
            else:
                # Configuración para un panel específico
                # Buscar primero por panel_id específico
                config_obj = self.db_session.query(PanelWindowConfiguration).filter(
                    and_(
                        PanelWindowConfiguration.panel_id == panel_id,
                        PanelWindowConfiguration.window_id == window_id,
                        PanelWindowConfiguration.parking_id == parking_id
                    )
                ).first()
                
                # Si no existe, buscar configuración preparatoria de la empresa y asociarla
                if not config_obj and company_id:
                    prep_config = self.db_session.query(PanelWindowConfiguration).filter(
                        and_(
                            PanelWindowConfiguration.company_id == company_id,
                            PanelWindowConfiguration.window_id == window_id,
                            PanelWindowConfiguration.parking_id == parking_id,
                            or_(
                                PanelWindowConfiguration.panel_id.is_(None),
                                PanelWindowConfiguration.panel_id == 0
                            )
                        )
                    ).first()
                    
                    if prep_config:
                        # Asociar la configuración preparatoria al panel
                        prep_config.panel_id = panel_id
                        config_obj = prep_config
                        logger.info(f"Configuración preparatoria {prep_config.id} asociada al panel {panel_id}")
                
                # Si aún no existe, crear nueva configuración
                if not config_obj:
                    config_obj = PanelWindowConfiguration(
                        panel_id=panel_id,
                        window_id=window_id,
                        parking_id=parking_id,
                        company_id=company_id,
                        is_active=True
                    )
                    self.db_session.add(config_obj)
            
            # Actualizar campos
            if 'rotation_enabled' in config:
                config_obj.rotation_enabled = config['rotation_enabled']
            if 'rotation_order' in config:
                config_obj.rotation_order = config['rotation_order']
            if 'refresh_time_seconds' in config:
                if config['refresh_time_seconds'] <= 0:
                    return {'success': False, 'error': 'refresh_time_seconds debe ser mayor que 0'}
                config_obj.refresh_time_seconds = config['refresh_time_seconds']
            if 'company_id' in config:
                config_obj.company_id = config['company_id']
            if 'parking_status_config' in config:
                config_obj.parking_status_config = config['parking_status_config']
            
            self.db_session.commit()
            
            logger.info(f"Configuración actualizada: Panel {panel_id}, Ventana {window_id}, Parking {parking_id}")
            
            return {
                'success': True,
                'config_id': config_obj.id,
                'message': 'Configuración actualizada exitosamente'
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error actualizando configuración: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    def get_window_configuration(
        self,
        panel_id: int,
        window_id: int,
        parking_id: int,
        company_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de una ventana
        
        Args:
            panel_id: ID del panel
            window_id: ID de la ventana
            parking_id: ID del parking
            company_id: ID de empresa (para superadmin) o None
            
        Returns:
            Dict con configuración o None
        """
        try:
            query = self.db_session.query(PanelWindowConfiguration).filter(
                and_(
                    PanelWindowConfiguration.panel_id == panel_id,
                    PanelWindowConfiguration.window_id == window_id,
                    PanelWindowConfiguration.parking_id == parking_id,
                    PanelWindowConfiguration.is_active == True
                )
            )
            
            # Si se especifica company_id, filtrar por él
            if company_id is not None:
                query = query.filter(
                    or_(
                        PanelWindowConfiguration.company_id == company_id,
                        PanelWindowConfiguration.company_id.is_(None)
                    )
                )
            
            config = query.first()
            
            if not config:
                return None
            
            return {
                'id': config.id,
                'panel_id': config.panel_id,
                'window_id': config.window_id,
                'parking_id': config.parking_id,
                'company_id': config.company_id,
                'rotation_enabled': config.rotation_enabled,
                'rotation_order': config.rotation_order,
                'refresh_time_seconds': config.refresh_time_seconds,
                'parking_status_config': config.parking_status_config,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            return None

