#!/usr/bin/env python3
"""
Script de Migración para agregar campos color y parking_status_config
Agrega el campo color a parking_panel_windows y parking_status_config a panel_window_configurations
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_add_color_and_status_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar configuración
try:
    from config import DB_URL
    DATABASE_URL = DB_URL
except ImportError:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

def add_color_column(engine):
    """Agregar columna color a parking_panel_windows"""
    logger.info("Agregando columna color a parking_panel_windows...")
    
    alter_sql = """
    ALTER TABLE parking_panel_windows 
    ADD COLUMN IF NOT EXISTS color INTEGER;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(alter_sql))
            conn.commit()
        logger.info("✅ Columna color agregada exitosamente")
    except Exception as e:
        logger.error(f"Error agregando columna color: {e}")
        raise

def add_parking_status_config_column(engine):
    """Agregar columna parking_status_config a panel_window_configurations"""
    logger.info("Agregando columna parking_status_config a panel_window_configurations...")
    
    alter_sql = """
    ALTER TABLE panel_window_configurations 
    ADD COLUMN IF NOT EXISTS parking_status_config JSONB;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(alter_sql))
            conn.commit()
        logger.info("✅ Columna parking_status_config agregada exitosamente")
    except Exception as e:
        logger.error(f"Error agregando columna parking_status_config: {e}")
        raise

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("Iniciando migración: agregar color y parking_status_config")
    logger.info("=" * 60)
    
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Conexión a base de datos establecida")
        
        # Agregar columnas
        add_color_column(engine)
        add_parking_status_config_column(engine)
        
        logger.info("=" * 60)
        logger.info("✅ Migración completada exitosamente")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error en migración: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()

