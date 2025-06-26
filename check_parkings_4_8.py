#!/usr/bin/env python3

import logging
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from models import Parking, Access
    from config import db
    
    logger.info("Verificando parkings 4 y 8 en la base de datos...")
    logger.info("=" * 50)
    logger.info("PARKINGS 4 Y 8 - CONFIGURACIÓN DE CÁMARAS")
    logger.info("=" * 50)
    
    db.connect()
    
    parkings = Parking.select().where(Parking.id.in_([4, 8]))
    
    for parking in parkings:
        logger.info(f"Parking {parking.id}: {parking.name}")
        logger.info(f"  - Total plazas: {parking.total_plazas}")
        logger.info(f"  - Plazas ocupadas: {parking.plazas_ocupadas}")
        logger.info(f"  - Estado: {parking.estado}")
        logger.info(f"  - Cámaras configuradas:")
        
        accesses = Access.select().where(Access.parking_id == parking.id)
        if accesses.count() == 0:
            logger.info("    * NO HAY CÁMARAS CONFIGURADAS")
        else:
            for access in accesses:
                logger.info(f"    * Access ID {access.id}: {access.device_name} (line {access.line})")
        
        logger.info("-" * 30)
    
    logger.info("=" * 50)
    logger.info("TODAS LAS CÁMARAS ACTIVAS EN EL SISTEMA")
    logger.info("=" * 50)
    all_accesses = Access.select()
    for access in all_accesses:
        logger.info(f"  - Parking {access.parking_id}: {access.device_name} (line {access.line})")
    
    db.close()
    
except Exception as e:
    logger.error(f"Error: {e}")
    if 'db' in locals():
        db.close() 