#!/usr/bin/env python3
"""
Script de Migración para Panel Tipo 4
======================================

Este script actualiza la base de datos para soportar Panel Tipo 4:
- Panel Tipo 4: Protocolo Nuevo - 16 Ventanas (0-15)
- Soporte para asignación de parkings y grupos de sensores a ventanas
- Configuración de rotación de contenido por ventana

Cambios realizados:
1. Crear tabla parking_panel_windows (asignación parking/panel/ventana/sensor_type)
2. Crear tabla panel_window_configurations (configuración de rotación)
3. Actualizar tabla panels (campo windows_count)
4. Insertar Panel Tipo 4 en panel_types
5. Migrar datos existentes
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_panel_type_4.log'),
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

def create_engine_and_session():
    """Crear engine y sesión de base de datos"""
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info("Conexión a base de datos establecida")
        return engine, session
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        sys.exit(1)

def create_parking_panel_windows_table(engine):
    """Crear tabla de asignación parking-panel-ventana"""
    logger.info("Creando tabla parking_panel_windows...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS parking_panel_windows (
        id SERIAL PRIMARY KEY,
        parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
        panel_id INTEGER NOT NULL REFERENCES panels(id) ON DELETE CASCADE,
        window_id INTEGER NOT NULL CHECK (window_id >= 0 AND window_id <= 15),
        sensor_type VARCHAR(20) CHECK (sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros', NULL)),
        display_type VARCHAR(20) DEFAULT 'parking' CHECK (display_type IN ('parking', 'sensor_group', 'mixed')),
        priority INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(panel_id, window_id, parking_id, sensor_type)
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        logger.info("Tabla parking_panel_windows creada exitosamente")
    except Exception as e:
        logger.error(f"Error creando tabla parking_panel_windows: {e}")
        raise

def create_panel_window_configurations_table(engine):
    """Crear tabla de configuración de ventanas"""
    logger.info("Creando tabla panel_window_configurations...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS panel_window_configurations (
        id SERIAL PRIMARY KEY,
        parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
        panel_id INTEGER NOT NULL REFERENCES panels(id) ON DELETE CASCADE,
        window_id INTEGER NOT NULL CHECK (window_id >= 0 AND window_id <= 15),
        company_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        rotation_enabled BOOLEAN DEFAULT TRUE,
        rotation_order JSONB,
        refresh_time_seconds INTEGER DEFAULT 5 CHECK (refresh_time_seconds > 0),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(panel_id, window_id, parking_id)
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        logger.info("Tabla panel_window_configurations creada exitosamente")
    except Exception as e:
        logger.error(f"Error creando tabla panel_window_configurations: {e}")
        raise

def create_indexes(engine):
    """Crear índices para las nuevas tablas"""
    logger.info("Creando índices...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_parking_panel_windows_parking_id ON parking_panel_windows(parking_id);",
        "CREATE INDEX IF NOT EXISTS idx_parking_panel_windows_panel_id ON parking_panel_windows(panel_id);",
        "CREATE INDEX IF NOT EXISTS idx_parking_panel_windows_window_id ON parking_panel_windows(window_id);",
        "CREATE INDEX IF NOT EXISTS idx_parking_panel_windows_sensor_type ON parking_panel_windows(sensor_type);",
        "CREATE INDEX IF NOT EXISTS idx_parking_panel_windows_panel_window ON parking_panel_windows(panel_id, window_id);",
        "CREATE INDEX IF NOT EXISTS idx_panel_window_config_parking_id ON panel_window_configurations(parking_id);",
        "CREATE INDEX IF NOT EXISTS idx_panel_window_config_panel_id ON panel_window_configurations(panel_id);",
        "CREATE INDEX IF NOT EXISTS idx_panel_window_config_company_id ON panel_window_configurations(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_panel_window_config_window_id ON panel_window_configurations(window_id);",
        "CREATE INDEX IF NOT EXISTS idx_panel_window_config_panel_window ON panel_window_configurations(panel_id, window_id);"
    ]
    
    try:
        with engine.connect() as conn:
            for index_sql in indexes:
                conn.execute(text(index_sql))
            conn.commit()
        logger.info("Índices creados exitosamente")
    except Exception as e:
        logger.error(f"Error creando índices: {e}")
        raise

def update_panels_table(engine):
    """Actualizar tabla panels con campo windows_count"""
    logger.info("Actualizando tabla panels...")
    
    update_sql = """
    ALTER TABLE panels 
    ADD COLUMN IF NOT EXISTS windows_count INTEGER DEFAULT 1 CHECK (windows_count >= 1 AND windows_count <= 16);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(update_sql))
            conn.commit()
        logger.info("Tabla panels actualizada exitosamente")
    except Exception as e:
        logger.error(f"Error actualizando tabla panels: {e}")
        raise

