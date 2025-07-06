#!/usr/bin/env python3
"""
Test de Migración T1.1 y T1.2 - v3.1.0
Prueba las funcionalidades implementadas en las tareas T1.1 y T1.2
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import unittest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
from models import User

class TestMigrationT1_1_T1_2(unittest.TestCase):
    """Test suite para las tareas T1.1 y T1.2"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        print("🚀 Configurando tests de migración T1.1 y T1.2...")
        cls.engine = create_engine(config.DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza final"""
        cls.session.close()
        print("✅ Tests de migración T1.1 y T1.2 completados")
    
    def test_01_database_fields_exist(self):
        """Test T1.1: Verificar que los campos de la base de datos existen"""
        print("\n📝 Test 1: Verificando campos en tabla users...")
        
        # Verificar campo 'role'
        result = self.session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """))
        
        role_field = result.fetchone()
        self.assertIsNotNone(role_field, "Campo 'role' no existe en tabla users")
        self.assertEqual(role_field[0], 'role', "Nombre del campo incorrecto")
        self.assertEqual(role_field[1], 'character varying', "Tipo de dato incorrecto")
        self.assertEqual(role_field[2], 'NO', "Campo debe ser NOT NULL")
        print("✅ Campo 'role' verificado correctamente")
        
        # Verificar campo 'updated_at'
        result = self.session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """))
        
        updated_at_field = result.fetchone()
        self.assertIsNotNone(updated_at_field, "Campo 'updated_at' no existe en tabla users")
        self.assertEqual(updated_at_field[0], 'updated_at', "Nombre del campo incorrecto")
        self.assertEqual(updated_at_field[1], 'timestamp with time zone', "Tipo de dato incorrecto")
        print("✅ Campo 'updated_at' verificado correctamente")
    
    def test_02_constraint_exists(self):
        """Test T1.1: Verificar que el constraint de roles existe"""
        print("\n🔒 Test 2: Verificando constraint de roles...")
        
        result = self.session.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'chk_user_role'
        """))
        
        constraint = result.fetchone()
        self.assertIsNotNone(constraint, "Constraint 'chk_user_role' no existe")
        self.assertEqual(constraint[0], 'chk_user_role', "Nombre del constraint incorrecto")
        self.assertIn("superadmin", constraint[1], "Constraint no incluye 'superadmin'")
        self.assertIn("user", constraint[1], "Constraint no incluye 'user'")
        print("✅ Constraint de roles verificado correctamente")
    
    def test_03_indexes_exist(self):
        """Test T1.1: Verificar que los índices existen"""
        print("\n📊 Test 3: Verificando índices...")
        
        # Verificar índice de email
        result = self.session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users' AND indexname = 'idx_users_email'
        """))
        
        email_index = result.fetchone()
        self.assertIsNotNone(email_index, "Índice 'idx_users_email' no existe")
        print("✅ Índice de email verificado")
        
        # Verificar índice de rol
        result = self.session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users' AND indexname = 'idx_users_role'
        """))
        
        role_index = result.fetchone()
        self.assertIsNotNone(role_index, "Índice 'idx_users_role' no existe")
        print("✅ Índice de rol verificado")
        
        # Verificar índice compuesto
        result = self.session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users' AND indexname = 'idx_users_active_role'
        """))
        
        compound_index = result.fetchone()
        self.assertIsNotNone(compound_index, "Índice 'idx_users_active_role' no existe")
        print("✅ Índice compuesto verificado")
    
    def test_04_initial_users_exist(self):
        """Test T1.1: Verificar que los usuarios iniciales existen"""
        print("\n👥 Test 4: Verificando usuarios iniciales...")
        
        # Verificar usuario superadmin
        result = self.session.execute(text("""
            SELECT name, email, role, is_active
            FROM users
            WHERE email = 'admin@parking-altea.es'
        """))
        
        admin_user = result.fetchone()
        self.assertIsNotNone(admin_user, "Usuario superadmin no existe")
        self.assertEqual(admin_user[0], 'Administrador del Sistema', "Nombre incorrecto")
        self.assertEqual(admin_user[1], 'admin@parking-altea.es', "Email incorrecto")
        self.assertEqual(admin_user[2], 'superadmin', "Rol incorrecto")
        self.assertTrue(admin_user[3], "Usuario debe estar activo")
        print("✅ Usuario superadmin verificado")
        
        # Verificar usuario Toni Alos
        result = self.session.execute(text("""
            SELECT name, email, role, is_active
            FROM users
            WHERE email = 'atea.dti@altea.es'
        """))
        
        toni_user = result.fetchone()
        self.assertIsNotNone(toni_user, "Usuario Toni Alos no existe")
        self.assertEqual(toni_user[0], 'Toni Alos', "Nombre incorrecto")
        self.assertEqual(toni_user[1], 'atea.dti@altea.es', "Email incorrecto")
        self.assertEqual(toni_user[2], 'user', "Rol incorrecto")
        self.assertTrue(toni_user[3], "Usuario debe estar activo")
        print("✅ Usuario Toni Alos verificado")
        
        # Verificar usuario Iván Martí
        result = self.session.execute(text("""
            SELECT name, email, role, is_active
            FROM users
            WHERE email = 'gerenciapstd@altea.es'
        """))
        
        ivan_user = result.fetchone()
        self.assertIsNotNone(ivan_user, "Usuario Iván Martí no existe")
        self.assertEqual(ivan_user[0], 'Iván Martí', "Nombre incorrecto")
        self.assertEqual(ivan_user[1], 'gerenciapstd@altea.es', "Email incorrecto")
        self.assertEqual(ivan_user[2], 'user', "Rol incorrecto")
        self.assertTrue(ivan_user[3], "Usuario debe estar activo")
        print("✅ Usuario Iván Martí verificado")
    
    def test_05_parking_assignments_exist(self):
        """Test T1.1: Verificar que las asignaciones de parkings existen"""
        print("\n🅿️  Test 5: Verificando asignaciones de parkings...")
        
        # Verificar que el superadmin tiene todos los parkings
        result = self.session.execute(text("""
            SELECT COUNT(up.parking_id) as parkings_assigned
            FROM users u
            JOIN user_parkings up ON u.id = up.user_id
            WHERE u.email = 'admin@parking-altea.es'
        """))
        
        admin_parkings = result.scalar()
        total_parkings = self.session.execute(text("SELECT COUNT(*) FROM parkings")).scalar()
        self.assertEqual(admin_parkings, total_parkings, "Superadmin no tiene todos los parkings")
        print(f"✅ Superadmin tiene {admin_parkings} parkings asignados")
        
        # Verificar que Toni Alos tiene parkings específicos
        result = self.session.execute(text("""
            SELECT COUNT(up.parking_id) as parkings_assigned
            FROM users u
            JOIN user_parkings up ON u.id = up.user_id
            JOIN parkings p ON up.parking_id = p.id
            WHERE u.email = 'atea.dti@altea.es'
            AND p.name IN ('P. Ciutat Esportiva', 'P. Port Altea', 'P. Estació Altea')
        """))
        
        toni_parkings = result.scalar()
        self.assertGreater(toni_parkings, 0, "Toni Alos no tiene parkings asignados")
        print(f"✅ Toni Alos tiene {toni_parkings} parkings asignados")
        
        # Verificar que Iván Martí tiene parkings específicos
        result = self.session.execute(text("""
            SELECT COUNT(up.parking_id) as parkings_assigned
            FROM users u
            JOIN user_parkings up ON u.id = up.user_id
            JOIN parkings p ON up.parking_id = p.id
            WHERE u.email = 'gerenciapstd@altea.es'
            AND p.name IN ('P. Altea Hills', 'P. Poble antic/Belles Arts 1', 'P. Poble antic/Belles Arts 2')
        """))
        
        ivan_parkings = result.scalar()
        self.assertGreater(ivan_parkings, 0, "Iván Martí no tiene parkings asignados")
        print(f"✅ Iván Martí tiene {ivan_parkings} parkings asignados")
    
    def test_06_model_properties(self):
        """Test T1.2: Verificar propiedades del modelo User"""
        print("\n🧪 Test 6: Verificando propiedades del modelo User...")
        
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
        print("✅ Propiedades de superadmin verificadas")
        
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
        print("✅ Propiedades de usuario regular verificadas")
        
        # Verificar representación
        self.assertIn("superadmin", str(superadmin), "Representación debe incluir rol")
        self.assertIn("test@admin.com", str(superadmin), "Representación debe incluir email")
        print("✅ Representación del modelo verificada")
    
    def test_07_data_integrity(self):
        """Test T1.1: Verificar integridad de datos"""
        print("\n🔍 Test 7: Verificando integridad de datos...")
        
        # Verificar que no hay usuarios sin rol
        result = self.session.execute(text("""
            SELECT COUNT(*) as users_without_role
            FROM users
            WHERE role IS NULL OR role = ''
        """))
        
        users_without_role = result.scalar()
        self.assertEqual(users_without_role, 0, "No debe haber usuarios sin rol")
        print("✅ Todos los usuarios tienen rol asignado")
        
        # Verificar que no hay roles inválidos
        result = self.session.execute(text("""
            SELECT COUNT(*) as invalid_roles
            FROM users
            WHERE role NOT IN ('superadmin', 'user')
        """))
        
        invalid_roles = result.scalar()
        self.assertEqual(invalid_roles, 0, "No debe haber roles inválidos")
        print("✅ Todos los roles son válidos")
        
        # Verificar que todos los usuarios tienen updated_at
        result = self.session.execute(text("""
            SELECT COUNT(*) as users_without_updated_at
            FROM users
            WHERE updated_at IS NULL
        """))
        
        users_without_updated_at = result.scalar()
        self.assertEqual(users_without_updated_at, 0, "Todos los usuarios deben tener updated_at")
        print("✅ Todos los usuarios tienen updated_at")

def run_tests():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests de migración T1.1 y T1.2...")
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMigrationT1_1_T1_2)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print(f"\n📊 Resumen de tests:")
    print(f"   - Tests ejecutados: {result.testsRun}")
    print(f"   - Tests exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - Tests fallidos: {len(result.failures)}")
    print(f"   - Tests con errores: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        return True
    else:
        print("❌ Algunos tests fallaron")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 