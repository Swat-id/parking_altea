#!/usr/bin/env python3
"""
Script para corregir el descuadre de ocupación del parking 6
El parking 6 tiene una ocupación de 168 cuando su capacidad máxima es 120
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Parking, Access, VehicleCount, CameraLog
from config import DB_URL
from datetime import datetime, timedelta

def fix_parking_6_occupancy():
    """Corregir el descuadre de ocupación del parking 6"""
    
    print("=== CORRECCIÓN DE DESCUADRE - PARKING 6 ===")
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener el parking 6
        parking = session.query(Parking).filter(Parking.id == 6).first()
        if not parking:
            print("❌ Parking 6 no encontrado")
            return
        
        print(f"🅿️  Parking: {parking.name}")
        print(f"   Capacidad máxima: {parking.max_capacity}")
        print(f"   Ocupación actual: {parking.current_occupancy}")
        print(f"   Estado actual: {parking.status}")
        
        # Obtener todas las cámaras del parking 6
        cameras = session.query(Access).filter(Access.parking_id == 6).all()
        print(f"\n📷 Cámaras del parking 6: {len(cameras)}")
        
        for camera in cameras:
            print(f"   - {camera.name} (IP: {camera.ip}, Línea: {camera.line})")
            
            # Obtener el último conteo de vehículos
            last_count = session.query(VehicleCount).filter(
                VehicleCount.access_id == camera.id
            ).order_by(VehicleCount.id.desc()).first()
            
            if last_count:
                print(f"     Último conteo - Entrada: {last_count.total_vehicles_in}, Salida: {last_count.total_vehicles_out}")
            else:
                print(f"     Sin conteos registrados")
        
        # Calcular la ocupación real basada en los contadores
        total_in = 0
        total_out = 0
        
        for camera in cameras:
            last_count = session.query(VehicleCount).filter(
                VehicleCount.access_id == camera.id
            ).order_by(VehicleCount.id.desc()).first()
            
            if last_count:
                total_in += last_count.total_vehicles_in
                total_out += last_count.total_vehicles_out
        
        real_occupancy = total_in - total_out
        print(f"\n📊 Cálculo de ocupación real:")
        print(f"   Total entrada: {total_in}")
        print(f"   Total salida: {total_out}")
        print(f"   Ocupación real: {real_occupancy}")
        
        # Verificar si hay descuadre
        if real_occupancy != parking.current_occupancy:
            print(f"\n⚠️  DESCUADRE DETECTADO:")
            print(f"   Ocupación en BD: {parking.current_occupancy}")
            print(f"   Ocupación real: {real_occupancy}")
            print(f"   Diferencia: {parking.current_occupancy - real_occupancy}")
            
            # Preguntar si corregir
            response = input("\n¿Desea corregir la ocupación? (s/n): ")
            if response.lower() == 's':
                # Corregir la ocupación
                parking.current_occupancy = real_occupancy
                
                # Actualizar estado
                free_spaces = parking.max_capacity - real_occupancy
                if free_spaces <= parking.threshold_full:
                    parking.status = "COMPLETO"
                elif free_spaces <= parking.threshold_dense:
                    parking.status = "DENSO"
                else:
                    parking.status = "LIBRE"
                
                session.commit()
                print(f"✅ Ocupación corregida:")
                print(f"   Nueva ocupación: {parking.current_occupancy}")
                print(f"   Nuevas plazas libres: {free_spaces}")
                print(f"   Nuevo estado: {parking.status}")
            else:
                print("❌ Corrección cancelada")
        else:
            print("✅ No hay descuadre detectado")
        
        # Mostrar logs recientes del parking 6
        print(f"\n📝 Logs recientes del parking 6:")
        recent_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == 6
        ).order_by(CameraLog.id.desc()).limit(5).all()
        
        for log in recent_logs:
            print(f"   {log.received_at} - {log.camera_name}")
            print(f"     Delta In: {log.delta_in}, Delta Out: {log.delta_out}")
            print(f"     Nueva ocupación: {log.new_occupancy}")
            if log.error_message:
                print(f"     ⚠️  Error: {log.error_message}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_parking_6_occupancy() 