#!/usr/bin/env python3
"""
Script de migración para hacer parking_id nullable en camera_logs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DB_URL

def migrate_camera_logs_nullable():
    """Hacer parking_id nullable en camera_logs"""
    
    print("🚀 Iniciando migración para hacer parking_id nullable en camera_logs...")
    
    # Crear conexión a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar si la columna ya es nullable
        result = session.execute(text("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'camera_logs' AND column_name = 'parking_id'
        """))
        
        column_info = result.fetchone()
        if not column_info:
            print("❌ ERROR: Columna parking_id no encontrada en camera_logs")
            return False
        
        if column_info.is_nullable == 'YES':
            print("✅ La columna parking_id ya es nullable")
            return True
        
        # Hacer la columna nullable
        print("📋 Haciendo parking_id nullable en camera_logs...")
        
        session.execute(text("""
            ALTER TABLE camera_logs ALTER COLUMN parking_id DROP NOT NULL
        """))
        
        session.commit()
        print("✅ Columna parking_id ahora es nullable")
        
        # Verificar el cambio
        result = session.execute(text("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'camera_logs' AND column_name = 'parking_id'
        """))
        
        column_info = result.fetchone()
        if column_info.is_nullable == 'YES':
            print("✅ Verificación exitosa: parking_id es ahora nullable")
            return True
        else:
            print("❌ ERROR: La columna no se actualizó correctamente")
            return False
            
    except Exception as e:
        print(f"❌ ERROR durante la migración: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = migrate_camera_logs_nullable()
    if success:
        print("\n🎉 Migración completada exitosamente!")
    else:
        print("\n❌ La migración falló")
        sys.exit(1) 