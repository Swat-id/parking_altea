#!/usr/bin/env python3
"""
Verificar el cálculo del checksum
"""

import struct

# Paquete correcto del usuario
correct_hex = "ffffffff1b0000006832017b011600000002000005030300220039220030000000e101"
correct = bytes.fromhex(correct_hex)

print("=" * 80)
print("VERIFICACIÓN DEL CHECKSUM")
print("=" * 80)

# Datos para checksum: desde Packet Type (offset 8) hasta Packet Data (antes del checksum)
data_for_checksum = correct[8:-2]

print(f"\nDatos para checksum ({len(data_for_checksum)} bytes):")
print(" ".join(f"{b:02x}" for b in data_for_checksum))

# Calcular checksum
checksum_calc = sum(data_for_checksum) & 0xFFFF
checksum_expected = int.from_bytes(correct[-2:], 'little')

print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")
print(f"Checksum en paquete: 0x{checksum_expected:04x} ({checksum_expected})")
print(f"Diferencia: {checksum_expected - checksum_calc}")

# Desglosar los datos para checksum
print("\n" + "=" * 80)
print("DESGLOSE DE DATOS PARA CHECKSUM:")
print("=" * 80)

offset = 0
print(f"\n[{offset}] Packet Type: {data_for_checksum[offset]:02x}")
offset += 1

print(f"[{offset}] Card Type: {data_for_checksum[offset]:02x}")
offset += 1

print(f"[{offset}] Card ID: {data_for_checksum[offset]:02x}")
offset += 1

print(f"[{offset}] Command/Protocol: {data_for_checksum[offset]:02x}")
offset += 1

print(f"[{offset}] Additional Info: {data_for_checksum[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(data_for_checksum[offset:offset+4], 'little')
print(f"[{offset}-{offset+3}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

packet_data = data_for_checksum[offset:]
print(f"[{offset}-{len(data_for_checksum)-1}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")

# Calcular checksum paso a paso
print("\n" + "=" * 80)
print("CÁLCULO PASO A PASO:")
print("=" * 80)

checksum_step = 0
for i, byte in enumerate(data_for_checksum):
    checksum_step = (checksum_step + byte) & 0xFFFF
    if i < 10 or i >= len(data_for_checksum) - 10:
        print(f"  Byte {i:2d}: 0x{byte:02x} → Checksum acumulado: 0x{checksum_step:04x}")

print(f"\nChecksum final: 0x{checksum_step:04x} ({checksum_step})")
print(f"Checksum esperado: 0x{checksum_expected:04x} ({checksum_expected})")

# Verificar si el problema es que el Packet Data Length declarado (22) no coincide con el real (16)
print("\n" + "=" * 80)
print("ANÁLISIS DEL PROBLEMA:")
print("=" * 80)

print(f"\nPacket Data Length declarado: {packet_data_length} bytes")
print(f"Packet Data real: {len(packet_data)} bytes")
print(f"Diferencia: {packet_data_length - len(packet_data)} bytes")

if packet_data_length != len(packet_data):
    print("\n⚠️ PROBLEMA: El Packet Data Length declarado no coincide con la longitud real")
    print("   Esto puede causar que el panel rechace el paquete o calcule mal el checksum")
    print("\n   Solución: El Packet Data Length debe ser igual a la longitud real del Packet Data")

