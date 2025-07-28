#!/usr/bin/env python3
"""
Script para corregir mensajes de programaciones y forzar actualización de paneles
"""
import sys
import os
sys.path.append('src')

from models import PanelSchedule, Panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
import requests
import time

def fix_schedule_messages():
    """Corregir mensajes de programaciones activas"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("🔧 Corrigiendo mensajes de programaciones...")
    
    # Corregir el error tipográfico en la programación 35
    schedule_35 = session.query(PanelSchedule).filter(PanelSchedule.id == 35).first()
    if schedule_35 and schedule_35.message == "EN PROVRES ":
        schedule_35.message = "EN PROVES "
        print(f"✅ Corregido mensaje de programación {schedule_35.id}: {schedule_35.message}")
    
    # Asegurar que todas las programaciones EN PROVES tengan el formato correcto
    schedules = session.query(PanelSchedule).filter(
        PanelSchedule.name.like("%EN PROVES%")
    ).all()
    
    for schedule in schedules:
        if schedule.message != "EN PROVES ":
            old_message = schedule.message
            schedule.message = "EN PROVES "
            print(f"✅ Corregido mensaje de programación {schedule.id}: '{old_message}' -> '{schedule.message}'")
    
    session.commit()
    session.close()
    print("✅ Mensajes de programaciones corregidos")

def force_panel_updates():
    """Forzar actualización de todos los paneles con programaciones activas"""
    print("\n🔄 Forzando actualización de paneles...")
    
    # Obtener todos los paneles
    try:
        response = requests.get('http://localhost:6001/api/panels', timeout=10)
        if response.status_code == 200:
            panels = response.json()
            
            for panel in panels:
                if panel.get('active_schedule'):
                    schedule = panel['active_schedule']
                    panel_id = panel['id']
                    panel_name = panel['name']
                    schedule_message = schedule['message']
                    
                    print(f"📡 Enviando mensaje a {panel_name} (ID: {panel_id}): '{schedule_message}'")
                    
                    # Enviar mensaje al panel
                    try:
                        panel_response = requests.post(
                            f'http://localhost:6001/api/panels/{panel_id}/message',
                            json={'message': schedule_message},
                            timeout=5
                        )
                        
                        if panel_response.status_code == 200:
                            print(f"✅ Mensaje enviado exitosamente a {panel_name}")
                        else:
                            print(f"❌ Error enviando mensaje a {panel_name}: {panel_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ Error de conexión con {panel_name}: {e}")
                    
                    # Pequeña pausa entre envíos
                    time.sleep(0.5)
        else:
            print(f"❌ Error obteniendo paneles: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error conectando con la API: {e}")

def verify_corrections():
    """Verificar que las correcciones se aplicaron correctamente"""
    print("\n🔍 Verificando correcciones...")
    
    try:
        response = requests.get('http://localhost:6001/api/panels', timeout=10)
        if response.status_code == 200:
            panels = response.json()
            
            print("\n📊 Estado actual de los paneles:")
            print("=" * 80)
            
            for panel in panels:
                panel_name = panel['name']
                last_message = panel.get('last_message', 'Sin mensaje')
                active_schedule = panel.get('active_schedule')
                
                if active_schedule:
                    schedule_message = active_schedule['message']
                    status = "✅" if last_message == schedule_message else "❌"
                    print(f"{status} {panel_name}: '{last_message}' (debería ser: '{schedule_message}')")
                else:
                    print(f"⚠️  {panel_name}: '{last_message}' (sin programación activa)")
                    
    except Exception as e:
        print(f"❌ Error verificando correcciones: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando corrección de mensajes de programaciones")
    print("=" * 60)
    
    # 1. Corregir mensajes en base de datos
    fix_schedule_messages()
    
    # 2. Forzar actualización de paneles
    force_panel_updates()
    
    # 3. Verificar correcciones
    verify_corrections()
    
    print("\n✅ Proceso de corrección completado") 