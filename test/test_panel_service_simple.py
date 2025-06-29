#!/usr/bin/env python3
"""
Script simple para probar el panel-service y enviar la IP al panel 172.20.4.52
"""

import requests
import json
import time

def test_panel_service():
    """Prueba el envío de mensaje al panel usando el panel-service"""
    
    panel_ip = "172.20.4.52"
    service_url = "http://localhost:3210"
    
    print("🧪 PROBANDO PANEL-SERVICE")
    print(f"📍 Panel IP: {panel_ip}")
    print(f"🌐 Servicio: {service_url}")
    print("=" * 50)
    
    # 1. Verificar que el servicio está funcionando
    print("1️⃣ Verificando servicio...")
    try:
        response = requests.get(f"{service_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Servicio funcionando correctamente")
        else:
            print(f"   ❌ Error en servicio: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando al servicio: {e}")
        return False
    
    # 2. Enviar texto al panel
    print("\n2️⃣ Enviando IP al panel...")
    text_data = {
        "window_no": 1,
        "mode": 0,
        "alignment": 0,
        "speed": 10,
        "stay_time": 5,
        "text": panel_ip
    }
    
    try:
        response = requests.post(
            f"{service_url}/send-text", 
            json=text_data, 
            timeout=10
        )
        
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        result = response.json()
        if result.get('status') == 'sent':
            print("   ✅ Mensaje enviado exitosamente")
            print(f"   📝 IP '{panel_ip}' enviada al panel")
            
            if result.get('response'):
                print(f"   📨 Respuesta del panel: {result['response']}")
            else:
                print("   📨 Panel no envió respuesta (normal en algunos protocolos)")
            
            return True
        else:
            print("   ❌ Error enviando mensaje")
            return False
            
    except Exception as e:
        print(f"   ❌ Error enviando mensaje: {e}")
        return False

if __name__ == "__main__":
    success = test_panel_service()
    if success:
        print("\n🎉 ¡Prueba completada exitosamente!")
        print("💡 El panel debería mostrar la IP '172.20.4.52'")
        print("🔍 Verifica físicamente si el panel muestra el texto")
    else:
        print("\n💥 Prueba falló") 