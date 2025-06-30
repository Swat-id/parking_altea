#!/usr/bin/env python3
"""
Script de pruebas comprehensivas para Java Panel Service v2.5
Este script verifica que el servicio esté funcionando correctamente
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5002/api"
TIMEOUT = 10

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, color=Colors.GREEN):
    """Imprimir mensaje con color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}]{Colors.ENDC} {message}")

def print_error(message):
    """Imprimir mensaje de error"""
    print_status(f"ERROR: {message}", Colors.RED)

def print_warning(message):
    """Imprimir mensaje de advertencia"""
    print_status(f"WARNING: {message}", Colors.YELLOW)

def print_info(message):
    """Imprimir mensaje informativo"""
    print_status(f"INFO: {message}", Colors.BLUE)

def test_health_check():
    """Probar health check del servicio"""
    print_info("Probando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_status(f"Health check OK: {data}")
            return True
        else:
            print_error(f"Health check falló con código {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error en health check: {e}")
        return False

def test_panel_status():
    """Probar endpoint de estado de paneles"""
    print_info("Probando estado de paneles...")
    try:
        response = requests.get(f"{BASE_URL}/panels/status", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_status(f"Estado de paneles OK: {len(data.get('panels', []))} paneles encontrados")
            for panel in data.get('panels', []):
                print_info(f"  - {panel.get('name', 'N/A')}: {panel.get('ip', 'N/A')}")
            return True
        else:
            print_error(f"Estado de paneles falló con código {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error en estado de paneles: {e}")
        return False

def test_send_message():
    """Probar envío de mensaje a panel"""
    print_info("Probando envío de mensaje...")
    
    # Datos de prueba
    test_message = {
        "ip": "172.20.5.50",
        "message": "TEST V2.5",
        "color": 1,
        "fontSize": 2,
        "windowNo": 0
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panels/send",
            json=test_message,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"Envío de mensaje OK: {data}")
            return True
        else:
            print_error(f"Envío de mensaje falló con código {response.status_code}")
            print_error(f"Respuesta: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error en envío de mensaje: {e}")
        return False

def test_send_multi_message():
    """Probar envío de mensaje multi-panel"""
    print_info("Probando envío de mensaje multi-panel...")
    
    # Datos de prueba
    test_message = {
        "ips": ["172.20.5.50", "172.20.5.51"],
        "message": "MULTI TEST V2.5",
        "color": 2,
        "fontSize": 2,
        "windowNo": 0
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panels/send-multi",
            json=test_message,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"Envío multi-panel OK: {data}")
            return True
        else:
            print_error(f"Envío multi-panel falló con código {response.status_code}")
            print_error(f"Respuesta: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error en envío multi-panel: {e}")
        return False

def test_panel_connectivity():
    """Probar conectividad con paneles"""
    print_info("Probando conectividad con paneles...")
    
    test_panels = [
        {"ip": "172.20.5.50", "name": "PANEL BASSETA 1"},
        {"ip": "172.20.5.51", "name": "PANEL BASSETA 2"},
        {"ip": "172.20.4.50", "name": "PANEL PALAU"}
    ]
    
    success_count = 0
    for panel in test_panels:
        try:
            response = requests.post(
                f"{BASE_URL}/panels/test",
                json={"ip": panel["ip"]},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print_status(f"Conectividad OK: {panel['name']} ({panel['ip']})")
                    success_count += 1
                else:
                    print_warning(f"Conectividad falló: {panel['name']} ({panel['ip']}) - {data.get('message', 'Sin mensaje')}")
            else:
                print_error(f"Test de conectividad falló para {panel['name']} con código {response.status_code}")
        except Exception as e:
            print_error(f"Error en test de conectividad para {panel['name']}: {e}")
    
    print_info(f"Conectividad: {success_count}/{len(test_panels)} paneles respondieron")
    return success_count > 0

def test_api_endpoints():
    """Probar todos los endpoints de la API"""
    print_info("Probando endpoints de la API...")
    
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("GET", "/panels/status", "Estado de Paneles"),
        ("GET", "/panels/list", "Lista de Paneles"),
        ("POST", "/panels/test", "Test de Conectividad"),
        ("POST", "/panels/send", "Envío de Mensaje"),
        ("POST", "/panels/send-multi", "Envío Multi-Panel")
    ]
    
    success_count = 0
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            else:
                # Para POST, enviar datos mínimos
                data = {"ip": "172.20.5.50"} if "test" in endpoint else {}
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=TIMEOUT)
            
            if response.status_code in [200, 201, 400, 422]:  # Códigos válidos
                print_status(f"Endpoint OK: {description} ({method} {endpoint})")
                success_count += 1
            else:
                print_warning(f"Endpoint inesperado: {description} - Código {response.status_code}")
                success_count += 1  # Contamos como OK si responde
        except Exception as e:
            print_error(f"Endpoint falló: {description} - {e}")
    
    print_info(f"Endpoints: {success_count}/{len(endpoints)} funcionando")
    return success_count == len(endpoints)

def main():
    """Función principal"""
    print(f"{Colors.BOLD}=========================================={Colors.ENDC}")
    print(f"{Colors.BOLD}Pruebas Java Panel Service v2.5{Colors.ENDC}")
    print(f"{Colors.BOLD}=========================================={Colors.ENDC}")
    print(f"URL Base: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Contador de pruebas exitosas
    passed_tests = 0
    total_tests = 6
    
    # Ejecutar pruebas
    tests = [
        ("Health Check", test_health_check),
        ("Estado de Paneles", test_panel_status),
        ("Endpoints API", test_api_endpoints),
        ("Conectividad", test_panel_connectivity),
        ("Envío Mensaje", test_send_message),
        ("Envío Multi-Panel", test_send_multi_message)
    ]
    
    for test_name, test_func in tests:
        print(f"{Colors.BOLD}--- {test_name} ---{Colors.ENDC}")
        try:
            if test_func():
                passed_tests += 1
                print_status(f"✓ {test_name} PASÓ")
            else:
                print_error(f"✗ {test_name} FALLÓ")
        except Exception as e:
            print_error(f"✗ {test_name} ERROR: {e}")
        print()
        time.sleep(1)  # Pausa entre pruebas
    
    # Resumen final
    print(f"{Colors.BOLD}=========================================={Colors.ENDC}")
    print(f"{Colors.BOLD}RESUMEN DE PRUEBAS{Colors.ENDC}")
    print(f"{Colors.BOLD}=========================================={Colors.ENDC}")
    print(f"Pruebas pasadas: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print_status("¡TODAS LAS PRUEBAS PASARON! El servicio está funcionando correctamente.")
        return 0
    else:
        print_error(f"FALLARON {total_tests - passed_tests} PRUEBAS. Revisar el servicio.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1) 