#!/usr/bin/env python3
"""
Script de prueba para el endpoint de ocupación
"""

import requests
import json

def test_occupancy_endpoint():
    """Probar el endpoint de ocupación"""
    url = "http://localhost:6001/parking/1/occupancy"
    
    # Datos de prueba
    data = {"occupancy": 50}
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"Probando endpoint: {url}")
    print(f"Datos enviados: {json.dumps(data)}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Éxito!")
        else:
            print("❌ Error!")
            
    except Exception as e:
        print(f"❌ Excepción: {e}")

if __name__ == "__main__":
    test_occupancy_endpoint() 