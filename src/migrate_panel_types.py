#!/usr/bin/env python3
"""
Script de Migración para Tipos de Paneles
=========================================

Este script actualiza la base de datos para soportar tres tipos de paneles:
- Panel Tipo 1: Rotulos eléctronicos, 1 ventana, 1 línea 64x16, protocolo antiguo
- Panel Tipo 2: Rotulos Electrónicos, 1 ventana, 1 línea 64x16, protocolo nuevo
- Panel Tipo 3: Rotulos Electrónicos, 2 ventanas, 32x16 cada una, protocolo nuevo

Cambios realizados:
1. Crear tabla de fabricantes
2. Crear tabla de tipos de paneles
3. Actualizar tabla de paneles con nuevos campos
4. Migrar paneles existentes al tipo 1 (protocolo antiguo)
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_panel_types.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://parking_user:parking_pass@localhost:5432/parking_altea')

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

def create_manufacturers_table(engine):
    """Crear tabla de fabricantes"""
    logger.info("Creando tabla de fabricantes...")
    
    create_manufacturers_sql = """
    CREATE TABLE IF NOT EXISTS manufacturers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        website VARCHAR(255),
        contact_email VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_manufacturers_sql))
            conn.commit()
        logger.info("Tabla manufacturers creada exitosamente")
    except Exception as e:
        logger.error(f"Error creando tabla manufacturers: {e}")
        raise

def create_panel_types_table(engine):
    """Crear tabla de tipos de paneles"""
    logger.info("Creando tabla de tipos de paneles...")
    
    create_panel_types_sql = """
    CREATE TABLE IF NOT EXISTS panel_types (
        id SERIAL PRIMARY KEY,
        manufacturer_id INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        protocol_type VARCHAR(50) NOT NULL, -- 'old', 'new'
        windows_count INTEGER NOT NULL DEFAULT 1,
        window_width INTEGER NOT NULL, -- Ancho de cada ventana
        window_height INTEGER NOT NULL, -- Alto de cada ventana
        total_width INTEGER NOT NULL, -- Ancho total del panel
        total_height INTEGER NOT NULL, -- Alto total del panel
        port INTEGER NOT NULL DEFAULT 5200,
        service_endpoint VARCHAR(255), -- URL del servicio a usar
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id)
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_panel_types_sql))
            conn.commit()
        logger.info("Tabla panel_types creada exitosamente")
    except Exception as e:
        logger.error(f"Error creando tabla panel_types: {e}")
        raise

def update_panels_table(engine):
    """Actualizar tabla de paneles con nuevos campos"""
    logger.info("Actualizando tabla de paneles...")
    
    # Añadir nuevos campos a la tabla panels
    alter_panels_sql = """
    ALTER TABLE panels 
    ADD COLUMN IF NOT EXISTS panel_type_id INTEGER,
    ADD COLUMN IF NOT EXISTS port INTEGER DEFAULT 5200,
    ADD COLUMN IF NOT EXISTS window_config JSONB,
    ADD COLUMN IF NOT EXISTS protocol_version VARCHAR(20) DEFAULT 'old',
    ADD COLUMN IF NOT EXISTS service_endpoint VARCHAR(255),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS last_protocol_check TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS protocol_status VARCHAR(20) DEFAULT 'unknown';
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(alter_panels_sql))
            conn.commit()
        logger.info("Tabla panels actualizada exitosamente")
    except Exception as e:
        logger.error(f"Error actualizando tabla panels: {e}")
        raise

def insert_manufacturer_data(session):
    """Insertar datos del fabricante Rotulos Electrónicos"""
    logger.info("Insertando datos del fabricante...")
    
    try:
        # Verificar si ya existe
        existing = session.execute(text("SELECT id FROM manufacturers WHERE name = 'Rotulos Electrónicos'")).fetchone()
        
        if not existing:
            insert_manufacturer_sql = """
            INSERT INTO manufacturers (name, description, website, contact_email)
            VALUES (
                'Rotulos Electrónicos',
                'Fabricante especializado en paneles LED para sistemas de parking y señalización',
                'https://www.rotuloselectronicos.com',
                'info@rotuloselectronicos.com'
            ) RETURNING id;
            """
            
            result = session.execute(text(insert_manufacturer_sql))
            manufacturer_id = result.fetchone()[0]
            session.commit()
            logger.info(f"Fabricante insertado con ID: {manufacturer_id}")
            return manufacturer_id
        else:
            logger.info("Fabricante ya existe en la base de datos")
            return existing[0]
            
    except Exception as e:
        logger.error(f"Error insertando fabricante: {e}")
        session.rollback()
        raise

