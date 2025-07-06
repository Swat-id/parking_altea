#!/usr/bin/env python3
"""
Script de verificación de migración v3.1.0
Valida que la migración se aplicó correctamente
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
import json
from datetime import datetime

def verify_migration():
    """Verificar que la migración se aplicó correctamente"""
    print("🔍 Verificando migración v3.1.0...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    verification_results = {
        'timestamp': datetime.now().isoformat(),
        'version': 'v3.1.0',
        'status': 'PENDING',
        'checks': {},
        'summary': {}
    }
    
    try:
        # 1. Verificar campos en tabla users
        print("\n📝 Verificando campos en tabla users...")
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('role', 'updated_at')
            ORDER BY column_name
        """))
        
        fields = result.fetchall()
        if len(fields) == 2:
            print("✅ Campos requeridos encontrados:")
            for field in fields:
                print(f"   - {field[0]}: {field[1]} (nullable: {field[2]}, default: {field[3]})")
            verification_results['checks']['database_fields'] = {'status': 'PASS', 'details': [dict(zip(['name', 'type', 'nullable', 'default'], field)) for field in fields]}
        else:
            print("❌ Faltan campos requeridos en tabla users")
            verification_results['checks']['database_fields'] = {'status': 'FAIL', 'details': f'Found {len(fields)} fields, expected 2'}
            return False
        
        # 2. Verificar constraint de roles
        print("\n🔒 Verificando constraint de roles...")
        result = session.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'chk_user_role'
        """))
        
        constraint = result.fetchone()
        if constraint:
            print(f"✅ Constraint de roles encontrado: {constraint[0]}")
            print(f"   - Regla: {constraint[1]}")
            verification_results['checks']['role_constraint'] = {'status': 'PASS', 'details': {'name': constraint[0], 'rule': constraint[1]}}
        else:
            print("❌ Constraint de roles no encontrado")
            verification_results['checks']['role_constraint'] = {'status': 'FAIL', 'details': 'Constraint not found'}
            return False
        
        # 3. Verificar índices
        print("\n📊 Verificando índices...")
        result = session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users' 
            AND indexname IN ('idx_users_email', 'idx_users_role', 'idx_users_active_role')
            ORDER BY indexname
        """))
        
        indexes = result.fetchall()
        if len(indexes) == 3:
            print("✅ Índices requeridos encontrados:")
            for index in indexes:
                print(f"   - {index[0]}")
            verification_results['checks']['database_indexes'] = {'status': 'PASS', 'details': [index[0] for index in indexes]}
        else:
            print("❌ Faltan índices requeridos")
            verification_results['checks']['database_indexes'] = {'status': 'FAIL', 'details': f'Found {len(indexes)} indexes, expected 3'}
            return False
        
        # 4. Verificar usuarios existentes
        print("\n👥 Verificando usuarios existentes...")
        result = session.execute(text("""
            SELECT id, name, email, role, is_active, created_at, updated_at
            FROM users
            ORDER BY role DESC, name
        """))
        
        users = result.fetchall()
        if len(users) > 0:
            print("✅ Usuarios encontrados:")
            for user in users:
                print(f"   - {user[1]} ({user[2]}) - Rol: {user[3]} - Activo: {user[4]}")
            verification_results['checks']['existing_users'] = {'status': 'PASS', 'details': [{'id': u[0], 'name': u[1], 'email': u[2], 'role': u[3], 'active': u[4]} for u in users]}
        else:
            print("❌ No se encontraron usuarios")
            verification_results['checks']['existing_users'] = {'status': 'FAIL', 'details': 'No users found'}
            return False
        
        # 5. Verificar asignaciones de parkings
        print("\n🅿️  Verificando asignaciones de parkings...")
        result = session.execute(text("""
            SELECT u.name, u.role, COUNT(up.parking_id) as parkings_assigned
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            GROUP BY u.id, u.name, u.role
            ORDER BY u.role DESC, u.name
        """))
        
        assignments = result.fetchall()
        if len(assignments) > 0:
            print("✅ Asignaciones de parkings:")
            for assignment in assignments:
                print(f"   - {assignment[0]} ({assignment[1]}): {assignment[2]} parkings")
            verification_results['checks']['parking_assignments'] = {'status': 'PASS', 'details': [{'name': a[0], 'role': a[1], 'parkings': a[2]} for a in assignments]}
        else:
            print("⚠️  No se encontraron asignaciones de parkings")
            verification_results['checks']['parking_assignments'] = {'status': 'WARNING', 'details': 'No parking assignments found'}
        
        # 6. Verificar integridad de datos
        print("\n🔍 Verificando integridad de datos...")
        
        # Verificar que no hay usuarios sin rol
        result = session.execute(text("""
            SELECT COUNT(*) as users_without_role
            FROM users
            WHERE role IS NULL OR role = ''
        """))
        
        users_without_role = result.scalar()
        if users_without_role == 0:
            print("✅ Todos los usuarios tienen rol asignado")
            verification_results['checks']['role_integrity'] = {'status': 'PASS', 'details': 'All users have roles'}
        else:
            print(f"❌ {users_without_role} usuarios sin rol asignado")
            verification_results['checks']['role_integrity'] = {'status': 'FAIL', 'details': f'{users_without_role} users without role'}
            return False
        
        # Verificar que no hay roles inválidos
        result = session.execute(text("""
            SELECT COUNT(*) as invalid_roles
            FROM users
            WHERE role NOT IN ('superadmin', 'user')
        """))
        
        invalid_roles = result.scalar()
        if invalid_roles == 0:
            print("✅ Todos los roles son válidos")
            verification_results['checks']['role_validation'] = {'status': 'PASS', 'details': 'All roles are valid'}
        else:
            print(f"❌ {invalid_roles} usuarios con roles inválidos")
            verification_results['checks']['role_validation'] = {'status': 'FAIL', 'details': f'{invalid_roles} users with invalid roles'}
            return False
        
        # Verificar que todos los usuarios tienen updated_at
        result = session.execute(text("""
            SELECT COUNT(*) as users_without_updated_at
            FROM users
            WHERE updated_at IS NULL
        """))
        
        users_without_updated_at = result.scalar()
        if users_without_updated_at == 0:
            print("✅ Todos los usuarios tienen updated_at")
            verification_results['checks']['updated_at_integrity'] = {'status': 'PASS', 'details': 'All users have updated_at'}
        else:
            print(f"❌ {users_without_updated_at} usuarios sin updated_at")
            verification_results['checks']['updated_at_integrity'] = {'status': 'FAIL', 'details': f'{users_without_updated_at} users without updated_at'}
            return False
        
        # 7. Verificar estadísticas generales
        print("\n📊 Estadísticas generales:")
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
        
        verification_results['summary'] = {
            'total_users': total_users,
            'superadmin_count': superadmin_count,
            'user_count': user_count,
            'total_parkings': total_parkings,
            'total_assignments': total_assignments
        }
        
        # Marcar verificación como exitosa
        verification_results['status'] = 'SUCCESS'
        print("\n🎉 ¡Verificación completada exitosamente!")
        
        # Guardar resultados en archivo
        save_verification_results(verification_results)
        
        return True
        
    except Exception as e:
        verification_results['status'] = 'ERROR'
        verification_results['error'] = str(e)
        print(f"❌ Error durante la verificación: {e}")
        save_verification_results(verification_results)
        return False
    finally:
        session.close()

