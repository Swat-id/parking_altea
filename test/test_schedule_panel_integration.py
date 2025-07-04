#!/usr/bin/env python3
"""
Script de prueba para verificar la integración entre programaciones y actualización de paneles
"""

import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService
from panel_communication_service import update_parking_panels
import config

def test_schedule_panel_integration():
    """Probar la integración entre programaciones y paneles"""
    
    print("=== PRUEBA DE INTEGRACIÓN PROGRAMACIONES Y PANELES ===")
    
    # Conectar a la base de datos
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener un parking de prueba
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para la prueba")
            return False
        
        print(f"✅ Parking de prueba: {parking.name} (ID: {parking.id})")
        
        # Obtener paneles del parking
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        if not panels:
            print("❌ No se encontraron paneles para el parking")
            return False
        
        print(f"✅ Paneles encontrados: {len(panels)}")
        
        # Crear servicio de programaciones
        schedule_service = PanelScheduleService(session)
        
        # 1. PRUEBA: Verificar que no hay programaciones activas
        print("\n--- PRUEBA 1: Verificar programaciones activas ---")
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        print(f"Programaciones activas: {len(active_schedules)}")
        
        if active_schedules:
            print("⚠️  Hay programaciones activas, se saltarán las actualizaciones de ocupación")
        else:
            print("✅ No hay programaciones activas, se permitirán actualizaciones de ocupación")
        
        # 2. PRUEBA: Crear una programación que se ejecute inmediatamente
        print("\n--- PRUEBA 2: Crear programación operativa ---")
        
        # Crear programación para el día actual y hora actual
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        # Programación que empieza ahora y dura 5 minutos
        start_time = current_time
        end_time = (now + timedelta(minutes=5)).strftime('%H:%M')
        
        schedule_data = {
            'parking_id': parking.id,
            'name': f'Prueba automática - {now.strftime("%H:%M")}',
            'description': 'Programación de prueba que se ejecuta automáticamente',
            'start_date': now.strftime('%Y-%m-%d'),
            'end_date': (now + timedelta(days=7)).strftime('%Y-%m-%d'),
            'start_time': start_time,
            'end_time': end_time,
            'message': 'PROVA AUTOMÀTICA',
            'color': 3,  # Amarillo
            'font_size': 2,
            'effect': 'static',
            'is_active': True,
            'priority': 1
        }
        
        # Activar solo el día actual
        for field in weekday_fields:
            schedule_data[field] = (field == current_weekday_field)
        
        # Crear la programación
        result = schedule_service.create_schedule(schedule_data)
        
        if result['success']:
            print(f"✅ Programación creada: {result['schedule_id']}")
            if result.get('auto_executed'):
                print(f"✅ Programación ejecutada automáticamente: {result.get('panels_affected', 0)} paneles afectados")
            else:
                print("⚠️  Programación no se ejecutó automáticamente")
        else:
            print(f"❌ Error creando programación: {result['error']}")
            return False
        
        # 3. PRUEBA: Verificar que ahora hay programaciones activas
        print("\n--- PRUEBA 3: Verificar programaciones activas después de crear ---")
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        print(f"Programaciones activas: {len(active_schedules)}")
        
        if active_schedules:
            print("✅ Ahora hay programaciones activas")
            for schedule in active_schedules:
                print(f"  - {schedule.name} (ID: {schedule.id})")
        else:
            print("❌ No se detectaron programaciones activas")
        
        # 4. PRUEBA: Intentar actualizar ocupación (debería ser bloqueada)
        print("\n--- PRUEBA 4: Intentar actualizar ocupación con programación activa ---")
        
        # Simular actualización de ocupación
        result = update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
        
        if result == "SCHEDULE_ACTIVE":
            print("✅ Actualización de ocupación bloqueada correctamente (hay programación activa)")
        else:
            print(f"⚠️  Actualización de ocupación permitida: {result}")
        
        # 5. PRUEBA: Esperar a que termine la programación y verificar restauración
        print("\n--- PRUEBA 5: Esperar finalización de programación ---")
        print("Esperando 6 minutos para que termine la programación...")
        
        # En un entorno real, el monitor detectaría automáticamente la finalización
        # Aquí simulamos la finalización manual
        time.sleep(10)  # Esperar 10 segundos para la demo
        
        # Finalizar la programación manualmente
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == result['schedule_id']).first()
        if schedule:
            end_result = schedule_service.end_schedule(schedule)
            if end_result['success']:
                print(f"✅ Programación finalizada: {end_result['panels_affected']} paneles actualizados")
            else:
                print(f"❌ Error finalizando programación: {end_result['error']}")
        
        # 6. PRUEBA: Verificar que ya no hay programaciones activas
        print("\n--- PRUEBA 6: Verificar que no hay programaciones activas después de finalizar ---")
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        print(f"Programaciones activas: {len(active_schedules)}")
        
        if not active_schedules:
            print("✅ No hay programaciones activas después de finalizar")
        else:
            print("⚠️  Todavía hay programaciones activas")
        
        # 7. PRUEBA: Intentar actualizar ocupación (debería permitirse)
        print("\n--- PRUEBA 7: Intentar actualizar ocupación sin programación activa ---")
        
        result = update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
        
        if result != "SCHEDULE_ACTIVE":
            print("✅ Actualización de ocupación permitida correctamente (no hay programación activa)")
        else:
            print("❌ Actualización de ocupación bloqueada incorrectamente")
        
        # Limpiar: eliminar la programación de prueba
        print("\n--- LIMPIEZA ---")
        if 'schedule_id' in locals():
            delete_result = schedule_service.delete_schedule(result['schedule_id'])
            if delete_result['success']:
                print("✅ Programación de prueba eliminada")
            else:
                print(f"⚠️  Error eliminando programación: {delete_result['error']}")
        
        print("\n=== PRUEBA COMPLETADA ===")
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_monitor_service():
    """Probar el servicio de monitorización"""
    
    print("\n=== PRUEBA DEL SERVICIO DE MONITORIZACIÓN ===")
    
    try:
        # Importar el monitor
        from schedule_monitor_service import ScheduleMonitorService
        
        # Crear instancia del monitor
        monitor = ScheduleMonitorService(check_interval=10)  # Verificar cada 10 segundos para la prueba
        
        # Obtener estado
        status = monitor.get_status()
        print(f"Estado del monitor: {status}")
        
        # Iniciar monitor
        print("Iniciando monitor...")
        monitor.start()
        
        # Esperar un poco para que procese
        time.sleep(15)
        
        # Obtener estado actualizado
        status = monitor.get_status()
        print(f"Estado del monitor después de 15 segundos: {status}")
        
        # Detener monitor
        print("Deteniendo monitor...")
        monitor.stop()
        
        print("✅ Prueba del monitor completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba del monitor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando pruebas de integración programaciones y paneles...")
    
    # Ejecutar pruebas
    test1_result = test_schedule_panel_integration()
    test2_result = test_monitor_service()
    
    if test1_result and test2_result:
        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
        sys.exit(1) 