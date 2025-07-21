#!/usr/bin/env python3
"""
Script de prueba para diagnosticar errores en la creación de programaciones
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService

def test_schedule_creation():
    """Probar la creación de programaciones para identificar errores"""
    
    print("🔍 DIAGNÓSTICO DE ERRORES EN PROGRAMACIONES")
    print("=" * 60)
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Verificar que hay parkings disponibles
        parkings = session.query(Parking).all()
        print(f"📊 Parkings disponibles: {len(parkings)}")
        
        if not parkings:
            print("❌ No hay parkings disponibles")
            return False
        
        # Mostrar parkings
        for parking in parkings:
            print(f"   - {parking.id}: {parking.name}")
        
        # 2. Verificar que hay paneles disponibles
        panels = session.query(Panel).all()
        print(f"📺 Paneles disponibles: {len(panels)}")
        
        for panel in panels:
            print(f"   - {panel.id}: {panel.name} ({panel.ip}) - Estado: {panel.status}")
        
        # 3. Verificar estructura de la tabla panel_schedules
        try:
            schedules = session.query(PanelSchedule).all()
            print(f"📅 Programaciones existentes: {len(schedules)}")
        except Exception as e:
            print(f"❌ Error accediendo a tabla panel_schedules: {e}")
            return False
        
        # 4. Probar creación de programación
        print("\n🧪 PROBANDO CREACIÓN DE PROGRAMACIÓN")
        print("-" * 40)
        
        # Obtener el primer parking
        parking = parkings[0]
        print(f"Usando parking: {parking.name} (ID: {parking.id})")
        
        # Crear datos de prueba
        now = datetime.now()
        start_date = now.strftime('%Y-%m-%d')
        end_date = (now + timedelta(days=7)).strftime('%Y-%m-%d')
        start_time = now.strftime('%H:%M')
        end_time = (now + timedelta(hours=1)).strftime('%H:%M')
        
        # Mapear día actual a campo de la base de datos
        weekday_fields = {
            0: 'monday',
            1: 'tuesday', 
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturday',
            6: 'sunday'
        }
        current_weekday = now.weekday()
        current_weekday_field = weekday_fields.get(current_weekday, 'monday')
        
        schedule_data = {
            'parking_id': parking.id,
            'name': f'Prueba de diagnóstico - {now.strftime("%H:%M:%S")}',
            'description': 'Programación de prueba para diagnosticar errores',
            'start_date': start_date,
            'end_date': end_date,
            'start_time': start_time,
            'end_time': end_time,
            'message': 'PROVA DIAGNÒSTIC',
            'color': 2,
            'font_size': 16,
            'effect': 'static',
            'is_active': True,
            'priority': 1,
            # Activar solo el día actual
            'monday': current_weekday_field == 'monday',
            'tuesday': current_weekday_field == 'tuesday',
            'wednesday': current_weekday_field == 'wednesday',
            'thursday': current_weekday_field == 'thursday',
            'friday': current_weekday_field == 'friday',
            'saturday': current_weekday_field == 'saturday',
            'sunday': current_weekday_field == 'sunday'
        }
        
        print(f"Datos de prueba:")
        print(json.dumps(schedule_data, indent=2, default=str))
        
        # Crear servicio de programaciones
        schedule_service = PanelScheduleService(session)
        
        # Intentar crear la programación
        print("\n🔄 Intentando crear programación...")
        result = schedule_service.create_schedule(schedule_data)
        
        print(f"Resultado: {result}")
        
        if result['success']:
            print("✅ Programación creada exitosamente")
            if result.get('auto_executed'):
                print(f"✅ Programación ejecutada automáticamente: {result.get('panels_affected', 0)} paneles afectados")
            else:
                print("⚠️  Programación no se ejecutó automáticamente")
            return True
        else:
            print(f"❌ Error creando programación: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_api_endpoint():
    """Probar el endpoint de la API directamente"""
    
    print("\n🌐 PROBANDO ENDPOINT DE LA API")
    print("-" * 40)
    
    import requests
    
    # Datos de prueba
    now = datetime.now()
    start_date = now.strftime('%Y-%m-%d')
    end_date = (now + timedelta(days=7)).strftime('%Y-%m-%d')
    start_time = now.strftime('%H:%M')
    end_time = (now + timedelta(hours=1)).strftime('%H:%M')
    
    weekday_fields = {
        0: 'monday',
        1: 'tuesday', 
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday'
    }
    current_weekday = now.weekday()
    current_weekday_field = weekday_fields.get(current_weekday, 'monday')
    
    schedule_data = {
        'parking_id': 1,  # Usar parking ID 1
        'name': f'Prueba API - {now.strftime("%H:%M:%S")}',
        'description': 'Prueba del endpoint de la API',
        'start_date': start_date,
        'end_date': end_date,
        'start_time': start_time,
        'end_time': end_time,
        'message': 'PROVA API',
        'color': 2,
        'font_size': 16,
        'effect': 'static',
        'is_active': True,
        'priority': 1,
        'monday': current_weekday_field == 'monday',
        'tuesday': current_weekday_field == 'tuesday',
        'wednesday': current_weekday_field == 'wednesday',
        'thursday': current_weekday_field == 'thursday',
        'friday': current_weekday_field == 'friday',
        'saturday': current_weekday_field == 'saturday',
        'sunday': current_weekday_field == 'sunday'
    }
    
    try:
        # Probar endpoint local
        response = requests.post(
            'http://localhost:6001/api/schedules',
            json=schedule_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Endpoint funciona correctamente")
            return True
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando al endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico de programaciones...")
    
    # Probar creación directa
    success1 = test_schedule_creation()
    
    # Probar endpoint de la API
    success2 = test_api_endpoint()
    
    if success1 and success2:
        print("\n🎉 Diagnóstico completado: Todo funciona correctamente")
    else:
        print("\n⚠️  Diagnóstico completado: Se encontraron problemas") 