"""
Constructor de paquetes del protocolo de paneles CPower

Formato CPower (correcto, usado por SDK Java):
    A5 + DeviceID (ASCII) + 00 + PacketType + CardType + CardID + ProtocolCode + 
    AdditionalInfo + PackedDataLength + PO + TP + PacketData + Checksum

Formato Legacy (antiguo, NO funciona con paneles CPower):
    FFFFFFFF + NetworkLength + Reserved + PacketType + ... + Checksum
"""

import struct
from typing import List, Tuple, Optional
from .constants import (
    CPOWER_START_MARKER, CPOWER_SEPARATOR,
    PACKET_TYPE_SEND, CARD_TYPE, CMD_PROTOCOL_CONTROL,
    SUB_CMD_CREATE_WINDOW, SUB_CMD_SEND_TEXT, SUB_CMD_SEND_IMAGE,
    SUB_CMD_EXECUTE_PROGRAM, CONFIRMATION_REQUESTED, NO_CONFIRMATION,
    CARD_ID_BROADCAST
)
from .checksum import calculate_checksum


class PacketBuilder:
    """Constructor de paquetes del protocolo de comunicación con paneles CPower"""
    
    @staticmethod
    def build_cpower_packet(
        device_id: str,
        card_id: int,
        command: int,
        packet_data: bytes,
        request_confirmation: bool = True,
        packet_number: int = 0x00,
        last_packet_number: int = 0x00
    ) -> bytes:
        """
        Construye un paquete CPower completo (formato correcto).
        
        Formato CPower:
        - Start Marker: 1 byte (0xA5)
        - Device ID: Variable (ASCII, ej: "00606ed81e7e")
        - Separator: 1 byte (0x00)
        - Packet Type: 1 byte (0x68)
        - Card Type: 1 byte (0x32)
        - Card ID: 1 byte (0x01-0xFE o 0xFF para broadcast)
        - Protocol Code: 1 byte (0x7B)
        - Additional Info: 1 byte (0x01 o 0x00)
        - Packed Data Length: 2 bytes (little-endian)
        - Packet Number (PO): 1 byte
        - Last Packet Number (TP): 1 byte
        - Packet Data (CC...): Variable
        - Checksum: 2 bytes (little-endian)
        
        Args:
            device_id: ID del dispositivo en ASCII (ej: "00606ed81e7e")
            card_id: ID de la tarjeta (0x01-0xFE) o 0xFF para broadcast
            command: Código de comando (0x7B para protocolo)
            packet_data: Datos del comando CC
            request_confirmation: Si True, solicita confirmación
            packet_number: Número de paquete actual
            last_packet_number: Número del último paquete
            
        Returns:
            bytes: Paquete completo listo para enviar
        """
        additional_info = CONFIRMATION_REQUESTED if request_confirmation else NO_CONFIRMATION
        
        packet_header = bytes([
            PACKET_TYPE_SEND,      # 0x68
            CARD_TYPE,             # 0x32
            card_id,               # 0x01-0xFE o 0xFF
            command,               # 0x7B (Protocol)
            additional_info        # 0x01 o 0x00
        ])
        
        packet_data_length = len(packet_data)
        packed_length = struct.pack('<H', packet_data_length)
        packet_numbers = bytes([packet_number, last_packet_number])
        
        data_for_checksum = packet_header + packed_length + packet_numbers + packet_data
        checksum = calculate_checksum(data_for_checksum)
        
        packet = (
            bytes([CPOWER_START_MARKER]) +               # 1 byte: 0xA5
            device_id.encode('ascii') +                  # Variable: Device ID
            bytes([CPOWER_SEPARATOR]) +                  # 1 byte: 0x00
            data_for_checksum +                          # Header + Length + PO + TP + Data
            checksum +                                   # 2 bytes: Checksum
            bytes([0xAE])                                # 1 byte: Terminador CPower
        )
        
        return packet
    
    @staticmethod
    def build_network_packet(
        card_id: int,
        command: int,
        packet_data: bytes,
        request_confirmation: bool = True,
        packet_number: int = 0x00,
        last_packet_number: int = 0x00,
        device_id: Optional[str] = None
    ) -> bytes:
        """
        Construye un paquete completo de red.
        
        Si device_id está presente, usa el formato CPower (correcto).
        Si no, usa el formato legacy (para compatibilidad, pero NO funciona con paneles CPower).
        
        Args:
            card_id: ID de la tarjeta (0x01-0xFE) o 0xFF para broadcast
            command: Código de comando (0x7B para protocolo)
            packet_data: Datos del comando CC
            request_confirmation: Si True, solicita confirmación
            packet_number: Número de paquete actual
            last_packet_number: Número del último paquete
            device_id: ID del dispositivo CPower (si se proporciona, usa formato CPower)
            
        Returns:
            bytes: Paquete completo listo para enviar
        """
        if device_id:
            return PacketBuilder.build_cpower_packet(
                device_id=device_id,
                card_id=card_id,
                command=command,
                packet_data=packet_data,
                request_confirmation=request_confirmation,
                packet_number=packet_number,
                last_packet_number=last_packet_number
            )
        
        # Formato legacy (mantener para compatibilidad, pero NO funciona con paneles CPower)
        from .constants import ID_CODE_LEGACY as ID_CODE
        
        additional_info = CONFIRMATION_REQUESTED if request_confirmation else NO_CONFIRMATION
        
        packet_header = bytes([
            PACKET_TYPE_SEND,
            CARD_TYPE,
            card_id,
            command,
            additional_info
        ])
        
        packet_data_length = len(packet_data)
        packed_length = struct.pack('<H', packet_data_length)
        packet_numbers = bytes([packet_number, last_packet_number])
        
        data_for_checksum = packet_header + packed_length + packet_numbers + packet_data
        checksum = calculate_checksum(data_for_checksum)
        network_length = len(data_for_checksum) + len(checksum)
        
        packet = (
            ID_CODE +
            struct.pack('<H', network_length) +
            b'\x00\x00' +
            data_for_checksum +
            checksum
        )
        
        return packet
    
    @staticmethod
    def build_create_window_packet(
        card_id: int,
        windows: List[Tuple[int, int, int, int]],
        request_confirmation: bool = True,
        device_id: Optional[str] = None
    ) -> bytes:
        """
        Construye un paquete para crear ventanas en el panel.
        
        Args:
            card_id: ID de la tarjeta
            windows: Lista de tuplas (x, y, width, height) para cada ventana
            request_confirmation: Si solicita confirmación
            device_id: ID del dispositivo CPower (requerido para formato correcto)
            
        Returns:
            bytes: Paquete completo
        """
        packet_data = bytes([SUB_CMD_CREATE_WINDOW, len(windows)])
        
        for x, y, width, height in windows:
            packet_data += struct.pack('>HHHH', x, y, width, height)
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation,
            device_id=device_id
        )
    
    @staticmethod
    def build_send_text_packet(
        card_id: int,
        window_id: int,
        text: str,
        color: int,
        font_size: int,
        effect: int = 0xFF,
        alignment: int = 0x00,
        speed: int = 0x05,
        stay_time: int = 50,
        request_confirmation: bool = True,
        device_id: Optional[str] = None
    ) -> bytes:
        """
        Construye un paquete para enviar texto a una ventana (CC=0x02).
        
        Args:
            card_id: ID de la tarjeta (usar CARD_ID_BROADCAST=0xFF para broadcast)
            window_id: ID de la ventana (0-7)
            text: Texto a enviar
            color: Color del texto (0x01-0x07)
            font_size: Tamaño de fuente (0x00-0x07)
            effect: Efecto de texto (0xFF=random/default, 0=Draw, 11=Scroll left, etc.)
            alignment: Alineación horizontal (0=left, 1=center, 2=right)
            speed: Velocidad del efecto (1-100, más bajo = más rápido)
            stay_time: Tiempo de espera (en décimas de segundo para SDK Java)
            request_confirmation: Si solicita confirmación
            device_id: ID del dispositivo CPower (requerido para formato correcto)
            
        Returns:
            bytes: Paquete completo
        """
        color_font = (color << 4) | font_size
        
        if alignment > 2:
            alignment = alignment & 0x03
            if alignment > 2:
                alignment = 1
        
        if speed < 1:
            speed = 5
        elif speed > 100:
            speed = 100
        
        command_data = bytes([
            SUB_CMD_SEND_TEXT,  # 0x02
            window_id,          # Número de ventana (0-7)
            effect,             # Mode/Efecto (0xFF para default)
            alignment,          # Alineación (0-2)
            speed               # Velocidad (1-100)
        ])
        
        command_data += struct.pack('>H', stay_time)
        
        if len(text) > 0:
            for char in text:
                command_data += bytes([color_font, 0x00, ord(char)])
            command_data += b'\x00\x00\x00'
        else:
            command_data += b'\x00\x00\x00'
        
        packet_data = command_data
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation,
            device_id=device_id
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
        request_confirmation: bool = True,
        device_id: Optional[str] = None
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
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_STATIC_TEXT,
            packet_data=command_data,
            request_confirmation=request_confirmation,
            device_id=device_id
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
        request_confirmation: bool = True,
        device_id: Optional[str] = None
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
            device_id: ID del dispositivo CPower
            
        Returns:
            bytes: Paquete completo
        """
        packet_data = bytes([
            SUB_CMD_SEND_IMAGE,
            window_id,
            draw_mode,
            speed
        ])
        
        packet_data += struct.pack('>H', stay_time)
        packet_data += bytes([file_reference])
        packet_data += struct.pack('>HH', x, y)
        packet_data += filename.encode('ascii') + b'\x00'
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation,
            device_id=device_id
        )
    
    @staticmethod
    def build_execute_program_packet(
        card_id: int,
        program_number: int,
        program_count: int = 1,
        request_confirmation: bool = True,
        device_id: Optional[str] = None
    ) -> bytes:
        """
        Construye un paquete para ejecutar un programa guardado.
        
        Args:
            card_id: ID de la tarjeta
            program_number: Número del programa a ejecutar (1-N)
            program_count: Cantidad de programas (por defecto 1)
            request_confirmation: Si solicita confirmación
            device_id: ID del dispositivo CPower
            
        Returns:
            bytes: Paquete completo
        """
        packet_data = bytes([
            SUB_CMD_EXECUTE_PROGRAM,
            0x00,
            program_count,
            program_number
        ])
        
        return PacketBuilder.build_network_packet(
            card_id=card_id,
            command=CMD_PROTOCOL_CONTROL,
            packet_data=packet_data,
            request_confirmation=request_confirmation,
            device_id=device_id
        )

