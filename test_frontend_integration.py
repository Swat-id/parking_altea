#!/usr/bin/env python3
"""
Script para probar la integración del frontend con la API
"""

import requests
import json

def test_frontend_integration():
    """Probar la integración completa del frontend"""
    base_url = "http://localhost:6001"
    
    print("🚀 Probando integración del frontend con la API...")
    
    # 1. Probar endpoint de listar parkings (como hace la página principal)
    print("\n1️⃣ Probando endpoint /parkings...")
    try:
        response = requests.get(f"{base_url}/parkings")
        if response.status_code == 200:
            parkings = response.json()
            print(f"✅ Éxito: {len(parkings)} parkings encontrados")
            if parkings:
                print(f"   Primer parking: {parkings[0]['name']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 2. Probar endpoint de obtener parking específico (como hace ParkingDetail)
    print("\n2️⃣ Probando endpoint /parking/1...")
    try:
        response = requests.get(f"{base_url}/parking/1")
        if response.status_code == 200:
            parking = response.json()
            print(f"✅ Éxito: Parking encontrado")
            print(f"   Nombre: {parking['name']}")
            print(f"   Ocupación: {parking['plazas_ocupadas']}/{parking['total_plazas']}")
            print(f"   Estado: {parking['estado']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 3. Probar endpoint de actualizar ocupación (como hace ParkingDetail)
    print("\n3️⃣ Probando endpoint /parking/1/occupancy...")
    try:
        data = {"occupancy": 60}
        response = requests.post(f"{base_url}/parking/1/occupancy", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Éxito: Ocupación actualizada")
            print(f"   Nueva ocupación: {result['occupancy']}")
            print(f"   Cambio: {result['change_amount']}")
            print(f"   Estado: {result['status']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 4. Probar endpoint de actualizar configuración (como hace ParkingDetail)
    print("\n4️⃣ Probando endpoint /parking/1/config...")
    try:
        data = {
            "total_plazas": 500,
            "threshold_dense": 15,
            "threshold_full": 5
        }
        response = requests.post(f"{base_url}/parking/1/config", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Éxito: Configuración actualizada")
            print(f"   Capacidad: {result['max_capacity']}")
            print(f"   Umbral denso: {result['threshold_dense']}")
            print(f"   Umbral completo: {result['threshold_full']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 5. Probar endpoint de obtener cámaras (como hace ParkingDetail)
    print("\n5️⃣ Probando endpoint /parking/1/cameras...")
    try:
        response = requests.get(f"{base_url}/parking/1/cameras")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ Éxito: {len(cameras)} cámaras encontradas")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    # 6. Probar endpoint de obtener paneles (como hace ParkingDetail)
    print("\n6️⃣ Probando endpoint /panels...")
    try:
        response = requests.get(f"{base_url}/panels")
        if response.status_code == 200:
            panels = response.json()
            print(f"✅ Éxito: {len(panels)} paneles encontrados")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")
    
    print("\n🎉 Pruebas de integración completadas")

if __name__ == "__main__":
    test_frontend_integration() 