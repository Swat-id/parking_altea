#!/usr/bin/env python3
"""
Script de Pruebas - Sistema de Autenticación Parking Altea
Prueba todos los endpoints de autenticación y gestión de usuarios
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class ParkingAlteaAuthTester:
    def __init__(self, base_url: str = "http://157.180.91.63:6001"):
        self.base_url = base_url
        self.results = []
        self.start_time = datetime.now()
        self.auth_token = None
        
    def log_test(self, endpoint: str, method: str, status: str, details: str = "", response_data: Any = None):
        """Registra el resultado de una prueba"""
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details,
            "response_data": response_data
        }
        self.results.append(test_result)
        print(f"[{status}] {method} {endpoint} - {details}")
        
    def test_register_user(self) -> bool:
        """Prueba registro de usuario"""
        try:
            payload = {
                "name": "Test User",
                "email": "test@example.com",
                "password": "test123!"
            }
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 201:
                data = response.json()
                self.log_test("/auth/register", "POST", "✅ EXITOSO", 
                            f"Usuario creado: {data['user']['email']}", data)
                return True
            else:
                self.log_test("/auth/register", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/auth/register", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_login_toni(self) -> bool:
        """Prueba login con Toni Alos"""
        try:
            payload = {
                "email": "atea.dti@altea.es",
                "password": "altea2025!"
            }
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['token']
                self.log_test("/auth/login", "POST", "✅ EXITOSO", 
                            f"Login exitoso: {data['user']['name']}", {"user": data['user']})
                return True
            else:
                self.log_test("/auth/login", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/auth/login", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_login_ivan(self) -> bool:
        """Prueba login con Iván Martí"""
        try:
            payload = {
                "email": "gerenciapstd@altea.es",
                "password": "altea2025!"
            }
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['token']
                self.log_test("/auth/login", "POST", "✅ EXITOSO", 
                            f"Login exitoso: {data['user']['name']}", {"user": data['user']})
                return True
            else:
                self.log_test("/auth/login", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/auth/login", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_get_permissions(self) -> bool:
        """Prueba obtener permisos del usuario"""
        if not self.auth_token:
            self.log_test("/auth/permissions", "GET", "❌ ERROR", "No hay token de autenticación")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/auth/permissions",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                permissions = data['permissions']
                self.log_test("/auth/permissions", "GET", "✅ EXITOSO", 
                            f"Permisos obtenidos: {len(permissions['parking_ids'])} parkings, {len(permissions['panel_ids'])} paneles, {len(permissions['access_ids'])} cámaras", data)
                return True
            else:
                self.log_test("/auth/permissions", "GET", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/auth/permissions", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_get_user_parkings(self) -> bool:
        """Prueba obtener parkings del usuario autenticado"""
        if not self.auth_token:
            self.log_test("/user/parkings", "GET", "❌ ERROR", "No hay token de autenticación")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/user/parkings",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("/user/parkings", "GET", "✅ EXITOSO", 
                            f"Parkings obtenidos: {len(data)}", data[:2])  # Solo primeros 2 para el log
                return True
            else:
                self.log_test("/user/parkings", "GET", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/user/parkings", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_get_user_parking_specific(self, parking_id: int = 1) -> bool:
        """Prueba obtener un parking específico del usuario"""
        if not self.auth_token:
            self.log_test(f"/user/parking/{parking_id}", "GET", "❌ ERROR", "No hay token de autenticación")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/user/parking/{parking_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"/user/parking/{parking_id}", "GET", "✅ EXITOSO", 
                            f"Parking obtenido: {data['name']}", data)
                return True
            else:
                self.log_test(f"/user/parking/{parking_id}", "GET", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"/user/parking/{parking_id}", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_change_password(self) -> bool:
        """Prueba cambiar contraseña"""
        if not self.auth_token:
            self.log_test("/auth/password", "PUT", "❌ ERROR", "No hay token de autenticación")
            return False
            
        try:
            payload = {
                "current_password": "altea2025!",
                "new_password": "altea2025!"
            }
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            response = requests.put(
                f"{self.base_url}/auth/password",
                json=payload,
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("/auth/password", "PUT", "✅ EXITOSO", 
                            "Contraseña cambiada correctamente", data)
                return True
            else:
                self.log_test("/auth/password", "PUT", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/auth/password", "PUT", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Prueba acceso no autorizado a endpoint protegido"""
        try:
            response = requests.get(
                f"{self.base_url}/user/parkings",
                timeout=10
            )
            if response.status_code == 401:
                self.log_test("/user/parkings (sin auth)", "GET", "✅ EXITOSO", 
                            "Acceso denegado correctamente (sin token)")
                return True
            else:
                self.log_test("/user/parkings (sin auth)", "GET", "❌ ERROR", 
                            f"Status code inesperado: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/user/parkings (sin auth)", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todas las pruebas de autenticación"""
        print("🚀 Iniciando pruebas de autenticación - Parking Altea v2.2")
        print("=" * 60)
        
        tests = [
            ("POST /auth/register", self.test_register_user),
            ("POST /auth/login (Toni)", self.test_login_toni),
            ("GET /auth/permissions", self.test_get_permissions),
            ("GET /user/parkings", self.test_get_user_parkings),
            ("GET /user/parking/1", self.test_get_user_parking_specific),
            ("PUT /auth/password", self.test_change_password),
            ("POST /auth/login (Iván)", self.test_login_ivan),
            ("GET /user/parkings (Iván)", self.test_get_user_parkings),
            ("GET /user/parking/5 (Iván)", self.test_get_user_parking_specific),
            ("GET /user/parkings (sin auth)", self.test_unauthorized_access),
        ]
        
        successful_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Ejecutando: {test_name}")
            if test_func():
                successful_tests += 1
            time.sleep(1)  # Pausa entre pruebas
        
        # Generar reporte
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "test_date": self.start_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "results": self.results
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Guarda el reporte en un archivo JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"auth_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte guardado en: {filename}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprime un resumen de las pruebas"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS DE AUTENTICACIÓN")
        print("=" * 60)
        print(f"Fecha: {report['test_date']}")
        print(f"Duración: {report['duration_seconds']:.2f} segundos")
        print(f"Total de pruebas: {report['total_tests']}")
        print(f"Pruebas exitosas: {report['successful_tests']}")
        print(f"Pruebas fallidas: {report['failed_tests']}")
        print(f"Tasa de éxito: {report['success_rate']:.1f}%")
        
        if report['success_rate'] >= 90:
            print("🎉 Estado: EXCELENTE - Sistema de autenticación funcionando perfectamente")
        elif report['success_rate'] >= 70:
            print("✅ Estado: BUENO - Sistema de autenticación funcionando correctamente")
        elif report['success_rate'] >= 50:
            print("⚠️  Estado: REGULAR - Algunos problemas en autenticación")
        else:
            print("❌ Estado: CRÍTICO - Problemas graves en autenticación")

def main():
    """Función principal"""
    tester = ParkingAlteaAuthTester()
    report = tester.run_all_tests()
    tester.print_summary(report)
    tester.save_report(report)
    
    # Guardar también en docs para documentación
    docs_filename = "docs/latest_auth_test_report.json"
    tester.save_report(report, docs_filename)

if __name__ == "__main__":
    main() 