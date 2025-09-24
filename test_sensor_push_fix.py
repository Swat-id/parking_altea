#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones del servicio push de sensores
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:3535"

def test_sensor_push_with_real_format():
    """Prueba el servicio push con el formato real de los sensores"""
    
    # Datos en el formato real que envían los sensores
    real_sensor_data = {
        "carpark_id": "905",
        "carpark_code": "ES-SW-2", 
        "floor": "0",
        "id": "35634",
        "number": "1",
        "parking_cards": [],
        "status": "FREE",  # Mayúsculas como envían los sensores reales
        "idle": True,
        "timestamp": "2025-09-24 07:30:51.987",  # Con milisegundos
        "sensor_info": {
            "serial_number": "FC072308",
            "network_info": {
                "type": "NBIOT",
                "rssi": "-99",
                "on_air": "2895"
            },
            "temperature": "22",
            "battery_voltage": "3570",
            "battery_capacity": 98.62,
            "visible_cards": []
        }
    }
    
    print("=== Test: Formato real de sensores ===")
    print(f"Enviando datos a {BASE_URL}/")
    print(f"Status: {real_sensor_data['status']} (mayúsculas)")
    print(f"Timestamp: {real_sensor_data['timestamp']} (con milisegundos)")
    print(f"Serial: {real_sensor_data['sensor_info']['serial_number']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/",
            json=real_sensor_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nRespuesta HTTP: {response.status_code}")
        print(f"Respuesta JSON: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ SUCCESS: Sensor procesado correctamente")
                return True
            else:
                print(f"❌ ERROR: {result.get('error')}")
                print(f"Detalles: {result.get('details')}")
                return False
        else:
            print(f"❌ ERROR HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_multiple_sensors():
    """Prueba múltiples sensores con diferentes estados"""
    
    sensors_data = [
        {
            "serial": "FC07230C",
            "number": "5", 
            "status": "FREE"
        },
        {
            "serial": "FC07230A", 
            "number": "3",
            "status": "BUSY"
        },
        {
            "serial": "FC07230E",
            "number": "7", 
            "status": "ERROR"
        }
    ]
    
    print("\n=== Test: Múltiples sensores ===")
    
    success_count = 0
    for sensor_data in sensors_data:
        test_data = {
            "carpark_id": "905",
            "carpark_code": "ES-SW-2",
            "floor": "0", 
            "id": f"3563{sensor_data['number']}",
            "number": sensor_data['number'],
            "parking_cards": [],
            "status": sensor_data['status'],
            "idle": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "sensor_info": {
                "serial_number": sensor_data['serial'],
                "network_info": {
                    "type": "NBIOT",
                    "rssi": "-99",
                    "on_air": "2895"
                },
                "temperature": "22",
                "battery_voltage": "3570", 
                "battery_capacity": 98.62,
                "visible_cards": []
            }
        }
        
        print(f"\nProbando sensor {sensor_data['serial']} - Estado: {sensor_data['status']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ {sensor_data['serial']}: SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ {sensor_data['serial']}: {result.get('error')}")
            else:
                print(f"❌ {sensor_data['serial']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {sensor_data['serial']}: Exception - {str(e)}")
    
    print(f"\n=== Resultados: {success_count}/{len(sensors_data)} sensores procesados correctamente ===")
    return success_count == len(sensors_data)

def test_health_endpoint():
    """Prueba el endpoint de salud"""
    print("\n=== Test: Health endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando pruebas del servicio push corregido...\n")
    
    # Probar endpoint de salud
    health_ok = test_health_endpoint()
    
    if not health_ok:
        print("❌ Servicio no disponible. Asegúrate de que esté corriendo en puerto 3535")
        exit(1)
    
    # Probar formato real de sensores
    real_format_ok = test_sensor_push_with_real_format()
    
    # Probar múltiples sensores
    multiple_ok = test_multiple_sensors()
    
    print(f"\n🏁 RESUMEN FINAL:")
    print(f"Health endpoint: {'✅' if health_ok else '❌'}")
    print(f"Formato real: {'✅' if real_format_ok else '❌'}")
    print(f"Múltiples sensores: {'✅' if multiple_ok else '❌'}")
    
    if health_ok and real_format_ok and multiple_ok:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! El servicio push está listo.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar logs del servicio.")