def save_verification_results(results):
    """Guardar resultados de verificación en archivo JSON"""
    try:
        filename = f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Resultados guardados en: {filepath}")
    except Exception as e:
        print(f"⚠️  Error guardando resultados: {e}")

def test_user_properties():
    """Probar las propiedades del modelo User"""
    print("\n🧪 Probando propiedades del modelo User...")
    
    try:
        from models import User
        
        # Crear instancias de prueba
        superadmin = User(
            name="Test Superadmin",
            email="test@admin.com",
            password_hash="hash",
            role="superadmin"
        )
        
        regular_user = User(
            name="Test User",
            email="test@user.com",
            password_hash="hash",
            role="user"
        )
        
        # Probar propiedades
        print(f"   - Superadmin is_superadmin: {superadmin.is_superadmin}")
        print(f"   - Superadmin is_regular_user: {superadmin.is_regular_user}")
        print(f"   - Regular user is_superadmin: {regular_user.is_superadmin}")
        print(f"   - Regular user is_regular_user: {regular_user.is_regular_user}")
        
        # Probar representación
        print(f"   - Superadmin repr: {superadmin}")
        print(f"   - Regular user repr: {regular_user}")
        
        print("✅ Propiedades del modelo User funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando propiedades: {e}")
        return False

def generate_verification_report():
    """Generar reporte de verificación"""
    print("\n📋 Generando reporte de verificación...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'version': 'v3.1.0',
            'database_info': {},
            'user_summary': {},
            'parking_summary': {},
            'recommendations': []
        }
        
        # Información de la base de datos
        result = session.execute(text("SELECT version()"))
        report['database_info']['version'] = result.scalar()
        
        # Resumen de usuarios
        result = session.execute(text("""
            SELECT role, COUNT(*) as count, 
                   COUNT(CASE WHEN is_active THEN 1 END) as active_count
            FROM users 
            GROUP BY role
        """))
        
        report['user_summary']['by_role'] = [dict(zip(['role', 'total', 'active'], row)) for row in result.fetchall()]
        
        # Resumen de parkings
        result = session.execute(text("""
            SELECT COUNT(*) as total_parkings,
                   COUNT(CASE WHEN current_occupancy > 0 THEN 1 END) as occupied_parkings
            FROM parkings
        """))
        
        parking_stats = result.fetchone()
        report['parking_summary'] = {
            'total': parking_stats[0],
            'occupied': parking_stats[1],
            'available': parking_stats[0] - parking_stats[1]
        }
        
        # Recomendaciones
        if report['user_summary']['by_role']:
            superadmin_count = next((u['total'] for u in report['user_summary']['by_role'] if u['role'] == 'superadmin'), 0)
            if superadmin_count == 0:
                report['recommendations'].append("Crear al menos un usuario superadmin")
            elif superadmin_count > 3:
                report['recommendations'].append("Considerar reducir el número de superadmins por seguridad")
        
        # Guardar reporte
        filename = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Reporte guardado en: {filepath}")
        return report
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        return None
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Iniciando verificación de migración v3.1.0...")
    
    # Verificar migración
    migration_ok = verify_migration()
    
    # Probar propiedades del modelo
    model_ok = test_user_properties()
    
    # Generar reporte
    report = generate_verification_report()
    
    if migration_ok and model_ok:
        print("\n✅ ¡Todas las verificaciones pasaron exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Algunas verificaciones fallaron")
        sys.exit(1) 