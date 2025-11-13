#!/usr/bin/env python3
"""
Enviar el paquete exacto que el usuario proporcionó como correcto
"""

import socket
import struct
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paquete exacto del usuario (para "90")
packet_hex = "ffffffff1b0000006832017b011600000002000005030300220039220030000000e101"
packet = bytes.fromhex(packet_hex)

print("=" * 80)
print("ENVÍO DE PAQUETE EXACTO DEL USUARIO")
print("=" * 80)

print(f"\nPaquete: {len(packet)} bytes")
print(" ".join(f"{b:02x}" for b in packet))

# Analizar
offset = 0
print(f"\n[{offset:2d}-{offset+3:2d}] ID Code: {' '.join(f'{b:02x}' for b in packet[offset:offset+4])}")
offset += 4

network_length = int.from_bytes(packet[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Network Length: {network_length:08x} ({network_length} bytes)")
offset += 4

print(f"[{offset:2d}] Packet Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card Type: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Card ID: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Command/Protocol: {packet[offset]:02x}")
offset += 1

print(f"[{offset:2d}] Additional Info: {packet[offset]:02x}")
offset += 1

packet_data_length = int.from_bytes(packet[offset:offset+4], 'little')
print(f"[{offset:2d}-{offset+3:2d}] Packet Data Length: {packet_data_length:08x} ({packet_data_length} bytes)")
offset += 4

packet_data = packet[offset:-2]
print(f"[{offset:2d}-{len(packet)-3:2d}] Packet Data ({len(packet_data)} bytes): {' '.join(f'{b:02x}' for b in packet_data)}")
print(f"  Longitud real: {len(packet_data)} bytes")
print(f"  Longitud declarada: {packet_data_length} bytes")
print(f"  ⚠️ DIFERENCIA: {packet_data_length - len(packet_data)} bytes")

checksum = int.from_bytes(packet[-2:], 'little')
print(f"[{len(packet)-2:2d}-{len(packet)-1:2d}] Checksum: {checksum:04x} ({checksum})")

# Verificar checksum
data_for_checksum = packet[8:-2]
checksum_calc = sum(data_for_checksum) & 0xFFFF
print(f"\nChecksum calculado: 0x{checksum_calc:04x} ({checksum_calc})")
print(f"Checksum en paquete: 0x{checksum:04x} ({checksum})")
print(f"¿Coinciden? {'✓ SÍ' if checksum_calc == checksum else '✗ NO'}")

# Enviar paquete
panel_ip = "10.8.22.101"
panel_port = 5200

try:
    print(f"\n📤 Conectando a {panel_ip}:{panel_port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((panel_ip, panel_port))
    print("✅ Conexión establecida")
    
    print(f"📤 Enviando {len(packet)} bytes...")
    sock.sendall(packet)
    print("✅ Datos enviados")
    
    print("⏳ Esperando respuesta (timeout: 15s)...")
    sock.settimeout(15.0)
    
    try:
        # Intentar leer respuesta
        response = sock.recv(1024)
        if response:
            print(f"✅ Respuesta recibida: {len(response)} bytes")
            print(f"  {' '.join(f'{b:02x}' for b in response)}")
        else:
            print("⚠️ No se recibió respuesta (socket cerrado)")
    except socket.timeout:
        print("❌ Timeout esperando respuesta del panel")
    except Exception as e:
        print(f"❌ Error leyendo respuesta: {e}")
    
    sock.close()
    print("✅ Conexión cerrada")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

