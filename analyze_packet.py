#!/usr/bin/env python3
"""
Script para analizar el paquete enviado y compararlo con el formato esperado
"""

# Paquete enviado (del log)
packet_hex = "ffffffff1b0000006832ff7b011000000002000005030300220039220030000000df02"
packet = bytes.fromhex(packet_hex)

print("=" * 80)
print("ANÁLISIS DEL PAQUETE ENVIADO")
print("=" * 80)
print(f"\nPaquete completo ({len(packet)} bytes):")
print(" ".join(f"{b:02x}" for b in packet))
print()

# Desglose del paquete
offset = 0

# ID Code (4 bytes)
id_code = packet[offset:offset+4]
print(f"ID Code: {' '.join(f'{b:02x}' for b in id_code)} (esperado: ff ff ff ff)")
offset += 4

# Network Length (2 bytes, little-endian)
network_length = int.from_bytes(packet[offset:offset+2], 'little')
print(f"Network Length: {network_length:04x} ({network_length} bytes)")
offset += 2

# Reserved (2 bytes)
reserved = packet[offset:offset+2]
print(f"Reserved: {' '.join(f'{b:02x}' for b in reserved)} (esperado: 00 00)")
offset += 2

# Packet Type
packet_type = packet[offset]
print(f"Packet Type: 0x{packet_type:02x} (esperado: 0x68)")
offset += 1

# Card Type
card_type = packet[offset]
print(f"Card Type: 0x{card_type:02x} (esperado: 0x32)")
offset += 1

# Card ID
card_id = packet[offset]
print(f"Card ID: 0x{card_id:02x} (enviado: 0xff = broadcast)")
offset += 1

# Command
command = packet[offset]
print(f"Command: 0x{command:02x} (esperado: 0x7b)")
offset += 1

# Additional Info
additional_info = packet[offset]
print(f"Additional Info: 0x{additional_info:02x} (esperado: 0x01 = confirmación)")
offset += 1

# Packet Data Length (4 bytes, little-endian)
packet_data_length = int.from_bytes(packet[offset:offset+4], 'little')
print(f"Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

# Packet Number
packet_number = packet[offset]
print(f"Packet Number: 0x{packet_number:02x}")
offset += 1

# Last Packet Number
last_packet_number = packet[offset]
print(f"Last Packet Number: 0x{last_packet_number:02x}")
offset += 1

# Command Data (CC = 0x02)
print(f"\n--- Command Data (desde offset {offset}) ---")
cmd_cc = packet[offset]
print(f"Comando CC: 0x{cmd_cc:02x} (esperado: 0x02 = SEND_TEXT)")
offset += 1

window_id = packet[offset]
print(f"Window ID: {window_id} (esperado: 0)")
offset += 1

effect = packet[offset]
print(f"Effect: 0x{effect:02x}")
offset += 1

alignment = packet[offset]
print(f"Alignment: 0x{alignment:02x}")
offset += 1

speed = packet[offset]
print(f"Speed: 0x{speed:02x}")
offset += 1

# Stay Time (2 bytes, little-endian)
stay_time = int.from_bytes(packet[offset:offset+2], 'little')
print(f"Stay Time: {stay_time} (0x{stay_time:04x})")
offset += 2

# Text data
print(f"\n--- Text Data (desde offset {offset}) ---")
text_data = packet[offset:-2]  # Hasta antes del checksum
print(f"Text data ({len(text_data)} bytes): {' '.join(f'{b:02x}' for b in text_data)}")

# Analizar formato del texto
print("\n--- Análisis del formato de texto ---")
print("Formato actual:")
i = 0
while i < len(text_data):
    if i + 2 < len(text_data):
        byte1 = text_data[i]
        byte2 = text_data[i+1]
        byte3 = text_data[i+2]
        if byte2 == 0x00 and byte3 == 0x00 and i + 2 == len(text_data) - 1:
            print(f"  [{i:2d}] 0x{byte1:02x} 0x{byte2:02x} 0x{byte3:02x} = Fin de texto")
            break
        elif byte2 == 0x00:
            char = chr(byte3) if 32 <= byte3 <= 126 else f"<{byte3:02x}>"
            print(f"  [{i:2d}] 0x{byte1:02x} 0x{byte2:02x} 0x{byte3:02x} = color_font={byte1:02x}, char='{char}'")
            i += 3
        else:
            print(f"  [{i:2d}] 0x{byte1:02x} 0x{byte2:02x} = ???")
            i += 2
    else:
        print(f"  [{i:2d}] 0x{text_data[i]:02x} = ???")
        i += 1

# Comparar con ejemplo de documentación
print("\n" + "=" * 80)
print("COMPARACIÓN CON EJEMPLO DE DOCUMENTACIÓN")
print("=" * 80)
print("\nEjemplo de documentación para 'hola' en rojo:")
print("0x02,0x00,0x00,0x00,0x03,0x00,0x03,0x10,0x00,0x68,0x10,0x00,0x6f,0x10,0x00,0x6c,0x10,0x00,0x61,0x00,0x00,0x00")
print("\nFormato esperado:")
print("  - color_font (0x10 = rojo, tamaño 16)")
print("  - 0x00 (reservado)")
print("  - carácter")
print("  - Repetir para cada carácter")
print("  - Fin: 0x00, 0x00, 0x00")

# Checksum
checksum = packet[-2:]
checksum_value = int.from_bytes(checksum, 'little')
print(f"\nChecksum: {' '.join(f'{b:02x}' for b in checksum)} (0x{checksum_value:04x})")

