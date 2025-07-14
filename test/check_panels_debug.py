#!/usr/bin/env python3
"""
Script temporal para verificar el estado de los paneles y debuggear el problema
"""

import sys
import os
sys.path.append('src')

from src.models import Panel, PanelSchedule
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import config

def check_panels_debug():
    """Verificar el estado de los paneles y debuggear el problema"""
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los paneles
        panels = session.query(Panel).all()
        print("PANELES:")
        print("-" * 60)
        
        for panel in panels:
            print(f"ID: {panel.id}, Nombre: {panel.name}, IP: {panel.ip}, Estado: {panel.status}, Parking: {panel.parking_id}")
        
        # Contar por estado
        online_panels = session.query(Panel).filter(Panel.status == 'ONLINE').count()
        other_panels = session.query(Panel).filter(Panel.status != 'ONLINE').count()
        
        print(f"\nRESUMEN:")
        print(f"Paneles ONLINE: {online_panels}")
        print(f"Paneles otros estados: {other_panels}")
        print(f"Total paneles: {len(panels)}")
        
        # Verificar programaciones activas
        schedules = session.query(PanelSchedule).filter(PanelSchedule.is_active == True).all()
        print(f"\nPROGRAMACIONES ACTIVAS:")
        print("-" * 60)
        
        for schedule in schedules:
            # Contar paneles del parking de esta programación
            parking_panels = session.query(Panel).filter(Panel.parking_id == schedule.parking_id).all()
            online_parking_panels = session.query(Panel).filter(
                and_(Panel.parking_id == schedule.parking_id, Panel.status == 'ONLINE')
            ).all()
            
            print(f"Programación ID: {schedule.id}, Nombre: {schedule.name}")
            print(f"  Parking ID: {schedule.parking_id}")
            print(f"  Paneles totales del parking: {len(parking_panels)}")
            print(f"  Paneles ONLINE del parking: {len(online_parking_panels)}")
            print(f"  Estados de paneles: {[p.status for p in parking_panels]}")
            print()
        
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        session.close()

if __name__ == "__main__":
    check_panels_debug() 