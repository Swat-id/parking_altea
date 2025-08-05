#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas con mensajes de paneles
Analiza por qué se está enviando "COMPLET" incorrectamente
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import config
from models import Parking, Panel, PanelSchedule, CameraParking, Access
from panel_schedule_service import PanelScheduleService
from panel_communication_service import update_parking_panels

def diagnose_panel_messages():
    """Diagnóstico completo de mensajes de paneles"""
    print("🔍 DIAGNÓSTICO DE MENSAJES DE PANELES")
    print("=" * 50)
    
    # Configurar conexión a BD
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Verificar estado actual de todos los parkings
        print("\n📊 ESTADO ACTUAL DE PARKINGS:")
        print("-" * 30)
        
        parkings = session.query(Parking).all()
        for parking in parkings:
            free_spaces = parking.max_capacity - parking.current_occupancy
            print(f"Parking {parking.name}:")
            print(f"  - Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
            print(f"  - Plazas libres: {free_spaces}")
            print(f"  - Estado actual: {parking.status}")
            print(f"  - Umbral denso: {parking.threshold_dense}")
            print(f"  - Umbral completo: {parking.threshold_full}")
            
            # Verificar si el estado es correcto según la ocupación
            expected_status = None
            if free_spaces < 0 or parking.current_occupancy > parking.max_capacity:
                expected_status = "COMPLETO"
            elif free_spaces <= parking.threshold_full:
                expected_status = "COMPLETO"
            elif free_spaces <= parking.threshold_dense:
                expected_status = "DENSO"
            else:
                expected_status = "LIBRE"
            
            status_correct = parking.status == expected_status
            print(f"  - Estado esperado: {expected_status}")
            print(f"  - ✅ Estado correcto" if status_correct else f"  - ❌ Estado incorrecto")
            print()
        
        # 2. Verificar programaciones activas
        print("\n📅 PROGRAMACIONES ACTIVAS:")
        print("-" * 30)
        
        schedule_service = PanelScheduleService(session)
        current_time = datetime.now().astimezone()
        current_time_str = current_time.strftime('%H:%M')
        current_weekday = current_time.weekday()
        
        weekday_fields = {
            0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday',
            4: 'friday', 5: 'saturday', 6: 'sunday'
        }
        current_weekday_field = weekday_fields.get(current_weekday, 'monday')
        
        active_schedules = []
        for parking in parkings:
            schedules = session.query(PanelSchedule).filter(
                and_(
                    PanelSchedule.parking_id == parking.id,
                    PanelSchedule.is_active == True,
                    getattr(PanelSchedule, current_weekday_field) == True,
                    PanelSchedule.start_time <= current_time_str,
                    PanelSchedule.end_time >= current_time_str
                )
            ).all()
            
            if schedules:
                print(f"Parking {parking.name} tiene {len(schedules)} programación(es) activa(s):")
                for schedule in schedules:
                    print(f"  - {schedule.name}: '{schedule.message}' ({schedule.start_time}-{schedule.end_time})")
                    active_schedules.append(schedule)
            else:
                print(f"Parking {parking.name}: Sin programaciones activas")
        
        # 3. Verificar mensajes actuales de paneles
        print("\n📺 MENSAJES ACTUALES DE PANELES:")
        print("-" * 30)
        
        panels = session.query(Panel).all()
        for panel in panels:
            parking = panel.parking
            print(f"Panel {panel.ip} ({parking.name}):")
            print(f"  - Último mensaje: '{panel.last_message}'")
            print(f"  - Última actualización: {panel.last_update}")
            print(f"  - Estado: {panel.status}")
            
            # Verificar si el mensaje coincide con el estado del parking
            if panel.last_message in ["LLIURE", "DENS", "COMPLET"]:
                # Es un mensaje de estado
                if parking.status == "LIBRE" and panel.last_message != "LLIURE":
                    print(f"  - ❌ Inconsistencia: Estado LIBRE pero mensaje '{panel.last_message}'")
                elif parking.status == "DENSO" and panel.last_message != "DENS":
                    print(f"  - ❌ Inconsistencia: Estado DENSO pero mensaje '{panel.last_message}'")
                elif parking.status == "COMPLETO" and panel.last_message != "COMPLET":
                    print(f"  - ❌ Inconsistencia: Estado COMPLETO pero mensaje '{panel.last_message}'")
                else:
                    print(f"  - ✅ Mensaje coherente con estado")
            else:
                # Es un mensaje de programación
                print(f"  - 📅 Mensaje de programación activa")
            
            print()
        
        # 4. Simular qué mensaje se enviaría ahora
        print("\n🧪 SIMULACIÓN DE ENVÍO DE MENSAJES:")
        print("-" * 30)
        
        for parking in parkings:
            print(f"Parking {parking.name}:")
            
            # Verificar si hay programaciones activas
            active_schedules_for_parking = schedule_service.get_active_schedules_for_parking(parking.id)
            
            if active_schedules_for_parking:
                schedule = active_schedules_for_parking[0]
                print(f"  - 📅 Programación activa: '{schedule.message}'")
                print(f"  - ✅ NO se enviaría mensaje de estado (programación tiene prioridad)")
            else:
                # Simular envío de mensaje de estado
                free_spaces = parking.max_capacity - parking.current_occupancy
                
                if free_spaces < 0 or parking.current_occupancy > parking.max_capacity:
                    message = "COMPLET"
                    color = 1
                elif free_spaces <= parking.threshold_full:
                    message = "COMPLET"
                    color = 1
                elif free_spaces <= parking.threshold_dense:
                    message = "DENS"
                    color = 3
                else:
                    message = "LLIURE"
                    color = 2
                
                print(f"  - 📤 Se enviaría: '{message}' (color {color})")
                print(f"  - 📊 Basado en: {free_spaces} plazas libres")
            
            print()
        
        # 5. Verificar lógica de cálculo de estado en camera_server.py
        print("\n🔧 ANÁLISIS DE LÓGICA DE ESTADO:")
        print("-" * 30)
        
        for parking in parkings:
            print(f"Parking {parking.name}:")
            
            # Simular la lógica exacta de camera_server.py
            occ = parking.current_occupancy
            free = parking.max_capacity - occ
            
            if free < 0:
                expected_status = 'COMPLETO'
                expected_message = 'COMPLET'
                reason = "descuadre negativo"
            elif occ > parking.max_capacity:
                expected_status = 'COMPLETO'
                expected_message = 'COMPLET'
                reason = "exceso de ocupación"
            elif free <= parking.threshold_full:
                expected_status = 'COMPLETO'
                expected_message = 'COMPLET'
                reason = "umbral completo"
            elif free <= parking.threshold_dense:
                expected_status = 'DENSO'
                expected_message = 'DENS'
                reason = "umbral denso"
            else:
                expected_status = 'LIBRE'
                expected_message = 'LLIURE'
                reason = "estado libre"
            
            print(f"  - Estado actual: {parking.status}")
            print(f"  - Estado esperado: {expected_status} ({reason})")
            print(f"  - Mensaje esperado: {expected_message}")
            
            if parking.status != expected_status:
                print(f"  - ❌ Estado incorrecto en BD")
            else:
                print(f"  - ✅ Estado correcto en BD")
            
            print()
        
        # 6. Recomendaciones
        print("\n💡 RECOMENDACIONES:")
        print("-" * 30)
        
        issues_found = []
        
        for parking in parkings:
            # Verificar si hay inconsistencias
            free_spaces = parking.max_capacity - parking.current_occupancy
            
            if free_spaces < 0:
                if parking.status != "COMPLETO":
                    issues_found.append(f"Parking {parking.name}: Descuadre negativo pero estado no es COMPLETO")
            
            elif parking.current_occupancy > parking.max_capacity:
                if parking.status != "COMPLETO":
                    issues_found.append(f"Parking {parking.name}: Exceso de ocupación pero estado no es COMPLETO")
            
            elif free_spaces <= parking.threshold_full:
                if parking.status != "COMPLETO":
                    issues_found.append(f"Parking {parking.name}: Por debajo del umbral completo pero estado no es COMPLETO")
            
            elif free_spaces <= parking.threshold_dense:
                if parking.status != "DENSO":
                    issues_found.append(f"Parking {parking.name}: Por debajo del umbral denso pero estado no es DENSO")
            
            else:
                if parking.status != "LIBRE":
                    issues_found.append(f"Parking {parking.name}: Por encima del umbral denso pero estado no es LIBRE")
        
        if issues_found:
            print("❌ PROBLEMAS DETECTADOS:")
            for issue in issues_found:
                print(f"  - {issue}")
        else:
            print("✅ No se detectaron inconsistencias en los estados")
        
        print("\n🔧 ACCIONES SUGERIDAS:")
        print("1. Verificar que los umbrales de los parkings sean correctos")
        print("2. Revisar si hay programaciones que no deberían estar activas")
        print("3. Verificar que el monitor de programaciones esté funcionando correctamente")
        print("4. Comprobar que no haya mensajes duplicados o incorrectos en la cola")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    diagnose_panel_messages() 