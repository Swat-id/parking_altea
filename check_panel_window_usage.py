#!/usr/bin/env python3
"""
Script para analizar qué ventana se está usando en los envíos a paneles
Analiza los logs y el código para determinar qué window_id se está utilizando
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Panel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_panel_window_usage():
    """Analiza qué ventana se está usando en los envíos a paneles"""
    
    print("=" * 80)
    print("ANÁLISIS DE USO DE VENTANAS EN ENVÍOS A PANELES")
    print("=" * 80)
    print()
    
    # Importar configuración
    import config
    
    # Conectar a la base de datos
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los paneles
        panels = session.query(Panel).all()
        
        print(f"Total de paneles encontrados: {len(panels)}")
        print()
        
        # Analizar cada panel
        for panel in panels:
            print(f"Panel: {panel.name} (IP: {panel.ip})")
            print(f"  - Tipo: {panel.panel_type.name if panel.panel_type else 'N/A'}")
            print(f"  - Protocolo: {panel.protocol_version or 'old'}")
            print(f"  - Soporta múltiples ventanas: {panel.supports_multiple_windows()}")
            
            # Verificar última actualización por ventana
            if hasattr(panel, 'get_last_message_for_window'):
                msg_0 = panel.get_last_message_for_window(0)
                msg_1 = panel.get_last_message_for_window(1) if panel.supports_multiple_windows() else None
                
                print(f"  - Último mensaje ventana 0: {msg_0 or 'N/A'}")
                if msg_1:
                    print(f"  - Último mensaje ventana 1: {msg_1}")
            
            print()
        
        # Analizar código de envío
        print("=" * 80)
        print("ANÁLISIS DEL CÓDIGO DE ENVÍO")
        print("=" * 80)
        print()
        
        # Verificar panel_communication_service.py
        print("1. PanelCommunicationService:")
        print("   - send_custom_text(): Usa ventana 0 por defecto (implícito)")
        print("   - send_custom_text_to_window(window_id): Usa la ventana especificada")
        print()
        
        # Verificar api_server.py
        print("2. API Server (/panel/<id>/message):")
        print("   - Parámetro 'window' (default: 0)")
        print("   - Si window == 1 y panel soporta múltiples ventanas:")
        print("     → Usa send_custom_text_to_window(window_id=1)")
        print("   - Si window == 0 o panel no soporta múltiples ventanas:")
        print("     → Usa send_custom_text() (ventana 0)")
        print()
        
        # Verificar nuevo servicio de protocolo
        print("3. Nuevo Panel Protocol Service (puerto 7110):")
        print("   - Endpoint: /api/v1/panels/send-text")
        print("   - Parámetro 'window_id' (default: 0)")
        print("   - Envía directamente a la ventana especificada")
        print()
        
        # Verificar qué servicio se está usando
        print("=" * 80)
        print("SERVICIO ACTUALMENTE EN USO")
        print("=" * 80)
        print()
        print("PanelCommunicationService usa:")
        print("  - API URL: http://localhost:8888/api/v1/panels/send")
        print("  - Este es el servicio PanelSender (puerto 8888)")
        print()
        print("Nuevo Panel Protocol Service:")
        print("  - API URL: http://localhost:7110/api/v1/panels/send-text")
        print("  - Este es el nuevo servicio (puerto 7110)")
        print()
        print("NOTA: El servicio actual (PanelSender en 8888) NO es el nuevo")
        print("      servicio de protocolo que creamos (puerto 7110).")
        print()
        
    finally:
        session.close()

if __name__ == '__main__':
    analyze_panel_window_usage()

