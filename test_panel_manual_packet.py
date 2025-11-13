#!/usr/bin/env python3
"""
Script para enviar un paquete construido manualmente según las especificaciones del usuario
"""

import sys
import os
import asyncio
import socket
import struct
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_manual_packet(panel_ip: str, panel_port: int = 5200):
    """
    Construye y envía un paquete manualmente según las especificaciones exactas
    """
    logger.info(f"=== ENVÍO DE PAQUETE MANUAL ===")
    logger.info(f"Panel: {panel_ip}:{panel_port}")
    logger.info("=" * 50)
    
    # Construir comando CC para "90"
    # Según el usuario, debería ser 19 bytes, no 16
    # Intentemos con el formato que el usuario espera
    command_data = bytes([
        0x02,  # SUB_CMD_SEND_TEXT
        0x00,  # window_id
        0x00,  # effect
        0x05,  # alignment
        0x03,  # speed
    ])
    command_data += struct.pack('<H', 3)  # stay_time
    # Texto "90" con color_font = 0x22 (verde, tamaño 16)
    command_data += bytes([0x22, 0x00, 0x39])  # '9'
    command_data += bytes([0x22, 0x00, 0x30])  # '0'
    command_data += b'\x00\x00\x00'  # Fin de texto
    
    logger.info(f"Comando CC: {len(command_data)} bytes")
    logger.info(f"  {' '.join(f'{b:02x}' for b in command_data)}")
    
    # Packet Header
    packet_header = bytes([
        0x68,  # PACKET_TYPE_SEND
        0x32,  # CARD_TYPE
        0x01,  # card_id (específico)
        0x00,  # Byte reservado
        0x7B,  # command
        0x01,  # additional_info (confirmación)
    ])
    
    # Packet Data Length (2 bytes)
    packet_data_length = len(command_data)
    packet_info = struct.pack('<H', packet_data_length)
    
    # Datos para checksum
    data_for_checksum = packet_header + packet_info + command_data
    
    # Checksum
    checksum = sum(data_for_checksum) & 0xFFFF
    checksum_bytes = struct.pack('<H', checksum)
    
    # Network Length
    network_length = len(data_for_checksum) + len(checksum_bytes)
    
    # Paquete completo
    packet = (
        bytes([0xFF, 0xFF, 0xFF, 0xFF]) +  # ID Code
        struct.pack('<H', network_length) +  # Network Length
        b'\x00\x00' +  # Reserved
        data_for_checksum +  # Packet Type hasta Packet Data
        checksum_bytes  # Checksum
    )
    
    logger.info(f"\nPaquete completo: {len(packet)} bytes")
    logger.info(f"  {' '.join(f'{b:02x}' for b in packet)}")
    logger.info(f"\nNetwork Length: {network_length} (0x{network_length:04x})")
    logger.info(f"Packet Data Length: {packet_data_length} (0x{packet_data_length:04x})")
    logger.info(f"Checksum: {checksum} (0x{checksum:04x})")
    
    # Enviar paquete
    try:
        logger.info(f"\n📤 Conectando a {panel_ip}:{panel_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((panel_ip, panel_port))
        logger.info("✅ Conexión establecida")
        
        logger.info(f"📤 Enviando {len(packet)} bytes...")
        sock.sendall(packet)
        logger.info("✅ Datos enviados")
        
        logger.info("⏳ Esperando respuesta (timeout: 15s)...")
        sock.settimeout(15.0)
        
        # Intentar leer respuesta
        try:
            # Leer header (12 bytes mínimo)
            header = sock.recv(12)
            logger.info(f"📥 Header recibido: {len(header)} bytes")
            logger.info(f"  {' '.join(f'{b:02x}' for b in header)}")
            
            if len(header) >= 12:
                # Leer el resto si hay
                network_length_resp = struct.unpack('<H', header[4:6])[0]
                logger.info(f"  Network Length en respuesta: {network_length_resp} bytes")
                
                if network_length_resp > 12:
                    remaining = network_length_resp - 12
                    body = sock.recv(remaining)
                    logger.info(f"📥 Body recibido: {len(body)} bytes")
                    logger.info(f"  {' '.join(f'{b:02x}' for b in body)}")
                    full_response = header + body
                else:
                    full_response = header
                
                logger.info(f"\n✅ Respuesta completa recibida: {len(full_response)} bytes")
                logger.info(f"  {' '.join(f'{b:02x}' for b in full_response)}")
            else:
                logger.warning(f"⚠️ Header incompleto: solo {len(header)} bytes")
                
        except socket.timeout:
            logger.error("❌ Timeout esperando respuesta del panel")
        except Exception as e:
            logger.error(f"❌ Error leyendo respuesta: {e}")
        
        sock.close()
        logger.info("✅ Conexión cerrada")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enviar paquete manual a panel')
    parser.add_argument('panel_ip', help='IP del panel')
    parser.add_argument('--port', type=int, default=5200, help='Puerto del panel (default: 5200)')
    
    args = parser.parse_args()
    
    # Ejecutar
    asyncio.run(send_manual_packet(args.panel_ip, args.port))

