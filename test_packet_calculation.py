#!/usr/bin/env python3
"""
Verificar el cálculo correcto del paquete
"""

import struct

# Paquete correcto según usuario
correct_hex = "ffffffff1b000000683215007b011000000002000005030300220039220030000000110202"
correct = bytes.fromhex(correct_hex)

print("=" * 80)
print("ANÁLISIS DEL PAQUETE CORRECTO")
print("=" * 80)

offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in correct[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(correct[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Network Length: {network_length:04x} ({network_length} bytes)")
offset += 2

print(f"[{offset:2d}-{offset+1:2d}] Reserved: {' '.join(f'{b:02x}' for b in correct[offset:offset+2])}")
offset += 2

print(f"[{offset:2d}] Packet Type: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Byte reservado: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {correct[offset]:02x}")
offset += 1

# El usuario dice que el Packet Data Length está en bytes 10-11 (2 bytes)
# Pero según la documentación debería ser 4 bytes
# Verificamos ambas opciones
packet_data_length_2bytes = int.from_bytes(correct[offset:offset+2], 'little')
packet_data_length_4bytes = int.from_bytes(correct[offset:offset+4], 'little')
print(f"\n[{offset:2d}-{offset+1:2d}] Packet Data Length (2 bytes): {packet_data_length_2bytes:04x} ({packet_data_length_2bytes} bytes)")
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length (4 bytes): {packet_data_length_4bytes:08x} ({packet_data_length_4bytes} bytes)")

# Verificar qué coincide con los datos reales
packet_data_start = offset + 4  # Si usamos 4 bytes
packet_data = correct[packet_data_start:-2]
print(f"\nPacket Data real: {len(packet_data)} bytes")
print(f"  Datos: {' '.join(f'{b:02x}' for b in packet_data)}")

# Calcular checksum
data_for_checksum = correct[8:-2]  # Desde Packet Type hasta Packet Data
checksum_calc = sum(data_for_checksum) & 0xFFFF
checksum_expected = int.from_bytes(correct[-2:], 'little')
print(f"\nChecksum calculado: 0x{checksum_calc:04x}")
print(f"Checksum en paquete: 0x{checksum_expected:04x}")
print(f"¿Coincide? {checksum_calc == checksum_expected}")

