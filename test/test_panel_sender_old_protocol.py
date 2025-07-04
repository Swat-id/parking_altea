#!/usr/bin/env python3
"""
Script de prueba para PanelSender_oldProtocol.py

Este script prueba el nuevo servicio que implementa la librería Java del fabricante
para enviar mensajes a paneles LED usando el protocolo antiguo.

Autor: Parking Altea Team
Fecha: 2025-07-04
"""

import requests
import json
import time
import sys
import os

# Configuración
SERVICE_URL = "http://127.0.0.1:7777"
TEST_PANEL_IP = "172.20.4.52"

def test_health():
    """Probar endpoint de salud"""
    print("🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health OK: {data}")
            return True
        else:
            print(f"❌ Health failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en health: {e}")
        return False

def test_init_network():
    """Probar inicialización de red"""
    print(f"\n🔍 Probando inicialización de red para {TEST_PANEL_IP}...")
    try:
        data = {
            "ip": TEST_PANEL_IP,
            "port": 5200,
            "idcode": "255.255.255.255"
        }
        response = requests.post(f"{SERVICE_URL}/initNetwork", json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Red inicializada: {result}")
                return True
            else:
                print(f"❌ Error inicializando red: {result}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en init_network: {e}")
        return False

def test_send_text():
    """Probar envío de texto"""
    print(f"\n🔍 Probando envío de texto a {TEST_PANEL_IP}...")
    try:
        data = {
            "ip": TEST_PANEL_IP,
            "windowNo": 0,
            "content": "TEST PANEL SENDER",
            "color": 1,  # Rojo
            "fontSize": 2,  # 16px
            "speed": 1,
            "effect": 0,
            "stayTime": 5,
            "alignmentHori": 1,  # Centro
            "alignmentVert": 1   # Centro
        }
        response = requests.post(f"{SERVICE_URL}/sendText", json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Texto enviado: {result}")
                return True
            else:
                print(f"❌ Error enviando texto: {result}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en send_text: {e}")
        return False

def test_send_multi():
    """Probar envío de múltiples textos"""
    print(f"\n🔍 Probando envío de múltiples textos a {TEST_PANEL_IP}...")
    try:
        data = {
            "ip": TEST_PANEL_IP,
            "itemNum": 2,
            "texts": ["TEXTO 1", "TEXTO 2"],
            "colors": [1, 2],  # Rojo, Verde
            "fontSizes": [2, 2],  # 16px, 16px
            "showEffects": [0, 0]
        }
        response = requests.post(f"{SERVICE_URL}/sendMulti", json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Múltiples textos enviados: {result}")
                return True
            else:
                print(f"❌ Error enviando múltiples textos: {result}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en send_multi: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de PanelSender_oldProtocol")
    print("=" * 50)
    
    # Verificar que el servicio esté corriendo
    if not test_health():
        print("❌ El servicio no está disponible. Asegúrate de que esté corriendo en puerto 7777")
        sys.exit(1)
    
    # Ejecutar pruebas
    tests = [
        ("Inicialización de red", test_init_network),
        ("Envío de texto", test_send_text),
        ("Envío de múltiples textos", test_send_multi)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
        time.sleep(2)  # Pausa entre pruebas
    
    # Resumen de resultados
    print("\n" + "="*50)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("⚠️  Algunas pruebas fallaron")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 