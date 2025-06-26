#!/usr/bin/env python3
"""
Script para verificar y corregir el estado de las cámaras
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from src import config
from src.models import Base, CameraLog, Access, Parking
from datetime import datetime, timedelta
import subprocess
import platform

# Configurar conexión a base de datos
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def ping_host(ip):
    """Hacer ping a una IP"""
    try:
        # Usar ping con timeout
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_camera_status():
    """Verificar y corregir el estado de las cámaras"""
    print("🔍 Verificando estado de cámaras")
    print("=" * 60)
    
    session = Session()
    
    try:
        # Obtener todas las cámaras
        cameras = session.query(Access).all()
        
        print(f"📊 Total de cámaras encontradas: {len(cameras)}")
        print()
        
        corrections_made = 0
        
        for camera in cameras:
            print(f"📷 Verificando cámara: {camera.name} ({camera.ip})")
            
            # Verificar ping actual
            ping_online = ping_host(camera.ip)
            ping_status = 'ONLINE' if ping_online else 'OFFLINE'
            
            # Verificar último mensaje (últimas 5 minutos)
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            recent_message = session.query(CameraLog).filter(
                CameraLog.camera_ip == camera.ip,
                CameraLog.processed_at >= five_minutes_ago,
                CameraLog.status == 'processed'
            ).order_by(CameraLog.processed_at.desc()).first()
            
            message_status = 'ONLINE' if recent_message else 'OFFLINE'
            
            # Determinar estado correcto
            if ping_online or recent_message:
                correct_status = 'ONLINE'
            else:
                correct_status = 'OFFLINE'
            
            # Verificar si necesita corrección
            needs_correction = False
            correction_reason = []
            
            if camera.status != correct_status:
                needs_correction = True
                correction_reason.append(f"Estado incorrecto: {camera.status} → {correct_status}")
            
            if camera.ping_status != ping_status:
                needs_correction = True
                correction_reason.append(f"Ping incorrecto: {camera.ping_status} → {ping_status}")
            
            # Mostrar información
            print(f"   📊 Estado actual: {camera.status}")
            print(f"   📊 Estado correcto: {correct_status}")
            print(f"   📊 Ping actual: {camera.ping_status}")
            print(f"   📊 Ping real: {ping_status}")
            print(f"   📊 Último mensaje: {recent_message.processed_at if recent_message else 'N/A'}")
            
            if needs_correction:
                print(f"   ⚠️  NECESITA CORRECCIÓN: {', '.join(correction_reason)}")
                
                # Aplicar corrección
                camera.status = correct_status
                camera.ping_status = ping_status
                camera.last_ping_check = datetime.now()
                
                if recent_message:
                    camera.last_message_received = recent_message.processed_at
                
                corrections_made += 1
                print(f"   ✅ CORREGIDO: Estado actualizado a {correct_status}")
            else:
                print(f"   ✅ OK: Estado correcto")
            
            print()
        
        # Commit cambios
        if corrections_made > 0:
            session.commit()
            print(f"✅ Se realizaron {corrections_made} correcciones")
        else:
            print("✅ No se necesitaron correcciones")
        
        # Mostrar resumen final
        print("\n📊 RESUMEN FINAL:")
        print("-" * 40)
        
        online_cameras = session.query(Access).filter(Access.status == 'ONLINE').count()
        offline_cameras = session.query(Access).filter(Access.status == 'OFFLINE').count()
        
        print(f"📷 Cámaras ONLINE: {online_cameras}")
        print(f"📷 Cámaras OFFLINE: {offline_cameras}")
        print(f"📷 Total: {len(cameras)}")
        
        # Mostrar cámaras con problemas
        print("\n🔍 Cámaras con problemas:")
        print("-" * 40)
        
        problem_cameras = session.query(Access).filter(
            Access.ping_status == 'ONLINE',
            Access.status == 'OFFLINE'
        ).all()
        
        if problem_cameras:
            for camera in problem_cameras:
                print(f"   ⚠️  {camera.name} ({camera.ip}): Ping ONLINE pero estado OFFLINE")
        else:
            print("   ✅ No hay cámaras con problemas detectados")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Función principal"""
    print("🚀 Verificación y corrección de estado de cámaras")
    print("📅 Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    check_camera_status()
    
    print("\n" + "=" * 60)
    print("📋 RECOMENDACIONES")
    print("=" * 60)
    print("1. Ejecutar este script periódicamente para mantener estados actualizados")
    print("2. Verificar logs de cámaras para detectar problemas de conectividad")
    print("3. Revisar configuración de red si hay cámaras con ping fallido")
    print("4. Monitorear el estado de las cámaras en el frontend")

if __name__ == "__main__":
    main() 