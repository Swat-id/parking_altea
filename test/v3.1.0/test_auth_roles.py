#!/usr/bin/env python3
"""
Test de autenticación y registro con roles para v3.1.0
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from auth import create_user, authenticate_user
from models import User

class TestAuthRoles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(config.DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()
        # Limpiar usuarios de test
        cls.session.query(User).filter(User.email.like('test_roles_%')).delete()
        cls.session.commit()
    @classmethod
    def tearDownClass(cls):
        cls.session.query(User).filter(User.email.like('test_roles_%')).delete()
        cls.session.commit()
        cls.session.close()
    def test_register_and_login_user_role(self):
        email = 'test_roles_user@altea.es'
        password = 'test1234!'
        # Crear usuario con rol user
        result = create_user(self.session, 'Test User', email, password, 'user')
        self.assertTrue(result['success'])
        self.assertEqual(result['user']['role'], 'user')
        # Login
        auth = authenticate_user(self.session, email, password)
        self.assertTrue(auth['success'])
        self.assertEqual(auth['user']['role'], 'user')
        self.assertIn('token', auth)
    def test_register_and_login_superadmin_role(self):
        email = 'test_roles_admin@altea.es'
        password = 'test1234!'
        # Crear usuario con rol superadmin
        result = create_user(self.session, 'Test Admin', email, password, 'superadmin')
        self.assertTrue(result['success'])
        self.assertEqual(result['user']['role'], 'superadmin')
        # Login
        auth = authenticate_user(self.session, email, password)
        self.assertTrue(auth['success'])
        self.assertEqual(auth['user']['role'], 'superadmin')
        self.assertIn('token', auth)
    def test_register_invalid_role(self):
        email = 'test_roles_invalid@altea.es'
        password = 'test1234!'
        # Intentar crear usuario con rol inválido
        result = create_user(self.session, 'Test Invalid', email, password, 'invalidrole')
        self.assertFalse(result['success'])
        self.assertIn('Rol no permitido', result['error'])
if __name__ == '__main__':
    unittest.main() 