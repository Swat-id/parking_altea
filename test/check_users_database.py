#!/usr/bin/env python3
"""
Script para verificar usuarios en la base de datos de Parking Altea
"""

import psycopg2
import os
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'parking_altea',
    'user': 'parking',
    'password': 'parking123',
    'port': 5432
}

def check_users():
    """Verificar usuarios existentes en la base de datos"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔍 Verificando usuarios en la base de datos...")
        print("=" * 60)
        
        # Consultar usuarios
        cursor.execute("""
            SELECT id, email, name, role, is_active, created_at, last_login
            FROM users 
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ No se encontraron usuarios en la base de datos")
            return
        
        print(f"✅ Se encontraron {len(users)} usuarios:")
        print("-" * 60)
        
        for user in users:
            user_id, email, name, role, is_active, created_at, last_login = user
            
            status = "🟢 ACTIVO" if is_active else "🔴 INACTIVO"
            role_icon = "👑" if role == "superadmin" else "👤"
            
            print(f"{role_icon} ID: {user_id}")
            print(f"   📧 Email: {email}")
            print(f"   👤 Nombre: {name}")
            print(f"   🏷️  Rol: {role}")
            print(f"   📊 Estado: {status}")
            print(f"   📅 Creado: {created_at}")
            if last_login:
                print(f"   🕒 Último login: {last_login}")
            else:
                print(f"   🕒 Último login: Nunca")
            print("-" * 60)
        
        # Verificar usuario específico info@swat-id.com
        print("\n🔍 Verificando usuario específico info@swat-id.com...")
        cursor.execute("""
            SELECT id, email, name, role, is_active, created_at, last_login
            FROM users 
            WHERE email = 'info@swat-id.com'
        """)
        
        specific_user = cursor.fetchone()
        
        if specific_user:
            user_id, email, name, role, is_active, created_at, last_login = specific_user
            print(f"✅ Usuario encontrado:")
            print(f"   📧 Email: {email}")
            print(f"   👤 Nombre: {name}")
            print(f"   🏷️  Rol: {role}")
            print(f"   📊 Estado: {'🟢 ACTIVO' if is_active else '🔴 INACTIVO'}")
        else:
            print("❌ Usuario info@swat-id.com NO encontrado")
        
        # Verificar estructura de la tabla
        print("\n📋 Estructura de la tabla users:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            col_name, data_type, is_nullable, default = col
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"   {col_name}: {data_type} {nullable}{default_str}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error de base de datos: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def create_superadmin_user():
    """Crear usuario superadmin info@swat-id.com si no existe"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM users WHERE email = 'info@swat-id.com'")
        existing_user = cursor.fetchone()
        
        if existing_user:
            print("ℹ️  Usuario info@swat-id.com ya existe")
            return
        
        # Crear usuario superadmin
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('admin123!')
        
        cursor.execute("""
            INSERT INTO users (email, name, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('info@swat-id.com', 'Superadmin SWAT-ID', password_hash, 'superadmin', True, datetime.now()))
        
        conn.commit()
        print("✅ Usuario superadmin info@swat-id.com creado exitosamente")
        print("   📧 Email: info@swat-id.com")
        print("   🔑 Contraseña: admin123!")
        print("   🏷️  Rol: superadmin")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creando usuario: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--create":
        create_superadmin_user()
    else:
        check_users() 