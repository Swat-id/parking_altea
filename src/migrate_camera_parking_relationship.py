#!/usr/bin/env python3
"""
Script de migración para cambiar la relación entre cámaras y parkings
de uno a muchos a muchos a muchos.

Este script:
1. Crea la nueva tabla camera_parkings
2. Migra los datos existentes de la relación directa
3. Elimina la columna parking_id de la tabla accesses
4. Actualiza las referencias en el código
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DB_URL as DATABASE_URL

def migrate_camera_parking_relationship():
    """Migra la relación de cámaras y parkings a muchos a muchos"""
    
    print("🚀 Iniciando migración de relación cámaras-parkings...")
    
    # Crear conexión a la base de datos
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Paso 1: Crear la nueva tabla camera_parkings
        print("📋 Paso 1: Creando tabla camera_parkings...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS camera_parkings (
            id SERIAL PRIMARY KEY,
            camera_id INTEGER NOT NULL REFERENCES accesses(id) ON DELETE CASCADE,
            parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(camera_id, parking_id)
        );
        """
        
        session.execute(text(create_table_sql))
        session.commit()
        print("✅ Tabla camera_parkings creada correctamente")
        
        # Paso 2: Migrar datos existentes
        print("📋 Paso 2: Migrando datos existentes...")
        
        # Obtener todas las cámaras con su parking_id actual
        result = session.execute(text("""
            SELECT id, parking_id, ip, line, name 
            FROM accesses 
            WHERE parking_id IS NOT NULL
        """))
        
        cameras_to_migrate = result.fetchall()
        print(f"📊 Encontradas {len(cameras_to_migrate)} cámaras para migrar")
        
        # Insertar en la nueva tabla
        for camera in cameras_to_migrate:
            insert_sql = """
            INSERT INTO camera_parkings (camera_id, parking_id, created_at)
            VALUES (:camera_id, :parking_id, :created_at)
            ON CONFLICT (camera_id, parking_id) DO NOTHING
            """
            
            session.execute(text(insert_sql), {
                'camera_id': camera.id,
                'parking_id': camera.parking_id,
                'created_at': datetime.now()
            })
        
        session.commit()
        print(f"✅ Migradas {len(cameras_to_migrate)} relaciones cámaras-parkings")
        
        # Paso 3: Verificar la migración
        print("📋 Paso 3: Verificando migración...")
        
        # Contar registros en la nueva tabla
        result = session.execute(text("SELECT COUNT(*) FROM camera_parkings"))
        count = result.scalar()
        print(f"📊 Total de relaciones en camera_parkings: {count}")
        
        # Mostrar algunas relaciones migradas
        result = session.execute(text("""
            SELECT cp.camera_id, cp.parking_id, a.ip, a.line, a.name, p.name as parking_name
            FROM camera_parkings cp
            JOIN accesses a ON cp.camera_id = a.id
            JOIN parkings p ON cp.parking_id = p.id
            LIMIT 5
        """))
        
        print("📋 Ejemplos de relaciones migradas:")
        for row in result.fetchall():
            print(f"   Cámara {row.ip}:{row.line} ({row.name}) -> Parking {row.parking_name}")
        
        # Paso 4: Eliminar la columna parking_id de accesses
        print("📋 Paso 4: Eliminando columna parking_id de accesses...")
        
        # Primero eliminar la restricción de clave foránea
        session.execute(text("""
            ALTER TABLE accesses DROP CONSTRAINT IF EXISTS accesses_parking_id_fkey
        """))
        
        # Luego eliminar la columna
        session.execute(text("""
            ALTER TABLE accesses DROP COLUMN IF EXISTS parking_id
        """))
        
        session.commit()
        print("✅ Columna parking_id eliminada de accesses")
        
        # Paso 5: Verificación final
        print("📋 Paso 5: Verificación final...")
        
        # Verificar que no hay parking_id en accesses
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'accesses' AND column_name = 'parking_id'
        """))
        
        if result.fetchone():
            print("❌ ERROR: La columna parking_id aún existe en accesses")
            return False
        else:
            print("✅ Columna parking_id eliminada correctamente")
        
        # Verificar que todas las relaciones están en camera_parkings
        result = session.execute(text("""
            SELECT COUNT(*) as total_cameras,
                   (SELECT COUNT(*) FROM camera_parkings) as total_relations
            FROM accesses
        """))
        
        stats = result.fetchone()
        print(f"📊 Total cámaras: {stats.total_cameras}")
        print(f"📊 Total relaciones: {stats.total_relations}")
        
        if stats.total_relations >= stats.total_cameras:
            print("✅ Migración completada exitosamente")
            return True
        else:
            print("⚠️  ADVERTENCIA: Algunas cámaras podrían no tener parkings asignados")
            return True
            
    except Exception as e:
        print(f"❌ ERROR durante la migración: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def rollback_migration():
    """Función para hacer rollback de la migración si es necesario"""
    
    print("🔄 Iniciando rollback de migración...")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Eliminar la tabla camera_parkings
        session.execute(text("DROP TABLE IF EXISTS camera_parkings CASCADE"))
        
        # Recrear la columna parking_id en accesses
        session.execute(text("""
            ALTER TABLE accesses ADD COLUMN IF NOT EXISTS parking_id INTEGER
        """))
        
        session.commit()
        print("✅ Rollback completado")
        
    except Exception as e:
        print(f"❌ ERROR durante el rollback: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar relación cámaras-parkings')
    parser.add_argument('--rollback', action='store_true', help='Hacer rollback de la migración')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        success = migrate_camera_parking_relationship()
        if success:
            print("\n🎉 Migración completada exitosamente!")
            print("📝 Recuerda actualizar el código para usar la nueva relación")
        else:
            print("\n❌ La migración falló")
            sys.exit(1) 