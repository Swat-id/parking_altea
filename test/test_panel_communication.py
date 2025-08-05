#!/usr/bin/env python3
"""
Script para probar la comunicación directa con los paneles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from panel_communication_service import PanelCommunicationService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Panel

def test_panel_communication():
    """Probar comunicación con paneles"""
    
    print("🔧 PRUEBA DE COMUNICACIÓN CON PANELES")
    print("=" * 50)
    
    # Crear sesión de base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los paneles
        panels = session.query(Panel).all()
        print(f"📺 Encontrados {len(panels)} paneles en el sistema")
        
        # Crear servicio de comunicación
        panel_service = PanelCommunicationService()
        
        for panel in panels:
            print(f"\n🔧 Probando panel {panel.ip}:")
            print(f"   - Estado: {panel.status}")
            print(f"   - Último mensaje: '{panel.last_message}'")
            print(f"   - Última actualización: {panel.last_update}")
            
            # Probar envío de mensaje de prueba
            try:
                result = panel_service.send_custom_text(
                    panel_ip=panel.ip,
                    text="TEST PANEL",
                    color=2,  # Verde
                    font_size=2,
                    effect=2  # Estático
                )
                
                if result.get('success'):
                    print(f"   ✅ Mensaje enviado exitosamente")
                    print(f"   📋 Respuesta: {result}")
                else:
                    print(f"   ❌ Error enviando mensaje: {result.get('message', 'Error desconocido')}")
                    print(f"   📋 Respuesta completa: {result}")
                    
            except Exception as e:
                print(f"   ❌ Excepción enviando mensaje: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_panel_communication() 