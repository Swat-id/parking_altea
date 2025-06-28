#!/usr/bin/env python3
"""
Script para corregir problemas de datos en los parkings
- Parking 5: Descuadre negativo (111 ocupadas de 90 total)
- Parking 6: Ocupación negativa (-25 plazas)
"""

import os
import sys
import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"

def fix_parking_data():
    """Corregir los problemas de datos identificados"""
    
    print("🔧 CORRECCIÓN DE DATOS DE PARKINGS")
    print("=" * 50)
    
    # 1. Corregir Parking 5 (Descuadre negativo)
    print("\n1. Corrigiendo Parking 5 (Descuadre negativo)...")
    print("   - Estado actual: 111 plazas ocupadas de 90 total")
    print("   - Acción: Ajustar ocupación a 85 (95% de capacidad)")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/parking/5/occupancy",
            json={"occupancy": 85},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("   ✅ Parking 5 corregido exitosamente")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # 2. Corregir Parking 6 (Ocupación negativa)
    print("\n2. Corrigiendo Parking 6 (Ocupación negativa)...")
    print("   - Estado actual: -25 plazas ocupadas")
    print("   - Acción: Ajustar ocupación a 0")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/parking/6/occupancy",
            json={"occupancy": 0},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("   ✅ Parking 6 corregido exitosamente")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # 3. Verificar correcciones
    print("\n3. Verificando correcciones...")
    
    parkings_to_check = [5, 6]
    
    for parking_id in parkings_to_check:
        try:
            response = requests.get(f"{API_BASE_URL}/parking/{parking_id}")
            
            if response.status_code == 200:
                parking = response.json()
                print(f"   Parking {parking_id}:")
                print(f"     - Nombre: {parking['name']}")
                print(f"     - Ocupación: {parking['plazas_ocupadas']}/{parking['total_plazas']}")
                print(f"     - Estado: {parking['estado']}")
                
                # Verificar si la corrección fue exitosa
                if parking_id == 5:
                    if parking['plazas_ocupadas'] <= parking['total_plazas']:
                        print(f"     ✅ Corrección exitosa")
                    else:
                        print(f"     ❌ Aún hay descuadre")
                elif parking_id == 6:
                    if parking['plazas_ocupadas'] >= 0:
                        print(f"     ✅ Corrección exitosa")
                    else:
                        print(f"     ❌ Aún hay ocupación negativa")
                        
            else:
                print(f"   ❌ Error obteniendo parking {parking_id}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error de conexión para parking {parking_id}: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Corrección de datos completada")
    print("=" * 50)

def verify_all_parkings():
    """Verificar el estado de todos los parkings después de las correcciones"""
    
    print("\n📊 VERIFICACIÓN COMPLETA DE PARKINGS")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/parkings")
        
        if response.status_code == 200:
            parkings = response.json()
            
            issues_found = 0
            
            for parking in parkings:
                print(f"\nParking {parking['id']}: {parking['name']}")
                print(f"  - Ocupación: {parking['plazas_ocupadas']}/{parking['total_plazas']}")
                print(f"  - Estado: {parking['estado']}")
                
                # Verificar problemas
                if parking['plazas_ocupadas'] > parking['total_plazas']:
                    print(f"  ⚠️  PROBLEMA: Descuadre negativo")
                    issues_found += 1
                elif parking['plazas_ocupadas'] < 0:
                    print(f"  ⚠️  PROBLEMA: Ocupación negativa")
                    issues_found += 1
                else:
                    print(f"  ✅ OK")
            
            print(f"\n📈 RESUMEN:")
            print(f"  - Total parkings: {len(parkings)}")
            print(f"  - Problemas encontrados: {issues_found}")
            
            if issues_found == 0:
                print(f"  🎉 Todos los parkings están en estado correcto")
            else:
                print(f"  ⚠️  Aún hay {issues_found} problemas por resolver")
                
        else:
            print(f"❌ Error obteniendo parkings: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    print(f"🚀 Iniciando corrección de datos - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar correcciones
    fix_parking_data()
    
    # Verificar resultados
    verify_all_parkings()
    
    print(f"\n✅ Proceso completado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 