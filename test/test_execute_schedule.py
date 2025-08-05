#!/usr/bin/env python3
"""
Script para probar directamente la función execute_schedule
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from panel_schedule_service import PanelScheduleService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import PanelSchedule, Panel

def test_execute_schedule():
    """Probar directamente la función execute_schedule"""
    
    print("🔧 PRUEBA DIRECTA DE EXECUTE_SCHEDULE")
    print("=" * 50)
    
    # Crear sesión de base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener una programación activa
        schedule = session.query(PanelSchedule).filter(PanelSchedule.is_active == True).first()
        
        if not schedule:
            print("❌ No hay programaciones activas para probar")
            return
        
        print(f"📋 Probando programación ID {schedule.id}: '{schedule.message}'")
        print(f"   - Parking ID: {schedule.parking_id}")
        print(f"   - Mensaje: '{schedule.message}'")
        print(f"   - Color: {schedule.color}")
        print(f"   - Efecto: {schedule.effect}")
        
        # Verificar paneles del parking
        panels = session.query(Panel).filter(Panel.parking_id == schedule.parking_id).all()
        print(f"   - Paneles configurados: {len(panels)}")
        for panel in panels:
            print(f"     * {panel.ip}: '{panel.last_message}' (estado: {panel.status})")
        
        # Crear servicio y ejecutar programación
        schedule_service = PanelScheduleService(session)
        
        print(f"\n🚀 Ejecutando programación...")
        result = schedule_service.execute_schedule(schedule)
        
        print(f"📊 Resultado de execute_schedule:")
        print(f"   - Success: {result.get('success')}")
        print(f"   - Paneles afectados: {result.get('panels_affected', 0)}")
        if not result.get('success'):
            print(f"   - Error: {result.get('error')}")
        
        # Verificar estado de paneles después de la ejecución
        print(f"\n🔍 Estado de paneles después de la ejecución:")
        session.refresh(schedule)
        for panel in panels:
            session.refresh(panel)
            print(f"   - {panel.ip}: '{panel.last_message}' (actualizado: {panel.last_update})")
        
        # Verificar logs recientes
        from models import PanelScheduleLog
        recent_logs = session.query(PanelScheduleLog).filter(
            PanelScheduleLog.schedule_id == schedule.id,
            PanelScheduleLog.execution_type == 'started'
        ).order_by(PanelScheduleLog.executed_at.desc()).limit(3).all()
        
        print(f"\n📋 Logs recientes de esta programación:")
        for log in recent_logs:
            print(f"   - {log.executed_at}: '{log.message_sent}' enviado a {log.panels_affected} paneles")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_execute_schedule() 