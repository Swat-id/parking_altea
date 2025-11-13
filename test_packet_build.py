#!/usr/bin/env python3
"""
Test para verificar la construcción correcta del paquete
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from panel_protocol.packet_builder import PacketBuilder
from panel_protocol.constants import Color

# Construir paquete para "90" en verde, tamaño 16, ventana 0
packet = PacketBuilder.build_send_text_packet(
    card_id=0xFF,  # Broadcast
    window_id=0,
    text="90",
    color=Color.GREEN,  # 0x02
    font_size=2,  # 16px = 0x02
    effect=0x00,
    alignment=5,  # CENTER_CENTER
    speed=0x03,
    stay_time=3,
    request_confirmation=True
)

print("=" * 80)
print("PAQUETE CONSTRUIDO")
print("=" * 80)
print(f"\nPaquete completo ({len(packet)} bytes):")
print(" ".join(f"{b:02x}" for b in packet))
print()

# Desglose
offset = 0
print(f"[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in packet[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(packet[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Network Length: {network_length:04x} ({network_length} bytes)")
offset += 2

print(f"[{offset:2d}-{offset+1:2d}] Reserved: {' '.join(f'{b:02x}' for b in packet[offset:offset+2])}")
offset += 2

print(f"[{offset:2d}] Packet Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Byte reservado: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {packet[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(packet[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Packet Data Length: {packet_data_length:04x} ({packet_data_length} bytes)")
offset += 2

packet_data = packet[offset:-2]
print(f"[{offset:2d}-{len(packet)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"  Longitud real: {len(packet_data)} bytes")
print(f"  Longitud declarada: {packet_data_length} bytes")
print(f"  ¿Coinciden? {len(packet_data) == packet_data_length}")

checksum = int.from_bytes(packet[-2:], 'little')
print(f"[{len(packet)-2:2d}-{len(packet)-1:2d}] Checksum: {checksum:04x} ({checksum})")

# Verificar checksum
data_for_checksum = packet[8:-2]  # Desde Packet Type hasta Packet Data
checksum_calc = sum(data_for_checksum) & 0xFFFF
print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")
print(f"Checksum en paquete: 0x{checksum:04x} ({checksum})")
print(f"¿Coinciden? {checksum_calc == checksum}")

# Verificar Network Length
network_length_calc = len(data_for_checksum) + 2  # +2 para el checksum
print(f"\nNetwork Length calculado: {network_length_calc} bytes (0x{network_length_calc:04x})")
print(f"Network Length en paquete: {network_length} bytes (0x{network_length:04x})")
print(f"¿Coinciden? {network_length_calc == network_length}")

