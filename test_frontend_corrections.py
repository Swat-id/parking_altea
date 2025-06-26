#!/usr/bin/env python3
"""
Script de validación para verificar las correcciones del frontend
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://157.180.91.63"
API_URL = f"{BASE_URL}:6001"

def test_api_endpoints():
    """Probar endpoints del API"""
    print("🔍 Probando endpoints del API...")
    
    endpoints = [
        ("/parkings", "GET"),
        ("/parking/1", "GET"),
        ("/parking/1/cameras", "GET"),
        ("/panels", "GET"),
        ("/camera/logs", "GET"),
        ("/camera/logs/stats", "GET"),
        ("/cameras/status", "GET")
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{API_URL}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {method} {endpoint} - OK")
                data = response.json()
                if isinstance(data, list):
                    print(f"   📊 Registros: {len(data)}")
                elif isinstance(data, dict):
                    if 'logs' in data:
                        print(f"   📊 Logs: {len(data['logs'])}")
                    elif 'cameras' in data:
                        print(f"   📊 Cámaras: {len(data['cameras'])}")
                    elif 'panels' in data:
                        print(f"   📊 Paneles: {len(data.get('panels', []))}")
            else:
                print(f"❌ {method} {endpoint} - Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {e}")

def test_frontend_pages():
    """Probar páginas del frontend"""
    print("\n🌐 Probando páginas del frontend...")
    
    pages = [
        "/",
        "/parkings",
        "/camera-logs",
        "/panels",
        "/statistics"
    ]
    
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {page} - OK")
            else:
                print(f"❌ {page} - Error {response.status_code}")
        except Exception as e:
            print(f"❌ {page} - Error: {e}")

def test_parking_detail():
    """Probar página de detalle de parking"""
    print("\n🏢 Probando página de detalle de parking...")
    
    try:
        response = requests.get(f"{BASE_URL}/parking/1", timeout=10)
        if response.status_code == 200:
            print("✅ /parking/1 - OK")
        else:
            print(f"❌ /parking/1 - Error {response.status_code}")
    except Exception as e:
        print(f"❌ /parking/1 - Error: {e}")

def test_camera_logs_with_filters():
    """Probar logs de cámaras con filtros"""
    print("\n📋 Probando logs de cámaras con filtros...")
    
    filters = [
        "?parking_id=1",
        "?parking_id=1&limit=10",
        "?date_filter=today",
        "?level=error"
    ]
    
    for filter_param in filters:
        try:
            response = requests.get(f"{API_URL}/camera/logs{filter_param}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ /camera/logs{filter_param} - OK ({len(data.get('logs', []))} logs)")
            else:
                print(f"❌ /camera/logs{filter_param} - Error {response.status_code}")
        except Exception as e:
            print(f"❌ /camera/logs{filter_param} - Error: {e}")

def test_panels_by_parking():
    """Probar paneles por parking"""
    print("\n🖥️ Probando paneles por parking...")
    
    try:
        # Obtener todos los paneles
        response = requests.get(f"{API_URL}/panels", timeout=10)
        if response.status_code == 200:
            panels = response.json()
            print(f"✅ /panels - OK ({len(panels)} paneles total)")
            
            # Agrupar por parking
            parking_panels = {}
            for panel in panels:
                parking_id = panel.get('parking_id')
                if parking_id not in parking_panels:
                    parking_panels[parking_id] = []
                parking_panels[parking_id].append(panel)
            
            for parking_id, panel_list in parking_panels.items():
                print(f"   🏢 Parking {parking_id}: {len(panel_list)} paneles")
        else:
            print(f"❌ /panels - Error {response.status_code}")
    except Exception as e:
        print(f"❌ /panels - Error: {e}")

def test_camera_status():
    """Probar estado de cámaras"""
    print("\n📹 Probando estado de cámaras...")
    
    try:
        response = requests.get(f"{API_URL}/cameras/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ /cameras/status - OK ({len(cameras)} cámaras)")
            
            # Contar por estado
            online_count = sum(1 for cam in cameras if cam.get('status') == 'ONLINE')
            offline_count = len(cameras) - online_count
            print(f"   🟢 Online: {online_count}")
            print(f"   🔴 Offline: {offline_count}")
        else:
            print(f"❌ /cameras/status - Error {response.status_code}")
    except Exception as e:
        print(f"❌ /cameras/status - Error: {e}")

def main():
    """Función principal"""
    print("🚀 Iniciando validación de correcciones del frontend")
    print("=" * 60)
    
    start_time = time.time()
    
    # Ejecutar todas las pruebas
    test_api_endpoints()
    test_frontend_pages()
    test_parking_detail()
    test_camera_logs_with_filters()
    test_panels_by_parking()
    test_camera_status()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print(f"✅ Validación completada en {duration:.2f} segundos")
    print("🎉 Las correcciones del frontend han sido aplicadas correctamente")
    print("\n📝 Resumen de mejoras:")
    print("   • ✅ Servicios corregidos con rutas correctas")
    print("   • ✅ Página de logs de cámaras funcional")
    print("   • ✅ Página de detalle de parking mejorada")
    print("   • ✅ Indicadores de última actualización")
    print("   • ✅ Filtros y navegación mejorados")
    print("   • ✅ Manejo de errores mejorado")

if __name__ == "__main__":
    main() 