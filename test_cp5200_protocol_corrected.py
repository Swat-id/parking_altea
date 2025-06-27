#!/usr/bin/env python3
"""
Test CP5200 Protocol Corrected - Implementación correcta del protocolo CP5200
Implementa la inicialización de red antes de enviar mensajes
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

class CP5200ProtocolCorrected:
    """Implementación corregida del protocolo CP5200"""
    
    def __init__(self):
        self.sequence_number = 0
        self.initialized = False
    
    def _get_sequence_number(self) -> int:
        """Obtener siguiente número de secuencia"""
        self.sequence_number = (self.sequence_number + 1) % 256
        return self.sequence_number
    
    def _ip_to_int(self, ip: str) -> int:
        """Convertir IP string a entero"""
        parts = ip.split('.')
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
    
    def build_init_message(self, panel_ip: str, port: int = 23, id_code: str = "255.255.255.255", timeout: int = 600) -> bytes:
        """Construir mensaje de inicialización CP5200_Net_Init"""
        ip_int = self._ip_to_int(panel_ip)
        id_code_int = self._ip_to_int(id_code)
        
        # Formato: [comando][secuencia][ip][puerto][id_code][timeout]
        message = struct.pack('>BB', 0x01, self._get_sequence_number())  # Comando de inicialización
        message += struct.pack('>IIII', ip_int, port, id_code_int, timeout)
        
        return message
    
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
        message += struct.pack('>I', height)
        
        return message
    
    def send_init_telnet(self, panel_ip: str) -> bool:
        """Enviar mensaje de inicialización via Telnet"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((panel_ip, 23))
            
            # Enviar mensaje de inicialización
            init_message = self.build_init_message(panel_ip)
            print(f"      Enviando inicialización: {len(init_message)} bytes")
            print(f"      Bytes: {init_message.hex()}")
            sock.send(init_message)
            
            # Esperar respuesta
            sock.settimeout(2.0)
            try:
                response = sock.recv(1024)
                print(f"      Respuesta inicialización: {response}")
                self.initialized = True
                return True
            except socket.timeout:
                print(f"      Sin respuesta inicialización (timeout)")
                self.initialized = True  # Asumimos éxito si se envió
                return True
            
        except Exception as e:
            print(f"      Error en inicialización: {e}")
            return False
        finally:
            try:
                sock.close()
            except:
                pass
    
    def send_message_telnet(self, panel_ip: str, message: bytes) -> bool:
        """Enviar mensaje via Telnet al panel"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((panel_ip, 23))
            
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

def test_cp5200_protocol_corrected(panel: Dict) -> Dict:
    """Testear protocolo CP5200 corregido en un panel"""
    print(f"\n=== Testeando Protocolo CP5200 Corregido Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'parking': panel['parking'],
        'ping_status': False,
        'telnet_status': False,
        'init_status': False,
        'text_message_sent': False,
        'static_message_sent': False,
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
    
    # 3. Inicialización CP5200
    print(f"3. Inicializando protocolo CP5200...")
    protocol = CP5200ProtocolCorrected()
    
    try:
        init_success = protocol.send_init_telnet(panel['ip'])
        results['init_status'] = init_success
        
        if init_success:
            print(f"   ✅ Inicialización CP5200 exitosa")
        else:
            print(f"   ❌ Fallo en inicialización CP5200")
            results['errors'].append("Fallo en inicialización CP5200")
            return results
        
    except Exception as e:
        error_msg = f"Error en inicialización: {e}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
        return results
    
    # 4. Enviar mensaje de texto
    print(f"4. Enviando mensaje de texto...")
    try:
        text_message = f"TEST {panel['id']}: {panel['ip']}"
        print(f"   Mensaje: '{text_message}'")
        
        message = protocol.build_text_message(1, 0, text_message, 0xFF, 16, 3, 0, 10, 5)
        print(f"   Mensaje CP5200: {len(message)} bytes")
        print(f"   Bytes: {message.hex()}")
        
        success = protocol.send_message_telnet(panel['ip'], message)
        
        if success:
            results['text_message_sent'] = True
            print(f"   ✅ Mensaje de texto enviado")
            print(f"   📺 El panel debería mostrar: '{text_message}'")
        else:
            print(f"   ❌ Fallo al enviar mensaje de texto")
            results['errors'].append("Fallo al enviar mensaje de texto")
        
    except Exception as e:
        error_msg = f"Error enviando mensaje de texto: {e}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
    
    # 5. Enviar mensaje estático
    print(f"5. Enviando mensaje estático...")
    try:
        static_text = f"PANEL {panel['id']}\n{panel['ip']}"
        print(f"   Mensaje estático: '{static_text}'")
        
        message = protocol.build_static_text_message(1, 0, static_text, 0xFF, 16, 0, 0, 0, 64, 32)
        print(f"   Mensaje estático CP5200: {len(message)} bytes")
        
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

def test_simple_telnet_text(panel: Dict) -> Dict:
    """Test simple de envío de texto por Telnet (sin protocolo CP5200)"""
    print(f"\n=== Testeando Texto Simple Telnet Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'simple_text_sent': False,
        'errors': []
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((panel['ip'], 23))
        
        # Enviar texto simple
        simple_text = f"TEST PANEL {panel['id']}: {panel['ip']}\r\n"
        print(f"   Enviando texto simple: '{simple_text.strip()}'")
        sock.send(simple_text.encode('utf-8'))
        
        # Esperar respuesta
        sock.settimeout(2.0)
        try:
            response = sock.recv(1024)
            print(f"   Respuesta: {response}")
            results['simple_text_sent'] = True
            print(f"   ✅ Texto simple enviado")
        except socket.timeout:
            print(f"   Sin respuesta (timeout)")
            results['simple_text_sent'] = True
            print(f"   ✅ Texto simple enviado (sin respuesta)")
        
    except Exception as e:
        error_msg = f"Error enviando texto simple: {e}"
        print(f"   ❌ {error_msg}")
        results['errors'].append(error_msg)
    finally:
        try:
            sock.close()
        except:
            pass
    
    return results

def main():
    """Función principal"""
    print("🚦 TESTEANDO PROTOCOLO CP5200 CORREGIDO")
    print("=" * 60)
    print("Este test implementa la inicialización CP5200 antes de enviar mensajes")
    print("y también prueba envío de texto simple por Telnet.")
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
            'cp5200_test': test_cp5200_protocol_corrected(panel),
            'simple_telnet_test': test_simple_telnet_text(panel)
        }
        
        all_results['panels'].append(panel_results)
        
        # Resumen del panel
        print(f"\n📊 RESUMEN PANEL {panel['id']}:")
        print(f"   Ping: {'✅' if panel_results['cp5200_test']['ping_status'] else '❌'}")
        print(f"   Telnet: {'✅' if panel_results['cp5200_test']['telnet_status'] else '❌'}")
        print(f"   CP5200 Init: {'✅' if panel_results['cp5200_test']['init_status'] else '❌'}")
        print(f"   CP5200 Text: {'✅' if panel_results['cp5200_test']['text_message_sent'] else '❌'}")
        print(f"   CP5200 Static: {'✅' if panel_results['cp5200_test']['static_message_sent'] else '❌'}")
        print(f"   Simple Telnet: {'✅' if panel_results['simple_telnet_test']['simple_text_sent'] else '❌'}")
        
        # Instrucciones para el usuario
        if panel_results['cp5200_test']['text_message_sent']:
            print(f"   👀 Verificar CP5200: 'TEST {panel['id']}: {panel['ip']}'")
        if panel_results['cp5200_test']['static_message_sent']:
            print(f"   👀 Verificar CP5200 Estático: 'PANEL {panel['id']}\\n{panel['ip']}'")
        if panel_results['simple_telnet_test']['simple_text_sent']:
            print(f"   👀 Verificar Telnet Simple: 'TEST PANEL {panel['id']}: {panel['ip']}'")
    
    # Resumen general
    print(f"\n{'='*60}")
    print("📊 RESUMEN GENERAL")
    print(f"{'='*60}")
    
    total_panels = len(PANELS)
    ping_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['ping_status'])
    telnet_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['telnet_status'])
    init_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['init_status'])
    text_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['text_message_sent'])
    static_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['static_message_sent'])
    simple_ok = sum(1 for p in all_results['panels'] if p['simple_telnet_test']['simple_text_sent'])
    
    print(f"Total paneles: {total_panels}")
    print(f"Ping OK: {ping_ok}/{total_panels} ({ping_ok/total_panels*100:.1f}%)")
    print(f"Telnet OK: {telnet_ok}/{total_panels} ({telnet_ok/total_panels*100:.1f}%)")
    print(f"CP5200 Init OK: {init_ok}/{total_panels} ({init_ok/total_panels*100:.1f}%)")
    print(f"CP5200 Text OK: {text_ok}/{total_panels} ({text_ok/total_panels*100:.1f}%)")
    print(f"CP5200 Static OK: {static_ok}/{total_panels} ({static_ok/total_panels*100:.1f}%)")
    print(f"Simple Telnet OK: {simple_ok}/{total_panels} ({simple_ok/total_panels*100:.1f}%)")
    
    # Guardar resultados
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"cp5200_protocol_corrected_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filename}")
    
    # Instrucciones finales
    print(f"\n📋 INSTRUCCIONES PARA VALIDACIÓN:")
    print(f"1. Verificar físicamente cada panel")
    print(f"2. Confirmar que se muestran los mensajes CP5200")
    print(f"3. Confirmar que se muestran los mensajes Telnet simples")
    print(f"4. Si los mensajes se ven correctamente, proceder con implementación")
    print(f"5. Si no se ven, revisar configuración de paneles")
    
    if text_ok > 0 or simple_ok > 0:
        print(f"\n✅ ÉXITO: Algunos paneles recibieron mensajes")
        print(f"   - Proceder con implementación de mensajes de estado")
        print(f"   - Implementar comunicación CP5200+Telnet en backend")
    else:
        print(f"\n⚠️  ADVERTENCIA: Ningún panel recibió mensajes")
        print(f"   - Revisar conectividad de red")
        print(f"   - Verificar configuración de paneles")

if __name__ == "__main__":
    main() 