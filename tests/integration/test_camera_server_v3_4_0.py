#!/usr/bin/env python3
"""
Tests de integración para Camera Server v3.4.0
Valida el funcionamiento completo del servidor integrado con CameraMessageProcessor
"""

import unittest
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Importar el camera server
import camera_server_v3_4_0 as camera_server


class TestCameraServerV340Integration(unittest.TestCase):
    """Tests de integración para Camera Server v3.4.0"""
    
    @classmethod
    def setUpClass(cls):
        """Configurar test environment a nivel de clase"""
        # Configurar Flask para testing
        camera_server.app.config['TESTING'] = True
        cls.client = camera_server.app.test_client()
        cls.app_context = camera_server.app.app_context()
        cls.app_context.push()
    
    @classmethod
    def tearDownClass(cls):
        """Limpiar después de todos los tests"""
        cls.app_context.pop()
        # Shutdown del procesador
        camera_server.message_processor.shutdown()
    
    def setUp(self):
        """Configurar cada test individual"""
        # Reset de estadísticas para cada test
        with camera_server.message_processor._stats_lock:
            for key in camera_server.message_processor._stats:
                if isinstance(camera_server.message_processor._stats[key], (int, float)):
                    camera_server.message_processor._stats[key] = 0
                elif isinstance(camera_server.message_processor._stats[key], list):
                    camera_server.message_processor._stats[key] = []
    
    # =================== TESTS DEL ENDPOINT PRINCIPAL ===================
    
    @patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation')
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_camera_endpoint_success(self, mock_process, mock_find_cameras):
        """Test de procesamiento exitoso en endpoint /camera"""
        # Mock del procesamiento exitoso
        from camera_message_processor import ProcessingResult
        
        mock_process.return_value = ProcessingResult(
            status='success',
            message_id='test_123',
            processing_time_ms=150.0,
            updated_parkings=[{
                'name': 'Test Parking',
                'new_occupancy': 100,
                'status': 'LIBRE'
            }],
            reset_detected=False
        )
        
        # Datos de test
        test_data = {
            'device': 'test_camera',
            'line': 1,
            'Vehicle In': 100,
            'Vehicle Out': 50
        }
        
        # Realizar petición
        response = self.client.post('/camera', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'ok')
        self.assertIn('processing_time_ms', response_data)
        self.assertEqual(response_data['version'], 'v3.4.0')
        self.assertIn('note', response_data)  # Nota sobre worker de paneles
        self.assertEqual(len(response_data['parkings']), 1)
    
    def test_camera_endpoint_invalid_json(self):
        """Test de manejo de JSON inválido"""
        response = self.client.post('/camera',
                                  data='invalid json{',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('Invalid JSON format', response_data['error'])
        self.assertEqual(response_data['version'], 'v3.4.0')
    
    def test_camera_endpoint_empty_data(self):
        """Test de manejo de datos vacíos"""
        response = self.client.post('/camera',
                                  data='',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['version'], 'v3.4.0')
    
    def test_camera_endpoint_missing_fields(self):
        """Test de manejo de campos faltantes"""
        test_data = {
            'device': 'test_camera'
            # Faltan line, Vehicle In, Vehicle Out
        }
        
        response = self.client.post('/camera',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('Campos faltantes', response_data['error'])
    
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_camera_endpoint_duplicate_message(self, mock_process):
        """Test de manejo de mensaje duplicado"""
        from camera_message_processor import ProcessingResult
        
        mock_process.return_value = ProcessingResult(
            status='duplicate',
            message_id='test_dup_123',
            processing_time_ms=50.0,
            updated_parkings=[],
            reset_detected=False
        )
        
        test_data = {
            'device': 'test_camera',
            'line': 1,
            'Vehicle In': 100,
            'Vehicle Out': 50
        }
        
        response = self.client.post('/camera',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'duplicate')
        self.assertIn('duplicado', response_data['message'])
    
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_camera_endpoint_camera_not_found(self, mock_process):
        """Test de cámara no encontrada"""
        from camera_message_processor import ProcessingResult
        
        mock_process.return_value = ProcessingResult(
            status='camera_not_found',
            message_id='test_notfound_123',
            processing_time_ms=25.0,
            updated_parkings=[],
            reset_detected=False,
            error='Camera not found: device=unknown, line=99'
        )
        
        test_data = {
            'device': 'unknown_camera',
            'line': 99,
            'Vehicle In': 100,
            'Vehicle Out': 50
        }
        
        response = self.client.post('/camera',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('Camera not found', response_data['error'])
    
    # =================== TESTS DE CONCURRENCIA ===================
    
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_concurrent_requests(self, mock_process):
        """Test de procesamiento concurrente de múltiples requests"""
        from camera_message_processor import ProcessingResult
        
        # Mock que simula procesamiento exitoso con delay
        def mock_processing(*args, **kwargs):
            time.sleep(0.1)  # Simular procesamiento
            return ProcessingResult(
                status='success',
                message_id=f'concurrent_{int(time.time() * 1000)}',
                processing_time_ms=100.0,
                updated_parkings=[],
                reset_detected=False
            )
        
        mock_process.side_effect = mock_processing
        
        # Crear múltiples requests concurrentes
        def send_request(camera_id):
            test_data = {
                'device': f'camera_{camera_id}',
                'line': 1,
                'Vehicle In': 100 + camera_id,
                'Vehicle Out': 50 + camera_id
            }
            
            response = self.client.post('/camera',
                                      data=json.dumps(test_data),
                                      content_type='application/json')
            return response.status_code, json.loads(response.data)
        
        # Enviar 5 requests concurrentes
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_request, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verificar que todos fueron exitosos
        for status_code, response_data in results:
            self.assertEqual(status_code, 200)
            self.assertEqual(response_data['status'], 'ok')
            self.assertEqual(response_data['version'], 'v3.4.0')
    
    # =================== TESTS DE NUEVOS ENDPOINTS ===================
    
    def test_stats_endpoint(self):
        """Test del endpoint /camera/stats"""
        response = self.client.get('/camera/stats')
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['version'], 'v3.4.0')
        self.assertIn('current_time', response_data)
        self.assertIn('processor_config', response_data)
        self.assertIn('messages_received', response_data)
        self.assertIn('messages_processed', response_data)
    
    def test_health_endpoint(self):
        """Test del endpoint /camera/health"""
        response = self.client.get('/camera/health')
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('status', response_data)
        self.assertEqual(response_data['version'], 'v3.4.0')
        self.assertIn('stats_summary', response_data)
        self.assertIn('uptime_seconds', response_data)
    
    def test_version_endpoint(self):
        """Test del endpoint /camera/version"""
        response = self.client.get('/camera/version')
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['version'], 'v3.4.0')
        self.assertIn('features', response_data)
        self.assertIn('performance', response_data)
        self.assertIn('compatibility', response_data)
        
        # Verificar características específicas
        self.assertIn('Concurrent message processing', response_data['features'])
        self.assertIn('Separated panel updates', response_data['features'])
    
    # =================== TESTS DE RENDIMIENTO ===================
    
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_response_time_under_200ms(self, mock_process):
        """Test de tiempo de respuesta bajo 200ms"""
        from camera_message_processor import ProcessingResult
        
        # Mock de procesamiento rápido
        mock_process.return_value = ProcessingResult(
            status='success',
            message_id='fast_test',
            processing_time_ms=50.0,
            updated_parkings=[],
            reset_detected=False
        )
        
        test_data = {
            'device': 'fast_camera',
            'line': 1,
            'Vehicle In': 100,
            'Vehicle Out': 50
        }
        
        start_time = time.time()
        response = self.client.post('/camera',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        end_time = time.time()
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar tiempo de respuesta
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 200, f"Response time {response_time_ms:.2f}ms exceeds 200ms target")
        
        # Verificar tiempo reportado en respuesta
        response_data = json.loads(response.data)
        self.assertLess(response_data['processing_time_ms'], 200)
    
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_throughput_multiple_messages(self, mock_process):
        """Test de throughput con múltiples mensajes"""
        from camera_message_processor import ProcessingResult
        
        # Mock de procesamiento rápido
        mock_process.return_value = ProcessingResult(
            status='success',
            message_id='throughput_test',
            processing_time_ms=10.0,
            updated_parkings=[],
            reset_detected=False
        )
        
        # Enviar 20 mensajes y medir throughput
        message_count = 20
        start_time = time.time()
        
        for i in range(message_count):
            test_data = {
                'device': f'throughput_camera_{i}',
                'line': 1,
                'Vehicle In': 100 + i,
                'Vehicle Out': 50 + i
            }
            
            response = self.client.post('/camera',
                                      data=json.dumps(test_data),
                                      content_type='application/json')
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        
        # Calcular throughput
        total_time = end_time - start_time
        throughput = message_count / total_time
        
        # Verificar que alcanza al menos 10 msg/s
        self.assertGreater(throughput, 10, f"Throughput {throughput:.2f} msg/s below target of 10 msg/s")
    
    # =================== TESTS DE COMPATIBILIDAD ===================
    
    @patch('camera_message_processor.CameraMessageProcessor._process_single_message')
    def test_backward_compatibility_response_format(self, mock_process):
        """Test de compatibilidad hacia atrás en formato de respuesta"""
        from camera_message_processor import ProcessingResult
        
        mock_process.return_value = ProcessingResult(
            status='success',
            message_id='compat_test',
            processing_time_ms=75.0,
            updated_parkings=[{
                'name': 'Parking Compat',
                'new_occupancy': 85,
                'status': 'DENSO'
            }],
            reset_detected=True
        )
        
        # Formato de datos compatible con versión anterior
        test_data = {
            'device': 'compat_camera',
            'line': 1,
            'Vehicle In': 100,
            'Vehicle Out': 50
        }
        
        response = self.client.post('/camera',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        
        # Verificar campos compatibles hacia atrás
        expected_fields = ['status', 'processing_time_ms', 'updated_parkings', 'parkings']
        for field in expected_fields:
            self.assertIn(field, response_data)
        
        # Verificar formato de parkings
        self.assertIsInstance(response_data['parkings'], list)
        if response_data['parkings']:
            parking = response_data['parkings'][0]
            self.assertIn('name', parking)
            self.assertIn('occupancy', parking)
            self.assertIn('status', parking)
        
        # Verificar campos nuevos
        self.assertEqual(response_data['version'], 'v3.4.0')
        self.assertIn('note', response_data)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)
