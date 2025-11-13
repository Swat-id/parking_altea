#!/usr/bin/env python3
"""
Analizar el comando CC del ejemplo de la documentación vs el que generamos
"""

# Ejemplo de la documentación para "hola" (4 caracteres)
# Packet Data Length: 0x16 (22 bytes)
# Comando CC: 0x02,0x00,0x00,0x00,0x03,0x00,0x03,0x10,0x00,0x68,0x10,0x00,0x6f,0x10,0x00,0x6c,0x10,0x00,0x61,0x00,0x00,0x00

example_cc = bytes([0x02, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x10, 0x00, 0x68, 0x10, 0x00, 0x6f, 0x10, 0x00, 0x6c, 0x10, 0x00, 0x61, 0x00, 0x00, 0x00])

print("=" * 80)
print("ANÁLISIS DEL COMANDO CC DEL EJEMPLO (hola)")
print("=" * 80)

print(f"\nComando CC del ejemplo: {len(example_cc)} bytes")
print(" ".join(f"{b:02x}" for b in example_cc))

# Desglosar
offset = 0
print(f"\n[{offset}] CC Command: {example_cc[offset]:02x} (0x02 = SEND_TEXT)")
offset += 1

print(f"[{offset}] Window ID: {example_cc[offset]}")
offset += 1

print(f"[{offset}] Effect: {example_cc[offset]:02x}")
offset += 1

print(f"[{offset}] Alignment: {example_cc[offset]:02x}")
offset += 1

print(f"[{offset}] Speed: {example_cc[offset]:02x}")
offset += 1

stay_time = int.from_bytes(example_cc[offset:offset+2], 'little')
print(f"[{offset}-{offset+1}] Stay Time: {stay_time} (0x{stay_time:04x})")
offset += 2

# Texto
print(f"\nTexto (desde offset {offset}):")
text_bytes = example_cc[offset:-3]
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
print(f"Longitud total del comando CC: {len(example_cc)} bytes")

# Comparar con nuestro comando CC para "90"
print("\n" + "=" * 80)
print("NUESTRO COMANDO CC PARA '90':")
print("=" * 80)

our_cc = bytes([0x02, 0x00, 0x00, 0x05, 0x03, 0x03, 0x00, 0x22, 0x00, 0x39, 0x22, 0x00, 0x30, 0x00, 0x00, 0x00])

print(f"\nNuestro comando CC: {len(our_cc)} bytes")
print(" ".join(f"{b:02x}" for b in our_cc))

print(f"\nDiferencia: {len(example_cc) - len(our_cc)} bytes")

# Contar bytes del ejemplo
print("\n" + "=" * 80)
print("CONTEO DE BYTES DEL EJEMPLO:")
print("=" * 80)
print("  0x02 (SEND_TEXT) = 1 byte")
print("  0x00 (window_id) = 1 byte")
print("  0x00 (effect) = 1 byte")
print("  0x00 (alignment) = 1 byte")
print("  0x03 (speed) = 1 byte")
print("  0x00, 0x03 (stay_time) = 2 bytes")
print("  0x10, 0x00, 0x68 ('h') = 3 bytes")
print("  0x10, 0x00, 0x6f ('o') = 3 bytes")
print("  0x10, 0x00, 0x6c ('l') = 3 bytes")
print("  0x10, 0x00, 0x61 ('a') = 3 bytes")
print("  0x00, 0x00, 0x00 (fin) = 3 bytes")
print(f"  Total: 1+1+1+1+1+2+3+3+3+3+3 = {1+1+1+1+1+2+3+3+3+3+3} bytes")

print("\n" + "=" * 80)
print("CONTEO DE BYTES DEL NUESTRO ('90'):")
print("=" * 80)
print("  0x02 (SEND_TEXT) = 1 byte")
print("  0x00 (window_id) = 1 byte")
print("  0x00 (effect) = 1 byte")
print("  0x05 (alignment) = 1 byte")
print("  0x03 (speed) = 1 byte")
print("  0x03, 0x00 (stay_time) = 2 bytes")
print("  0x22, 0x00, 0x39 ('9') = 3 bytes")
print("  0x22, 0x00, 0x30 ('0') = 3 bytes")
print("  0x00, 0x00, 0x00 (fin) = 3 bytes")
print(f"  Total: 1+1+1+1+1+2+3+3+3 = {1+1+1+1+1+2+3+3+3} bytes")

print("\n" + "=" * 80)
print("CONCLUSIÓN:")
print("=" * 80)
print("El comando CC para '90' tiene correctamente 16 bytes.")
print("El ejemplo de 'hola' tiene 22 bytes porque tiene 4 caracteres vs 2.")
print("El Packet Data Length debe ser igual a la longitud real del comando CC.")
print("Si el usuario dice que debe ser 22, puede que el panel espere un formato diferente,")
print("o que el ejemplo del usuario esté usando 'hola' como referencia.")