def insert_panel_types_data(session, manufacturer_id):
    """Insertar los tres tipos de paneles"""
    logger.info("Insertando tipos de paneles...")
    
    panel_types_data = [
        {
            'name': 'Panel Tipo 1 - Protocolo Antiguo',
            'description': 'Panel Rotulos Electrónicos con 1 ventana, 1 línea 64x16, protocolo antiguo',
            'protocol_type': 'old',
            'windows_count': 1,
            'window_width': 64,
            'window_height': 16,
            'total_width': 64,
            'total_height': 16,
            'port': 5200,
            'service_endpoint': 'http://localhost:3000/api/panels/send'
        },
        {
            'name': 'Panel Tipo 2 - Protocolo Nuevo 1 Ventana',
            'description': 'Panel Rotulos Electrónicos con 1 ventana, 1 línea 64x16, protocolo nuevo',
            'protocol_type': 'new',
            'windows_count': 1,
            'window_width': 64,
            'window_height': 16,
            'total_width': 64,
            'total_height': 16,
            'port': 5200,
            'service_endpoint': 'http://localhost:5657/api/v1/panels/send'
        },
        {
            'name': 'Panel Tipo 3 - Protocolo Nuevo 2 Ventanas',
            'description': 'Panel Rotulos Electrónicos con 2 ventanas, 32x16 cada una, protocolo nuevo',
            'protocol_type': 'new',
            'windows_count': 2,
            'window_width': 32,
            'window_height': 16,
            'total_width': 64,
            'total_height': 16,
            'port': 5200,
            'service_endpoint': 'http://localhost:5657/api/v1/panels/send'
        }
    ]
    
    try:
        for panel_type in panel_types_data:
            # Verificar si ya existe
            existing = session.execute(
                text("SELECT id FROM panel_types WHERE name = :name"),
                {'name': panel_type['name']}
            ).fetchone()
            
            if not existing:
                insert_panel_type_sql = """
                INSERT INTO panel_types (
                    manufacturer_id, name, description, protocol_type, 
                    windows_count, window_width, window_height, 
                    total_width, total_height, port, service_endpoint
                ) VALUES (
                    :manufacturer_id, :name, :description, :protocol_type,
                    :windows_count, :window_width, :window_height,
                    :total_width, :total_height, :port, :service_endpoint
                ) RETURNING id;
                """
                
                result = session.execute(text(insert_panel_type_sql), {
                    'manufacturer_id': manufacturer_id,
                    **panel_type
                })
                panel_type_id = result.fetchone()[0]
                logger.info(f"Tipo de panel '{panel_type['name']}' insertado con ID: {panel_type_id}")
            else:
                logger.info(f"Tipo de panel '{panel_type['name']}' ya existe")
        
        session.commit()
        
    except Exception as e:
        logger.error(f"Error insertando tipos de paneles: {e}")
        session.rollback()
        raise

