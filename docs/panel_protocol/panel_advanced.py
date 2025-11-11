#!/usr/bin/env python3
"""
Módulo avanzado para paneles LED
Funcionalidades adicionales: imágenes, creación de ventanas, cambio de programas, etc.
Mantiene retrocompatibilidad total con panel_protocol.py y panel_backend.py
"""

import struct
from typing import List, Optional, Tuple
from enum import IntEnum
from panel_protocol import PanelProtocol


class ImageFormat(IntEnum):
    """Formatos de imagen disponibles"""
    GIF_FILE_DATA = 0x01        # Datos del archivo GIF
    GIF_FILE_REFERENCE = 0x02   # Referencia a archivo GIF en el panel
    PACKAGE_REFERENCE = 0x03    # Referencia a package en el panel
    SIMPLE_FORMAT = 0x04        # Formato simple de imagen


class ImageMode(IntEnum):
    """Modos de visualización de imagen"""
    DRAW = 0x00           # Dibujar directamente
    CENTER = 0x00         # Centrar
    ZOOM = 0x01           # Zoom
    STRETCH = 0x02        # Estirar
    TILE = 0x03           # Mosaico


class PanelAdvanced(PanelProtocol):
    """
    Clase extendida con funcionalidades avanzadas
    Hereda de PanelProtocol para mantener compatibilidad
    """
    
    # Comandos adicionales
    CMD_CREATE_WINDOWS = 0x01
    CMD_SEND_IMAGE = 0x03
    CMD_STATIC_TEXT = 0x04
    CMD_SEND_CLOCK = 0x05
    CMD_EXIT_SHOW = 0x06
    CMD_SAVE_CLEAR = 0x07
    CMD_SELECT_PROGRAM = 0x08
    
    def build_image_packet(
        self,
        window_number: int,
        image_filename: str,
        image_format: ImageFormat = ImageFormat.GIF_FILE_REFERENCE,
        mode: ImageMode = ImageMode.DRAW,
        speed: int = 0x01,
        stay_time: int = 0x0003,
        x_position: int = 0x0000,
        y_position: int = 0x0000
    ) -> bytes:
        """
        Construye un paquete para enviar imagen a una ventana
        
        Args:
            window_number: Número de ventana (0-7)
            image_filename: Nombre del archivo de imagen (ej: "test.gif")
            image_format: Formato de la imagen
            mode: Modo de visualización
            speed: Velocidad de efecto
            stay_time: Tiempo de espera (2 bytes, high byte first)
            x_position: Posición X (relativa a la ventana)
            y_position: Posición Y (relativa a la ventana)
            
        Returns:
            Paquete completo en bytes listo para enviar
        """
        # Construir datos del comando (CC = 0x03)
        command_data = bytearray()
        command_data.append(self.CMD_SEND_IMAGE)  # CC
        command_data.append(window_number)         # Número de ventana
        command_data.append(mode)                  # Modo
        command_data.append(speed)                 # Velocidad
        command_data.extend(struct.pack('>H', stay_time))  # Tiempo espera (big-endian)
        command_data.append(image_format)          # Formato de imagen
        command_data.extend(struct.pack('>H', x_position))  # Posición X (big-endian)
        command_data.extend(struct.pack('>H', y_position))  # Posición Y (big-endian)
        
        # Agregar nombre del archivo (ASCII + null terminator)
        command_data.extend(image_filename.encode('ascii'))
        command_data.append(0x00)  # Null terminator
        
        # Construir packet data
        packet_data = bytearray()
        packet_data.append(self.PACKET_TYPE)
        packet_data.append(self.CARD_TYPE)
        packet_data.append(self.CARD_ID)
        packet_data.append(self.PROTOCOL_CODE)
        packet_data.append(self.CONFIRMATION_FLAG)
        
        # Longitud del comando
        command_length = len(command_data)
        packet_data.extend(struct.pack('<I', command_length))
        
        # Agregar datos del comando
        packet_data.extend(command_data)
        
        # Calcular checksum
        checksum = self.calculate_checksum(packet_data)
        packet_data.extend(checksum)
        
        # Construir paquete completo
        full_packet = bytearray()
        full_packet.extend(self.ID_CODE)
        
        # Network data length
        network_length = len(packet_data)
        full_packet.extend(struct.pack('<H', network_length))
        
        # Reservado
        full_packet.extend([0x00, 0x00])
        
        # Agregar packet data
        full_packet.extend(packet_data)
        
        return bytes(full_packet)
    
    def send_image(
        self,
        window_number: int,
        image_filename: str,
        image_format: ImageFormat = ImageFormat.GIF_FILE_REFERENCE,
        mode: ImageMode = ImageMode.DRAW,
        speed: int = 0x01,
        stay_time: int = 0x0003,
        x_position: int = 0x0000,
        y_position: int = 0x0000,
        verbose: bool = True
    ) -> bool:
        """
        Envía una imagen al panel LED
        
        Args:
            window_number: Ventana destino (0-7)
            image_filename: Nombre del archivo (ej: "logo.gif")
            image_format: Formato de la imagen
            mode: Modo de visualización
            speed: Velocidad del efecto
            stay_time: Tiempo de permanencia
            x_position: Posición X
            y_position: Posición Y
            verbose: Mostrar detalles
            
        Returns:
            True si fue exitoso
        """
        packet = self.build_image_packet(
            window_number=window_number,
            image_filename=image_filename,
            image_format=image_format,
            mode=mode,
            speed=speed,
            stay_time=stay_time,
            x_position=x_position,
            y_position=y_position
        )
        
        response = self.send_packet(packet, verbose)
        return response is not None
    
    def build_create_windows_packet(
        self,
        windows: List[Tuple[int, int, int, int]]
    ) -> bytes:
        """
        Construye paquete para crear/dividir ventanas
        
        Args:
            windows: Lista de tuplas (x, y, width, height) para cada ventana
                    Ejemplo: [(0, 0, 64, 8), (0, 8, 64, 8)]
            
        Returns:
            Paquete completo en bytes
        """
        # Validar máximo 8 ventanas
        if len(windows) > 8:
            raise ValueError("Maximum 8 windows allowed")
        
        # Construir datos del comando (CC = 0x01)
        command_data = bytearray()
        command_data.append(self.CMD_CREATE_WINDOWS)  # CC
        command_data.append(len(windows))             # Número de ventanas
        
        # Agregar coordenadas de cada ventana
        for x, y, width, height in windows:
            command_data.extend(struct.pack('>H', x))       # X (big-endian)
            command_data.extend(struct.pack('>H', y))       # Y (big-endian)
            command_data.extend(struct.pack('>H', width))   # Width (big-endian)
            command_data.extend(struct.pack('>H', height))  # Height (big-endian)
        
        # Construir packet data
        packet_data = bytearray()
        packet_data.append(self.PACKET_TYPE)
        packet_data.append(self.CARD_TYPE)
        packet_data.append(self.CARD_ID)
        packet_data.append(self.PROTOCOL_CODE)
        packet_data.append(self.CONFIRMATION_FLAG)
        
        # Longitud del comando
        command_length = len(command_data)
        packet_data.extend(struct.pack('<I', command_length))
        
        # Agregar datos del comando
        packet_data.extend(command_data)
        
        # Calcular checksum
        checksum = self.calculate_checksum(packet_data)
        packet_data.extend(checksum)
        
        # Construir paquete completo
        full_packet = bytearray()
        full_packet.extend(self.ID_CODE)
        
        network_length = len(packet_data)
        full_packet.extend(struct.pack('<H', network_length))
        full_packet.extend([0x00, 0x00])
        full_packet.extend(packet_data)
        
        return bytes(full_packet)
    
    def create_windows(
        self,
        windows: List[Tuple[int, int, int, int]],
        verbose: bool = True
    ) -> bool:
        """
        Crea/divide ventanas en el panel
        
        Args:
            windows: Lista de ventanas como tuplas (x, y, width, height)
                    Ejemplo: [(0, 0, 64, 8), (0, 8, 64, 8)]
            verbose: Mostrar detalles
            
        Returns:
            True si fue exitoso
        """
        packet = self.build_create_windows_packet(windows)
        response = self.send_packet(packet, verbose)
        return response is not None
    
    def build_select_program_packet(
        self,
        program_number: int
    ) -> bytes:
        """
        Construye paquete para seleccionar/cambiar programa
        
        Args:
            program_number: Número de programa (1-254)
            
        Returns:
            Paquete completo en bytes
        """
        if not 1 <= program_number <= 254:
            raise ValueError("Program number must be between 1 and 254")
        
        # Construir datos del comando (CC = 0x08)
        command_data = bytearray()
        command_data.append(self.CMD_SELECT_PROGRAM)  # CC
        command_data.append(0x00)                     # Reservado
        command_data.append(0x01)                     # Cantidad de programas
        command_data.append(program_number)           # Número de programa
        
        # Construir packet data
        packet_data = bytearray()
        packet_data.append(self.PACKET_TYPE)
        packet_data.append(self.CARD_TYPE)
        packet_data.append(self.CARD_ID)
        packet_data.append(self.PROTOCOL_CODE)
        packet_data.append(self.CONFIRMATION_FLAG)
        
        # Longitud del comando
        command_length = len(command_data)
        packet_data.extend(struct.pack('<I', command_length))
        
        # Agregar datos del comando
        packet_data.extend(command_data)
        
        # Calcular checksum
        checksum = self.calculate_checksum(packet_data)
        packet_data.extend(checksum)
        
        # Construir paquete completo
        full_packet = bytearray()
        full_packet.extend(self.ID_CODE)
        
        network_length = len(packet_data)
        full_packet.extend(struct.pack('<H', network_length))
        full_packet.extend([0x00, 0x00])
        full_packet.extend(packet_data)
        
        return bytes(full_packet)
    
    def select_program(
        self,
        program_number: int,
        verbose: bool = True
    ) -> bool:
        """
        Selecciona y ejecuta un programa guardado en el panel
        
        Args:
            program_number: Número de programa (1-254)
            verbose: Mostrar detalles
            
        Returns:
            True si fue exitoso
        """
        packet = self.build_select_program_packet(program_number)
        response = self.send_packet(packet, verbose)
        return response is not None
    
    def build_save_data_packet(
        self,
        save: bool = True
    ) -> bytes:
        """
        Construye paquete para guardar o limpiar datos en flash
        
        Args:
            save: True para guardar, False para limpiar
            
        Returns:
            Paquete completo en bytes
        """
        # Construir datos del comando (CC = 0x07)
        command_data = bytearray()
        command_data.append(self.CMD_SAVE_CLEAR)      # CC
        command_data.append(0x00 if save else 0x01)   # 0x00=guardar, 0x01=limpiar
        command_data.extend([0x00, 0x00])             # Reservado
        
        # Construir packet data
        packet_data = bytearray()
        packet_data.append(self.PACKET_TYPE)
        packet_data.append(self.CARD_TYPE)
        packet_data.append(self.CARD_ID)
        packet_data.append(self.PROTOCOL_CODE)
        packet_data.append(self.CONFIRMATION_FLAG)
        
        command_length = len(command_data)
        packet_data.extend(struct.pack('<I', command_length))
        packet_data.extend(command_data)
        
        checksum = self.calculate_checksum(packet_data)
        packet_data.extend(checksum)
        
        full_packet = bytearray()
        full_packet.extend(self.ID_CODE)
        network_length = len(packet_data)
        full_packet.extend(struct.pack('<H', network_length))
        full_packet.extend([0x00, 0x00])
        full_packet.extend(packet_data)
        
        return bytes(full_packet)
    
    def save_data_to_flash(
        self,
        verbose: bool = True
    ) -> bool:
        """
        Guarda los datos actuales en la memoria flash del panel
        
        Args:
            verbose: Mostrar detalles
            
        Returns:
            True si fue exitoso
        """
        packet = self.build_save_data_packet(save=True)
        response = self.send_packet(packet, verbose)
        return response is not None
    
    def clear_flash_data(
        self,
        verbose: bool = True
    ) -> bool:
        """
        Limpia los datos de la memoria flash del panel
        
        Args:
            verbose: Mostrar detalles
            
        Returns:
            True si fue exitoso
        """
        packet = self.build_save_data_packet(save=False)
        response = self.send_packet(packet, verbose)
        return response is not None


