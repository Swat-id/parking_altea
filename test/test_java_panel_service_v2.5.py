#!/usr/bin/env python3
"""
Script de prueba para el Java Panel Service v2.5
Prueba todos los endpoints disponibles
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5002/api/panels"
TIMEOUT = 10

def print_separator(title):
    """Imprime un separador con título"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_endpoint(method, endpoint, data=None, description=""):
    """Prueba un endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🔍 Probando: {description}")
    print(f"   URL: {method} {url}")
    
    if data:
        print(f"   Data: {json.dumps(data, indent=2)}")
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            print("   ❌ Método no soportado")
            return False
        
        response_time = (time.time() - start_time) * 1000
        
        print(f"   ⏱️  Tiempo de respuesta: {response_time:.2f}ms")
        print(f"   📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Respuesta: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            except json.JSONDecodeError:
                print(f"   ⚠️  Respuesta no es JSON válido: {response.text}")
                return False
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout después de {TIMEOUT}s")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Error de conexión - ¿Está el servicio ejecutándose?")
        return False
    except Exception as e:
        print(f"   💥 Error inesperado: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print_separator("PRUEBAS JAVA PANEL SERVICE v2.5")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    
    # Contador de pruebas
    total_tests = 0
    passed_tests = 0
    
    # 1. Health Check
    print_separator("1. HEALTH CHECK")
    total_tests += 1
    if test_endpoint("GET", "/health", description="Health Check del servicio"):
        passed_tests += 1
    
    # 2. Lista de Paneles
    print_separator("2. LISTA DE PANELES")
    total_tests += 1
    if test_endpoint("GET", "/list", description="Obtener lista de paneles disponibles"):
        passed_tests += 1
    
    # 3. Estado de Paneles
    print_separator("3. ESTADO DE PANELES")
    total_tests += 1
    if test_endpoint("GET", "/status", description="Obtener estado de la cache de paneles"):
        passed_tests += 1
    
    # 4. Colores Disponibles
    print_separator("4. COLORES DISPONIBLES")
    total_tests += 1
    if test_endpoint("GET", "/colors", description="Obtener colores disponibles"):
        passed_tests += 1
    
    # 5. Prueba de Panel Individual
    print_separator("5. PRUEBA DE PANEL INDIVIDUAL")
    test_data = {"ip": "172.20.5.50"}
    total_tests += 1
    if test_endpoint("POST", "/test", test_data, description="Probar conectividad con panel 172.20.5.50"):
        passed_tests += 1
    
    # 6. Envío de Mensaje Individual
    print_separator("6. ENVÍO DE MENSAJE INDIVIDUAL")
    message_data = {
        "panelIP": "172.20.5.50",
        "message": "PRUEBA TEST " + datetime.now().strftime("%H:%M:%S"),
        "color": 2,  # Verde
        "fontSize": 16,
        "windowNo": 0,
        "itemNum": 0,
        "effect": 0
    }
    total_tests += 1
    if test_endpoint("POST", "/send", message_data, description="Enviar mensaje a panel individual"):
        passed_tests += 1
    
    # 7. Envío de Mensaje Múltiple
    print_separator("7. ENVÍO DE MENSAJE MÚLTIPLE")
    multi_message_data = {
        "ips": ["172.20.5.50", "172.20.5.51"],
        "message": "MULTI TEST " + datetime.now().strftime("%H:%M:%S"),
        "color": 3,  # Amarillo
        "fontSize": 16,
        "windowNo": 0
    }
    total_tests += 1
    if test_endpoint("POST", "/send-multi", multi_message_data, description="Enviar mensaje a múltiples paneles"):
        passed_tests += 1
    
    # 8. Limpiar Cache
    print_separator("8. LIMPIAR CACHE")
    total_tests += 1
    if test_endpoint("POST", "/clear-cache", description="Limpiar cache de paneles"):
        passed_tests += 1
    
    # Resumen final
    print_separator("RESUMEN DE PRUEBAS")
    print(f"📊 Total de pruebas: {total_tests}")
    print(f"✅ Pruebas exitosas: {passed_tests}")
    print(f"❌ Pruebas fallidas: {total_tests - passed_tests}")
    print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} prueba(s) fallaron")
    
    print(f"\n⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 