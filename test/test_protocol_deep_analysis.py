#!/usr/bin/env python3
"""
Script de análisis profundo del protocolo antiguo
Para identificar por qué la fuente es 8 y el color siempre verde
"""

import requests
import json
import time
from datetime import datetime

def test_protocol_deep_analysis():
    """Análisis profundo del protocolo antiguo"""
    
    print("🔍 ANÁLISIS PROFUNDO DEL PROTOCOLO ANTIGUO")
    print("=" * 60)
    
    # Configuración
    panel_ip = "172.20.4.52"  # BELLES ARTS 2
    java_api_url = "http://127.0.0.1:5656/sendMulti"
    
    # Test 1: Verificar que el servicio Java está respondiendo
    print(f"\n1️⃣ Verificando servicio Java en puerto 5656...")
    try:
        response = requests.get("http://127.0.0.1:5656/health", timeout=5)
        print(f"   ✅ Servicio respondiendo: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Estado: {result}")
    except Exception as e:
        print(f"   ❌ Error conectando al servicio: {e}")
        return False
    
    # Test 2: Enviar mensaje con parámetros específicos
    print(f"\n2️⃣ Enviando mensaje con parámetros específicos...")
    
    payload = {
        "ip": panel_ip,
        "itemNum": 1,
        "texts": ["ANALISIS FONT 16"],
        "colors": [1],  # Rojo
        "fontSizes": [16],  # Tamaño 16
        "showEffects": [1]
    }
    
    print(f"   📤 Payload enviado: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            java_api_url,
            json=payload,
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
    
    # Test 3: Enviar mensaje con color verde y fuente 8
    print(f"\n3️⃣ Enviando mensaje con color verde y fuente 8...")
    
    payload_green = {
        "ip": panel_ip,
        "itemNum": 1,
        "texts": ["ANALISIS VERDE"],
        "colors": [2],  # Verde
        "fontSizes": [8],  # Tamaño 8
        "showEffects": [1]
    }
    
    print(f"   📤 Payload enviado: {json.dumps(payload_green, indent=2)}")
    
    try:
        response = requests.post(
            java_api_url,
            json=payload_green,
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
    
    # Test 4: Verificar logs del servicio Java
    print(f"\n4️⃣ Verificando logs del servicio Java...")
    print(f"   🔍 Comando para ver logs:")
    print(f"   📝 journalctl -u parking-panel-service.service -n 50")
    print(f"   📝 Buscar en logs:")
    print(f"   📝 - 'fontSizes: [16]' o 'fontSize: 16'")
    print(f"   📝 - 'colors: [1]' o 'color: 1'")
    print(f"   📝 - 'Simulando envío de mensaje'")
    
    # Test 5: Análisis del problema
    print(f"\n5️⃣ ANÁLISIS DEL PROBLEMA")
    print(f"   🔍 Posibles causas:")
    print(f"   📍 1. El servicio Java está en modo simulación")
    print(f"   📍 2. La librería CP5200.dll no está cargada")
    print(f"   📍 3. Los parámetros no se están pasando correctamente")
    print(f"   📍 4. El panel está ignorando los parámetros")
    
    # Test 6: Verificar si el servicio está usando la librería real
    print(f"\n6️⃣ VERIFICANDO USO DE LIBRERÍA")
    print(f"   🔍 En el código Java:")
    print(f"   📍 Línea 185: // int result = protocolInstance.sendMulti(...)")
    print(f"   📍 Línea 186: // return result == 0;")
    print(f"   📍 Línea 189: // Simulación temporal mientras se integra la librería")
    print(f"   📍 El servicio está en MODO SIMULACIÓN")
    
    # Test 7: Verificar logs específicos
    print(f"\n7️⃣ VERIFICAR LOGS ESPECÍFICOS")
    print(f"   🔍 Buscar en logs:")
    print(f"   📝 grep 'Simulando envío' /var/log/parking-panel-service.log")
    print(f"   📝 grep 'fontSizes' /var/log/parking-panel-service.log")
    print(f"   📝 grep 'colors' /var/log/parking-panel-service.log")
    
    return True

if __name__ == "__main__":
    test_protocol_deep_analysis() 