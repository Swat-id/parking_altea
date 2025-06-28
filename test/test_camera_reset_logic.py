#!/usr/bin/env python3
"""
Script de prueba para validar la lógica de detección de reinicios de cámaras
y cálculo correcto de deltas.

Este script simula diferentes escenarios de reinicio de cámaras para verificar
que la lógica implementada funciona correctamente.
"""

import sys
import os

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from camera_server import detect_camera_reset, calculate_deltas_with_reset_handling

def test_camera_reset_logic():
    """Probar la lógica de detección de reinicios de cámaras"""
    
    print("🧪 PRUEBA DE LÓGICA DE REINICIO DE CÁMARAS")
    print("=" * 60)
    
    # Casos de prueba
    test_cases = [
        {
            "name": "Primera vez (contadores None)",
            "previous_in": None,
            "previous_out": None,
            "new_in": 5,
            "new_out": 2,
            "expected_reset": False,
            "expected_delta_in": 5,
            "expected_delta_out": 2
        },
        {
            "name": "Contador normal (sin reinicio)",
            "previous_in": 10,
            "previous_out": 5,
            "new_in": 12,
            "new_out": 7,
            "expected_reset": False,
            "expected_delta_in": 2,
            "expected_delta_out": 2
        },
        {
            "name": "Reinicio completo (ambos a 0)",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": 0,
            "new_out": 0,
            "expected_reset": True,
            "expected_delta_in": 0,
            "expected_delta_out": 0
        },
        {
            "name": "Reinicio parcial (in a 0, out con valor)",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": 0,
            "new_out": 3,
            "expected_reset": True,
            "expected_delta_in": 0,
            "expected_delta_out": 3
        },
        {
            "name": "Reinicio parcial (in con valor, out a 0)",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": 2,
            "new_out": 0,
            "expected_reset": True,
            "expected_delta_in": 2,
            "expected_delta_out": 0
        },
        {
            "name": "Reinicio con valores menores",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": 5,
            "new_out": 2,
            "expected_reset": True,
            "expected_delta_in": 5,
            "expected_delta_out": 2
        },
        {
            "name": "Reinicio solo in (menor valor)",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": 80,
            "new_out": 60,
            "expected_reset": True,
            "expected_delta_in": 80,
            "expected_delta_out": 10
        },
        {
            "name": "Reinicio solo out (menor valor)",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": 120,
            "new_out": 30,
            "expected_reset": True,
            "expected_delta_in": 20,
            "expected_delta_out": 30
        },
        {
            "name": "Valores negativos (error de cámara)",
            "previous_in": 100,
            "previous_out": 50,
            "new_in": -5,
            "new_out": 60,
            "expected_reset": True,
            "expected_delta_in": 0,  # Se corrige a 0
            "expected_delta_out": 10
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Caso {i}: {test_case['name']}")
        print(f"   Anterior: In={test_case['previous_in']}, Out={test_case['previous_out']}")
        print(f"   Nuevo: In={test_case['new_in']}, Out={test_case['new_out']}")
        
        # Probar función de detección de reinicio
        is_reset, adjusted_prev_in, adjusted_prev_out = detect_camera_reset(
            test_case['previous_in'],
            test_case['previous_out'],
            test_case['new_in'],
            test_case['new_out']
        )
        
        # Probar función de cálculo de deltas
        delta_in, delta_out, is_reset_delta, reset_info = calculate_deltas_with_reset_handling(
            test_case['previous_in'],
            test_case['previous_out'],
            test_case['new_in'],
            test_case['new_out']
        )
        
        print(f"   🔍 Detección reinicio: {is_reset} (esperado: {test_case['expected_reset']})")
        print(f"   📊 Deltas calculados: In={delta_in}, Out={delta_out}")
        print(f"   📊 Deltas esperados: In={test_case['expected_delta_in']}, Out={test_case['expected_delta_out']}")
        print(f"   🔧 Contadores ajustados: In={adjusted_prev_in}, Out={adjusted_prev_out}")
        
        # Verificar resultados
        reset_correct = is_reset == test_case['expected_reset']
        delta_in_correct = delta_in == test_case['expected_delta_in']
        delta_out_correct = delta_out == test_case['expected_delta_out']
        
        if reset_correct and delta_in_correct and delta_out_correct:
            print(f"   ✅ PASÓ")
            passed_tests += 1
        else:
            print(f"   ❌ FALLÓ")
            if not reset_correct:
                print(f"      - Detección de reinicio incorrecta")
            if not delta_in_correct:
                print(f"      - Delta In incorrecto")
            if not delta_out_correct:
                print(f"      - Delta Out incorrecto")
    
    print(f"\n📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Pruebas pasadas: {passed_tests}/{total_tests}")
    print(f"Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        return True
    else:
        print("⚠️  ALGUNAS PRUEBAS FALLARON")
        return False

def test_edge_cases():
    """Probar casos extremos y edge cases"""
    
    print(f"\n🔬 PRUEBAS DE CASOS EXTREMOS")
    print("=" * 60)
    
    edge_cases = [
        {
            "name": "Valores muy grandes",
            "previous_in": 999999,
            "previous_out": 999998,
            "new_in": 1000000,
            "new_out": 999999
        },
        {
            "name": "Valores muy pequeños",
            "previous_in": 1,
            "previous_out": 0,
            "new_in": 0,
            "new_out": 0
        },
        {
            "name": "Valores iguales (sin cambio)",
            "previous_in": 10,
            "previous_out": 5,
            "new_in": 10,
            "new_out": 5
        },
        {
            "name": "Solo un contador cambia",
            "previous_in": 10,
            "previous_out": 5,
            "new_in": 10,
            "new_out": 6
        }
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n📋 Caso extremo {i}: {case['name']}")
        print(f"   Anterior: In={case['previous_in']}, Out={case['previous_out']}")
        print(f"   Nuevo: In={case['new_in']}, Out={case['new_out']}")
        
        delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
            case['previous_in'],
            case['previous_out'],
            case['new_in'],
            case['new_out']
        )
        
        print(f"   🔍 Reinicio detectado: {is_reset}")
        print(f"   📊 Deltas: In={delta_in}, Out={delta_out}")
        print(f"   📊 Info reinicio: {reset_info}")

def test_real_scenarios():
    """Probar escenarios reales basados en logs de producción"""
    
    print(f"\n🏭 PRUEBAS DE ESCENARIOS REALES")
    print("=" * 60)
    
    real_scenarios = [
        {
            "name": "Cámara que se reinicia después de mucho tiempo",
            "previous_in": 15420,
            "previous_out": 15200,
            "new_in": 0,
            "new_out": 0,
            "description": "Cámara se reinicia y contadores vuelven a 0"
        },
        {
            "name": "Cámara que se reinicia y empieza a contar",
            "previous_in": 15420,
            "previous_out": 15200,
            "new_in": 3,
            "new_out": 1,
            "description": "Cámara se reinicia y empieza a contar desde valores bajos"
        },
        {
            "name": "Cámara con contador parcial reiniciado",
            "previous_in": 15420,
            "previous_out": 15200,
            "new_in": 15420,  # No cambió
            "new_out": 0,     # Se reinició
            "description": "Solo el contador de salida se reinició"
        }
    ]
    
    for i, scenario in enumerate(real_scenarios, 1):
        print(f"\n📋 Escenario real {i}: {scenario['name']}")
        print(f"   Descripción: {scenario['description']}")
        print(f"   Anterior: In={scenario['previous_in']}, Out={scenario['previous_out']}")
        print(f"   Nuevo: In={scenario['new_in']}, Out={scenario['new_out']}")
        
        delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
            scenario['previous_in'],
            scenario['previous_out'],
            scenario['new_in'],
            scenario['new_out']
        )
        
        print(f"   🔍 Reinicio detectado: {is_reset}")
        print(f"   📊 Deltas: In={delta_in}, Out={delta_out}")
        print(f"   📊 Impacto en ocupación: {delta_in - delta_out}")
        
        if is_reset:
            print(f"   ⚠️  REINICIO DETECTADO - Se ajustaron los contadores")
        else:
            print(f"   ✅ Comportamiento normal")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE LÓGICA DE REINICIO DE CÁMARAS")
    print("=" * 80)
    
    # Ejecutar pruebas principales
    main_tests_passed = test_camera_reset_logic()
    
    # Ejecutar pruebas de casos extremos
    test_edge_cases()
    
    # Ejecutar pruebas de escenarios reales
    test_real_scenarios()
    
    print(f"\n🎯 RESULTADO FINAL")
    print("=" * 80)
    if main_tests_passed:
        print("✅ La lógica de reinicio de cámaras está funcionando correctamente")
        print("✅ Se pueden detectar reinicios y calcular deltas apropiadamente")
        print("✅ El sistema manejará correctamente los contadores que se reinician a 0")
    else:
        print("❌ La lógica de reinicio de cámaras tiene problemas")
        print("❌ Se necesitan correcciones antes de implementar en producción")
    
    print(f"\n📝 NOTAS:")
    print("- Los reinicios se detectan cuando los nuevos contadores son menores que los anteriores")
    print("- En caso de reinicio, se asume que los contadores anteriores eran 0")
    print("- Los deltas se calculan siempre de forma ascendente")
    print("- Se validan deltas negativos (excepto en reinicios) y se corrigen a 0") 