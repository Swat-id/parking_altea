#!/usr/bin/env python3
"""
Script para probar el envío de mensajes a un panel único usando el servicio Wine
"""

import requests
import json
import time

def test_single_panel():
    """Prueba el envío de mensaje a un panel único"""
    
    # Configuración del panel
    panel_ip = "172.20.4.52"
    card_id = 1
    
    print("🧪 PROBANDO PANEL ÚNICO")
    print(f"📍 IP: {panel_ip}")
    print(f"🆔 CardID: {card_id}")
    print("=" * 50)
    
    # 1. Inicializar conexión
    print("1️⃣ Inicializando conexión...")
    init_data = {
        "panelIP": panel_ip,
        "port": 5200,
        "timeout": 600
    }
    
    try:
        response = requests.post("http://localhost:5001/init", json=init_data, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        result = response.json()
        print(f"   Success: {result.get('success', False)}")
        print(f"   Result: {result.get('result', -1)}")
        
        if not result.get('success', False):
            print("   ❌ Error en inicialización")
            return False
        else:
            print("   ✅ Inicialización exitosa")
            
    except Exception as e:
        print(f"   ❌ Error en inicialización: {e}")
        return False
    
    # 2. Enviar texto con parámetros exactos del ejemplo funcional
    print("\n2️⃣ Enviando texto...")
    text_data = {
        "cardID": card_id,
        "text": "1",       # Enviar el texto "1"
        "wndNo": 0,
        "color": 3000,     # Color rojo como en el ejemplo
        "fontSize": 16,    # Tamaño de fuente como en el ejemplo
        "speed": 3,        # Velocidad como en el ejemplo
        "effect": 0,       # Efecto como en el ejemplo
        "stayTime": 3,     # Tiempo de permanencia como en el ejemplo
        "alignment": 0     # Alineación como en el ejemplo
    }
    
    try:
        response = requests.post("http://localhost:5001/sendtext", json=text_data, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        result = response.json()
        print(f"   Success: {result.get('success', False)}")
        print(f"   Result: {result.get('result', -1)}")
        
        if result.get('success', False):
            print("   ✅ Texto enviado exitosamente")
            print(f"   📝 Texto '1' enviado al panel")
            return True
        else:
            print("   ❌ Error enviando texto")
            return False
            
    except Exception as e:
        print(f"   ❌ Error enviando texto: {e}")
        return False

if __name__ == "__main__":
    success = test_single_panel()
    if success:
        print("\n🎉 ¡Prueba completada exitosamente!")
    else:
        print("\n💥 Prueba falló") 