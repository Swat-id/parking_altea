#!/usr/bin/env python3
"""
Script para verificar usuarios en la base de datos
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import User
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_users():
    """Verificar usuarios en la base de datos"""
    engine = create_engine(config.DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los usuarios
        users = session.query(User).all()
        
        logger.info("=" * 50)
        logger.info("USUARIOS EN LA BASE DE DATOS")
        logger.info("=" * 50)
        
        if not users:
            logger.info("No hay usuarios en la base de datos")
        else:
            for user in users:
                logger.info(f"ID: {user.id}")
                logger.info(f"Nombre: {user.name}")
                logger.info(f"Email: {user.email}")
                logger.info(f"Activo: {user.is_active}")
                logger.info(f"Creado: {user.created_at}")
                logger.info("-" * 30)
        
        # Verificar usuarios específicos según documentación
        logger.info("=" * 50)
        logger.info("VERIFICANDO USUARIOS SEGÚN DOCUMENTACIÓN")
        logger.info("=" * 50)
        
        expected_users = [
            "atea.dti@altea.es",
            "gerenciapstd@altea.es"
        ]
        
        for email in expected_users:
            user = session.query(User).filter(User.email == email).first()
            if user:
                logger.info(f"✅ {email} - ENCONTRADO (ID: {user.id})")
            else:
                logger.info(f"❌ {email} - NO ENCONTRADO")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando usuarios: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Verificando usuarios en la base de datos...")
    check_users() 