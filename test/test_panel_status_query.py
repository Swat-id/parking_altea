#!/usr/bin/env python3
"""
Script de prueba para verificar el problema de consulta de estado de paneles en el servicio de programaciones
"""

import sys
import os
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService

def test_panel_status_query():
    """Probar la consulta de estado de paneles"""
    
    print("🔍 PRUEBA DE CONSULTA DE ESTADO DE PANELES")
    print("=" * 50)
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los parkings
        parkings = session.query(Parking).all()
        print(f"Parkings disponibles: {len(parkings)}")
        
        for parking in parkings:
            print(f"\n🏢 Parking: {parking.name} (ID: {parking.id})")
            
            # Obtener paneles del parking
            panels = session.query(Panel).filter_by(parking_id=parking.id).all()
            print(f"  Total paneles: {len(panels)}")
            
            # Mostrar estado de cada panel
            for panel in panels:
                print(f"    - {panel.name} ({panel.ip}) - Estado: '{panel.status}'")
            
            # Probar consulta específica del servicio de programaciones
            online_panels = session.query(Panel).filter(
                Panel.parking_id == parking.id,
                Panel.status == 'ONLINE'
            ).all()
            
            print(f"  Paneles ONLINE (según consulta): {len(online_panels)}")
            
            # Verificar si hay discrepancias
            if len(panels) > 0 and len(online_panels) == 0:
                print(f"  ⚠️  PROBLEMA: Hay {len(panels)} paneles pero 0 están marcados como ONLINE")
                print(f"  Estados encontrados: {[p.status for p in panels]}")
            elif len(online_panels) > 0:
                print(f"  ✅ OK: {len(online_panels)} paneles online")
        
        # Probar con un parking específico que sabemos que tiene paneles
        print(f"\n🧪 PRUEBA ESPECÍFICA CON PARKING 1")
        print("-" * 40)
        
        parking_1 = session.query(Parking).filter_by(id=1).first()
        if parking_1:
            print(f"Parking: {parking_1.name}")
            
            # Consulta directa
            all_panels = session.query(Panel).filter_by(parking_id=1).all()
            print(f"Todos los paneles: {len(all_panels)}")
            for panel in all_panels:
                print(f"  - {panel.name}: status='{panel.status}'")
            
            # Consulta del servicio
            online_panels = session.query(Panel).filter(
                Panel.parking_id == 1,
                Panel.status == 'ONLINE'
            ).all()
            print(f"Paneles ONLINE: {len(online_panels)}")
            
            # Verificar si hay programaciones para este parking
            schedules = session.query(PanelSchedule).filter_by(parking_id=1).all()
            print(f"Programaciones para este parking: {len(schedules)}")
            
            if schedules:
                schedule = schedules[0]
                print(f"Probando ejecución de programación: {schedule.name}")
                
                schedule_service = PanelScheduleService(session)
                result = schedule_service.execute_schedule(schedule)
                print(f"Resultado: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_api_vs_database():
    """Comparar datos de la API vs base de datos"""
    
    print(f"\n🌐 COMPARACIÓN API vs BASE DE DATOS")
    print("=" * 40)
    
    import requests
    
    try:
        # Obtener datos de la API
        api_response = requests.get('http://157.180.91.63:6001/api/panels')
        api_panels = api_response.json()
        
        print(f"Paneles en API: {len(api_panels)}")
        
        # Conectar a la base de datos
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Obtener datos de la base de datos
        db_panels = session.query(Panel).all()
        print(f"Paneles en BD: {len(db_panels)}")
        
        # Comparar
        print(f"\nComparación:")
        for db_panel in db_panels:
            api_panel = next((p for p in api_panels if p['id'] == db_panel.id), None)
            if api_panel:
                status_match = db_panel.status == api_panel['status']
                print(f"  Panel {db_panel.id} ({db_panel.name}):")
                print(f"    BD status: '{db_panel.status}'")
                print(f"    API status: '{api_panel['status']}'")
                print(f"    Match: {'✅' if status_match else '❌'}")
            else:
                print(f"  Panel {db_panel.id} ({db_panel.name}): No encontrado en API")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error comparando API vs BD: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de estado de paneles...")
    
    success1 = test_panel_status_query()
    success2 = test_api_vs_database()
    
    if success1 and success2:
        print(f"\n🎉 Todas las pruebas completadas")
    else:
        print(f"\n⚠️  Algunas pruebas fallaron") 