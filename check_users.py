#!/usr/bin/env python3
"""
Script temporal para verificar usuarios en la base de datos
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DB_URL
from src.models import User
from src.auth import hash_password, verify_password

def check_users():
    """Verificar usuarios en la base de datos"""
    try:
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=== USUARIOS EN LA BASE DE DATOS ===")
        users = session.query(User).all()
        
        if not users:
            print("❌ No hay usuarios en la base de datos")
            return
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Name: {user.name}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print(f"Created: {user.created_at}")
            print(f"Updated: {user.updated_at}")
            print("-" * 50)
        
        # Probar credenciales del superadmin
        print("\n=== PRUEBA DE CREDENCIALES ===")
        admin_user = session.query(User).filter(User.email == 'admin@parking-altea.es').first()
        
        if admin_user:
            print(f"✅ Usuario admin encontrado: {admin_user.name}")
            print(f"Role: {admin_user.role}")
            print(f"Active: {admin_user.is_active}")
            
            # Probar contraseña
            test_password = 'admin123!'
            if verify_password(test_password, admin_user.password_hash):
                print(f"✅ Contraseña '{test_password}' es correcta")
            else:
                print(f"❌ Contraseña '{test_password}' es incorrecta")
                
                # Mostrar hash actual
                print(f"Hash actual: {admin_user.password_hash}")
                
                # Generar nuevo hash
                new_hash = hash_password(test_password)
                print(f"Nuevo hash: {new_hash}")
        else:
            print("❌ Usuario admin@parking-altea.es no encontrado")
        
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_users() 