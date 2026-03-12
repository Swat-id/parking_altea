#!/usr/bin/env python3
"""
Script de prueba para verificar efectos de scroll en paneles v4.5.0
"""

import requests
import json
import sys

# Configuración
API_URL = "http://localhost:8888/api/v1/panels/send"
PANELS = ["172.20.4.50", "172.20.4.51"]
TEST_TEXT = "PRUEBA SCROLL v4.5.0 - TEXTO LARGO PARA VERIFICAR DESPLAZAMIENTO"

def test_panel_effect(panel_ip, text, effect_string, effect_code, stay_time=50):
    """Enviar texto a un panel con efecto específico"""
    
    payload = {
        "panels": [
            {
                "ip": panel_ip,
                "port": 5200,
                "protocol": "new",
                "windows": [
                    {
                        "id": 0,
                        "text": text,
                        "color": 2,  # Verde
                        "fontSize": 2,  # 16px
                        "effect": effect_string,
                        "stayTime": stay_time,
                        "alignmentH": 0,
                        "alignmentV": 0
                    }
                ]
            }
        ]
    }
    
    print(f"\n{'='*60}")
    print(f"Panel: {panel_ip}")
    print(f"Efecto: {effect_string} (código: {hex(effect_code)})")
    print(f"Texto: {text[:50]}...")
    print(f"StayTime: {stay_time}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    print("="*60)
    print("TEST DE EFECTOS DE SCROLL v4.5.0")
    print("="*60)
    
    # Test 1: Efecto scroll_left (código 0x0B) - auto-scroll si texto largo
    print("\n\n*** TEST 1: scroll_left (0x0B) - Auto-scroll si texto largo ***")
    for panel in PANELS:
        test_panel_effect(panel, TEST_TEXT, "scroll_left", 0x0B, stay_time=50)
    
    input("\nPresiona Enter para continuar con el siguiente test...")
    
    # Test 2: Efecto continuous_scroll_left (código 0x0E) - siempre scroll
    print("\n\n*** TEST 2: continuous_scroll_left (0x0E) - Siempre scroll ***")
    for panel in PANELS:
        test_panel_effect(panel, TEST_TEXT, "continuous_scroll_left", 0x0E, stay_time=0)
    
    input("\nPresiona Enter para continuar con el siguiente test...")
    
    # Test 3: Efecto fijo (código 0x00) - estático
    print("\n\n*** TEST 3: fijo (0x00) - Estático ***")
    for panel in PANELS:
        test_panel_effect(panel, "ESTATICO", "fijo", 0x00, stay_time=50)
    
    input("\nPresiona Enter para probar con el código numérico directo...")
    
    # Test 4: Enviar código numérico directamente en lugar de string
    print("\n\n*** TEST 4: Código numérico directo (11 = 0x0B) ***")
    payload = {
        "panels": [
            {
                "ip": PANELS[0],
                "port": 5200,
                "protocol": "new",
                "windows": [
                    {
                        "id": 0,
                        "text": TEST_TEXT,
                        "color": 2,
                        "fontSize": 2,
                        "effect": 11,  # Código numérico directo
                        "stayTime": 50,
                        "alignmentH": 0,
                        "alignmentV": 0
                    }
                ]
            }
        ]
    }
    print(f"Payload con código numérico: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n\nTests completados.")


if __name__ == "__main__":
    main()
