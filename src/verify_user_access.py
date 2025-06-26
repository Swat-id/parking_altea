#!/usr/bin/env python3
"""
Script para verificar que todos los aparcamientos, cámaras y paneles
son accesibles por los usuarios Toni Alos e Iván Martí
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Parking, Access, Panel, UserParking, UserPanel
from auth import get_user_by_email, assign_parking_to_user, assign_panel_to_user
from config import DB_URL

def verify_and_assign_access():
    """Verificar y asignar acceso completo a todos los recursos"""
    
    # Configurar conexión a la base de datos
    engine = create_engine(DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    
    # Crear tablas si no existen
    Base.metadata.create_all(engine)
    
    session = Session()
    
    print("🔍 Verificando acceso de usuarios a recursos...")
    print("=" * 60)
    
    # Obtener usuarios
    toni = get_user_by_email('atea.dti@altea.es')
    ivan = get_user_by_email('gerenciapstd@altea.es')
    
    if not toni:
        print("❌ Usuario Toni Alos no encontrado")
        return False
    
    if not ivan:
        print("❌ Usuario Iván Martí no encontrado")
        return False
    
    print(f"✅ Toni Alos encontrado (ID: {toni.id})")
    print(f"✅ Iván Martí encontrado (ID: {ivan.id})")
    print()
    
    # Obtener todos los parkings
    all_parkings = session.query(Parking).all()
    print(f"📊 Total de parkings en el sistema: {len(all_parkings)}")
    
    # Obtener todos los paneles
    all_panels = session.query(Panel).all()
    print(f"📊 Total de paneles en el sistema: {len(all_panels)}")
    
    # Obtener todas las cámaras/accesos
    all_accesses = session.query(Access).all()
    print(f"📊 Total de cámaras/accesos en el sistema: {len(all_accesses)}")
    print()
    
    # Verificar asignaciones actuales
    print("🔍 Verificando asignaciones actuales...")
    
    # Parkings de Toni
    toni_parkings = session.query(UserParking).filter(UserParking.user_id == toni.id).all()
    toni_parking_ids = [up.parking_id for up in toni_parkings]
    print(f"   Toni Alos tiene {len(toni_parking_ids)} parkings asignados")
    
    # Parkings de Iván
    ivan_parkings = session.query(UserParking).filter(UserParking.user_id == ivan.id).all()
    ivan_parking_ids = [up.parking_id for up in ivan_parkings]
    print(f"   Iván Martí tiene {len(ivan_parking_ids)} parkings asignados")
    
    # Paneles de Toni
    toni_panels = session.query(UserPanel).filter(UserPanel.user_id == toni.id).all()
    toni_panel_ids = [up.panel_id for up in toni_panels]
    print(f"   Toni Alos tiene {len(toni_panel_ids)} paneles asignados")
    
    # Paneles de Iván
    ivan_panels = session.query(UserPanel).filter(UserPanel.user_id == ivan.id).all()
    ivan_panel_ids = [up.panel_id for up in ivan_panels]
    print(f"   Iván Martí tiene {len(ivan_panel_ids)} paneles asignados")
    print()
    
    # Asignar parkings faltantes
    print("🔧 Asignando parkings faltantes...")
    
    for parking in all_parkings:
        # Asignar a Toni si no tiene acceso
        if parking.id not in toni_parking_ids:
            success, error = assign_parking_to_user(toni.id, parking.id)
            if success:
                print(f"   ✅ Parking '{parking.name}' asignado a Toni Alos")
            else:
                print(f"   ❌ Error asignando parking '{parking.name}' a Toni: {error}")
        
        # Asignar a Iván si no tiene acceso
        if parking.id not in ivan_parking_ids:
            success, error = assign_parking_to_user(ivan.id, parking.id)
            if success:
                print(f"   ✅ Parking '{parking.name}' asignado a Iván Martí")
            else:
                print(f"   ❌ Error asignando parking '{parking.name}' a Iván: {error}")
    
    # Asignar paneles faltantes
    print("\n🔧 Asignando paneles faltantes...")
    
    for panel in all_panels:
        # Asignar a Toni si no tiene acceso
        if panel.id not in toni_panel_ids:
            success, error = assign_panel_to_user(toni.id, panel.id)
            if success:
                print(f"   ✅ Panel '{panel.name}' asignado a Toni Alos")
            else:
                print(f"   ❌ Error asignando panel '{panel.name}' a Toni: {error}")
        
        # Asignar a Iván si no tiene acceso
        if panel.id not in ivan_panel_ids:
            success, error = assign_panel_to_user(ivan.id, panel.id)
            if success:
                print(f"   ✅ Panel '{panel.name}' asignado a Iván Martí")
            else:
                print(f"   ❌ Error asignando panel '{panel.name}' a Iván: {error}")
    
    print()
    
    # Verificar asignaciones finales
    print("🔍 Verificando asignaciones finales...")
    
    # Recargar asignaciones
    toni_parkings_final = session.query(UserParking).filter(UserParking.user_id == toni.id).all()
    ivan_parkings_final = session.query(UserParking).filter(UserParking.user_id == ivan.id).all()
    toni_panels_final = session.query(UserPanel).filter(UserPanel.user_id == toni.id).all()
    ivan_panels_final = session.query(UserPanel).filter(UserPanel.user_id == ivan.id).all()
    
    print(f"   Toni Alos: {len(toni_parkings_final)} parkings, {len(toni_panels_final)} paneles")
    print(f"   Iván Martí: {len(ivan_parkings_final)} parkings, {len(ivan_panels_final)} paneles")
    
    # Verificar que ambos tienen acceso completo
    toni_has_all_parkings = len(toni_parkings_final) == len(all_parkings)
    ivan_has_all_parkings = len(ivan_parkings_final) == len(all_parkings)
    toni_has_all_panels = len(toni_panels_final) == len(all_panels)
    ivan_has_all_panels = len(ivan_panels_final) == len(all_panels)
    
    print()
    print("📋 RESUMEN DE VERIFICACIÓN:")
    print("=" * 40)
    print(f"Toni Alos - Parkings: {'✅' if toni_has_all_parkings else '❌'} ({len(toni_parkings_final)}/{len(all_parkings)})")
    print(f"Toni Alos - Paneles:  {'✅' if toni_has_all_panels else '❌'} ({len(toni_panels_final)}/{len(all_panels)})")
    print(f"Iván Martí - Parkings: {'✅' if ivan_has_all_parkings else '❌'} ({len(ivan_parkings_final)}/{len(all_parkings)})")
    print(f"Iván Martí - Paneles:  {'✅' if ivan_has_all_panels else '❌'} ({len(ivan_panels_final)}/{len(all_panels)})")
    
    # Mostrar detalles de parkings
    print("\n🏢 DETALLES DE PARKINGS:")
    for parking in all_parkings:
        toni_access = "✅" if parking.id in [up.parking_id for up in toni_parkings_final] else "❌"
        ivan_access = "✅" if parking.id in [up.parking_id for up in ivan_parkings_final] else "❌"
        print(f"   {parking.name}: Toni {toni_access} | Iván {ivan_access}")
    
    # Mostrar detalles de paneles
    print("\n📺 DETALLES DE PANELES:")
    for panel in all_panels:
        toni_access = "✅" if panel.id in [up.panel_id for up in toni_panels_final] else "❌"
        ivan_access = "✅" if panel.id in [up.panel_id for up in ivan_panels_final] else "❌"
        print(f"   {panel.name}: Toni {toni_access} | Iván {ivan_access}")
    
    session.close()
    
    # Verificar éxito completo
    all_success = toni_has_all_parkings and ivan_has_all_parkings and toni_has_all_panels and ivan_has_all_panels
    
    if all_success:
        print("\n🎉 ¡VERIFICACIÓN EXITOSA! Ambos usuarios tienen acceso completo a todos los recursos.")
        return True
    else:
        print("\n⚠️  VERIFICACIÓN INCOMPLETA. Algunos recursos no están asignados correctamente.")
        return False

if __name__ == '__main__':
    success = verify_and_assign_access()
    sys.exit(0 if success else 1) 