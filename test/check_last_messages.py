#!/usr/bin/env python3
"""
Script temporal para verificar si los campos last_message se están actualizando correctamente
"""

import sys
import os
sys.path.append('src')

from models import Panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def check_last_messages():
    """Verificar si los campos last_message se están actualizando correctamente"""
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar paneles PITERES específicos
        piteres_ips = ["172.20.8.50", "172.20.8.51"]
        panels = session.query(Panel).filter(Panel.ip.in_(piteres_ips)).all()
        
        print("PANELES PITERES - ÚLTIMOS MENSAJES:")
        print("-" * 60)
        
        for panel in panels:
            print(f"IP: {panel.ip}")
            print(f"Último mensaje: {panel.last_message}")
            print(f"Última actualización: {panel.last_update}")
            print(f"Protocolo: {panel.protocol_version}")
            print("-" * 30)
        
        # Verificar todos los paneles con sus últimos mensajes
        all_panels = session.query(Panel).all()
        print(f"\nTODOS LOS PANELES - ÚLTIMOS MENSAJES:")
        print("-" * 60)
        
        for panel in all_panels:
            print(f"ID: {panel.id}, IP: {panel.ip}, Mensaje: {panel.last_message}, Actualización: {panel.last_update}")
        
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        session.close()

if __name__ == "__main__":
    check_last_messages() 