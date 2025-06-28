#!/usr/bin/env python3
"""
Script para verificar si hay mensajes duplicados en el procesamiento de cámaras
"""

import sys
import os

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from sqlalchemy import create_engine, func, and_, desc, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar modelos y configuración
try:
    from models import Base, Parking, Access, CameraLog, OccupancyHistory, VehicleCount
    from config import DB_URL
    DATABASE_URL = DB_URL  # Alias para mantener compatibilidad
except ImportError as e:
    print(f"❌ Error: No se pueden importar los módulos: {e}")
    print(f"   Directorio actual: {os.getcwd()}")
    print(f"   Path de src: {src_dir}")
    print(f"   Archivos en src: {os.listdir(src_dir) if os.path.exists(src_dir) else 'No existe'}")
    sys.exit(1)

def analyze_message_processing():
    """Analizar el procesamiento de mensajes para detectar duplicados"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("🔍 ANÁLISIS DE PROCESAMIENTO DE MENSAJES")
    print("=" * 60)
    
    # Obtener todos los parkings
    parkings = session.query(Parking).all()
    
    for parking in parkings:
        print(f"\n🏢 PARKING: {parking.name}")
        
        # Obtener accesos del parking
        accesses = session.query(Access).filter(Access.parking_id == parking.id).all()
        print(f"   Cámaras configuradas: {len(accesses)}")
        
        for access in accesses:
            print(f"\n     📹 {access.name} (IP: {access.ip}, Línea: {access.line})")
            print(f"        Estado: {access.status}")
            print(f"        Último mensaje: {access.last_message_received}")
            print(f"        Contadores actuales - In: {access.last_vehicle_in}, Out: {access.last_vehicle_out}")
            
            # Analizar logs de las últimas 24 horas
            recent_logs = session.query(CameraLog).filter(
                CameraLog.access_id == access.id,
                CameraLog.received_at >= datetime.now() - timedelta(hours=24)
            ).order_by(desc(CameraLog.received_at)).all()
            
            print(f"        Logs en las últimas 24h: {len(recent_logs)}")
            
            if recent_logs:
                # Verificar si hay mensajes con los mismos contadores
                processed_messages = {}
                duplicate_count = 0
                
                for log in recent_logs:
                    key = (log.vehicle_in, log.vehicle_out, log.camera_ip, log.camera_line)
                    if key in processed_messages:
                        duplicate_count += 1
                        print(f"          ⚠️ DUPLICADO DETECTADO:")
                        print(f"            Original: {processed_messages[key].received_at.strftime('%H:%M:%S')}")
                        print(f"            Duplicado: {log.received_at.strftime('%H:%M:%S')}")
                        print(f"            Vehicle In: {log.vehicle_in}, Vehicle Out: {log.vehicle_out}")
                    else:
                        processed_messages[key] = log
                
                if duplicate_count > 0:
                    print(f"          🚨 Total duplicados: {duplicate_count}")
                else:
                    print(f"          ✅ No se detectaron duplicados")
                
                # Mostrar últimos 5 logs
                print(f"        Últimos 5 logs:")
                for log in recent_logs[:5]:
                    print(f"          {log.received_at.strftime('%H:%M:%S')} - {log.status}")
                    print(f"            Vehicle In: {log.vehicle_in} (delta: {log.delta_in})")
                    print(f"            Vehicle Out: {log.vehicle_out} (delta: {log.delta_out})")
                    print(f"            Ocupación: {log.new_occupancy} (cambio: {log.occupancy_change})")
                    if log.error_message:
                        print(f"            Error: {log.error_message}")

def analyze_occupancy_changes():
    """Analizar cambios de ocupación para detectar inconsistencias"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n📊 ANÁLISIS DE CAMBIOS DE OCUPACIÓN")
    print("=" * 60)
    
    # Obtener historial de ocupación de las últimas 24 horas
    recent_history = session.query(OccupancyHistory).filter(
        OccupancyHistory.created_at >= datetime.now() - timedelta(hours=24)
    ).order_by(desc(OccupancyHistory.created_at)).all()
    
    print(f"Registros de ocupación en las últimas 24h: {len(recent_history)}")
    
    # Agrupar por parking
    parking_changes = {}
    for hist in recent_history:
        if hist.parking_id not in parking_changes:
            parking_changes[hist.parking_id] = []
        parking_changes[hist.parking_id].append(hist)
    
    for parking_id, changes in parking_changes.items():
        parking = session.query(Parking).filter(Parking.id == parking_id).first()
        if not parking:
            continue
            
        print(f"\n🏢 {parking.name}:")
        print(f"   Cambios de ocupación: {len(changes)}")
        
        # Verificar si hay cambios muy frecuentes (posibles duplicados)
        if len(changes) > 100:  # Más de 100 cambios en 24h es sospechoso
            print(f"   ⚠️ Muchos cambios detectados ({len(changes)}) - posible procesamiento duplicado")
        
        # Mostrar últimos 5 cambios
        print(f"   Últimos 5 cambios:")
        for change in changes[:5]:
            print(f"     {change.created_at.strftime('%H:%M:%S')} - {change.occupancy} ({change.source})")
            if hasattr(change, 'previous_occupancy') and change.previous_occupancy is not None:
                diff = change.occupancy - change.previous_occupancy
                print(f"       Cambio: {diff:+d}")

def check_camera_server_logic():
    """Verificar la lógica del servidor de cámaras"""
    print("\n🔧 ANÁLISIS DE LA LÓGICA DEL SERVIDOR DE CÁMARAS")
    print("=" * 60)
    
    print("✅ ASPECTOS POSITIVOS:")
    print("   - Cada mensaje se registra en CameraLog con timestamp único")
    print("   - Se calculan deltas basados en contadores anteriores")
    print("   - Se actualiza el estado ONLINE de las cámaras")
    print("   - Se registra el tiempo de procesamiento")
    print("   - Se manejan errores y se registran en logs")
    
    print("\n⚠️ POSIBLES MEJORAS:")
    print("   - No hay verificación de duplicados por timestamp")
    print("   - No hay protección contra mensajes muy frecuentes")
    print("   - No hay validación de secuencia de contadores")
    print("   - No hay rate limiting por IP")
    
    print("\n🔍 RECOMENDACIONES:")
    print("   1. Implementar verificación de duplicados por timestamp")
    print("   2. Agregar rate limiting por IP de cámara")
    print("   3. Validar que los contadores sean secuenciales")
    print("   4. Implementar protección contra mensajes muy frecuentes")

def main():
    """Función principal"""
    print("🚀 INICIANDO ANÁLISIS DE MENSAJES DUPLICADOS")
    print("=" * 60)
    
    try:
        analyze_message_processing()
        analyze_occupancy_changes()
        check_camera_server_logic()
        
        print("\n✅ ANÁLISIS COMPLETADO")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 