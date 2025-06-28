#!/usr/bin/env python3
"""
Script simple para enviar solo la IP a cada panel
"""

import requests
import time

# Configuración del servicio de paneles
PANEL_SERVICE_URL = "http://157.180.91.63:5001"

# Lista de paneles con IPs reales
PANELS = [
    "172.20.17.50",  # PANEL C. ESPORTIVA
    "172.20.5.50",   # PANEL BASSETA 1
    "172.20.5.51",   # PANEL BASSETA 2
    "172.20.8.50",   # PANEL PITERES
    "172.20.4.50",   # PANEL PALAU
    "172.20.4.51",   # PANEL COCOLISO
    "172.20.4.52",   # BELLES ARTS 2
    "172.20.4.53",   # BELLES ARTS
    "172.20.2.50",   # PANEL RENFE
    "172.20.1.50"    # PANEL ALTEA VELLA
]

def send_simple_message(panel_ip):
    """Envía solo la IP como mensaje al panel"""
    try:
        payload = {
            "panelIP": panel_ip,
            "message": panel_ip,  # Solo la IP
            "color": 0x00FF00,    # Verde
            "fontSize": 16,
            "speed": 3,
            "effect": 0,
            "stayTime": 10,
            "alignment": 5
        }
        
        print(f"Enviando '{panel_ip}' a {panel_ip}...")
        
        response = requests.post(
            f"{PANEL_SERVICE_URL}/api/panel/send",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print(f"✅ Éxito - {result.get('responseTime', 0)}ms")
                return True
            else:
                print(f"❌ Fallo: {result.get('message', 'Sin mensaje')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Enviando IPs simples a todos los paneles...")
    print("=" * 50)
    
    success_count = 0
    
    for i, panel_ip in enumerate(PANELS, 1):
        print(f"\n📺 Panel {i}: {panel_ip}")
        
        if send_simple_message(panel_ip):
            success_count += 1
        
        time.sleep(1)  # Pausa entre envíos
    
    print(f"\n📊 RESUMEN:")
    print(f"✅ Exitosos: {success_count}/{len(PANELS)}")
    print(f"📈 Tasa de éxito: {(success_count/len(PANELS)*100):.1f}%")

if __name__ == "__main__":
    main() 