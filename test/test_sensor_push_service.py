#!/usr/bin/env python3
"""
Script de Testing - Servicio Push Sensores v4.1.0
Pruebas unitarias e integración para el servicio de push de sensores

Autor: Sistema SWATID
Versión: 4.1.0
"""

import unittest
import json
import requests
import time
from datetime import datetime
import sys
import os

# Añadir path para importar módulos del proyecto
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestSensorPushService(unittest.TestCase):
    """Pruebas para el servicio de push de sensores"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial de las pruebas"""
        cls.base_url = "http://localhost:3535"
        cls.timeout = 5
        
        # Datos de prueba
        cls.test_sensor_data = {
            "carpark_id": 1,
            "carpark_code": "TEST_PARKING",
            "floor": "0",
            "id": 999,
            "number": "TEST01",
            "status": "busy",
            "idle": False,
            "timestamp": "2025-09-19 12:00:00",
            "parking_cards": ["TEST1234"],
            "floor_stats": {
                "slot_count": 10,
                "free_count": 5,
                "busy_count": 4,
                "notcalib_count": 1
            },
            "sensor_info": {
                "serial_number": "TEST_SENSOR_001",
                "network_info": {
                    "ip_address": "192.168.1.100",
                    "signal_strength": -65,
                    "connection_type": "WiFi"
                },
                "temperature": 23.5,
                "battery_voltage": 3.2,
                "battery_capacity": 85,
                "visible_cards": ["TEST1234"],
                "radar_only": False
            }
        }
        
        cls.manual_update_data = {
            "sensor_id": 1,
            "status": "free",
            "battery_capacity": 90,
            "battery_voltage": 3.5,
            "temperature": 24.0
        }
    
    def test_01_health_check(self):
        """Prueba del endpoint de health check"""
        print("\n=== TEST: Health Check ===")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data['status'], 'healthy')
            self.assertEqual(data['service'], 'sensor-push-service')
            self.assertEqual(data['version'], '4.1.0')
            self.assertEqual(data['port'], 3535)
            
            print(f"✅ Health check OK: {data}")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"Error conectando al servicio: {e}")
    
    def test_02_push_endpoint_validation(self):
        """Prueba validación de datos en endpoint push"""
        print("\n=== TEST: Validación Push Endpoint ===")
        
        # Test 1: Sin datos JSON
        response = requests.post(f"{self.base_url}/push", timeout=self.timeout)
        self.assertEqual(response.status_code, 400)
        print("✅ Rechaza request sin JSON")
        
        # Test 2: JSON vacío
        response = requests.post(
            f"{self.base_url}/push",
            json={},
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
        print("✅ Rechaza JSON vacío")
        
        # Test 3: Campos obligatorios faltantes
        incomplete_data = {"status": "busy"}
        response = requests.post(
            f"{self.base_url}/push",
            json=incomplete_data,
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        print(f"✅ Rechaza datos incompletos: {data['error']}")
        
        # Test 4: Estado inválido
        invalid_status_data = self.test_sensor_data.copy()
        invalid_status_data['status'] = 'invalid_status'
        
        response = requests.post(
            f"{self.base_url}/push",
            json=invalid_status_data,
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
        print("✅ Rechaza estado inválido")
        
        # Test 5: Timestamp inválido
        invalid_timestamp_data = self.test_sensor_data.copy()
        invalid_timestamp_data['timestamp'] = 'invalid_timestamp'
        
        response = requests.post(
            f"{self.base_url}/push",
            json=invalid_timestamp_data,
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
        print("✅ Rechaza timestamp inválido")
    
    def test_03_push_sensor_not_found(self):
        """Prueba push para sensor no registrado"""
        print("\n=== TEST: Sensor No Registrado ===")
        
        # Usar datos de prueba con serial que no existe en BD
        response = requests.post(
            f"{self.base_url}/push",
            json=self.test_sensor_data,
            timeout=self.timeout
        )
        
        # Debería fallar porque el sensor no está registrado
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('no registrado', data['error'])
        print(f"✅ Maneja correctamente sensor no registrado: {data['error']}")
    
    def test_04_manual_update_validation(self):
        """Prueba validación de actualización manual"""
        print("\n=== TEST: Validación Manual Update ===")
        
        # Test 1: Sin datos JSON
        response = requests.post(f"{self.base_url}/manual-update", timeout=self.timeout)
        self.assertEqual(response.status_code, 400)
        print("✅ Rechaza request sin JSON")
        
        # Test 2: Campos obligatorios faltantes
        incomplete_data = {"sensor_id": 1}
        response = requests.post(
            f"{self.base_url}/manual-update",
            json=incomplete_data,
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        print(f"✅ Rechaza datos incompletos: {data['error']}")
        
        # Test 3: Sensor inexistente
        nonexistent_data = {
            "sensor_id": 99999,
            "status": "free"
        }
        response = requests.post(
            f"{self.base_url}/manual-update",
            json=nonexistent_data,
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        print(f"✅ Maneja sensor inexistente: {data['error']}")
    
    def test_05_stats_endpoint(self):
        """Prueba endpoint de estadísticas"""
        print("\n=== TEST: Endpoint Estadísticas ===")
        
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Verificar estructura de respuesta
            self.assertIn('total_sensors', data)
            self.assertIn('status_distribution', data)
            self.assertIn('type_distribution', data)
            self.assertIn('service_info', data)
            
            # Verificar que los valores son números
            self.assertIsInstance(data['total_sensors'], int)
            self.assertIsInstance(data['status_distribution'], dict)
            self.assertIsInstance(data['type_distribution'], dict)
            
            print(f"✅ Estadísticas OK:")
            print(f"  - Total sensores: {data['total_sensors']}")
            print(f"  - Distribución estados: {data['status_distribution']}")
            print(f"  - Distribución tipos: {data['type_distribution']}")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"Error obteniendo estadísticas: {e}")
    
    def test_06_service_performance(self):
        """Prueba de rendimiento básico del servicio"""
        print("\n=== TEST: Rendimiento Básico ===")
        
        # Medir tiempo de respuesta para health check
        start_time = time.time()
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0, "Health check debería responder en menos de 1 segundo")
        
        print(f"✅ Tiempo de respuesta health check: {response_time:.3f}s")
        
        # Test de múltiples requests concurrentes
        import concurrent.futures
        import threading
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
                return response.status_code == 200
            except:
                return False
        
        # Ejecutar 10 requests concurrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        self.assertGreaterEqual(success_rate, 0.9, "Al menos 90% de requests deberían tener éxito")
        
        print(f"✅ Tasa de éxito requests concurrentes: {success_rate:.1%}")

class TestSensorPushIntegration(unittest.TestCase):
    """Pruebas de integración con datos reales (requiere BD configurada)"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        self.base_url = "http://localhost:3535"
        self.timeout = 10
    
    def test_integration_full_flow(self):
        """Prueba de flujo completo de integración"""
        print("\n=== TEST: Integración Completa ===")
        
        # Este test requiere que haya al menos un sensor en la BD
        # Por ahora solo verificamos que los endpoints respondan
        
        try:
            # 1. Verificar servicio activo
            health_response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            self.assertEqual(health_response.status_code, 200)
            print("✅ Servicio activo")
            
            # 2. Obtener estadísticas actuales
            stats_response = requests.get(f"{self.base_url}/stats", timeout=self.timeout)
            self.assertEqual(stats_response.status_code, 200)
            stats_data = stats_response.json()
            print(f"✅ Estadísticas obtenidas: {stats_data['total_sensors']} sensores")
            
            # 3. Si hay sensores, intentar actualización manual
            if stats_data['total_sensors'] > 0:
                print("ℹ️  Sensores disponibles para testing de actualización manual")
                # Aquí se podría hacer una actualización manual real
                # pero requiere conocer IDs de sensores existentes
            else:
                print("⚠️  No hay sensores registrados para testing completo")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"Error en integración: {e}")

def run_connectivity_test():
    """Prueba básica de conectividad antes de ejecutar tests"""
    print("=== PRUEBA DE CONECTIVIDAD ===")
    
    base_url = "http://localhost:3535"
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servicio disponible: {data['service']} v{data['version']}")
            return True
        else:
            print(f"❌ Servicio responde con código: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servicio en puerto 3535")
        print("   Verificar que el servicio esté ejecutándose:")
        print("   systemctl status parking-sensor-push")
        return False
        
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False

def main():
    """Función principal de testing"""
    print("=== TESTING SERVICIO PUSH SENSORES v4.1.0 ===")
    print(f"Fecha: {datetime.now()}")
    print()
    
    # Prueba de conectividad inicial
    if not run_connectivity_test():
        print("\n❌ TESTING ABORTADO: Servicio no disponible")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("EJECUTANDO TESTS UNITARIOS")
    print("="*50)
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir tests unitarios
    suite.addTests(loader.loadTestsFromTestCase(TestSensorPushService))
    
    # Añadir tests de integración
    suite.addTests(loader.loadTestsFromTestCase(TestSensorPushIntegration))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen final
    print("\n" + "="*50)
    print("RESUMEN DE TESTING")
    print("="*50)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success = total_tests - failures - errors
    
    print(f"Total tests: {total_tests}")
    print(f"Exitosos: {success}")
    print(f"Fallos: {failures}")
    print(f"Errores: {errors}")
    
    if failures > 0:
        print("\n❌ FALLOS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print("\n❌ ERRORES:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Código de salida
    if failures > 0 or errors > 0:
        print(f"\n❌ TESTING FALLIDO")
        sys.exit(1)
    else:
        print(f"\n✅ TODOS LOS TESTS EXITOSOS")
        sys.exit(0)

if __name__ == '__main__':
    main()
