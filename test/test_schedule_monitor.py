#!/usr/bin/env python3
"""
Script de prueba para el servicio de monitorización de programaciones
"""

import sys
import os
import time
import requests
from datetime import datetime, timedelta

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from schedule_monitor_service import ScheduleMonitorService
from panel_schedule_service import PanelScheduleService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL

def test_schedule_monitor():
    """Probar el servicio de monitorización"""
    print("==========================================")
    print("Prueba del Servicio de Monitorización")
    print("Parking Altea v2.7")
    print("==========================================")
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Crear instancia del servicio de monitorización
        monitor = ScheduleMonitorService(check_interval=30)  # 30 segundos para pruebas
        
        print("✅ Servicio de monitorización creado")
        
        # Obtener estado inicial
        status = monitor.get_status()
        print(f"Estado inicial: {status}")
        
        # Crear una programación de prueba
        schedule_service = PanelScheduleService(session)
        
        # Datos de programación de prueba (para ejecutarse en los próximos 2 minutos)
        now = datetime.now()
        start_time = (now + timedelta(minutes=1)).strftime('%H:%M')
        end_time = (now + timedelta(minutes=3)).strftime('%H:%M')
        
        test_schedule = {
            'name': 'Prueba Monitorización',
            'parking_id': 1,  # P. Ciutat Esportiva
            'message': 'PRUEBA MONITOR',
            'start_date': now.strftime('%Y-%m-%d'),
            'end_date': (now + timedelta(days=1)).strftime('%Y-%m-%d'),
            'start_time': start_time,
            'end_time': end_time,
            'monday': True,
            'tuesday': True,
            'wednesday': True,
            'thursday': True,
            'friday': True,
            'saturday': True,
            'sunday': True,
            'priority': 5,
            'color': 1,  # Rojo
            'font_size': 2,
            'effect': 'static',
            'is_active': True
        }
        
        print(f"Creando programación de prueba...")
        result = schedule_service.create_schedule(test_schedule)
        
        if result['success']:
            schedule_id = result['schedule']['id']
            print(f"✅ Programación de prueba creada (ID: {schedule_id})")
            print(f"   Horario: {start_time} - {end_time}")
            print(f"   Mensaje: {test_schedule['message']}")
        else:
            print(f"❌ Error creando programación: {result['error']}")
            return
        
        # Iniciar el monitor
        print("\nIniciando monitorización...")
        monitor.start()
        
        # Esperar a que se ejecute la programación
        print("Esperando ejecución de programación...")
        for i in range(10):  # Esperar hasta 5 minutos
            time.sleep(30)
            print(f"Minuto {i+1}: Verificando...")
            
            # Verificar logs de la programación
            logs_result = schedule_service.get_schedule_logs(schedule_id=schedule_id)
            if logs_result['success'] and logs_result['logs']:
                latest_log = logs_result['logs'][0]
                print(f"✅ Log encontrado: {latest_log['execution_type']} - {latest_log['message_sent']}")
                print(f"   Paneles afectados: {latest_log['panels_affected']}")
                print(f"   Ejecutado: {latest_log['executed_at']}")
                break
        
        # Detener el monitor
        print("\nDeteniendo monitorización...")
        monitor.stop()
        
        # Limpiar programación de prueba
        print("Limpiando programación de prueba...")
        schedule_service.delete_schedule(schedule_id)
        print("✅ Programación de prueba eliminada")
        
        # Verificar estado final
        final_status = monitor.get_status()
        print(f"Estado final: {final_status}")
        
        session.close()
        
        print("\n==========================================")
        print("✅ Prueba completada exitosamente")
        print("==========================================")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Probar endpoints de la API relacionados con programaciones"""
    print("\n==========================================")
    print("Prueba de Endpoints de Programaciones")
    print("==========================================")
    
    base_url = "http://localhost:6001/api"
    
    endpoints = [
        "/schedules",
        "/schedules/logs",
        "/parking/1/schedules",
        "/parking/1/active-schedules"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"Probando: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: {len(data.get('schedules', data.get('logs', [])))} elementos")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Error de conexión - {e}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def test_monitor_status():
    """Probar estado del servicio de monitorización"""
    print("\n==========================================")
    print("Estado del Servicio de Monitorización")
    print("==========================================")
    
    try:
        # Verificar si el servicio systemd está activo
        import subprocess
        
        result = subprocess.run(['systemctl', 'is-active', 'parking-schedule-monitor'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            status = result.stdout.strip()
            print(f"Estado del servicio: {status}")
            
            if status == 'active':
                # Obtener logs recientes
                print("\nLogs recientes del servicio:")
                logs_result = subprocess.run(['journalctl', '-u', 'parking-schedule-monitor', 
                                            '--no-pager', '-n', '10'], 
                                           capture_output=True, text=True)
                print(logs_result.stdout)
            else:
                print("El servicio no está activo")
        else:
            print("No se pudo verificar el estado del servicio")
            
    except Exception as e:
        print(f"Error verificando estado: {e}")

if __name__ == "__main__":
    print("Iniciando pruebas del servicio de monitorización...")
    
    # Ejecutar pruebas
    test_schedule_monitor()
    test_api_endpoints()
    test_monitor_status()
    
    print("\n==========================================")
    print("Todas las pruebas completadas")
    print("==========================================") 