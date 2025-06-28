#!/usr/bin/env python3
"""
Script de prueba simple para enviar IPs usando solo SendText
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

def send_message_to_panel(panel_ip, message):
    """Envía un mensaje a un panel específico usando SendText"""
    try:
        payload = {
            "panelIP": panel_ip,
            "message": message,
            "color": 3000,  # Color por defecto del fabricante
            "fontSize": 16,
            "speed": 3,
            "effect": 0,
            "stayTime": 3,  # Según ejemplo del fabricante
            "alignment": 0
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

def test_sendtext_only():
    """Envía a cada panel su IP usando solo SendText"""
    print(f"\n🚀 Iniciando prueba SOLO con SendText - {datetime.now()}")
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
        
        print(f"   Enviando con SendText: '{message}'")
        
        # Enviar mensaje
        result = send_message_to_panel(panel_ip, message)
        
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
        time.sleep(2)
    
    # Resumen de resultados
    print(f"\n📊 RESUMEN DE RESULTADOS (SENDTEXT ONLY)")
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

if __name__ == "__main__":
    test_sendtext_only() 