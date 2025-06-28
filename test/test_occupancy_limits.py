#!/usr/bin/env python3
"""
Test de Límites de Ocupación
Prueba la nueva funcionalidad que permite ocupación superior al máximo
"""

import requests
import json
from datetime import datetime

def test_occupancy_limits():
    """Test de los nuevos límites de ocupación"""
    print("🧪 TEST DE LÍMITES DE OCUPACIÓN")
    print("=" * 60)
    print("Probando la nueva funcionalidad que permite ocupación superior al máximo")
    print("=" * 60)
    
    # Configuración
    base_url = "http://localhost:6001"
    
    # Obtener lista de parkings
    try:
        response = requests.get(f"{base_url}/parkings")
        if response.status_code != 200:
            print(f"❌ Error obteniendo parkings: {response.status_code}")
            return
        
        parkings = response.json()
        if not parkings:
            print("❌ No se encontraron parkings")
            return
        
        # Usar el primer parking para las pruebas
        parking = parkings[0]
        parking_id = parking['id']
        parking_name = parking['name']
        max_capacity = parking['total_plazas']
        current_occupancy = parking['ocupacion_actual']
        
        print(f"📊 Parking de prueba: {parking_name}")
        print(f"   Capacidad máxima: {max_capacity}")
        print(f"   Ocupación actual: {current_occupancy}")
        print()
        
        # Casos de prueba
        test_cases = [
            {
                "name": "Ocupación normal (dentro del límite)",
                "occupancy": max_capacity - 10,
                "expected_success": True
            },
            {
                "name": "Ocupación igual al máximo",
                "occupancy": max_capacity,
                "expected_success": True
            },
            {
                "name": "Ocupación ligeramente superior al máximo (+5)",
                "occupancy": max_capacity + 5,
                "expected_success": True
            },
            {
                "name": "Ocupación moderadamente superior al máximo (+20)",
                "occupancy": max_capacity + 20,
                "expected_success": True
            },
            {
                "name": "Ocupación muy superior al máximo (+100)",
                "occupancy": max_capacity + 100,
                "expected_success": True
            },
            {
                "name": "Ocupación 3x la capacidad máxima",
                "occupancy": max_capacity * 3,
                "expected_success": True
            },
            {
                "name": "Ocupación 5x la capacidad máxima (límite)",
                "occupancy": max_capacity * 5,
                "expected_success": True
            },
            {
                "name": "Ocupación 6x la capacidad máxima (debería fallar)",
                "occupancy": max_capacity * 6,
                "expected_success": False
            },
            {
                "name": "Ocupación 10x la capacidad máxima (debería fallar)",
                "occupancy": max_capacity * 10,
                "expected_success": False
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔸 Test {i}: {test_case['name']}")
            print(f"   Ocupación solicitada: {test_case['occupancy']}")
            
            try:
                response = requests.post(
                    f"{base_url}/parking/{parking_id}/occupancy",
                    json={"occupancy": test_case['occupancy']},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    success = result_data.get('status') == 'ok'
                    
                    if success == test_case['expected_success']:
                        print(f"   ✅ Resultado esperado: {test_case['expected_success']}")
                        if success:
                            print(f"   📊 Nueva ocupación: {result_data.get('occupancy')}")
                            print(f"   📊 Estado: {result_data.get('status')}")
                            print(f"   📊 Espacios libres: {result_data.get('free_spaces')}")
                    else:
                        print(f"   ❌ Resultado inesperado: {success} (esperado: {test_case['expected_success']})")
                    
                    results.append({
                        "test": test_case['name'],
                        "occupancy": test_case['occupancy'],
                        "expected": test_case['expected_success'],
                        "actual": success,
                        "status_code": response.status_code,
                        "response": result_data if success else response.text
                    })
                    
                else:
                    error_text = response.text
                    success = False
                    
                    if not test_case['expected_success']:
                        print(f"   ✅ Error esperado: {response.status_code}")
                        print(f"   📝 Mensaje: {error_text[:100]}...")
                    else:
                        print(f"   ❌ Error inesperado: {response.status_code}")
                        print(f"   📝 Mensaje: {error_text}")
                    
                    results.append({
                        "test": test_case['name'],
                        "occupancy": test_case['occupancy'],
                        "expected": test_case['expected_success'],
                        "actual": success,
                        "status_code": response.status_code,
                        "response": error_text
                    })
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                results.append({
                    "test": test_case['name'],
                    "occupancy": test_case['occupancy'],
                    "expected": test_case['expected_success'],
                    "actual": False,
                    "status_code": 0,
                    "response": str(e)
                })
            
            print()
        
        # Restaurar ocupación original
        print("🔄 Restaurando ocupación original...")
        try:
            response = requests.post(
                f"{base_url}/parking/{parking_id}/occupancy",
                json={"occupancy": current_occupancy},
                timeout=10
            )
            if response.status_code == 200:
                print(f"   ✅ Ocupación restaurada: {current_occupancy}")
            else:
                print(f"   ❌ Error restaurando ocupación: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Exception restaurando: {str(e)}")
        
        # Resumen final
        print()
        print("=" * 60)
        print("📊 RESUMEN DE RESULTADOS")
        print("=" * 60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['actual'] == r['expected'])
        
        print(f"Total tests: {total_tests}")
        print(f"Tests exitosos: {successful_tests}")
        print(f"Tests fallidos: {total_tests - successful_tests}")
        print(f"Porcentaje éxito: {successful_tests/total_tests*100:.1f}%")
        
        print()
        print("📋 RESULTADOS DETALLADOS:")
        for i, result in enumerate(results, 1):
            status = "✅" if result['actual'] == result['expected'] else "❌"
            print(f"  {i:2d}. {result['test']}: {status}")
            if result['actual'] != result['expected']:
                print(f"      Esperado: {result['expected']}, Actual: {result['actual']}")
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"occupancy_limits_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "parking": {
                    "id": parking_id,
                    "name": parking_name,
                    "max_capacity": max_capacity,
                    "original_occupancy": current_occupancy
                },
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: {filename}")
        
        if successful_tests == total_tests:
            print("\n🎉 ¡TODOS LOS TESTS EXITOSOS!")
            print("   - La nueva funcionalidad permite ocupación superior al máximo")
            print("   - Los límites están correctamente configurados")
            print("   - Se pueden manejar casos de coches mal aparcados")
        else:
            print("\n⚠️  ALGUNOS TESTS FALLARON")
            print("   - Revisar la implementación de los límites")
            print("   - Verificar la lógica de validación")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    test_occupancy_limits() 