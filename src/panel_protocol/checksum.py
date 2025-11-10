"""
Módulo para cálculo de checksum del protocolo de paneles
"""


def calculate_checksum(data: bytes) -> bytes:
    """
    Calcula el checksum de 16 bits para los datos del protocolo.
    
    El checksum es la suma de todos los bytes desde "Packet type" hasta "Packet data".
    Si la suma excede 0xFFFF, se toma solo el valor de 16 bits.
    
    Args:
        data: Bytes desde Packet Type hasta Packet Data (sin incluir checksum)
        
    Returns:
        bytes: Checksum en formato little-endian (2 bytes: low byte, high byte)
        
    Example:
        >>> data = bytes([0x68, 0x32, 0x01, 0x7b, 0x01, ...])
        >>> checksum = calculate_checksum(data)
        >>> # checksum = b'\\x6b\\x01' (por ejemplo)
    """
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFFFF  # Mantener solo 16 bits
    
    # Retornar en formato little-endian (low byte primero)
    return checksum.to_bytes(2, 'little')


def verify_checksum(data: bytes, received_checksum: bytes) -> bool:
    """
    Verifica que el checksum recibido coincida con el calculado.
    
    Args:
        data: Bytes desde Packet Type hasta Packet Data
        received_checksum: Checksum recibido (2 bytes, little-endian)
        
    Returns:
        bool: True si el checksum es válido, False en caso contrario
    """
    calculated = calculate_checksum(data)
    return calculated == received_checksum

