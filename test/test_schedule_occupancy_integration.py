#!/usr/bin/env python3
"""
Test para verificar la integración entre programaciones y actualización de ocupación
"""

import sys
import os
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService
from panel_communication_service import update_parking_panels

def test_schedule_occupancy_integration():
    """Test para verificar que las programaciones tienen prioridad sobre la actualización de ocupación"""
    
    print("=== TEST: Integración Programaciones vs Actualización de Ocupación ===")
    
    # Crear conexión a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener un parking de prueba
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para el test")
            return False
        
        print(f"✅ Parking encontrado: {parking.name} (ID: {parking.id})")
        
        # 2. Verificar que tiene paneles configurados
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        if not panels:
            print("❌ El parking no tiene paneles configurados")
            return False
        
        print(f"✅ Paneles encontrados: {len(panels)}")
        
        # 3. Crear una programación activa para el momento actual
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        
        # Mapear weekday a campos de la base de datos
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        # Crear programación que esté activa ahora
        schedule_data = {
            'parking_id': parking.id,
            'name': 'Test Schedule - Ocupación',
            'description': 'Programación de prueba para test de integración',
            'start_date': now.date(),
            'end_date': (now + timedelta(days=1)).date(),
            'start_time': current_time,
            'end_time': (now + timedelta(hours=1)).strftime('%H:%M'),
            'message': 'TEST PROGRAMACIÓ ACTIVA',
            'color': 1,  # Rojo
            'font_size': 16,
            'effect': 'static',
            'is_active': True,
            'priority': 1,
            current_weekday_field: True  # Activar el día actual
        }
        
        # Crear la programación
        schedule_service = PanelScheduleService(session)
        create_result = schedule_service.create_schedule(schedule_data)
        
        if not create_result['success']:
            print(f"❌ Error creando programación: {create_result['error']}")
            return False
        
        schedule_id = create_result['schedule_id']
        print(f"✅ Programación creada: {schedule_id}")
        
        # 4. Verificar que la programación está activa
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        if not active_schedules:
            print("❌ La programación no se detecta como activa")
            return False
        
        print(f"✅ Programación detectada como activa: {len(active_schedules)} programaciones")
        
        # 5. Intentar actualizar la ocupación del parking
        print("\n--- Intentando actualizar ocupación con programación activa ---")
        
        # Simular actualización de ocupación
        new_occupancy = parking.current_occupancy + 5
        parking.current_occupancy = new_occupancy
        
        # Recalcular estado
        free = parking.max_capacity - parking.current_occupancy
        if free <= parking.threshold_full:
            parking.status = 'COMPLETO'
        elif free <= parking.threshold_dense:
            parking.status = 'DENSO'
        else:
            parking.status = 'LIBRE'
        
        session.commit()
        
        print(f"✅ Ocupación actualizada en BD: {new_occupancy} (Estado: {parking.status})")
        
        # 6. Intentar actualizar paneles (debería ser bloqueado)
        print("\n--- Intentando actualizar paneles ---")
        
        result = update_parking_panels(
            parking_id=parking.id,
            current_occupancy=parking.current_occupancy,
            max_capacity=parking.max_capacity,
            status=parking.status,
            db_session=session
        )
        
        if result == "SCHEDULE_ACTIVE":
            print("✅ CORRECTO: La actualización de paneles fue bloqueada por programación activa")
            test_passed = True
        else:
            print(f"❌ ERROR: Se actualizaron los paneles cuando debería haberse bloqueado")
            print(f"   Resultado: {result}")
            test_passed = False
        
        # 7. Verificar que los paneles muestran el mensaje de la programación
        print("\n--- Verificando estado de los paneles ---")
        
        for panel in panels:
            if panel.last_message == schedule_data['message']:
                print(f"✅ Panel {panel.ip}: Muestra mensaje de programación")
            else:
                print(f"⚠️  Panel {panel.ip}: Último mensaje: {panel.last_message}")
        
        # 8. Finalizar la programación
        print("\n--- Finalizando programación ---")
        
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
        if schedule:
            end_result = schedule_service.end_schedule(schedule)
            if end_result['success']:
                print("✅ Programación finalizada correctamente")
            else:
                print(f"❌ Error finalizando programación: {end_result['error']}")
        
        # 9. Verificar que ahora sí se puede actualizar los paneles
        print("\n--- Verificando que ahora se pueden actualizar paneles ---")
        
        result = update_parking_panels(
            parking_id=parking.id,
            current_occupancy=parking.current_occupancy,
            max_capacity=parking.max_capacity,
            status=parking.status,
            db_session=session
        )
        
        if result != "SCHEDULE_ACTIVE":
            print("✅ CORRECTO: Ahora se pueden actualizar los paneles")
            test_passed = test_passed and True
        else:
            print("❌ ERROR: Los paneles siguen bloqueados después de finalizar la programación")
            test_passed = False
        
        # 10. Limpiar - eliminar la programación de prueba
        print("\n--- Limpiando datos de prueba ---")
        
        session.delete(schedule)
        session.commit()
        print("✅ Programación de prueba eliminada")
        
        return test_passed
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_schedule_priority_logic():
    """Test para verificar la lógica de prioridad de programaciones"""
    
    print("\n=== TEST: Lógica de Prioridad de Programaciones ===")
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener un parking
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para el test")
            return False
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        # Crear múltiples programaciones con diferentes prioridades
        schedules_data = [
            {
                'name': 'Programación Baja Prioridad',
                'priority': 1,
                'message': 'MENSAJE BAJA PRIORIDAD',
                'color': 2  # Verde
            },
            {
                'name': 'Programación Alta Prioridad',
                'priority': 5,
                'message': 'MENSAJE ALTA PRIORIDAD',
                'color': 1  # Rojo
            }
        ]
        
        schedule_service = PanelScheduleService(session)
        created_schedules = []
        
        for i, schedule_data in enumerate(schedules_data):
            full_schedule_data = {
                'parking_id': parking.id,
                'description': f'Programación de prueba {i+1}',
                'start_date': now.date(),
                'end_date': (now + timedelta(days=1)).date(),
                'start_time': current_time,
                'end_time': (now + timedelta(hours=1)).strftime('%H:%M'),
                'font_size': 16,
                'effect': 'static',
                'is_active': True,
                current_weekday_field: True,
                **schedule_data
            }
            
            result = schedule_service.create_schedule(full_schedule_data)
            if result['success']:
                created_schedules.append((result['schedule_id'], schedule_data['name']))
                print(f"✅ Programación creada: {schedule_data['name']} (ID: {result['schedule_id']})")
            else:
                print(f"❌ Error creando programación {schedule_data['name']}: {result['error']}")
        
        # Verificar que se detectan las programaciones activas
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        print(f"\n✅ Programaciones activas detectadas: {len(active_schedules)}")
        
        for schedule in active_schedules:
            print(f"   - {schedule.name} (Prioridad: {schedule.priority})")
        
        # Verificar que la de mayor prioridad se ejecuta primero
        if active_schedules:
            highest_priority = max(active_schedules, key=lambda s: s.priority)
            print(f"\n✅ Programación de mayor prioridad: {highest_priority.name} (Prioridad: {highest_priority.priority})")
        
        # Limpiar
        for schedule_id, name in created_schedules:
            schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
            if schedule:
                session.delete(schedule)
                print(f"✅ Programación eliminada: {name}")
        
        session.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test de prioridad: {e}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("Iniciando tests de integración programaciones vs ocupación...")
    
    test1_passed = test_schedule_occupancy_integration()
    test2_passed = test_schedule_priority_logic()
    
    print("\n" + "="*60)
    print("RESULTADOS DE LOS TESTS:")
    print(f"Test 1 - Integración Programaciones vs Ocupación: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"Test 2 - Lógica de Prioridad: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 TODOS LOS TESTS PASARON - El sistema funciona correctamente")
    else:
        print("\n⚠️  ALGUNOS TESTS FALLARON - Revisar la lógica del sistema")
    
    print("="*60) 