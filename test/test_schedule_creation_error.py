#!/usr/bin/env python3
"""
Script para probar la creación de programaciones y detectar errores específicos
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuración
API_BASE_URL = "http://157.180.91.63:8888/api"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def test_schedule_creation():
    """Probar la creación de una programación y capturar errores"""
    
    print("🔍 Probando creación de programación...")
    
    # Datos de prueba para la programación
    schedule_data = {
        "name": "Prueba Error Detection",
        "parking_id": 1,
        "message": "Mensaje de prueba",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "start_time": "09:00",
        "end_time": "18:00",
        "weekdays": [1, 2, 3, 4, 5],  # Lunes a Viernes
        "is_active": True
    }
    
    try:
        print(f"📤 Enviando petición a: {API_BASE_URL}/schedules")
        print(f"📋 Datos: {json.dumps(schedule_data, indent=2)}")
        
        response = requests.post(
            f"{API_BASE_URL}/schedules",
            headers=HEADERS,
            json=schedule_data,
            timeout=30
        )
        
        print(f"📥 Respuesta recibida:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            print("✅ Programación creada exitosamente")
            result = response.json()
            print(f"   ID: {result.get('id')}")
            print(f"   Nombre: {result.get('name')}")
        else:
            print("❌ Error al crear programación")
            print(f"   Response Text: {response.text}")
            
            try:
                error_data = response.json()
                print(f"   Error JSON: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error no es JSON válido")
                
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de petición: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

def test_parkings_endpoint():
    """Probar el endpoint de parkings para verificar que funciona"""
    
    print("\n🔍 Probando endpoint de parkings...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/parkings", timeout=10)
        
        print(f"📥 Respuesta parkings:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            parkings = response.json()
            print(f"   ✅ Parkings disponibles: {len(parkings)}")
            for parking in parkings[:3]:  # Mostrar solo los primeros 3
                print(f"      - ID: {parking.get('id')}, Nombre: {parking.get('name')}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_database_connection():
    """Probar la conexión a la base de datos"""
    
    print("\n🔍 Probando conexión a base de datos...")
    
    try:
        # Intentar obtener parkings como proxy de conexión a BD
        response = requests.get(f"{API_BASE_URL}/parkings", timeout=5)
        
        if response.status_code == 200:
            print("   ✅ Conexión a base de datos OK")
        else:
            print(f"   ❌ Error en conexión: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de creación de programaciones")
    print("=" * 60)
    
    test_database_connection()
    test_parkings_endpoint()
    test_schedule_creation()
    
    print("\n" + "=" * 60)
    print("🏁 Pruebas completadas") 