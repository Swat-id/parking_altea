#!/usr/bin/env python3
"""
Script para crear el usuario superadmin info@swat-id.com
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
from auth import hash_password

def create_superadmin():
    """Crear usuario superadmin info@swat-id.com"""
    print("🔧 Creando usuario superadmin...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Crear hash de la contraseña primero
        password_hash = hash_password('admin123!')
        
        # Verificar si el usuario ya existe
        result = session.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), 
                               {'email': 'info@swat-id.com'})
        existing_user = result.fetchone()
        
        if existing_user:
            print(f"ℹ️  Usuario ya existe: {existing_user}")
            print("🔄 Actualizando contraseña del usuario existente...")
            
            # Actualizar la contraseña del usuario existente
            session.execute(text("""
                UPDATE users 
                SET password_hash = :password_hash, updated_at = NOW()
                WHERE email = :email
            """), {
                'password_hash': password_hash,
                'email': 'info@swat-id.com'
            })
            
            session.commit()
            print("✅ Contraseña del usuario superadmin actualizada")
            print("   📧 Email: info@swat-id.com")
            print("   🔑 Nueva contraseña: admin123!")
            print("   🏷️  Rol: superadmin")
            
            # Verificar que se actualizó correctamente
            result = session.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), 
                                   {'email': 'info@swat-id.com'})
            updated_user = result.fetchone()
            print(f"   📋 Usuario actualizado: {updated_user}")
            return
        
        # Insertar usuario superadmin
        session.execute(text("""
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at)
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
        """), {
            'name': 'Superadmin SWAT-ID',
            'email': 'info@swat-id.com',
            'password_hash': password_hash,
            'role': 'superadmin'
        })
        
        session.commit()
        print("✅ Usuario superadmin creado exitosamente")
        print("   📧 Email: info@swat-id.com")
        print("   🔑 Contraseña: admin123!")
        print("   🏷️  Rol: superadmin")
        
        # Verificar que se creó correctamente
        result = session.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), 
                               {'email': 'info@swat-id.com'})
        new_user = result.fetchone()
        print(f"   📋 Usuario creado: {new_user}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creando usuario: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_superadmin() 