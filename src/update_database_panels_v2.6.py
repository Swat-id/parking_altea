#!/usr/bin/env python3
"""
Script de migración para actualizar la base de datos con nuevos campos de paneles
y tabla de idiomas para la versión 2.6
"""

import psycopg2
import sys
import os
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'parking_db',
    'user': 'parking_user',
    'password': 'parking_pass'
}

def connect_db():
    """Conectar a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        sys.exit(1)

def execute_migration(conn, migration_name, sql):
    """Ejecutar una migración específica"""
    try:
        cursor = conn.cursor()
        print(f"Ejecutando migración: {migration_name}")
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        print(f"✅ Migración {migration_name} completada exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error en migración {migration_name}: {e}")
        conn.rollback()
        return False

def add_panel_columns():
    """Añadir nuevas columnas a la tabla panels"""
    sql = """
    ALTER TABLE panels 
    ADD COLUMN IF NOT EXISTS fabricante VARCHAR(100) DEFAULT 'Rótulos electrónicos',
    ADD COLUMN IF NOT EXISTS num_pantallas INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS resolucion_ancho INTEGER DEFAULT 64,
    ADD COLUMN IF NOT EXISTS resolucion_alto INTEGER DEFAULT 16,
    ADD COLUMN IF NOT EXISTS tipo_visualizacion VARCHAR(20) DEFAULT 'plazas',
    ADD COLUMN IF NOT EXISTS idioma_principal VARCHAR(10) DEFAULT 'valenciano',
    ADD COLUMN IF NOT EXISTS idiomas_secundarios TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS intervalo_cambio INTEGER DEFAULT 0;
    """
    return sql

def create_languages_table():
    """Crear tabla de idiomas para los estados"""
    sql = """
    CREATE TABLE IF NOT EXISTS panel_languages (
        id SERIAL PRIMARY KEY,
        language_code VARCHAR(10) NOT NULL UNIQUE,
        language_name VARCHAR(50) NOT NULL,
        libre_text VARCHAR(50) NOT NULL,
        denso_text VARCHAR(50) NOT NULL,
        completo_text VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    return sql

def insert_languages_data():
    """Insertar datos de idiomas"""
    sql = """
    INSERT INTO panel_languages (language_code, language_name, libre_text, denso_text, completo_text) 
    VALUES 
        ('es', 'Castellano', 'LIBRE', 'DENSO', 'COMPLETO'),
        ('va', 'Valenciano', 'LLIURE', 'DENSA', 'COMPLET'),
        ('en', 'Inglés', 'FREE', 'BUSY', 'FULL'),
        ('fr', 'Francés', 'LIBRE', 'OCCUPÉ', 'COMPLET'),
        ('de', 'Alemán', 'FREI', 'BESETZT', 'VOLL');
    """
    return sql

def update_existing_panels():
    """Actualizar paneles existentes con los nuevos valores por defecto"""
    sql = """
    UPDATE panels 
    SET 
        fabricante = 'Rótulos electrónicos',
        num_pantallas = 1,
        resolucion_ancho = 64,
        resolucion_alto = 16,
        tipo_visualizacion = 'plazas',
        idioma_principal = 'valenciano',
        idiomas_secundarios = '',
        intervalo_cambio = 0
    WHERE fabricante IS NULL;
    """
    return sql

def create_panel_api_config_table():
    """Crear tabla de configuración de la API de paneles"""
    sql = """
    CREATE TABLE IF NOT EXISTS panel_api_config (
        id SERIAL PRIMARY KEY,
        api_url VARCHAR(255) DEFAULT 'http://127.0.0.1:5656/sendMulti',
        api_timeout INTEGER DEFAULT 30,
        retry_attempts INTEGER DEFAULT 3,
        retry_delay INTEGER DEFAULT 5,
        enabled BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    return sql

def insert_panel_api_config():
    """Insertar configuración por defecto de la API"""
    sql = """
    INSERT INTO panel_api_config (api_url, api_timeout, retry_attempts, retry_delay, enabled)
    VALUES ('http://127.0.0.1:5656/sendMulti', 30, 3, 5, true)
    ON CONFLICT (id) DO UPDATE SET
        api_url = EXCLUDED.api_url,
        api_timeout = EXCLUDED.api_timeout,
        retry_attempts = EXCLUDED.retry_attempts,
        retry_delay = EXCLUDED.retry_delay,
        enabled = EXCLUDED.enabled,
        updated_at = CURRENT_TIMESTAMP;
    """
    return sql

def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración de base de datos para paneles v2.6")
    print("=" * 60)
    
    conn = connect_db()
    
    migrations = [
        ("Añadir columnas a tabla panels", add_panel_columns()),
        ("Crear tabla de idiomas", create_languages_table()),
        ("Insertar datos de idiomas", insert_languages_data()),
        ("Actualizar paneles existentes", update_existing_panels()),
        ("Crear tabla de configuración API", create_panel_api_config_table()),
        ("Insertar configuración API", insert_panel_api_config())
    ]
    
    success_count = 0
    total_migrations = len(migrations)
    
    for migration_name, sql in migrations:
        if execute_migration(conn, migration_name, sql):
            success_count += 1
    
    conn.close()
    
    print("=" * 60)
    print(f"📊 Resumen de migración:")
    print(f"   ✅ Migraciones exitosas: {success_count}/{total_migrations}")
    print(f"   ❌ Migraciones fallidas: {total_migrations - success_count}")
    
    if success_count == total_migrations:
        print("🎉 ¡Migración completada exitosamente!")
        return True
    else:
        print("⚠️  Algunas migraciones fallaron. Revisar logs.")
        return False

if __name__ == "__main__":
    main() 