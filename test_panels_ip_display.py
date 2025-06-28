#!/usr/bin/env python3
"""
Script de prueba para enviar a cada panel su IP
Usa el servicio C# actualizado con colores correctos del SDK CP5200
"""

import requests
import json
import time
from datetime import datetime

# Configuración del servicio de paneles
PANEL_SERVICE_URL = "http://157.180.91.63:5001"

# Lista de paneles configurados (IPs reales de la base de datos)
PANELS = [
    {"ip": "172.20.17.50", "name": "PANEL C. ESPORTIVA", "parking": "P. Ciutat Esportiva"},
    {"ip": "172.20.5.50", "name": "PANEL BASSETA 1", "parking": "P. Poble antic 1"},
    {"ip": "172.20.5.51", "name": "PANEL BASSETA 2", "parking": "P. Poble antic 2"},
    {"ip": "172.20.8.50", "name": "PANEL PITERES", "parking": "P. Poble antic 3"},
    {"ip": "172.20.4.50", "name": "PANEL PALAU", "parking": "P. Poble antic 4"},
    {"ip": "172.20.4.51", "name": "PANEL COCOLISO", "parking": "P. Poble antic 5"},
    {"ip": "172.20.4.52", "name": "BELLES ARTS 2", "parking": "P. Port Altea"},
    {"ip": "172.20.4.53", "name": "BELLES ARTS", "parking": "P. Estació Altea"},
    {"ip": "172.20.2.50", "name": "PANEL RENFE", "parking": "P. Altea Hills"},
    {"ip": "172.20.1.50", "name": "PANEL ALTEA VELLA", "parking": "P. Ciutat Esportiva"}
]

def test_panel_service():
    """Prueba la conectividad del servicio de paneles"""
    try:
        response = requests.get(f"{PANEL_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servicio de paneles funcionando correctamente")
            return True
        else:
            print(f"❌ Servicio de paneles respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio de paneles: {e}")
        return False

def send_message_to_panel(panel_ip, message, color=0x00FF00):
    """Envía un mensaje a un panel específico"""
    try:
        payload = {
            "panelIP": panel_ip,
            "message": message,
            "color": color,
            "fontSize": 16,
            "speed": 3,
            "effect": 0,
            "stayTime": 10,
            "alignment": 5
        }
        
        response = requests.post(
            f"{PANEL_SERVICE_URL}/api/panel/send",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"❌ Error enviando mensaje a {panel_ip}: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Excepción enviando mensaje a {panel_ip}: {e}")
        return None

def test_all_panels_ip():
    """Envía a cada panel su IP para verificar funcionamiento"""
    print(f"\n🚀 Iniciando prueba de envío de IPs a paneles - {datetime.now()}")
    print("=" * 60)
    
    # Verificar servicio primero
    if not test_panel_service():
        return
    
    results = []
    
    for i, panel in enumerate(PANELS, 1):
        panel_ip = panel["ip"]
        panel_name = panel["name"]
        parking_name = panel["parking"]
        
        print(f"\n📺 Panel {i}: {panel_name} ({panel_ip})")
        print(f"   Parking: {parking_name}")
        
        # Mensaje simple con solo la IP del panel
        message = panel_ip
        
        # Color verde para la prueba
        color = 0x00FF00  # Verde según SDK CP5200
        
        print(f"   Enviando: '{message}'")
        
        # Enviar mensaje
        result = send_message_to_panel(panel_ip, message, color)
        
        if result:
            success = result.get("success", False)
            response_time = result.get("responseTime", 0)
            error_code = result.get("errorCode", -1)
            
            if success:
                print(f"   ✅ Éxito - Tiempo: {response_time}ms")
                results.append({"panel": panel_name, "ip": panel_ip, "status": "SUCCESS", "time": response_time})
            else:
                print(f"   ❌ Fallo - Código: {error_code} - {result.get('message', 'Sin mensaje')}")
                results.append({"panel": panel_name, "ip": panel_ip, "status": "FAILED", "error": error_code})
        else:
            print(f"   ❌ Sin respuesta del servicio")
            results.append({"panel": panel_name, "ip": panel_ip, "status": "NO_RESPONSE"})
        
        # Pausa entre envíos
        time.sleep(1)
    
    # Resumen de resultados
    print(f"\n📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    failed_count = len(results) - success_count
    
    print(f"Total paneles: {len(results)}")
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Fallidos: {failed_count}")
    print(f"📈 Tasa de éxito: {(success_count/len(results)*100):.1f}%")
    
    if success_count > 0:
        avg_time = sum(r["time"] for r in results if r["status"] == "SUCCESS") / success_count
        print(f"⏱️  Tiempo promedio: {avg_time:.1f}ms")
    
    # Detalles de fallos
    if failed_count > 0:
        print(f"\n❌ PANELES CON PROBLEMAS:")
        for result in results:
            if result["status"] != "SUCCESS":
                print(f"   - {result['panel']} ({result['ip']}): {result['status']}")
    
    return results

def test_specific_panel(panel_ip):
    """Prueba un panel específico"""
    print(f"\n🎯 Probando panel específico: {panel_ip}")
    
    # Buscar información del panel
    panel_info = next((p for p in PANELS if p["ip"] == panel_ip), None)
    if not panel_info:
        print(f"❌ Panel {panel_ip} no encontrado en la configuración")
        return
    
    message = f"TEST PANEL\n{panel_ip}\n{panel_info['name']}"
    color = 0x00FFFF  # Amarillo para test
    
    print(f"Enviando mensaje de prueba: '{message}'")
    
    result = send_message_to_panel(panel_ip, message, color)
    
    if result:
        success = result.get("success", False)
        if success:
            print(f"✅ Test exitoso - Tiempo: {result.get('responseTime', 0)}ms")
        else:
            print(f"❌ Test fallido - {result.get('message', 'Sin mensaje')}")
    else:
        print("❌ Sin respuesta del servicio")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Si se proporciona una IP específica, probar solo ese panel
        panel_ip = sys.argv[1]
        test_specific_panel(panel_ip)
    else:
        # Probar todos los paneles
        test_all_panels_ip() 