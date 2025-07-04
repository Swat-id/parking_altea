#!/usr/bin/env python3
"""
Script de prueba para verificar el mapeo correcto de fontSize y colors
según el protocolo del fabricante
"""

import requests
import json
import time
from datetime import datetime

def test_protocol_mapping():
    """Probar el mapeo correcto de parámetros según protocolo"""
    
    print("🔍 PRUEBA DE MAPEO DE PROTOCOLO")
    print("=" * 60)
    
    # Configuración
    panel_ip = "172.20.4.52"  # BELLES ARTS 2
    java_api_url = "http://127.0.0.1:5656/sendMulti"
    
    # Test 1: Verificar que el servicio Java está respondiendo
    print(f"\n1️⃣ Verificando servicio Java en puerto 5656...")
    try:
        response = requests.get("http://127.0.0.1:5656/health", timeout=5)
        print(f"   ✅ Servicio respondiendo: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error conectando al servicio: {e}")
        return False
    
    # Test 2: Probar mapeo de fontSize 16 -> valor 2
    print(f"\n2️⃣ Probando mapeo fontSize 16 -> valor 2...")
    
    payload_font16 = {
        "ip": panel_ip,
        "itemNum": 1,
        "texts": ["FONT 16 TEST"],
        "colors": [1],  # Rojo
        "fontSizes": [16],  # Debe mapearse a valor 2
        "showEffects": [1]
    }
    
    print(f"   📤 Payload: {json.dumps(payload_font16, indent=2)}")
    
    try:
        response = requests.post(
            java_api_url,
            json=payload_font16,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 Respuesta: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Resultado: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error enviando mensaje: {e}")
    
    # Test 3: Probar mapeo de color rojo (valor 1)
    print(f"\n3️⃣ Probando mapeo color rojo (valor 1)...")
    
    payload_red = {
        "ip": panel_ip,
        "itemNum": 1,
        "texts": ["COLOR ROJO TEST"],
        "colors": [1],  # Rojo según protocolo
        "fontSizes": [16],  # 16px = valor 2
        "showEffects": [1]
    }
    
    print(f"   📤 Payload: {json.dumps(payload_red, indent=2)}")
    
    try:
        response = requests.post(
            java_api_url,
            json=payload_red,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 Respuesta: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Resultado: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error enviando mensaje: {e}")
    
    # Test 4: Probar diferentes tamaños de fuente
    print(f"\n4️⃣ Probando diferentes tamaños de fuente...")
    
    font_sizes = [8, 12, 16, 24, 32, 40, 48, 56]
    protocol_values = [0, 1, 2, 3, 4, 5, 6, 7]
    
    for i, fontSize in enumerate(font_sizes):
        protocol_value = protocol_values[i]
        print(f"   📝 Probando fontSize {fontSize}px -> valor {protocol_value}")
        
        payload = {
            "ip": panel_ip,
            "itemNum": 1,
            "texts": [f"FONT {fontSize} TEST"],
            "colors": [1],  # Rojo
            "fontSizes": [fontSize],
            "showEffects": [1]
        }
        
        try:
            response = requests.post(
                java_api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"      ✅ Enviado correctamente")
            else:
                print(f"      ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        time.sleep(1)  # Pausa entre envíos
    
    # Test 5: Probar diferentes colores
    print(f"\n5️⃣ Probando diferentes colores...")
    
    colors = [
        (1, "ROJO"),
        (2, "VERDE"), 
        (3, "AMARILLO"),
        (4, "AZUL"),
        (5, "PURPURA"),
        (6, "AZUL2"),
        (7, "BLANCO")
    ]
    
    for color_value, color_name in colors:
        print(f"   📝 Probando color {color_name} (valor {color_value})")
        
        payload = {
            "ip": panel_ip,
            "itemNum": 1,
            "texts": [f"COLOR {color_name} TEST"],
            "colors": [color_value],
            "fontSizes": [16],  # 16px = valor 2
            "showEffects": [1]
        }
        
        try:
            response = requests.post(
                java_api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"      ✅ Enviado correctamente")
            else:
                print(f"      ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        time.sleep(1)  # Pausa entre envíos
    
    # Test 6: Verificar logs del servicio Java
    print(f"\n6️⃣ Verificando logs del servicio Java...")
    print(f"   🔍 Comando para ver logs:")
    print(f"   📝 journalctl -u parking-panel-service.service -n 50")
    print(f"   📝 Buscar en logs:")
    print(f"   📝 - 'Parámetros mapeados - fontSize: 16->2'")
    print(f"   📝 - 'Simulando envío de mensaje con fontSize=2 y color=1'")
    
    # Test 7: Resumen del mapeo
    print(f"\n7️⃣ RESUMEN DEL MAPEO")
    print(f"   📋 Mapeo de fontSize:")
    print(f"     8px -> valor 0")
    print(f"     12px -> valor 1") 
    print(f"     16px -> valor 2 (por defecto)")
    print(f"     24px -> valor 3")
    print(f"     32px -> valor 4")
    print(f"     40px -> valor 5")
    print(f"     48px -> valor 6")
    print(f"     56px -> valor 7")
    
    print(f"   📋 Mapeo de colores:")
    print(f"     1 -> Rojo")
    print(f"     2 -> Verde")
    print(f"     3 -> Amarillo")
    print(f"     4 -> Azul")
    print(f"     5 -> Púrpura")
    print(f"     6 -> Azul (otro tono)")
    print(f"     7 -> Blanco")
    
    return True

if __name__ == "__main__":
    test_protocol_mapping() 