#!/usr/bin/env python3
"""
Analizar los problemas del paquete actual
"""

# Paquete actual (del log)
current_hex = "ffffffff1a0000006832ff007b01100002000005030300220039220030000000df02"
current = bytes.fromhex(current_hex)

# Paquete correcto según usuario
correct_hex = "ffffffff1b000000683215007b011300020000050303002200392200300000000e02"
# Nota: El usuario dice que el Packet Data Length debe ser 13 00 (19 bytes)
# y el checksum debe ser 0e 02 (526)

print("=" * 80)
print("ANÁLISIS DEL PAQUETE ACTUAL")
print("=" * 80)

offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in current[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(current[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Network Length: {network_length:04x} ({network_length} bytes) - DEBERÍA SER 0x1b (27 bytes)")
offset += 2

print(f"[{offset:2d}-{offset+1:2d}] Reserved: {' '.join(f'{b:02x}' for b in current[offset:offset+2])}")
offset += 2

print(f"[{offset:2d}] Packet Type: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Byte reservado: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command: {current[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {current[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(current[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Packet Data Length: {packet_data_length:04x} ({packet_data_length} bytes) - DEBERÍA SER 0x13 (19 bytes)")
offset += 2

packet_data = current[offset:-2]
print(f"[{offset:2d}-{len(current)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"  Longitud real del Packet Data: {len(packet_data)} bytes")

checksum = int.from_bytes(current[-2:], 'little')
print(f"[{len(current)-2:2d}-{len(current)-1:2d}] Checksum: {checksum:04x} ({checksum}) - DEBERÍA SER 0x020e (526)")

print("\n" + "=" * 80)
print("PROBLEMAS IDENTIFICADOS:")
print("=" * 80)
print("\n1. Network Length: Está en 0x1a (26) pero debería ser 0x1b (27)")
print("   - Diferencia: -1 byte")
print("\n2. Packet Data Length: Está en 0x1000 (16) pero debería ser 0x13 (19)")
print("   - Diferencia: -3 bytes")
print("   - El Packet Data real tiene 19 bytes, pero estamos declarando 16")
print("\n3. Checksum: Está en 0x02df (735) pero debería ser 0x020e (526)")
print("   - El checksum no se está recalculando correctamente")

print("\n" + "=" * 80)
print("CÁLCULO CORRECTO:")
print("=" * 80)

# Calcular correctamente
# Packet Data real: desde el byte después de Packet Data Length hasta antes del checksum
packet_data_start = 14  # Después de: ID(4) + Network(2) + Reserved(2) + Packet Type(1) + Card Type(1) + Card ID(1) + Reserved(1) + Command(1) + Additional(1) + Packet Data Length(2) = 15 bytes, offset 14
packet_data_real = current[packet_data_start:-2]
print(f"\nPacket Data real: {len(packet_data_real)} bytes")
print(f"  Datos: {' '.join(f'{b:02x}' for b in packet_data_real)}")

# Calcular checksum correcto
# Desde Packet Type (offset 8) hasta Packet Data (antes del checksum)
data_for_checksum = current[8:-2]
checksum_calc = sum(data_for_checksum) & 0xFFFF
print(f"\nDatos para checksum ({len(data_for_checksum)} bytes):")
print(f"  {' '.join(f'{b:02x}' for b in data_for_checksum)}")
print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")

# Calcular Network Length correcto
# Desde Packet Type (offset 8) hasta Checksum (últimos 2 bytes)
network_length_calc = len(data_for_checksum) + 2  # +2 para el checksum
print(f"\nNetwork Length calculado: {network_length_calc} bytes (0x{network_length_calc:04x})")

