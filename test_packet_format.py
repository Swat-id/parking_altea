#!/usr/bin/env python3
"""
Script para verificar el formato correcto del paquete según la documentación
"""

# Ejemplo de la documentación para "hola" en rojo a ventana 0:
# 0xff,0xff,0xff,0xff,           //ID code
# 0x21,0x00,                     // Length desde Packet Type 0x68 hasta Checksum
# 0x00,0x00,                    // Reservado
# 0x68,                         // Packet Type
# 0x32,                        // Code Type
# 0x01,                                 // Card ID
# 0x7b,                                 // Tipo protocolo
# 0x01,                                 // Devolver respuesta
# 0x16,0x00,0x00,0x00,                 // Length del Comando CC 0x02. Formato: LowByte HighByte
# 0x02,0x00,0x00,0x00,0x03,0x00,0x03,0x10,0x00,0x68,0x10,0x00,0x6f,0x10,0x00,0x6c,0x10,0x00,0x61,0x00,0x00,0x00,
# 0x19,0x03 //Checksum

example_packet = bytes([
    0xff, 0xff, 0xff, 0xff,  # ID Code
    0x21, 0x00,              # Network Length (33 bytes desde Packet Type hasta Checksum)
    0x00, 0x00,              # Reserved
    0x68,                    # Packet Type
    0x32,                    # Card Type
    0x01,                    # Card ID
    0x7b,                    # Command (Protocol)
    0x01,                    # Additional Info (confirmation)
    0x16, 0x00, 0x00, 0x00,  # Packet Data Length (22 bytes, 4 bytes little-endian)
    # Comando CC 0x02 (22 bytes):
    0x02,                    # CC Command (SEND_TEXT)
    0x00,                    # Window ID
    0x00,                    # Effect
    0x00,                    # Alignment
    0x03,                    # Speed
    0x00, 0x03,              # Stay Time (little-endian)
    0x10, 0x00, 0x68,        # h: color_font(0x10), 0x00, char(0x68)
    0x10, 0x00, 0x6f,        # o: color_font(0x10), 0x00, char(0x6f)
    0x10, 0x00, 0x6c,        # l: color_font(0x10), 0x00, char(0x6c)
    0x10, 0x00, 0x61,        # a: color_font(0x10), 0x00, char(0x61)
    0x00, 0x00, 0x00,        # End of text
    0x19, 0x03               # Checksum
])

print("=" * 80)
print("EJEMPLO DE DOCUMENTACIÓN - Paquete para 'hola' en rojo")
print("=" * 80)
print(f"\nPaquete completo ({len(example_packet)} bytes):")
print(" ".join(f"{b:02x}" for b in example_packet))
print()

# Desglose
print("Estructura:")
print(f"  ID Code: {' '.join(f'{b:02x}' for b in example_packet[0:4])}")
print(f"  Network Length: {example_packet[4]:02x} {example_packet[5]:02x} = {int.from_bytes(example_packet[4:6], 'little')} bytes")
print(f"  Reserved: {example_packet[6]:02x} {example_packet[7]:02x}")
print(f"  Packet Type: {example_packet[8]:02x}")
print(f"  Card Type: {example_packet[9]:02x}")
print(f"  Card ID: {example_packet[10]:02x}")
print(f"  Command: {example_packet[11]:02x}")
print(f"  Additional Info: {example_packet[12]:02x}")
print(f"  Packet Data Length: {' '.join(f'{b:02x}' for b in example_packet[13:17])} = {int.from_bytes(example_packet[13:17], 'little')} bytes")
print(f"  Command Data: {' '.join(f'{b:02x}' for b in example_packet[17:39])}")
print(f"  Checksum: {' '.join(f'{b:02x}' for b in example_packet[39:41])}")

# Verificar checksum
data_for_checksum = example_packet[8:39]  # Desde Packet Type hasta Packet Data
checksum_calc = sum(data_for_checksum) & 0xFFFF
checksum_expected = int.from_bytes(example_packet[39:41], 'little')
print(f"\nChecksum calculado: 0x{checksum_calc:04x}")
print(f"Checksum en paquete: 0x{checksum_expected:04x}")
print(f"¿Coincide? {checksum_calc == checksum_expected}")

