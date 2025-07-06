#!/usr/bin/env python3
"""
Tests Completos de Migración v3.1.0
Valida toda la funcionalidad de migración, rollback y asignaciones
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import unittest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
from models import User
import json
from datetime import datetime

class TestMigrationComplete(unittest.TestCase):
    """Test suite completo para la migración v3.1.0"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        print("🚀 Configurando tests completos de migración v3.1.0...")
        cls.engine = create_engine(config.DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()
        
        # Guardar estado inicial para comparaciones
        cls.initial_state = cls.capture_initial_state()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza final"""
        cls.session.close()
        print("✅ Tests completos de migración v3.1.0 finalizados")
    
    @classmethod
    def capture_initial_state(cls):
        """Capturar estado inicial de la base de datos"""
        state = {
            'users_count': cls.session.execute(text("SELECT COUNT(*) FROM users")).scalar(),
            'parkings_count': cls.session.execute(text("SELECT COUNT(*) FROM parkings")).scalar(),
            'assignments_count': cls.session.execute(text("SELECT COUNT(*) FROM user_parkings")).scalar(),
            'users_with_roles': cls.session.execute(text("SELECT COUNT(*) FROM users WHERE role IS NOT NULL")).scalar(),
            'users_with_updated_at': cls.session.execute(text("SELECT COUNT(*) FROM users WHERE updated_at IS NOT NULL")).scalar()
        }
        return state
    
    def test_01_database_structure(self):
        """Test 1: Verificar estructura de base de datos"""
        print("\n📝 Test 1: Verificando estructura de base de datos...")
        
        # Verificar que la tabla users existe
        result = self.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'users'
        """))
        
        self.assertIsNotNone(result.fetchone(), "Tabla 'users' no existe")
        print("✅ Tabla 'users' existe")
        
        # Verificar campos requeridos
        result = self.session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('id', 'name', 'email', 'password_hash', 'role', 'created_at', 'updated_at', 'is_active')
            ORDER BY column_name
        """))
        
        required_fields = ['id', 'name', 'email', 'password_hash', 'role', 'created_at', 'updated_at', 'is_active']
        found_fields = [row[0] for row in result.fetchall()]
        
        for field in required_fields:
            self.assertIn(field, found_fields, f"Campo '{field}' no existe en tabla users")
        
        print(f"✅ Campos requeridos encontrados: {found_fields}")
    
    def test_02_role_constraint(self):
        """Test 2: Verificar constraint de roles"""
        print("\n🔒 Test 2: Verificando constraint de roles...")
        
        result = self.session.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'chk_user_role'
        """))
        
        constraint = result.fetchone()
        self.assertIsNotNone(constraint, "Constraint 'chk_user_role' no existe")
        
        # Verificar que el constraint permite 'superadmin' y 'user'
        check_clause = constraint[1].lower()
        self.assertIn("superadmin", check_clause, "Constraint no permite 'superadmin'")
        self.assertIn("user", check_clause, "Constraint no permite 'user'")
        
        print(f"✅ Constraint de roles verificado: {constraint[0]}")
    
    def test_03_database_indexes(self):
        """Test 3: Verificar índices de base de datos"""
        print("\n📊 Test 3: Verificando índices de base de datos...")
        
        result = self.session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users' 
            AND indexname IN ('idx_users_email', 'idx_users_role', 'idx_users_active_role')
            ORDER BY indexname
        """))
        
        indexes = [row[0] for row in result.fetchall()]
        expected_indexes = ['idx_users_email', 'idx_users_role', 'idx_users_active_role']
        
        for index in expected_indexes:
            self.assertIn(index, indexes, f"Índice '{index}' no existe")
        
        print(f"✅ Índices verificados: {indexes}")
    
    def test_04_user_data_integrity(self):
        """Test 4: Verificar integridad de datos de usuarios"""
        print("\n🔍 Test 4: Verificando integridad de datos de usuarios...")
        
        # Verificar que todos los usuarios tienen rol
        result = self.session.execute(text("""
            SELECT COUNT(*) as users_without_role
            FROM users
            WHERE role IS NULL OR role = ''
        """))
        
        users_without_role = result.scalar()
        self.assertEqual(users_without_role, 0, "Existen usuarios sin rol asignado")
        print("✅ Todos los usuarios tienen rol asignado")
        
        # Verificar que todos los roles son válidos
        result = self.session.execute(text("""
            SELECT COUNT(*) as invalid_roles
            FROM users
            WHERE role NOT IN ('superadmin', 'user')
        """))
        
        invalid_roles = result.scalar()
        self.assertEqual(invalid_roles, 0, "Existen usuarios con roles inválidos")
        print("✅ Todos los roles son válidos")
        
        # Verificar que todos los usuarios tienen updated_at
        result = self.session.execute(text("""
            SELECT COUNT(*) as users_without_updated_at
            FROM users
            WHERE updated_at IS NULL
        """))
        
        users_without_updated_at = result.scalar()
        self.assertEqual(users_without_updated_at, 0, "Existen usuarios sin updated_at")
        print("✅ Todos los usuarios tienen updated_at")
    
    def test_05_user_model_properties(self):
        """Test 5: Verificar propiedades del modelo User"""
        print("\n🧪 Test 5: Verificando propiedades del modelo User...")
        
        # Crear instancia de superadmin
        superadmin = User(
            name="Test Superadmin",
            email="test@admin.com",
            password_hash="hash",
            role="superadmin"
        )
        
        # Verificar propiedades
        self.assertTrue(superadmin.is_superadmin, "is_superadmin debe ser True para superadmin")
        self.assertFalse(superadmin.is_regular_user, "is_regular_user debe ser False para superadmin")
        
        # Crear instancia de usuario regular
        regular_user = User(
            name="Test User",
            email="test@user.com",
            password_hash="hash",
            role="user"
        )
        
        # Verificar propiedades
        self.assertFalse(regular_user.is_superadmin, "is_superadmin debe ser False para usuario regular")
        self.assertTrue(regular_user.is_regular_user, "is_regular_user debe ser True para usuario regular")
        
        # Verificar representación
        self.assertIn("superadmin", str(superadmin), "Representación debe incluir rol")
        self.assertIn("test@admin.com", str(superadmin), "Representación debe incluir email")
        
        print("✅ Propiedades del modelo User verificadas")
    
    def test_06_parking_assignments(self):
        """Test 6: Verificar asignaciones de parkings"""
        print("\n🅿️  Test 6: Verificando asignaciones de parkings...")
        
        # Verificar que existen asignaciones
        result = self.session.execute(text("""
            SELECT COUNT(*) as total_assignments
            FROM user_parkings
        """))
        
        total_assignments = result.scalar()
        self.assertGreater(total_assignments, 0, "No existen asignaciones de parkings")
        print(f"✅ Total de asignaciones: {total_assignments}")
        
        # Verificar que los usuarios con rol 'user' tienen asignaciones
        result = self.session.execute(text("""
            SELECT COUNT(*) as users_without_assignments
            FROM users u
            WHERE u.role = 'user'
            AND u.is_active = true
            AND NOT EXISTS (
                SELECT 1 FROM user_parkings up 
                WHERE up.user_id = u.id
            )
        """))
        
        users_without_assignments = result.scalar()
        self.assertEqual(users_without_assignments, 0, "Existen usuarios sin asignaciones de parkings")
        print("✅ Todos los usuarios con rol 'user' tienen asignaciones")
    
    def test_07_data_consistency(self):
        """Test 7: Verificar consistencia de datos"""
        print("\n🔄 Test 7: Verificando consistencia de datos...")
        
        # Verificar que no hay asignaciones huérfanas
        result = self.session.execute(text("""
            SELECT COUNT(*) as orphaned_assignments
            FROM user_parkings up
            LEFT JOIN users u ON up.user_id = u.id
            WHERE u.id IS NULL
        """))
        
        orphaned_assignments = result.scalar()
        self.assertEqual(orphaned_assignments, 0, "Existen asignaciones huérfanas (sin usuario)")
        print("✅ No hay asignaciones huérfanas")
        
        # Verificar que no hay asignaciones a parkings inexistentes
        result = self.session.execute(text("""
            SELECT COUNT(*) as invalid_parking_assignments
            FROM user_parkings up
            LEFT JOIN parkings p ON up.parking_id = p.id
            WHERE p.id IS NULL
        """))
        
        invalid_parking_assignments = result.scalar()
        self.assertEqual(invalid_parking_assignments, 0, "Existen asignaciones a parkings inexistentes")
        print("✅ No hay asignaciones a parkings inexistentes")
    
    def test_08_performance_indexes(self):
        """Test 8: Verificar rendimiento de índices"""
        print("\n⚡ Test 8: Verificando rendimiento de índices...")
        
        # Verificar que las consultas por email usan el índice
        result = self.session.execute(text("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM users WHERE email = 'test@example.com'
        """))
        
        explain_plan = result.fetchall()
        plan_text = ' '.join([row[0] for row in explain_plan if row[0]])
        
        # Verificar que se usa el índice de email
        self.assertIn("idx_users_email", plan_text, "Consulta por email no usa el índice")
        print("✅ Índice de email funciona correctamente")
        
        # Verificar que las consultas por rol usan el índice
        result = self.session.execute(text("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM users WHERE role = 'user'
        """))
        
        explain_plan = result.fetchall()
        plan_text = ' '.join([row[0] for row in explain_plan if row[0]])
        
        # Verificar que se usa el índice de rol
        self.assertIn("idx_users_role", plan_text, "Consulta por rol no usa el índice")
        print("✅ Índice de rol funciona correctamente")
    
    def test_09_migration_scripts(self):
        """Test 9: Verificar scripts de migración"""
        print("\n📜 Test 9: Verificando scripts de migración...")
        
        # Verificar que los scripts existen
        script_files = [
            'migrate_to_v3_1_0.py',
            'rollback_migration_v3_1_0.py',
            'verify_migration_v3_1_0.py',
            'assign_parkings_to_users.py'
        ]
        
        for script_file in script_files:
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', script_file)
            self.assertTrue(os.path.exists(script_path), f"Script {script_file} no existe")
            print(f"✅ Script {script_file} existe")
        
        # Verificar que los scripts son ejecutables
        for script_file in script_files:
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', script_file)
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('#!/usr/bin/env python3', content, f"Script {script_file} no tiene shebang")
                self.assertIn('def ', content, f"Script {script_file} no tiene funciones definidas")
        
        print("✅ Todos los scripts son válidos")
    
    def test_10_rollback_simulation(self):
        """Test 10: Simular rollback (sin ejecutar)"""
        print("\n🔄 Test 10: Simulando rollback...")
        
        # Verificar que el script de rollback tiene las queries correctas
        rollback_script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'rollback_migration_v3_1_0.py')
        
        with open(rollback_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar queries de rollback
        rollback_queries = [
            'DROP INDEX IF EXISTS',
            'DROP COLUMN IF EXISTS',
            'DROP CONSTRAINT IF EXISTS',
            'DELETE FROM user_parkings',
            'DELETE FROM users'
        ]
        
        for query in rollback_queries:
            self.assertIn(query, content, f"Script de rollback no contiene: {query}")
        
        print("✅ Script de rollback contiene todas las queries necesarias")
    
    def test_11_verification_script(self):
        """Test 11: Verificar script de verificación"""
        print("\n🔍 Test 11: Verificando script de verificación...")
        
        # Verificar que el script de verificación tiene las funciones correctas
        verify_script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'verify_migration_v3_1_0.py')
        
        with open(verify_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar funciones requeridas
        required_functions = [
            'def verify_migration',
            'def test_user_properties',
            'def generate_verification_report'
        ]
        
        for func in required_functions:
            self.assertIn(func, content, f"Script de verificación no contiene: {func}")
        
        print("✅ Script de verificación contiene todas las funciones necesarias")
    
    def test_12_assignment_script(self):
        """Test 12: Verificar script de asignación"""
        print("\n🅿️  Test 12: Verificando script de asignación...")
        
        # Verificar que el script de asignación tiene las funciones correctas
        assign_script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'assign_parkings_to_users.py')
        
        with open(assign_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar funciones requeridas
        required_functions = [
            'def assign_parkings_to_users',
            'def verify_parking_assignments',
            'def generate_assignment_report'
        ]
        
        for func in required_functions:
            self.assertIn(func, content, f"Script de asignación no contiene: {func}")
        
        print("✅ Script de asignación contiene todas las funciones necesarias")

def run_complete_tests():
    """Ejecutar todos los tests completos"""
    print("🚀 Iniciando tests completos de migración v3.1.0...")
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMigrationComplete)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print(f"\n📊 Resumen de tests completos:")
    print(f"   - Tests ejecutados: {result.testsRun}")
    print(f"   - Tests exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - Tests fallidos: {len(result.failures)}")
    print(f"   - Tests con errores: {len(result.errors)}")
    
    # Mostrar detalles de fallos
    if result.failures:
        print("\n❌ Tests fallidos:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n❌ Tests con errores:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n🎉 ¡Todos los tests completos pasaron exitosamente!")
        print("✅ La migración v3.1.0 está completamente validada")
        return True
    else:
        print("\n❌ Algunos tests completos fallaron")
        print("⚠️  Revisar los errores antes de proceder con el despliegue")
        return False

if __name__ == "__main__":
    success = run_complete_tests()
    sys.exit(0 if success else 1) 