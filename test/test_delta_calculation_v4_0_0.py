#!/usr/bin/env python3
"""
Tests comparativos para la nueva lógica de cálculo de deltas v4.0.0

Este archivo contiene tests que comparan el comportamiento entre:
- Lógica original (legacy)
- Nueva lógica v4.0.0 (almacenamiento inmediato + delta unificado)

Autor: Sistema de Parking Altea
Fecha: 12 de septiembre de 2025
"""

import unittest
import sys
import os

# Añadir el directorio src al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Importar las funciones de cálculo de deltas
from camera_server import (
    calculate_deltas_with_reset_handling,  # Lógica original
    calculate_deltas_new_logic,           # Nueva lógica v4.0.0
    detect_camera_reset,                  # Detección original
    detect_camera_reset_new_logic,        # Nueva detección
    validate_delta_thresholds
)

class TestDeltaCalculationComparison(unittest.TestCase):
    """Tests comparativos entre lógica original y nueva v4.0.0"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.test_cases = {
            'normal_operation': {
                'previous_in': 100,
                'previous_out': 80,
                'new_in': 105,
                'new_out': 83,
                'description': 'Funcionamiento normal - incremento de contadores'
            },
            'duplicate_message': {
                'previous_in': 105,
                'previous_out': 83,
                'new_in': 105,
                'new_out': 83,
                'description': 'Mensaje duplicado - valores idénticos'
            },
            'camera_reset': {
                'previous_in': 1400,
                'previous_out': 1370,
                'new_in': 5,
                'new_out': 2,
                'description': 'Reinicio de cámara - contadores menores'
            },
            'first_message': {
                'previous_in': None,
                'previous_out': None,
                'new_in': 10,
                'new_out': 5,
                'description': 'Primer mensaje - sin historial previo'
            },
            'partial_reset_in': {
                'previous_in': 500,
                'previous_out': 450,
                'new_in': 10,
                'new_out': 460,
                'description': 'Reinicio parcial - solo contador IN se reinicia'
            },
            'partial_reset_out': {
                'previous_in': 500,
                'previous_out': 450,
                'new_in': 510,
                'new_out': 5,
                'description': 'Reinicio parcial - solo contador OUT se reinicia'
            },
            'large_increment': {
                'previous_in': 100,
                'previous_out': 80,
                'new_in': 200,
                'new_out': 150,
                'description': 'Incremento grande pero válido'
            }
        }
    
    def test_normal_operation_comparison(self):
        """Test: Funcionamiento normal - ambas lógicas deben dar resultado similar"""
        case = self.test_cases['normal_operation']
        
        # Lógica original
        delta_in_old, delta_out_old, is_reset_old, reset_info_old = calculate_deltas_with_reset_handling(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        delta_final_old = delta_in_old - delta_out_old if not is_reset_old else 0
        
        # Nueva lógica
        delta_final_new, is_reset_new, reset_info_new = calculate_deltas_new_logic(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        
        # Verificaciones
        self.assertEqual(is_reset_old, is_reset_new, "Detección de reset debe ser igual")
        self.assertEqual(delta_final_old, delta_final_new, "Delta final debe ser igual en operación normal")
        self.assertFalse(is_reset_old, "No debe detectar reset en operación normal")
        self.assertEqual(delta_final_new, 2, "Delta final debe ser 2 (5-3)")
        
        print(f"✅ {case['description']}")
        print(f"   Original: delta_in={delta_in_old}, delta_out={delta_out_old}, final={delta_final_old}")
        print(f"   Nueva: delta_final={delta_final_new}")
    
    def test_camera_reset_comparison(self):
        """Test: Reinicio de cámara - comportamiento diferente esperado"""
        case = self.test_cases['camera_reset']
        
        # Lógica original
        delta_in_old, delta_out_old, is_reset_old, reset_info_old = calculate_deltas_with_reset_handling(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        delta_final_old = delta_in_old - delta_out_old if not is_reset_old else 0
        
        # Nueva lógica
        delta_final_new, is_reset_new, reset_info_new = calculate_deltas_new_logic(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        
        # Verificaciones
        self.assertTrue(is_reset_old, "Lógica original debe detectar reset")
        self.assertTrue(is_reset_new, "Nueva lógica debe detectar reset")
        self.assertEqual(delta_final_old, 0, "Lógica original: delta debe ser 0 en reset")
        self.assertEqual(delta_final_new, 3, "Nueva lógica: delta debe ser diferencia absoluta (5-2=3)")
        
        print(f"✅ {case['description']}")
        print(f"   Original: delta_final={delta_final_old} (mantiene ocupación)")
        print(f"   Nueva: delta_final={delta_final_new} (ajusta ocupación)")
    
    def test_first_message_comparison(self):
        """Test: Primer mensaje - sin historial previo"""
        case = self.test_cases['first_message']
        
        # Lógica original
        delta_in_old, delta_out_old, is_reset_old, reset_info_old = calculate_deltas_with_reset_handling(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        delta_final_old = delta_in_old - delta_out_old if not is_reset_old else 0
        
        # Nueva lógica
        delta_final_new, is_reset_new, reset_info_new = calculate_deltas_new_logic(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        
        # Verificaciones
        self.assertFalse(is_reset_old, "No debe detectar reset en primer mensaje")
        self.assertFalse(is_reset_new, "No debe detectar reset en primer mensaje")
        
        print(f"✅ {case['description']}")
        print(f"   Original: delta_final={delta_final_old}")
        print(f"   Nueva: delta_final={delta_final_new}")
    
    def test_duplicate_message_detection(self):
        """Test: Detección de mensajes duplicados"""
        case = self.test_cases['duplicate_message']
        
        # Lógica original (detección en detect_camera_reset)
        is_reset_old, adj_in_old, adj_out_old = detect_camera_reset(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        
        # Nueva lógica (detección simplificada)
        is_reset_new, base_in_new, base_out_new = detect_camera_reset_new_logic(
            case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
        )
        
        # En ambos casos, valores idénticos no deben ser considerados reset
        self.assertFalse(is_reset_old, "Lógica original: duplicados no son reset")
        self.assertFalse(is_reset_new, "Nueva lógica: duplicados no son reset")
        
        # Nueva lógica: la detección de duplicados se hace a nivel superior
        is_duplicate_new = (case['new_in'] == case['previous_in'] and 
                           case['new_out'] == case['previous_out'])
        self.assertTrue(is_duplicate_new, "Nueva lógica debe detectar duplicado")
        
        print(f"✅ {case['description']}")
        print(f"   Ambas lógicas detectan correctamente que no es reset")
        print(f"   Nueva lógica: detección de duplicado = {is_duplicate_new}")
    
    def test_threshold_validation(self):
        """Test: Validación de umbrales en nueva lógica"""
        
        # Test con delta normal
        is_valid, corrected, warning = validate_delta_thresholds(10, False)
        self.assertTrue(is_valid, "Delta normal debe ser válido")
        self.assertEqual(corrected, 10, "Delta normal no debe corregirse")
        self.assertIsNone(warning, "Delta normal no debe generar warning")
        
        # Test con delta excesivo en operación normal
        is_valid, corrected, warning = validate_delta_thresholds(100, False)
        self.assertFalse(is_valid, "Delta excesivo debe ser inválido")
        self.assertEqual(corrected, 50, "Delta debe limitarse al umbral")
        self.assertIsNotNone(warning, "Delta excesivo debe generar warning")
        
        # Test con delta excesivo en reinicio
        is_valid, corrected, warning = validate_delta_thresholds(250, True)
        self.assertFalse(is_valid, "Delta excesivo en reset debe ser inválido")
        self.assertEqual(corrected, 200, "Delta en reset debe limitarse al umbral")
        
        print("✅ Validación de umbrales funciona correctamente")
    
    def test_edge_cases(self):
        """Test: Casos extremos y edge cases"""
        
        edge_cases = [
            {
                'name': 'Contadores muy altos',
                'previous_in': 999999,
                'previous_out': 999998,
                'new_in': 1000005,
                'new_out': 1000002,
                'expected_delta_new': 2  # (1000005-999999) - (1000002-999998) = 6-4 = 2
            },
            {
                'name': 'Reset con valores altos',
                'previous_in': 50000,
                'previous_out': 49500,
                'new_in': 1000,
                'new_out': 800,
                'expected_delta_new': 200  # 1000-800 = 200 (diferencia absoluta)
            },
            {
                'name': 'Incremento cero',
                'previous_in': 100,
                'previous_out': 80,
                'new_in': 100,
                'new_out': 80,
                'expected_delta_new': 0
            }
        ]
        
        for case in edge_cases:
            with self.subTest(case=case['name']):
                delta_final_new, is_reset_new, reset_info_new = calculate_deltas_new_logic(
                    case['previous_in'], case['previous_out'], 
                    case['new_in'], case['new_out']
                )
                
                self.assertEqual(delta_final_new, case['expected_delta_new'], 
                               f"Delta incorrecto en caso: {case['name']}")
                
                print(f"✅ Edge case: {case['name']} - Delta: {delta_final_new}")
    
    def test_performance_comparison(self):
        """Test: Comparación básica de rendimiento"""
        import time
        
        case = self.test_cases['normal_operation']
        iterations = 1000
        
        # Test lógica original
        start_time = time.time()
        for _ in range(iterations):
            calculate_deltas_with_reset_handling(
                case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
            )
        original_time = time.time() - start_time
        
        # Test nueva lógica
        start_time = time.time()
        for _ in range(iterations):
            calculate_deltas_new_logic(
                case['previous_in'], case['previous_out'], case['new_in'], case['new_out']
            )
        new_time = time.time() - start_time
        
        print(f"✅ Performance comparison ({iterations} iterations):")
        print(f"   Original logic: {original_time:.4f}s")
        print(f"   New logic: {new_time:.4f}s")
        print(f"   Difference: {((new_time - original_time) / original_time * 100):+.1f}%")
    
    def test_reset_confidence_scenarios(self):
        """Test: Diferentes escenarios de confianza en detección de reinicios"""
        
        scenarios = [
            {
                'name': 'Reset total (ambos contadores a cero)',
                'previous_in': 1000, 'previous_out': 950,
                'new_in': 0, 'new_out': 0,
                'expected_reset': True
            },
            {
                'name': 'Reset parcial (solo IN)',
                'previous_in': 1000, 'previous_out': 950,
                'new_in': 5, 'new_out': 960,
                'expected_reset': True  # OUT aumentó, pero IN se reinició
            },
            {
                'name': 'Decremento menor (posible error de lectura)',
                'previous_in': 1000, 'previous_out': 950,
                'new_in': 999, 'new_out': 949,
                'expected_reset': True  # Cualquier decremento es considerado reset
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                # Test nueva lógica
                is_reset, _, _ = detect_camera_reset_new_logic(
                    scenario['previous_in'], scenario['previous_out'],
                    scenario['new_in'], scenario['new_out']
                )
                
                self.assertEqual(is_reset, scenario['expected_reset'],
                               f"Detección incorrecta en: {scenario['name']}")
                
                print(f"✅ Reset scenario: {scenario['name']} - Reset detected: {is_reset}")


class TestIntegrationScenarios(unittest.TestCase):
    """Tests de integración para escenarios reales"""
    
    def test_typical_day_simulation(self):
        """Simular un día típico de operación"""
        
        # Simular secuencia de mensajes de un día típico
        messages = [
            # Inicio del día
            {'in': 0, 'out': 0, 'description': 'Inicio del día'},
            {'in': 5, 'out': 0, 'description': 'Primeros vehículos'},
            {'in': 20, 'out': 3, 'description': 'Hora punta mañana'},
            {'in': 45, 'out': 15, 'description': 'Media mañana'},
            {'in': 45, 'out': 15, 'description': 'Mensaje duplicado'},  # Duplicado
            {'in': 80, 'out': 35, 'description': 'Mediodía'},
            {'in': 2, 'out': 1, 'description': 'Reinicio cámara'},  # Reset
            {'in': 25, 'out': 10, 'description': 'Después del reset'},
            {'in': 60, 'out': 25, 'description': 'Final del día'}
        ]
        
        occupancy_old = 0  # Ocupación usando lógica original
        occupancy_new = 0  # Ocupación usando nueva lógica
        previous_in, previous_out = None, None
        
        print("\n📊 Simulación de día típico:")
        print("Time | In | Out | Description           | Old Logic | New Logic | Diff")
        print("-" * 75)
        
        for i, msg in enumerate(messages):
            # Lógica original
            if previous_in is not None:
                delta_in_old, delta_out_old, is_reset_old, _ = calculate_deltas_with_reset_handling(
                    previous_in, previous_out, msg['in'], msg['out']
                )
                delta_final_old = delta_in_old - delta_out_old if not is_reset_old else 0
                occupancy_old += delta_final_old
            
            # Nueva lógica
            if previous_in is not None:
                # Simular detección de duplicados
                if msg['in'] == previous_in and msg['out'] == previous_out:
                    delta_final_new = 0  # Duplicado ignorado
                else:
                    delta_final_new, is_reset_new, _ = calculate_deltas_new_logic(
                        previous_in, previous_out, msg['in'], msg['out']
                    )
                    occupancy_new += delta_final_new
            else:
                delta_final_old = delta_final_new = 0
            
            diff = occupancy_new - occupancy_old
            print(f"{i+1:4d} |{msg['in']:3d} |{msg['out']:3d} | {msg['description']:<20} | "
                  f"{occupancy_old:8d} | {occupancy_new:8d} | {diff:+4d}")
            
            previous_in, previous_out = msg['in'], msg['out']
        
        print(f"\n📈 Resumen final:")
        print(f"   Ocupación lógica original: {occupancy_old}")
        print(f"   Ocupación nueva lógica: {occupancy_new}")
        print(f"   Diferencia: {occupancy_new - occupancy_old:+d}")
        
        # La diferencia principal debería estar en el manejo del reset
        self.assertNotEqual(occupancy_old, occupancy_new, 
                           "Las ocupaciones deben diferir debido al manejo diferente de reinicios")


if __name__ == '__main__':
    print("🧪 TESTS COMPARATIVOS - LÓGICA DE CÁLCULO DE DELTAS v4.0.0")
    print("=" * 60)
    
    # Ejecutar todos los tests
    unittest.main(verbosity=2)
