#!/usr/bin/env python3
"""
Script de Migración para agregar campo texto_fijo_previo
Agrega el campo texto_fijo_previo a la tabla parking_panel_windows
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
        logging.FileHandler('migration_add_texto_fijo_previo.log'),
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

def add_texto_fijo_previo_column(engine):
    """Agregar columna texto_fijo_previo a parking_panel_windows"""
    logger.info("Agregando columna texto_fijo_previo a parking_panel_windows...")
    
    alter_sql = """
    ALTER TABLE parking_panel_windows 
    ADD COLUMN IF NOT EXISTS texto_fijo_previo VARCHAR(50);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(alter_sql))
            conn.commit()
        logger.info("✅ Columna texto_fijo_previo agregada exitosamente")
    except Exception as e:
        logger.error(f"Error agregando columna: {e}")
        raise

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("Iniciando migración: agregar texto_fijo_previo")
    logger.info("=" * 60)
    
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Conexión a base de datos establecida")
        
        # Agregar columna
        add_texto_fijo_previo_column(engine)
        
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

