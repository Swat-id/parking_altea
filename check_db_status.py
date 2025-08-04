#!/usr/bin/env python3
"""
Script temporal para verificar el estado de la base de datos
"""

from sqlalchemy import create_engine, text
from config import DB_URL

def check_database_status():
    engine = create_engine(DB_URL)
    session = engine.connect()
    
    try:
        # Verificar si existe la tabla camera_parkings
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'camera_parkings'
            );
        """))
        camera_parkings_exists = result.fetchone()[0]
        print(f"✅ Tabla camera_parkings existe: {camera_parkings_exists}")
        
        if camera_parkings_exists:
            # Contar relaciones en camera_parkings
            result = session.execute(text("SELECT COUNT(*) FROM camera_parkings"))
            count = result.fetchone()[0]
            print(f"📊 Relaciones en camera_parkings: {count}")
            
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
        
        # Contar cámaras totales
        result = session.execute(text("SELECT COUNT(*) FROM accesses"))
        cameras_count = result.fetchone()[0]
        print(f"📊 Total cámaras: {cameras_count}")
        
        # Contar parkings totales
        result = session.execute(text("SELECT COUNT(*) FROM parkings"))
        parkings_count = result.fetchone()[0]
        print(f"📊 Total parkings: {parkings_count}")
        
        # Verificar cámaras con parking_id (si existe)
        if parking_id_exists:
            result = session.execute(text("SELECT COUNT(*) FROM accesses WHERE parking_id IS NOT NULL"))
            cameras_with_parking = result.fetchone()[0]
            print(f"📊 Cámaras con parking_id: {cameras_with_parking}")
        
        # Verificar vista camera_status_view
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = 'camera_status_view'
            );
        """))
        view_exists = result.fetchone()[0]
        print(f"📋 Vista camera_status_view existe: {view_exists}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database_status() 