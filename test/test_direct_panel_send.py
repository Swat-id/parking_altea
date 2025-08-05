#!/usr/bin/env python3
"""
Script para probar el envío directo de mensajes a los paneles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from panel_communication_service import PanelCommunicationService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from models import Panel
import requests
import json

def test_direct_panel_send():
    """Probar envío directo de mensajes a paneles"""
    
    print("🔧 PRUEBA DE ENVÍO DIRECTO A PANELES")
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
        
        # 1. Probar conexión con la API
        print(f"\n🔌 Probando conexión con API de paneles...")
        connection_test = panel_service.test_connection()
        if connection_test['success']:
            print(f"   ✅ API funcionando: {connection_test['message']}")
        else:
            print(f"   ❌ Error API: {connection_test['message']}")
            return
        
        # 2. Probar envío directo a cada panel
        for panel in panels:
            print(f"\n🔧 Probando panel {panel.ip}:")
            print(f"   - Estado: {panel.status}")
            print(f"   - Último mensaje: '{panel.last_message}'")
            print(f"   - Protocolo: {panel.protocol_version or 'old'}")
            
            # Probar envío de mensaje de programación
            try:
                result = panel_service.send_custom_text(
                    panel_ip=panel.ip,
                    text="EN PROVES",
                    color=1,  # Rojo
                    font_size=2,  # 16px
                    effect=2  # Estático
                )
                
                if result.get('success'):
                    print(f"   ✅ Mensaje enviado exitosamente")
                    print(f"   📋 Protocolo usado: {result.get('protocol')}")
                    print(f"   📋 Texto enviado: {result.get('texts')}")
                    
                    # Verificar si el panel se actualizó en la BD
                    session.refresh(panel)
                    print(f"   📋 Panel actualizado: '{panel.last_message}'")
                else:
                    print(f"   ❌ Error enviando mensaje: {result.get('message')}")
                    print(f"   📋 Respuesta completa: {result}")
                    
            except Exception as e:
                print(f"   ❌ Excepción enviando mensaje: {e}")
                import traceback
                traceback.print_exc()
        
        # 3. Probar envío directo a la API
        print(f"\n🔧 Probando envío directo a la API...")
        test_payload = {
            "panels": [
                {
                    "ip": "172.20.4.53",  # Panel de ejemplo
                    "port": 5200,
                    "protocol": "old",
                    "windows": [
                        {
                            "id": 0,
                            "text": "TEST API",
                            "color": 2,
                            "fontSize": 2,
                            "effect": "fijo",
                            "stayTime": 0,
                            "alignmentH": 0,
                            "alignmentV": 0
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                "http://localhost:8888/api/v1/panels/send",
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"   📋 Status Code: {response.status_code}")
            print(f"   📋 Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   📋 JSON Response: {json.dumps(result, indent=2)}")
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error en envío directo: {e}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_direct_panel_send() 