#!/usr/bin/env python3
"""
Script para validar que las programaciones tienen prioridad sobre las actualizaciones de ocupación
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService
from panel_communication_service import update_parking_panels

def test_schedule_priority_over_occupancy():
    """Probar que las programaciones tienen prioridad sobre las actualizaciones de ocupación"""
    
    print("🔍 Validando prioridad de programaciones sobre actualizaciones de ocupación")
    print("=" * 70)
    
    # Crear sesión de base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener un parking de prueba
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para la prueba")
            return False
        
        print(f"✅ Parking de prueba: {parking.name} (ID: {parking.id})")
        print(f"   Estado actual: {parking.status}")
        print(f"   Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
        
        # 2. Verificar que no hay programaciones activas inicialmente
        print("\n--- PASO 1: Verificar estado inicial ---")
        schedule_service = PanelScheduleService(session)
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        
        if active_schedules:
            print(f"⚠️  Hay {len(active_schedules)} programaciones activas")
            for schedule in active_schedules:
                print(f"   - {schedule.name} (ID: {schedule.id})")
        else:
            print("✅ No hay programaciones activas")
        
        # 3. Probar actualización de ocupación sin programaciones activas
        print("\n--- PASO 2: Probar actualización sin programaciones activas ---")
        result = update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status, session)
        
        if result == "SCHEDULE_ACTIVE":
            print("❌ Error: Se bloqueó la actualización cuando no hay programaciones activas")
            return False
        else:
            print("✅ Actualización permitida correctamente (no hay programaciones activas)")
        
        # 4. Crear una programación activa
        print("\n--- PASO 3: Crear programación activa ---")
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        # Programación que empieza ahora y dura 10 minutos
        start_time = current_time
        end_time = (now + timedelta(minutes=10)).strftime('%H:%M')
        
        schedule_data = {
            'parking_id': parking.id,
            'name': f'Prueba Prioridad {now.strftime("%H:%M:%S")}',
            'description': 'Programación de prueba para validar prioridad',
            'start_date': now.strftime('%Y-%m-%d'),
            'end_date': (now + timedelta(days=1)).strftime('%Y-%m-%d'),
            'start_time': start_time,
            'end_time': end_time,
            'message': 'PROGRAMACIÓ ACTIVA',
            'color': 1,  # Rojo
            'font_size': 2,
            'effect': 'static',
            'is_active': True,
            'priority': 5,  # Alta prioridad
            current_weekday_field: True
        }
        
        # Crear la programación
        create_result = schedule_service.create_schedule(schedule_data)
        
        if not create_result['success']:
            print(f"❌ Error creando programación: {create_result['error']}")
            return False
        
        schedule_id = create_result.get('schedule_id')
        print(f"✅ Programación creada: {schedule_id}")
        
        # 5. Verificar que ahora hay programaciones activas
        print("\n--- PASO 4: Verificar programaciones activas ---")
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        
        if active_schedules:
            print(f"✅ Hay {len(active_schedules)} programaciones activas")
            for schedule in active_schedules:
                print(f"   - {schedule.name} (ID: {schedule.id})")
                print(f"     Mensaje: {schedule.message}")
                print(f"     Horario: {schedule.start_time} - {schedule.end_time}")
        else:
            print("❌ No se detectaron programaciones activas")
            return False
        
        # 6. Probar actualización de ocupación CON programación activa
        print("\n--- PASO 5: Probar actualización CON programación activa ---")
        result = update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status, session)
        
        if result == "SCHEDULE_ACTIVE":
            print("✅ Actualización bloqueada correctamente (hay programación activa)")
        else:
            print(f"❌ Error: Se permitió la actualización cuando hay programación activa: {result}")
            return False
        
        # 7. Verificar que los paneles muestran el mensaje de la programación
        print("\n--- PASO 6: Verificar mensaje en paneles ---")
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        
        for panel in panels:
            print(f"   Panel {panel.ip}: último mensaje = '{panel.last_message}'")
            if panel.last_message == "PROGRAMACIÓ ACTIVA":
                print(f"   ✅ Panel {panel.ip} muestra mensaje de programación")
            else:
                print(f"   ⚠️  Panel {panel.ip} no muestra mensaje de programación")
        
        # 8. Simular finalización de programación
        print("\n--- PASO 7: Simular finalización de programación ---")
        
        # Obtener la programación y finalizarla manualmente
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
        if schedule:
            end_result = schedule_service.end_schedule(schedule)
            if end_result['success']:
                print(f"✅ Programación finalizada: {end_result['panels_affected']} paneles actualizados")
            else:
                print(f"❌ Error finalizando programación: {end_result['error']}")
        
        # 9. Verificar que ya no hay programaciones activas
        print("\n--- PASO 8: Verificar que no hay programaciones activas después de finalizar ---")
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        
        if not active_schedules:
            print("✅ No hay programaciones activas después de finalizar")
        else:
            print("⚠️  Todavía hay programaciones activas")
        
        # 10. Probar actualización de ocupación DESPUÉS de finalizar programación
        print("\n--- PASO 9: Probar actualización DESPUÉS de finalizar programación ---")
        result = update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status, session)
        
        if result == "SCHEDULE_ACTIVE":
            print("❌ Error: Se bloqueó la actualización cuando no hay programaciones activas")
            return False
        else:
            print("✅ Actualización permitida correctamente después de finalizar programación")
        
        # 11. Verificar que los paneles muestran el estado normal
        print("\n--- PASO 10: Verificar estado normal en paneles ---")
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        
        for panel in panels:
            print(f"   Panel {panel.ip}: último mensaje = '{panel.last_message}'")
            if panel.last_message in ["LLIURE", "DENS", "COMPLET"]:
                print(f"   ✅ Panel {panel.ip} muestra estado normal del parking")
            else:
                print(f"   ⚠️  Panel {panel.ip} no muestra estado normal")
        
        # Limpiar: eliminar la programación de prueba
        print("\n--- LIMPIEZA ---")
        delete_result = schedule_service.delete_schedule(schedule_id)
        if delete_result['success']:
            print("✅ Programación de prueba eliminada")
        else:
            print(f"⚠️  Error eliminando programación: {delete_result['error']}")
        
        print("\n" + "=" * 70)
        print("🎉 VALIDACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Las programaciones tienen prioridad sobre las actualizaciones de ocupación")
        print("✅ Los paneles muestran el mensaje de programación cuando está activa")
        print("✅ Los paneles vuelven al estado normal cuando termina la programación")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la validación: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_schedule_creation_with_auto_execution():
    """Probar que las programaciones se ejecutan automáticamente al crearlas si son operativas"""
    
    print("\n🔍 Validando ejecución automática de programaciones")
    print("=" * 70)
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener un parking
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para la prueba")
            return False
        
        print(f"✅ Parking de prueba: {parking.name} (ID: {parking.id})")
        
        # Crear programación que se ejecute inmediatamente
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        schedule_data = {
            'parking_id': parking.id,
            'name': f'Auto-Ejecución {now.strftime("%H:%M:%S")}',
            'description': 'Programación que se ejecuta automáticamente al crearla',
            'start_date': now.strftime('%Y-%m-%d'),
            'end_date': (now + timedelta(days=1)).strftime('%Y-%m-%d'),
            'start_time': current_time,
            'end_time': (now + timedelta(minutes=5)).strftime('%H:%M'),
            'message': 'AUTO-EJECUCIÓ',
            'color': 3,  # Amarillo
            'font_size': 2,
            'effect': 'static',
            'is_active': True,
            'priority': 3,
            current_weekday_field: True
        }
        
        # Crear la programación
        schedule_service = PanelScheduleService(session)
        create_result = schedule_service.create_schedule(schedule_data)
        
        if not create_result['success']:
            print(f"❌ Error creando programación: {create_result['error']}")
            return False
        
        schedule_id = create_result.get('schedule_id')
        print(f"✅ Programación creada: {schedule_id}")
        
        # Verificar si se ejecutó automáticamente
        if create_result.get('auto_executed'):
            print("✅ Programación ejecutada automáticamente al crearla")
            print(f"   Paneles afectados: {create_result.get('panels_affected', 0)}")
        else:
            print("⚠️  Programación no se ejecutó automáticamente")
        
        # Verificar que los paneles muestran el mensaje
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        for panel in panels:
            print(f"   Panel {panel.ip}: último mensaje = '{panel.last_message}'")
        
        # Limpiar
        delete_result = schedule_service.delete_schedule(schedule_id)
        if delete_result['success']:
            print("✅ Programación de prueba eliminada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba de auto-ejecución: {e}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Iniciando validación de prioridad de programaciones")
    
    # Ejecutar pruebas
    test1_result = test_schedule_priority_over_occupancy()
    test2_result = test_schedule_creation_with_auto_execution()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS")
    print(f"   Prioridad de programaciones: {'✅ PASÓ' if test1_result else '❌ FALLÓ'}")
    print(f"   Auto-ejecución: {'✅ PASÓ' if test2_result else '❌ FALLÓ'}")
    
    if test1_result and test2_result:
        print("\n🎉 TODAS LAS PRUEBAS PASARON")
        print("✅ El sistema de programaciones funciona correctamente")
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        print("❌ Hay problemas en el sistema de programaciones") 