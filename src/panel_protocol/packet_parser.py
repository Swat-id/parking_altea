"""
Analizador de paquetes de respuesta del protocolo de paneles
"""

import struct
from typing import Optional, Dict
from .constants import (
    ID_CODE, PACKET_TYPE_RESPONSE, CARD_TYPE, RESPONSE_SUCCESS
)
from .checksum import verify_checksum


class PacketParser:
    """Analizador de paquetes de respuesta del protocolo"""
    
    @staticmethod
    def parse_response(packet: bytes) -> Optional[Dict]:
        """
        Analiza un paquete de respuesta recibido.
        
        Args:
            packet: Paquete completo recibido
            
        Returns:
            Dict con información del paquete o None si es inválido
            {
                'card_id': int,
                'command': int,
                'return_value': int,
                'success': bool,
                'packet_data': bytes,
                'raw_packet': bytes
            }
        """
        if len(packet) < 15:  # Tamaño mínimo del paquete
            return None
        
        # Verificar ID Code (primeros 4 bytes)
        if packet[0:4] != ID_CODE:
            return None
        
        # Leer longitud de red (bytes 4-5, little-endian)
        network_length = struct.unpack('<H', packet[4:6])[0]
        
        # Verificar que el paquete tenga el tamaño correcto
        expected_length = 4 + 2 + 2 + network_length  # ID + length + reserved + data
        if len(packet) < expected_length:
            return None
        
        # Leer Packet Type (byte 8)
        packet_type = packet[8]
        if packet_type != PACKET_TYPE_RESPONSE:
            return None
        
        # Leer Card Type (byte 9)
        card_type = packet[9]
        if card_type != CARD_TYPE:
            return None
        
        # Leer Card ID (byte 10)
        card_id = packet[10]
        
        # Leer Command Code (byte 11)
        command = packet[11]
        
        # Leer Return Value (byte 12)
        return_value = packet[12]
        
        # Extraer datos del paquete (desde Packet Type hasta antes del checksum)
        data_for_checksum = packet[8:8+network_length-2]
        
        # Leer checksum (últimos 2 bytes)
        received_checksum = packet[8+network_length-2:8+network_length]
        
        # Verificar checksum
        if not verify_checksum(data_for_checksum, received_checksum):
            return None
        
        # Extraer Packet Data (desde Return Value hasta antes del checksum)
        packet_data = packet[13:8+network_length-2] if network_length > 5 else b''
        
        return {
            'card_id': card_id,
            'command': command,
            'return_value': return_value,
            'success': return_value == RESPONSE_SUCCESS,
            'packet_data': packet_data,
            'raw_packet': packet
        }
    
    @staticmethod
    def is_success_response(packet: bytes) -> bool:
        """
        Verifica rápidamente si una respuesta indica éxito.
        
        Args:
            packet: Paquete de respuesta
            
        Returns:
            bool: True si es una respuesta de éxito válida
        """
        parsed = PacketParser.parse_response(packet)
        return parsed is not None and parsed['success']

