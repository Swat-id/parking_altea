#!/usr/bin/env python3
"""Script para probar el endpoint de actualización de ocupación"""

import requests
import json

def test_occupancy_endpoint():
    """Probar el endpoint de actualización de ocupación"""
    
    print("🧪 Probando endpoint de actualización de ocupación...")
    
    # Configuración
    url = "http://localhost:6001/parking/1/occupancy"
    headers = {'Content-Type': 'application/json'}
    
    # Probar con diferentes payloads
    test_cases = [
        {"occupancy": 330},
        {"occupancy": 331},
        {"occupancy": 332}
    ]
    
    for i, payload in enumerate(test_cases):
        print(f"\n📤 Prueba {i+1}: {payload}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ Éxito")
                result = response.json()
                print(f"   Nueva ocupación: {result.get('occupancy')}")
                print(f"   Nuevo estado: {result.get('status')}")
            else:
                print("   ❌ Error")
                
        except Exception as e:
            print(f"   ❌ Excepción: {e}")

if __name__ == "__main__":
    test_occupancy_endpoint() 