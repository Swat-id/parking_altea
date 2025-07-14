#!/usr/bin/env python3
"""
Script temporal para verificar el estado de los paneles
"""

import sys
import os
sys.path.append('src')

from src.models import Panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def check_panels_status():
    """Verificar el estado de los paneles"""
    
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
        offline_panels = session.query(Panel).filter(Panel.status == 'OFFLINE').count()
        other_panels = session.query(Panel).filter(Panel.status.notin_(['ONLINE', 'OFFLINE'])).count()
        
        print(f"\nRESUMEN:")
        print(f"Online: {online_panels}")
        print(f"Offline: {offline_panels}")
        print(f"Otros estados: {other_panels}")
        print(f"Total: {len(panels)}")
        
        # Verificar paneles por parking
        print(f"\nPANELES POR PARKING:")
        parkings = session.query(Panel.parking_id).distinct().all()
        
        for parking_id in parkings:
            parking_panels = session.query(Panel).filter(Panel.parking_id == parking_id[0]).all()
            online_count = sum(1 for p in parking_panels if p.status == 'ONLINE')
            print(f"Parking {parking_id[0]}: {len(parking_panels)} paneles total, {online_count} online")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_panels_status() 