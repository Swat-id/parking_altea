#!/usr/bin/env python3
"""
Script para enviar las IPs de cada panel a sí mismo
Usa el servicio Wine corregido con el flujo correcto: Init → SplitScreen → SendText
"""

import requests
import json
import time
from datetime import datetime

# Configuración del servicio Wine
WINE_SERVICE_URL = "http://157.180.91.63:5002"

# Configuración de paneles desde la base de datos
PANELS = [
    {"id": 1, "name": "PANEL C. ESPORTIVA", "ip": "172.20.17.50", "parking": "1 - P. Ciutat Esportiva"},
    {"id": 2, "name": "PANEL BASSETA 1", "ip": "172.20.5.50", "parking": "2 - P. Basseta Centre"},
    {"id": 3, "name": "PANEL BASSETA 2", "ip": "172.20.5.51", "parking": "2 - P. Basseta Centre"},
    {"id": 4, "name": "PANEL PITERES", "ip": "172.20.8.50", "parking": "6 - P. Poble antic/Conservatori"},
    {"id": 5, "name": "PANEL PALAU", "ip": "172.20.4.50", "parking": "5 - P. Poble antic/Palau Altea"},
    {"id": 6, "name": "PANEL COCOLISO", "ip": "172.20.4.51", "parking": "5 - P. Poble antic/Palau Altea"},
    {"id": 7, "name": "BELLES ARTS 2", "ip": "172.20.4.52", "parking": "4 - P. Poble antic/Belles Arts 2"},
    {"id": 8, "name": "BELLES ARTS", "ip": "172.20.4.53", "parking": "3 - P. Poble antic/Belles Arts 1"},
    {"id": 9, "name": "PANEL RENFE", "ip": "172.20.2.50", "parking": "8 - P. Estació Altea"},
    {"id": 10, "name": "PANEL ALTEA VELLA", "ip": "172.20.1.50", "parking": "9 - P. Altea la Vella"}
]

def check_service_health():
    """Verificar que el servicio Wine esté funcionando"""
    try:
        response = requests.get(f"{WINE_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servicio Wine funcionando correctamente")
            return True
        else:
            print(f"❌ Servicio Wine no responde correctamente: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio Wine: {e}")
        return False

def init_panel_connection(panel_ip):
    """Inicializar conexión con un panel"""
    try:
        data = {
            "panelIP": panel_ip,
            "port": 5200,
            "idCode": 0xFFFFFFFF,
            "timeout": 600
        }
        
        response = requests.post(f"{WINE_SERVICE_URL}/init", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Conexión inicializada con {panel_ip}")
                return True
            else:
                print(f"❌ Error inicializando conexión con {panel_ip}: {result.get('result')}")
                return False
        else:
            print(f"❌ Error HTTP al inicializar {panel_ip}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción al inicializar {panel_ip}: {e}")
        return False

def split_screen(card_id, width=64, height=16):
    """Configurar división de pantalla"""
    try:
        data = {
            "cardID": card_id,
            "width": width,
            "height": height,
            "wndCount": 1
        }
        
        response = requests.post(f"{WINE_SERVICE_URL}/splitscreen", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ SplitScreen configurado para panel {card_id}")
                return True
            else:
                print(f"❌ Error configurando SplitScreen para panel {card_id}: {result.get('result')}")
                return False
        else:
            print(f"❌ Error HTTP configurando SplitScreen para panel {card_id}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción configurando SplitScreen para panel {card_id}: {e}")
        return False

def send_text_to_panel(card_id, text, wnd_no=0):
    """Enviar texto a un panel usando el servicio Wine"""
    try:
        data = {
            "cardID": card_id,
            "text": text,
            "wndNo": wnd_no,
            "color": 0xFF,         # Blanco
            "fontSize": 16,
            "speed": 3,
            "effect": 0,           # Sin efecto
            "stayTime": 0,         # Permanente
            "alignment": 5         # Centro
        }
        
        response = requests.post(f"{WINE_SERVICE_URL}/sendtext", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Texto enviado a panel {card_id}: '{text}'")
                return True
            else:
                print(f"❌ Error enviando texto a panel {card_id}: {result.get('result')}")
                return False
        else:
            print(f"❌ Error HTTP enviando texto a panel {card_id}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción enviando texto a panel {card_id}: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 ENVIANDO IPs A PANELES")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Servicio Wine: {WINE_SERVICE_URL}")
    print()
    
    # Verificar salud del servicio
    if not check_service_health():
        print("❌ No se puede continuar - servicio no disponible")
        return
    
    print(f"📺 Total de paneles: {len(PANELS)}")
    print()
    
    success_count = 0
    error_count = 0
    
    for panel in PANELS:
        panel_id = panel['id']
        panel_name = panel['name']
        panel_ip = panel['ip']
        parking_name = panel['parking']
        
        print(f"🎯 Procesando: {panel_name}")
        print(f"   📍 IP: {panel_ip}")
        print(f"   🏢 Parking: {parking_name}")
        print(f"   🆔 CardID: {panel_id}")
        
        # Paso 1: Inicializar conexión
        if init_panel_connection(panel_ip):
            # Paso 2: Configurar SplitScreen
            if split_screen(panel_id, 64, 16):
                # Paso 3: Enviar IP como texto
                message = f"IP: {panel_ip}"
                if send_text_to_panel(panel_id, message):
                    success_count += 1
                    print(f"   ✅ IP enviada correctamente")
                else:
                    error_count += 1
                    print(f"   ❌ Error enviando IP")
            else:
                error_count += 1
                print(f"   ❌ Error configurando SplitScreen")
        else:
            error_count += 1
            print(f"   ❌ Error inicializando conexión")
        
        print()
        time.sleep(1)  # Pausa entre paneles
    
    # Resumen final
    print("=" * 50)
    print("📊 RESUMEN FINAL")
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Errores: {error_count}")
    print(f"📺 Total: {len(PANELS)}")
    
    if success_count == len(PANELS):
        print("🎉 ¡Todos los paneles procesados exitosamente!")
    elif success_count > 0:
        print(f"⚠️  {success_count} de {len(PANELS)} paneles procesados correctamente")
    else:
        print("💥 No se pudo procesar ningún panel")

if __name__ == "__main__":
    main() 