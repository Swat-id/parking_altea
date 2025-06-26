#!/usr/bin/env python3
"""
Script para probar el endpoint de verificación de paneles
"""

import requests
import json

def test_panels_verify():
    """Probar el endpoint de verificación de paneles"""
    try:
        print("🔍 Probando endpoint /panels/verify")
        print("=" * 50)
        
        # URL del endpoint
        url = "http://localhost:6001/panels/verify"
        headers = {'Content-Type': 'application/json'}
        
        print(f"📡 Enviando petición POST a: {url}")
        
        # Hacer la petición
        response = requests.post(url, headers=headers, timeout=30)
        
        print(f"📊 Código de respuesta: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Respuesta exitosa:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error en la respuesta:")
            print(f"   Status: {response.status_code}")
            print(f"   Text: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_panels_verify() 