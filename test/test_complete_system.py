#!/usr/bin/env python3
"""
Script completo de pruebas para el sistema Parking Altea
Prueba API, frontend, base de datos y servicios
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"
FRONTEND_URL = "http://157.180.91.63:5789"
TEST_CREDENTIALS = {
    "toni": {"email": "atea.dti@altea.es", "password": "altea2025!"},
    "ivan": {"email": "gerenciapstd@altea.es", "password": "altea2025!"}
}

class TestResults:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name, success, details=""):
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} {test_name}")
        if details and not success:
            print(f"   Detalles: {details}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("RESUMEN DE PRUEBAS")
        print("="*60)
        
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        print(f"Total pruebas: {total}")
        print(f"Pruebas exitosas: {passed}")
        print(f"Pruebas fallidas: {total - passed}")
        print(f"Tasa de éxito: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nPruebas fallidas:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\nTiempo total: {datetime.now() - self.start_time}")
        return passed == total

def test_api_connectivity():
    """Probar conectividad básica de la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/parkings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, f"API responde correctamente. {len(data)} parkings encontrados"
        else:
            return False, f"API responde con código {response.status_code}"
    except Exception as e:
        return False, f"Error de conectividad: {str(e)}"

def test_frontend_connectivity():
    """Probar conectividad del frontend"""
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            return True, "Frontend responde correctamente"
        else:
            return False, f"Frontend responde con código {response.status_code}"
    except Exception as e:
        return False, f"Error de conectividad: {str(e)}"

def test_authentication(credentials, user_name):
    """Probar autenticación de usuario"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json=credentials,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return True, f"Login exitoso para {user_name}"
            else:
                return False, f"Login fallido: {data.get('error', 'Error desconocido')}"
        else:
            return False, f"Error HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Error de autenticación: {str(e)}"

def test_protected_endpoints(token, user_name):
    """Probar endpoints protegidos"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Probar obtener parkings del usuario
    try:
        response = requests.get(
            f"{API_BASE_URL}/user/parkings",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, f"Endpoints protegidos funcionan para {user_name}. {len(data)} parkings asignados"
        else:
            return False, f"Error en endpoints protegidos: {response.status_code}"
    except Exception as e:
        return False, f"Error en endpoints protegidos: {str(e)}"

def test_parking_data():
    """Probar datos de parkings"""
    try:
        response = requests.get(f"{API_BASE_URL}/parkings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura de datos
            if len(data) > 0:
                parking = data[0]
                required_fields = ["id", "name", "total_plazas", "plazas_ocupadas", "estado"]
                missing_fields = [field for field in required_fields if field not in parking]
                
                if not missing_fields:
                    return True, f"Datos de parkings válidos. {len(data)} parkings disponibles"
                else:
                    return False, f"Campos faltantes: {missing_fields}"
            else:
                return False, "No hay datos de parkings"
        else:
            return False, f"Error obteniendo parkings: {response.status_code}"
    except Exception as e:
        return False, f"Error en datos de parkings: {str(e)}"

def test_statistics_endpoints():
    """Probar endpoints de estadísticas"""
    try:
        # Probar estadísticas generales
        response = requests.get(f"{API_BASE_URL}/statistics", timeout=10)
        if response.status_code == 200:
            return True, "Endpoints de estadísticas funcionan"
        else:
            return False, f"Error en estadísticas: {response.status_code}"
    except Exception as e:
        return False, f"Error en estadísticas: {str(e)}"

def main():
    print("🧪 INICIANDO PRUEBAS COMPLETAS DEL SISTEMA PARKING ALTEA")
    print("="*60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API: {API_BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print("="*60)
    
    results = TestResults()
    
    # Pruebas de conectividad
    print("\n🔌 PRUEBAS DE CONECTIVIDAD")
    print("-" * 30)
    
    success, details = test_api_connectivity()
    results.add_result("Conectividad API", success, details)
    
    success, details = test_frontend_connectivity()
    results.add_result("Conectividad Frontend", success, details)
    
    # Pruebas de datos
    print("\n📊 PRUEBAS DE DATOS")
    print("-" * 30)
    
    success, details = test_parking_data()
    results.add_result("Datos de Parkings", success, details)
    
    success, details = test_statistics_endpoints()
    results.add_result("Endpoints de Estadísticas", success, details)
    
    # Pruebas de autenticación
    print("\n🔐 PRUEBAS DE AUTENTICACIÓN")
    print("-" * 30)
    
    for user_name, credentials in TEST_CREDENTIALS.items():
        success, details = test_authentication(credentials, user_name)
        results.add_result(f"Login {user_name.title()}", success, details)
        
        # Si el login fue exitoso, probar endpoints protegidos
        if success:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    json=credentials,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                data = response.json()
                if data.get("success") and data.get("token"):
                    token = data["token"]
                    success_protected, details_protected = test_protected_endpoints(token, user_name)
                    results.add_result(f"Endpoints Protegidos {user_name.title()}", success_protected, details_protected)
            except Exception as e:
                results.add_result(f"Endpoints Protegidos {user_name.title()}", False, f"Error obteniendo token: {str(e)}")
    
    # Resumen final
    all_passed = results.print_summary()
    
    # Guardar resultados en archivo
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "api_url": API_BASE_URL,
            "frontend_url": FRONTEND_URL,
            "results": results.results,
            "summary": {
                "total": len(results.results),
                "passed": sum(1 for r in results.results if r["success"]),
                "failed": sum(1 for r in results.results if not r["success"])
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados guardados en: test_results.json")
    
    if all_passed:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        return 0
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON. Revisar detalles arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 