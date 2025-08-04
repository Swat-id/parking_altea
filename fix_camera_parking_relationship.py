#!/usr/bin/env python3
"""
Script para verificar y corregir la relación entre cámaras y parkings
"""

from sqlalchemy import create_engine, text
from config import DB_URL

def check_and_fix_relationship():
    engine = create_engine(DB_URL)
    session = engine.connect()
    
    try:
        print("🔍 Verificando estado actual de la base de datos...")
        
        # Verificar si existe la tabla camera_parkings
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'camera_parkings'
            );
        """))
        camera_parkings_exists = result.fetchone()[0]
        print(f"📋 Tabla camera_parkings existe: {camera_parkings_exists}")
        
        # Verificar si existe parking_id en accesses
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'accesses' 
                AND column_name = 'parking_id'
            );
        """))
        parking_id_exists = result.fetchone()[0]
        print(f"📋 Columna parking_id en accesses: {parking_id_exists}")
        
        # Verificar si existe la vista camera_status_view
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = 'camera_status_view'
            );
        """))
        view_exists = result.fetchone()[0]
        print(f"📋 Vista camera_status_view existe: {view_exists}")
        
        # Contar cámaras y parkings
        result = session.execute(text("SELECT COUNT(*) FROM accesses"))
        cameras_count = result.fetchone()[0]
        print(f"📊 Total cámaras: {cameras_count}")
        
        result = session.execute(text("SELECT COUNT(*) FROM parkings"))
        parkings_count = result.fetchone()[0]
        print(f"📊 Total parkings: {parkings_count}")
        
        # Si no existe la tabla camera_parkings, crearla
        if not camera_parkings_exists:
            print("🔧 Creando tabla camera_parkings...")
            session.execute(text("""
                CREATE TABLE camera_parkings (
                    id SERIAL PRIMARY KEY,
                    camera_id INTEGER NOT NULL REFERENCES accesses(id) ON DELETE CASCADE,
                    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(camera_id, parking_id)
                )
            """))
            print("✅ Tabla camera_parkings creada")
        
        # Si existe parking_id en accesses, migrar los datos
        if parking_id_exists:
            print("🔧 Migrando datos de parking_id a camera_parkings...")
            session.execute(text("""
                INSERT INTO camera_parkings (camera_id, parking_id)
                SELECT id, parking_id 
                FROM accesses 
                WHERE parking_id IS NOT NULL
                ON CONFLICT (camera_id, parking_id) DO NOTHING
            """))
            print("✅ Datos migrados")
            
            # Eliminar la columna parking_id
            print("🔧 Eliminando columna parking_id...")
            session.execute(text("ALTER TABLE accesses DROP COLUMN IF EXISTS parking_id"))
            print("✅ Columna parking_id eliminada")
        
        # Crear la vista camera_status_view
        print("🔧 Creando vista camera_status_view...")
        session.execute(text("DROP VIEW IF EXISTS camera_status_view"))
        
        view_sql = """
        CREATE OR REPLACE VIEW camera_status_view AS
        SELECT 
            a.id,
            a.name as camera_name,
            a.ip as camera_ip,
            a.line as camera_line,
            a.status,
            a.last_message_received,
            a.last_ping_check,
            a.ping_status,
            a.last_vehicle_in,
            a.last_vehicle_out,
            p.id as parking_id,
            p.name as parking_name,
            p.current_occupancy,
            p.max_capacity as capacity,
            CASE 
                WHEN a.status = 'ONLINE' AND a.ping_status = 'ONLINE' THEN 'FULLY_ONLINE'
                WHEN a.status = 'ONLINE' AND a.ping_status = 'OFFLINE' THEN 'ONLINE_NO_PING'
                WHEN a.status = 'OFFLINE' AND a.ping_status = 'ONLINE' THEN 'OFFLINE_PING_OK'
                WHEN a.status = 'OFFLINE' AND a.ping_status = 'OFFLINE' THEN 'FULLY_OFFLINE'
                ELSE 'UNKNOWN'
            END as overall_status
        FROM accesses a
        LEFT JOIN camera_parkings cp ON a.id = cp.camera_id
        LEFT JOIN parkings p ON cp.parking_id = p.id
        ORDER BY p.name, a.name
        """
        
        session.execute(text(view_sql))
        print("✅ Vista camera_status_view creada")
        
        # Verificar el resultado final
        result = session.execute(text("SELECT COUNT(*) FROM camera_parkings"))
        relations_count = result.fetchone()[0]
        print(f"📊 Relaciones en camera_parkings: {relations_count}")
        
        # Mostrar algunas relaciones
        result = session.execute(text("""
            SELECT cp.camera_id, cp.parking_id, a.name as camera_name, p.name as parking_name
            FROM camera_parkings cp
            JOIN accesses a ON cp.camera_id = a.id
            JOIN parkings p ON cp.parking_id = p.id
            LIMIT 5
        """))
        print("📋 Ejemplos de relaciones:")
        for row in result.fetchall():
            print(f"   Cámara {row.camera_name} -> Parking {row.parking_name}")
        
        session.commit()
        print("✅ Corrección completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    check_and_fix_relationship() 