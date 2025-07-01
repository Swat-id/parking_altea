#!/usr/bin/env python3
"""
Script de prueba para el nuevo servicio de paneles v2.6
Verifica la comunicación con el servicio Java en puerto 5656
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuración
SERVICE_URL = "http://157.180.91.63:5656/sendMulti"
API_BASE_URL = "http://157.180.91.63:6001"

def test_service_connection():
    """Probar conexión con el servicio v2.6"""
    print("🔍 PROBANDO CONEXIÓN CON SERVICIO v2.6")
    print("=" * 60)
    
    try:
        # Test básico de conexión
        test_payload = {
            "ip": "192.168.1.101",
            "itemNum": 1,
            "texts": ["PRUEBA"],
            "colors": [2],
            "fontSizes": [2],
            "showEffects": [1]
        }
        
        response = requests.post(SERVICE_URL, json=test_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Servicio v2.6 disponible")
            print(f"  - Status: {response.status_code}")
            print(f"  - Response: {result}")
            return True
        else:
            print(f"❌ Error en servicio v2.6: {response.status_code}")
            print(f"  - Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al servicio v2.6 en {SERVICE_URL}")
        return False
    except Exception as e:
        print(f"❌ Error probando servicio: {e}")
        return False

def test_panel_message():
    """Probar envío de mensaje a panel"""
    print("\n📤 PROBANDO ENVÍO DE MENSAJE")
    print("=" * 60)
    
    try:
        # Obtener paneles desde la API
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error obteniendo paneles: {response.status_code}")
            return False
            
        panels = response.json()
        if not panels:
            print("❌ No hay paneles configurados")
            return False
            
        # Usar el primer panel disponible
        panel = panels[0]
        print(f"📺 Usando panel: {panel['name']} ({panel['ip_address']})")
        
        # Enviar mensaje de prueba
        test_payload = {
            "ip": panel['ip_address'],
            "itemNum": 1,
            "texts": ["PRUEBA v2.6"],
            "colors": [2],  # Verde
            "fontSizes": [2],
            "showEffects": [1]
        }
        
        start_time = time.time()
        response = requests.post(SERVICE_URL, json=test_payload, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Mensaje enviado exitosamente")
            print(f"  - Tiempo de respuesta: {response_time:.2f}ms")
            print(f"  - Resultado: {result}")
            return True
        else:
            print(f"❌ Error enviando mensaje: {response.status_code}")
            print(f"  - Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de mensaje: {e}")
        return False

def test_multiple_colors():
    """Probar diferentes colores"""
    print("\n🎨 PROBANDO DIFERENTES COLORES")
    print("=" * 60)
    
    try:
        # Obtener paneles
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        if response.status_code != 200:
            return False
            
        panels = response.json()
        if not panels:
            return False
            
        panel = panels[0]
        
        colors = [
            (1, "Rojo"),
            (2, "Verde"), 
            (3, "Amarillo"),
            (4, "Azul"),
            (5, "Magenta"),
            (6, "Cian"),
            (7, "Blanco")
        ]
        
        for color_code, color_name in colors:
            print(f"🎨 Probando color {color_name} (código {color_code})...")
            
            test_payload = {
                "ip": panel['ip_address'],
                "itemNum": 1,
                "texts": [f"COLOR {color_name}"],
                "colors": [color_code],
                "fontSizes": [2],
                "showEffects": [1]
            }
            
            try:
                response = requests.post(SERVICE_URL, json=test_payload, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"  ✅ {color_name} - OK")
                    else:
                        print(f"  ❌ {color_name} - Error: {result.get('message')}")
                else:
                    print(f"  ❌ {color_name} - HTTP {response.status_code}")
                    
                time.sleep(2)  # Pausa entre colores
                
            except Exception as e:
                print(f"  ❌ {color_name} - Error: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error probando colores: {e}")
        return False

def test_valenciano_messages():
    """Probar mensajes en valenciano"""
    print("\n🏴 PROBANDO MENSAJES EN VALENCIANO")
    print("=" * 60)
    
    try:
        # Obtener paneles
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        if response.status_code != 200:
            return False
            
        panels = response.json()
        if not panels:
            return False
            
        panel = panels[0]
        
        valenciano_messages = [
            ("LLIURE", 2, "Verde"),
            ("DENS", 3, "Amarillo"),
            ("COMPLET", 1, "Rojo")
        ]
        
        for message, color_code, color_name in valenciano_messages:
            print(f"🏴 Probando: {message} ({color_name})...")
            
            test_payload = {
                "ip": panel['ip_address'],
                "itemNum": 1,
                "texts": [message],
                "colors": [color_code],
                "fontSizes": [2],
                "showEffects": [1]
            }
            
            try:
                response = requests.post(SERVICE_URL, json=test_payload, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"  ✅ {message} - OK")
                    else:
                        print(f"  ❌ {message} - Error: {result.get('message')}")
                else:
                    print(f"  ❌ {message} - HTTP {response.status_code}")
                    
                time.sleep(3)  # Pausa entre mensajes
                
            except Exception as e:
                print(f"  ❌ {message} - Error: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error probando mensajes valencianos: {e}")
        return False

def test_frontend_integration():
    """Probar integración con frontend"""
    print("\n🌐 PROBANDO INTEGRACIÓN CON FRONTEND")
    print("=" * 60)
    
    try:
        # Simular llamada del frontend
        frontend_payload = {
            "ip": "192.168.1.101",
            "itemNum": 1,
            "texts": ["MENSAJE FRONTEND"],
            "colors": [1],
            "fontSizes": [2],
            "showEffects": [1]
        }
        
        response = requests.post(SERVICE_URL, json=frontend_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Integración frontend OK")
            print(f"  - Payload: {frontend_payload}")
            print(f"  - Response: {result}")
            return True
        else:
            print(f"❌ Error en integración frontend: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando integración frontend: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 PRUEBA COMPLETA DEL SERVICIO DE PANELES v2.6")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Servicio: {SERVICE_URL}")
    print("=" * 80)
    
    tests = [
        ("Conexión al servicio", test_service_connection),
        ("Envío de mensaje", test_panel_message),
        ("Diferentes colores", test_multiple_colors),
        ("Mensajes valencianos", test_valenciano_messages),
        ("Integración frontend", test_frontend_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El servicio v2.6 está funcionando correctamente.")
        return 0
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar configuración del servicio.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 