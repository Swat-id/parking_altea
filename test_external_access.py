#!/usr/bin/env python3
"""
Script para probar el acceso externo al endpoint /parkings/status
"""

import requests
import json
from datetime import datetime

def test_external_access():
    """Probar acceso externo al endpoint"""
    
    server_ip = "157.180.91.63"
    port = 6001
    endpoint = f"http://{server_ip}:{port}/parkings/status"
    
    print("🔍 PROBANDO ACCESO EXTERNO AL ENDPOINT")
    print("=" * 50)
    print(f"Servidor: {server_ip}")
    print(f"Puerto: {port}")
    print(f"Endpoint: {endpoint}")
    print()
    
    try:
        # Probar acceso
        print("📡 Enviando petición...")
        response = requests.get(endpoint, timeout=10)
        
        if response.status_code == 200:
            print("✅ ACCESO EXTERNO FUNCIONANDO")
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"Content-Length: {len(response.content)} bytes")
            
            # Parsear respuesta
            data = response.json()
            
            print(f"\n📊 INFORMACIÓN OBTENIDA:")
            print(f"Total parkings: {data.get('total_parkings', 0)}")
            print(f"Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"Success: {data.get('success', False)}")
            
            # Mostrar resumen de parkings
            parkings = data.get('parkings', [])
            print(f"\n🏢 RESUMEN DE PARKINGS:")
            for parking in parkings:
                print(f"  - {parking.get('name', 'N/A')}: {parking.get('estado', 'N/A')} ({parking.get('panel_display_text', 'N/A')})")
                print(f"    Plazas: {parking.get('plazas_ocupadas', 0)}/{parking.get('total_plazas', 0)}")
                print(f"    Paneles: {len(parking.get('panels', []))}")
            
            return True
            
        else:
            print(f"❌ ERROR: Status Code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar al servidor")
        print("Posibles causas:")
        print("  - Servidor no está ejecutándose")
        print("  - Puerto bloqueado por firewall")
        print("  - Problema de red")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout en la conexión")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_external_access()
    if success:
        print("\n🎉 PRUEBA EXITOSA: El endpoint es accesible desde el exterior")
    else:
        print("\n💥 PRUEBA FALLIDA: El endpoint no es accesible desde el exterior") 