#!/usr/bin/env python3
"""
Script para verificar la configuración correcta de puertos
"""

import requests
import json
from datetime import datetime, timedelta

def test_port_configuration():
    """Verificar la configuración de puertos"""
    
    print("🔍 Verificando configuración de puertos...")
    
    # Configuraciones a probar
    configs = [
        {
            "name": "Frontend (Puerto 5789) - API Parkings",
            "url": "http://157.180.91.63:5789/api/parkings",
            "expected": 200
        },
        {
            "name": "Frontend (Puerto 5789) - API Schedules",
            "url": "http://157.180.91.63:5789/api/schedules",
            "expected": 200
        },
        {
            "name": "Backend Directo (Puerto 6001) - API Parkings",
            "url": "http://157.180.91.63:6001/api/parkings",
            "expected": 200
        },
        {
            "name": "Panel Service (Puerto 8888) - Verificar que existe",
            "url": "http://157.180.91.63:8888/",
            "expected": "any"
        }
    ]
    
    for config in configs:
        try:
            print(f"\n📡 Probando: {config['name']}")
            response = requests.get(config['url'], timeout=10)
            
            if config['expected'] == "any":
                print(f"   ✅ Respuesta: {response.status_code}")
            elif response.status_code == config['expected']:
                print(f"   ✅ OK - Status: {response.status_code}")
            else:
                print(f"   ❌ Error - Status: {response.status_code} (esperado: {config['expected']})")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_schedule_creation():
    """Probar la creación de programación con la configuración correcta"""
    
    print("\n🔍 Probando creación de programación...")
    
    # Datos de prueba
    schedule_data = {
        "name": f"Prueba Puertos {datetime.now().strftime('%H:%M:%S')}",
        "parking_id": 1,
        "message": "TEST PUERTOS",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "start_time": "09:00",
        "end_time": "10:00",
        "monday": True,
        "tuesday": False,
        "wednesday": False,
        "thursday": False,
        "friday": False,
        "saturday": False,
        "sunday": False,
        "is_active": True
    }
    
    try:
        print(f"📤 Enviando a: http://157.180.91.63:5789/api/schedules")
        response = requests.post(
            "http://157.180.91.63:5789/api/schedules",
            headers={'Content-Type': 'application/json'},
            json=schedule_data,
            timeout=30
        )
        
        print(f"📥 Respuesta: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ Programación creada exitosamente")
                return True
            else:
                print(f"   ❌ Error del servidor: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Error HTTP: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"   🔌 ECONNRESET detectado: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False

def test_panel_service():
    """Verificar que el servicio de paneles está funcionando"""
    
    print("\n🔍 Verificando servicio de paneles (puerto 8888)...")
    
    try:
        response = requests.get("http://157.180.91.63:8888/", timeout=5)
        print(f"   ✅ Servicio de paneles responde: {response.status_code}")
        return True
    except Exception as e:
        print(f"   ❌ Servicio de paneles no responde: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Verificación de configuración de puertos")
    print("=" * 60)
    
    test_port_configuration()
    test_panel_service()
    test_schedule_creation()
    
    print("\n" + "=" * 60)
    print("🏁 Verificación completada") 