#!/usr/bin/env python3
"""
Script para analizar el problema de conteo detectado en los logs de cámaras
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from src import config
from models import Base, CameraLog, Access, Parking
from datetime import datetime, timedelta

# Configurar conexión a base de datos
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def analyze_camera_counting():
    """Analizar el problema de conteo en las cámaras"""
    print("🔍 Analizando problema de conteo en cámaras")
    print("=" * 60)
    
    session = Session()
    
    try:
        # Buscar la cámara específica mencionada en el problema
        camera_ip = "212.63.121.209"
        camera_name = "Basseta_Rastro camera 2"
        
        print(f"📷 Analizando cámara: {camera_name} ({camera_ip})")
        print()
        
        # Obtener logs recientes de esta cámara
        recent_logs = session.query(CameraLog).filter(
            CameraLog.camera_ip == camera_ip,
            CameraLog.status == "processed"
        ).order_by(CameraLog.processed_at.desc()).limit(10).all()
        
        if not recent_logs:
            print("❌ No se encontraron logs recientes para esta cámara")
            return
        
        print(f"📊 Últimos {len(recent_logs)} mensajes procesados:")
        print("-" * 60)
        
        for i, log in enumerate(recent_logs):
            print(f"📝 Mensaje {i+1}:")
            print(f"   🕐 Timestamp: {log.processed_at}")
            print(f"   📊 Contadores: In: {log.vehicle_in} | Out: {log.vehicle_out}")
            print(f"   📈 Deltas: In: {log.delta_in} | Out: {log.delta_out}")
            print(f"   🏢 Ocupación: {log.new_occupancy}")
            print(f"   📋 Estado: {log.parking_status}")
            print()
        
        # Analizar el problema específico mencionado
        print("🔍 Análisis del problema específico:")
        print("-" * 60)
        
        # Buscar los dos mensajes mencionados
        target_times = [
            datetime(2025, 6, 26, 23, 21, 47),
            datetime(2025, 6, 26, 23, 21, 7)
        ]
        
        for target_time in target_times:
            # Buscar logs cercanos a ese tiempo
            start_time = target_time - timedelta(seconds=30)
            end_time = target_time + timedelta(seconds=30)
            
            logs = session.query(CameraLog).filter(
                CameraLog.camera_ip == camera_ip,
                CameraLog.processed_at.between(start_time, end_time),
                CameraLog.status == "processed"
            ).order_by(CameraLog.processed_at.desc()).all()
            
            if logs:
                log = logs[0]
                print(f"📅 {log.processed_at.strftime('%d/%m/%Y, %H:%M:%S')}:")
                print(f"   📊 Contadores: In: {log.vehicle_in} | Out: {log.vehicle_out}")
                print(f"   📈 Deltas: In: {log.delta_in} | Out: {log.delta_out}")
                print(f"   🏢 Ocupación: {log.new_occupancy}")
                print(f"   📋 Estado: {log.parking_status}")
                print()
        
        # Analizar la lógica de cálculo
        print("🧮 Análisis de la lógica de cálculo:")
        print("-" * 60)
        
        # Obtener el acceso de esta cámara
        access = session.query(Access).filter_by(ip=camera_ip).first()
        if access:
            print(f"📋 Acceso encontrado:")
            print(f"   🆔 ID: {access.id}")
            print(f"   🏢 Parking: {access.parking.name}")
            print(f"   📊 Contadores actuales: In: {access.last_vehicle_in} | Out: {access.last_vehicle_out}")
            print(f"   🏢 Ocupación actual del parking: {access.parking.current_occupancy}")
            print()
            
            # Verificar si hay inconsistencias
            expected_occupancy = (access.last_vehicle_in or 0) - (access.last_vehicle_out or 0)
            actual_occupancy = access.parking.current_occupancy
            
            if expected_occupancy != actual_occupancy:
                print(f"⚠️  INCONSISTENCIA DETECTADA:")
                print(f"   📊 Ocupación esperada (In-Out): {expected_occupancy}")
                print(f"   🏢 Ocupación actual en BD: {actual_occupancy}")
                print(f"   📈 Diferencia: {actual_occupancy - expected_occupancy}")
                print()
        
        # Analizar patrones de deltas
        print("📈 Análisis de patrones de deltas:")
        print("-" * 60)
        
        # Obtener todos los logs de las últimas 24 horas
        yesterday = datetime.now() - timedelta(days=1)
        recent_logs = session.query(CameraLog).filter(
            CameraLog.camera_ip == camera_ip,
            CameraLog.processed_at >= yesterday,
            CameraLog.status == "processed"
        ).order_by(CameraLog.processed_at.asc()).all()
        
        if recent_logs:
            print(f"📊 Análisis de {len(recent_logs)} mensajes en las últimas 24h:")
            
            zero_deltas = 0
            negative_deltas = 0
            large_deltas = 0
            
            for log in recent_logs:
                if log.delta_in == 0 and log.delta_out == 0:
                    zero_deltas += 1
                if log.delta_in < 0 or log.delta_out < 0:
                    negative_deltas += 1
                if log.delta_in > 10 or log.delta_out > 10:
                    large_deltas += 1
            
            print(f"   📊 Deltas cero: {zero_deltas} ({zero_deltas/len(recent_logs)*100:.1f}%)")
            print(f"   📊 Deltas negativas: {negative_deltas} ({negative_deltas/len(recent_logs)*100:.1f}%)")
            print(f"   📊 Deltas grandes (>10): {large_deltas} ({large_deltas/len(recent_logs)*100:.1f}%)")
            print()
            
            # Mostrar ejemplos de deltas problemáticos
            print("🔍 Ejemplos de deltas problemáticos:")
            for log in recent_logs[-20:]:  # Últimos 20 mensajes
                if log.delta_in < 0 or log.delta_out < 0 or (log.delta_in == 0 and log.delta_out == 0):
                    print(f"   📅 {log.processed_at.strftime('%H:%M:%S')}: In={log.delta_in}, Out={log.delta_out}, Ocupación={log.new_occupancy}")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
    finally:
        session.close()

def main():
    """Función principal"""
    print("🚀 Análisis de problema de conteo en cámaras")
    print("📅 Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    analyze_camera_counting()
    
    print("=" * 60)
    print("📋 RECOMENDACIONES")
    print("=" * 60)
    print("1. Verificar si hay mensajes duplicados que no se están detectando")
    print("2. Revisar la lógica de cálculo de deltas")
    print("3. Verificar si hay problemas de concurrencia en la BD")
    print("4. Analizar si hay reset de contadores en las cámaras")
    print("5. Verificar la sincronización de timestamps")

if __name__ == "__main__":
    main() 