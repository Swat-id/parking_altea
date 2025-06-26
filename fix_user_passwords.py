#!/usr/bin/env python3
"""
Script para actualizar las contraseñas de los usuarios a altea2025!
"""

import sys
import os
sys.path.append('/opt/parking_altea/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
import bcrypt

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def update_user_passwords():
    """Actualizar contraseñas de usuarios a altea2025!"""
    try:
        # Conectar a la base de datos
        engine = create_engine('postgresql://parking_user:parking_pass@localhost/parking_db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=== ACTUALIZANDO CONTRASEÑAS DE USUARIOS ===")
        
        # Nueva contraseña
        new_password = "alte2025!"
        password_hash = hash_password(new_password)
        
        # Actualizar ambos usuarios
        users = session.query(User).filter(User.is_active == True).all()
        
        for user in users:
            print(f"Actualizando contraseña para: {user.name} ({user.email})")
            user.password_hash = password_hash
        
        session.commit()
        print(f"✅ Contraseñas actualizadas para {len(users)} usuarios")
        
        # Verificar que funciona
        print("\n=== VERIFICANDO CONTRASEÑAS ===")
        for user in users:
            is_valid = bcrypt.checkpw(new_password.encode('utf-8'), user.password_hash.encode('utf-8'))
            print(f"Usuario {user.name}: {'✅' if is_valid else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    update_user_passwords() 