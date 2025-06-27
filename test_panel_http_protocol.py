#!/usr/bin/env python3
"""
Test Panel HTTP Protocol - Protocolo HTTP correcto para paneles
Usa HTTP POST a /update con JSON como está configurado en el sistema
"""

import requests
import time
import subprocess
import platform
from typing import Dict, List, Optional
import json

# Configuración de paneles desde la base de datos
PANELS = [
    {"id": 1, "name": "PANEL C. ESPORTIVA", "ip": "172.20.17.50", "parking": "1 - P. Ciutat Esportiva"},
    {"id": 2, "name": "PANEL BASSETA 1", "ip": "172.20.5.50", "parking": "2 - P. Basseta Centre"},
    {"id": 3, "name": "PANEL BASSETA 2", "ip": "172.20.5.51", "parking": "2 - P. Basseta Centre"},
    {"id": 4, "name": "PANEL PITERES", "ip": "172.20.8.50", "parking": "6 - P. Poble antic/Conservatori"},
    {"id": 5, "name": "PANEL PALAU", "ip": "172.20.4.50", "parking": "5 - P. Poble antic/Palau Altea"},
    {"id": 6, "name": "PANEL COCOLISO", "ip": "172.20.4.51", "parking": "5 - P. Poble antic/Palau Altea"},
    {"id": 7, "name": "BELLES ARTS 2", "ip": "172.20.4.52", "parking": "4 - P. Poble antic/Belles Arts 2"},
    {"id": 8, "name": "BELLES ARTS", "ip": "172.20.4.53", "parking": "3 - P. Poble antic/Belles Arts 1"},
    {"id": 9, "name": "PANEL RENFE", "ip": "172.20.2.50", "parking": "8 - P. Estació Altea"},
    {"id": 10, "name": "PANEL ALTEA VELLA", "ip": "172.20.1.50", "parking": "9 - P. Altea la Vella"}
]

def ping_panel(panel_ip: str) -> bool:
    """Hacer ping a un panel"""
    try:
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", panel_ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", panel_ip]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception as e:
        print(f"Error haciendo ping a {panel_ip}: {e}")
        return False

