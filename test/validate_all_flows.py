#!/usr/bin/env python3
"""
Script para validar todos los flujos de actualización de paneles
y detectar problemas en la lógica de estados
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Parking, Panel, Access
import config
from panel_communication_service import update_parking_panels

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_parking_states():
    """Validar los estados actuales de todos los parkings"""
    print("🔍 VALIDACIÓN DE ESTADOS DE PARKINGS")
    print("=" * 60)
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        parkings = session.query(Parking).all()
        
        for parking in parkings:
            free_spaces = parking.max_capacity - parking.current_occupancy
            print(f"\n🏢 Parking: {parking.name} (ID: {parking.id})")
            print(f"   Ocupación: {parking.current_occupancy}/{parking.max_capacity}")
            print(f"   Espacios libres: {free_spaces}")
            print(f"   Estado actual: {parking.status}")
            print(f"   Umbral denso: {parking.threshold_dense}")
            print(f"   Umbral completo: {parking.threshold_full}")
            
            # Calcular estado esperado según la lógica
            if free_spaces < 0:
                expected_status = "COMPLETO"
                reason = "Descuadre negativo"
            elif parking.current_occupancy > parking.max_capacity:
                expected_status = "COMPLETO"
                reason = "Exceso de ocupación"
            elif free_spaces <= parking.threshold_full:
                expected_status = "COMPLETO"
                reason = f"Libres ({free_spaces}) <= umbral completo ({parking.threshold_full})"
            elif free_spaces <= parking.threshold_dense:
                expected_status = "DENSO"
                reason = f"Libres ({free_spaces}) <= umbral denso ({parking.threshold_dense})"
            else:
                expected_status = "LIBRE"
                reason = f"Libres ({free_spaces}) > umbral denso ({parking.threshold_dense})"
            
            print(f"   Estado esperado: {expected_status} ({reason})")
            
            if parking.status != expected_status:
                print(f"   ⚠️  PROBLEMA: Estado actual ({parking.status}) != esperado ({expected_status})")
            else:
                print(f"   ✅ Estado correcto")
    
    finally:
        session.close()

def validate_panel_messages():
    """Validar los mensajes que se envían a los paneles"""
    print("\n\n📺 VALIDACIÓN DE MENSAJES DE PANELES")
    print("=" * 60)
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        parkings = session.query(Parking).all()
        
        for parking in parkings:
            panels = session.query(Panel).filter_by(parking_id=parking.id).all()
            
            if not panels:
                print(f"\n🏢 Parking: {parking.name} - No tiene paneles configurados")
                continue
            
            print(f"\n🏢 Parking: {parking.name} (ID: {parking.id})")
            print(f"   Estado: {parking.status}")
            print(f"   Paneles: {len(panels)}")
            
            # Simular la función update_parking_panels para ver qué mensaje se enviaría
            free_spaces = parking.max_capacity - parking.current_occupancy
            
            # Lógica de la función update_parking_panels
            if parking.status.lower() == 'closed':
                message = "PARKING TANCAT"
                color = 1  # Rojo
            else:
                if parking.status.upper() == 'COMPLETO':
                    status_text = "COMPLET"
                    color = 1  # Rojo
                elif parking.status.upper() == 'DENSO':
                    status_text = "DENS"
                    color = 3  # Amarillo
                else:
                    status_text = "LLIURE"
                    color = 2  # Verde
                
                message = status_text
            
            print(f"   Mensaje que se enviaría: '{message}' (color: {color})")
            
            # Verificar si el mensaje es correcto para el estado
            if parking.status.upper() == 'COMPLETO' and message != "COMPLET":
                print(f"   ⚠️  PROBLEMA: Estado COMPLETO pero mensaje '{message}'")
            elif parking.status.upper() == 'DENSO' and message != "DENS":
                print(f"   ⚠️  PROBLEMA: Estado DENSO pero mensaje '{message}'")
            elif parking.status.upper() == 'LIBRE' and message != "LLIURE":
                print(f"   ⚠️  PROBLEMA: Estado LIBRE pero mensaje '{message}'")
            else:
                print(f"   ✅ Mensaje correcto para el estado")
            
            # Mostrar paneles
            for panel in panels:
                print(f"     📺 Panel: {panel.ip} ({panel.name})")
    
    finally:
        session.close()

def test_camera_flow_logic():
    """Probar la lógica del flujo de cámaras"""
    print("\n\n📹 VALIDACIÓN DE LÓGICA DE FLUJO DE CÁMARAS")
    print("=" * 60)
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        parkings = session.query(Parking).all()
        
        for parking in parkings:
            print(f"\n🏢 Parking: {parking.name} (ID: {parking.id})")
            
            # Simular diferentes escenarios de ocupación
            scenarios = [
                (parking.max_capacity + 5, "Exceso de ocupación"),
                (parking.max_capacity, "Ocupación máxima"),
                (parking.max_capacity - parking.threshold_full, "En umbral completo"),
                (parking.max_capacity - parking.threshold_dense, "En umbral denso"),
                (parking.max_capacity - parking.threshold_dense - 10, "Bajo umbral denso")
            ]
            
            for occupancy, description in scenarios:
                free_spaces = parking.max_capacity - occupancy
                
                # Lógica del servidor de cámaras
                if free_spaces < 0:
                    status = 'COMPLETO'
                    reason = "Descuadre negativo"
                elif occupancy > parking.max_capacity:
                    status = 'COMPLETO'
                    reason = "Exceso de ocupación"
                elif free_spaces <= parking.threshold_full:
                    status = 'COMPLETO'
                    reason = f"Libres ({free_spaces}) <= umbral completo ({parking.threshold_full})"
                elif free_spaces <= parking.threshold_dense:
                    status = 'DENSO'
                    reason = f"Libres ({free_spaces}) <= umbral denso ({parking.threshold_dense})"
                else:
                    status = 'LIBRE'
                    reason = f"Libres ({free_spaces}) > umbral denso ({parking.threshold_dense})"
                
                # Determinar mensaje según la función update_parking_panels
                if status.upper() == 'COMPLETO':
                    message = "COMPLET"
                elif status.upper() == 'DENSO':
                    message = "DENS"
                else:
                    message = "LLIURE"
                
                print(f"   {description}: {occupancy}/{parking.max_capacity} -> {status} -> '{message}' ({reason})")
    
    finally:
        session.close()

def test_manual_flow_logic():
    """Probar la lógica del flujo manual"""
    print("\n\n🖱️  VALIDACIÓN DE LÓGICA DE FLUJO MANUAL")
    print("=" * 60)
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        parkings = session.query(Parking).all()
        
        for parking in parkings:
            print(f"\n🏢 Parking: {parking.name} (ID: {parking.id})")
            
            # Simular actualización manual
            current_occupancy = parking.current_occupancy
            free_spaces = parking.max_capacity - current_occupancy
            
            # Lógica del API server para actualización manual
            if free_spaces <= parking.threshold_full:
                status = 'COMPLETO'
            elif free_spaces <= parking.threshold_dense:
                status = 'DENSO'
            else:
                status = 'LIBRE'
            
            # Determinar mensaje según la función update_parking_panels
            if status.upper() == 'COMPLETO':
                message = "COMPLET"
            elif status.upper() == 'DENSO':
                message = "DENS"
            else:
                message = "LLIURE"
            
            print(f"   Ocupación actual: {current_occupancy}/{parking.max_capacity}")
            print(f"   Estado calculado: {status}")
            print(f"   Mensaje que se enviaría: '{message}'")
            
            if parking.status != status:
                print(f"   ⚠️  PROBLEMA: Estado en BD ({parking.status}) != calculado ({status})")
            else:
                print(f"   ✅ Estado consistente")
    
    finally:
        session.close()

def check_camera_server_import():
    """Verificar el problema de import en camera_server.py"""
    print("\n\n🔧 VALIDACIÓN DE IMPORTS EN CAMERA_SERVER")
    print("=" * 60)
    
    try:
        # Intentar importar la función
        from panel_communication_service import update_parking_panels
        print("✅ Import exitoso de update_parking_panels")
        
        # Probar la función
        result = update_parking_panels(1, 50, 100, "COMPLETO")
        print(f"✅ Función funciona: {result}")
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
    except Exception as e:
        print(f"❌ Error ejecutando función: {e}")

def main():
    """Función principal"""
    print("🚀 VALIDACIÓN COMPLETA DE FLUJOS DE PANELES")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar todas las validaciones
    validate_parking_states()
    validate_panel_messages()
    test_camera_flow_logic()
    test_manual_flow_logic()
    check_camera_server_import()
    
    print("\n\n" + "=" * 80)
    print("✅ VALIDACIÓN COMPLETADA")
    print("Revisa los resultados para identificar problemas en los flujos")

if __name__ == "__main__":
    main() 