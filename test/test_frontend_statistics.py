#!/usr/bin/env python3
"""
Script para probar el frontend de estadísticas
"""

import requests
import json
from datetime import datetime

# Configuración
FRONTEND_URL = "http://157.180.91.63:5789"
API_BASE_URL = "http://157.180.91.63:6001"
PARKING_ID = 1

def test_frontend_access():
    """Probar acceso al frontend"""
    print("🔍 Probando acceso al frontend...")
    print(f"🌐 URL: {FRONTEND_URL}")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Frontend accesible")
            print(f"📄 Tamaño de respuesta: {len(response.text)} bytes")
        else:
            print(f"❌ Error accediendo al frontend: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_api_from_frontend():
    """Probar las llamadas API que hace el frontend"""
    print("\n🔍 Probando llamadas API del frontend...")
    
    # Simular la llamada que hace el frontend para obtener datos del parking
    try:
        url = f"{API_BASE_URL}/parking/{PARKING_ID}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos del parking obtenidos correctamente")
            print(f"   - Nombre: {data.get('name')}")
            print(f"   - Capacidad: {data.get('total_plazas')}")
            print(f"   - Umbrales: Denso={data.get('threshold_dense')}, Completo={data.get('threshold_full')}")
        else:
            print(f"❌ Error obteniendo datos del parking: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Simular la llamada de estadísticas por horas
    try:
        url = f"{API_BASE_URL}/parking/{PARKING_ID}/hourly-statistics"
        params = {'days': 1}
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Estadísticas por horas obtenidas correctamente")
            print(f"   - Parking: {data.get('parking_name')}")
            print(f"   - Horas: {len(data.get('hourly_statistics', []))}")
            print(f"   - Cámaras: {len(data.get('camera_statistics', []))}")
            
            # Verificar estructura de datos
            hourly_stats = data.get('hourly_statistics', [])
            if hourly_stats:
                first_stat = hourly_stats[0]
                print(f"   - Estructura de estadísticas: {list(first_stat.keys())}")
                
        else:
            print(f"❌ Error obteniendo estadísticas: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_cors_headers():
    """Probar headers CORS"""
    print("\n🔍 Probando headers CORS...")
    
    try:
        url = f"{API_BASE_URL}/parking/{PARKING_ID}/hourly-statistics"
        response = requests.get(url, timeout=10)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("📋 Headers CORS:")
        for header, value in cors_headers.items():
            print(f"   {header}: {value}")
            
        if cors_headers['Access-Control-Allow-Origin']:
            print("✅ Headers CORS configurados")
        else:
            print("⚠️  Headers CORS no encontrados")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_error_scenarios():
    """Probar escenarios de error"""
    print("\n🔍 Probando escenarios de error...")
    
    # Probar con parking inexistente
    try:
        url = f"{API_BASE_URL}/parking/999/hourly-statistics"
        response = requests.get(url, timeout=10)
        print(f"📊 Parking inexistente (999): {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error con parking inexistente: {e}")
    
    # Probar con parámetros inválidos
    try:
        url = f"{API_BASE_URL}/parking/{PARKING_ID}/hourly-statistics"
        params = {'days': 'invalid'}
        response = requests.get(url, params=params, timeout=10)
        print(f"📊 Parámetros inválidos: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error con parámetros inválidos: {e}")

if __name__ == "__main__":
    print("🧪 Iniciando pruebas del frontend de estadísticas")
    print("=" * 60)
    
    test_frontend_access()
    test_api_from_frontend()
    test_cors_headers()
    test_error_scenarios()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas") 