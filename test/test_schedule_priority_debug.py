#!/usr/bin/env python3
"""
Script para debuggear el problema de prioridad de programaciones
"""

import sys
import os
sys.path.append('src')

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService
from panel_communication_service import update_parking_panels

def debug_schedule_priority():
    """Debuggear el problema de prioridad de programaciones"""
    
    print("🔍 Debuggeando problema de prioridad de programaciones")
    print("=" * 70)
    
    # Crear sesión de base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener un parking con paneles
        parking = session.query(Parking).filter(Parking.id == 1).first()  # P. Ciutat Esportiva
        if not parking:
            print("❌ No se encontró el parking de prueba (ID: 1)")
            return False
        
        print(f"✅ Parking de prueba: {parking.name} (ID: {parking.id})")
        print(f"   Estado actual: {parking.status}")
        print(f"   Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
        
        # 2. Verificar paneles del parking
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        print(f"   Paneles: {len(panels)}")
        for panel in panels:
            print(f"     - {panel.ip} ({panel.name}) - Último mensaje: '{panel.last_message}'")
        
        # 3. Verificar programaciones activas
        print("\n--- PASO 1: Verificar programaciones activas ---")
        schedule_service = PanelScheduleService(session)
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        
        print(f"Programaciones activas encontradas: {len(active_schedules)}")
        for schedule in active_schedules:
            print(f"  - {schedule.name} (ID: {schedule.id})")
            print(f"    Mensaje: {schedule.message}")
            print(f"    Horario: {schedule.start_time} - {schedule.end_time}")
            print(f"    Activa: {schedule.is_active}")
        
        # 4. Crear una programación activa si no hay ninguna
        if not active_schedules:
            print("\n--- PASO 2: Crear programación activa ---")
            
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            current_weekday = now.weekday()
            
            weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            current_weekday_field = weekday_fields[current_weekday]
            
            # Programación que empieza ahora y dura 15 minutos
            start_time = current_time
            end_time = (now + timedelta(minutes=15)).strftime('%H:%M')
            
            schedule_data = {
                'parking_id': parking.id,
                'name': f'Debug Prioridad {now.strftime("%H:%M:%S")}',
                'description': 'Programación de debug para validar prioridad',
                'start_date': now.strftime('%Y-%m-%d'),
                'end_date': (now + timedelta(days=1)).strftime('%Y-%m-%d'),
                'start_time': start_time,
                'end_time': end_time,
                'message': 'DEBUG PROGRAMACIÓ',
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
            
            # Verificar que ahora hay programaciones activas
            active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
            print(f"Programaciones activas después de crear: {len(active_schedules)}")
        
        # 5. Simular llamada a update_parking_panels (como lo hace camera_server.py)
        print("\n--- PASO 3: Simular llamada a update_parking_panels ---")
        
        # Simular exactamente la llamada que hace camera_server.py
        print("Llamando a update_parking_panels...")
        result = update_parking_panels(
            parking.id, 
            parking.current_occupancy, 
            parking.max_capacity, 
            parking.status,
            session
        )
        
        print(f"Resultado de update_parking_panels: {result}")
        
        if result == "SCHEDULE_ACTIVE":
            print("✅ CORRECTO: Se detectó programación activa y se bloqueó la actualización")
        else:
            print(f"❌ PROBLEMA: Se permitió la actualización cuando hay programación activa")
            print(f"   Resultado: {result}")
        
        # 6. Verificar estado de los paneles después de la llamada
        print("\n--- PASO 4: Verificar estado de paneles después de la llamada ---")
        session.refresh(parking)
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        
        for panel in panels:
            print(f"   Panel {panel.ip}: último mensaje = '{panel.last_message}'")
            if panel.last_message == "DEBUG PROGRAMACIÓ":
                print(f"   ✅ Panel {panel.ip} mantiene mensaje de programación")
            elif panel.last_message in ["LLIURE", "DENS", "COMPLET"]:
                print(f"   ❌ Panel {panel.ip} muestra estado en lugar de programación")
            else:
                print(f"   ⚠️  Panel {panel.ip} muestra mensaje inesperado")
        
        # 7. Verificar logs del sistema
        print("\n--- PASO 5: Verificar logs del sistema ---")
        print("Ejecuta manualmente: journalctl -u parking-api --no-pager -n 20 | grep -E '(Active schedules|Programación|panel update)'")
        
        # 8. Limpiar programación de prueba
        if 'schedule_id' in locals():
            print("\n--- LIMPIEZA ---")
            delete_result = schedule_service.delete_schedule(schedule_id)
            if delete_result['success']:
                print("✅ Programación de debug eliminada")
            else:
                print(f"⚠️  Error eliminando programación: {delete_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el debug: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_direct_schedule_check():
    """Probar directamente la verificación de programaciones activas"""
    
    print("\n🔍 Probando verificación directa de programaciones activas")
    print("=" * 70)
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener parking
        parking = session.query(Parking).filter(Parking.id == 1).first()
        if not parking:
            print("❌ No se encontró el parking de prueba")
            return False
        
        # Crear servicio de programaciones
        schedule_service = PanelScheduleService(session)
        
        # Verificar programaciones activas
        active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
        
        print(f"Parking: {parking.name} (ID: {parking.id})")
        print(f"Programaciones activas: {len(active_schedules)}")
        
        for schedule in active_schedules:
            print(f"  - {schedule.name} (ID: {schedule.id})")
            print(f"    Mensaje: {schedule.message}")
            print(f"    Horario: {schedule.start_time} - {schedule.end_time}")
            print(f"    Fechas: {schedule.start_date} - {schedule.end_date}")
            print(f"    Activa: {schedule.is_active}")
            print(f"    Prioridad: {schedule.priority}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación directa: {e}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Iniciando debug de prioridad de programaciones")
    
    # Ejecutar debug principal
    debug_result = debug_schedule_priority()
    
    # Ejecutar verificación directa
    direct_result = test_direct_schedule_check()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE DEBUG")
    print(f"   Debug principal: {'✅ PASÓ' if debug_result else '❌ FALLÓ'}")
    print(f"   Verificación directa: {'✅ PASÓ' if direct_result else '❌ FALLÓ'}")
    
    if debug_result and direct_result:
        print("\n🎉 DEBUG COMPLETADO")
        print("✅ El sistema debería funcionar correctamente")
    else:
        print("\n⚠️  PROBLEMAS DETECTADOS")
        print("❌ Hay problemas en el sistema de programaciones") 