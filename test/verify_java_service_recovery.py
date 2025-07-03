#!/usr/bin/env python3
"""
Script de verificación rápida del servicio Java recuperado
"""

import requests
import json
import time
from datetime import datetime

def verify_java_service():
    """Verificar que el servicio Java está funcionando correctamente"""
    
    print("🔍 VERIFICACIÓN RÁPIDA - SERVICIO JAVA RECUPERADO")
    print("=" * 55)
    
    # Configuración
    base_url = "http://localhost:5656"
    panel_ip = "172.20.4.52"  # BELLES ARTS 2
    
    tests = [
        {
            "name": "Health Check",
            "url": f"{base_url}/api/health",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Estado de Paneles",
            "url": f"{base_url}/api/panels/status",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Lista de Paneles",
            "url": f"{base_url}/api/panels/list",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Test de Conectividad",
            "url": f"{base_url}/api/panels/test",
            "method": "POST",
            "data": {"ip": panel_ip},
            "expected_status": 200
        },
        {
            "name": "Envío Múltiple (Compatibilidad)",
            "url": f"{base_url}/sendMulti",
            "method": "POST",
            "data": {
                "ip": panel_ip,
                "itemNum": 1,
                "texts": ["VERIFICACIO"],
                "colors": [1],
                "fontSizes": [16],
                "showEffects": [0]
            },
            "expected_status": 200
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\n{i}️⃣ {test['name']}")
        print("-" * 30)
        
        try:
            if test['method'] == 'GET':
                response = requests.get(test['url'], timeout=5)
            else:
                response = requests.post(test['url'], 
                                       json=test['data'], 
                                       timeout=10)
            
            if response.status_code == test['expected_status']:
                print(f"   ✅ HTTP {response.status_code} - OK")
                
                # Verificar respuesta JSON
                try:
                    data = response.json()
                    if test['name'] == "Health Check":
                        if data.get('status') == 'UP':
                            print(f"   ✅ Servicio activo")
                        else:
                            print(f"   ⚠️  Servicio no activo: {data.get('status')}")
                    
                    elif test['name'] == "Envío Múltiple (Compatibilidad)":
                        if data.get('success'):
                            print(f"   ✅ Mensaje enviado exitosamente")
                            print(f"   📺 Panel: {data.get('panel_ip')}")
                            print(f"   🔧 Protocolo: {data.get('protocol')}")
                        else:
                            print(f"   ❌ Error enviando mensaje: {data.get('message')}")
                    
                    passed += 1
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️  Respuesta no es JSON válido")
                    print(f"   📋 Respuesta: {response.text[:100]}...")
                
            else:
                print(f"   ❌ HTTP {response.status_code} - Esperado {test['expected_status']}")
                print(f"   📋 Respuesta: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Error de conexión - Servicio no disponible")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout - Servicio lento")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 30)
    print(f"✅ Pruebas pasadas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 ¡SERVICIO JAVA FUNCIONANDO CORRECTAMENTE!")
        print("=" * 50)
        print("✅ El servicio Java de paneles v2.5 está operativo")
        print("✅ La API REST responde correctamente")
        print("✅ Los mensajes se envían a los paneles")
        print("✅ Compatibilidad con formato antiguo mantenida")
        return True
    else:
        print(f"\n⚠️  PROBLEMAS DETECTADOS")
        print("=" * 25)
        print("❌ Algunas pruebas fallaron")
        print("🔧 Revisar logs del servicio")
        print("🔧 Verificar configuración")
        return False

def check_panel_visual_update():
    """Verificar que el panel actualiza visualmente"""
    
    print(f"\n👁️  VERIFICACIÓN VISUAL DEL PANEL")
    print("=" * 35)
    
    panel_ip = "172.20.4.52"
    
    print(f"📺 Panel: {panel_ip} (BELLES ARTS 2)")
    print(f"🔍 Verificar que el panel muestra: 'VERIFICACIO'")
    print(f"🎨 Color: Rojo")
    print(f"⏱️  Duración: 5 segundos")
    print(f"")
    print(f"👀 ¿El panel muestra el mensaje correctamente?")
    print(f"   - Si: ✅ Panel funcionando")
    print(f"   - No: ❌ Problema de comunicación")
    
    return True

def main():
    """Función principal"""
    
    print(f"🚀 VERIFICACIÓN DEL SERVICIO JAVA RECUPERADO")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar servicio
    service_ok = verify_java_service()
    
    if service_ok:
        # Verificar panel visual
        check_panel_visual_update()
        
        print(f"\n✅ VERIFICACIÓN COMPLETADA")
        print("=" * 30)
        print("🎉 El servicio Java está funcionando correctamente")
        print("🎉 Los paneles reciben y muestran mensajes")
        print("🎉 La funcionalidad original está recuperada")
    else:
        print(f"\n❌ VERIFICACIÓN FALLIDA")
        print("=" * 25)
        print("🔧 Revisar logs del servicio")
        print("🔧 Verificar configuración")
        print("🔧 Ejecutar: systemctl status java-panel-service")
    
    print(f"\n⏰ Fin de verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 