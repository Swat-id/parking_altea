#!/usr/bin/env python3
"""
Script de prueba para verificar la gestión de fechas, días de la semana y ejecución de programaciones
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService

def test_date_handling():
    """Probar el manejo de fechas en programaciones"""
    
    print("📅 PRUEBA DE MANEJO DE FECHAS")
    print("=" * 50)
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener un parking para las pruebas
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No hay parkings disponibles")
            return False
        
        print(f"Usando parking: {parking.name} (ID: {parking.id})")
        
        # Obtener paneles del parking
        panels = session.query(Panel).filter_by(parking_id=parking.id).all()
        print(f"Paneles disponibles: {len(panels)}")
        for panel in panels:
            print(f"  - {panel.name} ({panel.ip}) - Estado: {panel.status}")
        
        # Crear datos de prueba con diferentes formatos de fecha
        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        tomorrow_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week_date = (now + timedelta(days=7)).strftime('%Y-%m-%d')
        
        current_time = now.strftime('%H:%M')
        end_time = (now + timedelta(hours=1)).strftime('%H:%M')
        
        # Mapear día actual
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
        
        print(f"\n📊 DATOS DE PRUEBA:")
        print(f"Fecha actual: {current_date}")
        print(f"Fecha mañana: {tomorrow_date}")
        print(f"Fecha próxima semana: {next_week_date}")
        print(f"Hora actual: {current_time}")
        print(f"Hora fin: {end_time}")
        print(f"Día actual: {current_weekday_field}")
        
        # Crear servicio de programaciones
        schedule_service = PanelScheduleService(session)
        
        # PRUEBA 1: Programación que debe ejecutarse ahora
        print(f"\n🧪 PRUEBA 1: Programación que debe ejecutarse ahora")
        print("-" * 50)
        
        schedule_data_1 = {
            'parking_id': parking.id,
            'name': f'Prueba ejecución inmediata - {now.strftime("%H:%M:%S")}',
            'description': 'Programación que debe ejecutarse inmediatamente',
            'start_date': current_date,
            'end_date': next_week_date,
            'start_time': current_time,
            'end_time': end_time,
            'message': 'PRUEBA EJECUCIÓN INMEDIATA',
            'color': 3,
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
        
        result_1 = schedule_service.create_schedule(schedule_data_1)
        print(f"Resultado creación: {result_1}")
        
        if result_1['success']:
            print(f"✅ Programación creada: {result_1['schedule_id']}")
            if result_1.get('auto_executed'):
                print(f"✅ Programación ejecutada automáticamente: {result_1.get('panels_affected', 0)} paneles afectados")
            else:
                print("⚠️  Programación no se ejecutó automáticamente")
        else:
            print(f"❌ Error creando programación: {result_1['error']}")
        
        # PRUEBA 2: Programación para mañana
        print(f"\n🧪 PRUEBA 2: Programación para mañana")
        print("-" * 40)
        
        schedule_data_2 = {
            'parking_id': parking.id,
            'name': f'Prueba mañana - {now.strftime("%H:%M:%S")}',
            'description': 'Programación para mañana',
            'start_date': tomorrow_date,
            'end_date': next_week_date,
            'start_time': '10:00',
            'end_time': '12:00',
            'message': 'PRUEBA MAÑANA',
            'color': 2,
            'font_size': 16,
            'effect': 'static',
            'is_active': True,
            'priority': 1,
            'monday': True,
            'tuesday': True,
            'wednesday': True,
            'thursday': True,
            'friday': True,
            'saturday': False,
            'sunday': False
        }
        
        result_2 = schedule_service.create_schedule(schedule_data_2)
        print(f"Resultado creación: {result_2}")
        
        if result_2['success']:
            print(f"✅ Programación creada: {result_2['schedule_id']}")
            if result_2.get('auto_executed'):
                print(f"✅ Programación ejecutada automáticamente: {result_2.get('panels_affected', 0)} paneles afectados")
            else:
                print("✅ Programación no se ejecutó automáticamente (correcto, es para mañana)")
        else:
            print(f"❌ Error creando programación: {result_2['error']}")
        
        # PRUEBA 3: Verificar programaciones activas
        print(f"\n🧪 PRUEBA 3: Verificar programaciones activas")
        print("-" * 45)
        
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        print(f"Programaciones activas encontradas: {len(active_schedules)}")
        
        for schedule in active_schedules:
            print(f"  - {schedule.name} (ID: {schedule.id})")
            print(f"    Horario: {schedule.start_time} - {schedule.end_time}")
            print(f"    Fechas: {schedule.start_date.strftime('%Y-%m-%d')} - {schedule.end_date.strftime('%Y-%m-%d')}")
            print(f"    Días: {get_weekdays_string(schedule)}")
            print(f"    Activa: {schedule.is_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def get_weekdays_string(schedule):
    """Obtener string de días de la semana activos"""
    days = []
    if schedule.monday: days.append('Lun')
    if schedule.tuesday: days.append('Mar')
    if schedule.wednesday: days.append('Mié')
    if schedule.thursday: days.append('Jue')
    if schedule.friday: days.append('Vie')
    if schedule.saturday: days.append('Sáb')
    if schedule.sunday: days.append('Dom')
    return ', '.join(days) if days else 'Ninguno'

def test_weekday_mapping():
    """Probar el mapeo de días de la semana"""
    
    print(f"\n📅 PRUEBA DE MAPEO DE DÍAS DE LA SEMANA")
    print("=" * 50)
    
    now = datetime.now()
    current_weekday = now.weekday()
    
    # Mapeo usado en el código
    weekday_fields = {
        0: 'monday',
        1: 'tuesday', 
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday'
    }
    
    weekday_names = {
        0: 'Lunes',
        1: 'Martes', 
        2: 'Miércoles',
        3: 'Jueves',
        4: 'Viernes',
        5: 'Sábado',
        6: 'Domingo'
    }
    
    print(f"Fecha actual: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Día de la semana (weekday): {current_weekday}")
    print(f"Nombre del día: {weekday_names.get(current_weekday, 'Desconocido')}")
    print(f"Campo de base de datos: {weekday_fields.get(current_weekday, 'monday')}")
    
    # Verificar mapeo
    for weekday, field in weekday_fields.items():
        print(f"  {weekday} ({weekday_names[weekday]}) → {field}")
    
    return True

def test_time_comparison():
    """Probar la comparación de horas"""
    
    print(f"\n⏰ PRUEBA DE COMPARACIÓN DE HORAS")
    print("=" * 40)
    
    now = datetime.now()
    current_time_str = now.strftime('%H:%M')
    
    # Simular diferentes horarios
    test_times = [
        ('09:00', '17:00', 'Programación diurna'),
        ('18:00', '22:00', 'Programación nocturna'),
        ('00:00', '23:59', 'Programación todo el día'),
        ('12:00', '12:30', 'Programación corta'),
    ]
    
    print(f"Hora actual: {current_time_str}")
    print()
    
    for start_time, end_time, description in test_times:
        is_active = start_time <= current_time_str <= end_time
        status = "✅ ACTIVA" if is_active else "❌ INACTIVA"
        print(f"{description}: {start_time} - {end_time} → {status}")
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de programaciones...")
    
    success1 = test_weekday_mapping()
    success2 = test_time_comparison()
    success3 = test_date_handling()
    
    if success1 and success2 and success3:
        print(f"\n🎉 Todas las pruebas completadas exitosamente")
    else:
        print(f"\n⚠️  Algunas pruebas fallaron") 