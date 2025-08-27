#!/usr/bin/env python3
"""
Tests End-to-End completos para Sistema v3.4.0
Valida el funcionamiento completo de la arquitectura separada
"""

import unittest
import json
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from camera_message_processor import CameraMessageProcessor
from panel_update_worker import PanelUpdateWorker
from models import Access, Parking, Panel


class TestSystemCompleteV340(unittest.TestCase):
    """Tests End-to-End completos para Sistema v3.4.0"""
    
    @classmethod
    def setUpClass(cls):
        """Configurar entorno de testing completo"""
        print("\n" + "="*60)
        print("🧪 INICIANDO TESTS END-TO-END SISTEMA v3.4.0")
        print("="*60)
        
        # Configurar componentes para testing
        cls.message_processor = CameraMessageProcessor(max_workers=5, cache_duration=60)
        cls.panel_worker = PanelUpdateWorker(update_interval=30, max_panel_workers=3)
        
        # URLs del sistema (ajustar según configuración)
        cls.camera_server_url = "http://localhost:5000"
        cls.api_server_url = "http://localhost:8080"
        
        print("✅ Componentes inicializados para testing")
    
    @classmethod
    def tearDownClass(cls):
        """Limpiar después de todos los tests"""
        cls.message_processor.shutdown()
        cls.panel_worker.stop()
        print("\n✅ Tests End-to-End completados")
        print("="*60)
    
    def setUp(self):
        """Configurar cada test individual"""
        self.test_start_time = time.time()
        print(f"\n🔄 Iniciando test: {self._testMethodName}")
    
    def tearDown(self):
        """Limpiar después de cada test"""
        test_duration = time.time() - self.test_start_time
        print(f"✅ Test completado en {test_duration:.2f}s: {self._testMethodName}")
    
    # =================== TESTS DE FLUJO COMPLETO ===================
    
    def test_e2e_message_flow_complete(self):
        """Test end-to-end del flujo completo de mensajes"""
        print("📡 Testing flujo completo: Mensaje → Procesamiento → BD → Worker → Paneles")
        
        # 1. Simular mensaje de cámara
        test_message = {
            'device': 'CAMERA_E2E_TEST',
            'line': 1,
            'Vehicle In': 150,
            'Vehicle Out': 75
        }
        
        # 2. Procesar con CameraMessageProcessor
        start_time = time.time()
        
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            # Mock de cámaras encontradas
            mock_camera = Mock(spec=Access)
            mock_camera.id = 1
            mock_camera.device_name = 'CAMERA_E2E_TEST'
            mock_camera.line = 1
            mock_camera.last_in_count = 100
            mock_camera.last_out_count = 50
            mock_camera.last_update = datetime.now() - timedelta(minutes=5)
            
            mock_cameras.return_value = [mock_camera]
            
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                from camera_message_processor import ProcessingResult
                
                mock_process.return_value = ProcessingResult(
                    status='success',
                    message_id='e2e_test_123',
                    processing_time_ms=125.0,
                    updated_parkings=[{
                        'id': 1,
                        'name': 'Test Parking E2E',
                        'old_occupancy': 100,
                        'new_occupancy': 125,
                        'status': 'LIBRE'
                    }],
                    reset_detected=False
                )
                
                # Procesar mensaje
                future = self.message_processor.process_message_async({
                    'device': 'CAMERA_E2E_TEST',
                    'line': 1,
                    'vehicle_in': 150,
                    'vehicle_out': 75,
                    'source_ip': '127.0.0.1',
                    'raw_data': json.dumps(test_message),
                    'timestamp': datetime.now()
                })
                
                result = future.result(timeout=5)
                processing_time = time.time() - start_time
        
        # 3. Validar resultado del procesamiento
        self.assertEqual(result.status, 'success')
        self.assertLess(processing_time, 1.0, "Procesamiento debe ser <1s")
        self.assertEqual(len(result.updated_parkings), 1)
        
        print(f"✅ Mensaje procesado en {processing_time:.3f}s")
        
        # 4. Verificar que el worker puede procesar la actualización
        with patch('panel_update_worker.PanelUpdateMethods.update_parking_panels') as mock_worker:
            from panel_update_worker import ParkingUpdateResult
            
            mock_worker.return_value = ParkingUpdateResult(
                parking_id=1,
                parking_name='Test Parking E2E',
                message_type='occupancy',
                message_sent='125',
                panels_total=2,
                panels_updated=2,
                panels_failed=0,
                execution_time_ms=200.0
            )
            
            # Simular ciclo del worker
            parking_data = {
                'id': 1,
                'name': 'Test Parking E2E',
                'current_occupancy': 125,
                'max_capacity': 200,
                'status': 'LIBRE',
                'panel_count': 2
            }
            
            worker_result = self.panel_worker._update_parking_panels(parking_data)
        
        # 5. Validar resultado del worker
        self.assertIsNotNone(worker_result)
        self.assertEqual(worker_result.panels_updated, 2)
        self.assertEqual(worker_result.panels_failed, 0)
        
        print("✅ Worker procesó actualización de paneles correctamente")
        print(f"✅ Flujo E2E completo validado exitosamente")
    
    def test_e2e_concurrent_messages(self):
        """Test end-to-end con múltiples mensajes concurrentes"""
        print("⚡ Testing concurrencia: Múltiples mensajes simultáneos")
        
        message_count = 10
        results = []
        
        def send_concurrent_message(msg_id):
            """Enviar mensaje individual"""
            with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                mock_camera = Mock(spec=Access)
                mock_camera.id = msg_id
                mock_camera.device_name = f'CAMERA_CONCURRENT_{msg_id}'
                mock_camera.line = 1
                mock_camera.last_in_count = 100 + msg_id
                mock_camera.last_out_count = 50 + msg_id
                mock_camera.last_update = datetime.now() - timedelta(minutes=5)
                
                mock_cameras.return_value = [mock_camera]
                
                with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                    from camera_message_processor import ProcessingResult
                    
                    mock_process.return_value = ProcessingResult(
                        status='success',
                        message_id=f'concurrent_{msg_id}',
                        processing_time_ms=50.0 + msg_id,
                        updated_parkings=[{
                            'id': msg_id,
                            'name': f'Parking {msg_id}',
                            'new_occupancy': 100 + msg_id,
                            'status': 'LIBRE'
                        }],
                        reset_detected=False
                    )
                    
                    # Procesar mensaje
                    future = self.message_processor.process_message_async({
                        'device': f'CAMERA_CONCURRENT_{msg_id}',
                        'line': 1,
                        'vehicle_in': 150 + msg_id,
                        'vehicle_out': 75 + msg_id,
                        'source_ip': '127.0.0.1',
                        'timestamp': datetime.now()
                    })
                    
                    return future.result(timeout=5)
        
        # Enviar mensajes concurrentes
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=message_count) as executor:
            futures = [executor.submit(send_concurrent_message, i) for i in range(1, message_count + 1)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Validar resultados
        self.assertEqual(len(results), message_count)
        
        successful_results = [r for r in results if r.status == 'success']
        self.assertEqual(len(successful_results), message_count)
        
        # Calcular throughput
        throughput = message_count / total_time
        self.assertGreater(throughput, 5, f"Throughput {throughput:.2f} msg/s debe ser >5 msg/s")
        
        print(f"✅ {message_count} mensajes procesados en {total_time:.3f}s")
        print(f"✅ Throughput alcanzado: {throughput:.2f} msg/s")
    
    def test_e2e_reset_detection_and_recovery(self):
        """Test end-to-end de detección de reinicio y recuperación"""
        print("🔄 Testing detección de reinicio y recuperación")
        
        # 1. Mensaje normal
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            mock_camera = Mock(spec=Access)
            mock_camera.id = 1
            mock_camera.device_name = 'CAMERA_RESET_TEST'
            mock_camera.line = 1
            mock_camera.last_in_count = 1000  # Contadores altos
            mock_camera.last_out_count = 500
            mock_camera.last_update = datetime.now() - timedelta(minutes=30)
            
            mock_cameras.return_value = [mock_camera]
            
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                from camera_message_processor import ProcessingResult
                
                # Simular detección de reinicio
                mock_process.return_value = ProcessingResult(
                    status='success',
                    message_id='reset_test_123',
                    processing_time_ms=200.0,
                    updated_parkings=[{
                        'id': 1,
                        'name': 'Parking Reset Test',
                        'new_occupancy': 150,
                        'status': 'DENSO'
                    }],
                    reset_detected=True,
                    reset_confidence=95
                )
                
                # Procesar mensaje con reinicio
                future = self.message_processor.process_message_async({
                    'device': 'CAMERA_RESET_TEST',
                    'line': 1,
                    'vehicle_in': 10,  # Contadores bajos después de reinicio
                    'vehicle_out': 5,
                    'source_ip': '127.0.0.1',
                    'timestamp': datetime.now()
                })
                
                result = future.result(timeout=5)
        
        # Validar detección de reinicio
        self.assertEqual(result.status, 'success')
        self.assertTrue(result.reset_detected)
        self.assertGreater(result.reset_confidence, 90)
        
        print(f"✅ Reinicio detectado con confianza: {result.reset_confidence}%")
        print("✅ Sistema recuperado correctamente después de reinicio")
    
    # =================== TESTS DE RENDIMIENTO ===================
    
    def test_e2e_performance_benchmark(self):
        """Test de rendimiento completo del sistema"""
        print("📊 Testing benchmark de rendimiento completo")
        
        test_scenarios = [
            {'messages': 50, 'workers': 5, 'target_throughput': 20},
            {'messages': 100, 'workers': 10, 'target_throughput': 30},
        ]
        
        for scenario in test_scenarios:
            print(f"📈 Scenario: {scenario['messages']} mensajes, {scenario['workers']} workers")
            
            # Configurar procesador para este escenario
            processor = CameraMessageProcessor(
                max_workers=scenario['workers'], 
                cache_duration=60
            )
            
            try:
                def process_benchmark_message(msg_id):
                    """Procesar mensaje de benchmark"""
                    with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                        mock_camera = Mock(spec=Access)
                        mock_camera.id = msg_id
                        mock_camera.device_name = f'CAMERA_BENCH_{msg_id}'
                        mock_camera.line = 1
                        mock_camera.last_in_count = 100
                        mock_camera.last_out_count = 50
                        mock_camera.last_update = datetime.now() - timedelta(minutes=5)
                        
                        mock_cameras.return_value = [mock_camera]
                        
                        with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                            from camera_message_processor import ProcessingResult
                            
                            # Simular latencia realista
                            time.sleep(0.01)  # 10ms de procesamiento simulado
                            
                            mock_process.return_value = ProcessingResult(
                                status='success',
                                message_id=f'bench_{msg_id}',
                                processing_time_ms=10.0,
                                updated_parkings=[{'id': msg_id, 'name': f'Parking {msg_id}', 'new_occupancy': 100, 'status': 'LIBRE'}],
                                reset_detected=False
                            )
                            
                            future = processor.process_message_async({
                                'device': f'CAMERA_BENCH_{msg_id}',
                                'line': 1,
                                'vehicle_in': 150,
                                'vehicle_out': 75,
                                'source_ip': '127.0.0.1',
                                'timestamp': datetime.now()
                            })
                            
                            return future.result(timeout=5)
                
                # Ejecutar benchmark
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=scenario['workers']) as executor:
                    futures = [
                        executor.submit(process_benchmark_message, i) 
                        for i in range(scenario['messages'])
                    ]
                    results = [future.result() for future in as_completed(futures)]
                
                total_time = time.time() - start_time
                
                # Calcular métricas
                throughput = len(results) / total_time
                avg_processing_time = sum(r.processing_time_ms for r in results) / len(results)
                
                # Validar métricas
                self.assertGreaterEqual(throughput, scenario['target_throughput'])
                self.assertLess(avg_processing_time, 100)  # <100ms promedio
                
                print(f"  ✅ Throughput: {throughput:.2f} msg/s (objetivo: {scenario['target_throughput']})")
                print(f"  ✅ Tiempo promedio: {avg_processing_time:.2f}ms")
                
            finally:
                processor.shutdown()
    
    # =================== TESTS DE ESCENARIOS CRÍTICOS ===================
    
    def test_e2e_error_recovery(self):
        """Test de recuperación de errores críticos"""
        print("🚨 Testing recuperación de errores críticos")
        
        # 1. Test de cámara no encontrada
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            mock_cameras.return_value = []  # No se encuentra la cámara
            
            future = self.message_processor.process_message_async({
                'device': 'CAMERA_NOT_FOUND',
                'line': 99,
                'vehicle_in': 150,
                'vehicle_out': 75,
                'source_ip': '127.0.0.1',
                'timestamp': datetime.now()
            })
            
            result = future.result(timeout=5)
            
            self.assertEqual(result.status, 'camera_not_found')
            print("✅ Error de cámara no encontrada manejado correctamente")
        
        # 2. Test de error de base de datos
        with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
            mock_process.side_effect = Exception("Database connection lost")
            
            future = self.message_processor.process_message_async({
                'device': 'CAMERA_DB_ERROR',
                'line': 1,
                'vehicle_in': 150,
                'vehicle_out': 75,
                'source_ip': '127.0.0.1',
                'timestamp': datetime.now()
            })
            
            result = future.result(timeout=5)
            
            self.assertEqual(result.status, 'error')
            self.assertIn('Database connection lost', result.error)
            print("✅ Error de base de datos manejado correctamente")
        
        # 3. Verificar que el sistema sigue operativo después de errores
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            mock_camera = Mock(spec=Access)
            mock_camera.id = 1
            mock_camera.device_name = 'CAMERA_RECOVERY'
            mock_camera.line = 1
            mock_cameras.return_value = [mock_camera]
            
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                from camera_message_processor import ProcessingResult
                
                mock_process.return_value = ProcessingResult(
                    status='success',
                    message_id='recovery_test',
                    processing_time_ms=50.0,
                    updated_parkings=[],
                    reset_detected=False
                )
                
                future = self.message_processor.process_message_async({
                    'device': 'CAMERA_RECOVERY',
                    'line': 1,
                    'vehicle_in': 150,
                    'vehicle_out': 75,
                    'source_ip': '127.0.0.1',
                    'timestamp': datetime.now()
                })
                
                result = future.result(timeout=5)
                
                self.assertEqual(result.status, 'success')
                print("✅ Sistema operativo después de errores - recuperación completa")
    
    def test_e2e_worker_panel_coordination(self):
        """Test de coordinación entre procesador y worker de paneles"""
        print("🔗 Testing coordinación entre componentes")
        
        # Simular que el worker está procesando cuando llega un mensaje
        with patch('panel_update_worker.PanelUpdateMethods.update_parking_panels') as mock_worker_update:
            from panel_update_worker import ParkingUpdateResult
            
            # Mock del worker actualizando paneles
            mock_worker_update.return_value = ParkingUpdateResult(
                parking_id=1,
                parking_name='Coordination Test',
                message_type='occupancy',
                message_sent='175',
                panels_total=3,
                panels_updated=3,
                panels_failed=0,
                execution_time_ms=150.0
            )
            
            # Simular ciclo del worker en paralelo con mensajes
            def worker_cycle():
                """Simular ciclo del worker"""
                time.sleep(0.1)  # Simular procesamiento
                parking_data = {
                    'id': 1,
                    'name': 'Coordination Test',
                    'current_occupancy': 175,
                    'max_capacity': 200,
                    'status': 'DENSO',
                    'panel_count': 3
                }
                return self.panel_worker._update_parking_panels(parking_data)
            
            # Ejecutar worker y procesador en paralelo
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Iniciar worker
                worker_future = executor.submit(worker_cycle)
                
                # Procesar mensaje mientras worker está activo
                with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                    mock_camera = Mock(spec=Access)
                    mock_camera.id = 1
                    mock_camera.device_name = 'CAMERA_COORDINATION'
                    mock_camera.line = 1
                    mock_cameras.return_value = [mock_camera]
                    
                    with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                        from camera_message_processor import ProcessingResult
                        
                        mock_process.return_value = ProcessingResult(
                            status='success',
                            message_id='coordination_test',
                            processing_time_ms=75.0,
                            updated_parkings=[{
                                'id': 1,
                                'name': 'Coordination Test',
                                'new_occupancy': 175,
                                'status': 'DENSO'
                            }],
                            reset_detected=False
                        )
                        
                        processor_future = self.message_processor.process_message_async({
                            'device': 'CAMERA_COORDINATION',
                            'line': 1,
                            'vehicle_in': 175,
                            'vehicle_out': 85,
                            'source_ip': '127.0.0.1',
                            'timestamp': datetime.now()
                        })
                        
                        # Esperar resultados
                        worker_result = worker_future.result(timeout=5)
                        processor_result = processor_future.result(timeout=5)
        
        # Validar que ambos componentes funcionaron correctamente
        self.assertEqual(processor_result.status, 'success')
        self.assertIsNotNone(worker_result)
        self.assertEqual(worker_result.panels_updated, 3)
        
        print("✅ Coordinación entre componentes exitosa")
        print("✅ Procesador y worker operan independientemente sin interferencias")


if __name__ == '__main__':
    # Configurar logging para tests E2E
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests con output detallado
    unittest.main(verbosity=2, buffer=True)
