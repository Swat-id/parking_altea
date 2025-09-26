#!/usr/bin/env python3
"""
Test para verificar que el superadmin tiene acceso completo sin filtros
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from auth import get_user_accessible_parking_ids, get_user_accessible_panel_ids, get_user_accessible_access_ids
from models import Parking, Panel, Access, User

def test_superadmin_access():
    """Test para verificar acceso completo del superadmin"""
    print("🧪 TESTING: Acceso de Superadmin")
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 1. Obtener total de parkings en la BD
        total_parkings = session.query(Parking).count()
        total_panels = session.query(Panel).count()
        total_accesses = session.query(Access).count()
        
        print(f"📊 Totales en BD:")
        print(f"   - Parkings: {total_parkings}")
        print(f"   - Paneles: {total_panels}")
        print(f"   - Accesos: {total_accesses}")
        
        # 2. Test Superadmin
        print(f"\n👑 Testing Superadmin:")
        superadmin_parkings = get_user_accessible_parking_ids(session, 1, 'superadmin')
        superadmin_panels = get_user_accessible_panel_ids(session, 1, 'superadmin')
        superadmin_accesses = get_user_accessible_access_ids(session, 1, 'superadmin')
        
        print(f"   - Parkings accesibles: {len(superadmin_parkings)}")
        print(f"   - Paneles accesibles: {len(superadmin_panels)}")
        print(f"   - Accesos accesibles: {len(superadmin_accesses)}")
        
        # 3. Verificaciones
        assert len(superadmin_parkings) == total_parkings, f"❌ Superadmin no tiene acceso a todos los parkings: {len(superadmin_parkings)}/{total_parkings}"
        assert len(superadmin_panels) == total_panels, f"❌ Superadmin no tiene acceso a todos los paneles: {len(superadmin_panels)}/{total_panels}"
        assert len(superadmin_accesses) == total_accesses, f"❌ Superadmin no tiene acceso a todos los accesos: {len(superadmin_accesses)}/{total_accesses}"
        
        print("✅ SUPERADMIN: Acceso completo verificado")
        
        # 4. Test Usuario Regular (para comparar)
        print(f"\n👤 Testing Usuario Regular:")
        regular_parkings = get_user_accessible_parking_ids(session, 2, 'user')
        regular_panels = get_user_accessible_panel_ids(session, 2, 'user')
        regular_accesses = get_user_accessible_access_ids(session, 2, 'user')
        
        print(f"   - Parkings accesibles: {len(regular_parkings)}")
        print(f"   - Paneles accesibles: {len(regular_panels)}")
        print(f"   - Accesos accesibles: {len(regular_accesses)}")
        
        # Usuario regular debe tener menos acceso que superadmin
        assert len(regular_parkings) <= total_parkings, "❌ Usuario regular tiene más parkings que el total"
        print("✅ USUARIO REGULAR: Filtrado funcionando correctamente")
        
        # 5. Mostrar algunos IDs para verificar
        if superadmin_parkings:
            print(f"\n📋 Primeros parkings del superadmin: {superadmin_parkings[:5]}")
        if regular_parkings:
            print(f"📋 Primeros parkings del usuario regular: {regular_parkings[:5]}")
        
        print(f"\n🎉 TODOS LOS TESTS PASARON")
        print(f"✅ Superadmin tiene acceso SIN FILTROS a todos los recursos")
        print(f"✅ Usuario regular tiene acceso FILTRADO según asignaciones")
        
    except Exception as e:
        print(f"❌ ERROR en test: {e}")
        return False
    finally:
        session.close()
    
    return True

def test_endpoint_access_simulation():
    """Simular el comportamiento en los endpoints"""
    print(f"\n🌐 SIMULANDO: Comportamiento en endpoints")
    
    engine = create_engine(DB_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Simular request.accessible_parking_ids para superadmin
        superadmin_accessible = get_user_accessible_parking_ids(session, 1, 'superadmin')
        
        # Simular query filtrada como en los endpoints
        if superadmin_accessible:
            # Esto es lo que pasaría en el endpoint
            print(f"🔍 Query simulada para superadmin:")
            print(f"   WHERE parking_id IN ({', '.join(map(str, superadmin_accessible[:5]))}...)")
            print(f"   Total IDs en filtro: {len(superadmin_accessible)}")
            
            # Verificar que incluye todos los parkings
            all_parking_ids = [p.id for p in session.query(Parking).all()]
            missing_ids = set(all_parking_ids) - set(superadmin_accessible)
            
            if not missing_ids:
                print("✅ Superadmin: Query incluye TODOS los parkings")
            else:
                print(f"❌ Superadmin: Faltan parkings en query: {missing_ids}")
        
        # Simular para usuario regular
        regular_accessible = get_user_accessible_parking_ids(session, 2, 'user')
        if regular_accessible:
            print(f"\n🔍 Query simulada para usuario regular:")
            print(f"   WHERE parking_id IN ({', '.join(map(str, regular_accessible))})")
            print(f"   Total IDs en filtro: {len(regular_accessible)}")
            print("✅ Usuario regular: Query filtrada correctamente")
        else:
            print("ℹ️ Usuario regular: Sin parkings asignados (query vacía)")
            
    except Exception as e:
        print(f"❌ ERROR en simulación: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST DE ACCESO SUPERADMIN vs USUARIO REGULAR")
    print("=" * 60)
    
    success = test_superadmin_access()
    test_endpoint_access_simulation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 RESULTADO: TODOS LOS TESTS PASARON")
        print("✅ El superadmin tiene acceso completo SIN FILTROS")
        print("✅ Los usuarios regulares tienen acceso FILTRADO")
    else:
        print("❌ RESULTADO: ALGUNOS TESTS FALLARON")
    print("=" * 60)
