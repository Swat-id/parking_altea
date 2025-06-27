#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de los paneles
"""

import requests
import psycopg2
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"
DB_CONFIG = {
    'host': 'localhost',
    'database': 'parking_altea',
    'user': 'postgres',
    'password': ''
}

def check_database_panels():
    """Verificar paneles directamente en la base de datos"""
    print("🔍 VERIFICANDO PANELES EN BASE DE DATOS")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, ip, status, last_update 
            FROM panels 
            ORDER BY id
        """)
        
        panels_db = cursor.fetchall()
        
        print(f"📊 Paneles en BD: {len(panels_db)}")
        for panel in panels_db:
            panel_id, name, ip, status, last_update = panel
            print(f"  📺 {name} ({ip}) - {status}")
            if last_update:
                print(f"     Última actualización: {last_update}")
        
        cursor.close()
        conn.close()
        
        return panels_db
        
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return None

def check_api_panels():
    """Verificar paneles desde la API"""
    print("\n🔍 VERIFICANDO PANELES DESDE API")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        if response.status_code == 200:
            panels_api = response.json()
            print(f"📊 Paneles en API: {len(panels_api)}")
            
            for panel in panels_api:
                print(f"  📺 {panel['name']} ({panel['ip_address']}) - {panel['status']}")
                if panel.get('last_update'):
                    print(f"     Última actualización: {panel['last_update']}")
            
            return panels_api
        else:
            print(f"❌ Error en API: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error conectando a API: {e}")
        return None

def test_verify_endpoint():
    """Probar el endpoint de verificación"""
    print("\n🔍 PROBANDO ENDPOINT DE VERIFICACIÓN")
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
            print(f"❌ Error en verificación: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return None

def compare_results(panels_db, panels_api):
    """Comparar resultados entre BD y API"""
    print("\n🔍 COMPARANDO RESULTADOS")
    print("=" * 50)
    
    if not panels_db or not panels_api:
        print("❌ No se pueden comparar resultados")
        return
    
    # Crear diccionarios para comparación
    db_dict = {panel[0]: {'name': panel[1], 'ip': panel[2], 'status': panel[3]} for panel in panels_db}
    api_dict = {panel['id']: {'name': panel['name'], 'ip': panel['ip_address'], 'status': panel['status']} for panel in panels_api}
    
    print("📊 COMPARACIÓN:")
    for panel_id in db_dict.keys():
        if panel_id in api_dict:
            db_panel = db_dict[panel_id]
            api_panel = api_dict[panel_id]
            
            status_match = db_panel['status'] == api_panel['status']
            status_icon = "✅" if status_match else "❌"
            
            print(f"  {status_icon} {db_panel['name']}")
            print(f"     BD: {db_panel['status']} | API: {api_panel['status']}")
            
            if not status_match:
                print(f"     ⚠️  DIFERENCIA DETECTADA")
        else:
            print(f"  ❌ Panel {panel_id} no encontrado en API")

def main():
    print("🚀 DIAGNÓSTICO DE PANELES")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar paneles en BD
    panels_db = check_database_panels()
    
    # 2. Verificar paneles en API
    panels_api = check_api_panels()
    
    # 3. Comparar resultados
    compare_results(panels_db, panels_api)
    
    # 4. Probar verificación
    verify_result = test_verify_endpoint()
    
    # 5. Verificar de nuevo después de la verificación
    if verify_result:
        print("\n🔄 VERIFICANDO DESPUÉS DE LA VERIFICACIÓN")
        print("=" * 50)
        
        # Esperar un momento
        import time
        time.sleep(2)
        
        # Verificar de nuevo
        panels_db_after = check_database_panels()
        panels_api_after = check_api_panels()
        compare_results(panels_db_after, panels_api_after)
    
    print("\n✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main() 