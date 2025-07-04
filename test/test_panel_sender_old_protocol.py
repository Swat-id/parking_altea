#!/usr/bin/env python3
"""
Test script for PanelSender_oldProtocol service
"""

import requests
import json
import time

def test_panel_sender_service():
    """Test the PanelSender_oldProtocol service endpoints"""
    
    base_url = "http://localhost:7777"
    
    print("🧪 Testing PanelSender_oldProtocol service...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test initNetwork endpoint
    print("\n2. Testing initNetwork endpoint...")
    try:
        data = {
            "ip": "172.20.4.52",
            "port": 5200,
            "idcode": "255.255.255.255"
        }
        response = requests.post(f"{base_url}/initNetwork", json=data)
        if response.status_code == 200:
            print("✅ InitNetwork endpoint OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ InitNetwork endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ InitNetwork endpoint error: {e}")
        return False
    
    # Test sendText endpoint
    print("\n3. Testing sendText endpoint...")
    try:
        data = {
            "ip": "172.20.4.52",
            "window_no": 0,
            "content": "PROVES CORREGIT",
            "color": 1,  # Rojo
            "font_size": 2,  # 16px
            "speed": 1,
            "effect": 0,
            "stay_time": 5,
            "alignment_hori": 1,
            "alignment_vert": 1
        }
        response = requests.post(f"{base_url}/sendText", json=data)
        if response.status_code == 200:
            print("✅ SendText endpoint OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ SendText endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ SendText endpoint error: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    test_panel_sender_service() 