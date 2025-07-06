#!/usr/bin/env python3
"""
Script de rollback de migración v3.1.0
Revierte los cambios de la migración si es necesario
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config

def rollback_migration():
    """Revertir la migración v3.1.0"""
    print("⚠️  ADVERTENCIA: Esto revertirá la migración v3.1.0")
    print("   - Se eliminarán los campos 'role' y 'updated_at' de la tabla users")
    print("   - Se eliminarán los índices creados")
    print("   - Se eliminarán las asignaciones de parkings")
    print("   - Se eliminarán los usuarios creados")
    
    confirm = input("\n¿Está seguro de que desea continuar? (escriba 'SI' para confirmar): ")
    if confirm != 'SI':
        print("❌ Rollback cancelado")
        return False
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\n🔄 Iniciando rollback...")
        
        # 1. Eliminar asignaciones de parkings de usuarios específicos
        print("🗑️  Eliminando asignaciones de parkings...")
        session.execute(text("""
            DELETE FROM user_parkings 
            WHERE user_id IN (
                SELECT id FROM users 
                WHERE email IN ('admin@parking-altea.es', 'atea.dti@altea.es', 'gerenciapstd@altea.es')
            )
        """))
        print("✅ Asignaciones de parkings eliminadas")
        
        # 2. Eliminar usuarios específicos creados en la migración
        print("🗑️  Eliminando usuarios creados en la migración...")
        session.execute(text("""
            DELETE FROM users 
            WHERE email IN ('admin@parking-altea.es', 'atea.dti@altea.es', 'gerenciapstd@altea.es')
        """))
        print("✅ Usuarios eliminados")
        
        # 3. Eliminar constraint de roles
        print("🔓 Eliminando constraint de roles...")
        try:
            session.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_user_role"))
            print("✅ Constraint de roles eliminado")
        except Exception as e:
            print(f"ℹ️  Constraint de roles no encontrado: {e}")
        
        # 4. Eliminar índices
        print("📊 Eliminando índices...")
        try:
            session.execute(text("DROP INDEX IF EXISTS idx_users_email"))
            print("✅ Índice de email eliminado")
        except Exception as e:
            print(f"ℹ️  Índice de email no encontrado: {e}")
        
        try:
            session.execute(text("DROP INDEX IF EXISTS idx_users_role"))
            print("✅ Índice de rol eliminado")
        except Exception as e:
            print(f"ℹ️  Índice de rol no encontrado: {e}")
        
        try:
            session.execute(text("DROP INDEX IF EXISTS idx_users_active_role"))
            print("✅ Índice compuesto eliminado")
        except Exception as e:
            print(f"ℹ️  Índice compuesto no encontrado: {e}")
        
        # 5. Eliminar campos de la tabla users
        print("📝 Eliminando campos de la tabla users...")
        try:
            session.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS updated_at"))
            print("✅ Campo 'updated_at' eliminado")
        except Exception as e:
            print(f"ℹ️  Campo 'updated_at' no encontrado: {e}")
        
        try:
            session.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS role"))
            print("✅ Campo 'role' eliminado")
        except Exception as e:
            print(f"ℹ️  Campo 'role' no encontrado: {e}")
        
        # Commit de todos los cambios
        session.commit()
        print("\n🎉 Rollback completado exitosamente!")
        
        # 6. Verificar estado después del rollback
        print("\n🔍 Verificando estado después del rollback...")
        
        # Verificar campos en tabla users
        result = session.execute(text("""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('role', 'updated_at')
        """))
        
        remaining_fields = result.fetchall()
        if len(remaining_fields) == 0:
            print("✅ Campos 'role' y 'updated_at' eliminados correctamente")
        else:
            print(f"⚠️  Campos restantes: {[f[0] for f in remaining_fields]}")
        
        # Verificar usuarios
        result = session.execute(text("""
            SELECT COUNT(*) as total_users
            FROM users
        """))
        
        total_users = result.scalar()
        print(f"✅ Total usuarios restantes: {total_users}")
        
        # Verificar asignaciones
        result = session.execute(text("""
            SELECT COUNT(*) as total_assignments
            FROM user_parkings
        """))
        
        total_assignments = result.scalar()
        print(f"✅ Total asignaciones restantes: {total_assignments}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error durante el rollback: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Iniciando rollback de migración v3.1.0...")
    
    success = rollback_migration()
    
    if success:
        print("\n✅ Rollback completado exitosamente")
        sys.exit(0)
    else:
        print("\n❌ Rollback falló")
        sys.exit(1) 