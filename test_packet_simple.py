#!/usr/bin/env python3
"""Script simple para validar construcción de paquete LLIURE"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from panel_protocol.packet_builder import PacketBuilder
from panel_protocol.constants import Color, FontSize

# Validar construcción de paquete para "LLIURE" en rojo, tamaño 16, ventana 0
print("=" * 80)
print("VALIDACIÓN: Paquete para 'LLIURE' en rojo, tamaño 16px, ventana 0")
print("=" * 80)

packet = PacketBuilder.build_send_text_packet(
    card_id=0x01,
    window_id=0,
    text="LLIURE",
    color=Color.RED,  # 0x01
    font_size=FontSize.SIZE_16,  # 0x02
    effect=0x00,  # Instantáneo
    alignment=0x00,  # Left Top
    speed=0x00,  # Más rápido
    stay_time=3,
    request_confirmation=True
)

print(f"\nPaquete generado ({len(packet)} bytes):")
print(" ".join(f"{b:02x}" for b in packet))

# Validar estructura
print("\n" + "-" * 80)
print("ESTRUCTURA DEL PAQUETE:")
print("-" * 80)

# ID Code
id_code = packet[0:4]
print(f"ID Code: {' '.join(f'{b:02x}' for b in id_code)} (esperado: ff ff ff ff)")

# Network length
network_length = int.from_bytes(packet[4:6], 'little')
print(f"Network length: {network_length:04x} ({network_length} bytes)")

# Packet Type
packet_type = packet[8]
print(f"Packet Type: 0x{packet_type:02x} (esperado: 0x68)")

# Card Type
card_type = packet[9]
print(f"Card Type: 0x{card_type:02x} (esperado: 0x32)")

# Card ID
card_id = packet[10]
print(f"Card ID: 0x{card_id:02x}")

# Command
command = packet[11]
print(f"Command: 0x{command:02x} (esperado: 0x7b)")

# Additional info
additional_info = packet[12]
print(f"Additional info: 0x{additional_info:02x} (esperado: 0x01)")

# Packet data
packet_data_start = 17
packet_data = packet[packet_data_start:-2]

print(f"\nPacket data ({len(packet_data)} bytes):")
print(" ".join(f"{b:02x}" for b in packet_data))

# Validar comando CC
cmd_cc = packet_data[0]
print(f"\nComando CC: 0x{cmd_cc:02x} (esperado: 0x02)")

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
print(f"Velocidad: 0x{speed:02x}")

# Tiempo espera
stay_time = int.from_bytes(packet_data[5:7], 'little')
print(f"Tiempo espera: {stay_time} segundos")

# Validar texto
text_start = 7
expected_text = "LLIURE"
expected_color_font = (Color.RED << 4) | FontSize.SIZE_16  # 0x12

print(f"\nTexto '{expected_text}':")
i = text_start
char_index = 0
while i < len(packet_data) - 3 and char_index < len(expected_text):
    char_byte = packet_data[i]
    color_font = packet_data[i+1]
    reserved = packet_data[i+2]
    
    expected_char = ord(expected_text[char_index])
    
    print(f"  '{expected_text[char_index]}': 0x{char_byte:02x} (esperado: 0x{expected_char:02x}), "
          f"color_font=0x{color_font:02x} (esperado: 0x{expected_color_font:02x}), "
          f"reserved=0x{reserved:02x}")
    
    if char_byte != expected_char:
        print(f"    ❌ ERROR: Carácter incorrecto")
    if color_font != expected_color_font:
        print(f"    ❌ ERROR: Color+Font incorrecto")
    if reserved != 0x00:
        print(f"    ❌ ERROR: Reservado incorrecto")
    
    i += 3
    char_index += 1

# Fin de texto
text_end = packet_data[-3:]
print(f"\nFin de texto: {' '.join(f'{b:02x}' for b in text_end)} (esperado: 00 00 00)")

# Checksum
checksum = packet[-2:]
print(f"Checksum: {' '.join(f'{b:02x}' for b in checksum)}")

print("\n" + "=" * 80)
print("✅ VALIDACIÓN COMPLETA")
print("=" * 80)

