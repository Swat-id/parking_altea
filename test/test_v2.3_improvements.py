#!/usr/bin/env python3
"""
Script de validación para las mejoras implementadas en v2.3
- Monitorización mejorada de mensajes de cámaras
- Estadísticas por horas
- Verificación periódica del estado de cámaras
- Protección contra duplicados con correcciones
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuración
BASE_URL = "http://localhost:5000"
CAMERA_URL = "http://localhost:5001"

def test_api_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Probar un endpoint de la API"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - OK")
            return response.json() if response.content else {}
        else:
            print(f"❌ {method} {endpoint} - Error {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return None

def test_camera_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Probar un endpoint del servidor de cámaras"""
    try:
        url = f"{CAMERA_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - OK")
            return response.json() if response.content else {}
        else:
            print(f"❌ {method} {endpoint} - Error {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return None

def test_camera_logs_improvements():
    """Probar mejoras en logs de cámaras"""
    print("\n🔍 Probando mejoras en logs de cámaras...")
    
    # Probar endpoint de logs con nuevos campos
    logs_data = test_api_endpoint("/camera/logs?limit=5")
    if logs_data and 'logs' in logs_data:
        logs = logs_data['logs']
        if logs:
            log = logs[0]
            required_fields = ['raw_message', 'previous_vehicle_in', 'previous_vehicle_out', 'delta_in', 'delta_out']
            missing_fields = [field for field in required_fields if field not in log]
            
            if missing_fields:
                print(f"⚠️ Campos faltantes en logs: {missing_fields}")
            else:
                print("✅ Todos los campos mejorados presentes en logs")
                
                # Verificar que raw_message contiene datos
                if log.get('raw_message'):
                    print("✅ Campo raw_message contiene datos")
                else:
                    print("⚠️ Campo raw_message vacío")
        else:
            print("⚠️ No hay logs para verificar")
    
    # Probar estadísticas de logs
    stats_data = test_api_endpoint("/camera/logs/stats?days=1")
    if stats_data:
        print("✅ Estadísticas de logs funcionando")

def test_hourly_statistics():
    """Probar estadísticas por horas"""
    print("\n📊 Probando estadísticas por horas...")
    
    # Probar endpoint de estadísticas por horas
    hourly_data = test_api_endpoint("/parking/1/hourly-statistics?days=1")
    if hourly_data:
        if 'hourly_statistics' in hourly_data:
            hourly_stats = hourly_data['hourly_statistics']
            print(f"✅ Estadísticas por horas obtenidas - {len(hourly_stats)} horas")
            
            # Verificar estructura de datos
            if hourly_stats:
                stat = hourly_stats[0]
                required_fields = ['hour', 'hour_label', 'total_vehicles_in', 'total_vehicles_out', 
                                 'net_change', 'message_count', 'avg_occupancy', 'max_occupancy', 'min_occupancy']
                missing_fields = [field for field in required_fields if field not in stat]
                
                if missing_fields:
                    print(f"⚠️ Campos faltantes en estadísticas por horas: {missing_fields}")
                else:
                    print("✅ Estructura de estadísticas por horas correcta")
        
        if 'camera_statistics' in hourly_data:
            camera_stats = hourly_data['camera_statistics']
            print(f"✅ Estadísticas de cámaras obtenidas - {len(camera_stats)} cámaras")
            
            # Verificar estructura de datos de cámaras
            if camera_stats:
                camera = camera_stats[0]
                required_fields = ['camera_id', 'camera_name', 'camera_ip', 'camera_line', 'status',
                                 'total_messages', 'processed_messages', 'error_messages', 
                                 'duplicate_messages', 'success_rate', 'total_vehicles_in', 
                                 'total_vehicles_out', 'last_message']
                missing_fields = [field for field in required_fields if field not in camera]
                
                if missing_fields:
                    print(f"⚠️ Campos faltantes en estadísticas de cámaras: {missing_fields}")
                else:
                    print("✅ Estructura de estadísticas de cámaras correcta")

def test_camera_status_monitoring():
    """Probar monitoreo de estado de cámaras"""
    print("\n📡 Probando monitoreo de estado de cámaras...")
    
    # Probar endpoint de estado de cámaras
    cameras_data = test_api_endpoint("/parking/1/cameras")
    if cameras_data and 'cameras' in cameras_data:
        cameras = cameras_data['cameras']
        print(f"✅ Estado de cámaras obtenido - {len(cameras)} cámaras")
        
        # Verificar campos de estado
        for camera in cameras:
            status_fields = ['status', 'ping_status', 'last_message_received', 'last_ping_check']
            missing_fields = [field for field in status_fields if field not in camera]
            
            if missing_fields:
                print(f"⚠️ Campos de estado faltantes en cámara {camera.get('name', 'N/A')}: {missing_fields}")
            else:
                print(f"✅ Cámara {camera.get('name', 'N/A')} - Estado: {camera.get('status')}, Ping: {camera.get('ping_status')}")

def test_duplicate_protection():
    """Probar protección contra duplicados"""
    print("\n🔄 Probando protección contra duplicados...")
    
    # Simular mensaje duplicado
    test_message = {
        "device": "TestCamera",
        "line": 1,
        "Vehicle In": 100,
        "Vehicle Out": 50,
        "event": "test",
        "time": datetime.now().isoformat()
    }
    
    # Enviar primer mensaje
    print("Enviando primer mensaje...")
    response1 = test_camera_endpoint("/camera", method="POST", data=test_message)
    
    # Enviar mensaje duplicado inmediatamente
    print("Enviando mensaje duplicado...")
    response2 = test_camera_endpoint("/camera", method="POST", data=test_message)
    
    if response1 and response2:
        print("✅ Mensajes enviados correctamente")
        print(f"Respuesta 1: {response1.get('status', 'unknown')}")
        print(f"Respuesta 2: {response2.get('status', 'unknown')}")
        
        # Verificar en logs si se detectó el duplicado
        time.sleep(2)  # Esperar a que se procesen los logs
        logs_data = test_api_endpoint("/camera/logs?limit=10")
        if logs_data and 'logs' in logs_data:
            logs = logs_data['logs']
            duplicate_logs = [log for log in logs if log.get('status') == 'duplicate']
            if duplicate_logs:
                print("✅ Duplicados detectados y registrados correctamente")
            else:
                print("⚠️ No se encontraron logs de duplicados")

def test_frontend_improvements():
    """Probar mejoras en el frontend"""
    print("\n🎨 Probando mejoras en el frontend...")
    
    # Verificar que el frontend está accesible
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend accesible")
        else:
            print(f"⚠️ Frontend no accesible - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accediendo al frontend: {e}")

def main():
    """Función principal de validación"""
    print("🚀 Iniciando validación de mejoras v2.3")
    print("=" * 50)
    
    # Verificar conectividad básica
    print("\n🔌 Verificando conectividad...")
    api_status = test_api_endpoint("/parkings")
    camera_status = test_camera_endpoint("/camera")
    
    if not api_status:
        print("❌ API no accesible - Abortando validación")
        return
    
    if not camera_status:
        print("⚠️ Servidor de cámaras no accesible - Algunas pruebas fallarán")
    
    # Ejecutar pruebas
    test_camera_logs_improvements()
    test_hourly_statistics()
    test_camera_status_monitoring()
    test_duplicate_protection()
    test_frontend_improvements()
    
    print("\n" + "=" * 50)
    print("✅ Validación de mejoras v2.3 completada")
    print("\n📋 Resumen de mejoras implementadas:")
    print("• Monitorización mejorada de mensajes de cámaras con contadores y cálculos")
    print("• Estadísticas por horas con gráficos de ocupación y actividad de cámaras")
    print("• Verificación periódica del estado de cámaras mediante ping")
    print("• Protección contra duplicados con correcciones en los conteos")
    print("• Visualización mejorada de logs con mensajes raw y detalles")

if __name__ == "__main__":
    main() 