#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de ping de paneles
"""

import requests
import json
import sys
from datetime import datetime

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"

def test_panels_endpoint():
    """Probar el endpoint de paneles"""
    print("🔍 PROBANDO ENDPOINT DE PANELES")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        if response.status_code == 200:
            panels = response.json()
            print(f"✅ Endpoint /panels OK - {len(panels)} paneles encontrados")
            
            for panel in panels:
                print(f"  📺 {panel['name']} ({panel['ip_address']}) - {panel['status']}")
            
            return panels
        else:
            print(f"❌ Error en /panels: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error conectando a /panels: {e}")
        return None

def test_verify_panels():
    """Probar el endpoint de verificación de paneles"""
    print("\n🔍 PROBANDO VERIFICACIÓN DE PANELES")
    print("=" * 50)
    
    try:
        response = requests.post(f"{API_BASE_URL}/panels/verify", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Verificación completada")
            print(f"  📊 Total paneles: {data['total_panels']}")
            print(f"  🔄 Actualizados: {data['updated_count']}")
            
            # Mostrar resultados detallados
            print("\n📋 RESULTADOS DETALLADOS:")
            for result in data['results']:
                status_icon = "🟢" if result.get('ping_success') else "🔴"
                print(f"  {status_icon} {result['panel_name']} ({result['ip']})")
                print(f"     Estado: {result['previous_status']} → {result['new_status']}")
                if result.get('response_time'):
                    print(f"     Tiempo: {result['response_time']:.0f}ms")
                if result.get('error'):
                    print(f"     Error: {result['error']}")
                print()
            
            return data
        else:
            print(f"❌ Error en /panels/verify: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalles: {error_data}")
            except:
                print(f"   Respuesta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return None

def test_panel_individual(panel_id):
    """Probar un panel individual"""
    print(f"\n🔍 PROBANDO PANEL INDIVIDUAL {panel_id}")
    print("=" * 50)
    
    try:
        response = requests.post(f"{API_BASE_URL}/panel/{panel_id}/test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test completado: {data}")
        else:
            print(f"❌ Error en test: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalles: {error_data}")
            except:
                print(f"   Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error en test individual: {e}")

def main():
    print("🚀 INICIANDO PRUEBAS DE PANELES")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API: {API_BASE_URL}")
    print()
    
    # 1. Probar endpoint de paneles
    panels = test_panels_endpoint()
    if not panels:
        print("❌ No se pudieron obtener los paneles. Abortando.")
        return
    
    # 2. Probar verificación de todos los paneles
    verify_result = test_verify_panels()
    if not verify_result:
        print("❌ Error en la verificación de paneles.")
        return
    
    # 3. Probar paneles individuales si hay problemas
    if verify_result['updated_count'] == 0:
        print("\n⚠️  No se actualizaron paneles. Probando individualmente...")
        for panel in panels[:3]:  # Probar solo los primeros 3
            test_panel_individual(panel['id'])
    
    print("\n✅ PRUEBAS COMPLETADAS")
    print("=" * 60)

if __name__ == "__main__":
    main() 