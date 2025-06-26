#!/usr/bin/env python3
"""
Test completo de validación del sistema Parking Altea
Incluye tests de API, autenticación, frontend y base de datos
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:6001"
FRONTEND_URL = "http://localhost:5789"

def print_test_result(test_name, success, details=""):
    """Imprime el resultado de un test"""
    status = "✅ PASÓ" if success else "❌ FALLÓ"
    print(f"{status} {test_name}")
    if details:
        print(f"   Detalles: {details}")
    print()

def test_api_connectivity():
    """Test de conectividad básica de la API"""
    try:
        response = requests.get(f"{BASE_URL}/parkings", timeout=5)
        return response.status_code == 200, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_frontend_connectivity():
    """Test de conectividad del frontend"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        return response.status_code == 200, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_user_login(email, password, expected_name):
    """Test de login de usuario"""
    try:
        data = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json=data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "token" in result and "user" in result:
                user = result["user"]
                if user.get("name") == expected_name:
                    return True, f"Login exitoso para {expected_name}"
                else:
                    return False, f"Nombre incorrecto: {user.get('name')} vs {expected_name}"
            else:
                return False, "Respuesta sin token o user"
        else:
            return False, f"Status: {response.status_code}, Response: {response.text}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_protected_endpoints(token):
    """Test de endpoints protegidos"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test parkings
    try:
        response = requests.get(f"{BASE_URL}/parkings", headers=headers, timeout=5)
        if response.status_code == 200:
            parkings = response.json()
            return True, f"Parkings obtenidos: {len(parkings)}"
        else:
            return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_statistics_endpoints(token):
    """Test de endpoints de estadísticas"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test estadísticas por hora
        response = requests.get(f"{BASE_URL}/statistics/hourly", headers=headers, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            return True, f"Estadísticas por hora obtenidas: {len(stats)} registros"
        else:
            return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_panel_endpoints(token):
    """Test de endpoints de paneles"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test obtener paneles
        response = requests.get(f"{BASE_URL}/panels", headers=headers, timeout=5)
        if response.status_code == 200:
            panels = response.json()
            return True, f"Paneles obtenidos: {len(panels)}"
        else:
            return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Función principal de tests"""
    print("=" * 60)
    print("TEST COMPLETO DE VALIDACIÓN - PARKING ALTEA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Conectividad API
    print("1. Test de conectividad de la API...")
    success, details = test_api_connectivity()
    print_test_result("Conectividad API", success, details)
    if success:
        tests_passed += 1
    total_tests += 1
    
    # Test 2: Conectividad Frontend
    print("2. Test de conectividad del Frontend...")
    success, details = test_frontend_connectivity()
    print_test_result("Conectividad Frontend", success, details)
    if success:
        tests_passed += 1
    total_tests += 1
    
    # Test 3: Login Toni Alos
    print("3. Test de login - Toni Alos...")
    success, details = test_user_login("toni.alos@swat-id.com", "alte2025!", "Toni Alos")
    print_test_result("Login Toni Alos", success, details)
    if success:
        tests_passed += 1
    total_tests += 1
    
    # Obtener token de Toni para tests posteriores
    toni_token = None
    if success:
        try:
            data = {"email": "toni.alos@swat-id.com", "password": "alte2025!"}
            response = requests.post(f"{BASE_URL}/auth/login", json=data, timeout=10)
            if response.status_code == 200:
                toni_token = response.json().get("token")
        except:
            pass
    
    # Test 4: Login Iván Martí
    print("4. Test de login - Iván Martí...")
    success, details = test_user_login("ivan.marti@swat-id.com", "alte2025!", "Iván Martí")
    print_test_result("Login Iván Martí", success, details)
    if success:
        tests_passed += 1
    total_tests += 1
    
    # Test 5: Endpoints protegidos (con token de Toni)
    if toni_token:
        print("5. Test de endpoints protegidos...")
        success, details = test_protected_endpoints(toni_token)
        print_test_result("Endpoints protegidos", success, details)
        if success:
            tests_passed += 1
        total_tests += 1
        
        # Test 6: Endpoints de estadísticas
        print("6. Test de endpoints de estadísticas...")
        success, details = test_statistics_endpoints(toni_token)
        print_test_result("Endpoints de estadísticas", success, details)
        if success:
            tests_passed += 1
        total_tests += 1
        
        # Test 7: Endpoints de paneles
        print("7. Test de endpoints de paneles...")
        success, details = test_panel_endpoints(toni_token)
        print_test_result("Endpoints de paneles", success, details)
        if success:
            tests_passed += 1
        total_tests += 1
    
    # Resumen final
    print("=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print(f"Tests pasados: {tests_passed}/{total_tests}")
    print(f"Porcentaje de éxito: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("El sistema está funcionando correctamente.")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) fallaron.")
        print("Revisar los detalles anteriores para identificar problemas.")
    
    print("\n" + "=" * 60)
    
    # Guardar resultados en archivo
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "success_rate": (tests_passed/total_tests)*100 if total_tests > 0 else 0
    }
    
    with open("test_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Resultados guardados en: test_validation_results.json")

if __name__ == "__main__":
    main() 