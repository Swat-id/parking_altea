#!/usr/bin/env python3
"""
Test del flujo correcto de comunicación con paneles según el manual del fabricante
Verifica el uso correcto de initNetwork, setListener y sendMulti
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración del servicio
BASE_URL = "http://localhost:5002/api"
TIMEOUT = 10

# Panel de prueba según la documentación
TEST_PANEL_IP = "172.20.4.52"  # BELLES ARTS 2
TEST_PANEL_PORT = 5200  # Puerto por defecto según documentación

def log(message):
    """Función de logging con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_init_network():
    """Prueba la inicialización de red (initNetwork) según el manual"""
    log("🌐 Probando initNetwork con parámetros por defecto...")
    
    init_data = {
        "panelIP": TEST_PANEL_IP,
        "port": TEST_PANEL_PORT,
        "idCode": "255.255.255.255",  # Código de identificación por defecto
        "timeout": 3000  # Timeout por defecto en ms
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/init-network",
            json=init_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            log(f"✅ initNetwork exitoso: {data.get('message', 'OK')}")
            return True
        else:
            log(f"❌ initNetwork falló: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error en initNetwork: {e}")
        return False

def test_set_listener():
    """Prueba la configuración del listener (setListener) según el manual"""
    log("👂 Probando setListener...")
    
    listener_data = {
        "panelIP": TEST_PANEL_IP,
        "enableListener": True,
        "callbackPort": 5001  # Puerto para callbacks
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/set-listener",
            json=listener_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            log(f"✅ setListener exitoso: {data.get('message', 'OK')}")
            return True
        else:
            log(f"❌ setListener falló: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error en setListener: {e}")
        return False

def test_send_multi():
    """Prueba el envío de mensaje usando sendMulti según el manual"""
    log("📤 Probando sendMulti con parámetros correctos...")
    
    # Datos para sendMulti según la documentación
    send_multi_data = {
        "panelIP": TEST_PANEL_IP,
        "itemNum": 0,  # Número de ventana (0-7)
        "texts": ["TEST SENDMULTI - " + datetime.now().strftime('%H:%M:%S')],
        "colors": [2],  # Verde (formato del panel: 1=red, 2=green, 3=yellow, etc.)
        "fontSizes": [16],
        "showEffects": [0]  # Sin efecto
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/send-multi",
            json=send_multi_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            response_time = data.get('responseTime', 0)
            log(f"✅ sendMulti exitoso en {response_time}ms: {data.get('message', 'OK')}")
            return True
        else:
            log(f"❌ sendMulti falló: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error en sendMulti: {e}")
        return False

def test_complete_flow():
    """Prueba el flujo completo: initNetwork -> setListener -> sendMulti"""
    log("🔄 Probando flujo completo según el manual del fabricante...")
    
    # Paso 1: initNetwork
    log("\n=== PASO 1: initNetwork ===")
    if not test_init_network():
        log("❌ Flujo falló en initNetwork")
        return False
    
    # Esperar un momento para que se establezca la conexión
    time.sleep(1)
    
    # Paso 2: setListener
    log("\n=== PASO 2: setListener ===")
    if not test_set_listener():
        log("❌ Flujo falló en setListener")
        return False
    
    # Esperar un momento para que se configure el listener
    time.sleep(1)
    
    # Paso 3: sendMulti
    log("\n=== PASO 3: sendMulti ===")
    if not test_send_multi():
        log("❌ Flujo falló en sendMulti")
        return False
    
    log("\n✅ Flujo completo ejecutado correctamente")
    return True

def test_manual_parameters():
    """Prueba con los parámetros exactos del manual"""
    log("📖 Probando con parámetros exactos del manual...")
    
    # Parámetros según el manual del fabricante
    manual_data = {
        "panelIP": TEST_PANEL_IP,
        "port": 5000,  # Puerto por defecto según documentación
        "idCode": "255.255.255.255",
        "timeout": 600,  # Timeout por defecto
        "cardId": 1,  # ID del panel
        "windowNo": 0,  # Número de ventana
        "message": "MANUAL TEST - " + datetime.now().strftime('%H:%M:%S'),
        "color": 2,  # Verde en formato del panel
        "fontSize": 16,
        "speed": 3,
        "effect": 0,
        "stayTime": 5,
        "alignment": 1  # Centro
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/send-manual",
            json=manual_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            response_time = data.get('responseTime', 0)
            log(f"✅ Envío con parámetros del manual exitoso en {response_time}ms")
            return True
        else:
            log(f"❌ Error con parámetros del manual: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error con parámetros del manual: {e}")
        return False

def test_panel_status():
    """Verifica el estado del panel después del flujo"""
    log("📊 Verificando estado del panel...")
    
    try:
        response = requests.get(f"{BASE_URL}/panel/status", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            initialized_panels = data.get('data', {}).get('initializedPanels', {})
            
            if TEST_PANEL_IP in initialized_panels:
                status = initialized_panels[TEST_PANEL_IP]
                log(f"✅ Panel {TEST_PANEL_IP} está {'inicializado' if status else 'no inicializado'}")
                return status
            else:
                log(f"⚠️ Panel {TEST_PANEL_IP} no aparece en la lista de paneles")
                return False
        else:
            log(f"❌ Error al obtener estado: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al obtener estado: {e}")
        return False

def main():
    """Función principal"""
    log("🚀 Iniciando test del flujo correcto según el manual del fabricante")
    log(f"Panel de prueba: {TEST_PANEL_IP}:{TEST_PANEL_PORT}")
    
    # Verificar que el servicio esté disponible
    try:
        health_response = requests.get(f"{BASE_URL}/panel/health", timeout=5)
        if health_response.status_code != 200:
            log("❌ El servicio Java no está disponible")
            sys.exit(1)
        log("✅ Servicio Java disponible")
    except:
        log("❌ No se puede conectar al servicio Java")
        sys.exit(1)
    
    # Ejecutar tests
    success_count = 0
    total_tests = 0
    
    # Test 1: Flujo completo
    total_tests += 1
    if test_complete_flow():
        success_count += 1
    
    # Test 2: Parámetros del manual
    total_tests += 1
    if test_manual_parameters():
        success_count += 1
    
    # Test 3: Verificar estado
    total_tests += 1
    if test_panel_status():
        success_count += 1
    
    # Resumen
    log(f"\n📋 RESUMEN: {success_count}/{total_tests} tests exitosos")
    
    if success_count == total_tests:
        log("🎉 Todos los tests pasaron correctamente")
        sys.exit(0)
    else:
        log("⚠️ Algunos tests fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main() 