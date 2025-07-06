#!/usr/bin/env python3
"""
Test script para verificar los decoradores de permisos implementados en T2.2
"""

import sys
import os
import requests
import json
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_decorators():
    """Prueba los decoradores de permisos"""
    print("=" * 60)
    print("TESTING DECORADORES DE PERMISOS - T2.2")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    results = []
    
    # 1. Crear usuarios de prueba
    print("\n1. Creando usuarios de prueba...")
    
    # Usuario superadmin
    superadmin_data = {
        "name": "Test Superadmin",
        "email": "superadmin@test.com",
        "password": "test123",
        "role": "superadmin"
    }
    
    # Usuario normal
    user_data = {
        "name": "Test User",
        "email": "user@test.com", 
        "password": "test123",
        "role": "user"
    }
    
    # Registrar usuarios
    try:
        response = requests.post(f"{base_url}/register", json=superadmin_data)
        if response.status_code == 200:
            print("✓ Usuario superadmin creado")
        else:
            print(f"✗ Error creando superadmin: {response.text}")
            
        response = requests.post(f"{base_url}/register", json=user_data)
        if response.status_code == 200:
            print("✓ Usuario normal creado")
        else:
            print(f"✗ Error creando usuario: {response.text}")
    except Exception as e:
        print(f"✗ Error en registro: {e}")
    
    # 2. Login de usuarios
    print("\n2. Haciendo login de usuarios...")
    
    superadmin_token = None
    user_token = None
    
    try:
        # Login superadmin
        response = requests.post(f"{base_url}/login", json={
            "email": "superadmin@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            superadmin_token = response.json().get('token')
            print("✓ Login superadmin exitoso")
        else:
            print(f"✗ Error login superadmin: {response.text}")
        
        # Login usuario normal
        response = requests.post(f"{base_url}/login", json={
            "email": "user@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            user_token = response.json().get('token')
            print("✓ Login usuario normal exitoso")
        else:
            print(f"✗ Error login usuario: {response.text}")
            
    except Exception as e:
        print(f"✗ Error en login: {e}")
    
    # 3. Probar decorador require_superadmin
    print("\n3. Probando decorador require_superadmin...")
    
    # Crear endpoint de prueba temporal
    test_endpoint = "/test/superadmin"
    
    # Probar con superadmin (debería funcionar)
    if superadmin_token:
        try:
            headers = {"Authorization": f"Bearer {superadmin_token}"}
            response = requests.get(f"{base_url}{test_endpoint}", headers=headers)
            if response.status_code == 200:
                print("✓ Superadmin puede acceder a endpoint superadmin")
                results.append(("require_superadmin - superadmin", "PASS"))
            else:
                print(f"✗ Superadmin no puede acceder: {response.text}")
                results.append(("require_superadmin - superadmin", "FAIL"))
        except Exception as e:
            print(f"✗ Error probando superadmin: {e}")
            results.append(("require_superadmin - superadmin", "ERROR"))
    
    # Probar con usuario normal (debería fallar)
    if user_token:
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            response = requests.get(f"{base_url}{test_endpoint}", headers=headers)
            if response.status_code == 403:
                print("✓ Usuario normal correctamente bloqueado")
                results.append(("require_superadmin - user", "PASS"))
            else:
                print(f"✗ Usuario normal no fue bloqueado: {response.status_code}")
                results.append(("require_superadmin - user", "FAIL"))
        except Exception as e:
            print(f"✗ Error probando usuario: {e}")
            results.append(("require_superadmin - user", "ERROR"))
    
    # 4. Probar decorador require_parking_access
    print("\n4. Probando decorador require_parking_access...")
    
    # Obtener lista de parkings
    try:
        response = requests.get(f"{base_url}/parkings")
        if response.status_code == 200:
            parkings = response.json()
            if parkings:
                test_parking_id = parkings[0]['id']
                print(f"✓ Usando parking ID: {test_parking_id}")
                
                # Probar con superadmin (debería funcionar)
                if superadmin_token:
                    headers = {"Authorization": f"Bearer {superadmin_token}"}
                    response = requests.get(f"{base_url}/parkings/{test_parking_id}", headers=headers)
                    if response.status_code == 200:
                        print("✓ Superadmin puede acceder a parking")
                        results.append(("require_parking_access - superadmin", "PASS"))
                    else:
                        print(f"✗ Superadmin no puede acceder: {response.text}")
                        results.append(("require_parking_access - superadmin", "FAIL"))
                
                # Probar con usuario normal (debería fallar si no tiene asignación)
                if user_token:
                    headers = {"Authorization": f"Bearer {user_token}"}
                    response = requests.get(f"{base_url}/parkings/{test_parking_id}", headers=headers)
                    if response.status_code == 403:
                        print("✓ Usuario normal correctamente bloqueado de parking")
                        results.append(("require_parking_access - user", "PASS"))
                    else:
                        print(f"✗ Usuario normal no fue bloqueado: {response.status_code}")
                        results.append(("require_parking_access - user", "FAIL"))
            else:
                print("✗ No hay parkings disponibles para probar")
        else:
            print(f"✗ Error obteniendo parkings: {response.text}")
    except Exception as e:
        print(f"✗ Error probando parking access: {e}")
    
    # 5. Probar decorador require_panel_access
    print("\n5. Probando decorador require_panel_access...")
    
    # Obtener lista de paneles
    try:
        response = requests.get(f"{base_url}/panels")
        if response.status_code == 200:
            panels = response.json()
            if panels:
                test_panel_id = panels[0]['id']
                print(f"✓ Usando panel ID: {test_panel_id}")
                
                # Probar con superadmin (debería funcionar)
                if superadmin_token:
                    headers = {"Authorization": f"Bearer {superadmin_token}"}
                    response = requests.get(f"{base_url}/panels/{test_panel_id}", headers=headers)
                    if response.status_code == 200:
                        print("✓ Superadmin puede acceder a panel")
                        results.append(("require_panel_access - superadmin", "PASS"))
                    else:
                        print(f"✗ Superadmin no puede acceder: {response.text}")
                        results.append(("require_panel_access - superadmin", "FAIL"))
                
                # Probar con usuario normal (debería fallar si no tiene asignación)
                if user_token:
                    headers = {"Authorization": f"Bearer {user_token}"}
                    response = requests.get(f"{base_url}/panels/{test_panel_id}", headers=headers)
                    if response.status_code == 403:
                        print("✓ Usuario normal correctamente bloqueado de panel")
                        results.append(("require_panel_access - user", "PASS"))
                    else:
                        print(f"✗ Usuario normal no fue bloqueado: {response.status_code}")
                        results.append(("require_panel_access - user", "FAIL"))
            else:
                print("✗ No hay paneles disponibles para probar")
        else:
            print(f"✗ Error obteniendo paneles: {response.text}")
    except Exception as e:
        print(f"✗ Error probando panel access: {e}")
    
    # 6. Probar sin token (modo sin login)
    print("\n6. Probando modo sin login...")
    
    try:
        response = requests.get(f"{base_url}/parkings")
        if response.status_code == 200:
            print("✓ Modo sin login funciona correctamente")
            results.append(("modo_sin_login", "PASS"))
        else:
            print(f"✗ Modo sin login falló: {response.text}")
            results.append(("modo_sin_login", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando modo sin login: {e}")
        results.append(("modo_sin_login", "ERROR"))
    
    # 7. Resumen de resultados
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    errors = 0
    
    for test_name, result in results:
        status_icon = "✓" if result == "PASS" else "✗" if result == "FAIL" else "!"
        print(f"{status_icon} {test_name}: {result}")
        
        if result == "PASS":
            passed += 1
        elif result == "FAIL":
            failed += 1
        else:
            errors += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"✓ Pasados: {passed}")
    print(f"✗ Fallidos: {failed}")
    print(f"! Errores: {errors}")
    
    if failed == 0 and errors == 0:
        print("\n🎉 TODOS LOS TESTS PASARON - T2.2 COMPLETADA")
        return True
    else:
        print(f"\n⚠️  {failed + errors} TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = test_decorators()
    sys.exit(0 if success else 1) 