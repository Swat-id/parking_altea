#!/usr/bin/env python3
"""
Script para probar envío directo a panel 10.8.23.101 ventana 1
"""

import requests
import json
import sys

def test_panel_send():
    """Enviar mensaje a panel directamente usando el servicio panelsender"""
    
    payload = {
        "panels": [
            {
                "ip": "10.8.23.101",
                "port": 5200,
                "protocol": "new",
                "windows": [
                    {
                        "id": 0,
                        "text": "50",
                        "color": 1,
                        "fontSize": 2,
                        "effect": "fijo",
                        "stayTime": 50,
                        "alignmentH": 0,
                        "alignmentV": 0
                    }
                ]
            }
        ]
    }
    
    try:
        print("Enviando mensaje a panel 10.8.23.101, ventana 1...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            'http://localhost:8888/api/v1/panels/send',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Mensaje enviado exitosamente!")
            if 'results' in result:
                for panel_result in result['results']:
                    print(f"Panel {panel_result.get('ip', 'unknown')}: {panel_result.get('message', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al conectar con el servicio panelsender")
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar con el servicio panelsender")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_panel_send()

