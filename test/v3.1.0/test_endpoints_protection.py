#!/usr/bin/env python3
"""
Test script para verificar la protección de endpoints implementada en T2.4
"""

import sys
import os
import requests
import json
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_endpoints_protection():
    """Prueba la protección de endpoints"""
    print("=" * 60)
    print("TESTING PROTECCIÓN DE ENDPOINTS - T2.4")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    results = []
    
    # 1. Crear usuarios de prueba
    print("\n1. Creando usuarios de prueba...")
    
    # Usuario superadmin
    superadmin_data = {
        "name": "Admin Test T2.4",
        "email": "admin_t24@test.com",
        "password": "test123",
        "role": "superadmin"
    }
    
    # Usuario normal
    user_data = {
        "name": "User Test T2.4",
        "email": "user_t24@test.com", 
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
            "email": "admin_t24@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            superadmin_token = response.json().get('token')
            print("✓ Login superadmin exitoso")
        else:
            print(f"✗ Error login superadmin: {response.text}")
        
        # Login usuario normal
        response = requests.post(f"{base_url}/login", json={
            "email": "user_t24@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            user_token = response.json().get('token')
            print("✓ Login usuario normal exitoso")
        else:
            print(f"✗ Error login usuario: {response.text}")
            
    except Exception as e:
        print(f"✗ Error en login: {e}")
    
    # 3. Probar endpoints públicos (deben funcionar sin token)
    print("\n3. Probando endpoints públicos...")
    
    public_endpoints = [
        ("GET", "/parkings"),
        ("GET", "/parkings/status"),
        ("GET", "/panels"),
        ("GET", "/panel-types"),
        ("GET", "/statistics"),
        ("GET", "/schedules")
    ]
    
    for method, endpoint in public_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}")
            else:
                response = requests.post(f"{base_url}{endpoint}")
            
            if response.status_code in [200, 201]:
                print(f"✓ {method} {endpoint} - Acceso público correcto")
                results.append((f"público_{method}_{endpoint}", "PASS"))
            else:
                print(f"✗ {method} {endpoint} - Error: {response.status_code}")
                results.append((f"público_{method}_{endpoint}", "FAIL"))
        except Exception as e:
            print(f"✗ {method} {endpoint} - Error: {e}")
            results.append((f"público_{method}_{endpoint}", "ERROR"))
    
    # 4. Probar endpoints protegidos con superadmin
    print("\n4. Probando endpoints protegidos con superadmin...")
    
    if superadmin_token:
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        
        # Obtener lista de parkings para usar IDs reales
        try:
            response = requests.get(f"{base_url}/parkings", headers=headers)
            if response.status_code == 200:
                parkings = response.json()
                if parkings:
                    test_parking_id = parkings[0]['id']
                    print(f"✓ Usando parking ID: {test_parking_id}")
                    
                    # Probar endpoint de ocupación
                    occupancy_data = {"occupancy": 50}
                    response = requests.post(f"{base_url}/parking/{test_parking_id}/occupancy", 
                                           json=occupancy_data, headers=headers)
                    if response.status_code == 200:
                        print("✓ POST /parking/{id}/occupancy - Superadmin puede modificar")
                        results.append(("superadmin_occupancy", "PASS"))
                    else:
                        print(f"✗ POST /parking/{id}/occupancy - Error: {response.status_code}")
                        results.append(("superadmin_occupancy", "FAIL"))
                    
                    # Probar endpoint de estadísticas
                    response = requests.get(f"{base_url}/parking/{test_parking_id}/statistics", headers=headers)
                    if response.status_code == 200:
                        print("✓ GET /parking/{id}/statistics - Superadmin puede acceder")
                        results.append(("superadmin_statistics", "PASS"))
                    else:
                        print(f"✗ GET /parking/{id}/statistics - Error: {response.status_code}")
                        results.append(("superadmin_statistics", "FAIL"))
                    
                    # Probar endpoint de historial
                    response = requests.get(f"{base_url}/parking/{test_parking_id}/history", headers=headers)
                    if response.status_code == 200:
                        print("✓ GET /parking/{id}/history - Superadmin puede acceder")
                        results.append(("superadmin_history", "PASS"))
                    else:
                        print(f"✗ GET /parking/{id}/history - Error: {response.status_code}")
                        results.append(("superadmin_history", "FAIL"))
                else:
                    print("✗ No hay parkings disponibles para probar")
                    results.append(("superadmin_parking_access", "FAIL"))
        except Exception as e:
            print(f"✗ Error obteniendo parkings: {e}")
            results.append(("superadmin_parking_access", "ERROR"))
        
        # Probar endpoints de administración
        try:
            response = requests.get(f"{base_url}/admin/users", headers=headers)
            if response.status_code == 200:
                print("✓ GET /admin/users - Superadmin puede acceder")
                results.append(("superadmin_users", "PASS"))
            else:
                print(f"✗ GET /admin/users - Error: {response.status_code}")
                results.append(("superadmin_users", "FAIL"))
        except Exception as e:
            print(f"✗ Error probando /admin/users: {e}")
            results.append(("superadmin_users", "ERROR"))
    
    # 5. Probar endpoints protegidos con usuario normal (deben fallar)
    print("\n5. Probando endpoints protegidos con usuario normal...")
    
    if user_token:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Obtener lista de parkings
        try:
            response = requests.get(f"{base_url}/parkings", headers=headers)
            if response.status_code == 200:
                parkings = response.json()
                if parkings:
                    test_parking_id = parkings[0]['id']
                    
                    # Probar endpoint de ocupación (debe fallar sin asignación)
                    occupancy_data = {"occupancy": 50}
                    response = requests.post(f"{base_url}/parking/{test_parking_id}/occupancy", 
                                           json=occupancy_data, headers=headers)
                    if response.status_code == 403:
                        print("✓ POST /parking/{id}/occupancy - Usuario correctamente bloqueado")
                        results.append(("user_occupancy_blocked", "PASS"))
                    else:
                        print(f"✗ POST /parking/{id}/occupancy - No fue bloqueado: {response.status_code}")
                        results.append(("user_occupancy_blocked", "FAIL"))
                    
                    # Probar endpoint de estadísticas (debe fallar sin asignación)
                    response = requests.get(f"{base_url}/parking/{test_parking_id}/statistics", headers=headers)
                    if response.status_code == 403:
                        print("✓ GET /parking/{id}/statistics - Usuario correctamente bloqueado")
                        results.append(("user_statistics_blocked", "PASS"))
                    else:
                        print(f"✗ GET /parking/{id}/statistics - No fue bloqueado: {response.status_code}")
                        results.append(("user_statistics_blocked", "FAIL"))
                    
                    # Probar endpoint de administración (debe fallar)
                    response = requests.get(f"{base_url}/admin/users", headers=headers)
                    if response.status_code == 403:
                        print("✓ GET /admin/users - Usuario correctamente bloqueado")
                        results.append(("user_admin_blocked", "PASS"))
                    else:
                        print(f"✗ GET /admin/users - No fue bloqueado: {response.status_code}")
                        results.append(("user_admin_blocked", "FAIL"))
                else:
                    print("✗ No hay parkings disponibles para probar")
                    results.append(("user_parking_access", "FAIL"))
        except Exception as e:
            print(f"✗ Error probando acceso de usuario: {e}")
            results.append(("user_parking_access", "ERROR"))
    
    # 6. Probar endpoints sin token (deben fallar los protegidos)
    print("\n6. Probando endpoints protegidos sin token...")
    
    try:
        # Obtener lista de parkings
        response = requests.get(f"{base_url}/parkings")
        if response.status_code == 200:
            parkings = response.json()
            if parkings:
                test_parking_id = parkings[0]['id']
                
                # Probar endpoint de ocupación sin token
                occupancy_data = {"occupancy": 50}
                response = requests.post(f"{base_url}/parking/{test_parking_id}/occupancy", json=occupancy_data)
                if response.status_code == 401:
                    print("✓ POST /parking/{id}/occupancy - Sin token correctamente bloqueado")
                    results.append(("no_token_occupancy_blocked", "PASS"))
                else:
                    print(f"✗ POST /parking/{id}/occupancy - No fue bloqueado sin token: {response.status_code}")
                    results.append(("no_token_occupancy_blocked", "FAIL"))
                
                # Probar endpoint de administración sin token
                response = requests.get(f"{base_url}/admin/users")
                if response.status_code == 401:
                    print("✓ GET /admin/users - Sin token correctamente bloqueado")
                    results.append(("no_token_admin_blocked", "PASS"))
                else:
                    print(f"✗ GET /admin/users - No fue bloqueado sin token: {response.status_code}")
                    results.append(("no_token_admin_blocked", "FAIL"))
            else:
                print("✗ No hay parkings disponibles para probar")
                results.append(("no_token_access", "FAIL"))
        else:
            print(f"✗ Error obteniendo parkings: {response.status_code}")
            results.append(("no_token_access", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando sin token: {e}")
        results.append(("no_token_access", "ERROR"))
    
    # 7. Probar endpoints de autenticación
    print("\n7. Probando endpoints de autenticación...")
    
    if user_token:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        try:
            # Probar obtener permisos
            response = requests.get(f"{base_url}/auth/permissions", headers=headers)
            if response.status_code == 200:
                print("✓ GET /auth/permissions - Funciona correctamente")
                results.append(("auth_permissions", "PASS"))
            else:
                print(f"✗ GET /auth/permissions - Error: {response.status_code}")
                results.append(("auth_permissions", "FAIL"))
            
            # Probar obtener parkings del usuario
            response = requests.get(f"{base_url}/user/parkings", headers=headers)
            if response.status_code == 200:
                print("✓ GET /user/parkings - Funciona correctamente")
                results.append(("user_parkings", "PASS"))
            else:
                print(f"✗ GET /user/parkings - Error: {response.status_code}")
                results.append(("user_parkings", "FAIL"))
        except Exception as e:
            print(f"✗ Error probando endpoints de auth: {e}")
            results.append(("auth_endpoints", "ERROR"))
    
    # Resumen de resultados
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
        print("\n🎉 TODOS LOS TESTS PASARON - T2.4 Y T2.5 COMPLETADAS")
        return True
    else:
        print(f"\n⚠️  {failed + errors} TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = test_endpoints_protection()
    sys.exit(0 if success else 1) 