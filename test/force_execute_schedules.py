#!/usr/bin/env python3
"""
Script para forzar la ejecución de programaciones activas y verificar mensajes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService
from datetime import datetime

def force_execute_schedules():
    """Forzar la ejecución de programaciones activas"""
    
    print("🚀 FORZANDO EJECUCIÓN DE PROGRAMACIONES ACTIVAS")
    print("=" * 60)
    
    # Crear sesión de base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todas las programaciones activas
        schedule_service = PanelScheduleService(session)
        result = schedule_service.get_schedules(active_only=True)
        
        if not result['success']:
            print(f"❌ Error obteniendo programaciones: {result['error']}")
            return
        
        schedules = result['schedules']
        print(f"📋 Total de programaciones activas: {len(schedules)}")
        
        current_time = datetime.now().astimezone()
        current_time_str = current_time.strftime('%H:%M')
        current_weekday = current_time.weekday()
        
        weekday_fields = {
            0: 'monday',
            1: 'tuesday', 
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturday',
            6: 'sunday'
        }
        current_weekday_field = weekday_fields.get(current_weekday, 'monday')
        
        print(f"🕐 Hora actual: {current_time_str}")
        print(f"📅 Día actual: {current_weekday_field}")
        
        executed_count = 0
        
        for schedule_data in schedules:
            # Verificar si debe ejecutarse ahora
            should_execute = (
                schedule_data['is_active'] and
                schedule_data.get(current_weekday_field, False) and
                schedule_data['start_time'] <= current_time_str <= schedule_data['end_time']
            )
            
            if should_execute:
                print(f"\n✅ Ejecutando programación ID {schedule_data['id']}: '{schedule_data['message']}'")
                
                # Obtener la programación completa
                schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_data['id']).first()
                if schedule:
                    # Ejecutar la programación
                    result = schedule_service.execute_schedule(schedule)
                    
                    if result['success']:
                        executed_count += 1
                        print(f"   ✅ Ejecutada exitosamente - {result.get('panels_affected', 0)} paneles actualizados")
                    else:
                        print(f"   ❌ Error ejecutando: {result.get('error', 'Error desconocido')}")
                else:
                    print(f"   ❌ Programación no encontrada en BD")
            else:
                print(f"\n❌ Programación ID {schedule_data['id']} NO debe ejecutarse ahora:")
                print(f"   - Activa: {schedule_data['is_active']}")
                print(f"   - Día {current_weekday_field}: {schedule_data.get(current_weekday_field, False)}")
                print(f"   - Horario: {schedule_data['start_time']} - {schedule_data['end_time']}")
        
        print(f"\n📊 Resumen: {executed_count} programaciones ejecutadas")
        
        # Verificar estado de paneles después de la ejecución
        print(f"\n🔍 Verificando estado de paneles después de la ejecución:")
        parkings = session.query(Parking).all()
        
        for parking in parkings:
            panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
            if panels:
                print(f"\n🏢 {parking.name}:")
                for panel in panels:
                    print(f"   - {panel.ip}: '{panel.last_message}' (actualizado: {panel.last_update})")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    force_execute_schedules() 