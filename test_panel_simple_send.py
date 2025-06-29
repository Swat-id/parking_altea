#!/usr/bin/env python3
"""
Script simple para enviar mensaje CP5200 sin esperar respuesta
Panel objetivo: 172.20.4.52 (BELLES ARTS 2)
"""

import socket
import struct
import time

class CP5200Protocol:
    """Implementación del protocolo CP5200 según la documentación oficial"""
    
    # Constantes del protocolo
    HEADER_START = 0xAA
    HEADER_END = 0x55
    
    # Comandos del protocolo
    SEND_TEXT = 0x10
    
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """Calcula checksum del mensaje"""
        checksum = 0
        for byte in data:
            checksum += byte
        return checksum & 0xFFFF
    
    @staticmethod
    def build_message(card_id: int, command: int, data: bytes = b'') -> bytes:
        """Construye mensaje según protocolo CP5200"""
        length = len(data)
        
        # Estructura: [START][END][CARD_ID][COMMAND][LENGTH][DATA][CHECKSUM]
        header = struct.pack('<BBBBH', 
            CP5200Protocol.HEADER_START,  # 0xAA
            CP5200Protocol.HEADER_END,    # 0x55
            card_id,                      # ID del panel
            command,                      # Comando
            length                        # Longitud de datos
        )
        
        # Calcular checksum
        checksum_data = header[2:] + data  # card_id + command + length + data
        checksum = CP5200Protocol.calculate_checksum(checksum_data)
        checksum_bytes = struct.pack('<H', checksum)
        
        return header + data + checksum_bytes
    
    @staticmethod
    def make_send_text_payload(text: str, window_no: int = 0, color: int = 0xFFFFFF, 
                              font_size: int = 16, speed: int = 5, effect: int = 0, 
                              stay_time: int = 5, alignment: int = 1) -> bytes:
        """Crea payload para comando SEND_TEXT"""
        # Parámetros del texto
        params = struct.pack('<BBBBBBBBB', 
            window_no,                    # Ventana
            (color >> 16) & 0xFF,        # Color R
            (color >> 8) & 0xFF,         # Color G
            color & 0xFF,                # Color B
            font_size,                   # Tamaño de fuente
            speed,                       # Velocidad
            effect,                      # Efecto
            stay_time,                   # Tiempo de permanencia
            alignment                    # Alineación
        )
        
        # Texto en UTF-8
        text_bytes = text.encode('utf-8')
        
        return params + text_bytes

def send_message_to_panel(panel_ip: str, panel_port: int, message: bytes):
    """Envía mensaje al panel sin esperar respuesta"""
    try:
        print(f"Conectando a {panel_ip}:{panel_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)  # Timeout corto
        sock.connect((panel_ip, panel_port))
        print(f"✅ Conexión establecida")
        
        print(f"📤 Enviando mensaje: {message.hex()}")
        sock.send(message)
        print(f"✅ Mensaje enviado")
        
        # Cerrar conexión inmediatamente
        sock.close()
        print(f"🔌 Conexión cerrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("=== Test Panel CP5200 - Envío Simple ===")
    print("Panel objetivo: 172.20.4.52 (BELLES ARTS 2)")
    print("Servidor: 157.180.91.63")
    print()
    
    # Configuración
    panel_ip = "172.20.4.52"
    panel_port = 5200
    server_ip = "157.180.91.63"
    
    # Crear mensaje de texto
    text = f"Servidor: {server_ip}"
    print(f"📝 Texto a enviar: '{text}'")
    
    # Construir payload
    payload = CP5200Protocol.make_send_text_payload(
        text=text,
        window_no=0,
        color=0x00FF00,  # Verde
        font_size=20,
        speed=3,
        effect=1,  # Desplazamiento izquierda
        stay_time=10,
        alignment=1  # Centro
    )
    
    # Construir mensaje completo
    message = CP5200Protocol.build_message(
        card_id=1,
        command=CP5200Protocol.SEND_TEXT,
        data=payload
    )
    
    print(f"📦 Mensaje completo: {message.hex()}")
    print(f"📏 Longitud: {len(message)} bytes")
    print()
    
    # Enviar mensaje
    success = send_message_to_panel(panel_ip, panel_port, message)
    
    if success:
        print(f"✅ Mensaje enviado exitosamente al panel {panel_ip}")
        print("💡 Verifica si el panel muestra el texto")
    else:
        print(f"❌ Error enviando mensaje al panel {panel_ip}")
    
    print("\n=== Test completado ===")

if __name__ == "__main__":
    main() 