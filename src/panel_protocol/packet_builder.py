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
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete completo de red según el protocolo.
        
        Formato según estructura de referencia (panel_protocol.py):
        - ID Code: 4 bytes (0xFF, 0xFF, 0xFF, 0xFF)
        - Network Length: 2 bytes (little-endian) - desde Packet Type hasta Checksum
        - Reserved: 2 bytes (0x00, 0x00)
        - Packet Type: 1 byte (0x68)
        - Card Type: 1 byte (0x32)
        - Card ID: 1 byte (0x01-0xFE o 0xFF)
        - Command/Protocol: 1 byte (0x7B) - directamente después del Card ID
        - Additional Info: 1 byte (0x01 o 0x00)
        - Packet Data Length: 4 bytes (little-endian) - Longitud del comando CC
        - Packet Data: Variable (comando CC)
        - Checksum: 2 bytes
        
        Args:
            card_id: ID de la tarjeta (0x01-0xFE) o 0xFF para broadcast
            command: Código de comando (0x7B para protocolo)
            packet_data: Datos del comando CC (sin incluir headers adicionales)
            request_confirmation: Si True, solicita confirmación (bit 0 = 1)
            
        Returns:
            bytes: Paquete completo listo para enviar
        """
        # Additional info: bit 0 = confirmación, bits 1-7 = 0
        additional_info = CONFIRMATION_REQUESTED if request_confirmation else NO_CONFIRMATION
        
        # Construir parte del paquete desde Packet Type hasta Additional Info
        # Según la estructura correcta del usuario:
        # Formato: Packet Type, Card Type, Card ID, Command, Additional Info
        # NO hay byte reservado después del Card ID
        packet_header = bytes([
            PACKET_TYPE_SEND,      # 0x68
            CARD_TYPE,             # 0x32
            card_id,               # 0x01-0xFE o 0xFF
            command,               # 0x7B (Protocol) - directamente después del Card ID
            additional_info        # 0x01 o 0x00 (Response/Additional Info)
        ])
        
        # Según la estructura correcta del usuario, el Packet Data Length es de 4 bytes, no 2
        # Después de Additional Info viene directamente:
        # - Packet data length (4 bytes, little-endian) - Longitud del comando CC
        packet_data_length = len(packet_data)
        packet_info = struct.pack('<I', packet_data_length)  # Packet data length (4 bytes, little-endian)
        
        # Datos completos para calcular checksum (desde Packet Type hasta Packet Data)
        # IMPORTANTE: El checksum se calcula sobre: Packet Type + Card Type + Card ID + Byte reservado + Command + Additional Info + Packet Data Length + Packet Data
        data_for_checksum = packet_header + packet_info + packet_data
        
        # Calcular checksum (suma desde Packet Type hasta Packet Data)
        # El checksum se calcula sobre todos los bytes desde Packet Type hasta Packet Data (sin incluir el checksum mismo)
        checksum = calculate_checksum(data_for_checksum)
        
        # Calcular longitud de red (desde Packet Type hasta Checksum)
        # Según la referencia panel_protocol.py, Network Length es de 2 bytes (little-endian)
        # Network Length = longitud desde Packet Type (incluido) hasta Checksum (incluido)
        # Esto incluye: Packet Type + Card Type + Card ID + Command + Additional Info + Packet Data Length + Packet Data + Checksum
        network_length = len(data_for_checksum) + len(checksum)
        
        # Construir paquete completo según estructura de referencia (panel_protocol.py):
        # - ID Code: 4 bytes (0xFF, 0xFF, 0xFF, 0xFF)
        # - Network Length: 2 bytes (little-endian) - desde Packet Type hasta Checksum
        # - Reserved: 2 bytes (0x00, 0x00)
        # - Packet Type hasta Checksum
        packet = (
            ID_CODE +                                    # 4 bytes: ID Code
            struct.pack('<H', network_length) +          # 2 bytes: Network Length (little-endian)
            b'\x00\x00' +                                # 2 bytes: Reserved
            data_for_checksum +                          # Packet Type + Card Type + Card ID + Command + Additional Info + Packet Data Length + Packet Data
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
        speed: int = 0x03,
        stay_time: int = 3,
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete para enviar texto a una ventana (CC=0x02).
        
        Args:
            card_id: ID de la tarjeta
            window_id: ID de la ventana (0-7)
            text: Texto a enviar
            color: Color del texto (0x01-0x07)
            font_size: Tamaño de fuente (0x00-0x07)
            effect: Efecto de texto (0=Draw, 11=Scroll left, 14=Continuous scroll left, etc.)
            alignment: Alineación horizontal (0=left, 1=center, 2=right)
            speed: Velocidad del efecto (1-100, más bajo = más rápido)
            stay_time: Tiempo de espera en segundos (para efectos no-scroll)
            request_confirmation: Si solicita confirmación
            
        Returns:
            bytes: Paquete completo
        """
        # Calcular byte de color + tamaño: (color << 4) | font_size
        color_font = (color << 4) | font_size
        
        # Validar y ajustar alignment (solo 0-2 según documentación CC=0x02)
        # 0=left, 1=center, 2=right
        if alignment > 2:
            # Convertir valores extendidos a valores simples
            # 0x04=LEFT_CENTER, 0x05=CENTER_CENTER, 0x06=RIGHT_CENTER -> extraer bits 0-1
            alignment = alignment & 0x03
            if alignment > 2:
                alignment = 1  # center por defecto
        
        # Validar speed (1-100 según documentación, 0 podría causar problemas)
        if speed < 1:
            speed = 3  # valor por defecto seguro
        elif speed > 100:
            speed = 100
        
        # Construir datos del comando CC (sin incluir la longitud)
        # Según documentación CC=0x02: CC, window_id, mode(effect), alignment, speed, stay_time
        command_data = bytes([
            SUB_CMD_SEND_TEXT,  # 0x02
            window_id,          # Número de ventana (0-7)
            effect,             # Mode/Efecto (códigos 0-70)
            alignment,          # Alineación (0-2)
            speed               # Velocidad (1-100)
        ])
        
        # Tiempo de espera (2 bytes, BIG-ENDIAN según doc: "High byte in the former")
        command_data += struct.pack('>H', stay_time)
        
        # Según el ejemplo exacto de la documentación (línea 47-68):
        # Formato para cada carácter: color_font + 0x00 + carácter
        # Ejemplo "hola" en rojo (0x10 = rojo, tamaño 8px):
        #   0x10, 0x00, 0x68  (h)
        #   0x10, 0x00, 0x6f  (o)
        #   0x10, 0x00, 0x6c  (l)
        #   0x10, 0x00, 0x61  (a)
        #   0x00, 0x00, 0x00  (fin de texto)
        if len(text) > 0:
            # Para cada carácter: color_font + 0x00 + carácter
            for char in text:
                command_data += bytes([color_font, 0x00, ord(char)])
            
            # Fin de texto: 3 bytes a 0x00
            command_data += b'\x00\x00\x00'
        else:
            # Si no hay texto, solo fin de texto
            command_data += b'\x00\x00\x00'
        
        # El packet_data es directamente el comando CC (sin incluir la longitud de 4 bytes)
        # La longitud se incluye en build_network_packet como "Packet data length"
        packet_data = command_data
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation
        )
    
    @staticmethod
    def build_static_text_packet(
        card_id: int,
        window_id: int,
        text: str,
        font_size: int,
        font_style: int = 0x00,
        alignment: int = 0x00,
        display_x: int = 0,
        display_y: int = 0,
        display_width: int = 64,
        display_height: int = 8,
        color_r: int = 255,
        color_g: int = 0,
        color_b: int = 0,
        request_confirmation: bool = True
    ) -> bytes:
        """
        Construye un paquete para enviar texto estático (comando 0x04).
        
        Según la documentación:
        - CC: 0x04 (1 byte)
        - Window NO: 0x00~0x07 (1 byte)
        - Data type: 0x01 (1 byte) - Simple text data
        - The level of alignment: 0~2 (1 byte) - 0: left, 1: center, 2: right
        - Display area X: 2 bytes (High byte in the former - big-endian según doc)
        - Display area Y: 2 bytes (High byte in the former - big-endian según doc)
        - Display area width: 2 bytes (High byte in the former - big-endian según doc)
        - Display area height: 2 bytes (High byte in the former - big-endian según doc)
        - Font: 1 byte - Bit0~3: font size, Bit4~6: font style, Bit7: Reserved
        - Text color R: 0~255 (1 byte)
        - Text color G: 0~255 (1 byte)
        - Text color B: 0~255 (1 byte)
        - Text: Variable length - Text string to the end of 0x00
        
        Args:
            card_id: ID de la tarjeta
            window_id: ID de la ventana (0x00~0x07)
            text: Texto a enviar
            font_size: Tamaño de fuente (0x00~0x07) - bits 0-3
            font_style: Estilo de fuente (0x00~0x07) - bits 4-6
            alignment: Alineación (0: left, 1: center, 2: right)
            display_x: Coordenada X del área de visualización
            display_y: Coordenada Y del área de visualización
            display_width: Ancho del área de visualización
            display_height: Alto del área de visualización
            color_r: Componente rojo del color (0~255)
            color_g: Componente verde del color (0~255)
            color_b: Componente azul del color (0~255)
            request_confirmation: Si solicita confirmación
            
        Returns:
            bytes: Paquete completo
        """
        # Validar window_id
        if window_id < 0 or window_id > 7:
            raise ValueError(f"window_id debe estar entre 0 y 7, recibido: {window_id}")
        
        # Validar alignment
        if alignment < 0 or alignment > 2:
            raise ValueError(f"alignment debe estar entre 0 y 2, recibido: {alignment}")
        
        # Validar font_size
        if font_size < 0 or font_size > 7:
            raise ValueError(f"font_size debe estar entre 0 y 7, recibido: {font_size}")
        
        # Validar font_style
        if font_style < 0 or font_style > 7:
            raise ValueError(f"font_style debe estar entre 0 y 7, recibido: {font_style}")
        
        # Construir datos del comando CC=0x04
        command_data = bytes([
            CMD_STATIC_TEXT,      # 0x04: Static text
            window_id,            # Window NO: 0x00~0x07
            0x01,                 # Data type: 0x01 (Simple text data)
            alignment             # The level of alignment: 0~2
        ])
        
        # Display area X, Y, width, height (2 bytes cada uno)
        # NOTA: La documentación dice "High byte in the former" lo que sugiere big-endian,
        # pero el protocolo general usa little-endian. Usaremos big-endian según la doc.
        command_data += struct.pack('>H', display_x)      # Display area X (big-endian)
        command_data += struct.pack('>H', display_y)       # Display area Y (big-endian)
        command_data += struct.pack('>H', display_width)  # Display area width (big-endian)
        command_data += struct.pack('>H', display_height) # Display area height (big-endian)
        
        # Font: Bit0~3: font size, Bit4~6: font style, Bit7: Reserved (0)
        font_byte = (font_size & 0x0F) | ((font_style & 0x07) << 4)
        command_data += bytes([font_byte])
        
        # Text color R, G, B (1 byte cada uno)
        command_data += bytes([
            color_r & 0xFF,  # Text color R: 0~255
            color_g & 0xFF,  # Text color G: 0~255
            color_b & 0xFF   # Text color B: 0~255
        ])
        
        # Text: Variable length - Text string to the end of 0x00
        command_data += text.encode('ascii', errors='ignore') + b'\x00'
        
        # El comando 0x04 es un comando directo, no un subcomando de 0x7B
        # Por lo tanto, usamos CMD_STATIC_TEXT directamente como command
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_STATIC_TEXT,
            packet_data=command_data,
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

