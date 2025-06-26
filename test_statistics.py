#!/usr/bin/env python3
"""
Script para probar las nuevas funcionalidades de estadísticas
"""

import requests
import json
from datetime import datetime, timedelta
import time

# Configuración
BASE_URL = "http://157.180.91.63:5000"
TEST_USER_EMAIL = "toni@swat-id.com"
TEST_USER_PASSWORD = "admin123!"

def get_auth_token():
    """Obtener token de autenticación"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code == 200:
            return response.json()["token"]
        else:
            print(f"❌ Error de autenticación: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error obteniendo token: {e}")
        return None

def test_panels_endpoints(token):
    """Probar endpoints de paneles"""
    print("\n🔧 Probando endpoints de paneles...")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # GET /panels
    try:
        response = requests.get(f"{BASE_URL}/panels", headers=headers)
        if response.status_code == 200:
            panels = response.json()
            print(f"✅ GET /panels - {len(panels)} paneles encontrados")
            for panel in panels[:3]:  # Mostrar solo los primeros 3
                print(f"   - Panel {panel['id']}: {panel['name']} ({panel['ip_address']}) - {panel['status']}")
        else:
            print(f"❌ GET /panels - Error {response.status_code}")
    except Exception as e:
        print(f"❌ Error en GET /panels: {e}")
    
    # Probar con un panel específico si existe
    try:
        response = requests.get(f"{BASE_URL}/panels")
        if response.status_code == 200:
            panels = response.json()
            if panels:
                panel_id = panels[0]['id']
                
                # POST /panel/{id}/test
                test_response = requests.post(f"{BASE_URL}/panel/{panel_id}/test", headers=headers)
                if test_response.status_code == 200:
                    result = test_response.json()
                    print(f"✅ POST /panel/{panel_id}/test - {result['status']} (Response time: {result.get('response_time', 'N/A')}ms)")
                else:
                    print(f"❌ POST /panel/{panel_id}/test - Error {test_response.status_code}")
                
                # POST /panel/{id}/message
                message_response = requests.post(f"{BASE_URL}/panel/{panel_id}/message", 
                    json={"message": "PRUEBA ESTADÍSTICAS", "duration": 10}, headers=headers)
                if message_response.status_code == 200:
                    result = message_response.json()
                    print(f"✅ POST /panel/{panel_id}/message - {result['status']}")
                else:
                    print(f"❌ POST /panel/{panel_id}/message - Error {message_response.status_code}")
    except Exception as e:
        print(f"❌ Error probando paneles específicos: {e}")

def test_statistics_endpoints(token):
    """Probar endpoints de estadísticas"""
    print("\n📊 Probando endpoints de estadísticas...")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # GET /statistics
    try:
        response = requests.get(f"{BASE_URL}/statistics?days=7", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ GET /statistics - Estadísticas obtenidas para {len(stats.get('statistics', {}))} parkings")
        else:
            print(f"❌ GET /statistics - Error {response.status_code}")
    except Exception as e:
        print(f"❌ Error en GET /statistics: {e}")
    
    # Probar con un parking específico
    try:
        response = requests.get(f"{BASE_URL}/parkings")
        if response.status_code == 200:
            parkings = response.json()
            if parkings:
                parking_id = parkings[0]['id']
                
                # GET /parking/{id}/statistics
                stats_response = requests.get(f"{BASE_URL}/parking/{parking_id}/statistics?days=7", headers=headers)
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print(f"✅ GET /parking/{parking_id}/statistics - Estadísticas obtenidas")
                    if 'daily_stats' in stats:
                        print(f"   - {len(stats['daily_stats'])} días de estadísticas")
                    if 'hourly_stats' in stats:
                        print(f"   - {len(stats['hourly_stats'])} horas de estadísticas")
                else:
                    print(f"❌ GET /parking/{parking_id}/statistics - Error {stats_response.status_code}")
                
                # GET /parking/{id}/history
                history_response = requests.get(f"{BASE_URL}/parking/{parking_id}/history?limit=10", headers=headers)
                if history_response.status_code == 200:
                    history = history_response.json()
                    print(f"✅ GET /parking/{parking_id}/history - {len(history.get('history', []))} registros de historial")
                else:
                    print(f"❌ GET /parking/{parking_id}/history - Error {history_response.status_code}")
    except Exception as e:
        print(f"❌ Error probando estadísticas específicas: {e}")

def test_logs_endpoints(token):
    """Probar endpoints de logs"""
    print("\n📝 Probando endpoints de logs...")
    
    if not token:
        print("⚠️  Los endpoints de logs requieren autenticación")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # GET /logs/activity
    try:
        response = requests.get(f"{BASE_URL}/logs/activity?limit=10", headers=headers)
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ GET /logs/activity - {logs.get('total', 0)} logs de actividad")
        else:
            print(f"❌ GET /logs/activity - Error {response.status_code}")
    except Exception as e:
        print(f"❌ Error en GET /logs/activity: {e}")
    
    # GET /logs/panels
    try:
        response = requests.get(f"{BASE_URL}/logs/panels?limit=10", headers=headers)
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ GET /logs/panels - {logs.get('total', 0)} logs de paneles")
        else:
            print(f"❌ GET /logs/panels - Error {response.status_code}")
    except Exception as e:
        print(f"❌ Error en GET /logs/panels: {e}")

def test_database_tables():
    """Verificar que las nuevas tablas existen"""
    print("\n🗄️  Verificando nuevas tablas de base de datos...")
    
    # Intentar acceder a estadísticas para verificar que las tablas existen
    try:
        response = requests.get(f"{BASE_URL}/statistics?days=1")
        if response.status_code == 200:
            print("✅ Tablas de estadísticas funcionando correctamente")
        elif response.status_code == 404:
            print("⚠️  No hay datos de estadísticas disponibles (tablas vacías)")
        else:
            print(f"❌ Error accediendo a estadísticas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")

def main():
    """Función principal de pruebas"""
    print("🧪 Iniciando pruebas de nuevas funcionalidades de estadísticas")
    print("=" * 60)
    
    # Obtener token de autenticación
    token = get_auth_token()
    if token:
        print(f"✅ Autenticación exitosa - Token obtenido")
    else:
        print("⚠️  No se pudo obtener token de autenticación")
    
    # Probar endpoints
    test_panels_endpoints(token)
    test_statistics_endpoints(token)
    test_logs_endpoints(token)
    test_database_tables()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("\n📋 Resumen de nuevas funcionalidades:")
    print("  - Gestión de paneles con estado en tiempo real")
    print("  - Estadísticas por hora y día")
    print("  - Historial de ocupación detallado")
    print("  - Logs de actividad y mensajes de paneles")
    print("  - Nuevas tablas de base de datos para estadísticas")

if __name__ == "__main__":
    main() 