#!/usr/bin/env python3
"""
Tests unitarios para CameraDetectionMethods
Valida la detección inteligente de reinicios y validación de deltas
"""

import unittest
from unittest.mock import Mock
from datetime import datetime, timedelta
import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from camera_detection_methods import CameraDetectionMethods
from camera_message_processor import ResetInfo, DeltaValidation
from models import Access


class TestCameraDetectionMethods(unittest.TestCase):
    """Tests unitarios para métodos de detección"""
    
    def setUp(self):
        """Configurar test environment"""
        self.mock_camera = Mock(spec=Access)
        self.mock_camera.id = 1
        self.mock_camera.device_name = 'test_camera'
        self.mock_camera.line = 1
    
    # =================== TESTS DE DETECCIÓN DE REINICIOS ===================
    
    def test_detect_reset_significant_decrease(self):
        """Test de detección de reinicio por disminución significativa"""
        # Setup: contadores altos que disminuyen >90%
        self.mock_camera.last_vehicle_in = 1000
        self.mock_camera.last_vehicle_out = 800
        self.mock_camera.last_message_received = datetime.now() - timedelta(minutes=30)
        
        message_data = {
            'vehicle_in': 50,  # Disminución >90%
            'vehicle_out': 40  # Disminución >90%
        }
        
        reset_info = CameraDetectionMethods.detect_reset_intelligent(self.mock_camera, message_data)
        
        self.assertTrue(reset_info.is_reset)
        self.assertTrue(reset_info.criteria_met['significant_decrease'])
        self.assertGreater(reset_info.confidence, 80)
        self.assertIn("significativa", reset_info.reason)
    
    def test_detect_reset_zero_reset(self):
        """Test de detección de reinicio por reset a cero"""
        # Setup: contadores altos que van a cero
        self.mock_camera.last_vehicle_in = 500
        self.mock_camera.last_vehicle_out = 300
        self.mock_camera.last_message_received = datetime.now() - timedelta(hours=1)
        
        message_data = {
            'vehicle_in': 0,   # Reset a cero
            'vehicle_out': 10  # Casi cero
        }
        
        reset_info = CameraDetectionMethods.detect_reset_intelligent(self.mock_camera, message_data)
        
        self.assertTrue(reset_info.is_reset)
        self.assertTrue(reset_info.criteria_met['zero_reset'])
        self.assertGreater(reset_info.confidence, 80)
    
    def test_detect_reset_time_gap(self):
        """Test de detección de reinicio por gap temporal"""
        # Setup: mucho tiempo sin mensajes + cambio significativo
        self.mock_camera.last_vehicle_in = 2000
        self.mock_camera.last_vehicle_out = 1500
        self.mock_camera.last_message_received = datetime.now() - timedelta(hours=15)  # >12 horas
        
        message_data = {
            'vehicle_in': 50,
            'vehicle_out': 30
        }
        
        reset_info = CameraDetectionMethods.detect_reset_intelligent(self.mock_camera, message_data)
        
        self.assertTrue(reset_info.is_reset)
        self.assertTrue(reset_info.criteria_met['time_gap'])
        self.assertTrue(reset_info.criteria_met['magnitude_check'])
    
    def test_detect_reset_false_positive_prevention(self):
        """Test de prevención de falsos positivos"""
        # Setup: cambio pequeño normal
        self.mock_camera.last_vehicle_in = 100
        self.mock_camera.last_vehicle_out = 80
        self.mock_camera.last_message_received = datetime.now() - timedelta(minutes=5)
        
        message_data = {
            'vehicle_in': 95,   # Disminución pequeña
            'vehicle_out': 78   # Disminución pequeña
        }
        
        reset_info = CameraDetectionMethods.detect_reset_intelligent(self.mock_camera, message_data)
        
        self.assertFalse(reset_info.is_reset)
        self.assertFalse(reset_info.criteria_met['significant_decrease'])
        self.assertFalse(reset_info.criteria_met['zero_reset'])
        self.assertLess(reset_info.confidence, 30)
    
    def test_detect_reset_both_counters_decrease(self):
        """Test de criterio adicional: ambos contadores disminuyen"""
        # Setup: ambos contadores disminuyen moderadamente
        self.mock_camera.last_vehicle_in = 200
        self.mock_camera.last_vehicle_out = 150
        self.mock_camera.last_message_received = datetime.now() - timedelta(hours=13)  # Gap temporal
        
        message_data = {
            'vehicle_in': 180,  # Disminución moderada
            'vehicle_out': 130  # Disminución moderada
        }
        
        reset_info = CameraDetectionMethods.detect_reset_intelligent(self.mock_camera, message_data)
        
        # Con gap temporal + ambos contadores disminuyen -> debería detectar reinicio
        self.assertTrue(reset_info.is_reset)
        self.assertTrue(reset_info.criteria_met['both_counters_decrease'])
        self.assertTrue(reset_info.criteria_met['time_gap'])
    
    def test_reset_confidence_calculation(self):
        """Test de cálculo de confianza de reinicio"""
        # Test con múltiples criterios
        criteria_strong = {
            'significant_decrease': True,
            'zero_reset': False,
            'time_gap': True,
            'magnitude_check': True,
            'both_counters_decrease': True
        }
        
        confidence = CameraDetectionMethods._calculate_reset_confidence(criteria_strong)
        
        # significant_decrease(40) + time_gap(10) + magnitude_check(15) + both_counters_decrease(10) = 75
        self.assertEqual(confidence, 75)
        
        # Test con criterio máximo
        criteria_max = {
            'significant_decrease': True,  # 40
            'zero_reset': True,           # 45
            'time_gap': True,            # 10
            'magnitude_check': True,      # 15
            'both_counters_decrease': True  # 10
        }
        
        confidence_max = CameraDetectionMethods._calculate_reset_confidence(criteria_max)
        
        # Debería ser 100 (máximo permitido)
        self.assertEqual(confidence_max, 100)
    
    # =================== TESTS DE VALIDACIÓN DE DELTAS ===================
    
    def test_validate_deltas_normal_case(self):
        """Test de validación exitosa de deltas normales"""
        self.mock_camera.last_message_received = datetime.now() - timedelta(minutes=2)
        
        message_data = {
            'vehicle_in': 110,
            'vehicle_out': 55
        }
        
        reset_info = ResetInfo(
            is_reset=False,
            criteria_met={},
            confidence=0.0,
            previous_in=100,
            previous_out=50,
            new_in=110,
            new_out=55,
            reason="No reset"
        )
        
        validation = CameraDetectionMethods.calculate_and_validate_deltas(
            self.mock_camera, message_data, reset_info
        )
        
        self.assertTrue(validation.valid)
        self.assertEqual(validation.delta_in, 10)
        self.assertEqual(validation.delta_out, 5)
        self.assertEqual(len(validation.validations), 0)
    
    def test_validate_deltas_reset_case(self):
        """Test de validación con reinicio detectado"""
        message_data = {
            'vehicle_in': 10,
            'vehicle_out': 5
        }
        
        reset_info = ResetInfo(
            is_reset=True,
            criteria_met={'zero_reset': True},
            confidence=90.0,
            previous_in=1000,
            previous_out=800,
            new_in=10,
            new_out=5,
            reason="Reset a cero detectado"
        )
        
        validation = CameraDetectionMethods.calculate_and_validate_deltas(
            self.mock_camera, message_data, reset_info
        )
        
        self.assertTrue(validation.valid)
        self.assertEqual(validation.delta_in, 0)  # Deltas a cero en reinicio
        self.assertEqual(validation.delta_out, 0)
        self.assertEqual(validation.reason, 'reset_detected_deltas_zeroed')
    
    def test_validate_deltas_excessive_magnitude(self):
        """Test de validación fallida por magnitud excesiva"""
        self.mock_camera.last_message_received = datetime.now() - timedelta(minutes=1)
        
        message_data = {
            'vehicle_in': 200,  # Delta de 100 (excesivo)
            'vehicle_out': 50
        }
        
        reset_info = ResetInfo(
            is_reset=False,
            criteria_met={},
            confidence=0.0,
            previous_in=100,
            previous_out=50,
            new_in=200,
            new_out=50,
            reason="No reset"
        )
        
        validation = CameraDetectionMethods.calculate_and_validate_deltas(
            self.mock_camera, message_data, reset_info
        )
        
        self.assertFalse(validation.valid)
        self.assertEqual(validation.delta_in, 0)  # Deltas a cero por invalidez
        self.assertEqual(validation.delta_out, 0)
        self.assertIn("excesivo", validation.reason)
    
    def test_validate_deltas_excessive_rate(self):
        """Test de validación fallida por tasa excesiva"""
        # Mensaje muy reciente (alta frecuencia)
        self.mock_camera.last_message_received = datetime.now() - timedelta(seconds=30)
        
        message_data = {
            'vehicle_in': 130,  # Delta de 30 en 30 segundos = 60 veh/min (excesivo)
            'vehicle_out': 50
        }
        
        reset_info = ResetInfo(
            is_reset=False,
            criteria_met={},
            confidence=0.0,
            previous_in=100,
            previous_out=50,
            new_in=130,
            new_out=50,
            reason="No reset"
        )
        
        validation = CameraDetectionMethods.calculate_and_validate_deltas(
            self.mock_camera, message_data, reset_info
        )
        
        self.assertFalse(validation.valid)
        self.assertIn("tasa de cambio excesiva", validation.reason)
    
    def test_validate_deltas_anomalous_pattern(self):
        """Test de detección de patrones anómalos"""
        self.mock_camera.last_message_received = datetime.now() - timedelta(minutes=5)
        
        # Caso 1: Solo salidas masivas sin entradas
        message_data_1 = {
            'vehicle_in': 100,  # Sin cambio
            'vehicle_out': 70   # Delta de 20 salidas
        }
        
        reset_info = ResetInfo(
            is_reset=False,
            criteria_met={},
            confidence=0.0,
            previous_in=100,
            previous_out=50,
            new_in=100,
            new_out=70,
            reason="No reset"
        )
        
        validation = CameraDetectionMethods.calculate_and_validate_deltas(
            self.mock_camera, message_data_1, reset_info
        )
        
        self.assertFalse(validation.valid)
        self.assertIn("solo salidas masivas", validation.reason)
    
    def test_validate_deltas_time_gap_permissive(self):
        """Test de permisividad con gap temporal"""
        # Gap temporal grande (más de 2 horas)
        self.mock_camera.last_message_received = datetime.now() - timedelta(hours=3)
        
        message_data = {
            'vehicle_in': 180,  # Delta grande pero con gap temporal
            'vehicle_out': 50
        }
        
        reset_info = ResetInfo(
            is_reset=False,
            criteria_met={},
            confidence=0.0,
            previous_in=100,
            previous_out=50,
            new_in=180,
            new_out=50,
            reason="No reset"
        )
        
        validation = CameraDetectionMethods.calculate_and_validate_deltas(
            self.mock_camera, message_data, reset_info
        )
        
        # Con gap temporal, debería ser más permisivo
        self.assertTrue(validation.valid)
        self.assertEqual(validation.delta_in, 80)
        self.assertEqual(validation.delta_out, 0)
    
    # =================== TESTS DE VALIDACIÓN DE OCUPACIÓN ===================
    
    def test_validate_parking_occupancy_normal(self):
        """Test de validación normal de ocupación de parking"""
        result = CameraDetectionMethods.validate_parking_occupancy(
            new_occupancy=150,
            max_capacity=200,
            current_occupancy=140,
            delta_in=15,
            delta_out=5
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['corrected_occupancy'], 150)
        self.assertFalse(result['needs_correction'])
    
    def test_validate_parking_occupancy_negative_extreme(self):
        """Test de corrección de ocupación muy negativa"""
        result = CameraDetectionMethods.validate_parking_occupancy(
            new_occupancy=-25,  # Muy negativo
            max_capacity=200,
            current_occupancy=10,
            delta_in=0,
            delta_out=35
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['corrected_occupancy'], -15)  # Corregido al mínimo
        self.assertTrue(result['needs_correction'])
        self.assertIn("muy negativa", result['reason'])
    
    def test_validate_parking_occupancy_excessive(self):
        """Test de corrección de ocupación excesiva"""
        result = CameraDetectionMethods.validate_parking_occupancy(
            new_occupancy=500,  # Muy alto (>200% capacidad)
            max_capacity=200,
            current_occupancy=180,
            delta_in=320,
            delta_out=0
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['corrected_occupancy'], 400)  # Corregido al máximo (200%)
        self.assertTrue(result['needs_correction'])
        self.assertIn("excesiva", result['reason'])
    
    def test_validate_parking_occupancy_impossible_exits(self):
        """Test de detección de salidas imposibles"""
        result = CameraDetectionMethods.validate_parking_occupancy(
            new_occupancy=50,
            max_capacity=200,
            current_occupancy=100,
            delta_in=5,
            delta_out=60  # Más salidas que vehículos disponibles (100+5)
        )
        
        self.assertFalse(result['valid'])
        self.assertIn("más salidas que vehículos disponibles", result['reason'])
    
    def test_validate_parking_occupancy_high_but_allowed(self):
        """Test de ocupación alta pero permitida"""
        result = CameraDetectionMethods.validate_parking_occupancy(
            new_occupancy=250,  # 125% de capacidad (alto pero <200%)
            max_capacity=200,
            current_occupancy=240,
            delta_in=15,
            delta_out=5
        )
        
        self.assertFalse(result['valid'])  # Genera validación pero no corrige
        self.assertEqual(result['corrected_occupancy'], 250)  # No corregido
        self.assertFalse(result['needs_correction'])
        self.assertIn("ocupación alta", result['reason'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
