#!/usr/bin/env python3
"""
Test script para verificar los endpoints de administración de usuarios implementados en T2.3
"""

import sys
import os
import requests
import json
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_admin_endpoints():
    """Prueba los endpoints de administración de usuarios"""
    print("=" * 60)
    print("TESTING ENDPOINTS DE ADMINISTRACIÓN - T2.3")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    results = []
    
    # 1. Crear usuarios de prueba
    print("\n1. Creando usuarios de prueba...")
    
    # Usuario superadmin
    superadmin_data = {
        "name": "Admin Test",
        "email": "admin@test.com",
        "password": "test123",
        "role": "superadmin"
    }
    
    # Usuario normal
    user_data = {
        "name": "User Test",
        "email": "user@test.com", 
        "password": "test123",
        "role": "user"
    }
    
    # Usuario para eliminar
    delete_user_data = {
        "name": "Delete Test",
        "email": "delete@test.com",
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
            
        response = requests.post(f"{base_url}/register", json=delete_user_data)
        if response.status_code == 200:
            print("✓ Usuario para eliminar creado")
        else:
            print(f"✗ Error creando usuario para eliminar: {response.text}")
    except Exception as e:
        print(f"✗ Error en registro: {e}")
    
    # 2. Login de superadmin
    print("\n2. Haciendo login de superadmin...")
    
    superadmin_token = None
    
    try:
        response = requests.post(f"{base_url}/login", json={
            "email": "admin@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            superadmin_token = response.json().get('token')
            print("✓ Login superadmin exitoso")
        else:
            print(f"✗ Error login superadmin: {response.text}")
            
    except Exception as e:
        print(f"✗ Error en login: {e}")
    
    if not superadmin_token:
        print("✗ No se pudo obtener token de superadmin")
        return False
    
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    
    # 3. Probar GET /admin/users
    print("\n3. Probando GET /admin/users...")
    
    try:
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'users' in data:
                print(f"✓ Lista de usuarios obtenida: {len(data['users'])} usuarios")
                results.append(("GET /admin/users", "PASS"))
            else:
                print(f"✗ Respuesta incorrecta: {data}")
                results.append(("GET /admin/users", "FAIL"))
        else:
            print(f"✗ Error obteniendo usuarios: {response.text}")
            results.append(("GET /admin/users", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando GET /admin/users: {e}")
        results.append(("GET /admin/users", "ERROR"))
    
    # 4. Probar POST /admin/users
    print("\n4. Probando POST /admin/users...")
    
    new_user_data = {
        "name": "New Admin User",
        "email": "newadmin@test.com",
        "password": "test123",
        "role": "user"
    }
    
    try:
        response = requests.post(f"{base_url}/admin/users", json=new_user_data, headers=headers)
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                print("✓ Usuario creado por superadmin")
                new_user_id = data['user']['id']
                results.append(("POST /admin/users", "PASS"))
            else:
                print(f"✗ Error en respuesta: {data}")
                results.append(("POST /admin/users", "FAIL"))
        else:
            print(f"✗ Error creando usuario: {response.text}")
            results.append(("POST /admin/users", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando POST /admin/users: {e}")
        results.append(("POST /admin/users", "ERROR"))
    
    # 5. Probar GET /admin/users/{id}
    print("\n5. Probando GET /admin/users/{id}...")
    
    try:
        # Obtener lista de usuarios para obtener un ID
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('users'):
                test_user_id = data['users'][0]['id']
                
                response = requests.get(f"{base_url}/admin/users/{test_user_id}", headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get('success') and 'user' in user_data:
                        print(f"✓ Detalles de usuario obtenidos: {user_data['user']['name']}")
                        results.append(("GET /admin/users/{id}", "PASS"))
                    else:
                        print(f"✗ Respuesta incorrecta: {user_data}")
                        results.append(("GET /admin/users/{id}", "FAIL"))
                else:
                    print(f"✗ Error obteniendo detalles: {response.text}")
                    results.append(("GET /admin/users/{id}", "FAIL"))
            else:
                print("✗ No hay usuarios para probar")
                results.append(("GET /admin/users/{id}", "FAIL"))
        else:
            print(f"✗ Error obteniendo lista de usuarios: {response.text}")
            results.append(("GET /admin/users/{id}", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando GET /admin/users/{id}: {e}")
        results.append(("GET /admin/users/{id}", "ERROR"))
    
    # 6. Probar POST /admin/users/{id}/assign
    print("\n6. Probando POST /admin/users/{id}/assign...")
    
    try:
        # Obtener lista de usuarios para obtener un ID
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('users'):
                test_user_id = data['users'][0]['id']
                
                assign_data = {
                    "parking_ids": [1, 2],  # IDs de ejemplo
                    "panel_ids": [1],       # IDs de ejemplo
                    "access_ids": []        # Sin cámaras
                }
                
                response = requests.post(f"{base_url}/admin/users/{test_user_id}/assign", 
                                       json=assign_data, headers=headers)
                if response.status_code == 200:
                    assign_result = response.json()
                    if assign_result.get('success'):
                        print("✓ Recursos asignados correctamente")
                        results.append(("POST /admin/users/{id}/assign", "PASS"))
                    else:
                        print(f"✗ Error en asignación: {assign_result}")
                        results.append(("POST /admin/users/{id}/assign", "FAIL"))
                else:
                    print(f"✗ Error asignando recursos: {response.text}")
                    results.append(("POST /admin/users/{id}/assign", "FAIL"))
            else:
                print("✗ No hay usuarios para probar")
                results.append(("POST /admin/users/{id}/assign", "FAIL"))
        else:
            print(f"✗ Error obteniendo lista de usuarios: {response.text}")
            results.append(("POST /admin/users/{id}/assign", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando POST /admin/users/{id}/assign: {e}")
        results.append(("POST /admin/users/{id}/assign", "ERROR"))
    
    # 7. Probar PUT /admin/users/{id}/role
    print("\n7. Probando PUT /admin/users/{id}/role...")
    
    try:
        # Obtener lista de usuarios para obtener un ID de usuario normal
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_to_update = None
            for user in data.get('users', []):
                if user['role'] == 'user':
                    user_to_update = user
                    break
            
            if user_to_update:
                role_data = {"role": "user"}  # Mantener como user
                
                response = requests.put(f"{base_url}/admin/users/{user_to_update['id']}/role", 
                                      json=role_data, headers=headers)
                if response.status_code == 200:
                    role_result = response.json()
                    if role_result.get('success'):
                        print("✓ Rol actualizado correctamente")
                        results.append(("PUT /admin/users/{id}/role", "PASS"))
                    else:
                        print(f"✗ Error actualizando rol: {role_result}")
                        results.append(("PUT /admin/users/{id}/role", "FAIL"))
                else:
                    print(f"✗ Error actualizando rol: {response.text}")
                    results.append(("PUT /admin/users/{id}/role", "FAIL"))
            else:
                print("✗ No hay usuarios normales para probar")
                results.append(("PUT /admin/users/{id}/role", "FAIL"))
        else:
            print(f"✗ Error obteniendo lista de usuarios: {response.text}")
            results.append(("PUT /admin/users/{id}/role", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando PUT /admin/users/{id}/role: {e}")
        results.append(("PUT /admin/users/{id}/role", "ERROR"))
    
    # 8. Probar POST /admin/users/{id}/toggle
    print("\n8. Probando POST /admin/users/{id}/toggle...")
    
    try:
        # Obtener lista de usuarios para obtener un ID de usuario normal
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_to_toggle = None
            for user in data.get('users', []):
                if user['role'] == 'user' and user['is_active']:
                    user_to_toggle = user
                    break
            
            if user_to_toggle:
                response = requests.post(f"{base_url}/admin/users/{user_to_toggle['id']}/toggle", 
                                       headers=headers)
                if response.status_code == 200:
                    toggle_result = response.json()
                    if toggle_result.get('success'):
                        print("✓ Estado de usuario cambiado correctamente")
                        results.append(("POST /admin/users/{id}/toggle", "PASS"))
                    else:
                        print(f"✗ Error cambiando estado: {toggle_result}")
                        results.append(("POST /admin/users/{id}/toggle", "FAIL"))
                else:
                    print(f"✗ Error cambiando estado: {response.text}")
                    results.append(("POST /admin/users/{id}/toggle", "FAIL"))
            else:
                print("✗ No hay usuarios activos para probar")
                results.append(("POST /admin/users/{id}/toggle", "FAIL"))
        else:
            print(f"✗ Error obteniendo lista de usuarios: {response.text}")
            results.append(("POST /admin/users/{id}/toggle", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando POST /admin/users/{id}/toggle: {e}")
        results.append(("POST /admin/users/{id}/toggle", "ERROR"))
    
    # 9. Probar DELETE /admin/users/{id}
    print("\n9. Probando DELETE /admin/users/{id}...")
    
    try:
        # Obtener lista de usuarios para obtener un ID de usuario normal
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_to_delete = None
            for user in data.get('users', []):
                if user['role'] == 'user' and user['email'] == 'delete@test.com':
                    user_to_delete = user
                    break
            
            if user_to_delete:
                response = requests.delete(f"{base_url}/admin/users/{user_to_delete['id']}", 
                                         headers=headers)
                if response.status_code == 200:
                    delete_result = response.json()
                    if delete_result.get('success'):
                        print("✓ Usuario eliminado correctamente")
                        results.append(("DELETE /admin/users/{id}", "PASS"))
                    else:
                        print(f"✗ Error eliminando usuario: {delete_result}")
                        results.append(("DELETE /admin/users/{id}", "FAIL"))
                else:
                    print(f"✗ Error eliminando usuario: {response.text}")
                    results.append(("DELETE /admin/users/{id}", "FAIL"))
            else:
                print("✗ No hay usuarios para eliminar")
                results.append(("DELETE /admin/users/{id}", "FAIL"))
        else:
            print(f"✗ Error obteniendo lista de usuarios: {response.text}")
            results.append(("DELETE /admin/users/{id}", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando DELETE /admin/users/{id}: {e}")
        results.append(("DELETE /admin/users/{id}", "ERROR"))
    
    # 10. Probar acceso denegado para usuarios normales
    print("\n10. Probando acceso denegado para usuarios normales...")
    
    try:
        # Login de usuario normal
        response = requests.post(f"{base_url}/login", json={
            "email": "user@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            user_token = response.json().get('token')
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            # Intentar acceder a endpoint de admin
            response = requests.get(f"{base_url}/admin/users", headers=user_headers)
            if response.status_code == 403:
                print("✓ Acceso correctamente denegado a usuario normal")
                results.append(("acceso_denegado", "PASS"))
            else:
                print(f"✗ Usuario normal pudo acceder: {response.status_code}")
                results.append(("acceso_denegado", "FAIL"))
        else:
            print(f"✗ Error en login de usuario normal: {response.text}")
            results.append(("acceso_denegado", "FAIL"))
    except Exception as e:
        print(f"✗ Error probando acceso denegado: {e}")
        results.append(("acceso_denegado", "ERROR"))
    
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
        print("\n🎉 TODOS LOS TESTS PASARON - T2.3 COMPLETADA")
        return True
    else:
        print(f"\n⚠️  {failed + errors} TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = test_admin_endpoints()
    sys.exit(0 if success else 1) 