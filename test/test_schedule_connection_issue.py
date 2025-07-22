#!/usr/bin/env python3
"""
Script para diagnosticar el problema ECONNRESET en la creación de programaciones
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuración
API_BASE_URL = "http://157.180.91.63:8888/api"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def test_connection_timeout():
    """Probar diferentes timeouts para identificar el problema"""
    
    print("🔍 Probando diferentes configuraciones de timeout...")
    
    # Datos de prueba
    schedule_data = {
        "name": "Prueba Timeout",
        "parking_id": 1,
        "message": "Mensaje de prueba",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "start_time": "09:00",
        "end_time": "18:00",
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
        "saturday": False,
        "sunday": False,
        "is_active": True
    }
    
    timeouts = [5, 10, 30, 60]
    
    for timeout in timeouts:
        print(f"\n⏱️  Probando con timeout de {timeout} segundos...")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/schedules",
                headers=HEADERS,
                json=schedule_data,
                timeout=timeout
            )
            end_time = time.time()
            
            print(f"   ✅ Respuesta recibida en {end_time - start_time:.2f}s")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ Programación creada: {result.get('schedule_id')}")
                    return True
                else:
                    print(f"   ❌ Error del servidor: {result.get('error')}")
            else:
                print(f"   ❌ Error HTTP: {response.text}")
                
        except requests.exceptions.Timeout as e:
            print(f"   ⏰ Timeout después de {timeout}s: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 Error de conexión: {e}")
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")
    
    return False

def test_simple_endpoints():
    """Probar endpoints simples para verificar conectividad básica"""
    
    print("\n🔍 Probando conectividad básica...")
    
    endpoints = [
        "/parkings",
        "/panels", 
        "/schedules"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"   Probando GET {endpoint}...")
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            print(f"   ✅ Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_database_connection():
    """Probar si el problema está en la base de datos"""
    
    print("\n🔍 Probando conexión a base de datos...")
    
    try:
        # Intentar obtener parkings (requiere conexión a BD)
        response = requests.get(f"{API_BASE_URL}/parkings", timeout=10)
        
        if response.status_code == 200:
            parkings = response.json()
            print(f"   ✅ Conexión a BD OK - {len(parkings)} parkings encontrados")
            return True
        else:
            print(f"   ❌ Error en BD: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_schedule_creation_step_by_step():
    """Probar la creación de programación paso a paso"""
    
    print("\n🔍 Probando creación paso a paso...")
    
    # Paso 1: Verificar que el parking existe
    try:
        response = requests.get(f"{API_BASE_URL}/parkings", timeout=10)
        if response.status_code == 200:
            parkings = response.json()
            if not parkings:
                print("   ❌ No hay parkings disponibles")
                return False
            parking_id = parkings[0]['id']
            print(f"   ✅ Parking encontrado: {parking_id}")
        else:
            print(f"   ❌ Error obteniendo parkings: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Paso 2: Crear programación con datos mínimos
    schedule_data = {
        "name": f"Prueba {datetime.now().strftime('%H:%M:%S')}",
        "parking_id": parking_id,
        "message": "TEST",
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
        print(f"   📤 Enviando programación...")
        response = requests.post(
            f"{API_BASE_URL}/schedules",
            headers=HEADERS,
            json=schedule_data,
            timeout=30
        )
        
        print(f"   📥 Respuesta: {response.status_code}")
        
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

if __name__ == "__main__":
    print("🚀 Diagnóstico de problema ECONNRESET en programaciones")
    print("=" * 60)
    
    # Pruebas básicas
    test_simple_endpoints()
    test_database_connection()
    
    # Pruebas específicas
    test_connection_timeout()
    test_schedule_creation_step_by_step()
    
    print("\n" + "=" * 60)
    print("🏁 Diagnóstico completado") 