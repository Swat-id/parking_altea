#!/usr/bin/env python3
"""
Script maestro para ejecutar todos los tests de la Fase 4
Ejecuta tests end-to-end, rendimiento y escenarios críticos con reporte completo
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


class Phase4TestRunner:
    """Runner de tests completo para Fase 4"""
    
    def __init__(self):
        """Inicializar runner de tests"""
        self.start_time = datetime.now()
        self.results = {
            'phase_4_results': {
                'start_time': self.start_time.isoformat(),
                'test_suites': {},
                'summary': {},
                'recommendations': []
            }
        }
        
        # Configuración de test suites
        self.test_suites = {
            'unit_tests': {
                'name': 'Tests Unitarios',
                'files': [
                    'tests/unit/test_camera_message_processor.py',
                    'tests/unit/test_camera_detection_methods.py',
                    'tests/unit/test_panel_update_worker.py'
                ],
                'required': True,
                'timeout': 300  # 5 minutos
            },
            'integration_tests': {
                'name': 'Tests de Integración',
                'files': [
                    'tests/integration/test_camera_server_v3_4_0.py'
                ],
                'required': True,
                'timeout': 600  # 10 minutos
            },
            'e2e_tests': {
                'name': 'Tests End-to-End',
                'files': [
                    'tests/e2e/test_system_complete_v3_4_0.py'
                ],
                'required': True,
                'timeout': 900  # 15 minutos
            },
            'performance_tests': {
                'name': 'Tests de Rendimiento',
                'files': [
                    'tests/performance/test_performance_benchmarks_v3_4_0.py'
                ],
                'required': True,
                'timeout': 1200  # 20 minutos
            },
            'critical_tests': {
                'name': 'Tests de Escenarios Críticos',
                'files': [
                    'tests/critical/test_critical_scenarios_v3_4_0.py'
                ],
                'required': True,
                'timeout': 900  # 15 minutos
            }
        }
        
        print("🧪 PHASE 4 TEST RUNNER v3.4.0")
        print("=" * 50)
        print(f"Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test suites: {len(self.test_suites)}")
        print()
    
    def run_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar una suite de tests
        
        Args:
            suite_name: Nombre de la suite
            suite_config: Configuración de la suite
            
        Returns:
            Resultados de la suite
        """
        print(f"🔬 Ejecutando: {suite_config['name']}")
        print(f"📁 Archivos: {len(suite_config['files'])}")
        
        suite_start = time.time()
        suite_results = {
            'name': suite_config['name'],
            'files': suite_config['files'],
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'execution_time': 0,
            'file_results': {},
            'errors': []
        }
        
        try:
            for test_file in suite_config['files']:
                print(f"  📄 Ejecutando: {test_file}")
                
                if not os.path.exists(test_file):
                    error_msg = f"Archivo no encontrado: {test_file}"
                    print(f"    ❌ {error_msg}")
                    suite_results['errors'].append(error_msg)
                    continue
                
                # Ejecutar test file
                file_start = time.time()
                
                try:
                    # Comando para ejecutar tests con unittest
                    cmd = [sys.executable, '-m', 'unittest', test_file.replace('/', '.').replace('\\', '.').replace('.py', ''), '-v']
                    
                    # Ejecutar con timeout
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=suite_config['timeout'],
                        cwd=os.path.dirname(os.path.abspath(__file__)) + '/..'
                    )
                    
                    file_duration = time.time() - file_start
                    
                    # Parsear resultados
                    file_results = self._parse_unittest_output(result.stderr, result.stdout, result.returncode)
                    file_results['execution_time'] = file_duration
                    file_results['file_path'] = test_file
                    
                    suite_results['file_results'][test_file] = file_results
                    
                    # Acumular estadísticas
                    suite_results['tests_run'] += file_results['tests_run']
                    suite_results['tests_passed'] += file_results['tests_passed']
                    suite_results['tests_failed'] += file_results['tests_failed']
                    suite_results['tests_skipped'] += file_results['tests_skipped']
                    
                    # Status del archivo
                    if file_results['tests_failed'] > 0:
                        print(f"    ❌ FAILED: {file_results['tests_failed']} tests fallidos")
                        if file_results['errors']:
                            for error in file_results['errors'][:3]:  # Mostrar solo primeros 3 errores
                                print(f"       {error}")
                    else:
                        print(f"    ✅ PASSED: {file_results['tests_passed']} tests exitosos")
                    
                    print(f"    ⏱️ Tiempo: {file_duration:.2f}s")
                
                except subprocess.TimeoutExpired:
                    error_msg = f"Timeout ejecutando {test_file} (>{suite_config['timeout']}s)"
                    print(f"    ⏰ {error_msg}")
                    suite_results['errors'].append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error ejecutando {test_file}: {e}"
                    print(f"    ❌ {error_msg}")
                    suite_results['errors'].append(error_msg)
            
            # Completar suite
            suite_results['execution_time'] = time.time() - suite_start
            suite_results['end_time'] = datetime.now().isoformat()
            
            # Determinar status final
            if suite_results['tests_failed'] > 0 or suite_results['errors']:
                suite_results['status'] = 'failed'
                print(f"  ❌ Suite FAILED: {suite_results['tests_failed']} tests fallidos, {len(suite_results['errors'])} errores")
            elif suite_results['tests_run'] == 0:
                suite_results['status'] = 'no_tests'
                print(f"  ⚠️ Suite WARNING: No se ejecutaron tests")
            else:
                suite_results['status'] = 'passed'
                print(f"  ✅ Suite PASSED: {suite_results['tests_passed']} tests exitosos")
            
            print(f"  ⏱️ Tiempo total: {suite_results['execution_time']:.2f}s")
            
        except Exception as e:
            suite_results['status'] = 'error'
            suite_results['execution_time'] = time.time() - suite_start
            suite_results['errors'].append(f"Error crítico en suite: {e}")
            print(f"  💥 ERROR CRÍTICO: {e}")
        
        print()
        return suite_results
    
    def _parse_unittest_output(self, stderr: str, stdout: str, returncode: int) -> Dict[str, Any]:
        """
        Parsear output de unittest
        
        Args:
            stderr: Error output
            stdout: Standard output
            returncode: Código de retorno
            
        Returns:
            Resultados parseados
        """
        results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'errors': [],
            'returncode': returncode,
            'stdout': stdout,
            'stderr': stderr
        }
        
        # Parsear stderr para estadísticas de unittest
        output = stderr + stdout
        
        # Buscar línea de resumen (ej: "Ran 25 tests in 10.234s")
        import re
        
        # Patrón para "Ran X tests in Y.Zs"
        run_match = re.search(r'Ran (\d+) tests? in ([\d.]+)s', output)
        if run_match:
            results['tests_run'] = int(run_match.group(1))
        
        # Patrón para resultados (ej: "OK", "FAILED (failures=2, errors=1)")
        if 'OK' in output and returncode == 0:
            results['tests_passed'] = results['tests_run']
        elif 'FAILED' in output:
            # Buscar detalles de fallos
            fail_match = re.search(r'failures=(\d+)', output)
            error_match = re.search(r'errors=(\d+)', output)
            skip_match = re.search(r'skipped=(\d+)', output)
            
            if fail_match:
                results['tests_failed'] = int(fail_match.group(1))
            if error_match:
                results['tests_failed'] += int(error_match.group(1))
            if skip_match:
                results['tests_skipped'] = int(skip_match.group(1))
            
            results['tests_passed'] = results['tests_run'] - results['tests_failed'] - results['tests_skipped']
        
        # Extraer errores específicos
        error_lines = [line.strip() for line in output.split('\n') if 'ERROR' in line or 'FAIL' in line]
        results['errors'] = error_lines[:5]  # Máximo 5 errores
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Ejecutar todos los test suites
        
        Returns:
            Resultados completos
        """
        print("🚀 INICIANDO EJECUCIÓN COMPLETA DE TESTS FASE 4")
        print("=" * 60)
        
        total_suites = len(self.test_suites)
        completed_suites = 0
        
        for suite_name, suite_config in self.test_suites.items():
            print(f"📋 Suite {completed_suites + 1}/{total_suites}: {suite_name}")
            
            suite_results = self.run_test_suite(suite_name, suite_config)
            self.results['phase_4_results']['test_suites'][suite_name] = suite_results
            
            completed_suites += 1
            
            # Parar si es requerido y falló
            if suite_config['required'] and suite_results['status'] in ['failed', 'error']:
                print(f"⚠️ Suite requerida falló: {suite_name}")
                print("❌ Deteniendo ejecución de tests")
                break
        
        # Generar resumen
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """Generar resumen de resultados"""
        print("📊 GENERANDO RESUMEN DE RESULTADOS")
        print("=" * 50)
        
        summary = {
            'total_suites': len(self.test_suites),
            'suites_executed': len(self.results['phase_4_results']['test_suites']),
            'suites_passed': 0,
            'suites_failed': 0,
            'total_tests_run': 0,
            'total_tests_passed': 0,
            'total_tests_failed': 0,
            'total_execution_time': (datetime.now() - self.start_time).total_seconds(),
            'overall_status': 'unknown'
        }
        
        # Calcular estadísticas
        for suite_name, suite_results in self.results['phase_4_results']['test_suites'].items():
            if suite_results['status'] == 'passed':
                summary['suites_passed'] += 1
            else:
                summary['suites_failed'] += 1
            
            summary['total_tests_run'] += suite_results['tests_run']
            summary['total_tests_passed'] += suite_results['tests_passed']
            summary['total_tests_failed'] += suite_results['tests_failed']
        
        # Determinar status general
        if summary['suites_failed'] == 0 and summary['total_tests_failed'] == 0:
            summary['overall_status'] = 'passed'
        elif summary['total_tests_failed'] / max(summary['total_tests_run'], 1) < 0.1:
            summary['overall_status'] = 'mostly_passed'
        else:
            summary['overall_status'] = 'failed'
        
        # Calcular tasas
        success_rate = summary['total_tests_passed'] / max(summary['total_tests_run'], 1)
        
        self.results['phase_4_results']['summary'] = summary
        self.results['phase_4_results']['end_time'] = datetime.now().isoformat()
        
        # Mostrar resumen
        print(f"⏱️ Tiempo total: {summary['total_execution_time']:.2f}s")
        print(f"📦 Suites ejecutadas: {summary['suites_executed']}/{summary['total_suites']}")
        print(f"✅ Suites exitosas: {summary['suites_passed']}")
        print(f"❌ Suites fallidas: {summary['suites_failed']}")
        print(f"🧪 Tests ejecutados: {summary['total_tests_run']}")
        print(f"✅ Tests exitosos: {summary['total_tests_passed']}")
        print(f"❌ Tests fallidos: {summary['total_tests_failed']}")
        print(f"📈 Tasa de éxito: {success_rate:.1%}")
        print(f"🎯 Status general: {summary['overall_status'].upper()}")
        
        # Generar recomendaciones
        self._generate_recommendations()
        
        print()
        print("=" * 50)
        if summary['overall_status'] == 'passed':
            print("🎉 FASE 4 COMPLETADA EXITOSAMENTE")
            print("✅ Sistema listo para despliegue en producción")
        elif summary['overall_status'] == 'mostly_passed':
            print("⚠️ FASE 4 COMPLETADA CON ADVERTENCIAS")
            print("🔧 Revisar fallos menores antes del despliegue")
        else:
            print("❌ FASE 4 FALLIDA")
            print("🚫 Sistema NO listo para despliegue")
        print("=" * 50)
    
    def _generate_recommendations(self):
        """Generar recomendaciones basadas en resultados"""
        recommendations = []
        summary = self.results['phase_4_results']['summary']
        
        # Recomendaciones basadas en resultados
        if summary['total_tests_failed'] == 0:
            recommendations.append("✅ Todos los tests pasaron - Sistema listo para producción")
        elif summary['total_tests_failed'] < 5:
            recommendations.append("⚠️ Pocos tests fallaron - Revisar fallos específicos")
        else:
            recommendations.append("❌ Múltiples tests fallaron - Revisión completa necesaria")
        
        if summary['total_execution_time'] > 3600:  # > 1 hora
            recommendations.append("⏰ Tiempo de ejecución elevado - Optimizar tests")
        
        # Recomendaciones por suite
        for suite_name, suite_results in self.results['phase_4_results']['test_suites'].items():
            if suite_results['status'] == 'failed':
                recommendations.append(f"🔧 Revisar suite fallida: {suite_results['name']}")
        
        self.results['phase_4_results']['recommendations'] = recommendations
        
        if recommendations:
            print("\n💡 RECOMENDACIONES:")
            for rec in recommendations:
                print(f"  {rec}")
    
    def save_results(self, filename: str = None):
        """
        Guardar resultados en archivo JSON
        
        Args:
            filename: Nombre del archivo (opcional)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'test_results_phase4_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"💾 Resultados guardados en: {filename}")
            
        except Exception as e:
            print(f"❌ Error guardando resultados: {e}")


def main():
    """Función principal del script"""
    print("Phase 4 Test Runner - Sistema v3.4.0")
    print("====================================")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('src'):
        print("❌ Error: Execute desde el directorio raíz del proyecto")
        return 1
    
    # Crear runner y ejecutar tests
    runner = Phase4TestRunner()
    
    try:
        results = runner.run_all_tests()
        
        # Guardar resultados
        runner.save_results()
        
        # Determinar código de salida
        summary = results['phase_4_results']['summary']
        if summary['overall_status'] == 'passed':
            return 0
        elif summary['overall_status'] == 'mostly_passed':
            return 1
        else:
            return 2
    
    except KeyboardInterrupt:
        print("\n⚠️ Ejecución interrumpida por usuario")
        return 130
    
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
