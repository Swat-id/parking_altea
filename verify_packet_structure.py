#!/usr/bin/env python3
"""
Verificar la estructura del paquete actual vs el correcto
"""

# Paquete actual (del log)
current_hex = "ffffffff1b0000006832017b011000000002000005030300220039220030000000e101"
current = bytes.fromhex(current_hex)

# Paquete correcto según usuario
correct_hex = "ffffffff1b0000006832017b011600000002000005030300220039220030000000e101"
correct = bytes.fromhex(correct_hex)

print("=" * 80)
print("COMPARACIÓN DE PAQUETES")
print("=" * 80)

print("\n📦 PAQUETE ACTUAL:")
print(" ".join(f"{b:02x}" for b in current))
print(f"Longitud: {len(current)} bytes")

print("\n✅ PAQUETE CORRECTO:")
print(" ".join(f"{b:02x}" for b in correct))
print(f"Longitud: {len(correct)} bytes")

print("\n" + "=" * 80)
print("DIFERENCIAS:")
print("=" * 80)

# Comparar byte por byte
for i in range(min(len(current), len(correct))):
    if current[i] != correct[i]:
        print(f"  Posición {i:2d}: Actual={current[i]:02x}, Correcto={correct[i]:02x}")

# Analizar Packet Data Length
print("\n" + "=" * 80)
print("ANÁLISIS DE PACKET DATA LENGTH:")
print("=" * 80)

# En el paquete actual, Packet Data Length está en bytes 13-16
packet_data_length_current = int.from_bytes(current[13:17], 'little')
packet_data_length_correct = int.from_bytes(correct[13:17], 'little')

print(f"\nPacket Data Length actual: {packet_data_length_current} bytes (0x{packet_data_length_current:08x})")
print(f"Packet Data Length correcto: {packet_data_length_correct} bytes (0x{packet_data_length_correct:08x})")

# Analizar el comando CC real
packet_data_current = current[17:-2]
packet_data_correct = correct[17:-2]

print(f"\nPacket Data actual: {len(packet_data_current)} bytes")
print(f"  {' '.join(f'{b:02x}' for b in packet_data_current)}")

print(f"\nPacket Data correcto: {len(packet_data_correct)} bytes")
print(f"  {' '.join(f'{b:02x}' for b in packet_data_correct)}")

print(f"\n¿Coinciden los datos? {'✓ SÍ' if packet_data_current == packet_data_correct else '✗ NO'}")

if packet_data_current != packet_data_correct:
    print("\nDiferencias en Packet Data:")
    for i in range(min(len(packet_data_current), len(packet_data_correct))):
        if packet_data_current[i] != packet_data_correct[i]:
            print(f"  Posición {i:2d}: Actual={packet_data_current[i]:02x}, Correcto={packet_data_correct[i]:02x}")

# Verificar si el problema es solo el Packet Data Length declarado
if packet_data_current == packet_data_correct:
    print("\n✅ El Packet Data es idéntico, solo el Packet Data Length declarado es diferente")
    print(f"   Actual declara: {packet_data_length_current} bytes")
    print(f"   Correcto declara: {packet_data_length_correct} bytes")
    print(f"   Real tiene: {len(packet_data_current)} bytes")
    print(f"   → El problema es que estamos declarando {packet_data_length_current} cuando deberíamos declarar {len(packet_data_current)}")
