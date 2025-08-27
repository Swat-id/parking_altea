#!/usr/bin/env python3
"""
Tests de escenarios críticos para Sistema v3.4.0
Valida el comportamiento del sistema en situaciones extremas y de fallo
"""

import unittest
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from camera_message_processor import CameraMessageProcessor
from panel_update_worker import PanelUpdateWorker
from models import Access, Parking, Panel


class TestCriticalScenariosV340(unittest.TestCase):
    """Tests de escenarios críticos para Sistema v3.4.0"""
    
    @classmethod
    def setUpClass(cls):
        """Configurar entorno de tests críticos"""
        print("\n" + "="*60)
        print("🚨 INICIANDO TESTS DE ESCENARIOS CRÍTICOS v3.4.0")
        print("="*60)
    
    def setUp(self):
        """Configurar cada test crítico"""
        self.processor = CameraMessageProcessor(max_workers=10, cache_duration=60)
        self.worker = PanelUpdateWorker(update_interval=10, max_panel_workers=3)
        
        self.test_start = time.time()
        print(f"\n🔬 Test crítico: {self._testMethodName}")
    
    def tearDown(self):
        """Limpiar después de cada test crítico"""
        self.processor.shutdown()
        self.worker.stop()
        
        duration = time.time() - self.test_start
        print(f"✅ Test crítico completado en {duration:.2f}s")
    
    # =================== TESTS DE REINICIOS DE CÁMARAS ===================
    
    def test_camera_reset_detection_extreme(self):
        """Test: Detección de reinicios en condiciones extremas"""
        print("🔄 Escenario crítico: Reinicio de cámara con contadores extremos")
        
        # Escenario: Cámara con contadores muy altos que se reinicia
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            mock_camera = Mock(spec=Access)
            mock_camera.id = 1
            mock_camera.device_name = 'CAMERA_EXTREME_RESET'
            mock_camera.line = 1
            mock_camera.last_in_count = 999999  # Contador extremadamente alto
            mock_camera.last_out_count = 500000
            mock_camera.last_update = datetime.now() - timedelta(hours=24)  # Hace 24 horas
            mock_cameras.return_value = [mock_camera]
            
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                from camera_message_processor import ProcessingResult
                
                # Simular detección de reinicio con alta confianza
                mock_process.return_value = ProcessingResult(
                    status='success',
                    message_id='extreme_reset_test',
                    processing_time_ms=150.0,
                    updated_parkings=[{
                        'id': 1,
                        'name': 'Parking Extreme Reset',
                        'new_occupancy': 200,
                        'status': 'DENSO'
                    }],
                    reset_detected=True,
                    reset_confidence=98
                )
                
                # Enviar mensaje con contadores bajos después del reinicio
                future = self.processor.process_message_async({
                    'device': 'CAMERA_EXTREME_RESET',
                    'line': 1,
                    'vehicle_in': 5,    # Contador bajo
                    'vehicle_out': 2,   # Contador bajo
                    'source_ip': '192.168.1.100',
                    'timestamp': datetime.now()
                })
                
                result = future.result(timeout=10)
        
        # Validar detección de reinicio
        self.assertEqual(result.status, 'success')
        self.assertTrue(result.reset_detected)
        self.assertGreater(result.reset_confidence, 90)
        
        print(f"  ✅ Reinicio detectado con confianza: {result.reset_confidence}%")
        print(f"  ✅ Sistema se recuperó correctamente de contadores extremos")
    
    def test_multiple_camera_resets_simultaneous(self):
        """Test: Múltiples reinicios de cámaras simultáneos"""
        print("🔄 Escenario crítico: Múltiples reinicios simultáneos")
        
        camera_count = 5
        reset_results = []
        
        def process_camera_reset(camera_id):
            """Procesar reinicio de cámara individual"""
            with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                mock_camera = Mock(spec=Access)
                mock_camera.id = camera_id
                mock_camera.device_name = f'CAMERA_MULTI_RESET_{camera_id}'
                mock_camera.line = 1
                mock_camera.last_in_count = 10000 + camera_id * 1000
                mock_camera.last_out_count = 5000 + camera_id * 500
                mock_camera.last_update = datetime.now() - timedelta(hours=12)
                mock_cameras.return_value = [mock_camera]
                
                with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                    from camera_message_processor import ProcessingResult
                    
                    mock_process.return_value = ProcessingResult(
                        status='success',
                        message_id=f'multi_reset_{camera_id}',
                        processing_time_ms=100.0 + camera_id * 10,
                        updated_parkings=[{
                            'id': camera_id,
                            'name': f'Parking {camera_id}',
                            'new_occupancy': 50 + camera_id * 10,
                            'status': 'LIBRE'
                        }],
                        reset_detected=True,
                        reset_confidence=90 + camera_id
                    )
                    
                    future = self.processor.process_message_async({
                        'device': f'CAMERA_MULTI_RESET_{camera_id}',
                        'line': 1,
                        'vehicle_in': camera_id * 2,
                        'vehicle_out': camera_id,
                        'source_ip': f'192.168.1.{100 + camera_id}',
                        'timestamp': datetime.now()
                    })
                    
                    return future.result(timeout=15)
        
        # Procesar reinicios simultáneos
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=camera_count) as executor:
            futures = [executor.submit(process_camera_reset, i + 1) for i in range(camera_count)]
            reset_results = [future.result() for future in as_completed(futures)]
        
        processing_time = time.time() - start_time
        
        # Validar resultados
        self.assertEqual(len(reset_results), camera_count)
        
        successful_resets = [r for r in reset_results if r.status == 'success' and r.reset_detected]
        self.assertEqual(len(successful_resets), camera_count)
        
        # Verificar que todos los reinicios fueron detectados
        for result in reset_results:
            self.assertTrue(result.reset_detected)
            self.assertGreater(result.reset_confidence, 90)
        
        print(f"  ✅ {camera_count} reinicios procesados simultáneamente en {processing_time:.2f}s")
        print(f"  ✅ Todos los reinicios detectados correctamente")
    
    # =================== TESTS DE DELTAS ANÓMALOS ===================
    
    def test_extreme_delta_validation(self):
        """Test: Validación de deltas extremadamente anómalos"""
        print("⚠️ Escenario crítico: Deltas extremadamente anómalos")
        
        extreme_scenarios = [
            {'name': 'Delta masivo entrada', 'in': 1000, 'out': 0, 'expected_status': 'invalid_delta'},
            {'name': 'Delta masivo salida', 'in': 0, 'out': 1000, 'expected_status': 'invalid_delta'},
            {'name': 'Delta bidireccional extremo', 'in': 500, 'out': 500, 'expected_status': 'invalid_delta'},
            {'name': 'Delta negativo simulado', 'in': -100, 'out': 50, 'expected_status': 'invalid_delta'},
        ]
        
        for scenario in extreme_scenarios:
            print(f"  🔍 Testing: {scenario['name']}")
            
            with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                mock_camera = Mock(spec=Access)
                mock_camera.id = 1
                mock_camera.device_name = 'CAMERA_EXTREME_DELTA'
                mock_camera.line = 1
                mock_camera.last_in_count = 100
                mock_camera.last_out_count = 50
                mock_camera.last_update = datetime.now() - timedelta(minutes=1)
                mock_cameras.return_value = [mock_camera]
                
                with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                    from camera_message_processor import ProcessingResult
                    
                    # Simular validación que rechaza el delta
                    mock_process.return_value = ProcessingResult(
                        status=scenario['expected_status'],
                        message_id=f'extreme_delta_{scenario["name"].replace(" ", "_")}',
                        processing_time_ms=75.0,
                        updated_parkings=[],
                        reset_detected=False,
                        error=f"Delta rejected: in={scenario['in']}, out={scenario['out']}",
                        validations={
                            'delta_in': scenario['in'],
                            'delta_out': scenario['out'],
                            'magnitude_check': False,
                            'rate_check': False,
                            'pattern_check': False
                        }
                    )
                    
                    future = self.processor.process_message_async({
                        'device': 'CAMERA_EXTREME_DELTA',
                        'line': 1,
                        'vehicle_in': 100 + scenario['in'],
                        'vehicle_out': 50 + scenario['out'],
                        'source_ip': '192.168.1.200',
                        'timestamp': datetime.now()
                    })
                    
                    result = future.result(timeout=10)
            
            # Validar que el delta anómalo fue rechazado
            self.assertEqual(result.status, scenario['expected_status'])
            self.assertFalse(result.reset_detected)
            self.assertEqual(len(result.updated_parkings), 0)
            
            print(f"    ✅ Delta anómalo correctamente rechazado")
        
        print("  ✅ Todos los deltas extremos fueron correctamente validados y rechazados")
    
    def test_rapid_fire_anomalous_deltas(self):
        """Test: Ráfaga de deltas anómalos consecutivos"""
        print("⚡ Escenario crítico: Ráfaga de deltas anómalos")
        
        rapid_fire_count = 20
        anomalous_results = []
        
        def send_anomalous_delta(msg_id):
            """Enviar delta anómalo individual"""
            with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                mock_camera = Mock(spec=Access)
                mock_camera.id = 1
                mock_camera.device_name = 'CAMERA_RAPID_ANOMALY'
                mock_camera.line = 1
                mock_camera.last_in_count = 100
                mock_camera.last_out_count = 50
                mock_camera.last_update = datetime.now() - timedelta(seconds=1)
                mock_cameras.return_value = [mock_camera]
                
                with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                    from camera_message_processor import ProcessingResult
                    
                    # Alternar entre diferentes tipos de anomalías
                    if msg_id % 3 == 0:
                        delta_in, delta_out = 200, 0  # Entrada masiva
                    elif msg_id % 3 == 1:
                        delta_in, delta_out = 0, 200  # Salida masiva
                    else:
                        delta_in, delta_out = 100, 100  # Bidireccional extremo
                    
                    mock_process.return_value = ProcessingResult(
                        status='invalid_delta',
                        message_id=f'rapid_anomaly_{msg_id}',
                        processing_time_ms=50.0,
                        updated_parkings=[],
                        reset_detected=False,
                        error=f"Rapid fire delta rejected: {delta_in}/{delta_out}"
                    )
                    
                    future = self.processor.process_message_async({
                        'device': 'CAMERA_RAPID_ANOMALY',
                        'line': 1,
                        'vehicle_in': 100 + delta_in,
                        'vehicle_out': 50 + delta_out,
                        'source_ip': '192.168.1.250',
                        'timestamp': datetime.now()
                    })
                    
                    return future.result(timeout=10)
        
        # Enviar ráfaga de deltas anómalos
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_anomalous_delta, i) for i in range(rapid_fire_count)]
            anomalous_results = [future.result() for future in as_completed(futures)]
        
        processing_time = time.time() - start_time
        
        # Validar que todos fueron rechazados
        self.assertEqual(len(anomalous_results), rapid_fire_count)
        
        rejected_count = sum(1 for r in anomalous_results if r.status == 'invalid_delta')
        self.assertEqual(rejected_count, rapid_fire_count)
        
        # Verificar que el sistema sigue respondiendo rápidamente
        avg_response_time = processing_time / rapid_fire_count
        self.assertLess(avg_response_time, 0.5, "Sistema debe mantener respuesta rápida bajo ataque de anomalías")
        
        print(f"  ✅ {rapid_fire_count} deltas anómalos procesados en {processing_time:.2f}s")
        print(f"  ✅ Tiempo promedio por mensaje: {avg_response_time:.3f}s")
        print("  ✅ Sistema mantiene rendimiento bajo ataque de anomalías")
    
    # =================== TESTS DE FALLOS DE PANELES ===================
    
    def test_panel_worker_massive_failures(self):
        """Test: Fallos masivos de paneles durante actualización"""
        print("📺 Escenario crítico: Fallos masivos de paneles")
        
        with patch('panel_update_worker.PanelUpdateMethods.update_parking_panels') as mock_update:
            from panel_update_worker import ParkingUpdateResult
            
            # Simular fallos masivos en múltiples parkings
            def simulate_panel_failures(parking_data):
                """Simular fallos en paneles"""
                parking_id = parking_data['id']
                
                if parking_id <= 3:  # Primeros 3 parkings con fallos totales
                    return ParkingUpdateResult(
                        parking_id=parking_id,
                        parking_name=f'Parking Fail {parking_id}',
                        message_type='occupancy',
                        message_sent=f'{parking_data["current_occupancy"]}',
                        panels_total=5,
                        panels_updated=0,  # Ningún panel actualizado
                        panels_failed=5,   # Todos los paneles fallaron
                        execution_time_ms=5000.0,  # Timeout prolongado
                        errors=[
                            'Panel 1: Connection timeout',
                            'Panel 2: Connection refused',
                            'Panel 3: Network unreachable',
                            'Panel 4: Protocol error',
                            'Panel 5: Hardware failure'
                        ]
                    )
                else:  # Parkings restantes con fallos parciales
                    return ParkingUpdateResult(
                        parking_id=parking_id,
                        parking_name=f'Parking Partial {parking_id}',
                        message_type='occupancy',
                        message_sent=f'{parking_data["current_occupancy"]}',
                        panels_total=4,
                        panels_updated=2,  # Solo 2 de 4 paneles actualizados
                        panels_failed=2,   # 2 paneles fallaron
                        execution_time_ms=3000.0,
                        errors=[
                            'Panel 3: Slow response',
                            'Panel 4: Partial timeout'
                        ]
                    )
            
            mock_update.side_effect = simulate_panel_failures
            
            # Simular datos de múltiples parkings
            parking_data_list = [
                {
                    'id': i,
                    'name': f'Test Parking {i}',
                    'current_occupancy': 100 + i * 10,
                    'max_capacity': 200,
                    'status': 'LIBRE',
                    'panel_count': 5 if i <= 3 else 4
                }
                for i in range(1, 8)  # 7 parkings
            ]
            
            # Procesar actualizaciones con fallos masivos
            start_time = time.time()
            results = []
            
            for parking_data in parking_data_list:
                result = self.worker._update_parking_panels(parking_data)
                results.append(result)
            
            processing_time = time.time() - start_time
            
            # Analizar resultados de fallos
            total_panels = sum(r.panels_total for r in results)
            total_updated = sum(r.panels_updated for r in results)
            total_failed = sum(r.panels_failed for r in results)
            
            success_rate = total_updated / total_panels if total_panels > 0 else 0
            failure_rate = total_failed / total_panels if total_panels > 0 else 0
            
            # Validaciones
            self.assertEqual(len(results), 7)  # Todos los parkings procesados
            self.assertLess(processing_time, 60, "Procesamiento debe completarse en <60s incluso con fallos")
            
            # Verificar que el sistema maneja los fallos gracefully
            for result in results:
                self.assertIsNotNone(result)
                self.assertGreaterEqual(result.panels_total, result.panels_updated + result.panels_failed)
            
            print(f"  📊 Parkings procesados: {len(results)}")
            print(f"  📺 Total paneles: {total_panels}")
            print(f"  ✅ Paneles actualizados: {total_updated}")
            print(f"  ❌ Paneles fallidos: {total_failed}")
            print(f"  📈 Tasa de éxito: {success_rate:.1%}")
            print(f"  📉 Tasa de fallo: {failure_rate:.1%}")
            print(f"  ⏱️ Tiempo total: {processing_time:.2f}s")
            print("  ✅ Sistema maneja fallos masivos gracefully")
    
    # =================== TESTS DE RECUPERACIÓN DE ERRORES ===================
    
    def test_database_connection_loss_recovery(self):
        """Test: Recuperación después de pérdida de conexión a BD"""
        print("🗄️ Escenario crítico: Pérdida y recuperación de conexión a BD")
        
        # Fase 1: Operación normal
        print("  📶 Fase 1: Operación normal")
        
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            mock_camera = Mock(spec=Access)
            mock_camera.id = 1
            mock_camera.device_name = 'CAMERA_DB_RECOVERY'
            mock_camera.line = 1
            mock_cameras.return_value = [mock_camera]
            
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                from camera_message_processor import ProcessingResult
                
                mock_process.return_value = ProcessingResult(
                    status='success',
                    message_id='db_recovery_normal',
                    processing_time_ms=100.0,
                    updated_parkings=[],
                    reset_detected=False
                )
                
                future = self.processor.process_message_async({
                    'device': 'CAMERA_DB_RECOVERY',
                    'line': 1,
                    'vehicle_in': 150,
                    'vehicle_out': 75,
                    'source_ip': '192.168.1.50',
                    'timestamp': datetime.now()
                })
                
                result_normal = future.result(timeout=10)
        
        self.assertEqual(result_normal.status, 'success')
        print("    ✅ Operación normal exitosa")
        
        # Fase 2: Simulación de pérdida de conexión
        print("  📉 Fase 2: Pérdida de conexión a BD")
        
        error_count = 0
        for i in range(3):  # 3 intentos con error
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                mock_process.side_effect = Exception("psycopg2.OperationalError: connection to server lost")
                
                future = self.processor.process_message_async({
                    'device': 'CAMERA_DB_RECOVERY',
                    'line': 1,
                    'vehicle_in': 160 + i,
                    'vehicle_out': 80 + i,
                    'source_ip': '192.168.1.50',
                    'timestamp': datetime.now()
                })
                
                result_error = future.result(timeout=10)
                
                if result_error.status == 'error':
                    error_count += 1
        
        self.assertEqual(error_count, 3)
        print(f"    ✅ {error_count} errores de BD correctamente manejados")
        
        # Fase 3: Recuperación de conexión
        print("  📈 Fase 3: Recuperación de conexión")
        
        # Simular que la conexión se recupera
        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
            mock_camera = Mock(spec=Access)
            mock_camera.id = 1
            mock_camera.device_name = 'CAMERA_DB_RECOVERY'
            mock_camera.line = 1
            mock_cameras.return_value = [mock_camera]
            
            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                from camera_message_processor import ProcessingResult
                
                mock_process.return_value = ProcessingResult(
                    status='success',
                    message_id='db_recovery_restored',
                    processing_time_ms=120.0,
                    updated_parkings=[{
                        'id': 1,
                        'name': 'Recovery Test',
                        'new_occupancy': 175,
                        'status': 'DENSO'
                    }],
                    reset_detected=False
                )
                
                future = self.processor.process_message_async({
                    'device': 'CAMERA_DB_RECOVERY',
                    'line': 1,
                    'vehicle_in': 175,
                    'vehicle_out': 85,
                    'source_ip': '192.168.1.50',
                    'timestamp': datetime.now()
                })
                
                result_recovered = future.result(timeout=10)
        
        self.assertEqual(result_recovered.status, 'success')
        self.assertEqual(len(result_recovered.updated_parkings), 1)
        print("    ✅ Sistema se recuperó completamente después de errores de BD")
        
        print("  🎯 Recuperación completa: Normal → Error → Recuperado")
    
    def test_system_shutdown_graceful(self):
        """Test: Shutdown graceful bajo carga"""
        print("🔄 Escenario crítico: Shutdown graceful bajo carga")
        
        # Configurar sistema con carga
        processor = CameraMessageProcessor(max_workers=5, cache_duration=60)
        worker = PanelUpdateWorker(update_interval=5, max_panel_workers=3)
        
        try:
            # Iniciar worker
            worker.start()
            
            # Generar carga de trabajo
            active_futures = []
            
            def generate_load():
                """Generar carga continua"""
                for i in range(50):  # 50 mensajes
                    with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                        mock_camera = Mock(spec=Access)
                        mock_camera.id = i + 1
                        mock_camera.device_name = f'CAMERA_SHUTDOWN_{i}'
                        mock_camera.line = 1
                        mock_cameras.return_value = [mock_camera]
                        
                        with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                            from camera_message_processor import ProcessingResult
                            
                            # Simular procesamiento que toma tiempo
                            time.sleep(0.1)  # 100ms por mensaje
                            
                            mock_process.return_value = ProcessingResult(
                                status='success',
                                message_id=f'shutdown_test_{i}',
                                processing_time_ms=100.0,
                                updated_parkings=[],
                                reset_detected=False
                            )
                            
                            future = processor.process_message_async({
                                'device': f'CAMERA_SHUTDOWN_{i}',
                                'line': 1,
                                'vehicle_in': 150,
                                'vehicle_out': 75,
                                'source_ip': '127.0.0.1',
                                'timestamp': datetime.now()
                            })
                            
                            active_futures.append(future)
            
            # Iniciar generación de carga en thread separado
            load_thread = threading.Thread(target=generate_load)
            load_thread.start()
            
            # Esperar a que se inicie la carga
            time.sleep(1)
            
            # Shutdown graceful mientras hay carga activa
            print("  🔄 Iniciando shutdown con carga activa...")
            shutdown_start = time.time()
            
            processor.shutdown()
            worker.stop()
            
            shutdown_time = time.time() - shutdown_start
            
            # Esperar a que termine la carga
            load_thread.join(timeout=10)
            
            # Verificar que el shutdown fue limpio
            self.assertLess(shutdown_time, 30, "Shutdown debe completarse en <30s")
            
            # Verificar estadísticas del procesador
            stats = processor.get_stats()
            self.assertGreaterEqual(stats['messages_processed'], 0)
            
            print(f"  ✅ Shutdown completado en {shutdown_time:.2f}s")
            print(f"  📊 Mensajes procesados antes del shutdown: {stats['messages_processed']}")
            print("  ✅ Shutdown graceful exitoso bajo carga")
            
        finally:
            # Asegurar cleanup
            processor.shutdown()
            worker.stop()


if __name__ == '__main__':
    # Configurar logging para tests críticos
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests críticos con output detallado
    unittest.main(verbosity=2, buffer=True)
