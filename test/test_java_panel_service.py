#!/usr/bin/env python3
"""
Script de prueba para el servicio Java de comunicación con paneles LED
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración del servicio
BASE_URL = "http://localhost:5002/api"
TIMEOUT = 10

def log(message):
    """Función de logging con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_health_check():
    """Prueba el endpoint de health check"""
    log("🔍 Probando health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/panel/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            log(f"✅ Health check exitoso: {data.get('message', 'OK')}")
            return True
        else:
            log(f"❌ Health check falló: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error en health check: {e}")
        return False

def test_get_colors():
    """Prueba el endpoint de colores disponibles"""
    log("🎨 Probando obtención de colores...")
    
    try:
        response = requests.get(f"{BASE_URL}/panel/colors", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            colors = data.get('data', {})
            log(f"✅ Colores obtenidos: {len(colors)} colores disponibles")
            for color_name, color_value in colors.items():
                log(f"   - {color_name}: {color_value}")
            return True
        else:
            log(f"❌ Error al obtener colores: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al obtener colores: {e}")
        return False

def test_send_message(panel_ip="172.20.5.50"):
    """Prueba el envío de mensaje a un panel"""
    log(f"📤 Probando envío de mensaje a panel {panel_ip}...")
    
    message_data = {
        "panelIP": panel_ip,
        "message": f"TEST JAVA SERVICE - {datetime.now().strftime('%H:%M:%S')}",
        "color": 0x00FF00,  # Verde
        "fontSize": 16,
        "speed": 3,
        "effect": 0,
        "stayTime": 5,
        "alignment": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/send",
            json=message_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            response_time = data.get('responseTime', 0)
            log(f"✅ Mensaje enviado exitosamente en {response_time}ms")
            return True
        else:
            log(f"❌ Error al enviar mensaje: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al enviar mensaje: {e}")
        return False

def test_send_occupancy(panel_ip="172.20.5.50"):
    """Prueba el envío de información de ocupación"""
    log(f"📊 Probando envío de ocupación a panel {panel_ip}...")
    
    occupancy_data = {
        "panelIP": panel_ip,
        "current": 45,
        "total": 500,
        "status": "LLIURE",
        "parkingName": "P. Ciutat Esportiva",
        "color": 0x00FF00,
        "fontSize": 16,
        "speed": 2,
        "alignment": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/occupancy",
            json=occupancy_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            response_time = data.get('responseTime', 0)
            log(f"✅ Ocupación enviada exitosamente en {response_time}ms")
            return True
        else:
            log(f"❌ Error al enviar ocupación: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al enviar ocupación: {e}")
        return False

def test_broadcast():
    """Prueba el broadcast a todos los paneles"""
    log("📢 Probando broadcast a todos los paneles...")
    
    broadcast_data = {
        "message": f"BROADCAST TEST - {datetime.now().strftime('%H:%M:%S')}",
        "color": 0xFFFF00,  # Amarillo
        "fontSize": 16,
        "speed": 3,
        "alignment": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/broadcast",
            json=broadcast_data,
            timeout=TIMEOUT * 2  # Más tiempo para broadcast
        )
        
        if response.status_code == 200:
            data = response.json()
            response_time = data.get('responseTime', 0)
            success_count = data.get('data', {}).get('successCount', 0)
            total_count = data.get('data', {}).get('totalCount', 0)
            log(f"✅ Broadcast completado en {response_time}ms: {success_count}/{total_count} paneles")
            return True
        else:
            log(f"❌ Error en broadcast: {response.status_code}")
            log(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error en broadcast: {e}")
        return False

def test_panel_connectivity(panel_ip="172.20.5.50"):
    """Prueba la conectividad con un panel específico"""
    log(f"🔌 Probando conectividad con panel {panel_ip}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/panel/test/{panel_ip}",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            response_time = data.get('responseTime', 0)
            log(f"✅ Panel {panel_ip} responde correctamente en {response_time}ms")
            return True
        else:
            log(f"❌ Panel {panel_ip} no responde: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al probar panel {panel_ip}: {e}")
        return False

def test_get_status():
    """Prueba la obtención del estado de paneles"""
    log("📋 Probando obtención de estado de paneles...")
    
    try:
        response = requests.get(f"{BASE_URL}/panel/status", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            initialized_panels = data.get('data', {}).get('initializedPanels', {})
            total_panels = data.get('data', {}).get('totalPanels', 0)
            online_panels = data.get('data', {}).get('onlinePanels', 0)
            
            log(f"✅ Estado obtenido: {online_panels}/{total_panels} paneles online")
            for panel_ip, status in initialized_panels.items():
                status_text = "🟢 ONLINE" if status else "🔴 OFFLINE"
                log(f"   - {panel_ip}: {status_text}")
            return True
        else:
            log(f"❌ Error al obtener estado: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al obtener estado: {e}")
        return False

def test_clear_cache():
    """Prueba la limpieza de cache"""
    log("🧹 Probando limpieza de cache...")
    
    try:
        response = requests.post(f"{BASE_URL}/panel/clear-cache", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            log(f"✅ Cache limpiada: {data.get('message', 'OK')}")
            return True
        else:
            log(f"❌ Error al limpiar cache: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Error al limpiar cache: {e}")
        return False

def run_comprehensive_test():
    """Ejecuta todas las pruebas de forma comprehensiva"""
    log("🚀 Iniciando pruebas comprehensivas del servicio Java de paneles")
    log("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Obtener Colores", test_get_colors),
        ("Estado de Paneles", test_get_status),
        ("Conectividad Panel", lambda: test_panel_connectivity("172.20.5.50")),
        ("Envío Mensaje", lambda: test_send_message("172.20.5.50")),
        ("Envío Ocupación", lambda: test_send_occupancy("172.20.5.50")),
        ("Broadcast", test_broadcast),
        ("Limpieza Cache", test_clear_cache)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        log(f"\n📝 Ejecutando: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                log(f"✅ {test_name}: EXITOSO")
            else:
                log(f"❌ {test_name}: FALLIDO")
        except Exception as e:
            log(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Pausa entre pruebas
    
    # Resumen de resultados
    log("\n" + "=" * 60)
    log("📊 RESUMEN DE PRUEBAS")
    log("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        log(f"{status} - {test_name}")
    
    log(f"\n🎯 Resultado Final: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        log("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return True
    else:
        log("⚠️  Algunas pruebas fallaron. Revisar logs para más detalles.")
        return False

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "health":
            test_health_check()
        elif command == "colors":
            test_get_colors()
        elif command == "status":
            test_get_status()
        elif command == "test":
            panel_ip = sys.argv[2] if len(sys.argv) > 2 else "172.20.5.50"
            test_panel_connectivity(panel_ip)
        elif command == "send":
            panel_ip = sys.argv[2] if len(sys.argv) > 2 else "172.20.5.50"
            test_send_message(panel_ip)
        elif command == "occupancy":
            panel_ip = sys.argv[2] if len(sys.argv) > 2 else "172.20.5.50"
            test_send_occupancy(panel_ip)
        elif command == "broadcast":
            test_broadcast()
        elif command == "clear":
            test_clear_cache()
        else:
            print("Comandos disponibles:")
            print("  health     - Health check")
            print("  colors     - Obtener colores")
            print("  status     - Estado de paneles")
            print("  test [IP]  - Probar conectividad")
            print("  send [IP]  - Enviar mensaje")
            print("  occupancy [IP] - Enviar ocupación")
            print("  broadcast  - Broadcast a todos")
            print("  clear      - Limpiar cache")
            print("  all        - Ejecutar todas las pruebas")
    else:
        # Ejecutar todas las pruebas por defecto
        run_comprehensive_test()

if __name__ == "__main__":
    main() 