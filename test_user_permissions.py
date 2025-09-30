#!/usr/bin/env python3
"""
Script para probar los permisos de usuarios
Verifica que los filtros funcionen correctamente para usuarios regulares vs superadmin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models import User, Parking, Panel, IndividualSensor, UserParking, UserPanel
from src.config import Session
from src.auth import get_user_accessible_parking_ids, get_user_accessible_panel_ids

def test_user_permissions():
    session = Session()
    
    try:
        print("=== TEST PERMISOS DE USUARIO ===")
        
        # 1. Obtener usuarios de prueba
        users = session.query(User).all()
        print(f"\n1. USUARIOS EN SISTEMA ({len(users)}):")
        for user in users:
            print(f"   ID: {user.id}, Email: {user.email}, Rol: {user.role}")
        
        if not users:
            print("   ❌ No hay usuarios en la base de datos")
            return
        
        # 2. Obtener parkings y paneles totales
        total_parkings = session.query(Parking).count()
        total_panels = session.query(Panel).count()
        total_sensors = session.query(IndividualSensor).count()
        
        print(f"\n2. RECURSOS TOTALES EN SISTEMA:")
        print(f"   Parkings: {total_parkings}")
        print(f"   Paneles: {total_panels}")
        print(f"   Sensores: {total_sensors}")
        
        # 3. Probar permisos para cada usuario
        print(f"\n3. PERMISOS POR USUARIO:")
        
        for user in users:
            print(f"\n   👤 USUARIO: {user.email} (ID: {user.id}, Rol: {user.role})")
            
            # Obtener permisos
            accessible_parking_ids = get_user_accessible_parking_ids(session, user.id, user.role)
            accessible_panel_ids = get_user_accessible_panel_ids(session, user.id, user.role)
            
            print(f"      🏢 Parkings accesibles: {len(accessible_parking_ids)} - {accessible_parking_ids}")
            print(f"      📺 Paneles accesibles: {len(accessible_panel_ids)} - {accessible_panel_ids}")
            
            # Verificar sensores en parkings accesibles
            if accessible_parking_ids:
                sensors_count = session.query(IndividualSensor).filter(
                    IndividualSensor.parking_id.in_(accessible_parking_ids)
                ).count()
                print(f"      🔍 Sensores en parkings accesibles: {sensors_count}")
            else:
                print(f"      🔍 Sensores en parkings accesibles: 0 (sin acceso a parkings)")
            
            # Verificar asignaciones directas para usuarios regulares
            if user.role != 'superadmin':
                user_parkings = session.query(UserParking).filter(UserParking.user_id == user.id).all()
                user_panels = session.query(UserPanel).filter(UserPanel.user_id == user.id).all()
                
                print(f"      📋 Asignaciones directas:")
                print(f"         - Parkings asignados: {len(user_parkings)} - {[up.parking_id for up in user_parkings]}")
                print(f"         - Paneles asignados: {len(user_panels)} - {[up.panel_id for up in user_panels]}")
                
                # Verificar paneles por parkings
                if user_parkings:
                    panels_by_parking = session.query(Panel).filter(
                        Panel.parking_id.in_([up.parking_id for up in user_parkings])
                    ).all()
                    print(f"         - Paneles por parkings: {len(panels_by_parking)} - {[p.id for p in panels_by_parking]}")
        
        # 4. Verificar casos problemáticos
        print(f"\n4. VERIFICACIÓN DE CASOS PROBLEMÁTICOS:")
        
        # Usuarios regulares sin asignaciones
        regular_users = [u for u in users if u.role != 'superadmin']
        for user in regular_users:
            user_parkings = session.query(UserParking).filter(UserParking.user_id == user.id).count()
            user_panels = session.query(UserPanel).filter(UserPanel.user_id == user.id).count()
            
            if user_parkings == 0 and user_panels == 0:
                print(f"   ⚠️  Usuario {user.email} no tiene asignaciones - no verá nada")
            else:
                print(f"   ✅ Usuario {user.email} tiene asignaciones correctas")
        
        # Superadmins
        superadmins = [u for u in users if u.role == 'superadmin']
        for user in superadmins:
            accessible_parkings = get_user_accessible_parking_ids(session, user.id, user.role)
            if len(accessible_parkings) == total_parkings:
                print(f"   ✅ Superadmin {user.email} ve todos los parkings ({len(accessible_parkings)})")
            else:
                print(f"   ❌ Superadmin {user.email} no ve todos los parkings ({len(accessible_parkings)}/{total_parkings})")
        
        print(f"\n✅ TEST COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_user_permissions()
