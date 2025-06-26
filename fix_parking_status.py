#!/usr/bin/env python3
"""
Script para corregir estados de parking que aún tienen DESCUADRE_NEGATIVO
y cambiarlos a COMPLETO según la nueva lógica implementada.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src import config
from src.models import Base, Parking
from datetime import datetime

# Configurar conexión a base de datos
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def fix_parking_status():
    """Corregir estados de parking con descuadre negativo"""
    print("🔧 Iniciando corrección de estados de parking")
    print("📅 Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    session = Session()
    
    try:
        # Obtener todos los parkings
        parkings = session.query(Parking).all()
        
        fixed_count = 0
        total_count = len(parkings)
        
        print(f"📊 Total de parkings encontrados: {total_count}")
        print()
        
        for parking in parkings:
            # Calcular espacios libres
            free_spaces = parking.max_capacity - parking.current_occupancy
            old_status = parking.status
            
            # Aplicar nueva lógica
            if free_spaces < 0:
                # Descuadre negativo - cambiar a COMPLETO
                if parking.status != 'COMPLETO':
                    parking.status = 'COMPLETO'
                    print(f"🔧 Parking {parking.id} - {parking.name}")
                    print(f"   📊 Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
                    print(f"   📈 Espacios libres: {free_spaces}")
                    print(f"   🔄 Estado: {old_status} → COMPLETO")
                    print()
                    fixed_count += 1
                else:
                    print(f"✅ Parking {parking.id} - {parking.name}: Ya tiene estado COMPLETO")
            elif free_spaces <= parking.threshold_full:
                if parking.status != 'COMPLETO':
                    parking.status = 'COMPLETO'
                    print(f"🔧 Parking {parking.id} - {parking.name}")
                    print(f"   📊 Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
                    print(f"   📈 Espacios libres: {free_spaces} (≤ {parking.threshold_full})")
                    print(f"   🔄 Estado: {old_status} → COMPLETO")
                    print()
                    fixed_count += 1
                else:
                    print(f"✅ Parking {parking.id} - {parking.name}: Ya tiene estado COMPLETO")
            elif free_spaces <= parking.threshold_dense:
                if parking.status != 'DENSO':
                    parking.status = 'DENSO'
                    print(f"🔧 Parking {parking.id} - {parking.name}")
                    print(f"   📊 Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
                    print(f"   📈 Espacios libres: {free_spaces} (≤ {parking.threshold_dense})")
                    print(f"   🔄 Estado: {old_status} → DENSO")
                    print()
                    fixed_count += 1
                else:
                    print(f"✅ Parking {parking.id} - {parking.name}: Ya tiene estado DENSO")
            else:
                if parking.status != 'LIBRE':
                    parking.status = 'LIBRE'
                    print(f"🔧 Parking {parking.id} - {parking.name}")
                    print(f"   📊 Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
                    print(f"   📈 Espacios libres: {free_spaces}")
                    print(f"   🔄 Estado: {old_status} → LIBRE")
                    print()
                    fixed_count += 1
                else:
                    print(f"✅ Parking {parking.id} - {parking.name}: Ya tiene estado LIBRE")
        
        # Guardar cambios
        session.commit()
        
        print("=" * 60)
        print("📊 RESUMEN DE CORRECCIÓN")
        print("=" * 60)
        print(f"🎯 Total de parkings procesados: {total_count}")
        print(f"🔧 Estados corregidos: {fixed_count}")
        print(f"✅ Estados ya correctos: {total_count - fixed_count}")
        
        if fixed_count > 0:
            print("\n🎉 CORRECCIÓN COMPLETADA")
            print("✅ Todos los parkings ahora tienen estados válidos según la nueva lógica")
        else:
            print("\n✅ NO SE NECESITARON CORRECCIONES")
            print("   Todos los parkings ya tenían estados correctos")
            
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        session.rollback()
        return False
    finally:
        session.close()
    
    return True

def verify_correction():
    """Verificar que la corrección fue exitosa"""
    print("\n🔍 Verificando corrección...")
    print("=" * 60)
    
    session = Session()
    
    try:
        parkings = session.query(Parking).all()
        
        invalid_states = []
        
        for parking in parkings:
            free_spaces = parking.max_capacity - parking.current_occupancy
            
            # Verificar que no hay estados DESCUADRE_NEGATIVO
            if 'DESCUADRE' in parking.status:
                invalid_states.append({
                    'id': parking.id,
                    'name': parking.name,
                    'status': parking.status,
                    'occupancy': parking.current_occupancy,
                    'capacity': parking.max_capacity,
                    'free_spaces': free_spaces
                })
        
        if invalid_states:
            print("❌ ERROR: Se encontraron estados inválidos:")
            for parking in invalid_states:
                print(f"   - Parking {parking['id']} ({parking['name']}): {parking['status']}")
            return False
        else:
            print("✅ VERIFICACIÓN EXITOSA")
            print("   Todos los parkings tienen estados válidos")
            return True
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        return False
    finally:
        session.close()

def main():
    """Función principal"""
    print("🚀 Script de corrección de estados de parking")
    print("🎯 Objetivo: Cambiar DESCUADRE_NEGATIVO a COMPLETO")
    print()
    
    # Ejecutar corrección
    if fix_parking_status():
        # Verificar corrección
        if verify_correction():
            print("\n🎉 CORRECCIÓN Y VERIFICACIÓN COMPLETADAS")
            print("✅ El sistema está listo para usar")
        else:
            print("\n❌ VERIFICACIÓN FALLIDA")
            print("   Revisar los errores mostrados")
    else:
        print("\n❌ CORRECCIÓN FALLIDA")
        print("   Revisar los errores mostrados")

if __name__ == "__main__":
    main() 