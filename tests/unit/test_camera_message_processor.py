#!/usr/bin/env python3
"""
Tests unitarios para CameraMessageProcessor
Valida el funcionamiento correcto de la gestión de concurrencia y procesamiento de mensajes
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future
import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from camera_message_processor import CameraMessageProcessor, ProcessingResult, ResetInfo, DeltaValidation
from models import Access


class TestCameraMessageProcessor(unittest.TestCase):
    """Tests unitarios para CameraMessageProcessor"""
    
    def setUp(self):
        """Configurar test environment"""
        self.processor = CameraMessageProcessor(max_workers=3, cache_duration=10)
        
        # Mock de base de datos
        self.mock_session = Mock()
        self.processor.Session = Mock(return_value=self.mock_session)
    
    def tearDown(self):
        """Limpiar después de tests"""
        self.processor.shutdown()
    
    # =================== TESTS DE GESTIÓN DE CONCURRENCIA ===================
    
    def test_process_message_async_returns_future(self):
        """Test que process_message_async retorna un Future"""
        message_data = {
            'device': 'test_camera',
            'line': 1,
            'vehicle_in': 100,
            'vehicle_out': 50
        }
        
        with patch.object(self.processor, '_process_single_message') as mock_process:
            mock_process.return_value = ProcessingResult(
                status='success',
                message_id='test_123',
                processing_time_ms=100.0,
                updated_parkings=[],
                reset_detected=False
            )
            
            future = self.processor.process_message_async(message_data)
            
            self.assertIsInstance(future, Future)
            result = future.result(timeout=5)
            self.assertEqual(result.status, 'success')
    
    def test_concurrent_message_processing(self):
        """Test de procesamiento concurrente de múltiples mensajes"""
        message_count = 5
        messages = [
            {
                'device': f'camera_{i}',
                'line': 1,
                'vehicle_in': 100 + i,
                'vehicle_out': 50 + i
            }
            for i in range(message_count)
        ]
        
        # Mock del procesamiento
        with patch.object(self.processor, '_process_single_message') as mock_process:
            mock_process.return_value = ProcessingResult(
                status='success',
                message_id='test',
                processing_time_ms=50.0,
                updated_parkings=[],
                reset_detected=False
            )
            
            # Enviar todos los mensajes concurrentemente
            futures = [self.processor.process_message_async(msg) for msg in messages]
            
            # Esperar todos los resultados
            results = [future.result(timeout=5) for future in futures]
            
            # Verificar que todos se procesaron exitosamente
            self.assertEqual(len(results), message_count)
            for result in results:
                self.assertEqual(result.status, 'success')
            
            # Verificar que se llamó al procesamiento el número correcto de veces
            self.assertEqual(mock_process.call_count, message_count)
    
    # =================== TESTS DE DETECCIÓN DE DUPLICADOS ===================
    
    def test_duplicate_message_detection(self):
        """Test de detección de mensajes duplicados"""
        message_data = {
            'device': 'test_camera',
            'line': 1,
            'vehicle_in': 100,
            'vehicle_out': 50
        }
        
        # Primer mensaje no debe ser duplicado
        is_duplicate_1 = self.processor._is_duplicate_message_threadsafe(message_data)
        self.assertFalse(is_duplicate_1)
        
        # Segundo mensaje idéntico debe ser duplicado
        is_duplicate_2 = self.processor._is_duplicate_message_threadsafe(message_data)
        self.assertTrue(is_duplicate_2)
    
    def test_duplicate_cache_expiration(self):
        """Test de expiración del cache de duplicados"""
        # Usar cache duration muy corto para el test
        processor = CameraMessageProcessor(max_workers=1, cache_duration=1)
        
        message_data = {
            'device': 'test_camera',
            'line': 1,
            'vehicle_in': 100,
            'vehicle_out': 50
        }
        
        # Primer mensaje
        is_duplicate_1 = processor._is_duplicate_message_threadsafe(message_data)
        self.assertFalse(is_duplicate_1)
        
        # Esperar a que expire el cache
        time.sleep(2)
        
        # Mensaje después de expiración no debe ser duplicado
        is_duplicate_2 = processor._is_duplicate_message_threadsafe(message_data)
        self.assertFalse(is_duplicate_2)
        
        processor.shutdown()
    
    def test_thread_safety_duplicate_detection(self):
        """Test de thread safety en detección de duplicados"""
        message_data = {
            'device': 'test_camera',
            'line': 1,
            'vehicle_in': 100,
            'vehicle_out': 50
        }
        
        results = []
        
        def check_duplicate():
            result = self.processor._is_duplicate_message_threadsafe(message_data)
            results.append(result)
        
        # Crear múltiples threads que verifican el mismo mensaje
        threads = [threading.Thread(target=check_duplicate) for _ in range(10)]
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join()
        
        # Solo uno debe retornar False (no duplicado), el resto True (duplicado)
        false_count = results.count(False)
        true_count = results.count(True)
        
        self.assertEqual(false_count, 1)
        self.assertEqual(true_count, 9)
    
    # =================== TESTS DE VALIDACIÓN DE CÁMARAS ===================
    
    def test_find_cameras_with_validation_success(self):
        """Test de búsqueda exitosa de cámaras"""
        # Mock de cámara encontrada
        mock_camera = Mock(spec=Access)
        mock_camera.id = 1
        mock_camera.device_name = 'test_camera'
        mock_camera.line = 1
        
        self.mock_session.query().filter().all.return_value = [mock_camera]
        
        message_data = {
            'device': 'test_camera',
            'line': 1
        }
        
        cameras = self.processor._find_cameras_with_validation(self.mock_session, message_data)
        
        self.assertEqual(len(cameras), 1)
        self.assertEqual(cameras[0], mock_camera)
    
    def test_find_cameras_with_validation_not_found(self):
        """Test cuando no se encuentra cámara"""
        # Mock de búsqueda sin resultados
        self.mock_session.query().filter().all.return_value = []
        
        message_data = {
            'device': 'nonexistent_camera',
            'line': 1
        }
        
        cameras = self.processor._find_cameras_with_validation(self.mock_session, message_data)
        
        self.assertEqual(len(cameras), 0)
    
    def test_find_cameras_empty_device_name(self):
        """Test con device name vacío"""
        message_data = {
            'device': '',
            'line': 1
        }
        
        cameras = self.processor._find_cameras_with_validation(self.mock_session, message_data)
        
        self.assertEqual(len(cameras), 0)
    
    # =================== TESTS DE ESTADÍSTICAS ===================
    
    def test_stats_initialization(self):
        """Test de inicialización correcta de estadísticas"""
        stats = self.processor.get_stats()
        
        expected_keys = [
            'messages_received', 'messages_processed', 'duplicates_detected',
            'resets_detected', 'concurrent_messages', 'processing_times',
            'errors', 'validations_failed', 'avg_processing_time',
            'max_processing_time', 'min_processing_time'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)
        
        # Verificar valores iniciales
        self.assertEqual(stats['messages_received'], 0)
        self.assertEqual(stats['messages_processed'], 0)
        self.assertEqual(stats['concurrent_messages'], 0)
    
    def test_stats_thread_safety(self):
        """Test de thread safety de estadísticas"""
        def increment_stats():
            with self.processor._stats_lock:
                self.processor._stats['messages_received'] += 1
        
        # Crear múltiples threads que incrementan stats
        threads = [threading.Thread(target=increment_stats) for _ in range(100)]
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join()
        
        # Verificar que el contador es correcto
        stats = self.processor.get_stats()
        self.assertEqual(stats['messages_received'], 100)
    
    # =================== TESTS DE MANEJO DE ERRORES ===================
    
    def test_database_error_handling(self):
        """Test de manejo de errores de base de datos"""
        message_data = {
            'device': 'test_camera',
            'line': 1,
            'vehicle_in': 100,
            'vehicle_out': 50
        }
        
        # Mock de error en base de datos
        self.mock_session.query.side_effect = Exception("Database connection error")
        
        with patch.object(self.processor, '_is_duplicate_message_threadsafe', return_value=False):
            result = self.processor._process_single_message(message_data)
        
        self.assertEqual(result.status, 'error')
        self.assertIn("Database connection error", result.error)
    
    def test_message_id_generation(self):
        """Test de generación de IDs únicos para mensajes"""
        message_data = {
            'device': 'test_camera',
            'line': 1
        }
        
        # Generar múltiples IDs
        ids = [self.processor._generate_message_id(message_data) for _ in range(10)]
        
        # Verificar que todos son únicos
        self.assertEqual(len(ids), len(set(ids)))
        
        # Verificar formato esperado
        for msg_id in ids:
            self.assertIn('test_camera_1_', msg_id)
    
    # =================== TESTS DE INTEGRACIÓN ===================
    
    @patch('camera_message_processor.CameraDetectionMethods')
    @patch('camera_message_processor.CameraAtomicOperations')
    def test_full_message_processing_flow(self, mock_atomic_ops, mock_detection):
        """Test del flujo completo de procesamiento de mensaje"""
        # Setup mocks
        mock_camera = Mock(spec=Access)
        mock_camera.id = 1
        
        self.mock_session.query().filter().all.return_value = [mock_camera]
        
        # Mock de detección de reinicio
        reset_info = ResetInfo(
            is_reset=False,
            criteria_met={},
            confidence=0.0,
            previous_in=90,
            previous_out=40,
            new_in=100,
            new_out=50,
            reason="No reset detected"
        )
        mock_detection.detect_reset_intelligent.return_value = reset_info
        
        # Mock de validación de deltas
        delta_validation = DeltaValidation(
            valid=True,
            delta_in=10,
            delta_out=10,
            validations=[],
            reason="valid"
        )
        mock_detection.calculate_and_validate_deltas.return_value = delta_validation
        
        # Mock de actualización atómica
        updated_parkings = [{
            'parking_id': 1,
            'name': 'Test Parking',
            'new_occupancy': 100,
            'change': 0
        }]
        mock_atomic_ops.update_occupancy_atomic.return_value = updated_parkings
        
        message_data = {
            'device': 'test_camera',
            'line': 1,
            'vehicle_in': 100,
            'vehicle_out': 50,
            'source_ip': '192.168.1.100'
        }
        
        # Procesar mensaje
        result = self.processor._process_single_message(message_data)
        
        # Verificar resultado
        self.assertEqual(result.status, 'success')
        self.assertEqual(len(result.updated_parkings), 1)
        self.assertFalse(result.reset_detected)
        
        # Verificar que se llamaron los métodos correctos
        mock_detection.detect_reset_intelligent.assert_called_once()
        mock_detection.calculate_and_validate_deltas.assert_called_once()
        mock_atomic_ops.update_occupancy_atomic.assert_called_once()


if __name__ == '__main__':
    # Configurar logging para tests
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)
