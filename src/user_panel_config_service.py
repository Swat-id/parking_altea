#!/usr/bin/env python3
"""
Servicio para gestionar la configuración de paneles por usuario/empresa
"""

import logging
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from models import UserPanelConfig, User

logger = logging.getLogger(__name__)


class UserPanelConfigService:
    """Servicio para gestionar configuración de paneles por usuario"""
    
    def __init__(self, db_session: Session):
        """
        Inicializa el servicio
        
        Args:
            db_session: Sesión de base de datos
        """
        self.db_session = db_session
    
    def get_user_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener configuración de paneles para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con configuración o None si no existe
        """
        try:
            config = self.db_session.query(UserPanelConfig).filter(
                UserPanelConfig.user_id == user_id
            ).first()
            
            if config:
                return {
                    'id': config.id,
                    'user_id': config.user_id,
                    'panel_update_interval_seconds': config.panel_update_interval_seconds,
                    'is_active': config.is_active,
                    'created_at': config.created_at.isoformat() if config.created_at else None,
                    'updated_at': config.updated_at.isoformat() if config.updated_at else None
                }
            else:
                # Si no existe, crear con valores por defecto
                return self.create_default_config(user_id)
                
        except Exception as e:
            logger.error(f"Error obteniendo configuración de usuario {user_id}: {e}")
            return None
    
    def create_default_config(self, user_id: int) -> Dict[str, Any]:
        """
        Crear configuración por defecto para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con configuración creada
        """
        try:
            # Verificar que el usuario existe
            user = self.db_session.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"Usuario {user_id} no encontrado")
                return None
            
            # Crear configuración por defecto
            config = UserPanelConfig(
                user_id=user_id,
                panel_update_interval_seconds=120,  # 2 minutos por defecto
                is_active=True
            )
            self.db_session.add(config)
            self.db_session.commit()
            
            logger.info(f"Configuración por defecto creada para usuario {user_id}")
            
            return {
                'id': config.id,
                'user_id': config.user_id,
                'panel_update_interval_seconds': config.panel_update_interval_seconds,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creando configuración por defecto para usuario {user_id}: {e}")
            return None
    
    def update_user_config(
        self,
        user_id: int,
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualizar configuración de paneles para un usuario
        
        Args:
            user_id: ID del usuario
            config_data: Dict con datos de configuración a actualizar
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            # Buscar configuración existente
            config = self.db_session.query(UserPanelConfig).filter(
                UserPanelConfig.user_id == user_id
            ).first()
            
            if not config:
                # Si no existe, crear nueva
                config = UserPanelConfig(
                    user_id=user_id,
                    is_active=True
                )
                self.db_session.add(config)
            
            # Actualizar campos
            if 'panel_update_interval_seconds' in config_data:
                interval = config_data['panel_update_interval_seconds']
                if interval <= 0:
                    return {
                        'success': False,
                        'error': 'panel_update_interval_seconds debe ser mayor que 0'
                    }
                config.panel_update_interval_seconds = interval
            
            if 'is_active' in config_data:
                config.is_active = config_data['is_active']
            
            self.db_session.commit()
            
            logger.info(f"Configuración actualizada para usuario {user_id}")
            
            return {
                'success': True,
                'config_id': config.id,
                'message': 'Configuración actualizada exitosamente',
                'config': {
                    'id': config.id,
                    'user_id': config.user_id,
                    'panel_update_interval_seconds': config.panel_update_interval_seconds,
                    'is_active': config.is_active,
                    'updated_at': config.updated_at.isoformat() if config.updated_at else None
                }
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error actualizando configuración para usuario {user_id}: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    def get_update_interval(self, user_id: int) -> int:
        """
        Obtener intervalo de actualización para un usuario (método de conveniencia)
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Intervalo en segundos (por defecto 120 si no existe)
        """
        config = self.get_user_config(user_id)
        if config:
            return config.get('panel_update_interval_seconds', 120)
        return 120  # Valor por defecto

