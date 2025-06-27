#!/usr/bin/env python3
"""
Test Panel Communication Protocols
Testa diferentes protocolos de comunicación con paneles basado en el ejemplo funcional CP5200
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
    """Implementación del protocolo CP5200 basado en la documentación real"""
    
    def __init__(self):
        self.sequence_number = 0
    
    def _get_sequence_number(self) -> int:
        """Obtener siguiente número de secuencia"""
        self.sequence_number = (self.sequence_number + 1) % 256
        return self.sequence_number
    
    def _ip_to_uint(self, ip_str: str) -> int:
        """Convertir IP string a uint32"""
        parts = ip_str.split('.')
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
    
    def build_init_message(self, ip: str, port: int = 5000, id_code: str = "255.255.255.255", timeout: int = 600) -> bytes:
        """Construir mensaje de inicialización CP5200_Net_Init"""
        dw_ip = self._ip_to_uint(ip)
        dw_id_code = self._ip_to_uint(id_code)
        
        # Formato basado en CP5200_Net_Init: (uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut)
        # Usamos un formato más simple para testing
        message = struct.pack('>BBIII', 0x01, self._get_sequence_number(), dw_ip, port, dw_id_code)
        return message
    
    def build_text_message(self, card_id: int, window: int, text: str, color: int = 0xFF, 
                          font_size: int = 16, speed: int = 3, effect: int = 0, 
                          stay_time: int = 3, alignment: int = 5) -> bytes:
        """Construir mensaje de texto CP5200_Net_SendText"""
        # Convertir texto a bytes
        text_bytes = text.encode('utf-8')
        
        # Formato basado en CP5200_Net_SendText: (int nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment)
        message = struct.pack('>BBBB', 0x02, self._get_sequence_number(), card_id, window)
        message += struct.pack('>I', len(text_bytes))  # Longitud del texto
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
        message += struct.pack('>IIIIII', color, font_size, alignment, x, y, width, height)
        
        return message
    
    def send_message_tcp(self, ip: str, port: int, message: bytes) -> bool:
        """Enviar mensaje TCP al panel"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((ip, port))
            sock.send(message)
            
            # Intentar recibir respuesta
            sock.settimeout(2.0)
            try:
                response = sock.recv(1024)
                print(f"      Respuesta recibida: {response}")
            except socket.timeout:
                print(f"      Sin respuesta (timeout)")
            
            sock.close()
            return True
            
        except Exception as e:
            print(f"      Error enviando mensaje TCP: {e}")
            return False

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

