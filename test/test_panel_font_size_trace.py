#!/usr/bin/env python3
"""
Script de prueba para trazar el flujo completo del tamaño de fuente
desde el API hasta el panel con protocolo antiguo
"""

import requests
import json
import time
from datetime import datetime

def test_font_size_trace():
    """Probar el flujo completo del tamaño de fuente"""
    
    print("🔍 INICIANDO PRUEBA DE TRAZABILIDAD - TAMAÑO DE FUENTE")
    print("=" * 60)
    
    # Configuración
    panel_ip = "172.20.4.52"  # BELLES ARTS 2 (protocolo antiguo)
    api_url = "http://127.0.0.1:6001/panel/7/message"  # Panel ID 7
    java_api_url = "http://127.0.0.1:5656/sendMulti"
    
    # Test 1: Verificar que el API está respondiendo
    print(f"\n1️⃣ Verificando API en puerto 6001...")
    try:
        response = requests.get("http://127.0.0.1:6001/health", timeout=5)
        print(f"   ✅ API respondiendo: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error conectando al API: {e}")
        return False
    
    # Test 2: Verificar que el servicio Java está respondiendo
    print(f"\n2️⃣ Verificando servicio Java en puerto 5656...")
    try:
        response = requests.get("http://127.0.0.1:5656/health", timeout=5)
        print(f"   ✅ Servicio Java respondiendo: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error conectando al servicio Java: {e}")
        return False
    
    # Test 3: Enviar mensaje a través del API con fontSize=8
    print(f"\n3️⃣ Enviando mensaje a través del API con fontSize=8...")
    
    payload_api = {
        "message": "PRUEBA FONT 8",
        "color": 1,  # Rojo
        "fontSize": 8,  # Tamaño 8 (incorrecto)
        "showEffect": 1,
        "duration": 10
    }
    
    print(f"   📤 Payload API: {json.dumps(payload_api, indent=2)}")
    
    try:
        response = requests.post(
            api_url,
            json=payload_api,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 Respuesta API: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Resultado API: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Error API: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error enviando mensaje al API: {e}")
        return False
    
    # Test 4: Verificar qué se envió al servicio Java
    print(f"\n4️⃣ Verificando logs del servicio Java...")
    print(f"   🔍 Revisar logs del servicio Java para ver el fontSize recibido")
    print(f"   📝 Comando: journalctl -u parking-panel-service.service -n 20")
    
    # Test 5: Enviar mensaje directo al servicio Java con fontSize=16
    print(f"\n5️⃣ Enviando mensaje directo al servicio Java con fontSize=16...")
    
    payload_java = {
        "ip": panel_ip,
        "itemNum": 1,
        "texts": ["PRUEBA FONT 16"],
        "colors": [1],  # Rojo
        "fontSizes": [16],  # Tamaño 16 (correcto)
        "showEffects": [1]
    }
    
    print(f"   📤 Payload Java: {json.dumps(payload_java, indent=2)}")
    
    try:
        response = requests.post(
            java_api_url,
            json=payload_java,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 Respuesta Java: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Resultado Java: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Error Java: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error enviando mensaje al servicio Java: {e}")
    
    # Test 6: Análisis del problema
    print(f"\n6️⃣ ANÁLISIS DEL PROBLEMA")
    print(f"   🔍 El problema está en el endpoint /panel/<id>/message del API")
    print(f"   📍 Línea 822: fontSize = req.get('fontSize', 2)  # Valor por defecto 2")
    print(f"   📍 Línea 840: font_size=fontSize  # Se pasa el valor 2 al servicio")
    print(f"   📍 El servicio Java recibe fontSize=2 en lugar de 16")
    print(f"   📍 El servicio Java debería usar 16 por defecto para protocolo antiguo")
    
    return True

if __name__ == "__main__":
    test_font_size_trace() 