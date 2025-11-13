#!/usr/bin/env python3
"""
Analizar el paquete actual vs el correcto
"""

# Paquete actual (incorrecto)
current = bytes.fromhex("ffffffff1b0000006832ff7b011000000002000005030300220039220030000000df02")

# Paquete correcto según usuario
correct = bytes.fromhex("ffffffff1b000000683215007b011000000002000005030300220039220030000000110202")

print("=" * 80)
print("ANÁLISIS DE PAQUETES")
print("=" * 80)

print("\n📦 PAQUETE ACTUAL (incorrecto):")
print(" ".join(f"{b:02x}" for b in current))
print(f"Longitud: {len(current)} bytes")

print("\n✅ PAQUETE CORRECTO:")
print(" ".join(f"{b:02x}" for b in correct))
print(f"Longitud: {len(correct)} bytes")

print("\n" + "=" * 80)
print("DIFERENCIAS:")
print("=" * 80)

# Comparar byte por byte
print("\nByte por byte:")
for i in range(min(len(current), len(correct))):
    if current[i] != correct[i]:
        print(f"  Posición {i:2d}: Actual={current[i]:02x}, Correcto={correct[i]:02x}")

print("\n" + "=" * 80)
print("ESTRUCTURA DEL PAQUETE CORRECTO:")
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

print(f"[{offset:2d}] Command: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {correct[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(correct[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

print(f"[{offset:2d}-{offset+len(correct)-offset-2:2d}] Packet Data: {' '.join(f'{b:02x}' for b in correct[offset:-2])}")
print(f"[{len(correct)-2:2d}-{len(correct)-1:2d}] Checksum: {' '.join(f'{b:02x}' for b in correct[-2:])}")

