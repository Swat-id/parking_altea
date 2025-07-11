#!/usr/bin/env python3
"""
Script para enviar mensaje "EN PROVES" a paneles específicos
Autor: Sistema de Despliegue
Fecha: 2025-01-07
"""

import requests
import json
import sys
from datetime import datetime

# Configuración
PANEL_API_URL = "http://localhost:8888/api/v1/panels/send"
PANELS = [
    {"ip": "172.20.8.50", "port": 5200, "protocol": "new"},
    {"ip": "172.20.8.51", "port": 5200, "protocol": "new"}
]

# Parámetros del mensaje
TEXT = "EN PROVES"
COLOR = 1  # Rojo
FONT_SIZE = 2  # Tamaño 16 (código 2)
EFFECT = "fijo"  # Texto fijo
STAY_TIME = 50
ALIGNMENT_H = 0  # Centrado horizontal
ALIGNMENT_V = 0  # Centrado vertical

def send_message_to_panels():
    """Enviar mensaje a los paneles especificados"""
    
    print(f"🎯 Enviando mensaje a {len(PANELS)} paneles...")
    print(f"📝 Texto: '{TEXT}'")
    print(f"🎨 Color: Rojo (código {COLOR})")
    print(f"📏 Tamaño: 16 (código {FONT_SIZE})")
    print(f"✨ Efecto: {EFFECT}")
    print(f"📍 Paneles: {[panel['ip'] for panel in PANELS]}")
    print("-" * 50)
    
    # Preparar payload para múltiples paneles
    panel_configs = []
    for panel in PANELS:
        panel_config = {
            "ip": panel['ip'],
            "port": panel['port'],
            "protocol": panel['protocol'],
            "windows": [
                {
                    "id": 0,
                    "text": TEXT,
                    "color": COLOR,
                    "fontSize": FONT_SIZE,
                    "speed": 100,
                    "effect": EFFECT,
                    "stayTime": STAY_TIME,
                    "alignmentH": ALIGNMENT_H,
                    "alignmentV": ALIGNMENT_V
                }
            ]
        }
        panel_configs.append(panel_config)
    
    payload = {"panels": panel_configs}
    
    try:
        print("📡 Enviando petición a la API...")
        response = requests.post(
            PANEL_API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Respuesta exitosa:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Analizar resultados por panel
            if 'results' in result:
                for panel_result in result['results']:
                    panel_ip = panel_result.get('panel_ip', 'Desconocido')
                    success = panel_result.get('success', False)
                    message = panel_result.get('message', 'Sin mensaje')
                    
                    if success:
                        print(f"✅ Panel {panel_ip}: Mensaje enviado correctamente")
                    else:
                        print(f"❌ Panel {panel_ip}: Error - {message}")
            else:
                print("⚠️  No se encontraron resultados detallados por panel")
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se puede conectar al servicio de paneles")
        print("💡 Verificar que el servicio esté ejecutándose en http://localhost:8888")
        
    except requests.exceptions.Timeout:
        print("❌ Error de timeout: La petición tardó demasiado")
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

def test_panel_connectivity():
    """Probar conectividad con los paneles"""
    print("🔍 Probando conectividad con los paneles...")
    
    for panel in PANELS:
        ip = panel['ip']
        try:
            # Intentar ping al panel
            import subprocess
            result = subprocess.run(['ping', '-c', '1', '-W', '2', ip], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"✅ Panel {ip}: Conectado")
            else:
                print(f"❌ Panel {ip}: Sin conexión")
                
        except Exception as e:
            print(f"⚠️  Panel {ip}: Error al probar conectividad - {str(e)}")

def main():
    """Función principal"""
    print("🚀 Envío de Mensaje 'EN PROVES' a Paneles")
    print("=" * 50)
    print(f"⏰ Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_panel_connectivity()
            return
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python send_en_proves_message.py          # Enviar mensaje")
            print("  python send_en_proves_message.py --test   # Probar conectividad")
            print("  python send_en_proves_message.py --help   # Mostrar ayuda")
            return
    
    # Enviar mensaje
    send_message_to_panels()
    
    print()
    print("🏁 Proceso completado")

if __name__ == "__main__":
    main() 