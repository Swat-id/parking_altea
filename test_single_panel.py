#!/usr/bin/env python3
"""
Script de prueba para un solo panel - ver salida completa de Wine
"""

import requests
import json

# Configuración del servicio Wine
WINE_SERVICE_URL = "http://157.180.91.63:5002"

def test_single_panel():
    """Probar un solo panel y ver la salida completa"""
    
    panel_ip = "172.20.17.50"  # PANEL C. ESPORTIVA
    card_id = 1
    
    print(f"🧪 PROBANDO PANEL ÚNICO")
    print(f"📍 IP: {panel_ip}")
    print(f"🆔 CardID: {card_id}")
    print("=" * 50)
    
    # Paso 1: Inicializar conexión
    print("1️⃣ Inicializando conexión...")
    data = {
        "panelIP": panel_ip,
        "port": 5200,
        "idCode": 0xFFFFFFFF,
        "timeout": 600
    }
    
    response = requests.post(f"{WINE_SERVICE_URL}/init", json=data, timeout=10)
    print(f"   HTTP Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Success: {result.get('success')}")
        print(f"   Result: {result.get('result')}")
        
        if result.get('success'):
            print("   ✅ Inicialización exitosa")
            
            # Paso 2: SplitScreen
            print("\n2️⃣ Configurando SplitScreen...")
            data = {
                "cardID": card_id,
                "width": 64,
                "height": 16,
                "wndCount": 1
            }
            
            response = requests.post(f"{WINE_SERVICE_URL}/splitscreen", json=data, timeout=10)
            print(f"   HTTP Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result.get('success')}")
                print(f"   Result: {result.get('result')}")
                
                if result.get('success'):
                    print("   ✅ SplitScreen exitoso")
                    
                    # Paso 3: Enviar texto
                    print("\n3️⃣ Enviando texto...")
                    message = f"IP: {panel_ip}"
                    data = {
                        "cardID": card_id,
                        "text": message,
                        "wndNo": 0,
                        "color": 0xFF,
                        "fontSize": 16,
                        "speed": 3,
                        "effect": 0,
                        "stayTime": 0,
                        "alignment": 5
                    }
                    
                    response = requests.post(f"{WINE_SERVICE_URL}/sendtext", json=data, timeout=10)
                    print(f"   HTTP Status: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   Success: {result.get('success')}")
                        print(f"   Result: {result.get('result')}")
                        
                        if result.get('success'):
                            print("   ✅ Texto enviado exitosamente")
                            print(f"   📺 Mensaje: {message}")
                        else:
                            print("   ❌ Error enviando texto")
                    else:
                        print("   ❌ Error HTTP enviando texto")
                else:
                    print("   ❌ Error configurando SplitScreen")
            else:
                print("   ❌ Error HTTP configurando SplitScreen")
        else:
            print("   ❌ Error en inicialización")
    else:
        print("   ❌ Error HTTP en inicialización")

if __name__ == "__main__":
    test_single_panel() 