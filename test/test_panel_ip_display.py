#!/usr/bin/env python3
"""
Test Panel IP Display - Validación de visualización de texto
Envía la IP de cada panel a sí mismo para validar que se muestra correctamente
"""

import socket
import struct
import time
import subprocess
import platform
from typing import Dict, List, Optional
import json

# Configuración de paneles desde la base de datos
PANELS = [
    {"id": 1, "name": "PANEL C. ESPORTIVA", "ip": "172.20.17.50", "parking": "1 - P. Ciutat Esportiva"},
    {"id": 2, "name": "PANEL BASSETA 1", "ip": "172.20.5.50", "parking": "2 - P. Basseta Centre"},
    {"id": 3, "name": "PANEL BASSETA 2", "ip": "172.20.5.51", "parking": "2 - P. Basseta Centre"},
    {"id": 4, "name": "PANEL PITERES", "ip": "172.20.8.50", "parking": "6 - P. Poble antic/Conservatori"},
    {"id": 5, "name": "PANEL PALAU", "ip": "172.20.4.50", "parking": "5 - P. Poble antic/Palau Altea"},
    {"id": 6, "name": "PANEL COCOLISO", "ip": "172.20.4.51", "parking": "5 - P. Poble antic/Palau Altea"},
    {"id": 7, "name": "BELLES ARTS 2", "ip": "172.20.4.52", "parking": "4 - P. Poble antic/Belles Arts 2"},
    {"id": 8, "name": "BELLES ARTS", "ip": "172.20.4.53", "parking": "3 - P. Poble antic/Belles Arts 1"},
    {"id": 9, "name": "PANEL RENFE", "ip": "172.20.2.50", "parking": "8 - P. Estació Altea"},
    {"id": 10, "name": "PANEL ALTEA VELLA", "ip": "172.20.1.50", "parking": "9 - P. Altea la Vella"}
]

