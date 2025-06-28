#!/usr/bin/env python3
"""
Script de prueba para comparar SendText vs SendTagText
"""

import requests
import json
import time
from datetime import datetime

# Configuración del servicio de paneles
PANEL_SERVICE_URL = "http://157.180.91.63:5001"

# Lista de paneles configurados (IPs reales de la base de datos)
PANELS = [
    {"ip": "172.20.17.50", "name": "PANEL C. ESPORTIVA", "parking": "P. Ciutat Esportiva"},
    {"ip": "172.20.5.50", "name": "PANEL BASSETA 1", "parking": "P. Poble antic 1"},
    {"ip": "172.20.5.51", "name": "PANEL BASSETA 2", "parking": "P. Poble antic 2"},
    {"ip": "172.20.8.50", "name": "PANEL PITERES", "parking": "P. Poble antic 3"},
    {"ip": "172.20.4.50", "name": "PANEL PALAU", "parking": "P. Poble antic 4"},
    {"ip": "172.20.4.51", "name": "PANEL COCOLISO", "parking": "P. Poble antic 5"},
    {"ip": "172.20.4.52", "name": "BELLES ARTS 2", "parking": "P. Port Altea"},
    {"ip": "172.20.4.53", "name": "BELLES ARTS", "parking": "P. Estació Altea"},
    {"ip": "172.20.2.50", "name": "PANEL RENFE", "parking": "P. Altea Hills"},
    {"ip": "172.20.1.50", "name": "PANEL ALTEA VELLA", "parking": "P. Ciutat Esportiva"}
]

def test_panel_service():
    """Prueba la conectividad del servicio de paneles"""
    try:
        response = requests.get(f"{PANEL_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servicio de paneles funcionando correctamente")
            return True
        else:
            print(f"❌ Servicio de paneles respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio de paneles: {e}")
        return False

def send_message_to_panel(panel_ip, message, function_type="send"):
    """Envía un mensaje a un panel específico"""
    try:
        payload = {
            "panelIP": panel_ip,
            "message": message,
            "color": 3000,  # Color por defecto del fabricante
            "fontSize": 16,
            "speed": 3,
            "effect": 0,
            "stayTime": 3,  # Según ejemplo del fabricante
            "alignment": 0
        }
        
        # Usar endpoint diferente según el tipo de función
        endpoint = "/api/panel/send" if function_type == "send" else "/api/panel/static"
        
        response = requests.post(
            f"{PANEL_SERVICE_URL}{endpoint}",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"❌ Error enviando mensaje a {panel_ip}: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Excepción enviando mensaje a {panel_ip}: {e}")
        return None

def test_both_functions():
    """Prueba ambas funciones SendText y SendTagText"""
    print(f"\n🚀 Iniciando prueba comparativa SendText vs SendTagText - {datetime.now()}")
    print("=" * 80)
    
    # Verificar servicio primero
    if not test_panel_service():
        return
    
    # Probar solo con 3 paneles para comparar
    test_panels = PANELS[:3]
    
    for i, panel in enumerate(test_panels, 1):
        panel_ip = panel["ip"]
        panel_name = panel["name"]
        parking_name = panel["parking"]
        
        print(f"\n📺 Panel {i}: {panel_name} ({panel_ip})")
        print(f"   Parking: {parking_name}")
        
        # Mensaje de prueba
        message = f"TEST {panel_ip}"
        
        print(f"   Enviando: '{message}'")
        
        # PRUEBA 1: SendText
        print(f"   🔄 Probando SendText...")
        result1 = send_message_to_panel(panel_ip, message, "send")
        
        if result1:
            success1 = result1.get("success", False)
            response_time1 = result1.get("responseTime", 0)
            error_code1 = result1.get("errorCode", -1)
            
            if success1:
                print(f"      ✅ SendText - Éxito - Tiempo: {response_time1}ms")
            else:
                print(f"      ❌ SendText - Fallo - Código: {error_code1}")
        else:
            print(f"      ❌ SendText - Sin respuesta")
        
        # Pausa entre funciones
        time.sleep(3)
        
        # PRUEBA 2: SendTagText (usando endpoint static)
        print(f"   🔄 Probando SendTagText...")
        result2 = send_message_to_panel(panel_ip, message, "static")
        
        if result2:
            success2 = result2.get("success", False)
            response_time2 = result2.get("responseTime", 0)
            error_code2 = result2.get("errorCode", -1)
            
            if success2:
                print(f"      ✅ SendTagText - Éxito - Tiempo: {response_time2}ms")
            else:
                print(f"      ❌ SendTagText - Fallo - Código: {error_code2}")
        else:
            print(f"      ❌ SendTagText - Sin respuesta")
        
        # Pausa entre paneles
        time.sleep(5)
    
    print(f"\n📊 RESUMEN DE PRUEBA COMPARATIVA")
    print("=" * 80)
    print("✅ Prueba completada. Revisa los logs del servicio para ver los códigos de retorno.")
    print("🔍 Verifica físicamente los paneles para ver cuál función muestra el texto.")

if __name__ == "__main__":
    test_both_functions() 