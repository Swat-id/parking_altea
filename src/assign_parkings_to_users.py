#!/usr/bin/env python3
"""
Script para asignar parkings a usuarios existentes
Asigna todos los parkings a usuarios con rol 'user' que no tengan asignaciones
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
from datetime import datetime

def assign_parkings_to_users():
    """Asignar parkings a usuarios existentes"""
    print("🅿️  Iniciando asignación de parkings a usuarios...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener usuarios con rol 'user' que no tengan asignaciones
        print("👥 Identificando usuarios sin asignaciones...")
        result = session.execute(text("""
            SELECT u.id, u.name, u.email, u.role
            FROM users u
            WHERE u.role = 'user'
            AND u.is_active = true
            AND NOT EXISTS (
                SELECT 1 FROM user_parkings up 
                WHERE up.user_id = u.id
            )
            ORDER BY u.name
        """))
        
        users_without_parkings = result.fetchall()
        
        if not users_without_parkings:
            print("ℹ️  No se encontraron usuarios sin asignaciones de parkings")
            return True
        
        print(f"✅ Encontrados {len(users_without_parkings)} usuarios sin asignaciones:")
        for user in users_without_parkings:
            print(f"   - {user[1]} ({user[2]})")
        
        # 2. Obtener todos los parkings disponibles
        result = session.execute(text("""
            SELECT id, name, location
            FROM parkings
            WHERE is_active = true OR is_active IS NULL
            ORDER BY name
        """))
        
        available_parkings = result.fetchall()
        
        if not available_parkings:
            print("❌ No se encontraron parkings disponibles")
            return False
        
        print(f"✅ Encontrados {len(available_parkings)} parkings disponibles:")
        for parking in available_parkings:
            print(f"   - {parking[1]} ({parking[2]})")
        
        # 3. Asignar todos los parkings a cada usuario
        print("\n🔗 Asignando parkings a usuarios...")
        assignments_created = 0
        
        for user in users_without_parkings:
            user_id = user[0]
            user_name = user[1]
            
            print(f"   Asignando parkings a {user_name}...")
            
            for parking in available_parkings:
                parking_id = parking[0]
                parking_name = parking[1]
                
                # Verificar si ya existe la asignación
                existing = session.execute(text("""
                    SELECT 1 FROM user_parkings 
                    WHERE user_id = :user_id AND parking_id = :parking_id
                """), {'user_id': user_id, 'parking_id': parking_id})
                
                if not existing.fetchone():
                    # Crear nueva asignación
                    session.execute(text("""
                        INSERT INTO user_parkings (user_id, parking_id, created_at)
                        VALUES (:user_id, :parking_id, NOW())
                    """), {'user_id': user_id, 'parking_id': parking_id})
                    
                    assignments_created += 1
                    print(f"     ✅ Asignado: {parking_name}")
                else:
                    print(f"     ℹ️  Ya asignado: {parking_name}")
        
        # 4. Commit de cambios
        session.commit()
        print(f"\n🎉 Asignación completada: {assignments_created} nuevas asignaciones creadas")
        
        # 5. Verificar resultado
        print("\n📊 Verificando asignaciones...")
        result = session.execute(text("""
            SELECT u.name, u.role, COUNT(up.parking_id) as parkings_assigned
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            WHERE u.role = 'user'
            GROUP BY u.id, u.name, u.role
            ORDER BY u.name
        """))
        
        assignments = result.fetchall()
        print("✅ Estado final de asignaciones:")
        for assignment in assignments:
            print(f"   - {assignment[0]} ({assignment[1]}): {assignment[2]} parkings")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la asignación: {e}")
        return False
    finally:
        session.close()

def verify_parking_assignments():
    """Verificar que las asignaciones de parkings son correctas"""
    print("\n🔍 Verificando asignaciones de parkings...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar usuarios sin asignaciones
        result = session.execute(text("""
            SELECT COUNT(*) as users_without_parkings
            FROM users u
            WHERE u.role = 'user'
            AND u.is_active = true
            AND NOT EXISTS (
                SELECT 1 FROM user_parkings up 
                WHERE up.user_id = u.id
            )
        """))
        
        users_without_parkings = result.scalar()
        
        if users_without_parkings == 0:
            print("✅ Todos los usuarios con rol 'user' tienen asignaciones de parkings")
        else:
            print(f"⚠️  {users_without_parkings} usuarios con rol 'user' no tienen asignaciones")
        
        # Verificar distribución de parkings
        result = session.execute(text("""
            SELECT u.name, u.role, COUNT(up.parking_id) as parkings_assigned
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            WHERE u.role = 'user'
            GROUP BY u.id, u.name, u.role
            ORDER BY parkings_assigned DESC, u.name
        """))
        
        assignments = result.fetchall()
        print("\n📊 Distribución de parkings por usuario:")
        for assignment in assignments:
            print(f"   - {assignment[0]}: {assignment[2]} parkings")
        
        # Verificar parkings sin asignar a usuarios regulares
        result = session.execute(text("""
            SELECT COUNT(*) as parkings_without_user_assignments
            FROM parkings p
            WHERE (p.is_active = true OR p.is_active IS NULL)
            AND NOT EXISTS (
                SELECT 1 FROM user_parkings up
                JOIN users u ON up.user_id = u.id
                WHERE up.parking_id = p.id AND u.role = 'user'
            )
        """))
        
        parkings_without_user_assignments = result.scalar()
        
        if parkings_without_user_assignments == 0:
            print("✅ Todos los parkings están asignados a usuarios regulares")
        else:
            print(f"⚠️  {parkings_without_user_assignments} parkings no están asignados a usuarios regulares")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        return False
    finally:
        session.close()

def generate_assignment_report():
    """Generar reporte de asignaciones"""
    print("\n📋 Generando reporte de asignaciones...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'version': 'v3.1.0',
            'assignment_summary': {},
            'user_details': [],
            'parking_details': []
        }
        
        # Resumen de asignaciones
        result = session.execute(text("""
            SELECT 
                COUNT(DISTINCT u.id) as total_users,
                COUNT(DISTINCT up.parking_id) as total_parkings_assigned,
                COUNT(up.id) as total_assignments
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            WHERE u.role = 'user'
        """))
        
        summary = result.fetchone()
        report['assignment_summary'] = {
            'total_users': summary[0],
            'total_parkings_assigned': summary[1],
            'total_assignments': summary[2]
        }
        
        # Detalles por usuario
        result = session.execute(text("""
            SELECT u.name, u.email, COUNT(up.parking_id) as parkings_assigned,
                   STRING_AGG(p.name, ', ' ORDER BY p.name) as parking_names
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            LEFT JOIN parkings p ON up.parking_id = p.id
            WHERE u.role = 'user'
            GROUP BY u.id, u.name, u.email
            ORDER BY u.name
        """))
        
        report['user_details'] = [
            {
                'name': row[0],
                'email': row[1],
                'parkings_assigned': row[2],
                'parking_names': row[3].split(', ') if row[3] else []
            }
            for row in result.fetchall()
        ]
        
        # Detalles por parking
        result = session.execute(text("""
            SELECT p.name, p.location, COUNT(up.user_id) as users_assigned,
                   STRING_AGG(u.name, ', ' ORDER BY u.name) as user_names
            FROM parkings p
            LEFT JOIN user_parkings up ON p.id = up.parking_id
            LEFT JOIN users u ON up.user_id = u.id AND u.role = 'user'
            WHERE p.is_active = true OR p.is_active IS NULL
            GROUP BY p.id, p.name, p.location
            ORDER BY p.name
        """))
        
        report['parking_details'] = [
            {
                'name': row[0],
                'location': row[1],
                'users_assigned': row[2],
                'user_names': row[3].split(', ') if row[3] else []
            }
            for row in result.fetchall()
        ]
        
        # Guardar reporte
        filename = f"parking_assignment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        import json
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Asignar parkings a usuarios existentes')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar asignaciones')
    parser.add_argument('--report-only', action='store_true', help='Solo generar reporte')
    parser.add_argument('--assign-only', action='store_true', help='Solo asignar parkings')
    
    args = parser.parse_args()
    
    if args.verify_only:
        success = verify_parking_assignments()
    elif args.report_only:
        report = generate_assignment_report()
        success = report is not None
    elif args.assign_only:
        success = assign_parkings_to_users()
    else:
        # Ejecutar asignación, verificación y reporte
        assign_success = assign_parkings_to_users()
        verify_success = verify_parking_assignments()
        report = generate_assignment_report()
        success = assign_success and verify_success and report is not None
    
    if success:
        print("\n✅ Proceso completado exitosamente")
        sys.exit(0)
    else:
        print("\n❌ Proceso falló")
        sys.exit(1) 