def insert_panel_type_4(session):
    """Insertar Panel Tipo 4 en panel_types"""
    logger.info("Insertando Panel Tipo 4...")
    
    # Obtener manufacturer_id (Rotulos Electrónicos)
    manufacturer_result = session.execute(
        text("SELECT id FROM manufacturers WHERE name = 'Rotulos Electrónicos'")
    )
    manufacturer_row = manufacturer_result.fetchone()
    
    if not manufacturer_row:
        logger.error("No se encontró el fabricante 'Rotulos Electrónicos'. Ejecutar migrate_panel_types.py primero.")
        raise ValueError("Fabricante no encontrado")
    
    manufacturer_id = manufacturer_row[0]
    
    # Verificar si ya existe Panel Tipo 4
    existing = session.execute(
        text("SELECT id FROM panel_types WHERE name LIKE '%Tipo 4%' OR windows_count = 16")
    ).fetchone()
    
    if existing:
        logger.info(f"Panel Tipo 4 ya existe con ID: {existing[0]}")
        return existing[0]
    
    # Insertar Panel Tipo 4
    insert_sql = """
    INSERT INTO panel_types (
        manufacturer_id, name, description, protocol_type, windows_count,
        window_width, window_height, total_width, total_height,
        port, service_endpoint, is_active
    ) VALUES (
        :manufacturer_id,
        'Panel Tipo 4 - Protocolo Nuevo - 16 Ventanas',
        'Panel LED con protocolo nuevo que soporta hasta 16 ventanas (0-15). Permite asignar parkings y grupos de sensores a ventanas específicas.',
        'new',
        16,
        64,  -- window_width (ajustar según especificaciones)
        8,   -- window_height (ajustar según especificaciones)
        1024, -- total_width (ajustar según especificaciones)
        128,  -- total_height (ajustar según especificaciones)
        5200,
        'http://localhost:7110/api/v1/panels/send-text',
        TRUE
    ) RETURNING id;
    """
    
    try:
        result = session.execute(text(insert_sql), {'manufacturer_id': manufacturer_id})
        panel_type_id = result.fetchone()[0]
        session.commit()
        logger.info(f"Panel Tipo 4 insertado con ID: {panel_type_id}")
        return panel_type_id
    except Exception as e:
        session.rollback()
        logger.error(f"Error insertando Panel Tipo 4: {e}")
        raise

