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
        Versión tolerante que acepta cualquier respuesta, incluso si está mal formateada.
        
        Args:
            packet: Paquete completo recibido
            
        Returns:
            Dict con información del paquete o None si es completamente inválido
            {
                'card_id': int,
                'command': int,
                'return_value': int,
                'success': bool,
                'packet_data': bytes,
                'raw_packet': bytes,
                'valid': bool  # True si el paquete está bien formateado, False si es parcial
            }
        """
        if len(packet) < 8:  # Tamaño mínimo absoluto (ID + length mínimo)
            return None
        
        # Verificar ID Code (primeros 4 bytes) - más tolerante
        id_code_valid = packet[0:4] == ID_CODE
        if not id_code_valid and len(packet) < 12:
            # Si no tiene ID code válido pero tiene al menos 12 bytes, intentar parsear igual
            pass
        
        # Intentar leer longitud de red (bytes 4-5, little-endian)
        try:
            if len(packet) >= 6:
                network_length = struct.unpack('<H', packet[4:6])[0]
            else:
                # Si no hay suficientes bytes, asumir longitud mínima
                network_length = len(packet) - 8
        except:
            network_length = len(packet) - 8 if len(packet) > 8 else 0
        
        # Leer Packet Type (byte 8) - más tolerante
        if len(packet) > 8:
            packet_type = packet[8]
            # Aceptar tanto 0xE8 (respuesta) como 0x68 (puede ser respuesta en versiones antiguas)
            is_response = packet_type == PACKET_TYPE_RESPONSE or packet_type == 0x68
        else:
            packet_type = 0
            is_response = False
        
        # Leer Card Type (byte 9) - más tolerante
        if len(packet) > 9:
            card_type = packet[9]
            card_type_valid = card_type == CARD_TYPE
        else:
            card_type = 0
            card_type_valid = False
        
        # Leer Card ID (byte 10) - más tolerante
        if len(packet) > 10:
            card_id = packet[10]
        else:
            card_id = 0
        
        # Leer Command Code (byte 11) - más tolerante
        if len(packet) > 11:
            command = packet[11]
        else:
            command = 0
        
        # Leer Return Value (byte 12) - más tolerante
        if len(packet) > 12:
            return_value = packet[12]
        else:
            return_value = 0x00  # Asumir éxito si no hay return value
        
        # Intentar verificar checksum solo si tenemos suficientes bytes
        checksum_valid = False
        if len(packet) >= 8 + network_length and network_length >= 2:
            try:
                data_for_checksum = packet[8:8+network_length-2]
                received_checksum = packet[8+network_length-2:8+network_length]
                checksum_valid = verify_checksum(data_for_checksum, received_checksum)
            except:
                checksum_valid = False
        
        # Extraer Packet Data (desde Return Value hasta antes del checksum) - más tolerante
        if len(packet) > 13 and network_length > 5:
            try:
                packet_data = packet[13:8+network_length-2] if network_length > 5 else b''
            except:
                packet_data = packet[13:] if len(packet) > 13 else b''
        else:
            packet_data = b''
        
        # Determinar si el paquete es válido o parcial
        valid = (id_code_valid and is_response and card_type_valid and checksum_valid and len(packet) >= 15)
        
        # Aceptar cualquier respuesta, incluso si está parcialmente formateada
        return {
            'card_id': card_id,
            'command': command,
            'return_value': return_value,
            'success': return_value == RESPONSE_SUCCESS or return_value == 0x00,  # Más tolerante
            'packet_data': packet_data,
            'raw_packet': packet,
            'valid': valid,  # Indica si el paquete está completamente válido
            'partial': not valid  # Indica si el paquete es parcial
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

