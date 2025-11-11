#!/usr/bin/env python3
"""
Módulo para comunicación con paneles LED mediante protocolo Network TCP
Puerto: 5200
Protocolo: Rotuloselectronicos.net
"""

import socket
import struct
from typing import List, Tuple, Optional
from enum import IntEnum


class TextColor(IntEnum):
    """Colores disponibles para el texto"""
    RED = 0x01
    GREEN = 0x02
    YELLOW = 0x03
    BLUE = 0x04
    PURPLE = 0x05
    CYAN = 0x06
    WHITE = 0x07


class FontSize(IntEnum):
    """Tamaños de fuente disponibles"""
    SIZE_8 = 0x00   # 8px
    SIZE_12 = 0x01  # 12px
    SIZE_16 = 0x02  # 16px (por defecto)
    SIZE_24 = 0x03  # 24px
    SIZE_32 = 0x04  # 32px
    SIZE_40 = 0x05  # 40px
    SIZE_48 = 0x06  # 48px
    SIZE_56 = 0x07  # 56px


class TextAlignment(IntEnum):
    """Alineaciones disponibles para el texto"""
    LEFT_TOP = 0x00
    LEFT_CENTER = 0x04
    CENTER_CENTER = 0x05
    RIGHT_CENTER = 0x06


class TextEffect(IntEnum):
    """Efectos disponibles para el texto"""
    STATIC = 0x00           # Estático (instantáneo) / Draw
    OPEN_LEFT = 0x01        # Abrir desde izquierda
    OPEN_RIGHT = 0x02       # Abrir desde derecha
    MOVE_LEFT = 0x06        # Mover a izquierda
    MOVE_RIGHT = 0x07       # Mover a derecha
    MOVE_UP = 0x08          # Mover arriba
    MOVE_DOWN = 0x09        # Mover abajo
    SCROLL_UP = 0x0A        # Scroll arriba
    SCROLL_LEFT = 0x0B      # Scroll de derecha a izquierda
    SCROLL_RIGHT = 0x0C     # Scroll de izquierda a derecha
    FLICKER = 0x0D          # Parpadeo
    CONTINUOUS_SCROLL_LEFT = 0x0E   # Scroll continuo a izquierda
    CONTINUOUS_SCROLL_RIGHT = 0x0F  # Scroll continuo a derecha


