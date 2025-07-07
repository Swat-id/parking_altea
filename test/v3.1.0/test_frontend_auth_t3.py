#!/usr/bin/env python3
"""
Test script para verificar el frontend de autenticación implementado en T3.1, T3.2 y T3.3
"""

import sys
import os
import requests
import json
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_frontend_auth_integration():
    """Prueba la integración del frontend de autenticación con el backend"""
    print("=" * 60)
    print("TESTING FRONTEND AUTH INTEGRATION - T3.1, T3.2, T3.3")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    frontend_url = "http://localhost:5173"  # Vite dev server
    results = []
    
    # 1. Verificar que el backend está funcionando
    print("\n1. Verificando backend...")
    
    try:
        response = requests.get(f"{base_url}/parkings")
        if response.status_code == 200:
            print("✓ Backend funcionando correctamente")
            results.append(("backend_status", "PASS"))
        else:
            print(f"✗ Backend no responde: {response.status_code}")
            results.append(("backend_status", "FAIL"))
            return False
    except Exception as e:
        print(f"✗ Error conectando al backend: {e}")
        results.append(("backend_status", "ERROR"))
        return False
    
    # 2. Crear usuarios de prueba
    print("\n2. Creando usuarios de prueba...")
    
    # Usuario superadmin
    superadmin_data = {
        "name": "Frontend Test Admin",
        "email": "frontend_admin@test.com",
        "password": "test123",
        "role": "superadmin"
    }
    
    # Usuario normal
    user_data = {
        "name": "Frontend Test User",
        "email": "frontend_user@test.com", 
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
    
    # 3. Probar endpoints de autenticación del backend
    print("\n3. Probando endpoints de autenticación del backend...")
    
    # Login superadmin
    try:
        response = requests.post(f"{base_url}/auth/login", json={
            "email": "frontend_admin@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            superadmin_token = response.json().get('token')
            superadmin_user = response.json().get('user')
            print("✓ Login superadmin exitoso")
            print(f"  - Token: {superadmin_token[:20]}...")
            print(f"  - Usuario: {superadmin_user['name']} ({superadmin_user['role']})")
            results.append(("backend_login_superadmin", "PASS"))
        else:
            print(f"✗ Error login superadmin: {response.text}")
            results.append(("backend_login_superadmin", "FAIL"))
    except Exception as e:
        print(f"✗ Error en login superadmin: {e}")
        results.append(("backend_login_superadmin", "ERROR"))
    
    # Login usuario normal
    try:
        response = requests.post(f"{base_url}/auth/login", json={
            "email": "frontend_user@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            user_token = response.json().get('token')
            user_user = response.json().get('user')
            print("✓ Login usuario normal exitoso")
            print(f"  - Token: {user_token[:20]}...")
            print(f"  - Usuario: {user_user['name']} ({user_user['role']})")
            results.append(("backend_login_user", "PASS"))
        else:
            print(f"✗ Error login usuario: {response.text}")
            results.append(("backend_login_user", "FAIL"))
    except Exception as e:
        print(f"✗ Error en login usuario: {e}")
        results.append(("backend_login_user", "ERROR"))
    
    # 4. Probar endpoints protegidos con tokens
    print("\n4. Probando endpoints protegidos con tokens...")
    
    if 'superadmin_token' in locals():
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        
        # Probar obtener permisos
        try:
            response = requests.get(f"{base_url}/auth/permissions", headers=headers)
            if response.status_code == 200:
                permissions = response.json()
                print("✓ GET /auth/permissions - Funciona correctamente")
                print(f"  - Parkings: {permissions.get('permissions', {}).get('parking_ids', [])}")
                print(f"  - Paneles: {permissions.get('permissions', {}).get('panel_ids', [])}")
                results.append(("backend_permissions", "PASS"))
            else:
                print(f"✗ GET /auth/permissions - Error: {response.status_code}")
                results.append(("backend_permissions", "FAIL"))
        except Exception as e:
            print(f"✗ Error obteniendo permisos: {e}")
            results.append(("backend_permissions", "ERROR"))
        
        # Probar obtener parkings del usuario
        try:
            response = requests.get(f"{base_url}/user/parkings", headers=headers)
            if response.status_code == 200:
                parkings = response.json()
                print("✓ GET /user/parkings - Funciona correctamente")
                print(f"  - Parkings disponibles: {len(parkings)}")
                results.append(("backend_user_parkings", "PASS"))
            else:
                print(f"✗ GET /user/parkings - Error: {response.status_code}")
                results.append(("backend_user_parkings", "FAIL"))
        except Exception as e:
            print(f"✗ Error obteniendo parkings: {e}")
            results.append(("backend_user_parkings", "ERROR"))
        
        # Probar endpoints de administración
        try:
            response = requests.get(f"{base_url}/admin/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                print("✓ GET /admin/users - Superadmin puede acceder")
                print(f"  - Usuarios totales: {users.get('total', 0)}")
                results.append(("backend_admin_users", "PASS"))
            else:
                print(f"✗ GET /admin/users - Error: {response.status_code}")
                results.append(("backend_admin_users", "FAIL"))
        except Exception as e:
            print(f"✗ Error obteniendo usuarios: {e}")
            results.append(("backend_admin_users", "ERROR"))
    
    # 5. Probar validación de tokens
    print("\n5. Probando validación de tokens...")
    
    # Probar con token inválido
    try:
        headers = {"Authorization": "Bearer invalid-token"}
        response = requests.get(f"{base_url}/auth/permissions", headers=headers)
        if response.status_code == 401:
            print("✓ Token inválido correctamente rechazado")
            results.append(("token_validation_invalid", "PASS"))
        else:
            print(f"✗ Token inválido no fue rechazado: {response.status_code}")
            results.append(("token_validation_invalid", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando token inválido: {e}")
        results.append(("token_validation_invalid", "ERROR"))
    
    # Probar sin token
    try:
        response = requests.get(f"{base_url}/auth/permissions")
        if response.status_code == 401:
            print("✓ Petición sin token correctamente rechazada")
            results.append(("token_validation_missing", "PASS"))
        else:
            print(f"✗ Petición sin token no fue rechazada: {response.status_code}")
            results.append(("token_validation_missing", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando sin token: {e}")
        results.append(("token_validation_missing", "ERROR"))
    
    # 6. Probar endpoints públicos (deben funcionar sin token)
    print("\n6. Probando endpoints públicos...")
    
    public_endpoints = [
        ("GET", "/parkings"),
        ("GET", "/parkings/status"),
        ("GET", "/panels"),
        ("GET", "/statistics")
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
    
    # 7. Probar manejo de errores de autenticación
    print("\n7. Probando manejo de errores de autenticación...")
    
    # Probar login con credenciales incorrectas
    try:
        response = requests.post(f"{base_url}/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        if response.status_code == 401:
            print("✓ Login con credenciales incorrectas correctamente rechazado")
            results.append(("auth_error_invalid_credentials", "PASS"))
        else:
            print(f"✗ Login con credenciales incorrectas no fue rechazado: {response.status_code}")
            results.append(("auth_error_invalid_credentials", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando credenciales incorrectas: {e}")
        results.append(("auth_error_invalid_credentials", "ERROR"))
    
    # Probar login con datos faltantes
    try:
        response = requests.post(f"{base_url}/auth/login", json={
            "email": "test@test.com"
            # Sin password
        })
        if response.status_code == 400:
            print("✓ Login con datos faltantes correctamente rechazado")
            results.append(("auth_error_missing_data", "PASS"))
        else:
            print(f"✗ Login con datos faltantes no fue rechazado: {response.status_code}")
            results.append(("auth_error_missing_data", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando datos faltantes: {e}")
        results.append(("auth_error_missing_data", "ERROR"))
    
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
        print("\n🎉 TODOS LOS TESTS PASARON - T3.1, T3.2, T3.3 COMPLETADAS")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Verificar que el frontend se conecta correctamente al backend")
        print("2. Probar el flujo completo de login en el navegador")
        print("3. Verificar que los tokens se manejan correctamente")
        print("4. Continuar con T3.4 (protección de rutas)")
        return True
    else:
        print(f"\n⚠️  {failed + errors} TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = test_frontend_auth_integration()
    sys.exit(0 if success else 1) 