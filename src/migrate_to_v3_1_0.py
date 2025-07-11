#!/usr/bin/env python3
"""
Script de migración de v3.0.0 a v3.1.0
Actualiza la base de datos para el sistema de login con roles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
import bcrypt
from datetime import datetime

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def migrate_database():
    """Ejecutar migración completa de la base de datos"""
    print("🚀 Iniciando migración a v3.1.0...")
    
    # Conectar a la base de datos
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Agregar campos a la tabla users
        print("📝 Agregando campos a la tabla users...")
        
        # Verificar si el campo role ya existe
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """))
        
        if not result.fetchone():
            session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
            print("✅ Campo 'role' agregado")
        else:
            print("ℹ️  Campo 'role' ya existe")
        
        # Verificar si el campo updated_at ya existe
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """))
        
        if not result.fetchone():
            session.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))
            print("✅ Campo 'updated_at' agregado")
        else:
            print("ℹ️  Campo 'updated_at' ya existe")
        
        # 2. Agregar constraint de validación de roles
        print("🔒 Agregando constraint de validación de roles...")
        try:
            session.execute(text("""
                ALTER TABLE users ADD CONSTRAINT chk_user_role 
                CHECK (role IN ('superadmin', 'user'))
            """))
            print("✅ Constraint de roles agregado")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Constraint de roles ya existe")
            else:
                raise e
        
        # 3. Crear índices para optimización
        print("📊 Creando índices para optimización...")
        
        # Índice para email
        try:
            session.execute(text("CREATE INDEX idx_users_email ON users(email)"))
            print("✅ Índice de email creado")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Índice de email ya existe")
            else:
                raise e
        
        # Índice para rol
        try:
            session.execute(text("CREATE INDEX idx_users_role ON users(role)"))
            print("✅ Índice de rol creado")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Índice de rol ya existe")
            else:
                raise e
        
        # Índice compuesto
        try:
            session.execute(text("CREATE INDEX idx_users_active_role ON users(is_active, role)"))
            print("✅ Índice compuesto creado")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Índice compuesto ya existe")
            else:
                raise e
        
        # 4. Crear usuarios iniciales
        print("👥 Creando usuarios iniciales...")
        
        # Usuario superadmin
        admin_password_hash = hash_password('admin123!')
        session.execute(text("""
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) 
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = TRUE,
                updated_at = NOW()
        """), {
            'name': 'Administrador del Sistema',
            'email': 'admin@parking-altea.es',
            'password_hash': admin_password_hash,
            'role': 'superadmin'
        })
        print("✅ Usuario superadmin creado/actualizado")
        
        # Usuario Toni Alos
        user_password_hash = hash_password('altea2025!')
        session.execute(text("""
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) 
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = TRUE,
                updated_at = NOW()
        """), {
            'name': 'Toni Alos',
            'email': 'atea.dti@altea.es',
            'password_hash': user_password_hash,
            'role': 'user'
        })
        print("✅ Usuario Toni Alos creado/actualizado")
        
        # Usuario Iván Martí
        session.execute(text("""
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) 
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = TRUE,
                updated_at = NOW()
        """), {
            'name': 'Iván Martí',
            'email': 'gerenciapstd@altea.es',
            'password_hash': user_password_hash,
            'role': 'user'
        })
        print("✅ Usuario Iván Martí creado/actualizado")
        
        # 5. Asignar parkings a usuarios
        print("🅿️  Asignando parkings a usuarios...")
        
        # Obtener IDs de usuarios
        admin_id = session.execute(text("SELECT id FROM users WHERE email = 'admin@parking-altea.es'")).scalar()
        toni_id = session.execute(text("SELECT id FROM users WHERE email = 'atea.dti@altea.es'")).scalar()
        ivan_id = session.execute(text("SELECT id FROM users WHERE email = 'gerenciapstd@altea.es'")).scalar()
        
        # Asignar todos los parkings al superadmin
        session.execute(text("""
            INSERT INTO user_parkings (user_id, parking_id, created_at)
            SELECT :admin_id, id, NOW()
            FROM parkings
            ON CONFLICT (user_id, parking_id) DO NOTHING
        """), {'admin_id': admin_id})
        print("✅ Todos los parkings asignados al superadmin")
        
        # Asignar parkings específicos a Toni Alos
        session.execute(text("""
            INSERT INTO user_parkings (user_id, parking_id, created_at)
            SELECT :toni_id, id, NOW()
            FROM parkings 
            WHERE name IN ('P. Ciutat Esportiva', 'P. Port Altea', 'P. Estació Altea')
            ON CONFLICT (user_id, parking_id) DO NOTHING
        """), {'toni_id': toni_id})
        print("✅ Parkings específicos asignados a Toni Alos")
        
        # Asignar parkings específicos a Iván Martí
        session.execute(text("""
            INSERT INTO user_parkings (user_id, parking_id, created_at)
            SELECT :ivan_id, id, NOW()
            FROM parkings 
            WHERE name IN ('P. Altea Hills', 'P. Poble antic/Belles Arts 1', 'P. Poble antic/Belles Arts 2')
            ON CONFLICT (user_id, parking_id) DO NOTHING
        """), {'ivan_id': ivan_id})
        print("✅ Parkings específicos asignados a Iván Martí")
        
        # 6. Actualizar usuarios existentes sin rol
        print("🔄 Actualizando usuarios existentes sin rol...")
        session.execute(text("""
            UPDATE users 
            SET role = 'user', updated_at = NOW()
            WHERE role IS NULL OR role = ''
        """))
        updated_count = session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'user'")).scalar()
        print(f"✅ {updated_count} usuarios actualizados con rol 'user'")
        
        # Commit de todos los cambios
        session.commit()
        print("🎉 Migración completada exitosamente!")
        
        # 7. Mostrar resumen
        print("\n📊 Resumen de la migración:")
        total_users = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        superadmin_count = session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")).scalar()
        user_count = session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'user'")).scalar()
        total_parkings = session.execute(text("SELECT COUNT(*) FROM parkings")).scalar()
        total_assignments = session.execute(text("SELECT COUNT(*) FROM user_parkings")).scalar()
        
        print(f"   - Total usuarios: {total_users}")
        print(f"   - Superadmins: {superadmin_count}")
        print(f"   - Usuarios regulares: {user_count}")
        print(f"   - Total parkings: {total_parkings}")
        print(f"   - Total asignaciones: {total_assignments}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la migración: {e}")
        raise
    finally:
        session.close()

def verify_migration():
    """Verificar que la migración se aplicó correctamente"""
    print("\n🔍 Verificando migración...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar campos en tabla users
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('role', 'updated_at')
            ORDER BY column_name
        """))
        
        fields = result.fetchall()
        print("✅ Campos en tabla users:")
        for field in fields:
            print(f"   - {field[0]}: {field[1]} (nullable: {field[2]}, default: {field[3]})")
        
        # Verificar constraint
        result = session.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'chk_user_role'
        """))
        
        constraint = result.fetchone()
        if constraint:
            print(f"✅ Constraint de roles: {constraint[0]}")
        else:
            print("⚠️  Constraint de roles no encontrado")
        
        # Verificar índices
        result = session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users' 
            AND indexname IN ('idx_users_email', 'idx_users_role', 'idx_users_active_role')
            ORDER BY indexname
        """))
        
        indexes = result.fetchall()
        print("✅ Índices creados:")
        for index in indexes:
            print(f"   - {index[0]}")
        
        # Verificar usuarios
        result = session.execute(text("""
            SELECT name, email, role, is_active
            FROM users
            ORDER BY role DESC, name
        """))
        
        users = result.fetchall()
        print("✅ Usuarios en el sistema:")
        for user in users:
            print(f"   - {user[0]} ({user[1]}) - Rol: {user[2]} - Activo: {user[3]}")
        
        # Verificar asignaciones
        result = session.execute(text("""
            SELECT u.name, u.role, COUNT(up.parking_id) as parkings_assigned
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            GROUP BY u.id, u.name, u.role
            ORDER BY u.role DESC, u.name
        """))
        
        assignments = result.fetchall()
        print("✅ Asignaciones de parkings:")
        for assignment in assignments:
            print(f"   - {assignment[0]} ({assignment[1]}): {assignment[2]} parkings")
        
        print("\n🎉 Verificación completada!")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migración de base de datos a v3.1.0')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar migración')
    parser.add_argument('--migrate-only', action='store_true', help='Solo ejecutar migración')
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_migration()
    elif args.migrate_only:
        migrate_database()
    else:
        # Ejecutar migración y luego verificar
        migrate_database()
        verify_migration() 