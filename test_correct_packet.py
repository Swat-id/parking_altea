#!/usr/bin/env python3
"""
Construir el paquete exacto según el ejemplo correcto del usuario
"""

import struct

# Paquete correcto según usuario
correct_hex = "ffffffff1b0000006832017b011600000002000005030300220039220030000000e101"
correct = bytes.fromhex(correct_hex)

print("=" * 80)
print("ANÁLISIS DEL PAQUETE CORRECTO DEL USUARIO")
print("=" * 80)

offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in correct[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(correct[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Network Length: {network_length:08x} ({network_length} bytes)")
offset += 4

print(f"[{offset:2d}] Packet Type: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command/Protocol: {correct[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {correct[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(correct[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

packet_data = correct[offset:-2]
print(f"[{offset:2d}-{len(correct)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"  Longitud real del Packet Data: {len(packet_data)} bytes")
print(f"  Longitud declarada: {packet_data_length} bytes")
print(f"  Diferencia: {packet_data_length - len(packet_data)} bytes")

checksum = int.from_bytes(correct[-2:], 'little')
print(f"[{len(correct)-2:2d}-{len(correct)-1:2d}] Checksum: {checksum:04x} ({checksum})")

# Analizar el comando CC
print("\n" + "=" * 80)
print("ANÁLISIS DEL COMANDO CC:")
print("=" * 80)

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
    while i < len(text_bytes) - 2:
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

# Verificar checksum
data_for_checksum = correct[8:-2]  # Desde Packet Type hasta Packet Data
checksum_calc = sum(data_for_checksum) & 0xFFFF
print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")
print(f"Checksum en paquete: 0x{checksum:04x} ({checksum})")
print(f"¿Coinciden? {'✓ SÍ' if checksum_calc == checksum else '✗ NO'}")

# Verificar Network Length
network_length_calc = len(data_for_checksum) + 2  # +2 para el checksum
print(f"\nNetwork Length calculado: {network_length_calc} bytes (0x{network_length_calc:08x})")
print(f"Network Length en paquete: {network_length} bytes (0x{network_length:08x})")
print(f"¿Coinciden? {'✓ SÍ' if network_length_calc == network_length else '✗ NO'}")

