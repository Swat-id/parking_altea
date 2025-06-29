#!/usr/bin/env python3
"""
Script de prueba para enviar IP del servidor al panel usando protocolo CP5200 corregido
Panel objetivo: 172.20.4.52 (BELLES ARTS 2)
"""

import socket
import struct
import time
import sys

class CP5200Protocol:
    """Implementación del protocolo CP5200 según la documentación oficial"""
    
    # Constantes del protocolo
    HEADER_START = 0xAA
    HEADER_END = 0x55
    
    # Comandos del protocolo
    CONNECT = 0x01
    DISCONNECT = 0x02
    PING = 0x03
    SEND_TEXT = 0x10
    CLEAR_TEXT = 0x11
    SEND_IMAGE = 0x20
    SEND_CLOCK = 0x30
    RESTART = 0x40
    GET_STATUS = 0x42
    
    # Respuestas
    ACK = 0x80
    NACK = 0x81
    
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

class CP5200Client:
    """Cliente TCP/IP para comunicación con paneles CP5200"""
    
    def __init__(self, host: str, port: int = 5000, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False
        self.card_id = 1
    
    def connect(self) -> bool:
        """Establece conexión TCP/IP con el panel"""
        try:
            print(f"Conectando a {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✅ Conexión establecida con {self.host}:{self.port}")
            
            # Enviar comando de conexión
            connect_msg = CP5200Protocol.build_message(self.card_id, CP5200Protocol.CONNECT)
            response = self._send_message(connect_msg)
            
            return response and response[2] == CP5200Protocol.ACK
            
        except Exception as e:
            print(f"❌ Error conectando a {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Cierra conexión con el panel"""
        try:
            if self.connected and self.socket:
                # Enviar comando de desconexión
                disconnect_msg = CP5200Protocol.build_message(self.card_id, CP5200Protocol.DISCONNECT)
                self._send_message(disconnect_msg)
                
                self.socket.close()
                self.connected = False
                print(f"🔌 Desconectado de {self.host}:{self.port}")
                return True
        except Exception as e:
            print(f"❌ Error desconectando: {e}")
        
        return False
    
    def send_text(self, text: str, **kwargs) -> bool:
        """Envía texto al panel"""
        if not self.connected:
            print("❌ No hay conexión activa")
            return False
        
        # Parámetros por defecto
        params = {
            'window': 0,
            'color': 0xFFFFFF,  # Blanco
            'font_size': 16,
            'speed': 5,
            'effect': 0,
            'stay_time': 5,
            'alignment': 1
        }
        params.update(kwargs)
        
        print(f"📤 Enviando texto: '{text}'")
        print(f"   Parámetros: {params}")
        
        # Construir payload
        payload = CP5200Protocol.make_send_text_payload(
            text=text,
            window_no=params['window'],
            color=params['color'],
            font_size=params['font_size'],
            speed=params['speed'],
            effect=params['effect'],
            stay_time=params['stay_time'],
            alignment=params['alignment']
        )
        
        # Enviar mensaje
        message = CP5200Protocol.build_message(self.card_id, CP5200Protocol.SEND_TEXT, payload)
        response = self._send_message(message)
        
        success = response and response[2] == CP5200Protocol.ACK
        if success:
            print(f"✅ Texto enviado exitosamente")
        else:
            print(f"❌ Error enviando texto")
        
        return success
    
    def _send_message(self, message: bytes) -> bytes:
        """Envía mensaje y espera respuesta"""
        try:
            print(f"📤 Enviando mensaje: {message.hex()}")
            self.socket.send(message)
            
            # Esperar respuesta
            response = self.socket.recv(1024)
            print(f"📥 Respuesta recibida: {response.hex()}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error en comunicación: {e}")
            return b''

def main():
    """Función principal"""
    print("=== Test Panel CP5200 Corregido ===")
    print("Panel objetivo: 172.20.4.52 (BELLES ARTS 2)")
    print("Servidor: 157.180.91.63")
    print()
    
    # Configuración
    panel_ip = "172.20.4.52"
    panel_port = 5000  # Puerto por defecto CP5200
    server_ip = "157.180.91.63"
    
    # Crear cliente
    client = CP5200Client(panel_ip, panel_port)
    
    try:
        # Conectar al panel
        if not client.connect():
            print("❌ No se pudo conectar al panel")
            return
        
        # Enviar IP del servidor
        message = f"Servidor: {server_ip}"
        success = client.send_text(
            text=message,
            color=0x00FF00,  # Verde
            font_size=20,
            speed=3,
            effect=1,  # Desplazamiento izquierda
            stay_time=10,
            alignment=1  # Centro
        )
        
        if success:
            print(f"✅ Mensaje enviado exitosamente al panel {panel_ip}")
        else:
            print(f"❌ Error enviando mensaje al panel {panel_ip}")
        
        # Esperar un momento para ver el resultado
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        # Desconectar
        client.disconnect()
    
    print("\n=== Test completado ===")

if __name__ == "__main__":
    main() 