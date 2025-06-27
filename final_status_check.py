#!/usr/bin/env python3
"""
Script final para verificar el estado completo del sistema después de la corrección
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Parking, Access, VehicleCount, CameraLog
from config import DB_URL
from datetime import datetime, timedelta

def check_final_status():
    """Verificar el estado final del sistema"""
    
    print("=" * 60)
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA DE PARKING ALTEA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar todos los parkings
        parkings = session.query(Parking).all()
        print(f"\n📊 ESTADO DE TODOS LOS PARKINGS ({len(parkings)} total)")
        print("-" * 60)
        
        total_issues = 0
        
        for parking in parkings:
            # Calcular ocupación real
            cameras = session.query(Access).filter(Access.parking_id == parking.id).all()
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
            free_spaces = parking.max_capacity - real_occupancy
            
            # Verificar descuadres
            has_issue = False
            issue_msg = ""
            
            if real_occupancy != parking.current_occupancy:
                has_issue = True
                issue_msg = f"DESCUADRE: BD={parking.current_occupancy}, Real={real_occupancy}"
            
            if real_occupancy > parking.max_capacity:
                has_issue = True
                issue_msg = f"EXCESO: {real_occupancy}/{parking.max_capacity}"
            
            if real_occupancy < 0:
                has_issue = True
                issue_msg = f"OCUPACIÓN NEGATIVA: {real_occupancy}"
            
            # Mostrar estado
            status_color = "🟢" if not has_issue else "🔴"
            print(f"{status_color} {parking.name}")
            print(f"   Capacidad: {parking.max_capacity}, Ocupación: {real_occupancy}, Libres: {free_spaces}")
            print(f"   Estado: {parking.status}")
            print(f"   Cámaras: {len(cameras)}")
            
            if has_issue:
                print(f"   ⚠️  {issue_msg}")
                total_issues += 1
            
            print()
        
        # Verificar cámaras activas
        print("📷 ESTADO DE CÁMARAS")
        print("-" * 60)
        
        cameras = session.query(Access).all()
        active_cameras = 0
        total_cameras = len(cameras)
        
        for camera in cameras:
            status = "🟢 ONLINE" if camera.status == "ONLINE" else "🔴 OFFLINE"
            print(f"{status} - {camera.name} ({camera.ip})")
            if camera.status == "ONLINE":
                active_cameras += 1
        
        print(f"\nCámaras activas: {active_cameras}/{total_cameras}")
        
        # Verificar logs recientes
        print(f"\n📝 LOGS RECIENTES (últimas 5 entradas)")
        print("-" * 60)
        
        recent_logs = session.query(CameraLog).order_by(CameraLog.id.desc()).limit(5).all()
        
        for log in recent_logs:
            parking_name = log.parking.name if log.parking else "N/A"
            status_icon = "✅" if log.status == "processed" else "❌"
            print(f"{status_icon} {log.received_at} - {parking_name} - {log.camera_name}")
            print(f"   Delta: +{log.delta_in or 0}/-{log.delta_out or 0}, Ocupación: {log.new_occupancy}")
            if log.error_message:
                print(f"   ⚠️  Error: {log.error_message}")
            print()
        
        # Resumen final
        print("=" * 60)
        print("📋 RESUMEN FINAL")
        print("=" * 60)
        
        print(f"✅ Parkings configurados: {len(parkings)}")
        print(f"✅ Cámaras totales: {total_cameras}")
        print(f"✅ Cámaras activas: {active_cameras}")
        print(f"❌ Problemas detectados: {total_issues}")
        
        if total_issues == 0:
            print("\n🎯 SISTEMA FUNCIONANDO CORRECTAMENTE")
            print("   Todos los parkings tienen ocupación correcta")
            print("   No se detectaron descuadres")
        else:
            print(f"\n⚠️  SE REQUIEREN CORRECCIONES")
            print(f"   {total_issues} problemas detectados")
        
        # Verificar si hay logs con errores recientes
        error_logs = session.query(CameraLog).filter(
            CameraLog.status == "error"
        ).order_by(CameraLog.id.desc()).limit(3).all()
        
        if error_logs:
            print(f"\n⚠️  LOGS CON ERRORES RECIENTES:")
            for log in error_logs:
                print(f"   {log.received_at} - {log.camera_name}: {log.error_message}")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_final_status() 