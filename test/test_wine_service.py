#!/usr/bin/env python3
import requests
import json

def test_wine_service():
    base_url = "http://localhost:5002"
    
    # Probar health
    print("🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Error en health: {e}")
        return
    
    # Probar inicialización
    print("\n🔍 Probando inicialización de panel...")
    try:
        data = {"panelIP": 2886732460}  # 172.20.17.50
        response = requests.post(f"{base_url}/init", json=data)
        print(f"✅ Init: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Error en init: {e}")
        return
    
    # Probar envío de texto
    print("\n🔍 Probando envío de texto...")
    try:
        data = {
            "panelIP": 2886732460,
            "text": "TEST WINE"
        }
        response = requests.post(f"{base_url}/sendtext", json=data)
        print(f"✅ SendText: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Error en sendtext: {e}")

if __name__ == "__main__":
    test_wine_service() 