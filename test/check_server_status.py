#!/usr/bin/env python3
"""
Script para verificar el estado del servidor y gestionar las respuestas
"""

import requests
import json
from datetime import datetime

# Configuración del servidor
SERVER_BASE = "http://157.180.91.63"
API_PORT = 6001
FRONTEND_PORT = 5789

def check_endpoint(url, description):
    """Verificar un endpoint específico"""
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ {description}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def check_api_endpoints():
    """Verificar todos los endpoints del API"""
    print("\n=== VERIFICACIÓN DE ENDPOINTS DEL API ===")
    
    endpoints = [
        (f"{SERVER_BASE}:{API_PORT}/parkings", "Lista de parkings"),
        (f"{SERVER_BASE}:{API_PORT}/statistics", "Estadísticas generales"),
        (f"{SERVER_BASE}:{API_PORT}/cameras/status", "Estado de cámaras"),
        (f"{SERVER_BASE}:{API_PORT}/panels", "Lista de paneles"),
        (f"{SERVER_BASE}:{API_PORT}/camera/logs", "Logs de cámaras"),
    ]
    
    results = []
    for url, desc in endpoints:
        success = check_endpoint(url, desc)
        results.append((desc, success))
    
    return results

def check_frontend():
    """Verificar el frontend"""
    print("\n=== VERIFICACIÓN DEL FRONTEND ===")
    return check_endpoint(f"{SERVER_BASE}:{FRONTEND_PORT}", "Frontend React")

def get_parking_details():
    """Obtener detalles de los parkings"""
    try:
        response = requests.get(f"{SERVER_BASE}:{API_PORT}/parkings", timeout=10)
        if response.status_code == 200:
            parkings = response.json()
            print(f"\n=== ESTADO DE PARKINGS ({len(parkings)} total) ===")
            
            for parking in parkings:
                print(f"🅿️  {parking['name']}")
                print(f"   Estado: {parking['estado']}")
                print(f"   Ocupadas: {parking['plazas_ocupadas']}/{parking['total_plazas']}")
                print(f"   Libres: {parking['plazas_libres']}")
                print()
            
            return parkings
    except Exception as e:
        print(f"❌ Error obteniendo detalles de parkings: {e}")
        return []

def get_camera_status():
    """Obtener estado de las cámaras"""
    try:
        response = requests.get(f"{SERVER_BASE}:{API_PORT}/cameras/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"\n=== ESTADO DE CÁMARAS ({len(cameras)} total) ===")
            
            for camera in cameras:
                status = "🟢 Activa" if camera.get('is_active') else "🔴 Inactiva"
                print(f"📷 {camera['name']} ({camera['ip']}) - {status}")
                if camera.get('last_message_received'):
                    print(f"   Último mensaje: {camera['last_message_received']}")
                print()
            
            return cameras
    except Exception as e:
        print(f"❌ Error obteniendo estado de cámaras: {e}")
        return []

def get_recent_camera_logs():
    """Obtener logs recientes de cámaras"""
    try:
        response = requests.get(f"{SERVER_BASE}:{API_PORT}/camera/logs?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            print(f"\n=== LOGS RECIENTES DE CÁMARAS ({len(logs)} últimos) ===")
            
            for log in logs:
                timestamp = log.get('timestamp', 'N/A')
                camera = log.get('camera_name', 'N/A')
                delta_in = log.get('delta_in', 0)
                delta_out = log.get('delta_out', 0)
                occupancy = log.get('new_occupancy', 0)
                
                print(f"📝 {timestamp} - {camera}")
                print(f"   Entrada: +{delta_in}, Salida: -{delta_out}, Ocupación: {occupancy}")
                if log.get('error_message'):
                    print(f"   ⚠️  Error: {log['error_message']}")
                print()
            
            return logs
    except Exception as e:
        print(f"❌ Error obteniendo logs de cámaras: {e}")
        return []

def main():
    """Función principal"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA DE PARKING ALTEA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar endpoints
    api_results = check_api_endpoints()
    frontend_ok = check_frontend()
    
    # Obtener detalles
    parkings = get_parking_details()
    cameras = get_camera_status()
    logs = get_recent_camera_logs()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL ESTADO DEL SISTEMA")
    print("=" * 60)
    
    api_success = sum(1 for _, success in api_results if success)
    print(f"✅ API Endpoints: {api_success}/{len(api_results)} funcionando")
    print(f"✅ Frontend: {'Funcionando' if frontend_ok else 'Error'}")
    print(f"✅ Parkings: {len(parkings)} configurados")
    print(f"✅ Cámaras: {len(cameras)} configuradas")
    print(f"✅ Logs recientes: {len(logs)} entradas")
    
    # Verificar si hay problemas
    if api_success < len(api_results):
        print("\n⚠️  PROBLEMAS DETECTADOS:")
        for desc, success in api_results:
            if not success:
                print(f"   - {desc}: No responde")
    
    if not frontend_ok:
        print("\n⚠️  PROBLEMAS DETECTADOS:")
        print("   - Frontend: No accesible")
    
    print("\n🎯 SISTEMA LISTO PARA PRODUCCIÓN" if api_success == len(api_results) and frontend_ok else "\n🔧 SE REQUIEREN CORRECCIONES")

if __name__ == "__main__":
    main() 