def test_http_endpoint(panel: Dict, endpoint: str, payload: Dict) -> Dict:
    """Testear endpoint HTTP específico"""
    results = {
        'endpoint': endpoint,
        'status': False,
        'response_code': None,
        'response_time': None,
        'response_text': None,
        'error': None
    }
    
    try:
        url = f"http://{panel['ip']}{endpoint}"
        print(f"   Probando: {url}")
        print(f"   Payload: {payload}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=5)
        response_time = time.time() - start_time
        
        results['status'] = response.status_code == 200
        results['response_code'] = response.status_code
        results['response_time'] = response_time
        results['response_text'] = response.text
        
        print(f"   Respuesta: {response.status_code} - {response.text}")
        print(f"   Tiempo: {response_time:.3f}s")
        print(f"   Estado: {'✅ OK' if results['status'] else '❌ FAIL'}")
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Conexión rechazada: {e}"
        results['error'] = error_msg
        print(f"   ❌ {error_msg}")
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout: {e}"
        results['error'] = error_msg
        print(f"   ❌ {error_msg}")
    except Exception as e:
        error_msg = f"Error: {e}"
        results['error'] = error_msg
        print(f"   ❌ {error_msg}")
    
    return results

def test_panel_http_protocol(panel: Dict) -> Dict:
    """Testear protocolo HTTP en un panel"""
    print(f"\n=== Testeando HTTP Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'parking': panel['parking'],
        'ping_status': False,
        'http_tests': [],
        'errors': []
    }
    
    # 1. Test ping
    print(f"1. Verificando conectividad...")
    results['ping_status'] = ping_panel(panel['ip'])
    print(f"   Ping: {'✅ OK' if results['ping_status'] else '❌ FAIL'}")
    
    if not results['ping_status']:
        results['errors'].append("Panel no responde al ping")
        return results
    
    # 2. Test HTTP endpoints
    print(f"2. Probando endpoints HTTP...")
    
    # Test 1: Endpoint /update con mensaje simple
    print(f"\n   Test 1: Endpoint /update")
    payload1 = {"message": f"TEST PANEL {panel['id']}: {panel['ip']}"}
    test1 = test_http_endpoint(panel, "/update", payload1)
    results['http_tests'].append(test1)
    
    # Test 2: Endpoint /update con formato del sistema
    print(f"\n   Test 2: Formato del sistema")
    payload2 = {"message": f"{panel['parking']}: 100 libres (LLIURE)"}
    test2 = test_http_endpoint(panel, "/update", payload2)
    results['http_tests'].append(test2)
    
    # Test 3: Endpoint /update con mensaje en catalán
    print(f"\n   Test 3: Mensaje en catalán")
    payload3 = {"message": f"PARKING {panel['id']}: LLIURE"}
    test3 = test_http_endpoint(panel, "/update", payload3)
    results['http_tests'].append(test3)
    
    # Test 4: Endpoint raíz
    print(f"\n   Test 4: Endpoint raíz /")
    payload4 = {"message": f"ROOT TEST: {panel['ip']}"}
    test4 = test_http_endpoint(panel, "/", payload4)
    results['http_tests'].append(test4)
    
    # Test 5: Endpoint /message
    print(f"\n   Test 5: Endpoint /message")
    payload5 = {"message": f"MESSAGE TEST: {panel['ip']}"}
    test5 = test_http_endpoint(panel, "/message", payload5)
    results['http_tests'].append(test5)
    
    # Test 6: Endpoint /panel
    print(f"\n   Test 6: Endpoint /panel")
    payload6 = {"message": f"PANEL TEST: {panel['ip']}"}
    test6 = test_http_endpoint(panel, "/panel", payload6)
    results['http_tests'].append(test6)
    
    # Test 7: GET request a /update
    print(f"\n   Test 7: GET request a /update")
    try:
        url = f"http://{panel['ip']}/update"
        start_time = time.time()
        response = requests.get(url, timeout=5)
        response_time = time.time() - start_time
        
        test7 = {
            'endpoint': '/update (GET)',
            'status': response.status_code == 200,
            'response_code': response.status_code,
            'response_time': response_time,
            'response_text': response.text,
            'error': None
        }
        print(f"   GET {url}: {response.status_code} - {response.text}")
        print(f"   Tiempo: {response_time:.3f}s")
        print(f"   Estado: {'✅ OK' if test7['status'] else '❌ FAIL'}")
        results['http_tests'].append(test7)
        
    except Exception as e:
        test7 = {
            'endpoint': '/update (GET)',
            'status': False,
            'response_code': None,
            'response_time': None,
            'response_text': None,
            'error': str(e)
        }
        print(f"   ❌ Error GET: {e}")
        results['http_tests'].append(test7)
    
    return results

def test_alternative_ports(panel: Dict) -> Dict:
    """Testear puertos alternativos"""
    print(f"\n=== Testeando Puertos Alternativos Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'port_tests': []
    }
    
    # Puertos comunes para probar
    ports = [80, 8080, 5000, 3000, 8000, 8888]
    
    for port in ports:
        test_result = {
            'port': port,
            'status': False,
            'response_code': None,
            'response_time': None,
            'error': None
        }
        
        try:
            url = f"http://{panel['ip']}:{port}/update"
            payload = {"message": f"PORT {port} TEST: {panel['ip']}"}
            
            print(f"   Probando puerto {port}: {url}")
            
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=3)
            response_time = time.time() - start_time
            
            test_result['status'] = response.status_code == 200
            test_result['response_code'] = response.status_code
            test_result['response_time'] = response_time
            
            print(f"   Respuesta: {response.status_code} - {response.text}")
            print(f"   Tiempo: {response_time:.3f}s")
            print(f"   Estado: {'✅ OK' if test_result['status'] else '❌ FAIL'}")
            
        except requests.exceptions.ConnectionError:
            test_result['error'] = "Conexión rechazada"
            print(f"   ❌ Conexión rechazada")
        except requests.exceptions.Timeout:
            test_result['error'] = "Timeout"
            print(f"   ❌ Timeout")
        except Exception as e:
            test_result['error'] = str(e)
            print(f"   ❌ Error: {e}")
        
        results['port_tests'].append(test_result)
    
    return results

