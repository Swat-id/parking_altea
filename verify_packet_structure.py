#!/usr/bin/env python3
"""
Verificar la estructura del paquete actual vs el correcto
"""

import struct

# Paquete actual (del log)
current_hex = "ffffffff1b0000006832ff7b011000000002000005030300220039220030000000df02"
current = bytes.fromhex(current_hex)

# Paquete correcto según usuario
correct_hex = "ffffffff1b000000683215007b011000000002000005030300220039220030000000110202"
correct = bytes.fromhex(correct_hex)

print("=" * 80)
print("ANÁLISIS DETALLADO")
print("=" * 80)

print("\n📦 PAQUETE ACTUAL:")
print(" ".join(f"{b:02x}" for b in current))
print(f"Longitud: {len(current)} bytes")

print("\n✅ PAQUETE CORRECTO:")
print(" ".join(f"{b:02x}" for b in correct))
print(f"Longitud: {len(correct)} bytes")

print("\n" + "=" * 80)
print("DESGLOSE DEL PAQUETE ACTUAL:")
print("=" * 80)

offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in current[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(current[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Network Length: {network_length:04x} ({network_length} bytes)")
offset += 2

print(f"[{offset:2d}-{offset+1:2d}] Reserved: {' '.join(f'{b:02x}' for b in current[offset:offset+2])}")
offset += 2

print(f"[{offset:2d}] Packet Type: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {current[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(current[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

packet_data = current[offset:-2]
print(f"[{offset:2d}-{len(current)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"[{len(current)-2:2d}-{len(current)-1:2d}] Checksum: {' '.join(f'{b:02x}' for b in current[-2:])}")

print("\n" + "=" * 80)
print("DESGLOSE DEL PAQUETE CORRECTO:")
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

# Aquí está la diferencia - hay un byte extra en el paquete correcto
if offset < len(correct):
    print(f"[{offset:2d}] Byte extra: {correct[offset]:02x}")
    offset += 1

print(f"[{offset:2d}] Command: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {correct[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(correct[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

packet_data = correct[offset:-2]
print(f"[{offset:2d}-{len(correct)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"[{len(correct)-2:2d}-{len(correct)-1:2d}] Checksum: {' '.join(f'{b:02x}' for b in correct[-2:])}")

print("\n" + "=" * 80)
print("DIFERENCIAS CLAVE:")
print("=" * 80)

# Comparar sección por sección
print("\n1. Card ID:")
print(f"   Actual: 0x{current[10]:02x} (0xFF = broadcast)")
print(f"   Correcto: 0x{correct[10]:02x} (0x15)")

print("\n2. Byte después de Card ID:")
print(f"   Actual: No existe (siguiente byte es Command)")
print(f"   Correcto: 0x{correct[11]:02x} (0x00)")

print("\n3. Command:")
print(f"   Actual: 0x{current[11]:02x}")
print(f"   Correcto: 0x{correct[12]:02x}")

print("\n4. Checksum:")
print(f"   Actual: {' '.join(f'{b:02x}' for b in current[-2:])}")
print(f"   Correcto: {' '.join(f'{b:02x}' for b in correct[-2:])}")

