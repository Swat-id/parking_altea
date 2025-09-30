#!/usr/bin/env python3
"""
Script para debuggear los datos de estadísticas
Verifica si hay datos en CameraLog y OccupancyHistory
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models import CameraLog, OccupancyHistory, Parking, CameraParking, Access
from src.config import Session
from datetime import datetime, timedelta
from sqlalchemy import func

def debug_statistics_data():
    session = Session()
    
    try:
        print("=== DEBUG ESTADÍSTICAS ===")
        
        # 1. Verificar parkings disponibles
        parkings = session.query(Parking).all()
        print(f"\n1. PARKINGS DISPONIBLES ({len(parkings)}):")
        for p in parkings:
            print(f"   ID: {p.id}, Nombre: {p.name}, Ocupación: {p.current_occupancy}")
        
        if not parkings:
            print("   ❌ No hay parkings en la base de datos")
            return
        
        # Usar el primer parking para las pruebas
        parking_id = parkings[0].id
        print(f"\n🎯 USANDO PARKING ID: {parking_id} ({parkings[0].name})")
        
        # 2. Verificar datos en CameraLog
        print(f"\n2. DATOS EN CAMERA_LOG:")
        total_logs = session.query(CameraLog).count()
        parking_logs = session.query(CameraLog).filter(CameraLog.parking_id == parking_id).count()
        processed_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed'
        ).count()
        
        print(f"   Total logs en sistema: {total_logs}")
        print(f"   Logs para parking {parking_id}: {parking_logs}")
        print(f"   Logs procesados para parking {parking_id}: {processed_logs}")
        
        # Logs recientes (últimos 7 días)
        week_ago = datetime.now() - timedelta(days=7)
        recent_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.received_at >= week_ago,
            CameraLog.status == 'processed'
        ).count()
        print(f"   Logs procesados últimos 7 días: {recent_logs}")
        
        # Mostrar algunos logs de ejemplo
        sample_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed'
        ).order_by(CameraLog.received_at.desc()).limit(5).all()
        
        print(f"\n   📋 LOGS DE EJEMPLO:")
        for log in sample_logs:
            print(f"      ID: {log.id}, Fecha: {log.received_at}, "
                  f"delta_in: {log.delta_in}, delta_out: {log.delta_out}, "
                  f"IP: {log.camera_ip}")
        
        # 3. Verificar datos en OccupancyHistory
        print(f"\n3. DATOS EN OCCUPANCY_HISTORY:")
        total_occupancy = session.query(OccupancyHistory).count()
        parking_occupancy = session.query(OccupancyHistory).filter(
            OccupancyHistory.parking_id == parking_id
        ).count()
        recent_occupancy = session.query(OccupancyHistory).filter(
            OccupancyHistory.parking_id == parking_id,
            OccupancyHistory.timestamp >= week_ago
        ).count()
        
        print(f"   Total registros ocupación: {total_occupancy}")
        print(f"   Registros para parking {parking_id}: {parking_occupancy}")
        print(f"   Registros últimos 7 días: {recent_occupancy}")
        
        # 4. Verificar relaciones cámara-parking
        print(f"\n4. RELACIONES CÁMARA-PARKING:")
        camera_parkings = session.query(CameraParking).filter(
            CameraParking.parking_id == parking_id
        ).all()
        
        print(f"   Cámaras vinculadas al parking {parking_id}: {len(camera_parkings)}")
        for cp in camera_parkings:
            camera = cp.camera
            print(f"      Cámara ID: {camera.id}, Nombre: {camera.name}, IP: {camera.ip}")
            
            # Verificar logs para esta cámara específica
            camera_logs = session.query(CameraLog).filter(
                CameraLog.camera_ip == camera.ip,
                CameraLog.received_at >= week_ago
            ).count()
            print(f"         Logs últimos 7 días: {camera_logs}")
        
        # 5. Verificar datos por hora (hoy)
        print(f"\n5. DATOS POR HORA (HOY):")
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = today_start + timedelta(days=1)
        
        for hour in range(0, 24, 4):  # Cada 4 horas para no saturar
            hour_start = today_start.replace(hour=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_logs = session.query(CameraLog).filter(
                CameraLog.parking_id == parking_id,
                CameraLog.received_at >= hour_start,
                CameraLog.received_at < hour_end,
                CameraLog.status == 'processed'
            ).all()
            
            if hour_logs:
                total_in = sum(log.delta_in or 0 for log in hour_logs)
                total_out = sum(log.delta_out or 0 for log in hour_logs)
                print(f"   {hour:02d}:00 - Logs: {len(hour_logs)}, Entradas: {total_in}, Salidas: {total_out}")
        
        # 6. Verificar si hay datos NULL o problemáticos
        print(f"\n6. VERIFICACIÓN DE DATOS PROBLEMÁTICOS:")
        null_deltas = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed',
            CameraLog.delta_in.is_(None),
            CameraLog.delta_out.is_(None)
        ).count()
        print(f"   Logs con delta_in y delta_out NULL: {null_deltas}")
        
        # Logs con parking_id NULL
        null_parking_logs = session.query(CameraLog).filter(
            CameraLog.parking_id.is_(None)
        ).count()
        print(f"   Logs con parking_id NULL: {null_parking_logs}")
        
        print(f"\n✅ DEBUG COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error durante debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_statistics_data()
