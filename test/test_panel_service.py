#!/usr/bin/env python3
"""
Test del Servicio de Paneles C#
Prueba la comunicación con el servicio .NET
"""

import time
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from panel_service_client import PanelServiceClient, get_panel_client

def test_service_connectivity():
    """Test de conectividad con el servicio"""
    print("🔌 TESTEANDO CONECTIVIDAD CON EL SERVICIO")
    print("=" * 50)
    
    client = get_panel_client()
    
    # Test de salud del servicio
    print("1. Verificando salud del servicio...")
    if client.is_service_online():
        print("   ✅ Servicio online")
    else:
        print("   ❌ Servicio offline")
        return False
    
    return True

def test_panel_status():
    """Test de estado de paneles"""
    print("\n📊 TESTEANDO ESTADO DE PANELES")
    print("=" * 50)
    
    client = get_panel_client()
    
    # Obtener estado de todos los paneles
    print("1. Obteniendo estado de todos los paneles...")
    panels = client.get_all_panels_status()
    
    if not panels:
        print("   ❌ No se pudieron obtener los paneles")
        return False
    
    print(f"   ✅ {len(panels)} paneles encontrados")
    
    # Mostrar estado de cada panel
    for panel in panels:
        status_icon = "✅" if panel.online else "❌"
        print(f"   {status_icon} {panel.ip}: {panel.status}")
    
    return True

def test_single_panel():
    """Test de un panel específico"""
    print("\n🎯 TESTEANDO PANEL ESPECÍFICO")
    print("=" * 50)
    
    client = get_panel_client()
    test_panel_ip = "172.20.17.50"  # Panel C. ESPORTIVA
    
    print(f"1. Testeando panel {test_panel_ip}...")
    
    # Test de estado
    status = client.get_panel_status(test_panel_ip)
    if status:
        print(f"   Estado: {'✅ ONLINE' if status.online else '❌ OFFLINE'}")
        print(f"   Status: {status.status}")
    else:
        print("   ❌ No se pudo obtener el estado")
        return False
    
    # Test de comunicación
    print("2. Testeando comunicación...")
    test_result = client.test_panel(test_panel_ip)
    print(f"   Test: {'✅ OK' if test_result.success else '❌ FAIL'}")
    print(f"   Mensaje: {test_result.message}")
    
    return test_result.success

def test_message_sending():
    """Test de envío de mensajes"""
    print("\n📤 TESTEANDO ENVÍO DE MENSAJES")
    print("=" * 50)
    
    client = get_panel_client()
    test_panel_ip = "172.20.17.50"
    
    # Test de mensaje simple
    print("1. Enviando mensaje simple...")
    message = f"TEST PYTHON {time.strftime('%H:%M:%S')}"
    response = client.send_message(test_panel_ip, message)
    
    print(f"   Envío: {'✅ OK' if response.success else '❌ FAIL'}")
    print(f"   Mensaje: {response.message}")
    print(f"   Tiempo: {response.response_time:.2f}ms")
    
    if response.success:
        print(f"   📺 El panel debería mostrar: '{message}'")
    
    return response.success

def test_occupancy_sending():
    """Test de envío de ocupación"""
    print("\n🚗 TESTEANDO ENVÍO DE OCUPACIÓN")
    print("=" * 50)
    
    client = get_panel_client()
    test_panel_ip = "172.20.17.50"
    
    # Test de ocupación
    print("1. Enviando información de ocupación...")
    response = client.send_occupancy(test_panel_ip, 150, 250, "LLIURE")
    
    print(f"   Envío: {'✅ OK' if response.success else '❌ FAIL'}")
    print(f"   Mensaje: {response.message}")
    print(f"   Tiempo: {response.response_time:.2f}ms")
    
    if response.success:
        print(f"   📺 El panel debería mostrar: '1 - P. Ciutat Esportiva: 150/250 (LLIURE)'")
    
    return response.success

def test_broadcast():
    """Test de broadcast"""
    print("\n📢 TESTEANDO BROADCAST")
    print("=" * 50)
    
    client = get_panel_client()
    
    # Test de broadcast
    print("1. Enviando broadcast...")
    broadcast_message = f"BROADCAST TEST {time.strftime('%H:%M:%S')}"
    response = client.broadcast_message(broadcast_message)
    
    print(f"   Total paneles: {response.total_panels}")
    print(f"   Exitosos: {response.success_count}")
    print(f"   Fallidos: {response.failure_count}")
    
    if response.success_count > 0:
        print(f"   📺 Los paneles deberían mostrar: '{broadcast_message}'")
    
    return response.success_count > 0

def test_static_text():
    """Test de texto estático"""
    print("\n📋 TESTEANDO TEXTO ESTÁTICO")
    print("=" * 50)
    
    client = get_panel_client()
    test_panel_ip = "172.20.17.50"
    
    # Test de texto estático
    print("1. Enviando texto estático...")
    static_text = f"PANEL TEST\n{time.strftime('%H:%M:%S')}"
    response = client.send_static_text(test_panel_ip, static_text)
    
    print(f"   Envío: {'✅ OK' if response.success else '❌ FAIL'}")
    print(f"   Mensaje: {response.message}")
    print(f"   Tiempo: {response.response_time:.2f}ms")
    
    if response.success:
        print(f"   📺 El panel debería mostrar estáticamente: '{static_text}'")
    
    return response.success

def main():
    """Función principal"""
    print("🚦 TESTEANDO SERVICIO DE PANELES C#")
    print("=" * 60)
    print("Este test verifica la comunicación con el servicio .NET")
    print("Asegúrate de que el servicio esté ejecutándose en http://localhost:5001")
    print("=" * 60)
    
    tests = [
        ("Conectividad", test_service_connectivity),
        ("Estado de Paneles", test_panel_status),
        ("Panel Específico", test_single_panel),
        ("Envío de Mensajes", test_message_sending),
        ("Envío de Ocupación", test_occupancy_sending),
        ("Broadcast", test_broadcast),
        ("Texto Estático", test_static_text)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: EXITOSO")
            else:
                print(f"❌ {test_name}: FALLIDO")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN FINAL")
    print(f"{'='*60}")
    
    total_tests = len(results)
    successful_tests = sum(1 for _, result in results if result)
    
    print(f"Total tests: {total_tests}")
    print(f"Exitosos: {successful_tests}")
    print(f"Fallidos: {total_tests - successful_tests}")
    print(f"Porcentaje éxito: {successful_tests/total_tests*100:.1f}%")
    
    print(f"\n📋 RESULTADOS DETALLADOS:")
    for test_name, result in results:
        status = "✅ EXITOSO" if result else "❌ FALLIDO"
        print(f"  {test_name}: {status}")
    
    if successful_tests == total_tests:
        print(f"\n🎉 ¡TODOS LOS TESTS EXITOSOS!")
        print("   - El servicio C# está funcionando correctamente")
        print("   - Se puede integrar con el backend Python")
        print("   - Verificar físicamente que los paneles muestran los mensajes")
    else:
        print(f"\n⚠️  ALGUNOS TESTS FALLARON")
        print("   - Revisar que el servicio C# esté ejecutándose")
        print("   - Verificar conectividad de red")
        print("   - Revisar logs del servicio")

if __name__ == "__main__":
    main() 