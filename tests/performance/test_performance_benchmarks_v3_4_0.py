#!/usr/bin/env python3
"""
Tests de rendimiento y benchmarks para Sistema v3.4.0
Valida que el sistema cumple con los objetivos de rendimiento definidos
"""

import unittest
import time
import statistics
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from camera_message_processor import CameraMessageProcessor
from panel_update_worker import PanelUpdateWorker
from models import Access


class TestPerformanceBenchmarksV340(unittest.TestCase):
    """Tests de rendimiento para Sistema v3.4.0"""
    
    @classmethod
    def setUpClass(cls):
        """Configurar entorno de benchmarks"""
        print("\n" + "="*60)
        print("📊 INICIANDO BENCHMARKS DE RENDIMIENTO v3.4.0")
        print("="*60)
        
        # Objetivos de rendimiento
        cls.PERFORMANCE_TARGETS = {
            'response_time_ms': 200,      # <200ms por mensaje
            'throughput_msg_per_sec': 20, # >20 msg/s
            'concurrent_workers': 10,      # 10 workers concurrentes
            'memory_efficiency': 0.95,     # 95% efficiency
            'error_rate': 0.01            # <1% error rate
        }
        
        print("🎯 Objetivos de rendimiento:")
        for metric, target in cls.PERFORMANCE_TARGETS.items():
            print(f"  - {metric}: {target}")
        print()
    
    def setUp(self):
        """Configurar cada benchmark"""
        self.processor = CameraMessageProcessor(max_workers=10, cache_duration=300)
        self.worker = PanelUpdateWorker(update_interval=30, max_panel_workers=5)
        
        # Métricas del benchmark
        self.benchmark_results = {
            'response_times': [],
            'throughput_samples': [],
            'error_count': 0,
            'total_messages': 0
        }
    
    def tearDown(self):
        """Limpiar después de cada benchmark"""
        self.processor.shutdown()
        self.worker.stop()
    
    # =================== BENCHMARKS DE RESPUESTA ===================
    
    def test_response_time_single_message(self):
        """Benchmark: Tiempo de respuesta de mensaje individual"""
        print("⏱️ Benchmark: Tiempo de respuesta mensaje individual")
        
        samples = 100
        response_times = []
        
        for i in range(samples):
            with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                # Mock de cámara
                mock_camera = Mock(spec=Access)
                mock_camera.id = 1
                mock_camera.device_name = f'CAMERA_RESPONSE_{i}'
                mock_camera.line = 1
                mock_camera.last_in_count = 100
                mock_camera.last_out_count = 50
                mock_camera.last_update = datetime.now() - timedelta(minutes=5)
                mock_cameras.return_value = [mock_camera]
                
                with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                    from camera_message_processor import ProcessingResult
                    
                    # Simular procesamiento realista
                    processing_start = time.time()
                    time.sleep(0.001)  # 1ms de procesamiento simulado
                    processing_time = (time.time() - processing_start) * 1000
                    
                    mock_process.return_value = ProcessingResult(
                        status='success',
                        message_id=f'response_test_{i}',
                        processing_time_ms=processing_time,
                        updated_parkings=[],
                        reset_detected=False
                    )
                    
                    # Medir tiempo de respuesta completo
                    start_time = time.time()
                    
                    future = self.processor.process_message_async({
                        'device': f'CAMERA_RESPONSE_{i}',
                        'line': 1,
                        'vehicle_in': 150,
                        'vehicle_out': 75,
                        'source_ip': '127.0.0.1',
                        'timestamp': datetime.now()
                    })
                    
                    result = future.result(timeout=5)
                    response_time = (time.time() - start_time) * 1000  # en ms
                    
                    response_times.append(response_time)
                    
                    # Validar que el mensaje fue procesado
                    self.assertEqual(result.status, 'success')
        
        # Calcular estadísticas
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # percentil 95
        max_response_time = max(response_times)
        
        # Validar objetivos
        self.assertLess(avg_response_time, self.PERFORMANCE_TARGETS['response_time_ms'],
                       f"Tiempo promedio {avg_response_time:.2f}ms excede objetivo {self.PERFORMANCE_TARGETS['response_time_ms']}ms")
        
        self.assertLess(p95_response_time, self.PERFORMANCE_TARGETS['response_time_ms'] * 1.5,
                       f"P95 {p95_response_time:.2f}ms excede objetivo {self.PERFORMANCE_TARGETS['response_time_ms'] * 1.5}ms")
        
        # Resultados
        print(f"  📈 Mensajes procesados: {samples}")
        print(f"  ⚡ Tiempo promedio: {avg_response_time:.2f}ms")
        print(f"  📊 Mediana: {median_response_time:.2f}ms")
        print(f"  🔝 P95: {p95_response_time:.2f}ms")
        print(f"  📏 Máximo: {max_response_time:.2f}ms")
        print(f"  ✅ Objetivo {self.PERFORMANCE_TARGETS['response_time_ms']}ms: {'CUMPLIDO' if avg_response_time < self.PERFORMANCE_TARGETS['response_time_ms'] else 'FALLIDO'}")
    
    def test_throughput_concurrent_messages(self):
        """Benchmark: Throughput con mensajes concurrentes"""
        print("🚀 Benchmark: Throughput con mensajes concurrentes")
        
        test_scenarios = [
            {'messages': 50, 'workers': 5, 'description': 'Carga baja'},
            {'messages': 100, 'workers': 10, 'description': 'Carga media'},
            {'messages': 200, 'workers': 10, 'description': 'Carga alta'},
        ]
        
        for scenario in test_scenarios:
            print(f"\n📋 Escenario: {scenario['description']} ({scenario['messages']} mensajes, {scenario['workers']} workers)")
            
            # Crear procesador específico para este escenario
            processor = CameraMessageProcessor(max_workers=scenario['workers'], cache_duration=60)
            
            try:
                def process_throughput_message(msg_id):
                    """Procesar mensaje individual para throughput"""
                    with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                        mock_camera = Mock(spec=Access)
                        mock_camera.id = msg_id
                        mock_camera.device_name = f'CAMERA_THROUGHPUT_{msg_id}'
                        mock_camera.line = 1
                        mock_cameras.return_value = [mock_camera]
                        
                        with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                            from camera_message_processor import ProcessingResult
                            
                            # Simular procesamiento realista
                            time.sleep(0.005)  # 5ms de procesamiento
                            
                            mock_process.return_value = ProcessingResult(
                                status='success',
                                message_id=f'throughput_{msg_id}',
                                processing_time_ms=5.0,
                                updated_parkings=[],
                                reset_detected=False
                            )
                            
                            future = processor.process_message_async({
                                'device': f'CAMERA_THROUGHPUT_{msg_id}',
                                'line': 1,
                                'vehicle_in': 150,
                                'vehicle_out': 75,
                                'source_ip': '127.0.0.1',
                                'timestamp': datetime.now()
                            })
                            
                            return future.result(timeout=10)
                
                # Ejecutar benchmark
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=scenario['workers']) as executor:
                    futures = [
                        executor.submit(process_throughput_message, i) 
                        for i in range(scenario['messages'])
                    ]
                    results = [future.result() for future in as_completed(futures)]
                
                total_time = time.time() - start_time
                throughput = len(results) / total_time
                
                # Validar resultados
                successful_results = [r for r in results if r.status == 'success']
                success_rate = len(successful_results) / len(results)
                
                # Validar objetivos
                if scenario['description'] == 'Carga baja':
                    min_throughput = self.PERFORMANCE_TARGETS['throughput_msg_per_sec']
                else:
                    min_throughput = self.PERFORMANCE_TARGETS['throughput_msg_per_sec'] * 0.8  # 80% para cargas altas
                
                self.assertGreaterEqual(throughput, min_throughput,
                                      f"Throughput {throughput:.2f} msg/s por debajo del objetivo {min_throughput}")
                
                self.assertGreaterEqual(success_rate, 1 - self.PERFORMANCE_TARGETS['error_rate'],
                                      f"Success rate {success_rate:.3f} por debajo del objetivo")
                
                # Resultados
                print(f"  📊 Mensajes procesados: {len(results)}")
                print(f"  ⏱️ Tiempo total: {total_time:.3f}s")
                print(f"  🚀 Throughput: {throughput:.2f} msg/s")
                print(f"  ✅ Success rate: {success_rate:.3f}")
                print(f"  🎯 Objetivo throughput: {'CUMPLIDO' if throughput >= min_throughput else 'FALLIDO'}")
                
            finally:
                processor.shutdown()
    
    # =================== BENCHMARKS DE CONCURRENCIA ===================
    
    def test_concurrent_workers_scalability(self):
        """Benchmark: Escalabilidad de workers concurrentes"""
        print("⚖️ Benchmark: Escalabilidad de workers concurrentes")
        
        worker_configs = [1, 2, 5, 10, 15, 20]
        messages_per_config = 100
        results = {}
        
        for worker_count in worker_configs:
            print(f"\n🔧 Configuración: {worker_count} workers")
            
            processor = CameraMessageProcessor(max_workers=worker_count, cache_duration=60)
            
            try:
                def process_scalability_message(msg_id):
                    """Procesar mensaje para test de escalabilidad"""
                    with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                        mock_camera = Mock(spec=Access)
                        mock_camera.id = msg_id
                        mock_camera.device_name = f'CAMERA_SCALE_{msg_id}'
                        mock_camera.line = 1
                        mock_cameras.return_value = [mock_camera]
                        
                        with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                            from camera_message_processor import ProcessingResult
                            
                            # Simular carga de trabajo constante
                            time.sleep(0.01)  # 10ms por mensaje
                            
                            mock_process.return_value = ProcessingResult(
                                status='success',
                                message_id=f'scale_{msg_id}',
                                processing_time_ms=10.0,
                                updated_parkings=[],
                                reset_detected=False
                            )
                            
                            future = processor.process_message_async({
                                'device': f'CAMERA_SCALE_{msg_id}',
                                'line': 1,
                                'vehicle_in': 150,
                                'vehicle_out': 75,
                                'source_ip': '127.0.0.1',
                                'timestamp': datetime.now()
                            })
                            
                            return future.result(timeout=15)
                
                # Ejecutar benchmark
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    futures = [
                        executor.submit(process_scalability_message, i) 
                        for i in range(messages_per_config)
                    ]
                    processed_results = [future.result() for future in as_completed(futures)]
                
                total_time = time.time() - start_time
                throughput = len(processed_results) / total_time
                
                results[worker_count] = {
                    'throughput': throughput,
                    'total_time': total_time,
                    'efficiency': throughput / worker_count if worker_count > 0 else 0
                }
                
                print(f"  🚀 Throughput: {throughput:.2f} msg/s")
                print(f"  ⚡ Eficiencia: {results[worker_count]['efficiency']:.2f} msg/s por worker")
                
            finally:
                processor.shutdown()
        
        # Análizar escalabilidad
        print("\n📊 Análisis de escalabilidad:")
        print("Workers | Throughput | Eficiencia | Mejora")
        print("--------|------------|------------|-------")
        
        baseline_throughput = results[1]['throughput']
        
        for workers in worker_configs:
            data = results[workers]
            improvement = (data['throughput'] / baseline_throughput) if baseline_throughput > 0 else 0
            print(f"{workers:7d} | {data['throughput']:10.2f} | {data['efficiency']:10.2f} | {improvement:6.2f}x")
        
        # Validar que la escalabilidad es efectiva
        max_throughput = max(results[w]['throughput'] for w in worker_configs)
        optimal_workers = [w for w in worker_configs if results[w]['throughput'] == max_throughput][0]
        
        self.assertGreaterEqual(optimal_workers, 5, "Escalabilidad efectiva debe alcanzarse con al menos 5 workers")
        self.assertGreaterEqual(max_throughput, self.PERFORMANCE_TARGETS['throughput_msg_per_sec'] * 2, 
                               "Throughput máximo debe ser al menos 2x el objetivo base")
        
        print(f"\n✅ Configuración óptima: {optimal_workers} workers ({max_throughput:.2f} msg/s)")
    
    # =================== BENCHMARKS DE MEMORIA ===================
    
    def test_memory_efficiency(self):
        """Benchmark: Eficiencia de memoria del sistema"""
        print("💾 Benchmark: Eficiencia de memoria")
        
        import psutil
        import gc
        
        # Medición baseline
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"📊 Memoria baseline: {baseline_memory:.2f} MB")
        
        # Procesamiento intensivo
        processor = CameraMessageProcessor(max_workers=10, cache_duration=60)
        
        try:
            messages_processed = 0
            memory_samples = []
            
            for batch in range(10):  # 10 batches de 50 mensajes cada uno
                batch_start_memory = process.memory_info().rss / 1024 / 1024
                
                def process_memory_message(msg_id):
                    """Procesar mensaje para test de memoria"""
                    with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                        mock_camera = Mock(spec=Access)
                        mock_camera.id = msg_id
                        mock_camera.device_name = f'CAMERA_MEMORY_{msg_id}'
                        mock_camera.line = 1
                        mock_cameras.return_value = [mock_camera]
                        
                        with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                            from camera_message_processor import ProcessingResult
                            
                            mock_process.return_value = ProcessingResult(
                                status='success',
                                message_id=f'memory_{msg_id}',
                                processing_time_ms=5.0,
                                updated_parkings=[],
                                reset_detected=False
                            )
                            
                            future = processor.process_message_async({
                                'device': f'CAMERA_MEMORY_{msg_id}',
                                'line': 1,
                                'vehicle_in': 150,
                                'vehicle_out': 75,
                                'source_ip': '127.0.0.1',
                                'timestamp': datetime.now()
                            })
                            
                            return future.result(timeout=5)
                
                # Procesar batch
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [
                        executor.submit(process_memory_message, messages_processed + i) 
                        for i in range(50)
                    ]
                    batch_results = [future.result() for future in as_completed(futures)]
                
                messages_processed += len(batch_results)
                
                # Medir memoria después del batch
                batch_end_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(batch_end_memory)
                
                print(f"  Batch {batch + 1}: {len(batch_results)} mensajes, {batch_end_memory:.2f} MB")
                
                # Permitir garbage collection entre batches
                time.sleep(0.1)
                gc.collect()
            
            # Análisis de memoria
            max_memory = max(memory_samples)
            avg_memory = statistics.mean(memory_samples)
            memory_growth = max_memory - baseline_memory
            memory_per_message = memory_growth / messages_processed if messages_processed > 0 else 0
            
            # Validar eficiencia de memoria
            max_allowed_growth = 100  # MB
            self.assertLess(memory_growth, max_allowed_growth,
                           f"Crecimiento de memoria {memory_growth:.2f} MB excede límite {max_allowed_growth} MB")
            
            max_memory_per_message = 0.1  # MB por mensaje
            self.assertLess(memory_per_message, max_memory_per_message,
                           f"Memoria por mensaje {memory_per_message:.4f} MB excede límite {max_memory_per_message} MB")
            
            # Resultados
            print(f"\n📊 Resumen de memoria:")
            print(f"  🏁 Baseline: {baseline_memory:.2f} MB")
            print(f"  📈 Máximo: {max_memory:.2f} MB")
            print(f"  📊 Promedio: {avg_memory:.2f} MB")
            print(f"  📏 Crecimiento: {memory_growth:.2f} MB")
            print(f"  💬 Por mensaje: {memory_per_message:.4f} MB")
            print(f"  ✅ Eficiencia: {'BUENA' if memory_growth < max_allowed_growth else 'MEJORABLE'}")
            
        finally:
            processor.shutdown()
            gc.collect()
    
    # =================== BENCHMARK INTEGRADO ===================
    
    def test_system_integrated_benchmark(self):
        """Benchmark integrado completo del sistema"""
        print("🏆 Benchmark: Sistema integrado completo")
        
        # Configuración del benchmark integrado
        duration_seconds = 30  # 30 segundos de prueba
        message_rate = 10      # 10 mensajes por segundo
        total_messages = duration_seconds * message_rate
        
        print(f"⏱️ Duración: {duration_seconds}s")
        print(f"📊 Tasa objetivo: {message_rate} msg/s")
        print(f"📈 Total mensajes: {total_messages}")
        
        # Métricas del benchmark
        sent_messages = 0
        processed_messages = 0
        response_times = []
        errors = 0
        
        processor = CameraMessageProcessor(max_workers=15, cache_duration=300)
        worker = PanelUpdateWorker(update_interval=10, max_panel_workers=5)  # Intervalo corto para testing
        
        try:
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            def send_messages():
                """Enviar mensajes a tasa constante"""
                nonlocal sent_messages
                message_interval = 1.0 / message_rate
                
                while time.time() < end_time:
                    msg_start = time.time()
                    
                    try:
                        with patch('camera_message_processor.CameraMessageProcessor._find_cameras_with_validation') as mock_cameras:
                            mock_camera = Mock(spec=Access)
                            mock_camera.id = sent_messages + 1
                            mock_camera.device_name = f'CAMERA_INTEGRATED_{sent_messages}'
                            mock_camera.line = 1
                            mock_cameras.return_value = [mock_camera]
                            
                            with patch('camera_message_processor.CameraMessageProcessor._process_single_message') as mock_process:
                                from camera_message_processor import ProcessingResult
                                
                                mock_process.return_value = ProcessingResult(
                                    status='success',
                                    message_id=f'integrated_{sent_messages}',
                                    processing_time_ms=20.0,
                                    updated_parkings=[],
                                    reset_detected=False
                                )
                                
                                future = processor.process_message_async({
                                    'device': f'CAMERA_INTEGRATED_{sent_messages}',
                                    'line': 1,
                                    'vehicle_in': 150,
                                    'vehicle_out': 75,
                                    'source_ip': '127.0.0.1',
                                    'timestamp': datetime.now()
                                })
                                
                                result = future.result(timeout=5)
                                
                                if result.status == 'success':
                                    nonlocal processed_messages
                                    processed_messages += 1
                                    response_time = (time.time() - msg_start) * 1000
                                    response_times.append(response_time)
                                else:
                                    nonlocal errors
                                    errors += 1
                        
                        sent_messages += 1
                        
                    except Exception as e:
                        errors += 1
                        print(f"❌ Error enviando mensaje {sent_messages}: {e}")
                    
                    # Esperar hasta el siguiente intervalo
                    elapsed = time.time() - msg_start
                    sleep_time = max(0, message_interval - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            
            # Iniciar worker
            worker.start()
            
            # Ejecutar benchmark
            send_messages()
            
            actual_duration = time.time() - start_time
            
            # Calcular métricas finales
            actual_send_rate = sent_messages / actual_duration
            actual_process_rate = processed_messages / actual_duration
            success_rate = processed_messages / sent_messages if sent_messages > 0 else 0
            error_rate = errors / sent_messages if sent_messages > 0 else 0
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]
            else:
                avg_response_time = 0
                p95_response_time = 0
            
            # Validar objetivos del benchmark integrado
            self.assertGreaterEqual(actual_process_rate, message_rate * 0.9,
                                  f"Tasa de procesamiento {actual_process_rate:.2f} por debajo del 90% del objetivo")
            
            self.assertGreaterEqual(success_rate, 0.99,
                                  f"Success rate {success_rate:.3f} por debajo del 99%")
            
            self.assertLess(avg_response_time, self.PERFORMANCE_TARGETS['response_time_ms'],
                           f"Tiempo promedio {avg_response_time:.2f}ms excede objetivo")
            
            # Resultados finales
            print(f"\n🏆 Resultados del benchmark integrado:")
            print(f"  ⏱️ Duración real: {actual_duration:.2f}s")
            print(f"  📤 Mensajes enviados: {sent_messages}")
            print(f"  ✅ Mensajes procesados: {processed_messages}")
            print(f"  ❌ Errores: {errors}")
            print(f"  📊 Tasa de envío: {actual_send_rate:.2f} msg/s")
            print(f"  🚀 Tasa de procesamiento: {actual_process_rate:.2f} msg/s")
            print(f"  ✅ Success rate: {success_rate:.3f}")
            print(f"  ❌ Error rate: {error_rate:.3f}")
            print(f"  ⚡ Tiempo promedio: {avg_response_time:.2f}ms")
            print(f"  🔝 P95: {p95_response_time:.2f}ms")
            
            # Evaluación final
            objectives_met = 0
            total_objectives = 4
            
            if actual_process_rate >= message_rate * 0.9:
                objectives_met += 1
                print(f"  🎯 Throughput: ✅ CUMPLIDO")
            else:
                print(f"  🎯 Throughput: ❌ FALLIDO")
            
            if success_rate >= 0.99:
                objectives_met += 1
                print(f"  🎯 Success Rate: ✅ CUMPLIDO")
            else:
                print(f"  🎯 Success Rate: ❌ FALLIDO")
            
            if avg_response_time < self.PERFORMANCE_TARGETS['response_time_ms']:
                objectives_met += 1
                print(f"  🎯 Response Time: ✅ CUMPLIDO")
            else:
                print(f"  🎯 Response Time: ❌ FALLIDO")
            
            if error_rate < self.PERFORMANCE_TARGETS['error_rate']:
                objectives_met += 1
                print(f"  🎯 Error Rate: ✅ CUMPLIDO")
            else:
                print(f"  🎯 Error Rate: ❌ FALLIDO")
            
            performance_score = (objectives_met / total_objectives) * 100
            print(f"\n🏆 PUNTUACIÓN FINAL: {performance_score:.0f}% ({objectives_met}/{total_objectives} objetivos)")
            
            # Validar puntuación mínima
            self.assertGreaterEqual(performance_score, 75, 
                                  f"Puntuación {performance_score:.0f}% por debajo del mínimo 75%")
            
        finally:
            processor.shutdown()
            worker.stop()


if __name__ == '__main__':
    # Configurar logging para benchmarks
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar benchmarks con output detallado
    unittest.main(verbosity=2, buffer=True)
