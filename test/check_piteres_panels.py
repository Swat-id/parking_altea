#!/usr/bin/env python3
"""
Script temporal para verificar específicamente los paneles PITERES que están fallando
"""

import sys
import os
sys.path.append('src')

from models import Panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def check_piteres_panels():
    """Verificar específicamente los paneles PITERES que están fallando"""
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar paneles PITERES específicos
        piteres_ips = ["172.20.8.50", "172.20.8.51"]
        panels = session.query(Panel).filter(Panel.ip.in_(piteres_ips)).all()
        
        print("PANELES PITERES:")
        print("-" * 60)
        
        for panel in panels:
            print(f"ID: {panel.id}")
            print(f"Nombre: {panel.name}")
            print(f"IP: {panel.ip}")
            print(f"Protocolo: {panel.protocol_version}")
            print(f"Estado: {panel.status}")
            print(f"Parking ID: {panel.parking_id}")
            print(f"Último mensaje: {panel.last_message}")
            print(f"Última actualización: {panel.last_update}")
            print("-" * 30)
        
        # Verificar si hay otros paneles con protocolo 'new'
        new_protocol_panels = session.query(Panel).filter(Panel.protocol_version == 'new').all()
        print(f"\nPANELES CON PROTOCOLO 'new':")
        print("-" * 60)
        
        for panel in new_protocol_panels:
            print(f"ID: {panel.id}, Nombre: {panel.name}, IP: {panel.ip}, Protocolo: {panel.protocol_version}")
        
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        session.close()

if __name__ == "__main__":
    check_piteres_panels() 