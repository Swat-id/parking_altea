"""
Constructor de paquetes del protocolo de paneles
"""

import struct
from typing import List, Tuple, Optional
from .constants import (
    ID_CODE, PACKET_TYPE_SEND, CARD_TYPE, CMD_PROTOCOL_CONTROL,
    SUB_CMD_CREATE_WINDOW, SUB_CMD_SEND_TEXT, SUB_CMD_SEND_IMAGE,
    SUB_CMD_EXECUTE_PROGRAM, CONFIRMATION_REQUESTED, NO_CONFIRMATION
)
from .checksum import calculate_checksum


class PacketBuilder:
    """Constructor de paquetes del protocolo de comunicación con paneles"""
    
    @staticmethod
    def build_network_packet(
        card_id: int,
        command: int,
        packet_data: bytes,
        request_confirmation: bool = True,
        packet_number: int = 0x00,
        last_packet_number: int = 0x00
    ) -> bytes:
        """
        Construye un paquete completo de red según el protocolo.
        
        Args:
            card_id: ID de la tarjeta (0x01-0xFE) o 0xFF para broadcast
            command: Código de comando
            packet_data: Datos del comando CC (sin incluir headers adicionales)
            request_confirmation: Si True, solicita confirmación (bit 0 = 1)
            packet_number: Número de secuencia del paquete (0x00-0xFF)
            last_packet_number: Número total de paquetes - 1 (0x00 para un solo paquete)
            
        Returns:
            bytes: Paquete completo listo para enviar
        """
        # Additional info: bit 0 = confirmación, bits 1-7 = 0
        additional_info = CONFIRMATION_REQUESTED if request_confirmation else NO_CONFIRMATION
        
        # Construir parte del paquete desde Packet Type hasta Additional Info
        packet_header = bytes([
            PACKET_TYPE_SEND,      # 0x68
            CARD_TYPE,             # 0x32
            card_id,               # 0x01-0xFE o 0xFF
            command,               # 0x7B
            additional_info        # 0x01 o 0x00
        ])
        
        # Según la documentación, después de Additional Info vienen:
        # - Packet data length (2 bytes) - Longitud de la parte "CC..."
        # - Packet number (1 byte)
        # - Last packet number (1 byte)
        packet_data_length = len(packet_data)
        packet_info = (
            struct.pack('<H', packet_data_length) +  # Packet data length (2 bytes, little-endian)
            bytes([packet_number]) +                  # Packet number (1 byte)
            bytes([last_packet_number])               # Last packet number (1 byte)
        )
        
        # Datos completos para calcular checksum (desde Packet Type hasta Packet Data)
        data_for_checksum = packet_header + packet_info + packet_data
        
        # Calcular checksum (suma desde Packet Type hasta Packet Data)
        checksum = calculate_checksum(data_for_checksum)
        
        # Calcular longitud de red (desde Packet Type hasta Checksum)
        # Según el protocolo, la longitud es de 2 bytes (little-endian)
        network_length = len(data_for_checksum) + len(checksum)
        
        # Construir paquete completo según documentación:
        # - ID Code: 4 bytes (0xFF, 0xFF, 0xFF, 0xFF)
        # - Network Length: 2 bytes (little-endian) - desde Packet Type hasta Checksum
        # - Reserved: 2 bytes (0x00, 0x00)
        # - Packet Type hasta Checksum
        packet = (
            ID_CODE +                                    # 4 bytes: ID Code
            struct.pack('<H', network_length) +          # 2 bytes: Network Length (little-endian)
            b'\x00\x00' +                                # 2 bytes: Reserved
            data_for_checksum +                          # Packet Type + Card Type + Card ID + CMD + Info + Packet Data Length + Packet Number + Last Packet Number + Packet Data
            checksum                                     # 2 bytes: Checksum
        )
        
        return packet
    
    @staticmethod
    def build_create_window_packet(
        card_id: int,
        windows: List[Tuple[int, int, int, int]],
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete para crear ventanas en el panel.
        
        Args:
            card_id: ID de la tarjeta
            windows: Lista de tuplas (x, y, width, height) para cada ventana
            request_confirmation: Si solicita confirmación
            
        Returns:
            bytes: Paquete completo
        """
        # Construir datos del comando
        # Comando CC: 0x01 (crear ventana)
        # Número de ventanas: len(windows)
        packet_data = bytes([SUB_CMD_CREATE_WINDOW, len(windows)])
        
        # Para cada ventana: x, y, width, height (cada uno 2 bytes, little-endian)
        for x, y, width, height in windows:
            packet_data += struct.pack('<HHHH', x, y, width, height)
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation
        )
    
    @staticmethod
    def build_send_text_packet(
        card_id: int,
        window_id: int,
        text: str,
        color: int,
        font_size: int,
        effect: int = 0x00,
        alignment: int = 0x00,
        speed: int = 0x00,
        stay_time: int = 3,
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete para enviar texto a una ventana.
        
        Args:
            card_id: ID de la tarjeta
            window_id: ID de la ventana (0, 1, 2, ...)
            text: Texto a enviar
            color: Color del texto (0x01-0x07)
            font_size: Tamaño de fuente (0x00-0x07)
            effect: Efecto de texto (0x00 = instantáneo)
            alignment: Alineación (0x00 = left top)
            speed: Velocidad del efecto (0x00 = más rápido)
            stay_time: Tiempo de espera en segundos
            request_confirmation: Si solicita confirmación
            
        Returns:
            bytes: Paquete completo
        """
        # Calcular byte de color + tamaño: (color << 4) | font_size
        color_font = (color << 4) | font_size
        
        # Construir datos del comando CC (sin incluir la longitud)
        # Comando CC: 0x02 (enviar texto)
        command_data = bytes([
            SUB_CMD_SEND_TEXT,
            window_id,
            effect,
            alignment,
            speed
        ])
        
        # Tiempo de espera (2 bytes, little-endian)
        command_data += struct.pack('<H', stay_time)
        
        # Según el ejemplo exacto de la documentación:
        # - color_font + 0x00 (reservado) antes del primer carácter
        # - Cada carácter (incluido el primero): carácter + color_font + 0x00
        # - Último carácter: carácter + 0x00 + 0x00 + 0x00 (sin color_font después)
        if len(text) > 0:
            # Primer byte: color_font + 0x00 (reservado) antes del primer carácter
            command_data += bytes([color_font, 0x00])
            
            # Todos los caracteres: carácter + color_font + 0x00
            for char in text:
                command_data += bytes([ord(char), color_font, 0x00])
            
            # Reemplazar los últimos 3 bytes (del último carácter) con: carácter + 0x00 + 0x00 + 0x00
            # Eliminar los últimos 3 bytes (color_font + 0x00 del último carácter)
            command_data = command_data[:-3]
            # Agregar el último carácter con terminación: carácter + 0x00 + 0x00 + 0x00
            command_data += bytes([ord(text[-1]), 0x00, 0x00, 0x00])
        else:
            # Si no hay texto, solo fin de texto
            command_data += b'\x00\x00\x00'
        
        # Según el ejemplo, el packet_data debe incluir la longitud del comando CC (4 bytes, little-endian)
        # al inicio, antes de los datos del comando
        packet_data = struct.pack('<I', len(command_data)) + command_data
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation
        )
    
    @staticmethod
    def build_send_image_packet(
        card_id: int,
        window_id: int,
        filename: str,
        draw_mode: int = 0x00,
        speed: int = 0x01,
        stay_time: int = 3,
        file_reference: int = 0x02,  # 0x02 = GIF
        x: int = 0,
        y: int = 0,
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete para enviar una imagen a una ventana.
        
        Args:
            card_id: ID de la tarjeta
            window_id: ID de la ventana
            filename: Nombre del archivo (ej: "test.gif")
            draw_mode: Modo de mostrar (0x00 = Draw)
            speed: Velocidad de mostrar
            stay_time: Tiempo de espera en segundos
            file_reference: Referencia de archivo (0x02 = GIF)
            x: Coordenada X
            y: Coordenada Y
            request_confirmation: Si solicita confirmación
            
        Returns:
            bytes: Paquete completo
        """
        # Construir datos del comando
        # Comando CC: 0x03 (enviar imagen)
        packet_data = bytes([
            SUB_CMD_SEND_IMAGE,
            window_id,
            draw_mode,
            speed
        ])
        
        # Tiempo de espera (2 bytes, little-endian)
        packet_data += struct.pack('<H', stay_time)
        
        # Referencia de archivo
        packet_data += bytes([file_reference])
        
        # Coordenadas X, Y (2 bytes cada una, little-endian)
        packet_data += struct.pack('<HH', x, y)
        
        # Nombre del archivo (ASCII) + byte terminador 0x00
        packet_data += filename.encode('ascii') + b'\x00'
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation
        )
    
    @staticmethod
    def build_execute_program_packet(
        card_id: int,
        program_number: int,
        program_count: int = 1,
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete para ejecutar un programa guardado.
        
        Args:
            card_id: ID de la tarjeta
            program_number: Número del programa a ejecutar (1-N)
            program_count: Cantidad de programas (por defecto 1)
            request_confirmation: Si solicita confirmación
            
        Returns:
            bytes: Paquete completo
        """
        # Construir datos del comando
        # Comando CC: 0x08 (ejecutar programa)
        packet_data = bytes([
            SUB_CMD_EXECUTE_PROGRAM,
            0x00,  # Reservado
            program_count,
            program_number
        ])
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation
        )

