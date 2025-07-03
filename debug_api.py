#!/usr/bin/env python3
"""
Script de diagnóstico para la API
"""

import sys
import os

# Añadir el directorio src al path
sys.path.insert(0, '/opt/parking_altea/src')

def test_imports():
    """Probar las importaciones necesarias"""
    print("🔍 Probando importaciones...")
    
    try:
        import config
        print("✅ config importado correctamente")
    except Exception as e:
        print(f"❌ Error importando config: {e}")
        return False
    
    try:
        from models import Parking, OccupancyHistory
        print("✅ models importado correctamente")
    except Exception as e:
        print(f"❌ Error importando models: {e}")
        return False
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        print("✅ SQLAlchemy importado correctamente")
    except Exception as e:
        print(f"❌ Error importando SQLAlchemy: {e}")
        return False
    
    return True

def test_database_connection():
    """Probar la conexión a la base de datos"""
    print("\n🔍 Probando conexión a la base de datos...")
    
    try:
        import config
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(config.DB_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Probar una consulta simple
        result = session.execute("SELECT 1")
        print("✅ Conexión a la base de datos exitosa")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

def test_parking_query():
    """Probar consulta de parking"""
    print("\n🔍 Probando consulta de parking...")
    
    try:
        import config
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import Parking
        
        engine = create_engine(config.DB_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Probar consulta de parking
        parking = session.query(Parking).get(1)
        if parking:
            print(f"✅ Parking encontrado: {parking.name}")
        else:
            print("❌ Parking con ID 1 no encontrado")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error consultando parking: {e}")
        return False

def test_occupancy_history_table():
    """Probar la tabla occupancy_history"""
    print("\n🔍 Probando tabla occupancy_history...")
    
    try:
        import config
        from sqlalchemy import create_engine, text
        
        engine = create_engine(config.DB_URL, echo=False)
        
        # Verificar estructura de la tabla
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'occupancy_history'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("Columnas en occupancy_history:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
            # Verificar si existen los campos problemáticos
            column_names = [col[0] for col in columns]
            if 'previous_occupancy' in column_names:
                print("✅ Campo 'previous_occupancy' existe")
            else:
                print("❌ Campo 'previous_occupancy' NO existe")
                
            if 'change_amount' in column_names:
                print("✅ Campo 'change_amount' existe")
            else:
                print("❌ Campo 'change_amount' NO existe")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando tabla occupancy_history: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando diagnóstico de la API...")
    
    # Probar importaciones
    if not test_imports():
        print("❌ Fallo en importaciones")
        return
    
    # Probar conexión a BD
    if not test_database_connection():
        print("❌ Fallo en conexión a base de datos")
        return
    
    # Probar consulta de parking
    if not test_parking_query():
        print("❌ Fallo en consulta de parking")
        return
    
    # Probar tabla occupancy_history
    if not test_occupancy_history_table():
        print("❌ Fallo en verificación de tabla occupancy_history")
        return
    
    print("\n✅ Diagnóstico completado")

if __name__ == "__main__":
    main() 