def migrate_existing_panels(session):
    """Migrar paneles existentes a nuevas tablas"""
    logger.info("Migrando paneles existentes...")
    
    # Obtener todos los paneles
    panels_result = session.execute(
        text("SELECT id, parking_id, panel_type_id FROM panels")
    )
    panels = panels_result.fetchall()
    
    migrated_count = 0
    
    for panel in panels:
        panel_id = panel[0]
        parking_id = panel[1]
        panel_type_id = panel[2]
        
        # Obtener windows_count del panel_type
        if panel_type_id:
            windows_count_result = session.execute(
                text("SELECT windows_count FROM panel_types WHERE id = :panel_type_id"),
                {'panel_type_id': panel_type_id}
            )
            windows_count_row = windows_count_result.fetchone()
            windows_count = windows_count_row[0] if windows_count_row else 1
        else:
            windows_count = 1
        
        # Actualizar windows_count en panel
        session.execute(
            text("UPDATE panels SET windows_count = :windows_count WHERE id = :panel_id"),
            {'windows_count': windows_count, 'panel_id': panel_id}
        )
        
        # Crear asignación en parking_panel_windows para ventana 0 (parking general)
        # Verificar si ya existe
        existing_assignment = session.execute(
            text("""
                SELECT id FROM parking_panel_windows 
                WHERE panel_id = :panel_id AND window_id = 0 AND parking_id = :parking_id AND sensor_type IS NULL
            """),
            {'panel_id': panel_id, 'parking_id': parking_id}
        ).fetchone()
        
        if not existing_assignment:
            session.execute(
                text("""
                    INSERT INTO parking_panel_windows (
                        parking_id, panel_id, window_id, sensor_type, display_type, is_active
                    ) VALUES (
                        :parking_id, :panel_id, 0, NULL, 'parking', TRUE
                    )
                """),
                {'parking_id': parking_id, 'panel_id': panel_id}
            )
            migrated_count += 1
        
        # Si el panel tiene ventana 1 configurada (Tipo 3), crear asignación adicional
        if windows_count >= 2:
            existing_assignment_1 = session.execute(
                text("""
                    SELECT id FROM parking_panel_windows 
                    WHERE panel_id = :panel_id AND window_id = 1 AND parking_id = :parking_id AND sensor_type IS NULL
                """),
                {'panel_id': panel_id, 'parking_id': parking_id}
            ).fetchone()
            
            if not existing_assignment_1:
                session.execute(
                    text("""
                        INSERT INTO parking_panel_windows (
                            parking_id, panel_id, window_id, sensor_type, display_type, is_active
                        ) VALUES (
                            :parking_id, :panel_id, 1, NULL, 'parking', TRUE
                        )
                    """),
                    {'parking_id': parking_id, 'panel_id': panel_id}
                )
                migrated_count += 1
    
    session.commit()
    logger.info(f"Migración completada: {migrated_count} asignaciones creadas para {len(panels)} paneles")
    return migrated_count

def verify_migration(session):
    """Verificar que la migración se completó correctamente"""
    logger.info("Verificando migración...")
    
    # Verificar Panel Tipo 4
    panel_type_4 = session.execute(
        text("SELECT id, name, windows_count FROM panel_types WHERE windows_count = 16")
    ).fetchone()
    
    if not panel_type_4:
        logger.warning("⚠️  Panel Tipo 4 no encontrado")
        return False
    
    logger.info(f"✅ Panel Tipo 4 encontrado: ID={panel_type_4[0]}, Name={panel_type_4[1]}, Windows={panel_type_4[2]}")
    
    # Verificar tablas
    tables_check = [
        ("parking_panel_windows", "SELECT COUNT(*) FROM parking_panel_windows"),
        ("panel_window_configurations", "SELECT COUNT(*) FROM panel_window_configurations")
    ]
    
    for table_name, query in tables_check:
        result = session.execute(text(query))
        count = result.fetchone()[0]
        logger.info(f"✅ Tabla {table_name}: {count} registros")
    
    # Verificar campo windows_count en panels
    panels_with_windows = session.execute(
        text("SELECT COUNT(*) FROM panels WHERE windows_count IS NOT NULL")
    ).fetchone()[0]
    
    total_panels = session.execute(
        text("SELECT COUNT(*) FROM panels")
    ).fetchone()[0]
    
    logger.info(f"✅ Paneles con windows_count: {panels_with_windows}/{total_panels}")
    
    return True

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("Iniciando migración para Panel Tipo 4")
    logger.info("=" * 60)
    
    try:
        # 1. Conectar a base de datos
        engine, session = create_engine_and_session()
        
        # 2. Crear tablas
        create_parking_panel_windows_table(engine)
        create_panel_window_configurations_table(engine)
        
        # 3. Crear índices
        create_indexes(engine)
        
        # 4. Actualizar tabla panels
        update_panels_table(engine)
        
        # 5. Insertar Panel Tipo 4
        panel_type_4_id = insert_panel_type_4(session)
        
        # 6. Migrar datos existentes
        migrate_existing_panels(session)
        
        # 7. Verificar migración
        if verify_migration(session):
            logger.info("=" * 60)
            logger.info("✅ Migración completada exitosamente")
            logger.info("=" * 60)
        else:
            logger.warning("⚠️  Migración completada con advertencias")
        
        session.close()
        
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()

