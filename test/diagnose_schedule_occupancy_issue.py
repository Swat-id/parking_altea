#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en la integración entre programaciones y ocupación
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService
from panel_communication_service import update_parking_panels

def diagnose_schedule_occupancy_issue():
    """Diagnosticar el problema con programaciones y ocupación"""
    
    print("=== DIAGNÓSTICO: Problema Programaciones vs Ocupación ===")
    
    # Crear conexión a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Verificar parkings disponibles
        parkings = session.query(Parking).all()
        print(f"\n1. PARKINGS DISPONIBLES: {len(parkings)}")
        for parking in parkings:
            panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
            print(f"   - {parking.name} (ID: {parking.id}) - Paneles: {len(panels)}")
            print(f"     Estado: {parking.status}, Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
        
        if not parkings:
            print("❌ No hay parkings configurados")
            return
        
        # 2. Verificar programaciones existentes
        schedules = session.query(PanelSchedule).all()
        print(f"\n2. PROGRAMACIONES EXISTENTES: {len(schedules)}")
        for schedule in schedules:
            print(f"   - {schedule.name} (ID: {schedule.id})")
            print(f"     Parking: {schedule.parking_id}, Activa: {schedule.is_active}")
            print(f"     Fechas: {schedule.start_date} - {schedule.end_date}")
            print(f"     Horario: {schedule.start_time} - {schedule.end_time}")
            print(f"     Días: L={schedule.monday} M={schedule.tuesday} X={schedule.wednesday} J={schedule.thursday} V={schedule.friday} S={schedule.saturday} D={schedule.sunday}")
        
        # 3. Verificar programaciones activas para cada parking
        print(f"\n3. PROGRAMACIONES ACTIVAS POR PARKING:")
        schedule_service = PanelScheduleService(session)
        
        for parking in parkings:
            active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
            print(f"\n   Parking {parking.name} (ID: {parking.id}):")
            if active_schedules:
                for schedule in active_schedules:
                    print(f"     ✅ ACTIVA: {schedule.name} (ID: {schedule.id})")
                    print(f"        Mensaje: '{schedule.message}'")
                    print(f"        Prioridad: {schedule.priority}")
            else:
                print(f"     ❌ No hay programaciones activas")
        
        # 4. Probar actualización de ocupación
        print(f"\n4. PRUEBA DE ACTUALIZACIÓN DE OCUPACIÓN:")
        
        # Seleccionar el primer parking con paneles
        test_parking = None
        for parking in parkings:
            panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
            if panels:
                test_parking = parking
                break
        
        if not test_parking:
            print("❌ No hay parkings con paneles configurados para la prueba")
            return
        
        print(f"   Parking de prueba: {test_parking.name} (ID: {test_parking.id})")
        
        # Verificar programaciones activas antes de la prueba
        active_schedules = schedule_service.get_active_schedules_for_parking(test_parking.id)
        print(f"   Programaciones activas antes de la prueba: {len(active_schedules)}")
        
        # Intentar actualizar paneles
        print(f"   Intentando actualizar paneles...")
        result = update_parking_panels(
            parking_id=test_parking.id,
            current_occupancy=test_parking.current_occupancy,
            max_capacity=test_parking.max_capacity,
            status=test_parking.status,
            db_session=session
        )
        
        print(f"   Resultado: {result}")
        
        if result == "SCHEDULE_ACTIVE":
            print("   ✅ CORRECTO: Los paneles fueron bloqueados por programación activa")
        elif isinstance(result, dict) and result.get('success'):
            print("   ✅ Los paneles se actualizaron correctamente")
        else:
            print("   ❌ Error en la actualización de paneles")
        
        # 5. Verificar estado actual de los paneles
        print(f"\n5. ESTADO ACTUAL DE LOS PANELES:")
        panels = session.query(Panel).filter(Panel.parking_id == test_parking.id).all()
        for panel in panels:
            print(f"   Panel {panel.ip}:")
            print(f"     Estado: {panel.status}")
            print(f"     Último mensaje: '{panel.last_message}'")
            print(f"     Última actualización: {panel.last_update}")
        
        # 6. Información del sistema
        print(f"\n6. INFORMACIÓN DEL SISTEMA:")
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        print(f"   Hora actual: {current_time}")
        print(f"   Día actual: {weekday_names[current_weekday]}")
        print(f"   Fecha: {now.strftime('%Y-%m-%d')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_schedule_creation():
    """Test para crear una programación de prueba"""
    
    print("\n=== TEST: Creación de Programación de Prueba ===")
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener un parking con paneles
        parking = None
        for p in session.query(Parking).all():
            panels = session.query(Panel).filter(Panel.parking_id == p.id).all()
            if panels:
                parking = p
                break
        
        if not parking:
            print("❌ No hay parkings con paneles para la prueba")
            return False
        
        # Crear programación de prueba
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        schedule_data = {
            'parking_id': parking.id,
            'name': 'Test Schedule - Diagnóstico',
            'description': 'Programación de prueba para diagnóstico',
            'start_date': now.date(),
            'end_date': (now + timedelta(days=1)).date(),
            'start_time': current_time,
            'end_time': (now + timedelta(hours=1)).strftime('%H:%M'),
            'message': 'TEST DIAGNÓSTICO ACTIVO',
            'color': 1,  # Rojo
            'font_size': 16,
            'effect': 'static',
            'is_active': True,
            'priority': 1,
            current_weekday_field: True
        }
        
        schedule_service = PanelScheduleService(session)
        result = schedule_service.create_schedule(schedule_data)
        
        if result['success']:
            print(f"✅ Programación creada: {result['schedule_id']}")
            
            # Verificar que está activa
            active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
            print(f"✅ Programaciones activas después de crear: {len(active_schedules)}")
            
            # Limpiar
            schedule = session.query(PanelSchedule).filter(PanelSchedule.id == result['schedule_id']).first()
            if schedule:
                session.delete(schedule)
                session.commit()
                print("✅ Programación de prueba eliminada")
            
            return True
        else:
            print(f"❌ Error creando programación: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de creación: {e}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("Iniciando diagnóstico del problema programaciones vs ocupación...")
    
    # Ejecutar diagnóstico
    diagnose_schedule_occupancy_issue()
    
    # Ejecutar test de creación
    test_schedule_creation()
    
    print("\n" + "="*60)
    print("DIAGNÓSTICO COMPLETADO")
    print("="*60) 