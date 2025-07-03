#!/usr/bin/env python3
"""
Script para probar endpoints simples de la API
"""

import requests
import json

def test_simple_endpoints():
    """Probar endpoints simples"""
    base_url = "http://localhost:6001"
    
    # Probar endpoint de listar parkings
    print("🔍 Probando endpoint /parkings...")
    try:
        response = requests.get(f"{base_url}/parkings")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Probar endpoint de obtener parking específico
    print("\n🔍 Probando endpoint /parking/1...")
    try:
        response = requests.get(f"{base_url}/parking/1")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Probar endpoint de ocupación con diferentes formatos
    print("\n🔍 Probando endpoint /parking/1/occupancy con diferentes formatos...")
    
    # Formato 1: JSON simple
    print("\n--- Formato 1: JSON simple ---")
    try:
        data = {"occupancy": 50}
        response = requests.post(f"{base_url}/parking/1/occupancy", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Formato 2: JSON como string
    print("\n--- Formato 2: JSON como string ---")
    try:
        data = '{"occupancy": 50}'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{base_url}/parking/1/occupancy", data=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Formato 3: Datos de formulario
    print("\n--- Formato 3: Datos de formulario ---")
    try:
        data = {"occupancy": 50}
        response = requests.post(f"{base_url}/parking/1/occupancy", data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_endpoints() 