#!/usr/bin/env python3
"""
Script para probar el endpoint de estadísticas por horas
"""

import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"
PARKING_ID = 1  # Parking de prueba

def test_statistics_endpoint():
    """Probar el endpoint de estadísticas por horas"""
    print("🔍 Probando endpoint de estadísticas por horas...")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Parking ID: {PARKING_ID}")
    print("=" * 80)
    
    try:
        # Probar endpoint de estadísticas por horas
        url = f"{API_BASE_URL}/parking/{PARKING_ID}/hourly-statistics?days=1"
        print(f"🌐 URL: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funcionando correctamente")
            print(f"📈 Datos recibidos:")
            print(f"   - Parking: {data.get('parking_name')}")
            print(f"   - Período: {data.get('period', {}).get('start_date')} a {data.get('period', {}).get('end_date')}")
            print(f"   - Estadísticas por horas: {len(data.get('hourly_statistics', []))} registros")
            print(f"   - Estadísticas de cámaras: {len(data.get('camera_statistics', []))} cámaras")
            
            # Mostrar algunas estadísticas de ejemplo
            hourly_stats = data.get('hourly_statistics', [])
            if hourly_stats:
                print("\n📊 Ejemplo de estadísticas por horas:")
                for stat in hourly_stats[:3]:  # Mostrar solo las primeras 3
                    print(f"   {stat.get('hour_label')}: {stat.get('total_vehicles_in')} entradas, {stat.get('total_vehicles_out')} salidas")
            
            camera_stats = data.get('camera_statistics', [])
            if camera_stats:
                print("\n📷 Estadísticas de cámaras:")
                for camera in camera_stats:
                    print(f"   {camera.get('camera_name')}: {camera.get('processed_messages')} mensajes procesados, {camera.get('success_rate')}% éxito")
            
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - El endpoint no responde en 30 segundos")
    except requests.exceptions.ConnectionError:
        print("🔌 Error de conexión - No se puede conectar al servidor")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_parking_endpoint():
    """Probar el endpoint básico del parking"""
    print("\n🔍 Probando endpoint básico del parking...")
    
    try:
        url = f"{API_BASE_URL}/parking/{PARKING_ID}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint de parking funcionando")
            print(f"   - Nombre: {data.get('name')}")
            print(f"   - Capacidad: {data.get('total_plazas')}")
            print(f"   - Ocupación: {data.get('plazas_ocupadas')}")
        else:
            print(f"❌ Error en endpoint de parking: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error probando parking: {e}")

def test_frontend_api():
    """Probar si el frontend puede acceder a la API"""
    print("\n🔍 Probando acceso desde frontend...")
    
    try:
        # Simular la llamada que hace el frontend
        url = f"{API_BASE_URL}/parking/{PARKING_ID}/hourly-statistics"
        params = {
            'days': 1
        }
        
        response = requests.get(url, params=params, timeout=30)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API accesible desde frontend")
            print(f"📈 Datos disponibles: {list(data.keys())}")
        else:
            print(f"❌ API no accesible: {response.status_code}")
            print(f"📄 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error accediendo a API: {e}")

if __name__ == "__main__":
    test_parking_endpoint()
    test_statistics_endpoint()
    test_frontend_api() 