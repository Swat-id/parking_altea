#!/usr/bin/env python3
"""
Script para verificar el estado de los paneles
- Estado en la base de datos
- Conectividad (ping)
- Estado en la API
"""

import os
import sys
import requests
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno y DB_URL
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

# Importar modelos
from models import Panel

# Crear engine y sesión
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def ping_device(ip, count=1, timeout=1):
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
        return False

def check_panels_status():
    """Verificar el estado de todos los paneles"""
    
    print("📺 VERIFICACIÓN DE ESTADO DE PANELES")
    print("=" * 60)
    
    # Obtener todos los paneles de la base de datos
    panels = session.query(Panel).all()
    
    print(f"Total paneles en BD: {len(panels)}")
    print()
    
    online_count = 0
    offline_count = 0
    
    for panel in panels:
        print(f"Panel: {panel.name}")
        print(f"  - IP: {panel.ip}")
        print(f"  - Estado en BD: {panel.status}")
        print(f"  - Última actualización: {panel.last_update}")
        
        # Verificar conectividad
        online = ping_device(panel.ip)
        print(f"  - Conectividad: {'✅ ONLINE' if online else '❌ OFFLINE'}")
        
        if online:
            online_count += 1
        else:
            offline_count += 1
        
        print("-" * 40)
    
    print(f"\n📊 RESUMEN:")
    print(f"  - Paneles ONLINE: {online_count}")
    print(f"  - Paneles OFFLINE: {offline_count}")
    print(f"  - Total: {len(panels)}")
    
    # Verificar si hay inconsistencias
    print(f"\n🔍 ANÁLISIS DE INCONSISTENCIAS:")
    
    for panel in panels:
        online = ping_device(panel.ip)
        if online and panel.status == 'OFFLINE':
            print(f"  ⚠️  {panel.name}: ONLINE pero marcado como OFFLINE en BD")
        elif not online and panel.status == 'ONLINE':
            print(f"  ⚠️  {panel.name}: OFFLINE pero marcado como ONLINE en BD")
    
    session.close()

def test_panel_api():
    """Probar la API de paneles si existe"""
    
    print("\n🌐 VERIFICACIÓN DE API DE PANELES")
    print("=" * 60)
    
    API_BASE_URL = "http://157.180.91.63:6001"
    
    # Intentar obtener información de paneles desde la API
    try:
        response = requests.get(f"{API_BASE_URL}/panels", timeout=5)
        if response.status_code == 200:
            panels_api = response.json()
            print(f"✅ API de paneles disponible")
            print(f"  - Paneles en API: {len(panels_api)}")
            for panel in panels_api:
                print(f"    - {panel.get('name', 'N/A')}: {panel.get('status', 'N/A')}")
        else:
            print(f"❌ API de paneles no disponible (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error conectando a API de paneles: {e}")
    
    # Verificar endpoint de actualización de estado
    try:
        response = requests.get(f"{API_BASE_URL}/panel/status", timeout=5)
        if response.status_code == 200:
            print(f"✅ Endpoint de estado de paneles disponible")
        else:
            print(f"❌ Endpoint de estado de paneles no disponible (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error conectando a endpoint de estado: {e}")

def check_panel_service():
    """Verificar si hay un servicio específico para paneles"""
    
    print("\n🔧 VERIFICACIÓN DE SERVICIOS DE PANELES")
    print("=" * 60)
    
    try:
        # Verificar si hay un servicio de paneles
        result = subprocess.run(
            ["systemctl", "status", "parking-panel.service"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Servicio parking-panel.service encontrado")
            print(result.stdout.decode())
        else:
            print("❌ Servicio parking-panel.service no encontrado")
            
    except Exception as e:
        print(f"❌ Error verificando servicios: {e}")
    
    # Verificar puertos relacionados con paneles
    panel_ports = [6002, 6003, 6004]  # Puertos típicos para servicios de paneles
    
    for port in panel_ports:
        try:
            result = subprocess.run(
                ["netstat", "-tlnp"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            if str(port) in result.stdout.decode():
                print(f"✅ Puerto {port} está en uso")
            else:
                print(f"❌ Puerto {port} no está en uso")
                
        except Exception as e:
            print(f"❌ Error verificando puerto {port}: {e}")

if __name__ == "__main__":
    print(f"🚀 Iniciando verificación de paneles - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_panels_status()
    test_panel_api()
    check_panel_service()
    
    print(f"\n✅ Verificación completada - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 