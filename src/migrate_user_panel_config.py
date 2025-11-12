#!/usr/bin/env python3
"""
Script de Migración para crear la tabla user_panel_configs
y asignar 120 segundos (2 minutos) de intervalo de actualización a todos los usuarios
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
        logging.FileHandler('migration_user_panel_config.log'),
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

def migrate_user_panel_config(engine):
    """Crear tabla user_panel_configs y asignar configuración a usuarios"""
    logger.info("Iniciando migración de configuración de paneles por usuario...")
    
    try:
        with engine.connect() as conn:
            # 1. Crear tabla user_panel_configs
            logger.info("Creando tabla user_panel_configs...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_panel_configs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    panel_update_interval_seconds INTEGER NOT NULL DEFAULT 120,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT fk_user_panel_config_user FOREIGN KEY (user_id) 
                        REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT check_update_interval_positive 
                        CHECK (panel_update_interval_seconds > 0)
                );
            """))
            conn.commit()
            logger.info("✅ Tabla user_panel_configs creada")
            
            # 2. Crear índice único en user_id (ya está en UNIQUE, pero por si acaso)
            logger.info("Creando índices...")
            try:
                conn.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_user_panel_config_user_id 
                    ON user_panel_configs(user_id);
                """))
                conn.commit()
                logger.info("✅ Índice único creado")
            except Exception as e:
                logger.warning(f"⚠️  Índice puede ya existir: {e}")
            
            # 3. Obtener todos los usuarios existentes
            logger.info("Obteniendo usuarios existentes...")
            result = conn.execute(text("SELECT id FROM users"))
            user_ids = [row[0] for row in result]
            logger.info(f"✅ Encontrados {len(user_ids)} usuarios")
            
            # 4. Crear configuración para cada usuario con 120 segundos (2 minutos)
            logger.info("Asignando configuración de 120 segundos a todos los usuarios...")
            inserted_count = 0
            updated_count = 0
            
            for user_id in user_ids:
                # Verificar si ya existe configuración para este usuario
                check_result = conn.execute(text("""
                    SELECT id FROM user_panel_configs WHERE user_id = :user_id
                """), {"user_id": user_id})
                existing = check_result.fetchone()
                
                if existing:
                    # Actualizar si existe
                    conn.execute(text("""
                        UPDATE user_panel_configs 
                        SET panel_update_interval_seconds = 120,
                            updated_at = NOW()
                        WHERE user_id = :user_id
                    """), {"user_id": user_id})
                    updated_count += 1
                else:
                    # Insertar si no existe
                    conn.execute(text("""
                        INSERT INTO user_panel_configs 
                        (user_id, panel_update_interval_seconds, is_active, created_at, updated_at)
                        VALUES (:user_id, 120, TRUE, NOW(), NOW())
                    """), {"user_id": user_id})
                    inserted_count += 1
            
            conn.commit()
            logger.info(f"✅ Configuración asignada: {inserted_count} insertadas, {updated_count} actualizadas")
            
            # 5. Verificar que todos los usuarios tienen configuración
            verify_result = conn.execute(text("""
                SELECT COUNT(*) FROM users u
                LEFT JOIN user_panel_configs upc ON u.id = upc.user_id
                WHERE upc.id IS NULL
            """))
            missing_count = verify_result.scalar()
            
            if missing_count > 0:
                logger.warning(f"⚠️  {missing_count} usuarios sin configuración (puede ser normal si se crearon después)")
            else:
                logger.info("✅ Todos los usuarios tienen configuración asignada")
            
            logger.info("✅ Migración de configuración de paneles por usuario completada exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en migración de configuración de paneles por usuario: {e}")
        raise

def run_migration():
    logger.info("============================================================")
    logger.info("Iniciando migración: user_panel_configs")
    logger.info("============================================================")
    
    engine = None
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Conexión a base de datos establecida")
        
        migrate_user_panel_config(engine)
        
        logger.info("============================================================")
        logger.info("✅ Migración completada exitosamente")
        logger.info("============================================================")
    except Exception as e:
        logger.error(f"❌ Migración fallida: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if engine:
            engine.dispose()

if __name__ == '__main__':
    run_migration()

