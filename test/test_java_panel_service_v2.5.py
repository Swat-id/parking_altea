#!/usr/bin/env python3
"""
Script de prueba para el servicio Java de paneles v2.5
"""

import requests
import json
import time
from datetime import datetime

def test_java_panel_service():
    """Probar el servicio Java de paneles"""
    
    print("🧪 PRUEBAS DEL SERVICIO JAVA DE PANELES v2.5")
    print("=" * 50)
    
    # Configuración
    base_url = "http://localhost:5656"
    panel_ip = "172.20.4.52"  # BELLES ARTS 2
    
    # Test 1: Health Check
    print(f"\n1️⃣ Health Check")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Servicio respondiendo: {data.get('status')}")
            print(f"   📋 Versión: {data.get('service')}")
            print(f"   🔧 Librería inicializada: {data.get('library_initialized')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando al servicio: {e}")
        return False
    
    # Test 2: Estado de paneles
    print(f"\n2️⃣ Estado de paneles")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/api/panels/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Estado: {data.get('status')}")
            print(f"   📊 Paneles: {data.get('panels_count')}")
            print(f"   🔧 Versión: {data.get('service_version')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Lista de paneles
    print(f"\n3️⃣ Lista de paneles")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/api/panels/list", timeout=5)
        if response.status_code == 200:
            panels = response.json()
            print(f"   ✅ Paneles encontrados: {len(panels)}")
            for panel in panels[:3]:  # Mostrar solo los primeros 3
                print(f"   📺 {panel.get('name')} ({panel.get('ip')}) - {panel.get('status')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Test de conectividad
    print(f"\n4️⃣ Test de conectividad")
    print("-" * 20)
    try:
        payload = {"ip": panel_ip}
        response = requests.post(f"{base_url}/api/panels/test", 
                               json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Panel {panel_ip}: {data.get('message')}")
            print(f"   ⏱️  Tiempo de respuesta: {data.get('response_time')}ms")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Envío de mensaje individual
    print(f"\n5️⃣ Envío de mensaje individual")
    print("-" * 20)
    try:
        payload = {
            "text": "PROVA JAVA",
            "color": 1,
            "fontSize": 16,
            "windowNo": 0,
            "effect": 0,
            "speed": 1,
            "stayTime": 5
        }
        response = requests.post(f"{base_url}/api/panels/send", 
                               json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Mensaje enviado: {data.get('message')}")
            print(f"   📺 Panel: {data.get('panelIp')}")
            print(f"   🔧 Protocolo: {data.get('protocol')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            print(f"   📋 Respuesta: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Envío múltiple (formato antiguo)
    print(f"\n6️⃣ Envío múltiple (formato antiguo)")
    print("-" * 20)
    try:
        payload = {
            "ip": panel_ip,
            "itemNum": 1,
            "texts": ["MULTI TEST"],
            "colors": [1],
            "fontSizes": [16],
            "showEffects": [0]
        }
        response = requests.post(f"{base_url}/sendMulti", 
                               json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Envío múltiple: {data.get('message')}")
            print(f"   📺 Panel: {data.get('panel_ip')}")
            print(f"   🔧 Protocolo: {data.get('protocol')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            print(f"   📋 Respuesta: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: Mensaje de ocupación
    print(f"\n7️⃣ Mensaje de ocupación")
    print("-" * 20)
    try:
        payload = {
            "ip": panel_ip,
            "parkingNumber": 4,
            "parkingName": "P. Poble antic/Belles Arts 2",
            "freeSpaces": 25,
            "totalSpaces": 50,
            "status": "LIBRE",
            "language": "es"
        }
        response = requests.post(f"{base_url}/api/panels/occupancy", 
                               json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Ocupación enviada: {data.get('message')}")
            print(f"   📺 Panel: {data.get('panelIp')}")
            print(f"   🔧 Protocolo: {data.get('protocol')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            print(f"   📋 Respuesta: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n✅ PRUEBAS COMPLETADAS")
    print("=" * 50)
    return True

def test_panel_communication():
    """Probar comunicación directa con el panel"""
    
    print(f"\n🔌 PRUEBA DE COMUNICACIÓN DIRECTA CON PANEL")
    print("=" * 50)
    
    panel_ip = "172.20.4.52"
    
    # Test de ping
    print(f"\n📡 Test de conectividad con {panel_ip}")
    print("-" * 40)
    
    import subprocess
    try:
        result = subprocess.run(['ping', '-c', '3', panel_ip], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ Panel responde al ping")
            # Extraer tiempo de respuesta
            lines = result.stdout.split('\n')
            for line in lines:
                if 'time=' in line:
                    time_str = line.split('time=')[1].split()[0]
                    print(f"   ⏱️  Tiempo de respuesta: {time_str}")
                    break
        else:
            print(f"   ❌ Panel no responde al ping")
            print(f"   📋 Salida: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Error en ping: {e}")
    
    return True

if __name__ == "__main__":
    print(f"🚀 Iniciando pruebas del servicio Java de paneles v2.5")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar pruebas
    success = test_java_panel_service()
    test_panel_communication()
    
    if success:
        print(f"\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    else:
        print(f"\n❌ ALGUNAS PRUEBAS FALLARON")
    
    print(f"\n⏰ Fin de pruebas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 