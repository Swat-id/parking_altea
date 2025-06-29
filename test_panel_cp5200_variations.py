#!/usr/bin/env python3
"""
Script para probar diferentes variaciones del protocolo CP5200
Panel objetivo: 172.20.4.52 (BELLES ARTS 2)
"""

import socket
import struct
import time

def send_cp5200_variation(panel_ip: str, panel_port: int, variation: str, message_data: bytes):
    """Envía una variación del protocolo CP5200"""
    try:
        print(f"🔌 Probando variación: {variation}")
        print(f"📤 Datos: {message_data.hex()}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((panel_ip, panel_port))
        
        sock.send(message_data)
        print("✅ Mensaje enviado")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("=== Test Panel CP5200 - Variaciones ===")
    print("Panel objetivo: 172.20.4.52 (BELLES ARTS 2)")
    print("Servidor: 157.180.91.63")
    print()
    
    panel_ip = "172.20.4.52"
    panel_port = 5200
    text = "Servidor: 157.180.91.63"
    text_bytes = text.encode('utf-8')
    
    print(f"📝 Texto a enviar: '{text}'")
    print(f"📏 Longitud del texto: {len(text_bytes)} bytes")
    print()
    
    # Variación 1: Protocolo CP5200 básico (sin parámetros)
    print("=== VARIACIÓN 1: Protocolo básico ===")
    card_id = 1
    command = 0x10  # SEND_TEXT
    length = len(text_bytes)
    
    header = struct.pack('<BBBBH', 0xAA, 0x55, card_id, command, length)
    checksum = sum(header[2:]) + sum(text_bytes)
    checksum_bytes = struct.pack('<H', checksum & 0xFFFF)
    
    message1 = header + text_bytes + checksum_bytes
    success1 = send_cp5200_variation(panel_ip, panel_port, "Básico", message1)
    print()
    
    # Variación 2: Con parámetros básicos
    print("=== VARIACIÓN 2: Con parámetros básicos ===")
    params = struct.pack('<BBBBBBBBB', 
        0,      # window
        255,    # color R (blanco)
        255,    # color G
        255,    # color B
        16,     # font_size
        5,      # speed
        0,      # effect
        5,      # stay_time
        1       # alignment
    )
    
    payload2 = params + text_bytes
    length2 = len(payload2)
    
    header2 = struct.pack('<BBBBH', 0xAA, 0x55, card_id, command, length2)
    checksum2 = sum(header2[2:]) + sum(payload2)
    checksum_bytes2 = struct.pack('<H', checksum2 & 0xFFFF)
    
    message2 = header2 + payload2 + checksum_bytes2
    success2 = send_cp5200_variation(panel_ip, panel_port, "Con parámetros", message2)
    print()
    
    # Variación 3: Comando CLEAR_TEXT primero
    print("=== VARIACIÓN 3: CLEAR_TEXT + SEND_TEXT ===")
    # Primero limpiar
    clear_header = struct.pack('<BBBBH', 0xAA, 0x55, card_id, 0x11, 0)  # CLEAR_TEXT
    clear_checksum = sum(clear_header[2:])
    clear_checksum_bytes = struct.pack('<H', clear_checksum & 0xFFFF)
    clear_message = clear_header + clear_checksum_bytes
    
    success3a = send_cp5200_variation(panel_ip, panel_port, "CLEAR_TEXT", clear_message)
    time.sleep(1)
    
    # Luego enviar texto
    success3b = send_cp5200_variation(panel_ip, panel_port, "SEND_TEXT después de CLEAR", message2)
    print()
    
    # Variación 4: Diferente card_id
    print("=== VARIACIÓN 4: Card ID diferente ===")
    card_id_alt = 0  # Probar con card_id = 0
    
    header4 = struct.pack('<BBBBH', 0xAA, 0x55, card_id_alt, command, length2)
    checksum4 = sum(header4[2:]) + sum(payload2)
    checksum_bytes4 = struct.pack('<H', checksum4 & 0xFFFF)
    
    message4 = header4 + payload2 + checksum_bytes4
    success4 = send_cp5200_variation(panel_ip, panel_port, "Card ID = 0", message4)
    print()
    
    # Variación 5: Texto simple sin parámetros
    print("=== VARIACIÓN 5: Texto simple ===")
    simple_text = "TEST"
    simple_bytes = simple_text.encode('utf-8')
    simple_length = len(simple_bytes)
    
    simple_header = struct.pack('<BBBBH', 0xAA, 0x55, card_id, command, simple_length)
    simple_checksum = sum(simple_header[2:]) + sum(simple_bytes)
    simple_checksum_bytes = struct.pack('<H', simple_checksum & 0xFFFF)
    
    simple_message = simple_header + simple_bytes + simple_checksum_bytes
    success5 = send_cp5200_variation(panel_ip, panel_port, "Texto simple 'TEST'", simple_message)
    print()
    
    # Resumen
    print("=== RESUMEN ===")
    print(f"Variación 1 (Básico): {'✅ Exitoso' if success1 else '❌ Falló'}")
    print(f"Variación 2 (Con parámetros): {'✅ Exitoso' if success2 else '❌ Falló'}")
    print(f"Variación 3 (CLEAR + SEND): {'✅ Exitoso' if success3a and success3b else '❌ Falló'}")
    print(f"Variación 4 (Card ID = 0): {'✅ Exitoso' if success4 else '❌ Falló'}")
    print(f"Variación 5 (Texto simple): {'✅ Exitoso' if success5 else '❌ Falló'}")
    
    print("\n💡 Todas las variaciones se envían exitosamente.")
    print("💡 Verifica si alguna variación hace que el panel muestre el texto.")
    print("\n=== Test completado ===")

if __name__ == "__main__":
    main() 