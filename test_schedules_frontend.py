#!/usr/bin/env python3
"""
Script para probar la integración del frontend con los endpoints de schedules
"""

import requests
import json

def test_schedules_integration():
    """Probar la integración de schedules"""
    base_url = "http://157.180.91.63:6001"
    
    print("🚀 Probando integración de schedules...")
    
    # 1. Probar endpoint de parkings (para el selector)
    print("\n1️⃣ Probando endpoint /parkings...")
    try:
        response = requests.get(f"{base_url}/parkings")
        if response.status_code == 200:
            parkings = response.json()
            print(f"✅ Éxito: {len(parkings)} parkings encontrados")
            if parkings:
                print(f"   Primer parking: {parkings[0]['name']} (ID: {parkings[0]['id']})")
                print(f"   Segundo parking: {parkings[1]['name']} (ID: {parkings[1]['id']})")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 2. Probar endpoint de schedules
    print("\n2️⃣ Probando endpoint /schedules...")
    try:
        response = requests.get(f"{base_url}/schedules")
        if response.status_code == 200:
            schedules = response.json()
            print(f"✅ Éxito: {len(schedules.get('schedules', []))} schedules encontrados")
            print(f"   Success: {schedules.get('success', False)}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 3. Probar endpoint de schedules con filtro de parking
    print("\n3️⃣ Probando endpoint /schedules con filtro de parking...")
    try:
        response = requests.get(f"{base_url}/schedules?parking_id=1")
        if response.status_code == 200:
            schedules = response.json()
            print(f"✅ Éxito: {len(schedules.get('schedules', []))} schedules para parking 1")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 4. Probar endpoint de schedules con filtro de activos
    print("\n4️⃣ Probando endpoint /schedules con filtro de activos...")
    try:
        response = requests.get(f"{base_url}/schedules?active_only=true")
        if response.status_code == 200:
            schedules = response.json()
            print(f"✅ Éxito: {len(schedules.get('schedules', []))} schedules activos")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 5. Probar creación de un schedule (POST)
    print("\n5️⃣ Probando creación de schedule...")
    try:
        schedule_data = {
            "parking_id": 1,
            "name": "Test Schedule",
            "description": "Schedule de prueba",
            "start_date": "2025-07-02T00:00:00Z",
            "end_date": "2025-07-31T23:59:59Z",
            "start_time": "09:00",
            "end_time": "18:00",
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": True,
            "friday": True,
            "saturday": False,
            "sunday": False,
            "message": "Mensaje de prueba",
            "color": 2,
            "font_size": 2,
            "effect": "static",
            "priority": 1,
            "is_active": True
        }
        
        response = requests.post(
            f"{base_url}/schedules",
            json=schedule_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Éxito: Schedule creado")
            print(f"   Success: {result.get('success', False)}")
            if result.get('schedule'):
                print(f"   ID: {result['schedule'].get('id')}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    print("\n🎉 Pruebas de integración de schedules completadas")

if __name__ == "__main__":
    test_schedules_integration() 