#!/usr/bin/env python3
"""
Script para probar la comunicación con cada panel enviando su IP
y validar que la comunicación funciona correctamente
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Panel
from config import DB_URL
from datetime import datetime
import requests
import time

def test_panel_communication():
    """Probar la comunicación con cada panel enviando su IP"""
    
    print("=" * 60)
    print("🔍 PRUEBA DE COMUNICACIÓN CON PANELES")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los paneles
        panels = session.query(Panel).all()
        print(f"\n📺 PANELES CONFIGURADOS: {len(panels)}")
        print("-" * 60)
        
        if len(panels) == 0:
            print("❌ No hay paneles configurados en la base de datos")
            return
        
        successful_tests = 0
        failed_tests = 0
        
        for panel in panels:
            print(f"\n🖥️  Probando panel: {panel.name}")
            print(f"   IP: {panel.ip}")
            print(f"   Parking: {panel.parking.name if panel.parking else 'No asignado'}")
            print(f"   Estado actual: {panel.status}")
            
            # Mensaje de prueba con la IP del panel
            test_message = f"TEST: {panel.ip}"
            
            try:
                # Enviar mensaje de prueba
                print(f"   📤 Enviando mensaje: '{test_message}'")
                
                # Usar la función send_to_panel del sistema
                from panel_client import send_to_panel
                
                start_time = time.time()
                success = send_to_panel(panel.ip, test_message)
                response_time = (time.time() - start_time) * 1000  # en ms
                
                if success:
                    print(f"   ✅ ÉXITO - Respuesta en {response_time:.1f}ms")
                    successful_tests += 1
                    
                    # Actualizar estado del panel en la BD
                    panel.status = 'ONLINE'
                    panel.last_message = test_message
                    panel.last_update = datetime.now()
                    
                else:
                    print(f"   ❌ FALLO - Sin respuesta")
                    failed_tests += 1
                    
                    # Actualizar estado del panel en la BD
                    panel.status = 'OFFLINE'
                    panel.last_update = datetime.now()
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                failed_tests += 1
                
                # Actualizar estado del panel en la BD
                panel.status = 'OFFLINE'
                panel.last_update = datetime.now()
            
            # Pausa entre pruebas para no sobrecargar
            time.sleep(1)
        
        # Guardar cambios en la base de datos
        session.commit()
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        print(f"✅ Pruebas exitosas: {successful_tests}")
        print(f"❌ Pruebas fallidas: {failed_tests}")
        print(f"📺 Total paneles: {len(panels)}")
        
        if successful_tests == len(panels):
            print("\n🎯 TODOS LOS PANELES FUNCIONAN CORRECTAMENTE")
        elif successful_tests > 0:
            print(f"\n⚠️  {failed_tests} PANELES CON PROBLEMAS")
            print("   Revisar conectividad y configuración de los paneles fallidos")
        else:
            print("\n🚨 NINGÚN PANEL RESPONDE")
            print("   Verificar configuración de red y estado de los paneles")
        
        # Mostrar estado final de cada panel
        print(f"\n📋 ESTADO FINAL DE PANELES")
        print("-" * 60)
        
        for panel in panels:
            status_icon = "🟢" if panel.status == "ONLINE" else "🔴"
            print(f"{status_icon} {panel.name} ({panel.ip}) - {panel.status}")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_panel_communication() 