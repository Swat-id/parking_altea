#!/usr/bin/env python3
"""
Test para Sprint 4 - Páginas de Administración
T4.1: Página de gestión de usuarios
T4.2: Asignación de parkings
T4.3: Dashboard de administración

Autor: Sistema de Testing v3.1.0
Fecha: 2025-01-07
"""

import requests
import json
import time
from datetime import datetime

class AdminPagesTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:5173"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "sprint": "Sprint 4",
            "tasks": ["T4.1", "T4.2", "T4.3"],
            "results": {},
            "summary": {}
        }
        
        # Credenciales de superadmin
        self.superadmin_credentials = {
            "email": "admin@parkingaltea.com",
            "password": "admin123"
        }
        
        self.token = None
        self.session = requests.Session()

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
                self.log(f"Error en login: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error en login: {str(e)}", "ERROR")
            return False

    def test_t4_1_user_management_page(self):
        """Test T4.1 - Página de gestión de usuarios"""
        self.log("=== Test T4.1 - Página de gestión de usuarios ===")
        results = {"passed": 0, "failed": 0, "tests": []}

        # Test 1: Verificar endpoint de usuarios
        try:
            response = self.session.get(f"{self.base_url}/admin/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                self.log(f"✓ Endpoint /admin/users funciona - {len(users)} usuarios encontrados")
                results["tests"].append({
                    "name": "Endpoint /admin/users",
                    "status": "PASS",
                    "details": f"Encontrados {len(users)} usuarios"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error en endpoint /admin/users: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Endpoint /admin/users",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de endpoint: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Endpoint /admin/users",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 2: Crear usuario de prueba
        try:
            test_user = {
                "email": f"test_user_{int(time.time())}@test.com",
                "password": "test123",
                "role": "user",
                "name": "Usuario de Prueba"
            }
            
            response = self.session.post(f"{self.base_url}/admin/users", json=test_user)
            if response.status_code == 201:
                user_data = response.json()
                test_user_id = user_data.get('user', {}).get('id')
                self.log(f"✓ Usuario de prueba creado - ID: {test_user_id}")
                results["tests"].append({
                    "name": "Crear usuario",
                    "status": "PASS",
                    "details": f"Usuario creado con ID: {test_user_id}"
                })
                results["passed"] += 1
                
                # Limpiar usuario de prueba
                self.session.delete(f"{self.base_url}/admin/users/{test_user_id}")
            else:
                self.log(f"✗ Error creando usuario: {response.status_code} - {response.text}", "ERROR")
                results["tests"].append({
                    "name": "Crear usuario",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de creación: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Crear usuario",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 3: Verificar permisos de superadmin
        try:
            response = self.session.get(f"{self.base_url}/auth/permissions")
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('permissions', {}).get('is_superadmin'):
                    self.log("✓ Permisos de superadmin verificados")
                    results["tests"].append({
                        "name": "Permisos superadmin",
                        "status": "PASS",
                        "details": "Permisos verificados correctamente"
                    })
                    results["passed"] += 1
                else:
                    self.log("✗ Permisos de superadmin no verificados", "ERROR")
                    results["tests"].append({
                        "name": "Permisos superadmin",
                        "status": "FAIL",
                        "details": "No se detectaron permisos de superadmin"
                    })
                    results["failed"] += 1
            else:
                self.log(f"✗ Error verificando permisos: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Permisos superadmin",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de permisos: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Permisos superadmin",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        self.test_results["results"]["T4.1"] = results
        return results["failed"] == 0

    def test_t4_2_parking_assignment(self):
        """Test T4.2 - Asignación de parkings"""
        self.log("=== Test T4.2 - Asignación de parkings ===")
        results = {"passed": 0, "failed": 0, "tests": []}

        # Test 1: Obtener parkings disponibles
        try:
            response = self.session.get(f"{self.base_url}/parkings")
            if response.status_code == 200:
                data = response.json()
                parkings = data.get('parkings', [])
                self.log(f"✓ Parkings disponibles: {len(parkings)}")
                results["tests"].append({
                    "name": "Obtener parkings",
                    "status": "PASS",
                    "details": f"Encontrados {len(parkings)} parkings"
                })
                results["passed"] += 1
                
                if parkings:
                    test_parking_id = parkings[0]['id']
                else:
                    self.log("⚠ No hay parkings disponibles para testing", "WARNING")
                    test_parking_id = None
            else:
                self.log(f"✗ Error obteniendo parkings: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Obtener parkings",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
                test_parking_id = None
        except Exception as e:
            self.log(f"✗ Error en test de parkings: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Obtener parkings",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1
            test_parking_id = None

        # Test 2: Crear usuario para asignación
        test_user_id = None
        try:
            test_user = {
                "email": f"assign_test_{int(time.time())}@test.com",
                "password": "test123",
                "role": "user",
                "name": "Usuario Asignación"
            }
            
            response = self.session.post(f"{self.base_url}/admin/users", json=test_user)
            if response.status_code == 201:
                user_data = response.json()
                test_user_id = user_data.get('user', {}).get('id')
                self.log(f"✓ Usuario para asignación creado - ID: {test_user_id}")
                results["tests"].append({
                    "name": "Crear usuario para asignación",
                    "status": "PASS",
                    "details": f"Usuario creado con ID: {test_user_id}"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error creando usuario para asignación: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Crear usuario para asignación",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de usuario asignación: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Crear usuario para asignación",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 3: Asignar parkings al usuario
        if test_user_id and test_parking_id:
            try:
                assignment_data = {
                    "parking_ids": [test_parking_id]
                }
                
                response = self.session.post(
                    f"{self.base_url}/admin/users/{test_user_id}/assign",
                    json=assignment_data
                )
                
                if response.status_code == 200:
                    self.log(f"✓ Parkings asignados al usuario {test_user_id}")
                    results["tests"].append({
                        "name": "Asignar parkings",
                        "status": "PASS",
                        "details": f"Parking {test_parking_id} asignado a usuario {test_user_id}"
                    })
                    results["passed"] += 1
                else:
                    self.log(f"✗ Error asignando parkings: {response.status_code} - {response.text}", "ERROR")
                    results["tests"].append({
                        "name": "Asignar parkings",
                        "status": "FAIL",
                        "details": f"Status code: {response.status_code}"
                    })
                    results["failed"] += 1
            except Exception as e:
                self.log(f"✗ Error en test de asignación: {str(e)}", "ERROR")
                results["tests"].append({
                    "name": "Asignar parkings",
                    "status": "FAIL",
                    "details": str(e)
                })
                results["failed"] += 1

        # Test 4: Verificar asignación
        if test_user_id:
            try:
                response = self.session.get(f"{self.base_url}/admin/users/{test_user_id}")
                if response.status_code == 200:
                    user_data = response.json()
                    user_parkings = user_data.get('user', {}).get('parkings', [])
                    if user_parkings:
                        self.log(f"✓ Asignación verificada - {len(user_parkings)} parkings asignados")
                        results["tests"].append({
                            "name": "Verificar asignación",
                            "status": "PASS",
                            "details": f"{len(user_parkings)} parkings asignados"
                        })
                        results["passed"] += 1
                    else:
                        self.log("✗ No se encontraron parkings asignados", "ERROR")
                        results["tests"].append({
                            "name": "Verificar asignación",
                            "status": "FAIL",
                            "details": "No se encontraron parkings asignados"
                        })
                        results["failed"] += 1
                else:
                    self.log(f"✗ Error verificando asignación: {response.status_code}", "ERROR")
                    results["tests"].append({
                        "name": "Verificar asignación",
                        "status": "FAIL",
                        "details": f"Status code: {response.status_code}"
                    })
                    results["failed"] += 1
            except Exception as e:
                self.log(f"✗ Error en test de verificación: {str(e)}", "ERROR")
                results["tests"].append({
                    "name": "Verificar asignación",
                    "status": "FAIL",
                    "details": str(e)
                })
                results["failed"] += 1

            # Limpiar usuario de prueba
            try:
                self.session.delete(f"{self.base_url}/admin/users/{test_user_id}")
                self.log(f"✓ Usuario de prueba eliminado - ID: {test_user_id}")
            except:
                pass

        self.test_results["results"]["T4.2"] = results
        return results["failed"] == 0

    def test_t4_3_admin_dashboard(self):
        """Test T4.3 - Dashboard de administración"""
        self.log("=== Test T4.3 - Dashboard de administración ===")
        results = {"passed": 0, "failed": 0, "tests": []}

        # Test 1: Verificar estadísticas de usuarios
        try:
            response = self.session.get(f"{self.base_url}/admin/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                # Calcular estadísticas
                total_users = len(users)
                active_users = len([u for u in users if u.get('is_active')])
                superadmins = len([u for u in users if u.get('role') == 'superadmin'])
                regular_users = len([u for u in users if u.get('role') == 'user'])
                
                self.log(f"✓ Estadísticas calculadas:")
                self.log(f"  - Total usuarios: {total_users}")
                self.log(f"  - Usuarios activos: {active_users}")
                self.log(f"  - Superadmins: {superadmins}")
                self.log(f"  - Usuarios regulares: {regular_users}")
                
                results["tests"].append({
                    "name": "Estadísticas de usuarios",
                    "status": "PASS",
                    "details": f"Total: {total_users}, Activos: {active_users}, Superadmins: {superadmins}, Regulares: {regular_users}"
                })
                results["passed"] += 1
            else:
                self.log(f"✗ Error obteniendo estadísticas: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Estadísticas de usuarios",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de estadísticas: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Estadísticas de usuarios",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        # Test 2: Verificar acceso a rutas de administración
        admin_routes = [
            "/admin/users",
            "/admin"
        ]
        
        for route in admin_routes:
            try:
                response = self.session.get(f"{self.base_url}{route}")
                if response.status_code == 200:
                    self.log(f"✓ Ruta {route} accesible")
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

        # Test 3: Verificar funcionalidades de gestión
        try:
            # Test de toggle de estado de usuario
            response = self.session.get(f"{self.base_url}/admin/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                if users:
                    test_user = users[0]
                    if test_user.get('role') != 'superadmin':  # No togglear superadmin
                        user_id = test_user['id']
                        original_status = test_user.get('is_active')
                        
                        # Toggle estado
                        response = self.session.post(f"{self.base_url}/admin/users/{user_id}/toggle")
                        if response.status_code == 200:
                            self.log(f"✓ Toggle de estado exitoso para usuario {user_id}")
                            results["tests"].append({
                                "name": "Toggle estado usuario",
                                "status": "PASS",
                                "details": f"Estado cambiado para usuario {user_id}"
                            })
                            results["passed"] += 1
                        else:
                            self.log(f"✗ Error en toggle de estado: {response.status_code}", "ERROR")
                            results["tests"].append({
                                "name": "Toggle estado usuario",
                                "status": "FAIL",
                                "details": f"Status code: {response.status_code}"
                            })
                            results["failed"] += 1
                    else:
                        self.log("⚠ Usuario es superadmin, saltando toggle", "WARNING")
                        results["tests"].append({
                            "name": "Toggle estado usuario",
                            "status": "SKIP",
                            "details": "Usuario es superadmin"
                        })
                else:
                    self.log("⚠ No hay usuarios para testing", "WARNING")
                    results["tests"].append({
                        "name": "Toggle estado usuario",
                        "status": "SKIP",
                        "details": "No hay usuarios disponibles"
                    })
            else:
                self.log(f"✗ Error obteniendo usuarios para toggle: {response.status_code}", "ERROR")
                results["tests"].append({
                    "name": "Toggle estado usuario",
                    "status": "FAIL",
                    "details": f"Status code: {response.status_code}"
                })
                results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Error en test de toggle: {str(e)}", "ERROR")
            results["tests"].append({
                "name": "Toggle estado usuario",
                "status": "FAIL",
                "details": str(e)
            })
            results["failed"] += 1

        self.test_results["results"]["T4.3"] = results
        return results["failed"] == 0

    def run_all_tests(self):
        """Ejecutar todos los tests"""
        self.log("🚀 Iniciando tests de Sprint 4 - Páginas de Administración")
        self.log("=" * 60)
        
        # Login como superadmin
        if not self.login_superadmin():
            self.log("❌ No se pudo iniciar sesión como superadmin. Abortando tests.", "ERROR")
            return False
        
        # Ejecutar tests
        t4_1_success = self.test_t4_1_user_management_page()
        t4_2_success = self.test_t4_2_parking_assignment()
        t4_3_success = self.test_t4_3_admin_dashboard()
        
        # Resumen
        self.log("=" * 60)
        self.log("📊 RESUMEN DE TESTS")
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
            "tasks_completed": [task for task, results in self.test_results["results"].items() if results["failed"] == 0]
        }
        
        # Guardar en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_sprint4_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.log(f"📄 Resultados guardados en: {filename}")
        except Exception as e:
            self.log(f"⚠ Error guardando resultados: {str(e)}", "WARNING")
        
        return overall_success

def main():
    """Función principal"""
    print("🧪 Test de Sprint 4 - Páginas de Administración")
    print("T4.1: Página de gestión de usuarios")
    print("T4.2: Asignación de parkings")
    print("T4.3: Dashboard de administración")
    print("=" * 60)
    
    test = AdminPagesTest()
    success = test.run_all_tests()
    
    if success:
        print("\n🎉 ¡Todos los tests pasaron! Sprint 4 completado exitosamente.")
        return 0
    else:
        print("\n💥 Algunos tests fallaron. Revisar resultados para más detalles.")
        return 1

if __name__ == "__main__":
    exit(main()) 