#!/usr/bin/env python3
"""
Tests unitarios para PanelUpdateWorker
Valida el funcionamiento del worker independiente de actualización de paneles
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from panel_update_worker import PanelUpdateWorker, PanelUpdateResult, ParkingUpdateResult
from models import Panel, Parking


class TestPanelUpdateWorker(unittest.TestCase):
    """Tests unitarios para PanelUpdateWorker"""
    
    def setUp(self):
        """Configurar test environment"""
        # Worker con intervalo corto para tests
        self.worker = PanelUpdateWorker(update_interval=1, max_panel_workers=2)
        
        # Mock de base de datos
        self.mock_session = Mock()
        self.worker.Session = Mock(return_value=self.mock_session)
        
        # Mock de panel service
        self.worker.panel_service = Mock()
    
    def tearDown(self):
        """Limpiar después de tests"""
        if self.worker.running:
            self.worker.stop()
    
    # =================== TESTS DE INICIALIZACIÓN ===================
    
    def test_worker_initialization(self):
        """Test de inicialización correcta del worker"""
        worker = PanelUpdateWorker(update_interval=60, max_panel_workers=5)
        
        self.assertEqual(worker.update_interval, 60)
        self.assertEqual(worker.max_panel_workers, 5)
        self.assertFalse(worker.running)
        self.assertIsNone(worker.worker_thread)
        
        # Verificar estadísticas iniciales
        stats = worker.get_stats()
        self.assertEqual(stats['cycles_completed'], 0)
        self.assertEqual(stats['panels_updated'], 0)
        self.assertFalse(stats['is_running'])
        
        worker.stop()
    
    def test_worker_start_stop(self):
        """Test de inicio y parada del worker"""
        # Iniciar worker
        self.worker.start()
        
        self.assertTrue(self.worker.running)
        self.assertIsNotNone(self.worker.worker_thread)
        self.assertTrue(self.worker.worker_thread.is_alive())
        
        # Verificar que las estadísticas muestran que está corriendo
        stats = self.worker.get_stats()
        self.assertTrue(stats['is_running'])
        self.assertTrue(stats['worker_thread_alive'])
        
        # Detener worker
        self.worker.stop()
        
        self.assertFalse(self.worker.running)
        # Dar tiempo para que el thread termine
        time.sleep(0.1)
        
        stats = self.worker.get_stats()
        self.assertFalse(stats['is_running'])
    
    def test_context_manager(self):
        """Test del context manager del worker"""
        with PanelUpdateWorker(update_interval=1) as worker:
            self.assertTrue(worker.running)
            stats = worker.get_stats()
            self.assertTrue(stats['is_running'])
        
        # Al salir del context manager debe detenerse
        self.assertFalse(worker.running)
    
    # =================== TESTS DE OBTENCIÓN DE DATOS ===================
    
    def test_get_parkings_data_success(self):
        """Test de obtención exitosa de datos de parkings"""
        # Mock de resultado de consulta
        mock_result = [
            (1, 'Parking A', 50, 100, 'LIBRE', 20, 10, False, 3),
            (2, 'Parking B', 80, 100, 'DENSO', 15, 5, False, 2),
        ]
        
        self.mock_session.execute().fetchall.return_value = mock_result
        
        parkings_data = self.worker._get_parkings_data(self.mock_session)
        
        self.assertEqual(len(parkings_data), 2)
        
        # Verificar primer parking
        parking1 = parkings_data[0]
        self.assertEqual(parking1['id'], 1)
        self.assertEqual(parking1['name'], 'Parking A')
        self.assertEqual(parking1['current_occupancy'], 50)
        self.assertEqual(parking1['panel_count'], 3)
        
        # Verificar segundo parking
        parking2 = parkings_data[1]
        self.assertEqual(parking2['id'], 2)
        self.assertEqual(parking2['status'], 'DENSO')
        self.assertEqual(parking2['panel_count'], 2)
    
    def test_get_parkings_data_empty(self):
        """Test cuando no hay parkings con paneles"""
        self.mock_session.execute().fetchall.return_value = []
        
        parkings_data = self.worker._get_parkings_data(self.mock_session)
        
        self.assertEqual(len(parkings_data), 0)
    
    def test_get_parkings_data_error(self):
        """Test de manejo de errores en obtención de datos"""
        self.mock_session.execute.side_effect = Exception("Database error")
        
        parkings_data = self.worker._get_parkings_data(self.mock_session)
        
        self.assertEqual(len(parkings_data), 0)
    
    # =================== TESTS DE ESTADÍSTICAS ===================
    
    def test_stats_initialization(self):
        """Test de inicialización correcta de estadísticas"""
        stats = self.worker.get_stats()
        
        expected_keys = [
            'cycles_completed', 'panels_updated', 'panels_failed',
            'parkings_processed', 'last_update', 'average_cycle_time',
            'active_schedules_processed', 'occupancy_updates_sent',
            'errors', 'uptime_start', 'is_running', 'worker_thread_alive'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)
        
        # Verificar valores iniciales
        self.assertEqual(stats['cycles_completed'], 0)
        self.assertEqual(stats['panels_updated'], 0)
        self.assertEqual(stats['errors'], 0)
    
    def test_stats_thread_safety(self):
        """Test de thread safety de estadísticas"""
        def increment_stats():
            with self.worker._stats_lock:
                self.worker._stats['panels_updated'] += 1
        
        # Crear múltiples threads que incrementan stats
        threads = [threading.Thread(target=increment_stats) for _ in range(50)]
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join()
        
        # Verificar que el contador es correcto
        stats = self.worker.get_stats()
        self.assertEqual(stats['panels_updated'], 50)
    
    def test_stats_calculations(self):
        """Test de cálculos adicionales en estadísticas"""
        # Simular datos
        with self.worker._stats_lock:
            self.worker._stats['cycles_completed'] = 10
            self.worker._stats['panels_updated'] = 100
            self.worker._stats['panels_failed'] = 20
            self.worker._stats['errors'] = 2
            self.worker._stats['uptime_start'] = datetime.now() - timedelta(hours=1)
        
        stats = self.worker.get_stats()
        
        # Verificar cálculos
        self.assertEqual(stats['panels_per_cycle'], 10.0)  # 100/10
        self.assertEqual(stats['errors_per_cycle'], 0.2)   # 2/10
        self.assertIn('uptime_seconds', stats)
        self.assertIn('uptime_formatted', stats)
    
    # =================== TESTS DE FORCE UPDATE ===================
    
    @patch('panel_update_worker.PanelUpdateMethods')
    def test_force_update_cycle_success(self, mock_methods):
        """Test de ciclo forzado exitoso"""
        # Mock de datos de parkings
        parking_data = [{'id': 1, 'name': 'Test Parking'}]
        
        with patch.object(self.worker, '_get_parkings_data', return_value=parking_data):
            with patch.object(self.worker, '_update_parking_panels') as mock_update:
                mock_update.return_value = ParkingUpdateResult(
                    parking_id=1,
                    parking_name='Test Parking',
                    message_type='occupancy',
                    message_sent='100',
                    panels_total=3,
                    panels_updated=3,
                    panels_failed=0,
                    execution_time_ms=100.0
                )
                
                # Iniciar worker
                self.worker.start()
                
                # Forzar ciclo
                result = self.worker.force_update_cycle()
                
                self.assertTrue(result['success'])
                self.assertIn('execution_time_ms', result)
                self.assertEqual(result['message'], 'Ciclo forzado completado exitosamente')
    
    def test_force_update_cycle_not_running(self):
        """Test de ciclo forzado cuando worker no está corriendo"""
        result = self.worker.force_update_cycle()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Worker no está ejecutándose')
    
    def test_force_update_cycle_error(self):
        """Test de manejo de errores en ciclo forzado"""
        # Mock que causa error
        with patch.object(self.worker, '_update_all_panels', side_effect=Exception("Test error")):
            self.worker.start()
            
            result = self.worker.force_update_cycle()
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error'], 'Test error')
    
    # =================== TESTS DE INTEGRACIÓN BÁSICA ===================
    
    @patch('panel_update_worker.PanelUpdateMethods')
    def test_update_all_panels_integration(self, mock_methods):
        """Test de integración básica de actualización de paneles"""
        # Mock de datos
        parking_data = [
            {'id': 1, 'name': 'Parking A', 'panel_count': 2},
            {'id': 2, 'name': 'Parking B', 'panel_count': 1}
        ]
        
        with patch.object(self.worker, '_get_parkings_data', return_value=parking_data):
            with patch.object(self.worker, '_update_parking_panels') as mock_update:
                # Mock de resultados exitosos
                mock_update.side_effect = [
                    ParkingUpdateResult(
                        parking_id=1, parking_name='Parking A', message_type='occupancy',
                        message_sent='50', panels_total=2, panels_updated=2, panels_failed=0,
                        execution_time_ms=150.0
                    ),
                    ParkingUpdateResult(
                        parking_id=2, parking_name='Parking B', message_type='schedule',
                        message_sent='MANTENIMIENTO', panels_total=1, panels_updated=1, panels_failed=0,
                        execution_time_ms=80.0
                    )
                ]
                
                # Ejecutar actualización
                self.worker._update_all_panels()
                
                # Verificar que se llamó para cada parking
                self.assertEqual(mock_update.call_count, 2)
                
                # Verificar estadísticas actualizadas
                stats = self.worker.get_stats()
                self.assertEqual(stats['parkings_processed'], 2)
                self.assertEqual(stats['panels_updated'], 3)  # 2 + 1
                self.assertEqual(stats['active_schedules_processed'], 1)
                self.assertEqual(stats['occupancy_updates_sent'], 1)
    
    def test_update_all_panels_no_panel_service(self):
        """Test cuando no hay servicio de paneles disponible"""
        # Simular servicio no disponible
        self.worker.panel_service = None
        
        # La función debe retornar sin hacer nada
        self.worker._update_all_panels()
        
        # Verificar que no se procesó nada
        stats = self.worker.get_stats()
        self.assertEqual(stats['parkings_processed'], 0)
    
    def test_update_all_panels_no_parkings(self):
        """Test cuando no hay parkings para procesar"""
        with patch.object(self.worker, '_get_parkings_data', return_value=[]):
            self.worker._update_all_panels()
            
            # Verificar que no se procesó nada
            stats = self.worker.get_stats()
            self.assertEqual(stats['parkings_processed'], 0)
    
    # =================== TESTS DE MANEJO DE ERRORES ===================
    
    def test_worker_loop_error_handling(self):
        """Test de manejo de errores en el bucle principal"""
        # Mock que cause error en la actualización
        with patch.object(self.worker, '_update_all_panels', side_effect=Exception("Test error")):
            self.worker.start()
            
            # Esperar a que se ejecute al menos un ciclo
            time.sleep(1.5)
            
            # Verificar que el worker sigue corriendo a pesar del error
            self.assertTrue(self.worker.running)
            
            # Verificar que se registró el error
            stats = self.worker.get_stats()
            self.assertGreater(stats['errors'], 0)
    
    def test_database_error_resilience(self):
        """Test de resistencia a errores de base de datos"""
        # Mock que cause error de BD
        self.mock_session.execute.side_effect = Exception("Database connection lost")
        
        # La función debe manejar el error sin crashear
        parkings = self.worker._get_parkings_data(self.mock_session)
        
        self.assertEqual(len(parkings), 0)
        # No debe lanzar excepción


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)
