#!/usr/bin/env python3
"""
Script temporal para verificar el protocolo del panel 172.20.4.52
"""

import sys
import os
sys.path.append('src')

from models import Panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def check_panel_protocol():
    """Verificar el protocolo del panel 172.20.4.52"""
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        panel = session.query(Panel).filter(Panel.ip == '172.20.4.52').first()
        
        if panel:
            print(f"Panel encontrado: {panel.name}")
            print(f"IP: {panel.ip}")
            print(f"Protocol Version: {panel.protocol_version}")
            print(f"Panel Type ID: {panel.panel_type_id}")
            print(f"Service Endpoint: {panel.service_endpoint}")
            print(f"Status: {panel.status}")
            
            if panel.panel_type:
                print(f"Panel Type: {panel.panel_type.name}")
                print(f"Panel Type Protocol: {panel.panel_type.protocol_type}")
            else:
                print("Panel Type: No asignado")
        else:
            print("Panel 172.20.4.52 no encontrado en la base de datos")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_panel_protocol() 