#!/usr/bin/env python3
"""
Test completo para Sprint 4 - Funcionalidades de Administración
T4.4: Cambio de contraseña
T4.5: Perfil de usuario
T4.6: Tests de administración completos

Autor: Sistema de Testing v3.1.0
Fecha: 2025-01-07
"""

import requests
import json
import time
from datetime import datetime

class AdminCompleteTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:5173"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "sprint": "Sprint 4 - Completado",
            "tasks": ["T4.4", "T4.5", "T4.6"],
            "results": {},
            "summary": {}
        }
        
        # Credenciales de prueba
        self.superadmin_credentials = {
            "email": "admin@parkingaltea.com",
            "password": "admin123"
        }
        
        self.test_user_credentials = {
            "email": "test_user@example.com",
            "password": "test123"
        }
        
        self.token = None
        self.test_user_token = None
        self.session = requests.Session()
        self.test_user_session = requests.Session()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def login_superadmin(self):
        """Iniciar sesión como superadmin"""
        try:
            self.log("Iniciando sesión como superadmin...")
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=self.superadmin_credentials
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self.log("Login exitoso como superadmin")
                return True
            else:
                self.log(f"Error en login superadmin: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error en login superadmin: {str(e)}", "ERROR")
            return False

    def create_test_user(self):
        """Crear usuario de prueba"""
        try:
            test_user_data = {
                "email": f"test_user_{int(time.time())}@example.com",
                "password": "test123",
                "role": "user",
                "name": "Usuario de Prueba"
            }
            
            response = self.session.post(f"{self.base_url}/admin/users", json=test_user_data)
            if response.status_code == 201:
                user_data = response.json()
                self.test_user_credentials["email"] = test_user_data["email"]
                self.log(f"Usuario de prueba creado: {test_user_data['email']}")
                return user_data.get('user', {}).get('id')
            else:
                self.log(f"Error creando usuario de prueba: {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Error creando usuario de prueba: {str(e)}", "ERROR")
            return None

    def login_test_user(self):
        """Iniciar sesión como usuario de prueba"""
        try:
            self.log("Iniciando sesión como usuario de prueba...")
            response = self.test_user_session.post(
                f"{self.base_url}/auth/login",
                json=self.test_user_credentials
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_token = data.get('token')
                self.test_user_session.headers.update({'Authorization': f'Bearer {self.test_user_token}'})
                self.log("Login exitoso como usuario de prueba")
                return True
            else:
                self.log(f"Error en login usuario de prueba: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error en login usuario de prueba: {str(e)}", "ERROR")
            return False

    def test_t4_4_password_change(self):
        """Test T4.4 - Cambio de contraseña"""
        self.log("=== Test T4.4 - Cambio de contraseña ===")
        results = {"passed": 0, "failed": 0, "tests": []}

        # Test 1: Cambio de contraseña exitoso
        try:
            new_password = f"newpass_{int(time.time())}"
            password_data = {
                "current_password": self.test_user_credentials["password"],
                "new_password": new_password
            }
            
            response = self.test_user_session.put(f"{self.base_url}/auth/password", json=password_data)
            if response.status_code == 200:
                self.log("✓ Cambio de contraseña exitoso")
                results["tests"].append({
                    "name": "Cambio de contraseña exitoso",
                    "status": "PASS",
                    "details": "Contraseña cambiada correctamente"
                })
                results["passed"] += 1
                
                # Actualizar contraseña en credenciales
                self.test_user_credentials["password"] = new_password
            else:
                self.log(f"✗ Error en cambio de contraseña: {response.status_code} - {response.text}", "ERROR")
                results["tests"].append({
                    "name": "Cambio de contraseña exitoso",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de cambio de contraseña: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Cambio de contraseña exitoso",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 2: Validación de contraseña actual incorrecta
        try:
            password_data = {
                "current_password": "wrong_password",
                "new_password": "new_password"
            }
            
            response = self.test_user_session.put(f"{self.base_url}/auth/password", json=password_data)
            if response.status_code == 400:
                self.log("✓ Validación de contraseña actual incorrecta")
                results["tests"].append({
                    "name": "Validación contraseña actual",
                    "status": "PASS",
                    "details": "Rechaza contraseña actual incorrecta"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error en validación: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Validación contraseña actual",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de validación: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Validación contraseña actual",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 3: Validación de contraseña nueva débil
        try:
            password_data = {
                "current_password": self.test_user_credentials["password"],
                "new_password": "123"
            }
            
            response = self.test_user_session.put(f"{self.base_url}/auth/password", json=password_data)
            if response.status_code == 400:
                self.log("✓ Validación de contraseña nueva débil")
                results["tests"].append({
                    "name": "Validación contraseña nueva",
                    "status": "PASS",
                    "details": "Rechaza contraseña nueva débil"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error en validación de contraseña débil: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Validación contraseña nueva",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de contraseña débil: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Validación contraseña nueva",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        self.test_results["results"]["T4.4"] = results
        return results["failed"] == 0

    def test_t4_5_user_profile(self):
        """Test T4.5 - Perfil de usuario"""
        self.log("=== Test T4.5 - Perfil de usuario ===")
        results = {"passed": 0, "failed": 0, "tests": []}

        # Test 1: Obtener información del perfil
        try:
            response = self.test_user_session.get(f"{self.base_url}/auth/permissions")
            if response.status_code == 200:
                data = response.json()
                self.log("✓ Información del perfil obtenida")
                results["tests"].append({
                    "name": "Obtener información del perfil",
                    "status": "PASS",
                    "details": "Perfil accesible correctamente"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error obteniendo perfil: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Obtener información del perfil",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de perfil: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Obtener información del perfil",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 2: Obtener parkings del usuario
        try:
            response = self.test_user_session.get(f"{self.base_url}/user/parkings")
            if response.status_code == 200:
                data = response.json()
                parkings = data.get('parkings', [])
                self.log(f"✓ Parkings del usuario obtenidos: {len(parkings)}")
                results["tests"].append({
                    "name": "Obtener parkings del usuario",
                    "status": "PASS",
                    "details": f"Encontrados {len(parkings)} parkings"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error obteniendo parkings: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Obtener parkings del usuario",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de parkings: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Obtener parkings del usuario",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 3: Verificar permisos específicos
        try:
            response = self.test_user_session.get(f"{self.base_url}/auth/permissions")
            if response.status_code == 200:
                data = response.json()
                permissions = data.get('permissions', {})
                
                # Verificar estructura de permisos
                has_parking_ids = 'parking_ids' in permissions
                has_panel_ids = 'panel_ids' in permissions
                has_access_ids = 'access_ids' in permissions
                
                if has_parking_ids and has_panel_ids and has_access_ids:
                    self.log("✓ Estructura de permisos correcta")
                    results["tests"].append({
                        "name": "Estructura de permisos",
                        "status": "PASS",
                        "details": "Permisos estructurados correctamente"
                    })
                    results["passed"] += 1
                else:
                    self.log("✗ Estructura de permisos incorrecta", "ERROR")
                    results["tests"].append({
                        "name": "Estructura de permisos",
                        "status": "FAIL",
                        "details": "Faltan campos de permisos"
                    })
                    results["failed"] += 1
            else:
                self.log(f"✗ Error verificando permisos: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Estructura de permisos",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de estructura de permisos: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Estructura de permisos",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        self.test_results["results"]["T4.5"] = results
        return results["failed"] == 0

    def test_t4_6_admin_complete(self):
        """Test T4.6 - Tests de administración completos"""
        self.log("=== Test T4.6 - Tests de administración completos ===")
        results = {"passed": 0, "failed": 0, "tests": []}

        # Test 1: Verificar acceso a rutas de administración
        admin_routes = [
            "/admin/users",
            "/admin"
        ]
        
        for route in admin_routes:
            try:
                response = self.session.get(f"{self.base_url}{route}")
                if response.status_code == 200:
                    self.log(f"✓ Ruta {route} accesible para superadmin")
                    results["tests"].append({
                        "name": f"Acceso a {route}",
                        "status": "PASS",
                        "details": "Ruta accesible para superadmin"
                    })
                    results["passed"] += 1
                else:
                    self.log(f"✗ Error accediendo a {route}: {response.status_code}", "ERROR")
                    results["tests"].append({
                        "name": f"Acceso a {route}",
                        "status": "FAIL",
                        "details": f"Status code: {response.status_code}"
                    })
                    results["failed"] += 1
            except Exception as e:
                self.log(f"✗ Error en test de ruta {route}: {str(e)}", "ERROR")
                results["tests"].append({
                    "name": f"Acceso a {route}",
                    "status": "FAIL",
                    "details": str(e)
                })
                results["failed"] += 1

        # Test 2: Verificar que usuario normal no puede acceder a rutas de admin
        try:
            response = self.test_user_session.get(f"{self.base_url}/admin/users")
            if response.status_code == 403:
                self.log("✓ Usuario normal bloqueado de rutas de admin")
                results["tests"].append({
                    "name": "Bloqueo de usuario normal",
                    "status": "PASS",
                    "details": "Usuario normal no puede acceder a admin"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Usuario normal puede acceder a admin: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Bloqueo de usuario normal",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de bloqueo: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Bloqueo de usuario normal",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 3: Verificar funcionalidades completas de gestión de usuarios
        try:
            # Obtener lista de usuarios
            response = self.session.get(f"{self.base_url}/admin/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                if users:
                    test_user = users[0]
                    user_id = test_user['id']
                    
                    # Verificar que el usuario tiene todos los campos necesarios
                    required_fields = ['id', 'email', 'role', 'is_active', 'created_at']
                    missing_fields = [field for field in required_fields if field not in test_user]
                    
                    if not missing_fields:
                        self.log("✓ Estructura de usuario completa")
                        results["tests"].append({
                            "name": "Estructura de usuario",
                            "status": "PASS",
                            "details": "Usuario tiene todos los campos requeridos"
                        })
                        results["passed"] += 1
                    else:
                        self.log(f"✗ Campos faltantes en usuario: {missing_fields}", "ERROR")
                        results["tests"].append({
                            "name": "Estructura de usuario",
                            "status": "FAIL",
                            "details": f"Faltan campos: {missing_fields}"
                        })
                        results["failed"] += 1
                else:
                    self.log("⚠ No hay usuarios para testing", "WARNING")
                    results["tests"].append({
                        "name": "Estructura de usuario",
                        "status": "SKIP",
                        "details": "No hay usuarios disponibles"
                    })
            else:
                self.log(f"✗ Error obteniendo usuarios: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Estructura de usuario",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de estructura de usuario: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Estructura de usuario",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 4: Verificar integración completa del sistema
        try:
            # Verificar que el sistema mantiene consistencia
            endpoints_to_check = [
                "/auth/permissions",
                "/user/parkings",
                "/admin/users"
            ]
            
            all_endpoints_working = True
            for endpoint in endpoints_to_check:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code != 200:
                    all_endpoints_working = False
                    self.log(f"✗ Endpoint {endpoint} no funciona: {response.status_code}", "ERROR")
                    break
            
            if all_endpoints_working:
                self.log("✓ Integración completa del sistema verificada")
                results["tests"].append({
                    "name": "Integración del sistema",
                    "status": "PASS",
                    "details": "Todos los endpoints funcionan correctamente"
                })
                results["passed"] += 1
            else:
                results["tests"].append({
                    "name": "Integración del sistema",
                    "status": "FAIL",
                    "details": "Algunos endpoints no funcionan"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de integración: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Integración del sistema",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        self.test_results["results"]["T4.6"] = results
        return results["failed"] == 0

    def cleanup_test_user(self, user_id):
        """Limpiar usuario de prueba"""
        if user_id:
            try:
                self.session.delete(f"{self.base_url}/admin/users/{user_id}")
                self.log(f"✓ Usuario de prueba eliminado - ID: {user_id}")
            except:
                pass

    def run_all_tests(self):
        """Ejecutar todos los tests"""
        self.log("🚀 Iniciando tests completos de Sprint 4")
        self.log("=" * 60)
        
        # Login como superadmin
        if not self.login_superadmin():
            self.log("❌ No se pudo iniciar sesión como superadmin. Abortando tests.", "ERROR")
            return False
        
        # Crear usuario de prueba
        test_user_id = self.create_test_user()
        if not test_user_id:
            self.log("❌ No se pudo crear usuario de prueba. Abortando tests.", "ERROR")
            return False
        
        # Login como usuario de prueba
        if not self.login_test_user():
            self.log("❌ No se pudo iniciar sesión como usuario de prueba. Abortando tests.", "ERROR")
            self.cleanup_test_user(test_user_id)
            return False
        
        # Ejecutar tests
        t4_4_success = self.test_t4_4_password_change()
        t4_5_success = self.test_t4_5_user_profile()
        t4_6_success = self.test_t4_6_admin_complete()
        
        # Limpiar usuario de prueba
        self.cleanup_test_user(test_user_id)
        
        # Resumen
        self.log("=" * 60)
        self.log("📊 RESUMEN DE TESTS COMPLETOS")
        self.log("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for task, results in self.test_results["results"].items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASÓ" if failed == 0 else "❌ FALLÓ"
            self.log(f"{task}: {status} ({passed} pasaron, {failed} fallaron)")
        
        self.log("=" * 60)
        self.log(f"TOTAL: {total_passed} tests pasaron, {total_failed} tests fallaron")
        
        overall_success = total_failed == 0
        self.log(f"RESULTADO GENERAL: {'✅ ÉXITO' if overall_success else '❌ FALLO'}")
        
        # Guardar resultados
        self.test_results["summary"] = {
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success": overall_success,
            "tasks_completed": [task for task, results in self.test_results["results"].items() if results["failed"] == 0],
            "sprint_completion": "100%" if overall_success else "Parcial"
        }
        
        # Guardar en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_sprint4_complete_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.log(f"📄 Resultados guardados en: {filename}")
        except Exception as e:
            self.log(f"⚠ Error guardando resultados: {str(e)}", "WARNING")
        
        return overall_success

def main():
    """Función principal"""
    print("🧪 Test Completo de Sprint 4 - Funcionalidades de Administración")
    print("T4.4: Cambio de contraseña")
    print("T4.5: Perfil de usuario")
    print("T4.6: Tests de administración completos")
    print("=" * 60)
    
    test = AdminCompleteTest()
    success = test.run_all_tests()
    
    if success:
        print("\n🎉 ¡Sprint 4 completado al 100%! Todas las funcionalidades funcionan correctamente.")
        return 0
    else:
        print("\n💥 Algunos tests fallaron. Revisar resultados para más detalles.")
        return 1

if __name__ == "__main__":
    exit(main()) 