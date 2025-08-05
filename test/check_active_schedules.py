#!/usr/bin/env python3
"""
Script temporal para verificar programaciones activas y mensajes enviados a paneles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Parking, Panel, PanelSchedule, PanelScheduleLog
from panel_schedule_service import PanelScheduleService
from datetime import datetime

def check_active_schedules():
    """Verificar programaciones activas y mensajes enviados"""
    
    print("🔍 VERIFICACIÓN DE PROGRAMACIONES ACTIVAS Y MENSAJES A PANELES")
    print("=" * 70)
    
    # Crear sesión de base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener todos los parkings
        parkings = session.query(Parking).all()
        print(f"📊 Encontrados {len(parkings)} parkings en el sistema")
        
        for parking in parkings:
            print(f"\n🏢 PARKING: {parking.name} (ID: {parking.id})")
            print("-" * 50)
            
            # 2. Verificar programaciones activas
            schedule_service = PanelScheduleService(session)
            active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
            
            if active_schedules:
                print(f"   ✅ PROGRAMACIONES ACTIVAS ENCONTRADAS: {len(active_schedules)}")
                for i, schedule in enumerate(active_schedules, 1):
                    print(f"      {i}. ID: {schedule.id} - Mensaje: '{schedule.message}'")
                    print(f"         Horario: {schedule.start_time} - {schedule.end_time}")
                    print(f"         Color: {schedule.color}, Efecto: {schedule.effect}")
                    print(f"         Días activos: {get_active_days(schedule)}")
                
                # 3. Verificar paneles del parking
                panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
                print(f"\n   📺 Paneles configurados: {len(panels)}")
                
                for panel in panels:
                    print(f"      - {panel.ip}: último mensaje = '{panel.last_message}'")
                    print(f"        Última actualización: {panel.last_update}")
                    print(f"        Estado: {panel.status}")
                
                # 4. Verificar logs de programaciones recientes
                print(f"\n   📋 Logs de programaciones recientes:")
                recent_logs = session.query(PanelScheduleLog).filter(
                    PanelScheduleLog.parking_id == parking.id,
                    PanelScheduleLog.execution_type == 'started'
                ).order_by(PanelScheduleLog.executed_at.desc()).limit(5).all()
                
                if recent_logs:
                    for log in recent_logs:
                        print(f"      - {log.executed_at}: '{log.message_sent}' enviado a {log.panels_affected} paneles")
                else:
                    print(f"      - No hay logs recientes de programaciones")
                
            else:
                print(f"   ❌ NO HAY PROGRAMACIONES ACTIVAS")
                
                # Verificar paneles sin programación activa
                panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
                print(f"\n   📺 Paneles configurados: {len(panels)}")
                
                for panel in panels:
                    print(f"      - {panel.ip}: último mensaje = '{panel.last_message}'")
                    print(f"        Última actualización: {panel.last_update}")
                    print(f"        Estado: {panel.status}")
        
        print(f"\n" + "=" * 70)
        print("✅ VERIFICACIÓN COMPLETADA")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def get_active_days(schedule):
    """Obtener los días activos de una programación"""
    days = []
    if schedule.monday: days.append("Lun")
    if schedule.tuesday: days.append("Mar")
    if schedule.wednesday: days.append("Mié")
    if schedule.thursday: days.append("Jue")
    if schedule.friday: days.append("Vie")
    if schedule.saturday: days.append("Sáb")
    if schedule.sunday: days.append("Dom")
    return ", ".join(days) if days else "Ninguno"

if __name__ == "__main__":
    check_active_schedules() 