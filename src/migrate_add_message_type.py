#!/usr/bin/env python3
"""
Migración: Añadir campo message_type a tabla parkings
Versión: v3.4.1
Fecha: 2025-08-29

Este script añade el campo message_type a la tabla parkings para configurar
qué tipo de información se envía a los paneles por parking:
- 'ESTADO': Envía LLIURE, DENS, COMPLET
- 'PLAZAS_LIBRES': Envía solo el número de plazas libres
"""

import logging
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DB_URL

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_add_message_type():
    """Ejecutar migración para añadir campo message_type"""
    
    logger.info("=== MIGRACIÓN: Añadir campo message_type a parkings ===")
    
    try:
        # Conectar a la base de datos
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 1. Verificar si el campo ya existe
        logger.info("1. Verificando si el campo message_type ya existe...")
        
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'parkings' AND column_name = 'message_type'
        """)).fetchone()
        
        if result:
            logger.info("✅ El campo message_type ya existe en la tabla parkings")
            session.close()
            return True
        
        # 2. Añadir campo message_type
        logger.info("2. Añadiendo campo message_type a tabla parkings...")
        
        session.execute(text("""
            ALTER TABLE parkings 
            ADD COLUMN IF NOT EXISTS message_type VARCHAR(20) DEFAULT 'ESTADO' NOT NULL
        """))
        
        logger.info("✅ Campo message_type añadido correctamente")
        
        # 3. Verificar que todos los parkings tienen el valor por defecto
        logger.info("3. Verificando valores por defecto...")
        
        result = session.execute(text("""
            SELECT COUNT(*) as total_parkings, 
                   SUM(CASE WHEN message_type = 'ESTADO' THEN 1 ELSE 0 END) as estado_count,
                   SUM(CASE WHEN message_type IS NULL THEN 1 ELSE 0 END) as null_count
            FROM parkings
        """)).fetchone()
        
        total = result[0]
        estado_count = result[1] 
        null_count = result[2]
        
        logger.info(f"📊 Verificación: {total} parkings total, {estado_count} con 'ESTADO', {null_count} con NULL")
        
        if null_count > 0:
            logger.warning(f"⚠️  {null_count} parkings con message_type NULL - actualizando...")
            session.execute(text("UPDATE parkings SET message_type = 'ESTADO' WHERE message_type IS NULL"))
        
        # 4. Commit de cambios
        session.commit()
        logger.info("✅ Migración completada exitosamente")
        
        # 5. Mostrar estadísticas finales
        result = session.execute(text("""
            SELECT id, name, message_type 
            FROM parkings 
            ORDER BY id 
            LIMIT 5
        """)).fetchall()
        
        logger.info("📋 Primeros 5 parkings con configuración:")
        for row in result:
            logger.info(f"   {row[0]} - {row[1]} -> {row[2]}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def rollback_message_type():
    """Rollback: Eliminar campo message_type"""
    
    logger.info("=== ROLLBACK: Eliminar campo message_type ===")
    
    try:
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("Eliminando campo message_type de tabla parkings...")
        
        session.execute(text("ALTER TABLE parkings DROP COLUMN IF EXISTS message_type"))
        session.commit()
        
        logger.info("✅ Rollback completado - Campo message_type eliminado")
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante rollback: {e}")
        if 'session' in locals():
            session.rollback() 
            session.close()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_message_type()
    else:
        success = migrate_add_message_type()
    
    sys.exit(0 if success else 1)
