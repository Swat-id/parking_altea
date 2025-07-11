#!/usr/bin/env python3
"""
Script de migración a v3.1.0 - Parking Altea
Corregido para manejar transacciones fallidas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt
import config

def hash_password(password: str) -> str:
    """Generar hash de contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def execute_safe(session, sql, params=None):
    """Ejecutar SQL de forma segura con manejo de errores"""
    try:
        if params:
            result = session.execute(text(sql), params)
        else:
            result = session.execute(text(sql))
        session.commit()
        return result
    except Exception as e:
        session.rollback()
        if "already exists" in str(e).lower():
            print(f"ℹ️  Ya existe: {sql}")
            return None
        else:
            print(f"❌ Error ejecutando: {sql}")
            print(f"   Error: {e}")
            raise e

def migrate_database():
    """Migrar la base de datos a v3.1.0"""
    print("🚀 Iniciando migración a v3.1.0...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Agregar campos a la tabla users
        print("📝 Agregando campos a la tabla users...")
        
        # Campo role
        execute_safe(session, """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'
        """)
        
        # Campo updated_at
        execute_safe(session, """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
        """)
        
        # 2. Agregar constraint de validación de roles
        print("🔒 Agregando constraint de validación de roles...")
        execute_safe(session, """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.check_constraints 
                    WHERE constraint_name = 'check_user_role'
                ) THEN
                    ALTER TABLE users ADD CONSTRAINT check_user_role 
                    CHECK (role IN ('superadmin', 'admin', 'user'));
                END IF;
            END $$;
        """)
        
        # 3. Crear índices para optimización
        print("📊 Creando índices para optimización...")
        
        # Índice para email
        execute_safe(session, "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        # Índice para rol
        execute_safe(session, "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        
        # Índice compuesto
        execute_safe(session, "CREATE INDEX IF NOT EXISTS idx_users_active_role ON users(is_active, role)")
        
        # 4. Crear usuarios iniciales
        print("👥 Creando usuarios iniciales...")
        
        # Usuario superadmin
        admin_password_hash = hash_password('admin123!')
        execute_safe(session, """
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) 
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = TRUE,
                updated_at = NOW()
        """, {
            'name': 'Administrador del Sistema',
            'email': 'admin@parking-altea.es',
            'password_hash': admin_password_hash,
            'role': 'superadmin'
        })
        
        # Usuario Toni Alos
        user_password_hash = hash_password('altea2025!')
        execute_safe(session, """
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) 
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = TRUE,
                updated_at = NOW()
        """, {
            'name': 'Toni Alos',
            'email': 'atea.dti@altea.es',
            'password_hash': user_password_hash,
            'role': 'user'
        })
        
        # Usuario Iván Martí
        execute_safe(session, """
            INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) 
            VALUES (:name, :email, :password_hash, :role, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = TRUE,
                updated_at = NOW()
        """, {
            'name': 'Iván Martí',
            'email': 'gerenciapstd@altea.es',
            'password_hash': user_password_hash,
            'role': 'user'
        })
        
        # 5. Asignar parkings a usuarios
        print("🅿️  Asignando parkings a usuarios...")
        
        # Obtener IDs de usuarios
        admin_id = session.execute(text("SELECT id FROM users WHERE email = 'admin@parking-altea.es'")).scalar()
        toni_id = session.execute(text("SELECT id FROM users WHERE email = 'atea.dti@altea.es'")).scalar()
        ivan_id = session.execute(text("SELECT id FROM users WHERE email = 'gerenciapstd@altea.es'")).scalar()
        
        # Asignar todos los parkings al superadmin
        execute_safe(session, """
            INSERT INTO user_parkings (user_id, parking_id, created_at)
            SELECT :admin_id, id, NOW()
            FROM parkings
            WHERE NOT EXISTS (
                SELECT 1 FROM user_parkings 
                WHERE user_id = :admin_id AND parking_id = parkings.id
            )
        """, {'admin_id': admin_id})
        
        # Asignar parkings específicos a Toni Alos
        execute_safe(session, """
            INSERT INTO user_parkings (user_id, parking_id, created_at)
            SELECT :toni_id, id, NOW()
            FROM parkings 
            WHERE name IN ('P. Ciutat Esportiva', 'P. Port Altea', 'P. Estació Altea')
            AND NOT EXISTS (
                SELECT 1 FROM user_parkings 
                WHERE user_id = :toni_id AND parking_id = parkings.id
            )
        """, {'toni_id': toni_id})
        
        # Asignar parkings específicos a Iván Martí
        execute_safe(session, """
            INSERT INTO user_parkings (user_id, parking_id, created_at)
            SELECT :ivan_id, id, NOW()
            FROM parkings 
            WHERE name IN ('P. Altea Hills', 'P. Poble antic/Belles Arts 1', 'P. Poble antic/Belles Arts 2')
            AND NOT EXISTS (
                SELECT 1 FROM user_parkings 
                WHERE user_id = :ivan_id AND parking_id = parkings.id
            )
        """, {'ivan_id': ivan_id})
        
        # 6. Actualizar usuarios existentes sin rol
        print("🔄 Actualizando usuarios existentes sin rol...")
        execute_safe(session, """
            UPDATE users 
            SET role = 'user', updated_at = NOW()
            WHERE role IS NULL OR role = ''
        """)
        
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
            WHERE constraint_name = 'check_user_role'
        """))
        
        constraints = result.fetchall()
        if constraints:
            print("✅ Constraint de roles encontrado")
        else:
            print("⚠️  Constraint de roles no encontrado")
        
        # Verificar índices
        result = session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users' 
            AND indexname IN ('idx_users_email', 'idx_users_role', 'idx_users_active_role')
        """))
        
        indexes = result.fetchall()
        print(f"✅ Índices encontrados: {len(indexes)}")
        
        # Verificar usuarios
        result = session.execute(text("SELECT email, role, is_active FROM users ORDER BY email"))
        users = result.fetchall()
        print(f"✅ Usuarios encontrados: {len(users)}")
        for user in users:
            print(f"   - {user[0]}: {user[1]} (activo: {user[2]})")
        
        # Verificar asignaciones
        result = session.execute(text("""
            SELECT u.email, COUNT(up.parking_id) as parking_count
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            GROUP BY u.id, u.email
            ORDER BY u.email
        """))
        
        assignments = result.fetchall()
        print("✅ Asignaciones de parkings:")
        for assignment in assignments:
            print(f"   - {assignment[0]}: {assignment[1]} parkings")
        
        print("✅ Verificación completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    try:
        migrate_database()
        verify_migration()
        print("\n🎉 ¡Migración y verificación completadas exitosamente!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 