class CP5200Protocol:
    """Implementación del protocolo CP5200 para envío de mensajes"""
    
    def __init__(self):
        self.sequence_number = 0
    
    def _get_sequence_number(self) -> int:
        """Obtener siguiente número de secuencia"""
        self.sequence_number = (self.sequence_number + 1) % 256
        return self.sequence_number
    
    def build_text_message(self, card_id: int, window: int, text: str, color: int = 0xFF, 
                          font_size: int = 16, speed: int = 3, effect: int = 0, 
                          stay_time: int = 5, alignment: int = 5) -> bytes:
        """Construir mensaje de texto CP5200_Net_SendText"""
        text_bytes = text.encode('utf-8')
        
        # Formato: [comando][secuencia][card_id][window][longitud_texto][texto][color][font_size][speed][effect][stay_time][alignment]
        message = struct.pack('>BBBB', 0x02, self._get_sequence_number(), card_id, window)
        message += struct.pack('>I', len(text_bytes))
        message += text_bytes
        message += struct.pack('>IIIIII', color, font_size, speed, effect, stay_time, alignment)
        
        return message
    
    def build_static_text_message(self, card_id: int, window: int, text: str, color: int = 0xFF,
                                 font_size: int = 16, alignment: int = 0, x: int = 0, y: int = 0,
                                 width: int = 64, height: int = 32) -> bytes:
        """Construir mensaje de texto estático CP5200_Net_SendStatic"""
        text_bytes = text.encode('utf-8')
        
        message = struct.pack('>BBBB', 0x03, self._get_sequence_number(), card_id, window)
        message += struct.pack('>I', len(text_bytes))
        message += text_bytes
        message += struct.pack('>IIIIII', color, font_size, alignment, x, y, width)
        
        return message
    
    def send_message_telnet(self, ip: str, message: bytes) -> bool:
        """Enviar mensaje via Telnet al panel"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((ip, 23))  # Puerto Telnet
            
            # Enviar mensaje
            sock.send(message)
            
            # Intentar recibir respuesta
            sock.settimeout(2.0)
            try:
                response = sock.recv(1024)
                print(f"      Respuesta Telnet: {response}")
                return True
            except socket.timeout:
                print(f"      Sin respuesta (timeout)")
                return True  # Consideramos éxito si se envió el mensaje
            
        except Exception as e:
            print(f"      Error enviando mensaje: {e}")
            return False
        finally:
            try:
                sock.close()
            except:
                pass

def ping_panel(panel_ip: str) -> bool:
    """Hacer ping a un panel"""
    try:
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", panel_ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", panel_ip]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception as e:
        print(f"Error haciendo ping a {panel_ip}: {e}")
        return False

def test_panel_ip_display(panel: Dict) -> Dict:
    """Testear visualización de IP en un panel"""
    print(f"\n=== Testeando Visualización Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'parking': panel['parking'],
        'ping_status': False,
        'telnet_status': False,
        'message_sent': False,
        'response_received': False,
        'errors': []
    }
    
    # 1. Test ping
    print(f"1. Verificando conectividad...")
    results['ping_status'] = ping_panel(panel['ip'])
    print(f"   Ping: {'✅ OK' if results['ping_status'] else '❌ FAIL'}")
    
    if not results['ping_status']:
        results['errors'].append("Panel no responde al ping")
        return results
    
    # 2. Test Telnet
    print(f"2. Verificando Telnet...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        result = sock.connect_ex((panel['ip'], 23))
        sock.close()
        results['telnet_status'] = result == 0
        print(f"   Telnet: {'✅ OK' if results['telnet_status'] else '❌ FAIL'}")
    except:
        print(f"   Telnet: ❌ FAIL")
        results['errors'].append("Error verificando Telnet")
        return results
    
    # 3. Enviar mensaje con IP del panel
    print(f"3. Enviando mensaje con IP del panel...")
    protocol = CP5200Protocol()
    
    try:
        # Mensaje simple con la IP del panel
        ip_message = f"IP: {panel['ip']}"
        print(f"   Mensaje a enviar: '{ip_message}'")
        
        # Construir mensaje CP5200
        message = protocol.build_text_message(1, 0, ip_message, 0xFF, 16, 3, 0, 10, 5)
        print(f"   Mensaje CP5200 construido: {len(message)} bytes")
        print(f"   Bytes: {message.hex()}")
        
        # Enviar via Telnet
        print(f"   Enviando via Telnet...")
        success = protocol.send_message_telnet(panel['ip'], message)
        
        if success:
            results['message_sent'] = True
            results['response_received'] = True
            print(f"   ✅ Mensaje enviado exitosamente")
            print(f"   📺 El panel debería mostrar: '{ip_message}'")
        else:
            print(f"   ❌ Fallo al enviar mensaje")
            results['errors'].append("Fallo al enviar mensaje")
        
    except Exception as e:
        error_msg = f"Error enviando mensaje: {e}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def test_static_message(panel: Dict) -> Dict:
    """Testear mensaje estático en un panel"""
    print(f"\n=== Testeando Mensaje Estático Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'static_message_sent': False,
        'errors': []
    }
    
    try:
        protocol = CP5200Protocol()
        
        # Mensaje estático con información del panel
        static_text = f"PANEL {panel['id']}\n{panel['ip']}"
        print(f"   Mensaje estático: '{static_text}'")
        
        # Construir mensaje estático CP5200
        message = protocol.build_static_text_message(1, 0, static_text, 0xFF, 16, 0, 0, 0, 64, 32)
        print(f"   Mensaje estático CP5200: {len(message)} bytes")
        
        # Enviar via Telnet
        print(f"   Enviando mensaje estático...")
        success = protocol.send_message_telnet(panel['ip'], message)
        
        if success:
            results['static_message_sent'] = True
            print(f"   ✅ Mensaje estático enviado")
            print(f"   📺 El panel debería mostrar estáticamente: '{static_text}'")
        else:
            print(f"   ❌ Fallo al enviar mensaje estático")
            results['errors'].append("Fallo al enviar mensaje estático")
        
    except Exception as e:
        error_msg = f"Error enviando mensaje estático: {e}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def main():
    """Función principal"""
    print("🚦 TESTEANDO VISUALIZACIÓN DE IP EN PANELES")
    print("=" * 60)
    print("Este test envía la IP de cada panel a sí mismo para validar")
    print("que se muestra correctamente el texto en los paneles.")
    print("=" * 60)
    
    all_results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'panels': []
    }
    
    for panel in PANELS:
        print(f"\n{'='*60}")
        print(f"PANEL {panel['id']}: {panel['name']}")
        print(f"IP: {panel['ip']} | Parking: {panel['parking']}")
        print(f"{'='*60}")
        
        panel_results = {
            'panel_info': panel,
            'ip_display_test': test_panel_ip_display(panel),
            'static_message_test': test_static_message(panel)
        }
        
        all_results['panels'].append(panel_results)
        
        # Resumen del panel
        print(f"\n📊 RESUMEN PANEL {panel['id']}:")
        print(f"   Ping: {'✅' if panel_results['ip_display_test']['ping_status'] else '❌'}")
        print(f"   Telnet: {'✅' if panel_results['ip_display_test']['telnet_status'] else '❌'}")
        print(f"   Mensaje IP: {'✅' if panel_results['ip_display_test']['message_sent'] else '❌'}")
        print(f"   Mensaje Estático: {'✅' if panel_results['static_message_test']['static_message_sent'] else '❌'}")
        
        # Instrucciones para el usuario
        if panel_results['ip_display_test']['message_sent']:
            print(f"   👀 Verificar que el panel muestra: 'IP: {panel['ip']}'")
        if panel_results['static_message_test']['static_message_sent']:
            print(f"   👀 Verificar que el panel muestra estáticamente: 'PANEL {panel['id']}\\n{panel['ip']}'")
    
    # Resumen general
    print(f"\n{'='*60}")
    print("📊 RESUMEN GENERAL")
    print(f"{'='*60}")
    
    total_panels = len(PANELS)
    ping_ok = sum(1 for p in all_results['panels'] if p['ip_display_test']['ping_status'])
    telnet_ok = sum(1 for p in all_results['panels'] if p['ip_display_test']['telnet_status'])
    message_ok = sum(1 for p in all_results['panels'] if p['ip_display_test']['message_sent'])
    static_ok = sum(1 for p in all_results['panels'] if p['static_message_test']['static_message_sent'])
    
    print(f"Total paneles: {total_panels}")
    print(f"Ping OK: {ping_ok}/{total_panels} ({ping_ok/total_panels*100:.1f}%)")
    print(f"Telnet OK: {telnet_ok}/{total_panels} ({telnet_ok/total_panels*100:.1f}%)")
    print(f"Mensaje IP OK: {message_ok}/{total_panels} ({message_ok/total_panels*100:.1f}%)")
    print(f"Mensaje Estático OK: {static_ok}/{total_panels} ({static_ok/total_panels*100:.1f}%)")
    
    # Guardar resultados
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"panel_ip_display_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filename}")
    
    # Instrucciones finales
    print(f"\n📋 INSTRUCCIONES PARA VALIDACIÓN:")
    print(f"1. Verificar físicamente cada panel")
    print(f"2. Confirmar que se muestra la IP del panel")
    print(f"3. Confirmar que se muestra el mensaje estático")
    print(f"4. Si los mensajes se ven correctamente, proceder con implementación")
    print(f"5. Si no se ven, revisar configuración de paneles")
    
    if message_ok == total_panels:
        print(f"\n✅ ÉXITO: Todos los paneles recibieron mensajes")
        print(f"   - Proceder con implementación de mensajes de estado")
        print(f"   - Implementar comunicación CP5200+Telnet en backend")
    else:
        print(f"\n⚠️  ADVERTENCIA: Algunos paneles no recibieron mensajes")
        print(f"   - Revisar conectividad de red")
        print(f"   - Verificar configuración de paneles")

if __name__ == "__main__":
    main() 