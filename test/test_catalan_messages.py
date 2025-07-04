#!/usr/bin/env python3
"""
Script para probar el envío de mensajes con estado en catalán
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Parking, Panel
from config import DB_URL
from datetime import datetime

def test_catalan_messages():
    """Probar el envío de mensajes con estado en catalán"""
    
    print("=" * 60)
    print("🔍 PRUEBA DE MENSAJES EN CATALÁN")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conectar a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los parkings
        parkings = session.query(Parking).all()
        print(f"\n📺 PARKINGS CONFIGURADOS: {len(parkings)}")
        print("-" * 60)
        
        if len(parkings) == 0:
            print("❌ No hay parkings configurados en la base de datos")
            return
        
        # Probar diferentes estados
        test_states = [
            ("LIBRE", "LLIURE"),
            ("DENSO", "DENS"), 
            ("COMPLETO", "COMPLET")
        ]
        
        print(f"\n📝 PRUEBAS DE CONVERSIÓN DE ESTADOS")
        print("-" * 60)
        
        for spanish_state, expected_catalan in test_states:
            print(f"🇪🇸 {spanish_state} → 🇨🇦 {expected_catalan}")
        
        print(f"\n📊 PRUEBAS DE MENSAJES POR PARKING")
        print("-" * 60)
        
        for parking in parkings:
            print(f"\n🅿️  {parking.name}")
            print(f"   Capacidad: {parking.max_capacity}")
            print(f"   Ocupación actual: {parking.current_occupancy}")
            print(f"   Estado actual: {parking.status}")
            
            # Obtener paneles del parking
            panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
            print(f"   Paneles: {len(panels)}")
            
            for panel in panels:
                print(f"     📺 {panel.name} ({panel.ip}) - {panel.status}")
            
            # Simular mensaje que se enviaría
            if parking.status == "LIBRE":
                catalan_status = "LLIURE"
            elif parking.status == "DENSO":
                catalan_status = "DENS"
            elif parking.status == "COMPLETO":
                catalan_status = "COMPLET"
            else:
                catalan_status = parking.status
            
            message = f"{parking.current_occupancy}/{parking.max_capacity} - {catalan_status}"
            print(f"   📤 Mensaje que se enviaría: '{message}'")
            
            # Simular envío a paneles (sin enviar realmente)
            if panels:
                print(f"   📡 Se enviaría a {len(panels)} panel(es)")
                for panel in panels:
                    print(f"      → {panel.ip}: {message}")
            else:
                print(f"   ⚠️  No hay paneles configurados para este parking")
        
        # Probar la función de conversión
        print(f"\n🧪 PRUEBA DE FUNCIÓN DE CONVERSIÓN")
        print("-" * 60)
        
        from panel_communication_service import update_parking_panels
        
        # Simular llamada a la función (sin enviar realmente)
        for parking in parkings:
            try:
                # Simular la función sin enviar realmente
                catalan_status = ""
                if parking.status == "LIBRE":
                    catalan_status = "LLIURE"
                elif parking.status == "DENSO":
                    catalan_status = "DENS"
                elif parking.status == "COMPLETO":
                    catalan_status = "COMPLET"
                else:
                    catalan_status = parking.status
                
                message = f"{parking.current_occupancy}/{parking.max_capacity} - {catalan_status}"
                
                print(f"✅ Parking {parking.id}: {parking.status} → {catalan_status}")
                print(f"   Mensaje: {message}")
                
            except Exception as e:
                print(f"❌ Error en parking {parking.id}: {e}")
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        print(f"✅ Parkings procesados: {len(parkings)}")
        
        total_panels = sum(len(session.query(Panel).filter(Panel.parking_id == p.id).all()) for p in parkings)
        print(f"📺 Total paneles: {total_panels}")
        
        print(f"\n🎯 CONVERSIONES DE ESTADO:")
        print(f"   🇪🇸 LIBRE → 🇨🇦 LLIURE")
        print(f"   🇪🇸 DENSO → 🇨🇦 DENS") 
        print(f"   🇪🇸 COMPLETO → 🇨🇦 COMPLET")
        
        print(f"\n📝 FORMATO DE MENSAJE:")
        print(f"   'OCUPACION/MAXIMO - ESTADO_CATALAN'")
        print(f"   Ejemplo: '45/120 - DENS'")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_catalan_messages() 