def test_tcp_connection(ip: str, port: int, timeout: float = 5.0) -> bool:
    """Testear conexión TCP a un puerto específico"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testando TCP {ip}:{port}: {e}")
        return False

def test_cp5200_protocol(panel: Dict) -> Dict:
    """Testear protocolo CP5200 con un panel"""
    print(f"\n=== Testeando Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'parking': panel['parking'],
        'ping_status': False,
        'tcp_ports': {},
        'cp5200_init': False,
        'cp5200_text': False,
        'cp5200_static': False,
        'errors': []
    }
    
    # 1. Test ping
    print(f"1. Testeando ping...")
    results['ping_status'] = ping_panel(panel['ip'])
    print(f"   Ping: {'✅ OK' if results['ping_status'] else '❌ FAIL'}")
    
    if not results['ping_status']:
        results['errors'].append("Panel no responde al ping")
        return results
    
    # 2. Test puertos TCP comunes
    print(f"2. Testeando puertos TCP...")
    common_ports = [80, 443, 5000, 8080, 8888]
    
    for port in common_ports:
        results['tcp_ports'][port] = test_tcp_connection(panel['ip'], port)
        status = "✅ OK" if results['tcp_ports'][port] else "❌ FAIL"
        print(f"   Puerto {port}: {status}")
    
    # 3. Test protocolo CP5200
    print(f"3. Testeando protocolo CP5200...")
    protocol = CP5200Protocol()
    
    try:
        # Test inicialización
        init_msg = protocol.build_init_message(panel['ip'], 5000)
        print(f"   Mensaje de inicialización construido: {len(init_msg)} bytes")
        results['cp5200_init'] = True
        
        # Test mensaje de texto
        text_msg = protocol.build_text_message(1, 0, "TEST CP5200", 0xFF, 16, 3, 0, 3, 5)
        print(f"   Mensaje de texto construido: {len(text_msg)} bytes")
        results['cp5200_text'] = True
        
        # Test mensaje estático
        static_msg = protocol.build_static_text_message(1, 0, "STATIC TEST", 0xFF, 16, 0, 0, 0, 64, 32)
        print(f"   Mensaje estático construido: {len(static_msg)} bytes")
        results['cp5200_static'] = True
        
        print(f"   Protocolo CP5200: ✅ OK")
        
    except Exception as e:
        error_msg = f"Error en protocolo CP5200: {e}"
        print(f"   Protocolo CP5200: ❌ FAIL - {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def test_http_protocol(panel: Dict) -> Dict:
    """Testear protocolo HTTP con un panel"""
    print(f"\n=== Testeando HTTP Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'http_status': False,
        'response_code': None,
        'response_time': None,
        'errors': []
    }
    
    try:
        import requests
        
        # Test endpoint /update
        url = f"http://{panel['ip']}/update"
        payload = {"message": "TEST HTTP"}
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=5)
        response_time = time.time() - start_time
        
        results['http_status'] = response.status_code == 200
        results['response_code'] = response.status_code
        results['response_time'] = response_time
        
        print(f"   HTTP POST {url}: {response.status_code}")
        print(f"   Tiempo de respuesta: {response_time:.3f}s")
        print(f"   Estado: {'✅ OK' if results['http_status'] else '❌ FAIL'}")
        
    except requests.exceptions.ConnectionError:
        error_msg = "Conexión HTTP rechazada"
        results['errors'].append(error_msg)
        print(f"   HTTP: ❌ FAIL - {error_msg}")
    except requests.exceptions.Timeout:
        error_msg = "Timeout HTTP"
        results['errors'].append(error_msg)
        print(f"   HTTP: ❌ FAIL - {error_msg}")
    except Exception as e:
        error_msg = f"Error HTTP: {e}"
        results['errors'].append(error_msg)
        print(f"   HTTP: ❌ FAIL - {error_msg}")
    
    return results

def test_raw_tcp_protocol(panel: Dict) -> Dict:
    """Testear protocolo TCP raw con un panel"""
    print(f"\n=== Testeando TCP Raw Panel {panel['id']}: {panel['name']} ({panel['ip']}) ===")
    
    results = {
        'panel_id': panel['id'],
        'panel_name': panel['name'],
        'ip': panel['ip'],
        'tcp_raw_status': False,
        'connection_time': None,
        'errors': []
    }
    
    try:
        # Intentar conexión TCP directa
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((panel['ip'], 5000))
        connection_time = time.time() - start_time
        
        # Enviar mensaje de prueba
        test_message = b"TEST TCP RAW MESSAGE\n"
        sock.send(test_message)
        
        # Intentar recibir respuesta
        sock.settimeout(2.0)
        try:
            response = sock.recv(1024)
            print(f"   Respuesta recibida: {response}")
        except socket.timeout:
            print(f"   Sin respuesta (timeout)")
        
        sock.close()
        
        results['tcp_raw_status'] = True
        results['connection_time'] = connection_time
        
        print(f"   Conexión TCP establecida en {connection_time:.3f}s")
        print(f"   Estado: ✅ OK")
        
    except socket.timeout:
        error_msg = "Timeout en conexión TCP"
        results['errors'].append(error_msg)
        print(f"   TCP Raw: ❌ FAIL - {error_msg}")
    except ConnectionRefusedError:
        error_msg = "Conexión TCP rechazada"
        results['errors'].append(error_msg)
        print(f"   TCP Raw: ❌ FAIL - {error_msg}")
    except Exception as e:
        error_msg = f"Error TCP Raw: {e}"
        results['errors'].append(error_msg)
        print(f"   TCP Raw: ❌ FAIL - {error_msg}")
    
    return results

def main():
    """Función principal"""
    print("🚦 TESTEANDO PROTOCOLOS DE COMUNICACIÓN CON PANELES")
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
            'cp5200_test': test_cp5200_protocol(panel),
            'http_test': test_http_protocol(panel),
            'tcp_raw_test': test_raw_tcp_protocol(panel)
        }
        
        all_results['panels'].append(panel_results)
        
        # Resumen del panel
        print(f"\n📊 RESUMEN PANEL {panel['id']}:")
        print(f"   Ping: {'✅' if panel_results['cp5200_test']['ping_status'] else '❌'}")
        print(f"   CP5200: {'✅' if panel_results['cp5200_test']['cp5200_init'] else '❌'}")
        print(f"   HTTP: {'✅' if panel_results['http_test']['http_status'] else '❌'}")
        print(f"   TCP Raw: {'✅' if panel_results['tcp_raw_test']['tcp_raw_status'] else '❌'}")
    
    # Resumen general
    print(f"\n{'='*60}")
    print("📊 RESUMEN GENERAL")
    print(f"{'='*60}")
    
    total_panels = len(PANELS)
    ping_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['ping_status'])
    cp5200_ok = sum(1 for p in all_results['panels'] if p['cp5200_test']['cp5200_init'])
    http_ok = sum(1 for p in all_results['panels'] if p['http_test']['http_status'])
    tcp_raw_ok = sum(1 for p in all_results['panels'] if p['tcp_raw_test']['tcp_raw_status'])
    
    print(f"Total paneles: {total_panels}")
    print(f"Ping OK: {ping_ok}/{total_panels} ({ping_ok/total_panels*100:.1f}%)")
    print(f"CP5200 OK: {cp5200_ok}/{total_panels} ({cp5200_ok/total_panels*100:.1f}%)")
    print(f"HTTP OK: {http_ok}/{total_panels} ({http_ok/total_panels*100:.1f}%)")
    print(f"TCP Raw OK: {tcp_raw_ok}/{total_panels} ({tcp_raw_ok/total_panels*100:.1f}%)")
    
    # Guardar resultados
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"panel_protocol_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filename}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if ping_ok > 0 and http_ok == 0 and tcp_raw_ok == 0:
        print("   - Los paneles responden al ping pero no a HTTP/TCP")
        print("   - Posible: paneles apagados, firewall, o protocolo diferente")
        print("   - Verificar: estado físico de paneles y configuración de red")
    elif cp5200_ok > 0:
        print("   - Protocolo CP5200 disponible")
        print("   - Implementar comunicación nativa con paneles")
    elif http_ok > 0:
        print("   - Protocolo HTTP disponible")
        print("   - Continuar con implementación HTTP actual")

if __name__ == "__main__":
    main() 