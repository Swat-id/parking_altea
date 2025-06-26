#!/usr/bin/env python3
"""
Script de validación rápida para la página de estadísticas
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://157.180.91.63:6001"
FRONTEND_URL = "http://157.180.91.63"

def test_statistics_endpoints():
    """Probar endpoints de estadísticas"""
    print("🔍 Probando endpoints de estadísticas...")
    print("=" * 50)
    
    # Test 1: Ruta de estadísticas sin ID (debería redirigir)
    try:
        response = requests.get(f"{BASE_URL}/statistics", timeout=10)
        print(f"📊 GET /statistics - Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Endpoint accesible")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test 2: Estadísticas con ID específico
    try:
        response = requests.get(f"{BASE_URL}/parking/1/hourly-statistics?days=1", timeout=10)
        print(f"📊 GET /parking/1/hourly-statistics - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Datos obtenidos para: {data.get('parking_name', 'N/A')}")
            print(f"   📈 Horas con datos: {len(data.get('hourly_statistics', []))}")
            print(f"   📷 Cámaras: {len(data.get('camera_statistics', []))}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test 3: Frontend accesible
    try:
        response = requests.get(f"{FRONTEND_URL}", timeout=10)
        print(f"🌐 GET Frontend - Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Frontend accesible")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

def test_parking_data():
    """Probar datos de parking para estadísticas"""
    print("\n🔍 Probando datos de parking...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/parkings", timeout=10)
        if response.status_code == 200:
            parkings = response.json()
            print(f"📊 Total parkings: {len(parkings)}")
            
            # Mostrar primeros 3 parkings
            for i, parking in enumerate(parkings[:3]):
                name = parking.get('name', 'N/A')
                status = parking.get('estado', 'N/A')
                occupancy = parking.get('plazas_ocupadas', 0)
                capacity = parking.get('total_plazas', 0)
                print(f"   📍 {name}: {status} ({occupancy}/{capacity})")
        else:
            print(f"❌ Error obteniendo parkings: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def main():
    """Función principal"""
    print("🚀 Validación rápida de página de estadísticas")
    print("📅 Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    test_statistics_endpoints()
    test_parking_data()
    
    print("\n" + "=" * 50)
    print("📋 INSTRUCCIONES PARA EL USUARIO")
    print("=" * 50)
    print("1. Abrir el navegador y ir a: http://157.180.91.63")
    print("2. Navegar a la página de Estadísticas")
    print("3. Verificar que se muestra correctamente")
    print("4. Probar cambiar entre diferentes parkings")
    print("5. Verificar que los gráficos se cargan")
    print("\n✅ Si todo funciona, las correcciones están aplicadas correctamente")

if __name__ == "__main__":
    main() 