# Funciones de conveniencia para uso rápido

def quick_send_image(
    ip: str,
    window: int,
    image_filename: str,
    stay_time: int = 3,
    verbose: bool = False
) -> bool:
    """
    Función rápida para enviar imagen
    
    Args:
        ip: IP del panel
        window: Número de ventana
        image_filename: Nombre del archivo (ej: "logo.gif")
        stay_time: Tiempo de visualización en segundos
        verbose: Mostrar detalles
        
    Returns:
        True si fue exitoso
    """
    panel = PanelAdvanced(ip)
    return panel.send_image(
        window_number=window,
        image_filename=image_filename,
        stay_time=stay_time,
        verbose=verbose
    )


def quick_create_windows(
    ip: str,
    windows: List[Tuple[int, int, int, int]],
    verbose: bool = False
) -> bool:
    """
    Función rápida para crear ventanas
    
    Args:
        ip: IP del panel
        windows: Lista de ventanas (x, y, width, height)
        verbose: Mostrar detalles
        
    Returns:
        True si fue exitoso
    """
    panel = PanelAdvanced(ip)
    return panel.create_windows(windows, verbose)


def quick_select_program(
    ip: str,
    program_number: int,
    verbose: bool = False
) -> bool:
    """
    Función rápida para cambiar programa
    
    Args:
        ip: IP del panel
        program_number: Número de programa (1-254)
        verbose: Mostrar detalles
        
    Returns:
        True si fue exitoso
    """
    panel = PanelAdvanced(ip)
    return panel.select_program(program_number, verbose)


if __name__ == "__main__":
    print("Módulo Avanzado para Paneles LED")
    print("=" * 60)
    print("\nFuncionalidades adicionales:")
    print("  • Envío de imágenes (CC=0x03)")
    print("  • Creación de ventanas (CC=0x01)")
    print("  • Cambio de programas (CC=0x08)")
    print("  • Guardar/limpiar datos en flash (CC=0x07)")
    print("\nImporta este módulo para funciones avanzadas")
    print("Mantiene compatibilidad total con panel_protocol y panel_backend")

