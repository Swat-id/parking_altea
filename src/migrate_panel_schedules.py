#!/usr/bin/env python3
"""
Script de migración para añadir las tablas de programaciones de paneles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import DB_URL
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_panel_schedule_tables():
    """Crear las tablas de programaciones de paneles"""
    
    engine = create_engine(DB_URL)
    
    try:
        with engine.connect() as conn:
            # Crear tabla panel_schedules
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS panel_schedules (
                    id SERIAL PRIMARY KEY,
                    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    
                    -- Información básica
                    name VARCHAR NOT NULL,
                    description TEXT,
                    
                    -- Fechas de vigencia
                    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    
                    -- Horario diario
                    start_time VARCHAR NOT NULL,
                    end_time VARCHAR NOT NULL,
                    
                    -- Días de la semana
                    monday BOOLEAN DEFAULT FALSE,
                    tuesday BOOLEAN DEFAULT FALSE,
                    wednesday BOOLEAN DEFAULT FALSE,
                    thursday BOOLEAN DEFAULT FALSE,
                    friday BOOLEAN DEFAULT FALSE,
                    saturday BOOLEAN DEFAULT FALSE,
                    sunday BOOLEAN DEFAULT FALSE,
                    
                    -- Configuración del mensaje
                    message TEXT NOT NULL,
                    color INTEGER DEFAULT 2,
                    font_size INTEGER DEFAULT 2,
                    effect VARCHAR DEFAULT 'static',
                    
                    -- Estado de la programación
                    is_active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 1,
                    
                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Crear tabla panel_schedule_logs
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS panel_schedule_logs (
                    id SERIAL PRIMARY KEY,
                    schedule_id INTEGER NOT NULL REFERENCES panel_schedules(id) ON DELETE CASCADE,
                    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
                    
                    -- Información de ejecución
                    execution_type VARCHAR NOT NULL,
                    message_sent TEXT,
                    panels_affected INTEGER DEFAULT 0,
                    
                    -- Timestamps
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Crear índices para mejorar rendimiento
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_panel_schedules_parking_id 
                ON panel_schedules(parking_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_panel_schedules_active 
                ON panel_schedules(is_active, start_date, end_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_panel_schedule_logs_schedule_id 
                ON panel_schedule_logs(schedule_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_panel_schedule_logs_executed_at 
                ON panel_schedule_logs(executed_at)
            """))
            
            # Añadir campo panel_display_text a la tabla parkings
            conn.execute(text("""
                ALTER TABLE parkings 
                ADD COLUMN IF NOT EXISTS panel_display_text TEXT
            """))
            
            logger.info("✅ Tablas de programaciones de paneles creadas exitosamente")
            
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        raise

def verify_migration():
    """Verificar que las tablas se crearon correctamente"""
    
    engine = create_engine(DB_URL)
    
    try:
        with engine.connect() as conn:
            # Verificar que las tablas existen
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('panel_schedules', 'panel_schedule_logs')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            if len(tables) == 2:
                logger.info("✅ Verificación exitosa: Todas las tablas creadas")
                return True
            else:
                logger.error(f"❌ Error en verificación: Tablas encontradas: {tables}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error en verificación: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando migración de programaciones de paneles...")
    
    try:
        create_panel_schedule_tables()
        
        if verify_migration():
            logger.info("🎉 Migración completada exitosamente")
        else:
            logger.error("❌ Migración falló en la verificación")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        sys.exit(1) 