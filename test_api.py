#!/usr/bin/env python3
"""
Script de Pruebas Automatizadas - API REST Parking Altea
Ejecuta todas las pruebas de endpoints y genera un reporte detallado
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class ParkingAlteaAPITester:
    def __init__(self, base_url: str = "http://157.180.91.63:6001"):
        self.base_url = base_url
        self.results = []
        self.start_time = datetime.now()
        
    def log_test(self, endpoint: str, method: str, status: str, details: str = "", response_data: Any = None):
        """Registra el resultado de una prueba"""
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details,
            "response_data": response_data
        }
        self.results.append(test_result)
        print(f"[{status}] {method} {endpoint} - {details}")
        
    def test_get_parkings(self) -> bool:
        """Prueba GET /parkings"""
        try:
            response = requests.get(f"{self.base_url}/parkings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                parking_count = len(data)
                self.log_test("/parkings", "GET", "✅ EXITOSO", 
                            f"Lista de {parking_count} parkings obtenida", data[:2])  # Solo primeros 2 para el log
                return True
            else:
                self.log_test("/parkings", "GET", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/parkings", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_get_parking_specific(self, parking_id: int = 1) -> bool:
        """Prueba GET /parking/{id}"""
        try:
            response = requests.get(f"{self.base_url}/parking/{parking_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"/parking/{parking_id}", "GET", "✅ EXITOSO", 
                            f"Parking {data.get('name', 'N/A')} obtenido", data)
                return True
            else:
                self.log_test(f"/parking/{parking_id}", "GET", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"/parking/{parking_id}", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_update_occupancy(self, parking_id: int = 1, occupancy: int = 450) -> bool:
        """Prueba POST /parking/{id}/occupancy"""
        try:
            payload = {"occupancy": occupancy}
            response = requests.post(
                f"{self.base_url}/parking/{parking_id}/occupancy",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"/parking/{parking_id}/occupancy", "POST", "✅ EXITOSO", 
                            f"Ocupación actualizada a {occupancy}", data)
                return True
            else:
                self.log_test(f"/parking/{parking_id}/occupancy", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"/parking/{parking_id}/occupancy", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_update_config(self, parking_id: int = 1) -> bool:
        """Prueba POST /parking/{id}/config"""
        try:
            payload = {
                "max_capacity": 500,
                "threshold_dense": 30,
                "threshold_full": 10
            }
            response = requests.post(
                f"{self.base_url}/parking/{parking_id}/config",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"/parking/{parking_id}/config", "POST", "✅ EXITOSO", 
                            "Configuración actualizada", data)
                return True
            else:
                self.log_test(f"/parking/{parking_id}/config", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"/parking/{parking_id}/config", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_send_message(self, parking_id: int = 1) -> bool:
        """Prueba POST /parking/{id}/message"""
        try:
            payload = {
                "message": f"Test automático - {datetime.now().strftime('%H:%M:%S')}",
                "color": "AMARILLO",
                "scroll": True
            }
            response = requests.post(
                f"{self.base_url}/parking/{parking_id}/message",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                panels_success = data.get('panels_success', 0)
                panels_failed = len(data.get('panels_failed', []))
                self.log_test(f"/parking/{parking_id}/message", "POST", "✅ EXITOSO", 
                            f"Mensaje enviado - {panels_success} exitosos, {panels_failed} fallidos", data)
                return True
            else:
                self.log_test(f"/parking/{parking_id}/message", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"/parking/{parking_id}/message", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_get_messages(self, parking_id: int = 1) -> bool:
        """Prueba GET /parking/{id}/message"""
        try:
            response = requests.get(f"{self.base_url}/parking/{parking_id}/message", timeout=10)
            if response.status_code == 200:
                data = response.json()
                message_count = len(data) if isinstance(data, list) else 0
                self.log_test(f"/parking/{parking_id}/message", "GET", "✅ EXITOSO", 
                            f"{message_count} mensajes programados", data)
                return True
            else:
                self.log_test(f"/parking/{parking_id}/message", "GET", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"/parking/{parking_id}/message", "GET", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def test_camera_endpoint(self) -> bool:
        """Prueba el endpoint de cámaras"""
        try:
            camera_url = "http://157.180.91.63:6400/camera"
            payload = {
                "device_name": "TEST_CAMERA_01",
                "occupancy": 150,
                "timestamp": datetime.now().isoformat()
            }
            response = requests.post(
                camera_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                self.log_test("/camera", "POST", "✅ EXITOSO", 
                            "Datos de cámara enviados correctamente", payload)
                return True
            else:
                self.log_test("/camera", "POST", "❌ ERROR", 
                            f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/camera", "POST", "❌ ERROR", f"Excepción: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todas las pruebas"""
        print("🚀 Iniciando pruebas automatizadas de la API Parking Altea")
        print("=" * 60)
        
        tests = [
            ("GET /parkings", self.test_get_parkings),
            ("GET /parking/1", self.test_get_parking_specific),
            ("POST /parking/1/occupancy", self.test_update_occupancy),
            ("POST /parking/1/config", self.test_update_config),
            ("POST /parking/1/message", self.test_send_message),
            ("GET /parking/1/message", self.test_get_messages),
            ("POST /camera", self.test_camera_endpoint),
        ]
        
        successful_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Ejecutando: {test_name}")
            if test_func():
                successful_tests += 1
            time.sleep(1)  # Pausa entre pruebas
        
        # Generar reporte
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "test_date": self.start_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "results": self.results
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Guarda el reporte en un archivo JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte guardado en: {filename}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprime un resumen de las pruebas"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        print(f"Fecha: {report['test_date']}")
        print(f"Duración: {report['duration_seconds']:.2f} segundos")
        print(f"Total de pruebas: {report['total_tests']}")
        print(f"Pruebas exitosas: {report['successful_tests']}")
        print(f"Pruebas fallidas: {report['failed_tests']}")
        print(f"Tasa de éxito: {report['success_rate']:.1f}%")
        
        if report['success_rate'] >= 90:
            print("🎉 Estado: EXCELENTE")
        elif report['success_rate'] >= 70:
            print("✅ Estado: BUENO")
        elif report['success_rate'] >= 50:
            print("⚠️  Estado: REGULAR")
        else:
            print("❌ Estado: CRÍTICO")

def main():
    """Función principal"""
    tester = ParkingAlteaAPITester()
    report = tester.run_all_tests()
    tester.print_summary(report)
    tester.save_report(report)
    
    # Guardar también en docs para documentación
    docs_filename = "docs/latest_test_report.json"
    tester.save_report(report, docs_filename)

if __name__ == "__main__":
    main() 