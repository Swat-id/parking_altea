#!/usr/bin/env python3
"""
Script para probar login directamente en el servidor
"""

import sys
import os
sys.path.append('/opt/parking_altea/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
import bcrypt

def test_login_direct():
    """Probar login directamente con la base de datos"""
    try:
        # Conectar a la base de datos
        engine = create_engine('postgresql://parking_user:parking_pass@localhost/parking_db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=== PRUEBA DIRECTA DE LOGIN ===")
        
        # Buscar usuario
        email = "atea.dti@altea.es"
        user = session.query(User).filter(User.email == email, User.is_active == True).first()
        
        if not user:
            print(f"❌ Usuario no encontrado: {email}")
            return False
        
        print(f"✅ Usuario encontrado: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Password hash: {user.password_hash[:50]}...")
        
        # Probar contraseña
        password = "toni123!"
        print(f"\nProbando contraseña: {password}")
        
        try:
            # Verificar contraseña
            is_valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
            print(f"✅ Verificación bcrypt: {is_valid}")
            
            if is_valid:
                print("🎉 Login exitoso!")
                return True
            else:
                print("❌ Contraseña incorrecta")
                return False
                
        except Exception as e:
            print(f"❌ Error en verificación bcrypt: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if 'session' in locals():
            session.close()

def test_bcrypt_import():
    """Probar importación de bcrypt"""
    try:
        import bcrypt
        print("✅ bcrypt importado correctamente")
        print(f"   Versión: {bcrypt.__version__}")
        return True
    except Exception as e:
        print(f"❌ Error importando bcrypt: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando bcrypt...")
    test_bcrypt_import()
    
    print("\n🔍 Probando login directo...")
    test_login_direct() 