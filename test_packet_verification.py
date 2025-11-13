#!/usr/bin/env python3
"""
Verificar que el Packet Data Length coincida con la longitud real
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from panel_protocol.packet_builder import PacketBuilder
from panel_protocol.constants import Color

# Construir paquete para "90"
packet = PacketBuilder.build_send_text_packet(
    card_id=0x01,
    window_id=0,
    text="90",
    color=Color.GREEN,
    font_size=2,
    effect=0x00,
    alignment=5,
    speed=0x03,
    stay_time=3,
    request_confirmation=True
)

print("=" * 80)
print("VERIFICACIÓN DEL PAQUETE GENERADO")
print("=" * 80)

print(f"\nPaquete completo ({len(packet)} bytes):")
print(" ".join(f"{b:02x}" for b in packet))

# Analizar
offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in packet[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(packet[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Network Length: {network_length:08x} ({network_length} bytes)")
offset += 4

print(f"[{offset:2d}] Packet Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command/Protocol: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {packet[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(packet[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

packet_data = packet[offset:-2]
print(f"[{offset:2d}-{len(packet)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"  Longitud real: {len(packet_data)} bytes")
print(f"  Longitud declarada: {packet_data_length} bytes")
print(f"  ¿Coinciden? {'✓ SÍ' if len(packet_data) == packet_data_length else '✗ NO - Diferencia: ' + str(packet_data_length - len(packet_data)) + ' bytes'}")

checksum = int.from_bytes(packet[-2:], 'little')
print(f"[{len(packet)-2:2d}-{len(packet)-1:2d}] Checksum: {checksum:04x} ({checksum})")

# Verificar checksum
data_for_checksum = packet[8:-2]  # Desde Packet Type hasta Packet Data
checksum_calc = sum(data_for_checksum) & 0xFFFF
print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")
print(f"Checksum en paquete: 0x{checksum:04x} ({checksum})")
print(f"¿Coinciden? {'✓ SÍ' if checksum_calc == checksum else '✗ NO'}")

# Comparar con paquete correcto del usuario
correct_hex = "ffffffff1b0000006832017b011600000002000005030300220039220030000000e101"
correct = bytes.fromhex(correct_hex)

print("\n" + "=" * 80)
print("COMPARACIÓN CON PAQUETE CORRECTO DEL USUARIO:")
print("=" * 80)

if len(packet) == len(correct):
    print(f"✓ Longitud coincide: {len(packet)} bytes")
else:
    print(f"✗ Longitud diferente: Generado={len(packet)}, Correcto={len(correct)}")

# Comparar byte por byte
differences = []
for i in range(min(len(packet), len(correct))):
    if packet[i] != correct[i]:
        differences.append((i, packet[i], correct[i]))

if differences:
    print(f"\n✗ {len(differences)} diferencias encontradas:")
    for pos, actual, expected in differences[:10]:  # Mostrar solo las primeras 10
        print(f"  Posición {pos:2d}: Actual={actual:02x}, Esperado={expected:02x}")
    if len(differences) > 10:
        print(f"  ... y {len(differences) - 10} más")
else:
    print("\n✓ Paquete idéntico al correcto")

