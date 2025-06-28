#!/usr/bin/env python3

import logging
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    from models import Access
    from config import db
    
    logger.info("Verificando cámaras de parkings 4 y 8 en la base de datos...")
    logger.info("=" * 50)
    
    db.connect()
    
    # Consultar cámaras de parkings 4 y 8
    accesses = Access.select().where(Access.parking_id.in_([4, 8]))
    
    if accesses.count() == 0:
        logger.info("❌ NO HAY CÁMARAS CONFIGURADAS para parkings 4 y 8")
    else:
        logger.info("✅ CÁMARAS ENCONTRADAS:")
        for access in accesses:
            logger.info(f"  - Parking {access.parking_id}: {access.device_name} ({access.ip})")
    
    logger.info("=" * 50)
    logger.info("TODAS LAS CÁMARAS EN LA BASE DE DATOS:")
    logger.info("=" * 50)
    all_accesses = Access.select()
    for access in all_accesses:
        logger.info(f"  - Parking {access.parking_id}: {access.device_name} ({access.ip})")
    
    db.close()
    
except Exception as e:
    logger.error(f"Error: {e}")
    if 'db' in locals():
        db.close() 