#!/usr/bin/env python3
"""
Script para verificar el estado de las cámaras por ping
- Verificar conectividad de todas las cámaras
- Actualizar estado en la base de datos
- Generar reporte de estado
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno y DB_URL
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

# Importar modelos
from models import Access

# Crear engine y sesión
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def ping_device(ip, count=1, timeout=1):
    """Verificar conectividad de un dispositivo por ping"""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), ip], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=timeout + 2
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        logger.error(f"Error pinging {ip}: {e}")
        return False

def check_cameras_status():
    """Verificar estado de todas las cámaras por ping"""
    
    print("📷 VERIFICACIÓN DE ESTADO DE CÁMARAS POR PING")
    print("=" * 60)
    
    # Obtener todas las cámaras
    cameras = session.query(Access).all()
    
    print(f"Total cámaras en BD: {len(cameras)}")
    print()
    
    online_count = 0
    offline_count = 0
    updated_count = 0
    
    for camera in cameras:
        print(f"Cámara: {camera.name}")
        print(f"  - IP: {camera.ip}")
        print(f"  - Línea: {camera.line}")
        print(f"  - Estado actual: {getattr(camera, 'status', 'OFFLINE')}")
        print(f"  - Último mensaje: {camera.last_message_received}")
        print(f"  - Último ping: {camera.last_ping_check}")
        
        # Verificar conectividad por ping
        online = ping_device(camera.ip)
        ping_status = 'ONLINE' if online else 'OFFLINE'
        
        print(f"  - Ping actual: {'✅ ONLINE' if online else '❌ OFFLINE'}")
        
        # Actualizar estado en la base de datos si cambió
        old_ping_status = getattr(camera, 'ping_status', 'UNKNOWN')
        if old_ping_status != ping_status:
            camera.ping_status = ping_status
            camera.last_ping_check = datetime.now()
            updated_count += 1
            print(f"  - ⚠️  Estado actualizado: {old_ping_status} → {ping_status}")
        else:
            print(f"  - ✅ Estado sin cambios")
        
        # Contar estados
        if online:
            online_count += 1
        else:
            offline_count += 1
        
        print("-" * 40)
    
    # Guardar cambios en la base de datos
    try:
        session.commit()
        print(f"\n💾 Cambios guardados en la base de datos")
    except Exception as e:
        print(f"\n❌ Error guardando cambios: {e}")
        session.rollback()
        return
    
    print(f"\n📊 RESUMEN:")
    print(f"  - Cámaras ONLINE: {online_count}")
    print(f"  - Cámaras OFFLINE: {offline_count}")
    print(f"  - Estados actualizados: {updated_count}")
    print(f"  - Total: {len(cameras)}")
    
    # Análisis de inconsistencias
    print(f"\n🔍 ANÁLISIS DE INCONSISTENCIAS:")
    
    for camera in cameras:
        message_status = getattr(camera, 'status', 'OFFLINE')
        ping_status = getattr(camera, 'ping_status', 'UNKNOWN')
        
        if message_status == 'ONLINE' and ping_status == 'OFFLINE':
            print(f"  ⚠️  {camera.name}: ONLINE por mensajes pero OFFLINE por ping")
        elif message_status == 'OFFLINE' and ping_status == 'ONLINE':
            print(f"  ⚠️  {camera.name}: OFFLINE por mensajes pero ONLINE por ping")
    
    session.close()

def get_cameras_summary():
    """Obtener resumen de estado de cámaras"""
    
    print(f"\n📋 RESUMEN DETALLADO DE CÁMARAS")
    print("=" * 60)
    
    session = Session()
    cameras = session.query(Access).all()
    
    # Agrupar por estado
    online_cameras = []
    offline_cameras = []
    unknown_cameras = []
    
    for camera in cameras:
        ping_status = getattr(camera, 'ping_status', 'UNKNOWN')
        message_status = getattr(camera, 'status', 'OFFLINE')
        
        camera_info = {
            'name': camera.name,
            'ip': camera.ip,
            'line': camera.line,
            'ping_status': ping_status,
            'message_status': message_status,
            'last_message': camera.last_message_received,
            'last_ping': camera.last_ping_check
        }
        
        if ping_status == 'ONLINE':
            online_cameras.append(camera_info)
        elif ping_status == 'OFFLINE':
            offline_cameras.append(camera_info)
        else:
            unknown_cameras.append(camera_info)
    
    print(f"🟢 CÁMARAS ONLINE ({len(online_cameras)}):")
    for camera in online_cameras:
        print(f"  - {camera['name']} ({camera['ip']}:{camera['line']})")
        if camera['last_message']:
            time_diff = datetime.now() - camera['last_message']
            if time_diff > timedelta(minutes=5):
                print(f"    ⚠️  Último mensaje hace {time_diff.total_seconds()/60:.1f} minutos")
    
    print(f"\n🔴 CÁMARAS OFFLINE ({len(offline_cameras)}):")
    for camera in offline_cameras:
        print(f"  - {camera['name']} ({camera['ip']}:{camera['line']})")
    
    if unknown_cameras:
        print(f"\n🟡 CÁMARAS SIN VERIFICAR ({len(unknown_cameras)}):")
        for camera in unknown_cameras:
            print(f"  - {camera['name']} ({camera['ip']}:{camera['line']})")
    
    session.close()

if __name__ == "__main__":
    print(f"🚀 Iniciando verificación de cámaras por ping - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_cameras_status()
    get_cameras_summary()
    
    print(f"\n✅ Verificación completada - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 