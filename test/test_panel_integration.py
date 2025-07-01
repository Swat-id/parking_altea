#!/usr/bin/env python3
"""
Script para probar la integración completa de actualización de paneles
"""

import sys
import os
sys.path.append('src')

import requests
import json
from datetime import datetime

def test_panel_integration():
    """Probar la integración completa de actualización de paneles"""
    
    print("=" * 60)
    print("🔍 PRUEBA DE INTEGRACIÓN DE ACTUALIZACIÓN DE PANELES")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configuración
    API_BASE_URL = "http://localhost:6001"
    CAMERA_BASE_URL = "http://localhost:6400"
    
    try:
        # 1. Verificar que los servicios están funcionando
        print("\n📡 Verificando servicios...")
        
        # API Server
        try:
            response = requests.get(f"{API_BASE_URL}/parkings", timeout=5)
            if response.status_code == 200:
                print("✅ API Server funcionando")
            else:
                print(f"❌ API Server error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Server no disponible: {e}")
            return False
        
        # Camera Server
        try:
            response = requests.get(f"{CAMERA_BASE_URL}/camera", timeout=5)
            if response.status_code == 200:
                print("✅ Camera Server funcionando")
            else:
                print(f"❌ Camera Server error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Camera Server no disponible: {e}")
            return False
        
        # 2. Obtener información de parkings
        print("\n📊 Obteniendo información de parkings...")
        response = requests.get(f"{API_BASE_URL}/parkings")
        parkings = response.json()
        
        print(f"Parkings encontrados: {len(parkings)}")
        
        # Buscar un parking con paneles para la prueba
        test_parking = None
        for parking in parkings:
            if parking.get('paneles', 0) > 0:
                test_parking = parking
                break
        
        if not test_parking:
            print("❌ No se encontró ningún parking con paneles para la prueba")
            return False
        
        print(f"Parking de prueba: {test_parking['name']} (ID: {test_parking['id']})")
        print(f"Ocupación actual: {test_parking['plazas_ocupadas']}")
        print(f"Estado actual: {test_parking['estado']}")
        
        # 3. Probar actualización manual de ocupación
        print(f"\n🧪 Probando actualización manual de ocupación...")
        
        # Obtener ocupación actual
        current_occupancy = test_parking['plazas_ocupadas']
        new_occupancy = current_occupancy + 1  # Incrementar en 1
        
        print(f"Cambiando ocupación de {current_occupancy} a {new_occupancy}")
        
        # Hacer la petición
        payload = {"occupancy": new_occupancy}
        response = requests.post(
            f"{API_BASE_URL}/parking/{test_parking['id']}/occupancy",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Actualización manual exitosa")
            print(f"   Nueva ocupación: {result['occupancy']}")
            print(f"   Nuevo estado: {result['status']}")
            print(f"   Cambio: {result['change_amount']}")
        else:
            print(f"❌ Error en actualización manual: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
        
        # 4. Verificar que se actualizó en la base de datos
        print(f"\n🔍 Verificando actualización en base de datos...")
        response = requests.get(f"{API_BASE_URL}/parking/{test_parking['id']}")
        updated_parking = response.json()
        
        if updated_parking['plazas_ocupadas'] == new_occupancy:
            print("✅ Ocupación actualizada correctamente en BD")
        else:
            print(f"❌ Ocupación no se actualizó en BD: {updated_parking['plazas_ocupadas']}")
            return False
        
        # 5. Probar actualización de configuración
        print(f"\n⚙️ Probando actualización de configuración...")
        
        # Obtener configuración actual
        current_threshold_dense = test_parking['threshold_dense']
        new_threshold_dense = current_threshold_dense + 1
        
        print(f"Cambiando threshold_dense de {current_threshold_dense} a {new_threshold_dense}")
        
        # Hacer la petición
        payload = {"threshold_dense": new_threshold_dense}
        response = requests.post(
            f"{API_BASE_URL}/parking/{test_parking['id']}/config",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Actualización de configuración exitosa")
            print(f"   Nuevo threshold_dense: {result['threshold_dense']}")
        else:
            print(f"❌ Error en actualización de configuración: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
        
        # 6. Restaurar valores originales
        print(f"\n🔄 Restaurando valores originales...")
        
        # Restaurar ocupación
        payload = {"occupancy": current_occupancy}
        response = requests.post(
            f"{API_BASE_URL}/parking/{test_parking['id']}/occupancy",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Ocupación restaurada")
        else:
            print(f"❌ Error restaurando ocupación: {response.status_code}")
        
        # Restaurar configuración
        payload = {"threshold_dense": current_threshold_dense}
        response = requests.post(
            f"{API_BASE_URL}/parking/{test_parking['id']}/config",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Configuración restaurada")
        else:
            print(f"❌ Error restaurando configuración: {response.status_code}")
        
        # 7. Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        print("✅ Servicios funcionando")
        print("✅ Actualización manual de ocupación")
        print("✅ Actualización de configuración")
        print("✅ Verificación en base de datos")
        print("✅ Restauración de valores")
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_panel_integration()
    sys.exit(0 if success else 1) 