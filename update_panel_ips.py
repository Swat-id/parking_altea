#!/usr/bin/env python3
"""
Script para actualizar las IPs de los paneles en la base de datos
"""

import sys
import os
sys.path.append('src')

from models import Session, Panel

def update_panel_ips():
    """Actualizar las IPs de los paneles"""
    session = Session()
    
    # Mapeo de paneles y sus IPs
    panel_ips = {
        7: "172.20.4.52",  # BELLES ARTS 2
        # Agregar más paneles según sea necesario
    }
    
    try:
        for panel_id, ip in panel_ips.items():
            panel = session.query(Panel).filter_by(id=panel_id).first()
            if panel:
                panel.ip = ip
                print(f"Panel {panel_id} ({panel.name}) actualizado con IP {ip}")
            else:
                print(f"Panel {panel_id} no encontrado")
        
        session.commit()
        print("✅ IPs actualizadas correctamente")
        
    except Exception as e:
        print(f"❌ Error actualizando IPs: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    update_panel_ips() 