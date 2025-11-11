#!/usr/bin/env python3
"""
Script de Migración para configuraciones a nivel de empresa
- Hace panel_id nullable en panel_window_configurations
- Cambia el constraint único para que sea por company_id, window_id, parking_id
- Actualiza configuraciones existentes con panel_id=0 a NULL
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
        logging.FileHandler('migration_panel_config_company_level.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar configuración
try:
    from config import DB_URL
    DATABASE_URL = DB_URL
except ImportError:
    # Fallback si no se puede importar config
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

def migrate_panel_config_company_level(engine):
    """Migra configuraciones a nivel de empresa"""
    logger.info("Iniciando migración de configuraciones a nivel de empresa...")
    
    try:
        with engine.connect() as conn:
            # 1. Eliminar constraint único antiguo
            logger.info("Eliminando constraint único antiguo...")
            try:
                conn.execute(text("""
                    ALTER TABLE panel_window_configurations
                    DROP CONSTRAINT IF EXISTS unique_panel_window_parking_config;
                """))
                conn.commit()
                logger.info("✅ Constraint único antiguo eliminado")
            except Exception as e:
                logger.warning(f"⚠️  No se pudo eliminar constraint antiguo (puede no existir): {e}")
            
            # 2. Hacer panel_id nullable
            logger.info("Haciendo panel_id nullable...")
            conn.execute(text("""
                ALTER TABLE panel_window_configurations
                ALTER COLUMN panel_id DROP NOT NULL;
            """))
            conn.commit()
            logger.info("✅ panel_id ahora es nullable")
            
            # 3. Actualizar panel_id=0 a NULL (configuraciones preparatorias)
            logger.info("Actualizando panel_id=0 a NULL...")
            result = conn.execute(text("""
                UPDATE panel_window_configurations
                SET panel_id = NULL
                WHERE panel_id = 0;
            """))
            conn.commit()
            updated_count = result.rowcount
            logger.info(f"✅ {updated_count} configuración(es) actualizada(s) (panel_id=0 -> NULL)")
            
            # 4. Crear nuevo constraint único por company_id, window_id, parking_id
            logger.info("Creando nuevo constraint único por empresa...")
            try:
                conn.execute(text("""
                    ALTER TABLE panel_window_configurations
                    ADD CONSTRAINT unique_company_window_parking_config
                    UNIQUE (company_id, window_id, parking_id);
                """))
                conn.commit()
                logger.info("✅ Nuevo constraint único creado")
            except Exception as e:
                logger.warning(f"⚠️  No se pudo crear constraint único (puede ya existir): {e}")
                # Intentar sin el constraint si ya existe
                conn.rollback()
            
            logger.info("✅ Migración de configuraciones a nivel de empresa completada")
            
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        raise

def run_migration():
    logger.info("=" * 60)
    logger.info("Iniciando migración: Configuraciones a nivel de empresa")
    logger.info("=" * 60)
    
    engine = None
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Conexión a base de datos establecida")
        
        migrate_panel_config_company_level(engine)
        
        logger.info("=" * 60)
        logger.info("✅ Migración completada exitosamente")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Migración fallida: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    run_migration()

