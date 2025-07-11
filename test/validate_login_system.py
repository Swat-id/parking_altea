#!/usr/bin/env python3
"""
Script de Validación del Sistema de Login - Parking Altea v3.1.0
Valida todos los aspectos críticos del sistema de autenticación antes del despliegue
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
from auth import create_user, authenticate_user, verify_token, get_user_permissions
from models import User, UserParking, Parking

class LoginSystemValidator:
    """Validador completo del sistema de login"""
    
    def __init__(self):
        self.engine = create_engine(config.DB_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.results = {
            'database': {},
            'backend': {},
            'frontend': {},
            'security': {},
            'integration': {}
        }
        self.test_users = []
        
    def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        try:
            # Eliminar usuarios de prueba
            self.session.query(User).filter(User.email.like('test_validation_%')).delete()
            self.session.commit()
            print("✅ Datos de prueba limpiados")
        except Exception as e:
            print(f"⚠️  Error limpiando datos de prueba: {e}")
    
    def test_01_database_structure(self):
        """Test 1: Verificar estructura de base de datos"""
        print("\n🔍 Test 1: Verificando estructura de base de datos...")
        
        try:
            # Verificar tabla users
            result = self.session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('id', 'name', 'email', 'password_hash', 'role', 'created_at', 'updated_at', 'is_active')
                ORDER BY column_name
            """))
            
            columns = {row[0]: row[1] for row in result.fetchall()}
            required_columns = ['id', 'name', 'email', 'password_hash', 'role', 'created_at', 'updated_at', 'is_active']
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                self.results['database']['structure'] = {
                    'status': 'FAILED',
                    'error': f'Columnas faltantes: {missing_columns}'
                }
                print(f"❌ Columnas faltantes: {missing_columns}")
                return False
            else:
                self.results['database']['structure'] = {'status': 'PASSED'}
                print("✅ Estructura de tabla users correcta")
                return True
                
        except Exception as e:
            self.results['database']['structure'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error verificando estructura: {e}")
            return False
    
    def test_02_role_constraints(self):
        """Test 2: Verificar constraints de roles"""
        print("\n🔒 Test 2: Verificando constraints de roles...")
        
        try:
            # Verificar constraint de roles
            result = self.session.execute(text("""
                SELECT constraint_name, check_clause
                FROM information_schema.check_constraints
                WHERE constraint_name = 'chk_user_role'
            """))
            
            constraint = result.fetchone()
            if not constraint:
                self.results['database']['constraints'] = {
                    'status': 'FAILED',
                    'error': 'Constraint chk_user_role no existe'
                }
                print("❌ Constraint chk_user_role no existe")
                return False
            
            # Verificar que permite roles válidos
            check_clause = constraint[1].lower()
            if 'superadmin' not in check_clause or 'user' not in check_clause:
                self.results['database']['constraints'] = {
                    'status': 'FAILED',
                    'error': 'Constraint no permite roles superadmin/user'
                }
                print("❌ Constraint no permite roles superadmin/user")
                return False
            
            self.results['database']['constraints'] = {'status': 'PASSED'}
            print("✅ Constraints de roles correctos")
            return True
            
        except Exception as e:
            self.results['database']['constraints'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error verificando constraints: {e}")
            return False
    
    def test_03_database_indexes(self):
        """Test 3: Verificar índices de base de datos"""
        print("\n📊 Test 3: Verificando índices de base de datos...")
        
        try:
            result = self.session.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'users' 
                AND indexname IN ('idx_users_email', 'idx_users_role', 'idx_users_active_role')
                ORDER BY indexname
            """))
            
            indexes = [row[0] for row in result.fetchall()]
            expected_indexes = ['idx_users_email', 'idx_users_role', 'idx_users_active_role']
            
            missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
            
            if missing_indexes:
                self.results['database']['indexes'] = {
                    'status': 'FAILED',
                    'error': f'Índices faltantes: {missing_indexes}'
                }
                print(f"❌ Índices faltantes: {missing_indexes}")
                return False
            else:
                self.results['database']['indexes'] = {'status': 'PASSED'}
                print("✅ Índices de base de datos correctos")
                return True
                
        except Exception as e:
            self.results['database']['indexes'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error verificando índices: {e}")
            return False
    
    def test_04_user_creation_and_roles(self):
        """Test 4: Verificar creación de usuarios y roles"""
        print("\n👤 Test 4: Verificando creación de usuarios y roles...")
        
        try:
            # Crear usuario con rol user
            user_result = create_user(
                self.session, 
                'Test User Validation', 
                'test_validation_user@altea.es', 
                'test1234!', 
                'user'
            )
            
            if not user_result['success']:
                self.results['backend']['user_creation'] = {
                    'status': 'FAILED',
                    'error': user_result['error']
                }
                print(f"❌ Error creando usuario: {user_result['error']}")
                return False
            
            # Crear usuario con rol superadmin
            admin_result = create_user(
                self.session, 
                'Test Admin Validation', 
                'test_validation_admin@altea.es', 
                'test1234!', 
                'superadmin'
            )
            
            if not admin_result['success']:
                self.results['backend']['admin_creation'] = {
                    'status': 'FAILED',
                    'error': admin_result['error']
                }
                print(f"❌ Error creando admin: {admin_result['error']}")
                return False
            
            # Verificar que los usuarios se crearon correctamente
            user = self.session.query(User).filter(User.email == 'test_validation_user@altea.es').first()
            admin = self.session.query(User).filter(User.email == 'test_validation_admin@altea.es').first()
            
            if not user or not admin:
                self.results['backend']['user_verification'] = {
                    'status': 'FAILED',
                    'error': 'Usuarios no encontrados en base de datos'
                }
                print("❌ Usuarios no encontrados en base de datos")
                return False
            
            # Verificar roles
            if user.role != 'user' or admin.role != 'superadmin':
                self.results['backend']['role_verification'] = {
                    'status': 'FAILED',
                    'error': f'Roles incorrectos: user={user.role}, admin={admin.role}'
                }
                print(f"❌ Roles incorrectos: user={user.role}, admin={admin.role}")
                return False
            
            self.test_users = [user, admin]
            self.results['backend']['user_creation'] = {'status': 'PASSED'}
            self.results['backend']['role_verification'] = {'status': 'PASSED'}
            print("✅ Creación de usuarios y roles correcta")
            return True
            
        except Exception as e:
            self.results['backend']['user_creation'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error en creación de usuarios: {e}")
            return False
    
    def test_05_authentication_and_tokens(self):
        """Test 5: Verificar autenticación y generación de tokens"""
        print("\n🔑 Test 5: Verificando autenticación y tokens...")
        
        try:
            # Autenticar usuario regular
            user_auth = authenticate_user(
                self.session, 
                'test_validation_user@altea.es', 
                'test1234!'
            )
            
            if not user_auth['success']:
                self.results['backend']['user_authentication'] = {
                    'status': 'FAILED',
                    'error': user_auth['error']
                }
                print(f"❌ Error autenticando usuario: {user_auth['error']}")
                return False
            
            # Autenticar admin
            admin_auth = authenticate_user(
                self.session, 
                'test_validation_admin@altea.es', 
                'test1234!'
            )
            
            if not admin_auth['success']:
                self.results['backend']['admin_authentication'] = {
                    'status': 'FAILED',
                    'error': admin_auth['error']
                }
                print(f"❌ Error autenticando admin: {admin_auth['error']}")
                return False
            
            # Verificar tokens
            user_token = user_auth['token']
            admin_token = admin_auth['token']
            
            # Verificar longitud de tokens (deben ser > 255 caracteres)
            if len(user_token) <= 255:
                self.results['security']['token_length'] = {
                    'status': 'FAILED',
                    'error': f'Token demasiado corto: {len(user_token)} caracteres'
                }
                print(f"❌ Token demasiado corto: {len(user_token)} caracteres")
                return False
            
            if len(admin_token) <= 255:
                self.results['security']['token_length'] = {
                    'status': 'FAILED',
                    'error': f'Token admin demasiado corto: {len(admin_token)} caracteres'
                }
                print(f"❌ Token admin demasiado corto: {len(admin_token)} caracteres")
                return False
            
            # Verificar tokens
            user_token_data = verify_token(user_token)
            admin_token_data = verify_token(admin_token)
            
            if not user_token_data['success'] or not admin_token_data['success']:
                self.results['security']['token_verification'] = {
                    'status': 'FAILED',
                    'error': 'Error verificando tokens'
                }
                print("❌ Error verificando tokens")
                return False
            
            # Verificar contenido de tokens
            if user_token_data['user_data']['role'] != 'user':
                self.results['security']['token_content'] = {
                    'status': 'FAILED',
                    'error': 'Token de usuario no contiene rol correcto'
                }
                print("❌ Token de usuario no contiene rol correcto")
                return False
            
            if admin_token_data['user_data']['role'] != 'superadmin':
                self.results['security']['token_content'] = {
                    'status': 'FAILED',
                    'error': 'Token de admin no contiene rol correcto'
                }
                print("❌ Token de admin no contiene rol correcto")
                return False
            
            self.results['backend']['user_authentication'] = {'status': 'PASSED'}
            self.results['backend']['admin_authentication'] = {'status': 'PASSED'}
            self.results['security']['token_length'] = {'status': 'PASSED'}
            self.results['security']['token_verification'] = {'status': 'PASSED'}
            self.results['security']['token_content'] = {'status': 'PASSED'}
            
            print(f"✅ Autenticación correcta - Tokens generados: {len(user_token)} y {len(admin_token)} caracteres")
            return True
            
        except Exception as e:
            self.results['backend']['authentication'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error en autenticación: {e}")
            return False
    
    def test_06_permissions_system(self):
        """Test 6: Verificar sistema de permisos"""
        print("\n🔐 Test 6: Verificando sistema de permisos...")
        
        try:
            # Obtener permisos del usuario regular
            user_permissions = get_user_permissions(self.session, self.test_users[0].id)
            
            if not user_permissions['success']:
                self.results['backend']['permissions'] = {
                    'status': 'FAILED',
                    'error': user_permissions['error']
                }
                print(f"❌ Error obteniendo permisos: {user_permissions['error']}")
                return False
            
            # Verificar estructura de permisos
            permissions = user_permissions['permissions']
            required_keys = ['parking_ids', 'panel_ids', 'access_ids']
            
            missing_keys = [key for key in required_keys if key not in permissions]
            
            if missing_keys:
                self.results['backend']['permissions_structure'] = {
                    'status': 'FAILED',
                    'error': f'Claves faltantes en permisos: {missing_keys}'
                }
                print(f"❌ Claves faltantes en permisos: {missing_keys}")
                return False
            
            self.results['backend']['permissions'] = {'status': 'PASSED'}
            self.results['backend']['permissions_structure'] = {'status': 'PASSED'}
            print("✅ Sistema de permisos funcionando correctamente")
            return True
            
        except Exception as e:
            self.results['backend']['permissions'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error en sistema de permisos: {e}")
            return False
    
    def test_07_api_endpoints(self):
        """Test 7: Verificar endpoints de la API"""
        print("\n🌐 Test 7: Verificando endpoints de la API...")
        
        try:
            # Determinar URL base
            api_base = "http://localhost:6001"
            
            # Test de endpoint de login
            login_data = {
                'email': 'test_validation_user@altea.es',
                'password': 'test1234!'
            }
            
            response = requests.post(f"{api_base}/auth/login", json=login_data, timeout=10)
            
            if response.status_code != 200:
                self.results['integration']['api_login'] = {
                    'status': 'FAILED',
                    'error': f'Status code: {response.status_code}, Response: {response.text}'
                }
                print(f"❌ Error en endpoint de login: {response.status_code}")
                return False
            
            login_response = response.json()
            
            if 'token' not in login_response or 'user' not in login_response:
                self.results['integration']['api_response'] = {
                    'status': 'FAILED',
                    'error': 'Respuesta de login no contiene token o user'
                }
                print("❌ Respuesta de login no contiene token o user")
                return False
            
            token = login_response['token']
            user_data = login_response['user']
            
            # Verificar longitud del token
            if len(token) <= 255:
                self.results['integration']['api_token_length'] = {
                    'status': 'FAILED',
                    'error': f'Token de API demasiado corto: {len(token)} caracteres'
                }
                print(f"❌ Token de API demasiado corto: {len(token)} caracteres")
                return False
            
            # Test de endpoint de permisos
            headers = {'Authorization': f'Bearer {token}'}
            permissions_response = requests.get(f"{api_base}/auth/permissions", headers=headers, timeout=10)
            
            if permissions_response.status_code != 200:
                self.results['integration']['api_permissions'] = {
                    'status': 'FAILED',
                    'error': f'Status code: {permissions_response.status_code}'
                }
                print(f"❌ Error en endpoint de permisos: {permissions_response.status_code}")
                return False
            
            self.results['integration']['api_login'] = {'status': 'PASSED'}
            self.results['integration']['api_response'] = {'status': 'PASSED'}
            self.results['integration']['api_token_length'] = {'status': 'PASSED'}
            self.results['integration']['api_permissions'] = {'status': 'PASSED'}
            
            print(f"✅ Endpoints de API funcionando - Token: {len(token)} caracteres")
            return True
            
        except requests.exceptions.ConnectionError:
            self.results['integration']['api_connection'] = {
                'status': 'FAILED',
                'error': 'No se puede conectar al servidor API'
            }
            print("❌ No se puede conectar al servidor API")
            return False
        except Exception as e:
            self.results['integration']['api_general'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error en endpoints de API: {e}")
            return False
    
    def test_08_security_validation(self):
        """Test 8: Validación de seguridad"""
        print("\n🛡️ Test 8: Validación de seguridad...")
        
        try:
            # Verificar que las contraseñas están hasheadas
            user = self.session.query(User).filter(User.email == 'test_validation_user@altea.es').first()
            
            if not user.password_hash.startswith('$2b$'):
                self.results['security']['password_hashing'] = {
                    'status': 'FAILED',
                    'error': 'Contraseña no está hasheada con bcrypt'
                }
                print("❌ Contraseña no está hasheada con bcrypt")
                return False
            
            # Verificar que no se puede acceder con contraseña incorrecta
            wrong_auth = authenticate_user(
                self.session, 
                'test_validation_user@altea.es', 
                'wrongpassword'
            )
            
            if wrong_auth['success']:
                self.results['security']['wrong_password'] = {
                    'status': 'FAILED',
                    'error': 'Autenticación exitosa con contraseña incorrecta'
                }
                print("❌ Autenticación exitosa con contraseña incorrecta")
                return False
            
            # Verificar que no se puede acceder con email inexistente
            nonexistent_auth = authenticate_user(
                self.session, 
                'nonexistent@altea.es', 
                'test1234!'
            )
            
            if nonexistent_auth['success']:
                self.results['security']['nonexistent_user'] = {
                    'status': 'FAILED',
                    'error': 'Autenticación exitosa con usuario inexistente'
                }
                print("❌ Autenticación exitosa con usuario inexistente")
                return False
            
            self.results['security']['password_hashing'] = {'status': 'PASSED'}
            self.results['security']['wrong_password'] = {'status': 'PASSED'}
            self.results['security']['nonexistent_user'] = {'status': 'PASSED'}
            
            print("✅ Validaciones de seguridad correctas")
            return True
            
        except Exception as e:
            self.results['security']['validation'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ Error en validación de seguridad: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🚀 Iniciando validación completa del sistema de login...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Ejecutar tests en orden
        tests = [
            ('Estructura de BD', self.test_01_database_structure),
            ('Constraints de roles', self.test_02_role_constraints),
            ('Índices de BD', self.test_03_database_indexes),
            ('Creación de usuarios', self.test_04_user_creation_and_roles),
            ('Autenticación y tokens', self.test_05_authentication_and_tokens),
            ('Sistema de permisos', self.test_06_permissions_system),
            ('Endpoints de API', self.test_07_api_endpoints),
            ('Validación de seguridad', self.test_08_security_validation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASADO")
                else:
                    print(f"❌ {test_name}: FALLIDO")
            except Exception as e:
                print(f"💥 {test_name}: ERROR - {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN DE VALIDACIÓN")
        print(f"Tests pasados: {passed_tests}/{total_tests}")
        print(f"Tiempo total: {duration:.2f} segundos")
        
        if passed_tests == total_tests:
            print("🎉 ¡TODOS LOS TESTS PASARON! El sistema está listo para despliegue.")
        else:
            print("⚠️  Algunos tests fallaron. Revisar antes del despliegue.")
        
        return passed_tests == total_tests
    
    def generate_report(self):
        """Generar reporte detallado"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'error_tests': 0
            },
            'results': self.results
        }
        
        # Contar resultados
        for category in self.results.values():
            for test_name, result in category.items():
                report['summary']['total_tests'] += 1
                if result['status'] == 'PASSED':
                    report['summary']['passed_tests'] += 1
                elif result['status'] == 'FAILED':
                    report['summary']['failed_tests'] += 1
                elif result['status'] == 'ERROR':
                    report['summary']['error_tests'] += 1
        
        return report
    
    def cleanup(self):
        """Limpieza final"""
        self.cleanup_test_data()
        self.session.close()

def main():
    """Función principal"""
    validator = LoginSystemValidator()
    
    try:
        success = validator.run_all_tests()
        
        # Generar reporte
        report = validator.generate_report()
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"login_validation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte guardado en: {report_file}")
        
        # Mostrar resumen final
        print(f"\n📋 RESUMEN FINAL:")
        print(f"✅ Tests pasados: {report['summary']['passed_tests']}")
        print(f"❌ Tests fallidos: {report['summary']['failed_tests']}")
        print(f"💥 Tests con error: {report['summary']['error_tests']}")
        
        if success:
            print("\n🎯 RECOMENDACIÓN: El sistema está listo para despliegue.")
            return 0
        else:
            print("\n⚠️  RECOMENDACIÓN: Corregir errores antes del despliegue.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario.")
        return 1
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        return 1
    finally:
        validator.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 