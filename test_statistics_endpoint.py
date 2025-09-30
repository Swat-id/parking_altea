#!/usr/bin/env python3
"""
Script para probar el endpoint de estadísticas por horas
Verificar por qué los valores están en 0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from src.models import User, Parking, CameraLog, OccupancyHistory, CameraParking, Access
from src.config import Session
from src.auth import create_token
from datetime import datetime, timedelta

def test_statistics_endpoint():
    session = Session()
    
    try:
        print("=== TEST ENDPOINT ESTADÍSTICAS ===")
        
        # 1. Verificar datos base
        parkings = session.query(Parking).all()
        print(f"\n1. PARKINGS DISPONIBLES ({len(parkings)}):")
        for p in parkings:
            print(f"   ID: {p.id}, Nombre: {p.name}")
        
        if not parkings:
            print("   ❌ No hay parkings")
            return
        
        parking_id = parkings[0].id
        print(f"\n🎯 USANDO PARKING ID: {parking_id}")
        
        # 2. Verificar datos de CameraLog
        print(f"\n2. DATOS EN CAMERA_LOG:")
        total_logs = session.query(CameraLog).count()
        parking_logs = session.query(CameraLog).filter(CameraLog.parking_id == parking_id).count()
        processed_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking_id,
            CameraLog.status == 'processed'
        ).count()
        
        print(f"   Total logs sistema: {total_logs}")
        print(f"   Logs parking {parking_id}: {parking_logs}")
        print(f"   Logs procesados parking {parking_id}: {processed_logs}")
        
        # Logs recientes
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
            print(f"      ID: {log.id}, Fecha: {log.received_at}")
            print(f"         delta_in: {log.delta_in}, delta_out: {log.delta_out}")
            print(f"         vehicle_in: {log.vehicle_in}, vehicle_out: {log.vehicle_out}")
            print(f"         IP: {log.camera_ip}, Status: {log.status}")
        
        # 3. Verificar datos de OccupancyHistory
        print(f"\n3. DATOS EN OCCUPANCY_HISTORY:")
        total_occupancy = session.query(OccupancyHistory).count()
        parking_occupancy = session.query(OccupancyHistory).filter(
            OccupancyHistory.parking_id == parking_id
        ).count()
        recent_occupancy = session.query(OccupancyHistory).filter(
            OccupancyHistory.parking_id == parking_id,
            OccupancyHistory.timestamp >= week_ago
        ).count()
        
        print(f"   Total registros: {total_occupancy}")
        print(f"   Registros parking {parking_id}: {parking_occupancy}")
        print(f"   Registros últimos 7 días: {recent_occupancy}")
        
        # 4. Verificar relaciones cámara-parking
        print(f"\n4. RELACIONES CÁMARA-PARKING:")
        camera_parkings = session.query(CameraParking).filter(
            CameraParking.parking_id == parking_id
        ).all()
        
        print(f"   Cámaras vinculadas: {len(camera_parkings)}")
        for cp in camera_parkings:
            camera = cp.camera
            print(f"      Cámara ID: {camera.id}, IP: {camera.ip}, Nombre: {camera.name}")
            
            # Logs para esta cámara
            camera_logs = session.query(CameraLog).filter(
                CameraLog.camera_ip == camera.ip,
                CameraLog.received_at >= week_ago
            ).count()
            print(f"         Logs últimos 7 días: {camera_logs}")
        
        # 5. Probar endpoint directamente
        print(f"\n5. PRUEBA ENDPOINT /api/parkings/{parking_id}/hourly-statistics:")
        
        # Obtener usuario para token
        users = session.query(User).all()
        if not users:
            print("   ❌ No hay usuarios para generar token")
            return
        
        user = users[0]
        token_data = create_token(user.id, user.email, user.role)
        token = token_data['access_token']
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Llamar al endpoint
        base_url = "http://localhost:6001"
        url = f"{base_url}/api/parkings/{parking_id}/hourly-statistics?days=7"
        
        print(f"   URL: {url}")
        print(f"   Usuario: {user.email} (rol: {user.role})")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Respuesta exitosa")
                
                # Analizar respuesta
                hourly_stats = data.get('hourly_statistics', [])
                camera_stats = data.get('camera_statistics', [])
                
                print(f"   📊 Estadísticas por horas: {len(hourly_stats)} horas")
                print(f"   📷 Estadísticas de cámaras: {len(camera_stats)} cámaras")
                
                # Mostrar algunas horas con datos
                hours_with_data = [h for h in hourly_stats if h.get('total_vehicles_in', 0) > 0 or h.get('total_vehicles_out', 0) > 0]
                print(f"   🚗 Horas con tráfico: {len(hours_with_data)}")
                
                if hours_with_data:
                    print(f"   📋 HORAS CON DATOS:")
                    for hour in hours_with_data[:5]:  # Primeras 5
                        print(f"      {hour.get('hour_label')}: IN={hour.get('total_vehicles_in')}, OUT={hour.get('total_vehicles_out')}, MSG={hour.get('message_count')}")
                else:
                    print(f"   ❌ NINGUNA HORA TIENE DATOS DE TRÁFICO")
                    # Mostrar algunas horas para debug
                    print(f"   📋 PRIMERAS 5 HORAS (debug):")
                    for hour in hourly_stats[:5]:
                        print(f"      {hour.get('hour_label')}: IN={hour.get('total_vehicles_in')}, OUT={hour.get('total_vehicles_out')}, MSG={hour.get('message_count')}")
                
                # Analizar estadísticas de cámaras
                if camera_stats:
                    print(f"   📋 ESTADÍSTICAS DE CÁMARAS:")
                    for cam in camera_stats:
                        print(f"      Cámara {cam.get('camera_name')} ({cam.get('camera_ip')}):")
                        print(f"         Mensajes: {cam.get('total_messages')}, Procesados: {cam.get('processed_messages')}")
                        print(f"         Entradas: {cam.get('total_vehicles_in')}, Salidas: {cam.get('total_vehicles_out')}")
                else:
                    print(f"   ❌ SIN ESTADÍSTICAS DE CÁMARAS")
                
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                print(f"   Respuesta: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error llamando endpoint: {e}")
        
        print(f"\n✅ TEST COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_statistics_endpoint()
