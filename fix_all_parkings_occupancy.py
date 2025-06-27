#!/usr/bin/env python3
"""
Script para corregir la ocupación de todos los parkings con descuadres
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Parking, Access, VehicleCount, CameraLog
from config import DB_URL
from datetime import datetime, timedelta

def fix_all_parkings_occupancy():
    """Corregir la ocupación de todos los parkings"""
    
    print("=" * 60)
    print("🔧 CORRECCIÓN MASIVA DE OCUPACIÓN - TODOS LOS PARKINGS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los parkings
        parkings = session.query(Parking).all()
        print(f"\n📊 ANALIZANDO {len(parkings)} PARKINGS")
        print("-" * 60)
        
        corrections_made = 0
        
        for parking in parkings:
            print(f"\n🅿️  {parking.name}")
            print(f"   Capacidad: {parking.max_capacity}")
            print(f"   Ocupación actual en BD: {parking.current_occupancy}")
            print(f"   Estado actual: {parking.status}")
            
            # Obtener cámaras del parking
            cameras = session.query(Access).filter(Access.parking_id == parking.id).all()
            print(f"   Cámaras: {len(cameras)}")
            
            # Calcular ocupación real
            total_in = 0
            total_out = 0
            
            for camera in cameras:
                last_count = session.query(VehicleCount).filter(
                    VehicleCount.access_id == camera.id
                ).order_by(VehicleCount.id.desc()).first()
                
                if last_count:
                    total_in += last_count.total_vehicles_in
                    total_out += last_count.total_vehicles_out
                    print(f"     📷 {camera.name}: In={last_count.total_vehicles_in}, Out={last_count.total_vehicles_out}")
            
            real_occupancy = total_in - total_out
            print(f"   Ocupación real calculada: {real_occupancy}")
            
            # Verificar si hay descuadre
            if real_occupancy != parking.current_occupancy:
                print(f"   ⚠️  DESCUADRE DETECTADO: {parking.current_occupancy} vs {real_occupancy}")
                
                # Corregir automáticamente
                old_occupancy = parking.current_occupancy
                parking.current_occupancy = real_occupancy
                
                # Actualizar estado
                free_spaces = parking.max_capacity - real_occupancy
                if free_spaces <= parking.threshold_full:
                    parking.status = "COMPLETO"
                elif free_spaces <= parking.threshold_dense:
                    parking.status = "DENSO"
                else:
                    parking.status = "LIBRE"
                
                print(f"   ✅ CORREGIDO: {old_occupancy} → {real_occupancy}")
                print(f"   ✅ Nuevo estado: {parking.status}")
                corrections_made += 1
            else:
                print(f"   ✅ Sin descuadre")
        
        # Confirmar cambios
        if corrections_made > 0:
            print(f"\n💾 GUARDANDO {corrections_made} CORRECCIONES...")
            session.commit()
            print(f"✅ Correcciones guardadas exitosamente")
        else:
            print(f"\n✅ No se requieren correcciones")
        
        # Verificar estado final
        print(f"\n📋 RESUMEN DE CORRECCIONES")
        print("-" * 60)
        print(f"✅ Parkings analizados: {len(parkings)}")
        print(f"✅ Correcciones realizadas: {corrections_made}")
        
        # Mostrar estado final de cada parking
        print(f"\n📊 ESTADO FINAL DE PARKINGS")
        print("-" * 60)
        
        for parking in parkings:
            status_icon = "🟢" if parking.status == "LIBRE" else "🟡" if parking.status == "DENSO" else "🔴"
            print(f"{status_icon} {parking.name}: {parking.current_occupancy}/{parking.max_capacity} ({parking.status})")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_all_parkings_occupancy() 