#!/usr/bin/env python3
"""
Script para debuggear específicamente los datos de CameraLog
Verificar por qué las estadísticas están en 0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models import CameraLog, Parking, CameraParking, Access
from src.config import Session
from datetime import datetime, timedelta
from sqlalchemy import func

def debug_camera_logs():
    session = Session()
    
    try:
        print("=== DEBUG CAMERA LOGS ===")
        
        # 1. Verificar parkings
        parkings = session.query(Parking).all()
        print(f"\n1. PARKINGS ({len(parkings)}):")
        for p in parkings:
            print(f"   ID: {p.id}, Nombre: {p.name}")
        
        if not parkings:
            print("   ❌ No hay parkings")
            return
        
        parking_id = parkings[0].id
        print(f"\n🎯 ANALIZANDO PARKING ID: {parking_id}")
        
        # 2. Análisis general de CameraLog
        print(f"\n2. ANÁLISIS GENERAL CAMERA_LOG:")
        total_logs = session.query(CameraLog).count()
        print(f"   Total logs en sistema: {total_logs}")
        
        if total_logs == 0:
            print("   ❌ NO HAY LOGS EN CAMERA_LOG - Este es el problema principal")
            return
        
        # Distribución por parking_id
        parking_distribution = session.query(
            CameraLog.parking_id,
            func.count(CameraLog.id).label('count')
        ).group_by(CameraLog.parking_id).all()
        
        print(f"   Distribución por parking_id:")
        for pid, count in parking_distribution:
            pid_str = str(pid) if pid is not None else "NULL"
            print(f"     Parking {pid_str}: {count} logs")
        
        # Distribución por status
        status_distribution = session.query(
            CameraLog.status,
            func.count(CameraLog.id).label('count')
        ).group_by(CameraLog.status).all()
        
        print(f"   Distribución por status:")
        for status, count in status_distribution:
            print(f"     {status}: {count} logs")
        
        # 3. Análisis específico del parking
        print(f"\n3. ANÁLISIS PARKING {parking_id}:")
        parking_logs = session.query(CameraLog).filter(CameraLog.parking_id == parking_id).count()
        print(f"   Logs con parking_id={parking_id}: {parking_logs}")
        
        if parking_logs == 0:
            print(f"   ❌ NO HAY LOGS PARA PARKING {parking_id}")
            
            # Verificar si hay logs con parking_id NULL
            null_logs = session.query(CameraLog).filter(CameraLog.parking_id.is_(None)).count()
            print(f"   Logs con parking_id NULL: {null_logs}")
            
            if null_logs > 0:
                print(f"   ⚠️  PROBLEMA: Hay {null_logs} logs sin parking_id asignado")
                
                # Mostrar algunos logs NULL para análisis
                sample_null_logs = session.query(CameraLog).filter(
                    CameraLog.parking_id.is_(None)
                ).limit(5).all()
                
                print(f"   📋 LOGS SIN PARKING_ID (muestra):")
                for log in sample_null_logs:
                    print(f"      ID: {log.id}, IP: {log.camera_ip}, Fecha: {log.received_at}")
                    print(f"         delta_in: {log.delta_in}, delta_out: {log.delta_out}")
            
            return
        
        # Análisis por status del parking específico
        parking_status_dist = session.query(
            CameraLog.status,
            func.count(CameraLog.id).label('count')
        ).filter(CameraLog.parking_id == parking_id).group_by(CameraLog.status).all()
        
        print(f"   Distribución por status (parking {parking_id}):")
        for status, count in parking_status_dist:
            print(f"     {status}: {count} logs")
        
        # 4. Análisis temporal
        print(f"\n4. ANÁLISIS TEMPORAL:")
        week_ago = datetime.now() - timedelta(days=7)
        today = datetime.now().date()
        
        recent_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.received_at >= week_ago
        ).count()
        print(f"   Logs últimos 7 días: {recent_logs}")
        
        today_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            func.date(CameraLog.received_at) == today
        ).count()
        print(f"   Logs de hoy: {today_logs}")
        
        # Logs procesados recientes
        processed_recent = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.received_at >= week_ago,
            CameraLog.status == 'processed'
        ).count()
        print(f"   Logs procesados últimos 7 días: {processed_recent}")
        
        # 5. Análisis de deltas
        print(f"\n5. ANÁLISIS DE DELTAS:")
        logs_with_deltas = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed',
            (CameraLog.delta_in.isnot(None)) | (CameraLog.delta_out.isnot(None))
        ).count()
        print(f"   Logs procesados con deltas: {logs_with_deltas}")
        
        # Suma total de deltas
        delta_sums = session.query(
            func.sum(CameraLog.delta_in).label('total_in'),
            func.sum(CameraLog.delta_out).label('total_out')
        ).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed',
            CameraLog.received_at >= week_ago
        ).first()
        
        total_in = delta_sums.total_in or 0
        total_out = delta_sums.total_out or 0
        print(f"   Suma deltas últimos 7 días: IN={total_in}, OUT={total_out}")
        
        # 6. Mostrar logs de ejemplo
        print(f"\n6. LOGS DE EJEMPLO (últimos 5 procesados):")
        sample_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed'
        ).order_by(CameraLog.received_at.desc()).limit(5).all()
        
        for i, log in enumerate(sample_logs, 1):
            print(f"   {i}. ID: {log.id}")
            print(f"      Fecha: {log.received_at}")
            print(f"      IP: {log.camera_ip}, Línea: {log.camera_line}")
            print(f"      Vehículos: IN={log.vehicle_in}, OUT={log.vehicle_out}")
            print(f"      Deltas: IN={log.delta_in}, OUT={log.delta_out}")
            print(f"      Status: {log.status}")
        
        # 7. Verificar relaciones cámara-parking
        print(f"\n7. RELACIONES CÁMARA-PARKING:")
        camera_parkings = session.query(CameraParking).filter(
            CameraParking.parking_id == parking_id
        ).all()
        
        print(f"   Cámaras vinculadas: {len(camera_parkings)}")
        for cp in camera_parkings:
            camera = cp.camera
            print(f"      Cámara ID: {camera.id}, IP: {camera.ip}")
            
            # Logs para esta IP específica
            ip_logs = session.query(CameraLog).filter(
                CameraLog.camera_ip == camera.ip,
                CameraLog.received_at >= week_ago
            ).count()
            print(f"         Logs por IP últimos 7 días: {ip_logs}")
        
        print(f"\n✅ DEBUG COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error durante debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_camera_logs()