def main():
    """Función principal"""
    print("🚦 TESTEANDO PROTOCOLO HTTP PARA PANELES")
    print("=" * 60)
    print("Este test usa el protocolo HTTP correcto configurado en el sistema")
    print("HTTP POST a /update con JSON como está documentado.")
    print("=" * 60)
    
    all_results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'panels': []
    }
    
    for panel in PANELS:
        print(f"\n{'='*60}")
        print(f"PANEL {panel['id']}: {panel['name']}")
        print(f"IP: {panel['ip']} | Parking: {panel['parking']}")
        print(f"{'='*60}")
        
        panel_results = {
            'panel_info': panel,
            'http_test': test_panel_http_protocol(panel),
            'port_test': test_alternative_ports(panel)
        }
        
        all_results['panels'].append(panel_results)
        
        # Resumen del panel
        print(f"\n📊 RESUMEN PANEL {panel['id']}:")
        print(f"   Ping: {'✅' if panel_results['http_test']['ping_status'] else '❌'}")
        
        successful_tests = sum(1 for test in panel_results['http_test']['http_tests'] if test['status'])
        total_tests = len(panel_results['http_test']['http_tests'])
        print(f"   HTTP Tests: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        
        successful_ports = sum(1 for test in panel_results['port_test']['port_tests'] if test['status'])
        total_ports = len(panel_results['port_test']['port_tests'])
        print(f"   Port Tests: {successful_ports}/{total_ports} ({successful_ports/total_ports*100:.1f}%)")
        
        # Mostrar endpoints exitosos
        if successful_tests > 0:
            print(f"   ✅ Endpoints exitosos:")
            for test in panel_results['http_test']['http_tests']:
                if test['status']:
                    print(f"      - {test['endpoint']}")
        
        if successful_ports > 0:
            print(f"   ✅ Puertos exitosos:")
            for test in panel_results['port_test']['port_tests']:
                if test['status']:
                    print(f"      - Puerto {test['port']}")
    
    # Resumen general
    print(f"\n{'='*60}")
    print("📊 RESUMEN GENERAL")
    print(f"{'='*60}")
    
    total_panels = len(PANELS)
    ping_ok = sum(1 for p in all_results['panels'] if p['http_test']['ping_status'])
    
    total_http_tests = sum(len(p['http_test']['http_tests']) for p in all_results['panels'])
    successful_http_tests = sum(
        sum(1 for test in p['http_test']['http_tests'] if test['status'])
        for p in all_results['panels']
    )
    
    total_port_tests = sum(len(p['port_test']['port_tests']) for p in all_results['panels'])
    successful_port_tests = sum(
        sum(1 for test in p['port_test']['port_tests'] if test['status'])
        for p in all_results['panels']
    )
    
    print(f"Total paneles: {total_panels}")
    print(f"Ping OK: {ping_ok}/{total_panels} ({ping_ok/total_panels*100:.1f}%)")
    print(f"HTTP Tests OK: {successful_http_tests}/{total_http_tests} ({successful_http_tests/total_http_tests*100:.1f}%)")
    print(f"Port Tests OK: {successful_port_tests}/{total_port_tests} ({successful_port_tests/total_port_tests*100:.1f}%)")
    
    # Guardar resultados
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"panel_http_protocol_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filename}")
    
    # Instrucciones finales
    print(f"\n📋 INSTRUCCIONES PARA VALIDACIÓN:")
    print(f"1. Verificar físicamente cada panel")
    print(f"2. Confirmar que se muestran los mensajes HTTP")
    print(f"3. Si los mensajes se ven correctamente, proceder con implementación")
    print(f"4. Si no se ven, revisar configuración de paneles")
    
    if successful_http_tests > 0:
        print(f"\n✅ ÉXITO: Algunos paneles respondieron a HTTP")
        print(f"   - Proceder con implementación de mensajes HTTP")
        print(f"   - Implementar comunicación HTTP en backend")
    else:
        print(f"\n⚠️  ADVERTENCIA: Ningún panel respondió a HTTP")
        print(f"   - Los paneles pueden usar un protocolo diferente")
        print(f"   - Revisar documentación específica de los paneles")

if __name__ == "__main__":
    main() 