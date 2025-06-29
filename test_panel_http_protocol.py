#!/usr/bin/env python3
"""
Script para probar protocolo HTTP con paneles
Según docs/panels.md, los paneles usan HTTP POST en /update
"""

import requests
import json
import time

def test_http_panel(panel_ip: str, message: str):
    """Prueba envío HTTP al panel"""
    url = f"http://{panel_ip}/update"
    payload = {"message": message}
    
    print(f"🌐 Probando HTTP POST a {url}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=5,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ HTTP POST exitoso")
            return True
        else:
            print("❌ HTTP POST falló")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - Panel no responde en HTTP")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - Panel no responde en tiempo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_tcp_panel(panel_ip: str, panel_port: int, message: str):
    """Prueba envío TCP al panel"""
    import socket
    import struct
    
    # Protocolo CP5200 simplificado
    def build_cp5200_message(text: str) -> bytes:
        # Estructura básica: [AA][55][CARD_ID][COMMAND][LENGTH][DATA][CHECKSUM]
        card_id = 1
        command = 0x10  # SEND_TEXT
        text_bytes = text.encode('utf-8')
        length = len(text_bytes)
        
        # Header
        header = struct.pack('<BBBBH', 0xAA, 0x55, card_id, command, length)
        
        # Checksum simple
        checksum = sum(header[2:]) + sum(text_bytes)
        checksum_bytes = struct.pack('<H', checksum & 0xFFFF)
        
        return header + text_bytes + checksum_bytes
    
    try:
        print(f"🔌 Probando TCP a {panel_ip}:{panel_port}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((panel_ip, panel_port))
        
        # Enviar mensaje simple
        message_bytes = build_cp5200_message(message)
        print(f"📤 Mensaje TCP: {message_bytes.hex()}")
        
        sock.send(message_bytes)
        print("✅ Mensaje TCP enviado")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Error TCP: {e}")
        return False

def main():
    """Función principal"""
    print("=== Test Panel - Protocolos HTTP y TCP ===")
    print("Panel objetivo: 172.20.4.52 (BELLES ARTS 2)")
    print("Servidor: 157.180.91.63")
    print()
    
    panel_ip = "172.20.4.52"
    server_ip = "157.180.91.63"
    message = f"Servidor: {server_ip}"
    
    print(f"📝 Mensaje a enviar: '{message}'")
    print()
    
    # Probar HTTP (protocolo documentado en panels.md)
    print("=== PRUEBA 1: Protocolo HTTP ===")
    http_success = test_http_panel(panel_ip, message)
    print()
    
    # Probar TCP puerto 80 (HTTP alternativo)
    print("=== PRUEBA 2: TCP Puerto 80 ===")
    tcp80_success = test_tcp_panel(panel_ip, 80, message)
    print()
    
    # Probar TCP puerto 5200 (CP5200)
    print("=== PRUEBA 3: TCP Puerto 5200 ===")
    tcp5200_success = test_tcp_panel(panel_ip, 5200, message)
    print()
    
    # Resumen
    print("=== RESUMEN ===")
    print(f"HTTP POST: {'✅ Exitoso' if http_success else '❌ Falló'}")
    print(f"TCP Puerto 80: {'✅ Exitoso' if tcp80_success else '❌ Falló'}")
    print(f"TCP Puerto 5200: {'✅ Exitoso' if tcp5200_success else '❌ Falló'}")
    
    if http_success:
        print("\n💡 El panel responde al protocolo HTTP")
    elif tcp80_success:
        print("\n💡 El panel responde al protocolo TCP en puerto 80")
    elif tcp5200_success:
        print("\n💡 El panel responde al protocolo TCP en puerto 5200")
    else:
        print("\n❌ El panel no responde a ningún protocolo probado")
    
    print("\n=== Test completado ===")

if __name__ == "__main__":
    main() 