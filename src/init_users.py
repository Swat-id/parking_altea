#!/usr/bin/env python3
"""
Script para inicializar usuarios y asignar permisos
Crea los usuarios Toni Alos e Iván Martí con acceso a todos los recursos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base, User, UserParking, UserPanel, UserAccess, Parking, Panel, Access
from auth import create_user, assign_user_to_resources
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_users():
    """Inicializar usuarios y asignar permisos"""
    engine = create_engine(config.DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    
    # Crear tablas si no existen
    Base.metadata.create_all(engine)
    
    session = Session()
    
    try:
        # Crear usuario Toni Alos
        logger.info("Creando usuario Toni Alos...")
        toni_result = create_user(session, "Toni Alos", "atea.dti@altea.es", "altea2025!")
        
        if not toni_result['success']:
            logger.error(f"Error creando Toni Alos: {toni_result['error']}")
            return False
        
        toni_user_id = toni_result['user']['id']
        logger.info(f"Usuario Toni Alos creado con ID: {toni_user_id}")
        
        # Crear usuario Iván Martí
        logger.info("Creando usuario Iván Martí...")
        ivan_result = create_user(session, "Iván Martí", "gerenciapstd@altea.es", "altea2025!")
        
        if not ivan_result['success']:
            logger.error(f"Error creando Iván Martí: {ivan_result['error']}")
            return False
        
        ivan_user_id = ivan_result['user']['id']
        logger.info(f"Usuario Iván Martí creado con ID: {ivan_user_id}")
        
        # Obtener todos los parkings, paneles y cámaras
        all_parkings = session.query(Parking).all()
        all_panels = session.query(Panel).all()
        all_accesses = session.query(Access).all()
        
        parking_ids = [p.id for p in all_parkings]
        panel_ids = [p.id for p in all_panels]
        access_ids = [a.id for a in all_accesses]
        
        logger.info(f"Recursos encontrados: {len(parking_ids)} parkings, {len(panel_ids)} paneles, {len(access_ids)} cámaras")
        
        # Asignar todos los recursos a Toni Alos
        logger.info("Asignando recursos a Toni Alos...")
        toni_assign_result = assign_user_to_resources(
            session, toni_user_id, parking_ids, panel_ids, access_ids
        )
        
        if not toni_assign_result['success']:
            logger.error(f"Error asignando recursos a Toni: {toni_assign_result['error']}")
            return False
        
        logger.info("Recursos asignados a Toni Alos correctamente")
        
        # Asignar todos los recursos a Iván Martí
        logger.info("Asignando recursos a Iván Martí...")
        ivan_assign_result = assign_user_to_resources(
            session, ivan_user_id, parking_ids, panel_ids, access_ids
        )
        
        if not ivan_assign_result['success']:
            logger.error(f"Error asignando recursos a Iván: {ivan_assign_result['error']}")
            return False
        
        logger.info("Recursos asignados a Iván Martí correctamente")
        
        session.commit()
        
        # Mostrar resumen
        logger.info("=" * 50)
        logger.info("INICIALIZACIÓN DE USUARIOS COMPLETADA")
        logger.info("=" * 50)
        logger.info(f"Usuario 1: Toni Alos (ID: {toni_user_id})")
        logger.info(f"  Email: atea.dti@altea.es")
        logger.info(f"  Contraseña: altea2025!")
        logger.info(f"  Acceso a: {len(parking_ids)} parkings, {len(panel_ids)} paneles, {len(access_ids)} cámaras")
        logger.info("")
        logger.info(f"Usuario 2: Iván Martí (ID: {ivan_user_id})")
        logger.info(f"  Email: gerenciapstd@altea.es")
        logger.info(f"  Contraseña: altea2025!")
        logger.info(f"  Acceso a: {len(parking_ids)} parkings, {len(panel_ids)} paneles, {len(access_ids)} cámaras")
        logger.info("")
        logger.info("Ambos usuarios tienen acceso completo a todos los recursos del sistema.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en la inicialización: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def verify_users():
    """Verificar que los usuarios se crearon correctamente"""
    engine = create_engine(config.DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar usuarios
        users = session.query(User).filter(User.is_active == True).all()
        logger.info(f"Usuarios activos encontrados: {len(users)}")
        
        for user in users:
            logger.info(f"  - {user.name} ({user.email}) - ID: {user.id}")
            
            # Verificar permisos
            user_parkings = session.query(UserParking).filter(UserParking.user_id == user.id).count()
            user_panels = session.query(UserPanel).filter(UserPanel.user_id == user.id).count()
            user_accesses = session.query(UserAccess).filter(UserAccess.user_id == user.id).count()
            
            logger.info(f"    Parkings: {user_parkings}, Paneles: {user_panels}, Cámaras: {user_accesses}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando usuarios: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Iniciando configuración de usuarios...")
    
    if init_users():
        logger.info("Configuración completada exitosamente")
        logger.info("Verificando usuarios...")
        verify_users()
    else:
        logger.error("Error en la configuración de usuarios")
        sys.exit(1) 