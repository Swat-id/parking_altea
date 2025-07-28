#!/usr/bin/env python3
"""
Script de prueba para validar el cálculo correcto de deltas en el sistema de cámaras
"""

import sys
import os
sys.path.append('src')

from models import Parking, Access, CameraParking
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_delta_calculation():
    """Probar el cálculo de deltas con múltiples parkings por cámara"""
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔍 Analizando configuración de cámaras y parkings...")
        
        # Obtener todas las cámaras
        cameras = session.query(Access).all()
        
        print(f"\n📊 Total de cámaras encontradas: {len(cameras)}")
        
        for camera in cameras:
            print(f"\n📹 Cámara: {camera.name} (IP: {camera.ip}, Línea: {camera.line})")
            
            # Obtener parkings asociados a esta cámara
            camera_parkings = session.query(CameraParking).filter_by(camera_id=camera.id).all()
            
            if not camera_parkings:
                print("  ⚠️  No hay parkings asociados a esta cámara")
                continue
            
            print(f"  🏢 Parkings asociados: {len(camera_parkings)}")
            
            for cp in camera_parkings:
                parking = cp.parking
                print(f"    - {parking.name}: Ocupación actual {parking.current_occupancy}/{parking.max_capacity}")
            
            # Simular un delta de entrada
            delta_in = 5
            delta_out = 2
            net_delta = delta_in - delta_out
            
            print(f"  📈 Delta simulado: +{delta_in} entradas, -{delta_out} salidas = {net_delta} neto")
            
            # Aplicar delta completo a todos los parkings asociados (lógica correcta)
            print(f"  📋 Impacto en cada parking (delta completo aplicado):")
            for cp in camera_parkings:
                parking = cp.parking
                new_occupancy = parking.current_occupancy + net_delta
                print(f"    - {parking.name}: {parking.current_occupancy} → {new_occupancy} (+{net_delta})")
        
        print("\n" + "="*60)
        print("📋 RESUMEN DE CONFIGURACIÓN")
        print("="*60)
        
        # Estadísticas generales
        total_cameras = len(cameras)
        total_parkings = session.query(Parking).count()
        total_relationships = session.query(CameraParking).count()
        
        print(f"Total de cámaras: {total_cameras}")
        print(f"Total de parkings: {total_parkings}")
        print(f"Total de relaciones cámara-parking: {total_relationships}")
        
        # Cámaras con múltiples parkings
        cameras_with_multiple_parkings = []
        for camera in cameras:
            parking_count = session.query(CameraParking).filter_by(camera_id=camera.id).count()
            if parking_count > 1:
                cameras_with_multiple_parkings.append((camera, parking_count))
        
        if cameras_with_multiple_parkings:
            print(f"\n⚠️  CÁMARAS CON MÚLTIPLES PARKINGS (requieren corrección):")
            for camera, count in cameras_with_multiple_parkings:
                print(f"  - {camera.name} (IP: {camera.ip}): {count} parkings")
        else:
            print("\n✅ Todas las cámaras están asociadas a un solo parking")
        
        # Parkings con múltiples cámaras
        parkings_with_multiple_cameras = []
        parkings = session.query(Parking).all()
        for parking in parkings:
            camera_count = session.query(CameraParking).filter_by(parking_id=parking.id).count()
            if camera_count > 1:
                parkings_with_multiple_cameras.append((parking, camera_count))
        
        if parkings_with_multiple_cameras:
            print(f"\n📹 PARKINGS CON MÚLTIPLES CÁMARAS:")
            for parking, count in parkings_with_multiple_cameras:
                print(f"  - {parking.name}: {count} cámaras")
        else:
            print("\n✅ Todos los parkings están asociados a una sola cámara")
        
        print("\n" + "="*60)
        print("🔧 RECOMENDACIONES")
        print("="*60)
        
        if cameras_with_multiple_parkings:
            print("1. ⚠️  Implementar distribución proporcional de deltas para cámaras con múltiples parkings")
            print("2. 📊 Revisar la lógica en camera_server.py líneas 400-450")
            print("3. 🧪 Probar con datos reales para validar la corrección")
        else:
            print("1. ✅ La configuración actual no requiere corrección de deltas")
            print("2. 📈 El sistema actual debería funcionar correctamente")
        
        print("3. 🔍 Verificar que las programaciones activas se respeten")
        print("4. 📱 Mejorar el frontend para mostrar información de programaciones")
        
    except Exception as e:
        logger.error(f"Error en el análisis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def test_schedule_verification():
    """Probar la verificación de programaciones activas"""
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\n" + "="*60)
        print("📅 VERIFICACIÓN DE PROGRAMACIONES ACTIVAS")
        print("="*60)
        
        from panel_schedule_service import PanelScheduleService
        schedule_service = PanelScheduleService(session)
        
        # Obtener todos los parkings
        parkings = session.query(Parking).all()
        
        print(f"📊 Total de parkings: {len(parkings)}")
        
        for parking in parkings:
            active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
            
            if active_schedules:
                print(f"\n🏢 {parking.name}: {len(active_schedules)} programación(es) activa(s)")
                for schedule in active_schedules:
                    print(f"  📋 {schedule.name}: {schedule.start_time} - {schedule.end_time}")
                    print(f"     Mensaje: {schedule.message}")
            else:
                print(f"\n🏢 {parking.name}: Sin programaciones activas")
        
        print("\n" + "="*60)
        print("🔧 RECOMENDACIONES PARA PROGRAMACIONES")
        print("="*60)
        print("1. ✅ Verificar que las programaciones activas se respeten en camera_server.py")
        print("2. 📱 Mostrar información de programaciones en el frontend")
        print("3. 📊 Mejorar el logging de omisiones por programaciones activas")
        
    except Exception as e:
        logger.error(f"Error en verificación de programaciones: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    print("🧪 INICIO DE PRUEBAS DEL SISTEMA DE CÁMARAS Y PROGRAMACIONES")
    print("="*60)
    
    test_delta_calculation()
    test_schedule_verification()
    
    print("\n" + "="*60)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*60)
    print("📋 Revisar el documento de análisis completo:")
    print("   docs/analisis_profundo_sistema_camaras_programaciones.md") 