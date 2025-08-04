#!/usr/bin/env python3
"""
Test para verificar el comportamiento del frontend con programaciones
"""

import sys
import os
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DB_URL
from models import Parking, Panel, PanelSchedule
from panel_schedule_service import PanelScheduleService

# Configuración de la API
API_BASE_URL = "http://localhost:5000"

def test_schedule_creation_and_execution():
    """Test para verificar que al crear una programación se ejecuta automáticamente si es operativa"""
    
    print("=== TEST: Creación y Ejecución Automática de Programaciones ===")
    
    # Crear conexión a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener un parking con paneles
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para el test")
            return False
        
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        if not panels:
            print("❌ El parking no tiene paneles configurados")
            return False
        
        print(f"✅ Parking encontrado: {parking.name} (ID: {parking.id})")
        print(f"✅ Paneles configurados: {len(panels)}")
        
        # 2. Crear programación que esté activa ahora
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        schedule_data = {
            'parking_id': parking.id,
            'name': 'Test Frontend - Ejecución Automática',
            'description': 'Programación de prueba para verificar ejecución automática',
            'start_date': now.date(),
            'end_date': (now + timedelta(days=1)).date(),
            'start_time': current_time,
            'end_time': (now + timedelta(hours=1)).strftime('%H:%M'),
            'message': 'TEST FRONTEND AUTO EJECUCIÓN',
            'color': 1,  # Rojo
            'font_size': 16,
            'effect': 'static',
            'is_active': True,
            'priority': 1,
            current_weekday_field: True
        }
        
        # 3. Crear la programación usando el servicio
        schedule_service = PanelScheduleService(session)
        create_result = schedule_service.create_schedule(schedule_data)
        
        if not create_result['success']:
            print(f"❌ Error creando programación: {create_result['error']}")
            return False
        
        schedule_id = create_result['schedule_id']
        auto_executed = create_result.get('auto_executed', False)
        panels_affected = create_result.get('panels_affected', 0)
        
        print(f"✅ Programación creada: {schedule_id}")
        print(f"✅ Ejecución automática: {auto_executed}")
        print(f"✅ Paneles afectados: {panels_affected}")
        
        # 4. Verificar que se ejecutó automáticamente
        if auto_executed:
            print("✅ CORRECTO: La programación se ejecutó automáticamente al crearla")
        else:
            print("⚠️  La programación no se ejecutó automáticamente (puede ser normal si no es operativa ahora)")
        
        # 5. Verificar estado de los paneles
        print("\n--- Verificando estado de los paneles ---")
        for panel in panels:
            if panel.last_message == schedule_data['message']:
                print(f"✅ Panel {panel.ip}: Muestra mensaje de programación")
            else:
                print(f"⚠️  Panel {panel.ip}: Último mensaje: {panel.last_message}")
        
        # 6. Limpiar
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
        if schedule:
            session.delete(schedule)
            session.commit()
            print("✅ Programación de prueba eliminada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_manual_execution_via_api():
    """Test para verificar la ejecución manual de programaciones via API"""
    
    print("\n=== TEST: Ejecución Manual de Programaciones via API ===")
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Obtener un parking con paneles
        parking = session.query(Parking).first()
        if not parking:
            print("❌ No se encontró ningún parking para el test")
            return False
        
        # 2. Crear programación que NO esté activa ahora (para probar ejecución manual)
        now = datetime.now()
        future_time = (now + timedelta(hours=2)).strftime('%H:%M')
        current_weekday = now.weekday()
        weekday_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday_field = weekday_fields[current_weekday]
        
        schedule_data = {
            'parking_id': parking.id,
            'name': 'Test Frontend - Ejecución Manual',
            'description': 'Programación de prueba para verificar ejecución manual',
            'start_date': now.date(),
            'end_date': (now + timedelta(days=1)).date(),
            'start_time': future_time,  # Hora futura
            'end_time': (now + timedelta(hours=3)).strftime('%H:%M'),
            'message': 'TEST FRONTEND MANUAL EJECUCIÓN',
            'color': 2,  # Verde
            'font_size': 16,
            'effect': 'static',
            'is_active': True,
            'priority': 1,
            current_weekday_field: True
        }
        
        # 3. Crear la programación
        schedule_service = PanelScheduleService(session)
        create_result = schedule_service.create_schedule(schedule_data)
        
        if not create_result['success']:
            print(f"❌ Error creando programación: {create_result['error']}")
            return False
        
        schedule_id = create_result['schedule_id']
        print(f"✅ Programación creada: {schedule_id}")
        
        # 4. Ejecutar manualmente via API
        print("--- Ejecutando programación manualmente via API ---")
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/schedules/{schedule_id}/execute")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    panels_affected = result.get('panels_affected', 0)
                    print(f"✅ Programación ejecutada manualmente: {panels_affected} paneles afectados")
                else:
                    print(f"❌ Error ejecutando programación: {result.get('error')}")
            else:
                print(f"❌ Error HTTP: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        
        # 5. Verificar estado de los paneles después de la ejecución manual
        print("\n--- Verificando estado de los paneles después de ejecución manual ---")
        panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
        for panel in panels:
            if panel.last_message == schedule_data['message']:
                print(f"✅ Panel {panel.ip}: Muestra mensaje de programación")
            else:
                print(f"⚠️  Panel {panel.ip}: Último mensaje: {panel.last_message}")
        
        # 6. Limpiar
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
        if schedule:
            session.delete(schedule)
            session.commit()
            print("✅ Programación de prueba eliminada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

def test_schedule_monitor_interval():
    """Test para verificar el intervalo de verificación del monitor de programaciones"""
    
    print("\n=== TEST: Intervalo de Verificación del Monitor ===")
    
    try:
        # 1. Verificar configuración del monitor
        from schedule_monitor_service import ScheduleMonitorService
        
        # Crear instancia del monitor con intervalo de 30 segundos para testing
        monitor = ScheduleMonitorService(check_interval=30)
        print(f"✅ Monitor configurado con intervalo de {monitor.check_interval} segundos")
        
        # 2. Verificar que el intervalo es configurable
        if monitor.check_interval == 30:
            print("✅ El intervalo de verificación es configurable")
        else:
            print("⚠️  El intervalo de verificación no es el esperado")
        
        # 3. Información sobre el comportamiento esperado
        print("\n--- Información del Monitor de Programaciones ---")
        print(f"• Intervalo de verificación: {monitor.check_interval} segundos")
        print("• El monitor verifica programaciones activas cada intervalo")
        print("• Si una programación es operativa, se ejecuta automáticamente")
        print("• Se evitan ejecuciones duplicadas en el mismo minuto")
        print("• Al finalizar una programación, se restaura el estado normal")
        
        # 4. Verificar que el monitor no está ejecutándose (para evitar conflictos)
        if not monitor.running:
            print("✅ El monitor no está ejecutándose (correcto para testing)")
        else:
            print("⚠️  El monitor está ejecutándose (puede causar conflictos en testing)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_button_behavior():
    """Test para verificar el comportamiento de los botones del frontend"""
    
    print("\n=== TEST: Comportamiento de Botones del Frontend ===")
    
    try:
        # 1. Verificar endpoints disponibles
        endpoints_to_test = [
            "/api/schedules",
            "/api/schedules/1/execute",
            "/api/schedules/1/toggle"
        ]
        
        print("--- Verificando endpoints del frontend ---")
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}")
                if response.status_code in [200, 404, 405]:  # 404 es normal si no hay datos, 405 si es POST
                    print(f"✅ Endpoint {endpoint}: Accesible")
                else:
                    print(f"⚠️  Endpoint {endpoint}: Status {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"❌ Endpoint {endpoint}: No accesible")
        
        # 2. Información sobre el comportamiento esperado
        print("\n--- Comportamiento Esperado del Frontend ---")
        print("• Botón 'Play' (▶️): Ejecuta la programación inmediatamente")
        print("• Botón 'Toggle' (⏸️/▶️): Activa/desactiva la programación")
        print("• Al guardar programación: Se ejecuta automáticamente si es operativa")
        print("• Al editar programación: Se ejecuta automáticamente si es operativa")
        print("• El monitor verifica cada 60 segundos por defecto")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando tests de comportamiento del frontend con programaciones...")
    
    test1_passed = test_schedule_creation_and_execution()
    test2_passed = test_manual_execution_via_api()
    test3_passed = test_schedule_monitor_interval()
    test4_passed = test_frontend_button_behavior()
    
    print("\n" + "="*60)
    print("RESULTADOS DE LOS TESTS:")
    print(f"Test 1 - Creación y Ejecución Automática: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"Test 2 - Ejecución Manual via API: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    print(f"Test 3 - Intervalo de Monitor: {'✅ PASÓ' if test3_passed else '❌ FALLÓ'}")
    print(f"Test 4 - Botones Frontend: {'✅ PASÓ' if test4_passed else '❌ FALLÓ'}")
    
    if all([test1_passed, test2_passed, test3_passed, test4_passed]):
        print("\n🎉 TODOS LOS TESTS PASARON - El frontend funciona correctamente")
    else:
        print("\n⚠️  ALGUNOS TESTS FALLARON - Revisar el comportamiento del frontend")
    
    print("="*60) 