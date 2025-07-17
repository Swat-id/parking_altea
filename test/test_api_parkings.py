#!/usr/bin/env python3
"""
Script de prueba para validar la API de Parkings - Parking Altea v3.1.0
Autor: Sistema Parking Altea
Fecha: 16/07/2025
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuración
BASE_URL = "http://157.180.91.63:6001"
TIMEOUT = 10

class ParkingAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0
            }
        }
    
    def log_test(self, test_name: str, success: bool, details: Dict[str, Any] | None = None):
        """Registra el resultado de una prueba"""
        test_result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results["tests"].append(test_result)
        self.results["summary"]["total_tests"] += 1
        
        if success:
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}: PASÓ")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_name}: FALLÓ")
            if details and "error" in details:
                print(f"   Error: {details['error']}")
    
    def test_connectivity(self) -> bool:
        """Prueba la conectividad básica con el servidor"""
        try:
            response = self.session.get(f"{self.base_url}/parkings", timeout=5)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def test_get_all_parkings(self) -> Dict[str, Any]:
        """Prueba el endpoint GET /parkings"""
        try:
            response = self.session.get(f"{self.base_url}/parkings")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}",
                    "response": response.text
                }
            
            data = response.json()
            
            # Validar estructura básica
            if not isinstance(data, list):
                return {
                    "success": False,
                    "error": "Response is not a list",
                    "response": data
                }
            
            # Validar campos requeridos en cada parking
            required_fields = ["id", "name", "estado", "total_plazas", "plazas_ocupadas", "plazas_libres"]
            for i, parking in enumerate(data):
                missing_fields = [field for field in required_fields if field not in parking]
                if missing_fields:
                    return {
                        "success": False,
                        "error": f"Parking {i} missing fields: {missing_fields}",
                        "parking": parking
                    }
            
            return {
                "success": True,
                "parkings_count": len(data),
                "sample_parking": data[0] if data else None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON decode error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def test_get_parkings_status(self) -> Dict[str, Any]:
        """Prueba el endpoint GET /parkings/status"""
        try:
            response = self.session.get(f"{self.base_url}/parkings/status")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}",
                    "response": response.text
                }
            
            data = response.json()
            
            # Validar estructura
            if not isinstance(data, dict):
                return {
                    "success": False,
                    "error": "Response is not a dictionary",
                    "response": data
                }
            
            required_fields = ["success", "total_parkings", "timestamp", "parkings"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing fields: {missing_fields}",
                    "response": data
                }
            
            if not data["success"]:
                return {
                    "success": False,
                    "error": "API returned success: false",
                    "response": data
                }
            
            # Validar parkings
            parkings = data["parkings"]
            if not isinstance(parkings, list):
                return {
                    "success": False,
                    "error": "Parkings field is not a list",
                    "response": data
                }
            
            # Validar campos de cada parking
            required_parking_fields = [
                "id", "name", "total_plazas", "plazas_ocupadas", "plazas_libres",
                "estado", "estado_valenciano", "panel_display_text", "panels"
            ]
            
            for i, parking in enumerate(parkings):
                missing_fields = [field for field in required_parking_fields if field not in parking]
                if missing_fields:
                    return {
                        "success": False,
                        "error": f"Parking {i} missing fields: {missing_fields}",
                        "parking": parking
                    }
                
                # Validar que panels es una lista
                if not isinstance(parking["panels"], list):
                    return {
                        "success": False,
                        "error": f"Parking {i} panels field is not a list",
                        "parking": parking
                    }
            
            return {
                "success": True,
                "total_parkings": data["total_parkings"],
                "timestamp": data["timestamp"],
                "sample_parking": parkings[0] if parkings else None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON decode error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def test_get_specific_parking(self, parking_id: int = 1) -> Dict[str, Any]:
        """Prueba el endpoint GET /parking/{id}"""
        try:
            response = self.session.get(f"{self.base_url}/parking/{parking_id}")
            
            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Parking {parking_id} not found",
                    "status_code": 404
                }
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}",
                    "response": response.text
                }
            
            data = response.json()
            
            # Validar estructura
            if not isinstance(data, dict):
                return {
                    "success": False,
                    "error": "Response is not a dictionary",
                    "response": data
                }
            
            required_fields = ["id", "name", "total_plazas", "plazas_ocupadas", "plazas_libres", "estado"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing fields: {missing_fields}",
                    "response": data
                }
            
            # Validar que el ID coincide
            if data["id"] != parking_id:
                return {
                    "success": False,
                    "error": f"ID mismatch: expected {parking_id}, got {data['id']}",
                    "response": data
                }
            
            return {
                "success": True,
                "parking": data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON decode error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def test_invalid_parking_id(self) -> Dict[str, Any]:
        """Prueba el endpoint con un ID de parking inválido"""
        try:
            response = self.session.get(f"{self.base_url}/parking/99999")
            
            if response.status_code == 404:
                return {
                    "success": True,
                    "message": "Correctly returned 404 for invalid parking ID"
                }
            else:
                return {
                    "success": False,
                    "error": f"Expected 404, got {response.status_code}",
                    "response": response.text
                }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def analyze_parkings_data(self, parkings_data: List[Dict]) -> Dict[str, Any]:
        """Analiza los datos de parkings para detectar problemas"""
        analysis = {
            "total_parkings": len(parkings_data),
            "status_distribution": {},
            "descuadres": [],
            "panels_summary": {
                "total_panels": 0,
                "online_panels": 0,
                "offline_panels": 0
            },
            "occupancy_summary": {
                "total_spaces": 0,
                "total_occupied": 0,
                "total_free": 0,
                "average_occupancy": 0
            }
        }
        
        for parking in parkings_data:
            # Distribución de estados
            status = parking.get("estado", "UNKNOWN")
            analysis["status_distribution"][status] = analysis["status_distribution"].get(status, 0) + 1
            
            # Detectar descuadres
            if status in ["DESCUADRE_NEGATIVO", "DESCUADRE_POSITIVO"]:
                analysis["descuadres"].append({
                    "id": parking["id"],
                    "name": parking["name"],
                    "status": status,
                    "ocupadas": parking["plazas_ocupadas"],
                    "total": parking["total_plazas"],
                    "libres": parking["plazas_libres"]
                })
            
            # Resumen de ocupación
            total_spaces = parking.get("total_plazas", 0)
            occupied = parking.get("plazas_ocupadas", 0)
            free = parking.get("plazas_libres", 0)
            
            analysis["occupancy_summary"]["total_spaces"] += total_spaces
            analysis["occupancy_summary"]["total_occupied"] += occupied
            analysis["occupancy_summary"]["total_free"] += free
            
            # Resumen de paneles (si está disponible)
            if "panels" in parking:
                panels = parking["panels"]
                analysis["panels_summary"]["total_panels"] += len(panels)
                analysis["panels_summary"]["online_panels"] += len([p for p in panels if p.get("status") == "ONLINE"])
                analysis["panels_summary"]["offline_panels"] += len([p for p in panels if p.get("status") == "OFFLINE"])
        
        # Calcular ocupación media
        if analysis["occupancy_summary"]["total_spaces"] > 0:
            analysis["occupancy_summary"]["average_occupancy"] = (
                analysis["occupancy_summary"]["total_occupied"] / 
                analysis["occupancy_summary"]["total_spaces"] * 100
            )
        
        return analysis
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🚀 Iniciando pruebas de la API de Parkings")
        print("=" * 50)
        
        # Prueba 1: Conectividad
        print("\n1. Probando conectividad...")
        if self.test_connectivity():
            self.log_test("Conectividad", True)
        else:
            self.log_test("Conectividad", False, {"error": "No se puede conectar al servidor"})
            print("❌ No se puede conectar al servidor. Verificar que el servicio esté ejecutándose.")
            return
        
        # Prueba 2: GET /parkings
        print("\n2. Probando GET /parkings...")
        result = self.test_get_all_parkings()
        self.log_test("GET /parkings", result["success"], result)
        
        if result["success"]:
            print(f"   📊 Parkings encontrados: {result['parkings_count']}")
        
        # Prueba 3: GET /parkings/status
        print("\n3. Probando GET /parkings/status...")
        result = self.test_get_parkings_status()
        self.log_test("GET /parkings/status", result["success"], result)
        
        if result["success"]:
            print(f"   📊 Total parkings: {result['total_parkings']}")
            print(f"   🕐 Timestamp: {result['timestamp']}")
        
        # Prueba 4: GET /parking/{id}
        print("\n4. Probando GET /parking/1...")
        result = self.test_get_specific_parking(1)
        self.log_test("GET /parking/1", result["success"], result)
        
        if result["success"]:
            parking = result["parking"]
            print(f"   📍 Parking: {parking['name']}")
            print(f"   🚗 Estado: {parking['estado']}")
        
        # Prueba 5: GET /parking/{id} con ID inválido
        print("\n5. Probando GET /parking/99999 (ID inválido)...")
        result = self.test_invalid_parking_id()
        self.log_test("GET /parking/99999", result["success"], result)
        
        # Análisis de datos (si las pruebas principales pasaron)
        if result["success"] and "parkings" in result and result["parkings"] is not None:
            print("\n6. Analizando datos de parkings...")
            analysis = self.analyze_parkings_data(result["parkings"])
            
            print(f"   📊 Resumen de análisis:")
            print(f"      - Total parkings: {analysis['total_parkings']}")
            print(f"      - Estados: {analysis['status_distribution']}")
            print(f"      - Descuadres: {len(analysis['descuadres'])}")
            print(f"      - Ocupación media: {analysis['occupancy_summary']['average_occupancy']:.1f}%")
            
            if analysis['panels_summary']['total_panels'] > 0:
                print(f"      - Paneles: {analysis['panels_summary']['online_panels']}/{analysis['panels_summary']['total_panels']} online")
            
            if analysis['descuadres']:
                print(f"   ⚠️  Descuadres detectados:")
                for descuadre in analysis['descuadres']:
                    print(f"      - {descuadre['name']}: {descuadre['ocupadas']}/{descuadre['total']} ({descuadre['status']})")
        
        # Resumen final
        print("\n" + "=" * 50)
        print("📋 RESUMEN DE PRUEBAS")
        print("=" * 50)
        
        summary = self.results["summary"]
        print(f"Total pruebas: {summary['total_tests']}")
        print(f"✅ Pasaron: {summary['passed']}")
        print(f"❌ Fallaron: {summary['failed']}")
        print(f"⚠️  Errores: {summary['errors']}")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ¡Todas las pruebas pasaron! La API está funcionando correctamente.")
        elif success_rate >= 80:
            print("\n✅ La mayoría de las pruebas pasaron. La API está funcionando bien.")
        else:
            print("\n⚠️  Hay problemas con la API que requieren atención.")
        
        return self.results

def main():
    """Función principal"""
    tester = ParkingAPITester()
    results = tester.run_all_tests()
    
    # Guardar resultados en archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_parkings_api_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Resultados guardados en: {filename}")
    except Exception as e:
        print(f"\n⚠️  Error guardando resultados: {e}")
    
    # Retornar código de salida
    summary = results["summary"]
    if summary['failed'] > 0 or summary['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 