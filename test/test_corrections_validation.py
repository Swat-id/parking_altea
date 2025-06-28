#!/usr/bin/env python3
"""
Script de validación para verificar las correcciones implementadas
- Ruta de estadísticas con redirección
- Manejo de descuadre negativo
- Validación de ID en estadísticas
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://157.180.91.63:6001"

def test_statistics_route():
    """Probar la ruta de estadísticas con redirección"""
    print("🔍 Probando ruta de estadísticas...")
    
    # Probar ruta sin ID (debería redirigir)
    try:
        response = requests.get(f"{BASE_URL}/statistics", timeout=10)
        print(f"   📊 GET /statistics - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Ruta de estadísticas accesible")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_statistics_with_id():
    """Probar estadísticas con ID específico"""
    print("🔍 Probando estadísticas con ID...")
    
    try:
        response = requests.get(f"{BASE_URL}/parking/1/hourly-statistics?days=1", timeout=10)
        print(f"   📊 GET /parking/1/hourly-statistics - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Estadísticas obtenidas para parking: {data.get('parking_name', 'N/A')}")
            print(f"   📈 Período: {data.get('period', 'N/A')}")
            print(f"   📊 Horas con datos: {len(data.get('hourly_statistics', []))}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_parking_negative_discrepancy():
    """Probar el manejo de descuadre negativo"""
    print("🔍 Probando manejo de descuadre negativo...")
    
    try:
        # Obtener parking actual
        response = requests.get(f"{BASE_URL}/parking/1", timeout=10)
        if response.status_code != 200:
            print(f"   ❌ No se pudo obtener parking: {response.status_code}")
            return False
            
        parking_data = response.json()
        current_occupancy = parking_data.get('plazas_ocupadas', 0)
        max_capacity = parking_data.get('total_plazas', 0)
        
        print(f"   📊 Ocupación actual: {current_occupancy}/{max_capacity}")
        
        # Intentar establecer ocupación que cause descuadre negativo
        test_occupancy = max_capacity + 10  # 10 más que la capacidad máxima
        
        update_data = {'occupancy': test_occupancy}
        response = requests.post(f"{BASE_URL}/parking/1/occupancy", 
                               json=update_data, timeout=10)
        
        print(f"   📊 POST /parking/1/occupancy - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            new_status = result.get('status', '')
            print(f"   ✅ Ocupación actualizada: {result.get('occupancy', 'N/A')}")
            print(f"   📊 Estado resultante: {new_status}")
            
            # Verificar que el estado sea COMPLETO para descuadre negativo
            if new_status == 'COMPLETO':
                print("   ✅ Descuadre negativo manejado correctamente (estado: COMPLETO)")
                return True
            else:
                print(f"   ⚠️  Estado inesperado: {new_status}")
                return False
        else:
            print(f"   ❌ Error actualizando ocupación: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_parking_list_status():
    """Probar que la lista de parkings muestra estados correctos"""
    print("🔍 Probando lista de parkings...")
    
    try:
        response = requests.get(f"{BASE_URL}/parkings", timeout=10)
        print(f"   📊 GET /parkings - Status: {response.status_code}")
        
        if response.status_code == 200:
            parkings = response.json()
            print(f"   ✅ {len(parkings)} parkings obtenidos")
            
            # Verificar estados
            for parking in parkings:
                name = parking.get('name', 'N/A')
                status = parking.get('estado', 'N/A')
                occupancy = parking.get('plazas_ocupadas', 0)
                capacity = parking.get('total_plazas', 0)
                free_spaces = parking.get('plazas_libres', 0)
                
                print(f"   📍 {name}: {status} ({occupancy}/{capacity}, {free_spaces} libres)")
                
                # Verificar que no hay estados de descuadre negativo
                if 'DESCUADRE' in status:
                    print(f"   ❌ ERROR: Parking {name} tiene estado incorrecto: {status}")
                    return False
            
            print("   ✅ Todos los parkings tienen estados válidos")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def main():
    """Función principal de validación"""
    print("🚀 Iniciando validación de correcciones")
    print("📅 Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    results = []
    
    # Ejecutar pruebas
    results.append(("Ruta de estadísticas", test_statistics_route()))
    results.append(("Estadísticas con ID", test_statistics_with_id()))
    results.append(("Manejo descuadre negativo", test_parking_negative_discrepancy()))
    results.append(("Lista de parkings", test_parking_list_status()))
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ OK" if result else "❌ ERROR"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 TODAS LAS CORRECCIONES FUNCIONAN CORRECTAMENTE")
        print("\n✅ Correcciones verificadas:")
        print("   - Ruta /statistics redirige correctamente")
        print("   - Estadísticas con ID funcionan")
        print("   - Descuadre negativo se maneja como COMPLETO")
        print("   - Lista de parkings muestra estados válidos")
    else:
        print("❌ HAY PROBLEMAS QUE NECESITAN ATENCIÓN")
        print("   Revisar los errores mostrados arriba")

if __name__ == "__main__":
    main() 