class PanelProtocol:
    """
    Clase para construir y enviar paquetes de protocolo a paneles LED
    """
    
    # Constantes del protocolo
    ID_CODE = bytes([0xFF, 0xFF, 0xFF, 0xFF])
    PACKET_TYPE = 0x68
    CARD_TYPE = 0x32
    CARD_ID = 0x01
    PROTOCOL_CODE = 0x7B
    CONFIRMATION_FLAG = 0x01  # Solicitar confirmación de recepción
    PORT = 5200
    
    # Comandos
    CMD_CREATE_WINDOW = 0x01
    CMD_SEND_TEXT = 0x02
    CMD_SEND_IMAGE = 0x03
    CMD_CHANGE_PROGRAM = 0x08
    
    def __init__(self, ip_address: str, port: int = PORT):
        """
        Inicializa el protocolo con la dirección IP del panel
        
        Args:
            ip_address: Dirección IP del panel LED
            port: Puerto TCP (por defecto 5200)
        """
        self.ip_address = ip_address
        self.port = port
        self.timeout = 5  # timeout en segundos
    
    @staticmethod
    def calculate_checksum(data: bytes) -> bytes:
        """
        Calcula el checksum de los datos (suma de todos los bytes)
        
        Args:
            data: Bytes desde Packet Type hasta el final de Packet Data
            
        Returns:
            Checksum en formato Low Byte, High Byte (2 bytes)
        """
        checksum = sum(data) & 0xFFFF
        return struct.pack('<H', checksum)  # Little-endian
    
    @staticmethod
    def encode_color_font(color: TextColor, font_size: FontSize) -> int:
        """
        Codifica color y tamaño de fuente en un byte
        Fórmula: (color << 4) | font_size
        
        Args:
            color: Color del texto
            font_size: Tamaño de la fuente
            
        Returns:
            Byte codificado
        """
        return (color << 4) | font_size
    
    def build_text_packet(
        self,
        text: str,
        window_number: int = 0,
        color: TextColor = TextColor.RED,
        font_size: FontSize = FontSize.SIZE_16,
        alignment: TextAlignment = TextAlignment.LEFT_TOP,
        effect: TextEffect = TextEffect.STATIC,
        speed: int = 0x03,
        wait_time: int = 0x0003
    ) -> bytes:
        """
        Construye un paquete para enviar texto a una ventana específica
        
        Args:
            text: Texto a enviar (ASCII)
            window_number: Número de ventana (0-7)
            color: Color del texto
            font_size: Tamaño de la fuente
            alignment: Alineación del texto
            effect: Efecto de visualización
            speed: Velocidad del efecto (0x00 más rápido)
            wait_time: Tiempo de espera (2 bytes)
            
        Returns:
            Paquete completo en bytes listo para enviar
        """
        # Codificar color y fuente
        color_font_byte = self.encode_color_font(color, font_size)
        
        # Construir datos del comando (CC = 0x02)
        command_data = bytearray()
        command_data.append(self.CMD_SEND_TEXT)  # CC
        command_data.append(window_number)        # Número de ventana
        command_data.append(effect)               # Efecto
        command_data.append(alignment)            # Alineación
        command_data.append(speed)                # Velocidad
        command_data.extend(struct.pack('<H', wait_time))  # Tiempo espera (little-endian)
        
        # Agregar texto con formato: [color_font_byte, 0x00, carácter]
        for char in text:
            command_data.append(color_font_byte)
            command_data.append(0x00)  # Reservado
            command_data.append(ord(char))
        
        # Agregar fin de texto (3 bytes a 0)
        command_data.extend([0x00, 0x00, 0x00])
        
        # Construir packet data (desde Packet Type hasta datos)
        packet_data = bytearray()
        packet_data.append(self.PACKET_TYPE)
        packet_data.append(self.CARD_TYPE)
        packet_data.append(self.CARD_ID)
        packet_data.append(self.PROTOCOL_CODE)
        packet_data.append(self.CONFIRMATION_FLAG)
        
        # Longitud del comando (4 bytes, little-endian)
        command_length = len(command_data)
        packet_data.extend(struct.pack('<I', command_length))
        
        # Agregar datos del comando
        packet_data.extend(command_data)
        
        # Calcular checksum
        checksum = self.calculate_checksum(packet_data)
        packet_data.extend(checksum)
        
        # Construir paquete completo (Network format)
        full_packet = bytearray()
        full_packet.extend(self.ID_CODE)
        
        # Network data length (longitud desde Packet Type hasta Checksum)
        network_length = len(packet_data)
        full_packet.extend(struct.pack('<H', network_length))
        
        # Reservado (2 bytes)
        full_packet.extend([0x00, 0x00])
        
        # Agregar packet data
        full_packet.extend(packet_data)
        
        return bytes(full_packet)
    
    def send_packet(self, packet: bytes, verbose: bool = True) -> Optional[bytes]:
        """
        Envía un paquete al panel LED por TCP
        
        Args:
            packet: Paquete en bytes para enviar
            verbose: Mostrar información de debug
            
        Returns:
            Respuesta del panel si hay, None en caso contrario
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                
                if verbose:
                    print(f"Conectando a {self.ip_address}:{self.port}...")
                
                sock.connect((self.ip_address, self.port))
                
                if verbose:
                    print(f"Enviando {len(packet)} bytes...")
                    print(f"Paquete (hex): {packet.hex(' ')}")
                
                sock.sendall(packet)
                
                # Intentar recibir respuesta si se solicitó confirmación
                try:
                    response = sock.recv(1024)
                    if verbose and response:
                        print(f"Respuesta recibida: {response.hex(' ')}")
                    return response
                except socket.timeout:
                    if verbose:
                        print("No se recibió respuesta (timeout)")
                    return None
                    
        except ConnectionRefusedError:
            print(f"Error: No se pudo conectar a {self.ip_address}:{self.port}")
            print("Verifica que el panel esté encendido y accesible")
            return None
        except socket.timeout:
            print(f"Error: Timeout al conectar con {self.ip_address}:{self.port}")
            return None
        except Exception as e:
            print(f"Error al enviar paquete: {e}")
            return None
    
    def send_text(
        self,
        text: str,
        window_number: int = 0,
        color: TextColor = TextColor.RED,
        font_size: FontSize = FontSize.SIZE_16,
        alignment: TextAlignment = TextAlignment.LEFT_TOP,
        effect: TextEffect = TextEffect.STATIC,
        speed: int = 0x03,
        wait_time: int = 0x0003,
        verbose: bool = True
    ) -> bool:
        """
        Envía texto al panel LED (método simplificado)
        
        Args:
            text: Texto a enviar
            window_number: Número de ventana (0-7)
            color: Color del texto
            font_size: Tamaño de la fuente
            alignment: Alineación del texto
            effect: Efecto de visualización
            speed: Velocidad del efecto
            wait_time: Tiempo de espera
            verbose: Mostrar información de debug
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        packet = self.build_text_packet(
            text=text,
            window_number=window_number,
            color=color,
            font_size=font_size,
            alignment=alignment,
            effect=effect,
            speed=speed,
            wait_time=wait_time
        )
        
        response = self.send_packet(packet, verbose)
        return response is not None
    
    def send_hex_string(self, hex_string: str, verbose: bool = True) -> bool:
        """
        Envía un paquete desde una cadena hexadecimal
        Útil para probar ejemplos de la documentación
        
        Args:
            hex_string: String hexadecimal (ej: "FF FF FF FF 0F 00 ...")
            verbose: Mostrar información de debug
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            # Limpiar el string y convertir a bytes
            hex_clean = hex_string.replace(' ', '').replace(',', '').replace('0x', '')
            packet = bytes.fromhex(hex_clean)
            
            response = self.send_packet(packet, verbose)
            return response is not None
            
        except ValueError as e:
            print(f"Error al parsear hexadecimal: {e}")
            return False


def print_color_table():
    """Imprime una tabla de referencia de colores"""
    print("\n=== COLORES DISPONIBLES ===")
    for color in TextColor:
        print(f"  {color.name:10s} = 0x{color.value:02X}")


def print_font_table():
    """Imprime una tabla de referencia de tamaños de fuente"""
    print("\n=== TAMAÑOS DE FUENTE ===")
    for font in FontSize:
        size = font.name.replace('SIZE_', '')
        print(f"  {size:3s}px = 0x{font.value:02X}")


def print_alignment_table():
    """Imprime una tabla de referencia de alineaciones"""
    print("\n=== ALINEACIONES ===")
    for align in TextAlignment:
        print(f"  {align.name:15s} = 0x{align.value:02X}")


if __name__ == "__main__":
    print("Módulo de protocolo para paneles LED")
    print("=" * 50)
    print_color_table()
    print_font_table()
    print_alignment_table()
    print("\nImporta este módulo para usar en tus scripts")

