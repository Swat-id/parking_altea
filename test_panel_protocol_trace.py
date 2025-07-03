#!/usr/bin/env python3
"""
Script de prueba para verificar la trazabilidad del protocolo antiguo
con el panel 172.20.4.52 (Belles Arts 2)
"""

import requests
import json
import time
from datetime import datetime

def test_old_protocol_trace():
    """Probar la trazabilidad del protocolo antiguo"""
    
    print("🔍 INICIANDO PRUEBA DE TRAZABILIDAD - PROTOCOLO ANTIGUO")
    print("=" * 60)
    
    # Configuración
    panel_ip = "172.20.4.52"
    java_api_url = "http://127.0.0.1:5656/sendMulti"
    
    # Test 1: Verificar que el servicio está respondiendo
    print(f"\n1️⃣ Verificando servicio Java en puerto 5656...")
    try:
        response = requests.get("http://127.0.0.1:5656/health", timeout=5)
        print(f"   ✅ Servicio respondiendo: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error conectando al servicio: {e}")
        return False
    
    # Test 2: Enviar mensaje de prueba con formato correcto
    print(f"\n2️⃣ Enviando mensaje de prueba a {panel_ip}...")
    
    # Crear payload con formato correcto para el servicio antiguo
    payload = {
        "ip": panel_ip,
        "itemNum": 1,
        "texts": ["EN PROVES"],
        "colors": [1],  # Rojo
        "fontSizes": [16],
        "showEffects": [1]
    }
    
    print(f"   📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            java_api_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 Respuesta HTTP: {response.status_code}")
        print(f"   📄 Contenido: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ Mensaje enviado exitosamente")
                return True
            else:
                print(f"   ❌ Error en respuesta: {result.get('message')}")
                return False
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error enviando mensaje: {e}")
        return False

def test_backend_integration():
    """Probar la integración con el backend"""
    
    print(f"\n3️⃣ Probando integración con backend...")
    
    # Cambiar aforo del parking 4 para forzar estado COMPLETO
    parking_id = 4
    new_occupancy = 43  # Esto debería forzar estado COMPLETO
    
    print(f"   📊 Cambiando aforo del parking {parking_id} a {new_occupancy}...")
    
    try:
        response = requests.put(
            f"http://127.0.0.1:5000/api/parkings/{parking_id}",
            json={"current_occupancy": new_occupancy},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 Respuesta HTTP: {response.status_code}")
        print(f"   📄 Contenido: {response.text}")
        
        if response.status_code == 200:
            print(f"   ✅ Aforo actualizado correctamente")
            return True
        else:
            print(f"   ❌ Error actualizando aforo: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en integración: {e}")
        return False

def main():
    """Función principal"""
    
    print(f"🚀 INICIO DE PRUEBA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Protocolo antiguo directo
    success1 = test_old_protocol_trace()
    
    # Test 2: Integración con backend
    success2 = test_backend_integration()
    
    print(f"\n" + "=" * 60)
    print(f"📋 RESUMEN DE PRUEBAS:")
    print(f"   Protocolo Antiguo Directo: {'✅ EXITOSO' if success1 else '❌ FALLIDO'}")
    print(f"   Integración Backend: {'✅ EXITOSO' if success2 else '❌ FALLIDO'}")
    
    if success1 and success2:
        print(f"\n🎉 TODAS LAS PRUEBAS EXITOSAS")
        print(f"   El protocolo antiguo está funcionando correctamente")
        print(f"   La trazabilidad está completa")
    else:
        print(f"\n⚠️  ALGUNAS PRUEBAS FALLIDAS")
        print(f"   Revisar logs para más detalles")
    
    print(f"\n🏁 FIN DE PRUEBA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 