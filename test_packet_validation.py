#!/usr/bin/env python3
"""
Script para validar la construcción de paquetes según los ejemplos del protocolo
"""

import sys
sys.path.insert(0, 'src')

from panel_protocol.packet_builder import PacketBuilder
from panel_protocol.constants import Color, FontSize

def bytes_to_hex(data: bytes, format='hex') -> str:
    """Convierte bytes a formato legible"""
    if format == 'hex':
        return ' '.join(f'{b:02x}' for b in data)
    elif format == 'c':
        return ', '.join(f'0x{b:02x}' for b in data)
    return str(data)

def validate_example_hola():
    """Valida el ejemplo de envío de 'hola' en rojo a ventana 0"""
    print("=" * 80)
    print("VALIDACIÓN: Enviar 'hola' en rojo, tamaño 8px, ventana 0")
    print("=" * 80)
    
    # Parámetros según el ejemplo
    # Color rojo = 0x01, Tamaño 8px = 0x00
    # color_font = (0x01 << 4) | 0x00 = 0x10
    
    packet = PacketBuilder.build_send_text_packet(
        card_id=0x01,
        window_id=0,  # Ventana 0 (aunque el ejemplo dice ventana 1, el byte es 0x00)
        text="hola",
        color=Color.RED,  # 0x01
        font_size=FontSize.SIZE_8,  # 0x00
        effect=0x00,  # Instantáneo
        alignment=0x00,  # Left Top
        speed=0x03,  # Velocidad efecto
        stay_time=3,  # Tiempo espera
        request_confirmation=True
    )
    
    print(f"\nPaquete generado ({len(packet)} bytes):")
    print(bytes_to_hex(packet, 'c'))
    print(f"\nFormato hex:")
    print(bytes_to_hex(packet))
    
    # Validar estructura básica
    print("\n" + "-" * 80)
    print("VALIDACIÓN DE ESTRUCTURA:")
    print("-" * 80)
    
    # ID Code (4 bytes)
    id_code = packet[0:4]
    print(f"ID Code: {bytes_to_hex(id_code)} (esperado: ff ff ff ff)")
    assert id_code == b'\xff\xff\xff\xff', f"ID Code incorrecto: {id_code}"
    
    # Network data length (2 bytes, little-endian)
    network_length = int.from_bytes(packet[4:6], 'little')
    print(f"Network length: {network_length:04x} (bytes 4-5)")
    
    # Reservation (2 bytes)
    reservation = packet[6:8]
    print(f"Reservation: {bytes_to_hex(reservation)} (esperado: 00 00)")
    
    # Packet Type
    packet_type = packet[8]
    print(f"Packet Type: 0x{packet_type:02x} (esperado: 0x68)")
    assert packet_type == 0x68, f"Packet Type incorrecto: 0x{packet_type:02x}"
    
    # Card Type
    card_type = packet[9]
    print(f"Card Type: 0x{card_type:02x} (esperado: 0x32)")
    assert card_type == 0x32, f"Card Type incorrecto: 0x{card_type:02x}"
    
    # Card ID
    card_id = packet[10]
    print(f"Card ID: 0x{card_id:02x} (esperado: 0x01)")
    
    # Command
    command = packet[11]
    print(f"Command: 0x{command:02x} (esperado: 0x7b)")
    assert command == 0x7b, f"Command incorrecto: 0x{command:02x}"
    
    # Additional info
    additional_info = packet[12]
    print(f"Additional info: 0x{additional_info:02x} (esperado: 0x01 para confirmación)")
    
    # Packet data length (4 bytes, little-endian)
    packet_data_length = int.from_bytes(packet[13:17], 'little')
    print(f"Packet data length: {packet_data_length} bytes")
    
    # Packet data
    packet_data_start = 17
    packet_data = packet[packet_data_start:-2]  # Excluir checksum
    
    print(f"\nPacket data ({len(packet_data)} bytes):")
    print(bytes_to_hex(packet_data, 'c'))
    
    # Validar comando CC
    cmd_cc = packet_data[0]
    print(f"\nComando CC: 0x{cmd_cc:02x} (esperado: 0x02)")
    assert cmd_cc == 0x02, f"Comando CC incorrecto: 0x{cmd_cc:02x}"
    
    # Ventana
    window = packet_data[1]
    print(f"Ventana: {window} (esperado: 0)")
    
    # Efecto
    effect = packet_data[2]
    print(f"Efecto: 0x{effect:02x} (esperado: 0x00)")
    
    # Alineación
    alignment = packet_data[3]
    print(f"Alineación: 0x{alignment:02x} (esperado: 0x00)")
    
    # Velocidad
    speed = packet_data[4]
    print(f"Velocidad: 0x{speed:02x} (esperado: 0x03)")
    
    # Tiempo espera (2 bytes, little-endian)
    stay_time = int.from_bytes(packet_data[5:7], 'little')
    print(f"Tiempo espera: {stay_time} segundos (esperado: 3)")
    
    # Texto
    text_start = 7
    text_bytes = packet_data[text_start:-3]  # Excluir los 3 bytes finales
    print(f"\nTexto codificado ({len(text_bytes)} bytes):")
    print(bytes_to_hex(text_bytes, 'c'))
    
    # Validar caracteres
    expected_text = "hola"
    char_index = 0
    i = 0
    while i < len(text_bytes) and char_index < len(expected_text):
        char_byte = text_bytes[i]
        color_font = text_bytes[i+1]
        reserved = text_bytes[i+2]
        
        expected_char = ord(expected_text[char_index])
        expected_color_font = (Color.RED << 4) | FontSize.SIZE_8  # 0x10
        
        print(f"  Carácter {char_index}: 0x{char_byte:02x} (esperado: 0x{expected_char:02x} '{expected_text[char_index]}')")
        print(f"    Color+Font: 0x{color_font:02x} (esperado: 0x{expected_color_font:02x})")
        print(f"    Reservado: 0x{reserved:02x} (esperado: 0x00)")
        
        assert char_byte == expected_char, f"Carácter incorrecto en posición {char_index}"
        assert color_font == expected_color_font, f"Color+Font incorrecto: 0x{color_font:02x}"
        assert reserved == 0x00, f"Byte reservado incorrecto: 0x{reserved:02x}"
        
        i += 3
        char_index += 1
    
    # Fin de texto
    text_end = packet_data[-3:]
    print(f"\nFin de texto: {bytes_to_hex(text_end)} (esperado: 00 00 00)")
    assert text_end == b'\x00\x00\x00', f"Fin de texto incorrecto: {text_end}"
    
    # Checksum
    checksum = packet[-2:]
    print(f"\nChecksum: {bytes_to_hex(checksum)}")
    
    print("\n✅ VALIDACIÓN COMPLETA: Paquete correcto según el ejemplo")
    print("=" * 80)

