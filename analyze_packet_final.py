#!/usr/bin/env python3
"""
Analizar el paquete final y verificar todos los campos
"""

# Paquete actual del log
packet_hex = "ffffffff1a000000683201007b01100002000005030300220039220030000000e101"
packet = bytes.fromhex(packet_hex)

print("=" * 80)
print("ANÁLISIS DEL PAQUETE ACTUAL")
print("=" * 80)

offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in packet[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(packet[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Network Length: {network_length:04x} ({network_length} bytes) - DEBERÍA SER 0x1b (27 bytes)")
offset += 2

print(f"[{offset:2d}-{offset+1:2d}] Reserved: {' '.join(f'{b:02x}' for b in packet[offset:offset+2])}")
offset += 2

print(f"[{offset:2d}] Packet Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {packet[offset]:02x} {'✓ CORRECTO' if packet[offset] == 0x01 else '✗ INCORRECTO'}")
offset += 1

print(f"[{offset:2d}] Byte reservado: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {packet[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(packet[offset:offset+2], 'little')
print(f"[{offset:2d}-{offset+1:2d}] Packet Data Length: {packet_data_length:04x} ({packet_data_length} bytes)")
offset += 2

packet_data = packet[offset:-2]
print(f"[{offset:2d}-{len(packet)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"  Longitud real del Packet Data: {len(packet_data)} bytes")
print(f"  Longitud declarada: {packet_data_length} bytes")
print(f"  ¿Coinciden? {'✓ SÍ' if len(packet_data) == packet_data_length else '✗ NO - Diferencia: ' + str(len(packet_data) - packet_data_length) + ' bytes'}")

checksum = int.from_bytes(packet[-2:], 'little')
print(f"[{len(packet)-2:2d}-{len(packet)-1:2d}] Checksum: {checksum:04x} ({checksum})")

# Calcular checksum correcto
data_for_checksum = packet[8:-2]  # Desde Packet Type hasta Packet Data
checksum_calc = sum(data_for_checksum) & 0xFFFF
print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")
print(f"Checksum en paquete: 0x{checksum:04x} ({checksum})")
print(f"¿Coinciden? {'✓ SÍ' if checksum_calc == checksum else '✗ NO'}")

# Calcular Network Length correcto
network_length_calc = len(data_for_checksum) + 2  # +2 para el checksum
print(f"\nNetwork Length calculado: {network_length_calc} bytes (0x{network_length_calc:04x})")
print(f"Network Length en paquete: {network_length} bytes (0x{network_length:04x})")
print(f"¿Coinciden? {'✓ SÍ' if network_length_calc == network_length else '✗ NO - Diferencia: ' + str(network_length_calc - network_length) + ' bytes'}")

# Analizar el comando CC
print("\n" + "=" * 80)
print("ANÁLISIS DEL COMANDO CC (Packet Data):")
print("=" * 80)
print(f"\nComando CC completo ({len(packet_data)} bytes):")
print(" ".join(f"{b:02x}" for b in packet_data))

cc_offset = 0
if len(packet_data) > 0:
    print(f"\n[{cc_offset}] CC Command: {packet_data[cc_offset]:02x} (0x02 = SEND_TEXT)")
    cc_offset += 1
    
    if len(packet_data) > cc_offset:
        print(f"[{cc_offset}] Window ID: {packet_data[cc_offset]}")
        cc_offset += 1
        
    if len(packet_data) > cc_offset:
        print(f"[{cc_offset}] Effect: {packet_data[cc_offset]:02x}")
        cc_offset += 1
        
    if len(packet_data) > cc_offset:
        print(f"[{cc_offset}] Alignment: {packet_data[cc_offset]:02x}")
        cc_offset += 1
        
    if len(packet_data) > cc_offset:
        print(f"[{cc_offset}] Speed: {packet_data[cc_offset]:02x}")
        cc_offset += 1
        
    if len(packet_data) > cc_offset + 1:
        stay_time = int.from_bytes(packet_data[cc_offset:cc_offset+2], 'little')
        print(f"[{cc_offset}-{cc_offset+1}] Stay Time: {stay_time} (0x{stay_time:04x})")
        cc_offset += 2
        
    # Texto
    print(f"\nTexto (desde offset {cc_offset}):")
    text_bytes = packet_data[cc_offset:-3]  # Hasta los últimos 3 bytes (fin de texto)
    i = 0
    text_chars = []
    while i < len(text_bytes) - 2:  # -2 para dejar espacio para el fin
        if i + 2 < len(text_bytes):
            color_font = text_bytes[i]
            reserved = text_bytes[i+1]
            char_code = text_bytes[i+2]
            if reserved == 0x00 and 32 <= char_code <= 126:
                char = chr(char_code)
                text_chars.append(char)
                print(f"  [{i:2d}-{i+2:2d}] color_font={color_font:02x}, reserved={reserved:02x}, char='{char}' (0x{char_code:02x})")
                i += 3
            else:
                break
        else:
            break
    
    print(f"\nTexto extraído: '{''.join(text_chars)}'")
    print(f"Texto esperado: '90'")
    print(f"¿Coinciden? {'✓ SÍ' if ''.join(text_chars) == '90' else '✗ NO'}")

