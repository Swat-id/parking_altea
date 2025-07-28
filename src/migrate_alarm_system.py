#!/usr/bin/env python3
"""
Script de migración para el sistema de alarmas v3.2.0_alarms
Crea las nuevas tablas necesarias para el sistema de alarmas
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import create_engine, text
from config import DB_URL
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_alarm_system():
    """Migración completa del sistema de alarmas"""
    
    engine = create_engine(DB_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("🚀 Iniciando migración del sistema de alarmas...")
            
            # 1. Crear tabla alarm_configurations
            logger.info("📋 Creando tabla alarm_configurations...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alarm_configurations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    alarm_type VARCHAR(50) NOT NULL CHECK (alarm_type IN ('panel', 'camera', 'parking')),
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 2. Crear tabla alarm_configuration_targets
            logger.info("📋 Creando tabla alarm_configuration_targets...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alarm_configuration_targets (
                    id SERIAL PRIMARY KEY,
                    alarm_configuration_id INTEGER REFERENCES alarm_configurations(id) ON DELETE CASCADE,
                    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('panel', 'camera', 'parking')),
                    target_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 3. Crear tabla alarm_configuration_thresholds
            logger.info("📋 Creando tabla alarm_configuration_thresholds...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alarm_configuration_thresholds (
                    id SERIAL PRIMARY KEY,
                    alarm_configuration_id INTEGER REFERENCES alarm_configurations(id) ON DELETE CASCADE,
                    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LEVE', 'NORMAL', 'GRAVE')),
                    threshold_value INTEGER NOT NULL CHECK (threshold_value > 0),
                    threshold_type VARCHAR(50) NOT NULL CHECK (threshold_type IN ('disconnection_time', 'occupancy_high', 'occupancy_low')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 4. Crear tabla alarms
            logger.info("📋 Creando tabla alarms...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alarms (
                    id SERIAL PRIMARY KEY,
                    alarm_configuration_id INTEGER REFERENCES alarm_configurations(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LEVE', 'NORMAL', 'GRAVE')),
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved')),
                    message TEXT NOT NULL,
                    affected_targets JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolution_description TEXT
                )
            """))
            
            # 5. Crear tabla alarm_history
            logger.info("📋 Creando tabla alarm_history...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alarm_history (
                    id SERIAL PRIMARY KEY,
                    alarm_id INTEGER REFERENCES alarms(id) ON DELETE CASCADE,
                    action VARCHAR(50) NOT NULL CHECK (action IN ('created', 'resolved', 'escalated')),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 6. Crear índices para optimización
            logger.info("📊 Creando índices de optimización...")
            
            # Índices para alarm_configurations
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_config_user_id ON alarm_configurations(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_config_type ON alarm_configurations(alarm_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_config_status ON alarm_configurations(status)"))
            
            # Índices para alarm_configuration_targets
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_targets_config_id ON alarm_configuration_targets(alarm_configuration_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_targets_type_id ON alarm_configuration_targets(target_type, target_id)"))
            
            # Índices para alarm_configuration_thresholds
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_thresholds_config_id ON alarm_configuration_thresholds(alarm_configuration_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_thresholds_severity ON alarm_configuration_thresholds(severity)"))
            
            # Índices para alarms
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarms_config_id ON alarms(alarm_configuration_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarms_user_id ON alarms(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarms_status ON alarms(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarms_severity ON alarms(severity)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarms_created_at ON alarms(created_at)"))
            
            # Índices para alarm_history
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_history_alarm_id ON alarm_history(alarm_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_history_action ON alarm_history(action)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alarm_history_created_at ON alarm_history(created_at)"))
            
            # 7. Crear constraints adicionales
            logger.info("🔒 Creando constraints adicionales...")
            
            # Constraint para evitar configuraciones duplicadas del mismo tipo por usuario
            conn.execute(text("""
                ALTER TABLE alarm_configurations 
                ADD CONSTRAINT unique_user_alarm_type 
                UNIQUE (user_id, name)
            """))
            
            # Constraint para evitar umbrales duplicados por configuración y severidad
            conn.execute(text("""
                ALTER TABLE alarm_configuration_thresholds 
                ADD CONSTRAINT unique_config_severity 
                UNIQUE (alarm_configuration_id, severity)
            """))
            
            # 8. Crear función para actualizar updated_at
            logger.info("⚙️ Creando función para updated_at...")
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            # 9. Crear trigger para updated_at en alarm_configurations
            conn.execute(text("""
                DROP TRIGGER IF EXISTS update_alarm_configurations_updated_at ON alarm_configurations;
                CREATE TRIGGER update_alarm_configurations_updated_at
                    BEFORE UPDATE ON alarm_configurations
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """))
            
            conn.commit()
            logger.info("✅ Migración del sistema de alarmas completada exitosamente")
            
            # 10. Verificar tablas creadas
            logger.info("🔍 Verificando tablas creadas...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'alarm%'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"📋 Tablas creadas: {', '.join(tables)}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        return False

def rollback_alarm_system():
    """Rollback de la migración del sistema de alarmas"""
    
    engine = create_engine(DB_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("🔄 Iniciando rollback del sistema de alarmas...")
            
            # Eliminar tablas en orden inverso (por dependencias)
            tables_to_drop = [
                'alarm_history',
                'alarms', 
                'alarm_configuration_thresholds',
                'alarm_configuration_targets',
                'alarm_configurations'
            ]
            
            for table in tables_to_drop:
                logger.info(f"🗑️ Eliminando tabla {table}...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            # Eliminar función
            conn.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE"))
            
            conn.commit()
            logger.info("✅ Rollback del sistema de alarmas completado")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error durante el rollback: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migración del sistema de alarmas')
    parser.add_argument('--rollback', action='store_true', help='Realizar rollback de la migración')
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_alarm_system()
    else:
        success = migrate_alarm_system()
    
    sys.exit(0 if success else 1) 