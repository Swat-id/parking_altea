#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla parkings
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

# Crear engine y sesión
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def check_parkings_structure():
    """Verificar estructura de la tabla parkings"""
    
    print("🔍 VERIFICANDO ESTRUCTURA DE LA TABLA PARKINGS")
    print("=" * 50)
    
    session = Session()
    
    try:
        # Obtener columnas de la tabla parkings
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'parkings' 
            ORDER BY ordinal_position
        """))
        
        print("Columnas de la tabla 'parkings':")
        for row in result:
            print(f"  - {row[0]} ({row[1]}) - Nullable: {row[2]} - Default: {row[3]}")
        
        # Obtener algunos datos de ejemplo
        result = session.execute(text("SELECT * FROM parkings LIMIT 1"))
        if result.rowcount > 0:
            row = result.fetchone()
            print(f"\nDatos de ejemplo:")
            for i, column in enumerate(result.keys()):
                print(f"  - {column}: {row[i]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_parkings_structure() 