def validate_lliure():
    """Valida el envío de 'LLIURE' en rojo, tamaño 16px, ventana 0"""
    print("\n" + "=" * 80)
    print("VALIDACIÓN: Enviar 'LLIURE' en rojo, tamaño 16px, ventana 0")
    print("=" * 80)
    
    # Parámetros
    # Color rojo = 0x01, Tamaño 16px = 0x02
    # color_font = (0x01 << 4) | 0x02 = 0x10 | 0x02 = 0x12
    
    packet = PacketBuilder.build_send_text_packet(
        card_id=0x01,
        window_id=0,
        text="LLIURE",
        color=Color.RED,  # 0x01
        font_size=FontSize.SIZE_16,  # 0x02
        effect=0x00,  # Instantáneo
        alignment=0x00,  # Left Top
        speed=0x00,  # Velocidad más rápida
        stay_time=3,
        request_confirmation=True
    )
    
    print(f"\nPaquete generado ({len(packet)} bytes):")
    print(bytes_to_hex(packet, 'c'))
    print(f"\nFormato hex:")
    print(bytes_to_hex(packet))
    
    # Validar color_font
    packet_data = packet[17:-2]  # Excluir header y checksum
    text_start = 7  # Después de: cmd, window, effect, alignment, speed, stay_time(2)
    
    expected_color_font = (Color.RED << 4) | FontSize.SIZE_16  # 0x12
    print(f"\nColor+Font esperado: 0x{expected_color_font:02x} (rojo=0x01, tamaño16=0x02)")
    
    # Validar cada carácter
    expected_text = "LLIURE"
    i = text_start
    char_index = 0
    print(f"\nValidando texto '{expected_text}':")
    while i < len(packet_data) - 3 and char_index < len(expected_text):
        char_byte = packet_data[i]
        color_font = packet_data[i+1]
        reserved = packet_data[i+2]
        
        expected_char = ord(expected_text[char_index])
        
        print(f"  '{expected_text[char_index]}': 0x{char_byte:02x}, color_font=0x{color_font:02x}, reserved=0x{reserved:02x}")
        
        assert char_byte == expected_char, f"Carácter incorrecto: 0x{char_byte:02x} != 0x{expected_char:02x}"
        assert color_font == expected_color_font, f"Color+Font incorrecto: 0x{color_font:02x} != 0x{expected_color_font:02x}"
        assert reserved == 0x00, f"Reservado incorrecto: 0x{reserved:02x}"
        
        i += 3
        char_index += 1
    
    print("\n✅ VALIDACIÓN COMPLETA: Paquete 'LLIURE' correcto")
    print("=" * 80)

if __name__ == '__main__':
    try:
        validate_example_hola()
        validate_lliure()
        print("\n✅ TODAS LAS VALIDACIONES PASARON")
    except AssertionError as e:
        print(f"\n❌ ERROR DE VALIDACIÓN: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

