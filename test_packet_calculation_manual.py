#!/usr/bin/env python3
"""
Cálculo manual del paquete para verificar
"""

import struct

# Simular construcción del paquete para "90"
# Comando CC
command_data = bytes([
    0x02,  # SUB_CMD_SEND_TEXT
    0x00,  # window_id
    0x00,  # effect
    0x05,  # alignment (CENTER_CENTER)
    0x03,  # speed
])
command_data += struct.pack('<H', 3)  # stay_time = 3
# Texto "90" con color_font = 0x22 (verde, tamaño 16)
command_data += bytes([0x22, 0x00, 0x39])  # '9'
command_data += bytes([0x22, 0x00, 0x30])  # '0'
command_data += b'\x00\x00\x00'  # Fin de texto

print("=" * 80)
print("CÁLCULO MANUAL DEL PAQUETE")
print("=" * 80)

print(f"\nComando CC: {len(command_data)} bytes")
print(" ".join(f"{b:02x}" for b in command_data))

# Packet Header
packet_header = bytes([
    0x68,  # PACKET_TYPE_SEND
    0x32,  # CARD_TYPE
    0x01,  # card_id
    0x00,  # Byte reservado
    0x7B,  # command
    0x01,  # additional_info
])

print(f"\nPacket Header: {len(packet_header)} bytes")
print(" ".join(f"{b:02x}" for b in packet_header))

# Packet Data Length (2 bytes)
packet_data_length = len(command_data)
packet_info = struct.pack('<H', packet_data_length)

print(f"\nPacket Data Length: {packet_data_length} bytes (0x{packet_data_length:04x})")
print(" ".join(f"{b:02x}" for b in packet_info))

# Datos para checksum
data_for_checksum = packet_header + packet_info + command_data
print(f"\nDatos para checksum: {len(data_for_checksum)} bytes")
print(" ".join(f"{b:02x}" for b in data_for_checksum))

# Checksum
checksum = sum(data_for_checksum) & 0xFFFF
checksum_bytes = struct.pack('<H', checksum)
print(f"\nChecksum calculado: 0x{checksum:04x} ({checksum})")
print(" ".join(f"{b:02x}" for b in checksum_bytes))

# Network Length
network_length = len(data_for_checksum) + len(checksum_bytes)
print(f"\nNetwork Length: {network_length} bytes (0x{network_length:04x})")

# Paquete completo
packet = (
    bytes([0xFF, 0xFF, 0xFF, 0xFF]) +  # ID Code
    struct.pack('<H', network_length) +  # Network Length
    b'\x00\x00' +  # Reserved
    data_for_checksum +  # Packet Type hasta Packet Data
    checksum_bytes  # Checksum
)

print(f"\nPaquete completo: {len(packet)} bytes")
print(" ".join(f"{b:02x}" for b in packet))

print("\n" + "=" * 80)
print("COMPARACIÓN CON PAQUETE DEL LOG:")
print("=" * 80)
log_packet = bytes.fromhex("ffffffff1a000000683201007b01100002000005030300220039220030000000e101")
print(f"\nPaquete del log: {len(log_packet)} bytes")
print(" ".join(f"{b:02x}" for b in log_packet))

print("\nDiferencias:")
if len(packet) != len(log_packet):
    print(f"  Longitud: Calculado={len(packet)}, Log={len(log_packet)}")

# Comparar Network Length
network_length_log = int.from_bytes(log_packet[4:6], 'little')
print(f"  Network Length: Calculado={network_length} (0x{network_length:04x}), Log={network_length_log} (0x{network_length_log:04x})")

# Comparar Packet Data Length
packet_data_length_log = int.from_bytes(log_packet[14:16], 'little')
print(f"  Packet Data Length: Calculado={packet_data_length} (0x{packet_data_length:04x}), Log={packet_data_length_log} (0x{packet_data_length_log:04x})")

# Comparar Checksum
checksum_log = int.from_bytes(log_packet[-2:], 'little')
print(f"  Checksum: Calculado={checksum} (0x{checksum:04x}), Log={checksum_log} (0x{checksum_log:04x})")

