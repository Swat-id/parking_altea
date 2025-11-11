#!/usr/bin/env python3
"""
Script para analizar los paquetes enviados y verificar el window_id
"""

import re
import subprocess
import sys

def analyze_packets():
    """Analiza los paquetes enviados y extrae el window_id"""
    
    print("=" * 80)
    print("ANÁLISIS DE PAQUETES ENVIADOS - VERIFICACIÓN DE window_id")
    print("=" * 80)
    print()
    
    # Obtener logs
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'parking-panel-protocol.service', '--since', '2 hours ago', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=30
        )
        logs = result.stdout
    except Exception as e:
        print(f"Error obteniendo logs: {e}")
        return
    
    # Buscar líneas con "ventana X" y "Paquete completo"
    ventana_pattern = r"ventana (\d+)"
    paquete_pattern = r"Paquete completo \(hex\): ([a-f0-9]+)"
    
    ventanas_encontradas = {}
    current_ventana = None
    
    for line in logs.split('\n'):
        # Buscar ventana
        ventana_match = re.search(ventana_pattern, line)
        if ventana_match:
            current_ventana = ventana_match.group(1)
            continue
        
        # Buscar paquete
        paquete_match = re.search(paquete_pattern, line)
        if paquete_match and current_ventana is not None:
            hex_packet = paquete_match.group(1)
            if current_ventana not in ventanas_encontradas:
                ventanas_encontradas[current_ventana] = []
            ventanas_encontradas[current_ventana].append(hex_packet)
            current_ventana = None
    
    # Analizar cada ventana
    for ventana in sorted(ventanas_encontradas.keys(), key=int):
        print(f"VENTANA {ventana}:")
        print(f"  Total de paquetes encontrados: {len(ventanas_encontradas[ventana])}")
        
        if ventanas_encontradas[ventana]:
            # Analizar el último paquete
            hex_packet = ventanas_encontradas[ventana][-1]
            print(f"  Último paquete (hex): {hex_packet}")
            print(f"  Longitud del paquete: {len(hex_packet) // 2} bytes")
            
            # Analizar estructura del paquete
            try:
                packet_bytes = bytes.fromhex(hex_packet)
                
                # Estructura según protocolo:
                # 0-3: ID Code (4 bytes)
                # 4-5: Network Length (2 bytes, little-endian)
                # 6-7: Reserved (2 bytes)
                # 8: Packet Type (0x68)
                # 9: Card Type (0x32)
                # 10: Card ID
                # 11: Command (0x7B)
                # 12: Additional Info
                # 13-16: Length del comando CC (4 bytes, little-endian)
                # 17: Subcomando (0x02 = send text)
                # 18: window_id ← AQUÍ ESTÁ
                
                if len(packet_bytes) > 18:
                    id_code = packet_bytes[0:4]
                    network_length = int.from_bytes(packet_bytes[4:6], 'little')
                    reserved = packet_bytes[6:8]
                    packet_type = packet_bytes[8]
                    card_type = packet_bytes[9]
                    card_id = packet_bytes[10]
                    command = packet_bytes[11]
                    additional_info = packet_bytes[12]
                    length_cc = int.from_bytes(packet_bytes[13:17], 'little')
                    subcommand = packet_bytes[17]
                    window_id_byte = packet_bytes[18]
                    
                    print()
                    print("  Estructura del paquete:")
                    print(f"    ID Code: {id_code.hex()}")
                    print(f"    Network Length: {network_length} bytes")
                    print(f"    Reserved: {reserved.hex()}")
                    print(f"    Packet Type: 0x{packet_type:02x}")
                    print(f"    Card Type: 0x{card_type:02x}")
                    print(f"    Card ID: 0x{card_id:02x}")
                    print(f"    Command: 0x{command:02x}")
                    print(f"    Additional Info: 0x{additional_info:02x}")
                    print(f"    Length CC: {length_cc} bytes")
                    print(f"    Subcomando: 0x{subcommand:02x}")
                    print(f"    window_id: {window_id_byte} (0x{window_id_byte:02x})")
                    print()
                    
                    # Verificar coincidencia
                    if window_id_byte == int(ventana):
                        print(f"  ✅ VERIFICACIÓN: window_id en paquete ({window_id_byte}) coincide con ventana indicada ({ventana})")
                    else:
                        print(f"  ❌ ERROR: window_id en paquete ({window_id_byte}) NO coincide con ventana indicada ({ventana})")
                    
                    # Mostrar siguientes bytes para contexto
                    if len(packet_bytes) > 25:
                        print(f"    Siguientes bytes (efecto, alineación, velocidad): {packet_bytes[19:22].hex()}")
                else:
                    print(f"  ⚠️  Paquete demasiado corto para analizar (solo {len(packet_bytes)} bytes)")
                    
            except Exception as e:
                print(f"  ❌ Error analizando paquete: {e}")
        
        print()
        print("-" * 80)
        print()
    
    # Resumen
    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Total de ventanas encontradas: {len(ventanas_encontradas)}")
    for ventana in sorted(ventanas_encontradas.keys(), key=int):
        print(f"  - Ventana {ventana}: {len(ventanas_encontradas[ventana])} paquetes")

if __name__ == '__main__':
    analyze_packets()


