#!/usr/bin/env python3
"""
Script para actualizar las contraseñas de los usuarios existentes
Según la documentación oficial del proyecto
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import User
from auth import hash_password
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_user_passwords():
    """Actualizar contraseñas de usuarios según la documentación"""
    engine = create_engine(config.DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Usuarios según la documentación
        users_to_update = [
            {
                "email": "atea.dti@altea.es",
                "name": "Toni Alos",
                "password": "altea2025!"
            },
            {
                "email": "gerenciapstd@altea.es", 
                "name": "Iván Martí",
                "password": "altea2025!"
            }
        ]
        
        for user_data in users_to_update:
            email = user_data["email"]
            name = user_data["name"]
            password = user_data["password"]
            
            # Buscar usuario por email
            user = session.query(User).filter(User.email == email).first()
            
            if user:
                # Actualizar contraseña
                password_hash = hash_password(password)
                user.password_hash = password_hash
                logger.info(f"Contraseña actualizada para {name} ({email})")
            else:
                logger.warning(f"Usuario no encontrado: {name} ({email})")
        
        session.commit()
        logger.info("Todas las contraseñas actualizadas correctamente")
        
        # Verificar usuarios
        logger.info("Verificando usuarios...")
        users = session.query(User).filter(User.is_active == True).all()
        for user in users:
            logger.info(f"  - {user.name} ({user.email}) - ID: {user.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando contraseñas: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Actualizando contraseñas de usuarios...")
    
    if update_user_passwords():
        logger.info("Actualización completada exitosamente")
    else:
        logger.error("Error en la actualización")
        sys.exit(1) 