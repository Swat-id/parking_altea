#!/usr/bin/env python3
"""
Diagnóstico completo de conexión con el panel
"""

import socket
import struct
import time
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

panel_ip = "10.8.22.101"
panel_port = 5200

print("=" * 80)
print("DIAGNÓSTICO DE CONEXIÓN CON PANEL")
print("=" * 80)

# 1. Verificar conectividad básica
print("\n1. Verificando conectividad básica...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((panel_ip, panel_port))
    print(f"✅ Conexión establecida con {panel_ip}:{panel_port}")
    sock.close()
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit(1)

# 2. Enviar paquete simple (ping/test)
print("\n2. Enviando paquete de prueba...")
# Paquete mínimo para verificar respuesta
# ID Code + Network Length + Packet Type + Card Type + Card ID + Protocol + Additional Info + Packet Data Length + Checksum
test_packet = bytes.fromhex("ffffffff0a0000006832017b0100000000a500")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    sock.connect((panel_ip, panel_port))
    print(f"📤 Enviando paquete de prueba ({len(test_packet)} bytes)...")
    sock.sendall(test_packet)
    print("✅ Paquete enviado")
    
    # Intentar leer respuesta inmediatamente
    sock.settimeout(1.0)
    try:
        response = sock.recv(1024)
        if response:
            print(f"✅ Respuesta recibida: {len(response)} bytes")
            print(f"   {' '.join(f'{b:02x}' for b in response)}")
        else:
            print("⚠️ No se recibió respuesta (socket cerrado)")
    except socket.timeout:
        print("⚠️ Timeout esperando respuesta (el panel puede no estar configurado para responder)")
    except Exception as e:
        print(f"❌ Error leyendo respuesta: {e}")
    
    sock.close()
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Enviar paquete con texto "90" (el que estamos generando)
print("\n3. Enviando paquete con texto '90' (generado por nuestro código)...")
# Paquete generado por nuestro código (Packet Data Length = 16)
our_packet = bytes.fromhex("ffffffff1b0000006832017b011000000002000005030300220039220030000000e101")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    sock.connect((panel_ip, panel_port))
    print(f"📤 Enviando paquete ({len(our_packet)} bytes)...")
    sock.sendall(our_packet)
    print("✅ Paquete enviado")
    
    # Intentar leer respuesta
    sock.settimeout(3.0)
    try:
        response = sock.recv(1024)
        if response:
            print(f"✅ Respuesta recibida: {len(response)} bytes")
            print(f"   {' '.join(f'{b:02x}' for b in response)}")
            
            # Analizar respuesta
            if len(response) >= 8:
                packet_type = response[8] if len(response) > 8 else 0
                if packet_type == 0xE8 or packet_type == 0x68:
                    return_value = response[11] if len(response) > 11 else 0
                    if return_value == 0x00:
                        print("✅ Panel respondió con éxito (Return Value = 0x00)")
                    else:
                        print(f"⚠️ Panel respondió con error (Return Value = 0x{return_value:02x})")
        else:
            print("⚠️ No se recibió respuesta (socket cerrado)")
    except socket.timeout:
        print("⚠️ Timeout esperando respuesta")
        print("   Posibles causas:")
        print("   - El panel no está configurado para responder")
        print("   - El formato del paquete no es el esperado")
        print("   - Problema de red/conectividad")
    except Exception as e:
        print(f"❌ Error leyendo respuesta: {e}")
    
    sock.close()
except Exception as e:
    print(f"❌ Error: {e}")

# 4. Verificar si el panel muestra el texto
print("\n4. Verificación manual:")
print("   Por favor, verifica físicamente si el panel muestra el texto '90'")
print("   Aunque no haya respuesta, el panel puede haber recibido y procesado el mensaje")

print("\n" + "=" * 80)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 80)