def migrate_existing_panels(session):
    """Migrar paneles existentes al tipo 1 (protocolo antiguo)"""
    logger.info("Migrando paneles existentes al tipo 1...")
    
    try:
        # Obtener el ID del tipo de panel 1 (protocolo antiguo)
        panel_type_1 = session.execute(
            text("SELECT id FROM panel_types WHERE name LIKE '%Protocolo Antiguo%'")
        ).fetchone()
        
        if not panel_type_1:
            logger.error("No se encontró el tipo de panel 1")
            return
        
        panel_type_1_id = panel_type_1[0]
        
        # Actualizar todos los paneles existentes
        update_panels_sql = """
        UPDATE panels 
        SET 
            panel_type_id = :panel_type_id,
            protocol_version = 'old',
            service_endpoint = 'http://localhost:3000/api/panels/send',
            window_config = '{"windows": [{"id": 0, "coordinates": [0, 0, 64, 16], "description": "Ventana Principal"}]}',
            is_active = TRUE
        WHERE panel_type_id IS NULL;
        """
        
        result = session.execute(text(update_panels_sql), {
            'panel_type_id': panel_type_1_id
        })
        
        updated_count = result.rowcount
        session.commit()
        logger.info(f"Migrados {updated_count} paneles al tipo 1 (protocolo antiguo)")
        
    except Exception as e:
        logger.error(f"Error migrando paneles existentes: {e}")
        session.rollback()
        raise

def create_indexes(engine):
    """Crear índices para mejorar rendimiento"""
    logger.info("Creando índices...")
    
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_panels_panel_type_id ON panels(panel_type_id);",
        "CREATE INDEX IF NOT EXISTS idx_panels_protocol_version ON panels(protocol_version);",
        "CREATE INDEX IF NOT EXISTS idx_panels_is_active ON panels(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_panel_types_manufacturer_id ON panel_types(manufacturer_id);",
        "CREATE INDEX IF NOT EXISTS idx_panel_types_protocol_type ON panel_types(protocol_type);",
        "CREATE INDEX IF NOT EXISTS idx_panel_types_is_active ON panel_types(is_active);"
    ]
    
    try:
        with engine.connect() as conn:
            for index_sql in indexes_sql:
                conn.execute(text(index_sql))
            conn.commit()
        logger.info("Índices creados exitosamente")
    except Exception as e:
        logger.error(f"Error creando índices: {e}")
        raise

def verify_migration(session):
    """Verificar que la migración se realizó correctamente"""
    logger.info("Verificando migración...")
    
    try:
        # Verificar fabricante
        manufacturer_count = session.execute(
            text("SELECT COUNT(*) FROM manufacturers WHERE name = 'Rotulos Electrónicos'")
        ).fetchone()[0]
        
        # Verificar tipos de paneles
        panel_types_count = session.execute(
            text("SELECT COUNT(*) FROM panel_types")
        ).fetchone()[0]
        
        # Verificar paneles migrados
        migrated_panels_count = session.execute(
            text("SELECT COUNT(*) FROM panels WHERE panel_type_id IS NOT NULL")
        ).fetchone()[0]
        
        total_panels_count = session.execute(
            text("SELECT COUNT(*) FROM panels")
        ).fetchone()[0]
        
        logger.info(f"Verificación completada:")
        logger.info(f"  - Fabricantes: {manufacturer_count}")
        logger.info(f"  - Tipos de paneles: {panel_types_count}")
        logger.info(f"  - Paneles migrados: {migrated_panels_count}/{total_panels_count}")
        
        if migrated_panels_count == total_panels_count and panel_types_count == 3:
            logger.info("✅ Migración completada exitosamente")
            return True
        else:
            logger.warning("⚠️  Migración incompleta - revisar logs")
            return False
            
    except Exception as e:
        logger.error(f"Error verificando migración: {e}")
        return False

def main():
    """Función principal de migración"""
    logger.info("Iniciando migración de tipos de paneles...")
    logger.info("=" * 60)
    
    try:
        # Crear conexión
        engine, session = create_engine_and_session()
        
        # Ejecutar migración
        create_manufacturers_table(engine)
        create_panel_types_table(engine)
        update_panels_table(engine)
        
        manufacturer_id = insert_manufacturer_data(session)
        insert_panel_types_data(session, manufacturer_id)
        migrate_existing_panels(session)
        create_indexes(engine)
        
        # Verificar migración
        success = verify_migration(session)
        
        session.close()
        engine.dispose()
        
        if success:
            logger.info("🎉 Migración completada exitosamente")
            logger.info("Los paneles existentes han sido migrados al tipo 1 (protocolo antiguo)")
            logger.info("Ahora puedes actualizar los tipos de panel desde el menú de administración")
        else:
            logger.error("❌ Migración falló - revisar logs")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error en migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 