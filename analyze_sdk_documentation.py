#!/usr/bin/env python3
"""
Análisis Técnico de Documentación SDK - Paneles Rotuloselectronicos.NET
Parking Altea v2.4 - Integración Avanzada con Paneles Electrónicos

Este script analiza la documentación técnica del SDK CP5200 para extraer
información clave sobre el protocolo de comunicación con paneles.
"""

import os
import re
import json
import struct
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class SDKDocumentationAnalyzer:
    """Analizador de documentación SDK para paneles electrónicos"""
    
    def __init__(self, docs_path: str = "docs/Rotuloselectronicos.NET_API+ejemplos"):
        self.docs_path = Path(docs_path)
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'sdk_version': 'CP5200',
            'files_analyzed': [],
            'functions_found': [],
            'protocol_details': {},
            'examples_found': [],
            'recommendations': []
        }
    
    def analyze_documentation(self) -> Dict[str, Any]:
        """Analiza toda la documentación SDK disponible"""
        print("🔍 Iniciando análisis de documentación SDK...")
        
        if not self.docs_path.exists():
            print(f"❌ Ruta de documentación no encontrada: {self.docs_path}")
            return self.analysis_results
        
        # Analizar estructura de directorios
        self._analyze_directory_structure()
        
        # Analizar archivos DLL y headers
        self._analyze_binary_files()
        
        # Analizar código fuente de ejemplos
        self._analyze_source_code()
        
        # Analizar documentación PDF
        self._analyze_pdf_documentation()
        
        # Generar recomendaciones
        self._generate_recommendations()
        
        return self.analysis_results
    
    def _analyze_directory_structure(self):
        """Analiza la estructura de directorios de la documentación"""
        print("📁 Analizando estructura de directorios...")
        
        structure = {
            'root': str(self.docs_path),
            'subdirectories': [],
            'files': []
        }
        
        for item in self.docs_path.rglob('*'):
            if item.is_file():
                structure['files'].append({
                    'name': item.name,
                    'path': str(item.relative_to(self.docs_path)),
                    'size': item.stat().st_size,
                    'extension': item.suffix.lower()
                })
            elif item.is_dir():
                structure['subdirectories'].append(str(item.relative_to(self.docs_path)))
        
        self.analysis_results['directory_structure'] = structure
        print(f"✅ Encontrados {len(structure['files'])} archivos en {len(structure['subdirectories'])} directorios")
    
    def _analyze_binary_files(self):
        """Analiza archivos binarios (DLL, LIB, etc.)"""
        print("🔧 Analizando archivos binarios...")
        
        binary_files = []
        for file_info in self.analysis_results['directory_structure']['files']:
            if file_info['extension'] in ['.dll', '.lib', '.exe']:
                binary_files.append(file_info)
        
        # Análisis específico de CP5200.dll
        cp5200_files = [f for f in binary_files if 'cp5200' in f['name'].lower()]
        
        binary_analysis = {
            'total_binary_files': len(binary_files),
            'cp5200_files': cp5200_files,
            'architectures': self._detect_architectures(binary_files),
            'dependencies': self._analyze_dependencies(binary_files)
        }
        
        self.analysis_results['binary_analysis'] = binary_analysis
        print(f"✅ Analizados {len(binary_files)} archivos binarios")
    
    def _detect_architectures(self, binary_files: List[Dict]) -> Dict[str, List[str]]:
        """Detecta arquitecturas de archivos binarios"""
        architectures = {
            'x86': [],
            'x64': [],
            'unknown': []
        }
        
        for file_info in binary_files:
            if 'x64' in file_info['name'].lower() or 'x86_64' in file_info['name'].lower():
                architectures['x64'].append(file_info['name'])
            elif 'x86' in file_info['name'].lower() or 'win32' in file_info['name'].lower():
                architectures['x86'].append(file_info['name'])
            else:
                architectures['unknown'].append(file_info['name'])
        
        return architectures
    
    def _analyze_dependencies(self, binary_files: List[Dict]) -> Dict[str, List[str]]:
        """Analiza dependencias de archivos binarios"""
        dependencies = {
            'system_dlls': [],
            'framework_dlls': [],
            'custom_dlls': []
        }
        
        # Dependencias típicas del sistema
        system_dlls = ['kernel32.dll', 'user32.dll', 'ws2_32.dll', 'msvcrt.dll']
        framework_dlls = ['mscorlib.dll', 'System.dll', 'System.Net.dll']
        
        for file_info in binary_files:
            if file_info['name'].lower() in system_dlls:
                dependencies['system_dlls'].append(file_info['name'])
            elif file_info['name'].lower() in framework_dlls:
                dependencies['framework_dlls'].append(file_info['name'])
            else:
                dependencies['custom_dlls'].append(file_info['name'])
        
        return dependencies
    
    def _analyze_source_code(self):
        """Analiza código fuente de ejemplos"""
        print("💻 Analizando código fuente de ejemplos...")
        
        source_files = []
        for file_info in self.analysis_results['directory_structure']['files']:
            if file_info['extension'] in ['.cs', '.vb', '.cpp', '.h', '.hpp']:
                source_files.append(file_info)
        
        # Análisis específico de archivos C#
        cs_files = [f for f in source_files if f['extension'] == '.cs']
        source_analysis = {
            'total_source_files': len(source_files),
            'csharp_files': cs_files,
            'functions_extracted': self._extract_functions_from_cs(cs_files),
            'usage_examples': self._extract_usage_examples(cs_files)
        }
        
        self.analysis_results['source_analysis'] = source_analysis
        print(f"✅ Analizados {len(source_files)} archivos de código fuente")
    
    def _extract_functions_from_cs(self, cs_files: List[Dict]) -> List[Dict]:
        """Extrae funciones de archivos C#"""
        functions = []
        
        for file_info in cs_files:
            file_path = self.docs_path / file_info['path']
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Buscar declaraciones de funciones DllImport
                dll_import_pattern = r'\[DllImport\("([^"]+)"\)\]\s*public\s+static\s+extern\s+(\w+)\s+(\w+)\s*\(([^)]*)\)'
                matches = re.findall(dll_import_pattern, content, re.MULTILINE)
                
                for match in matches:
                    dll_name, return_type, function_name, parameters = match
                    functions.append({
                        'dll': dll_name,
                        'return_type': return_type,
                        'name': function_name,
                        'parameters': self._parse_parameters(parameters),
                        'file': file_info['name']
                    })
                    
            except Exception as e:
                print(f"⚠️ Error analizando {file_info['name']}: {e}")
        
        return functions
    
    def _parse_parameters(self, param_string: str) -> List[Dict]:
        """Parsea string de parámetros a lista estructurada"""
        if not param_string.strip():
            return []
        
        params = []
        param_parts = param_string.split(',')
        
        for part in param_parts:
            part = part.strip()
            if not part:
                continue
            
            # Buscar tipo y nombre del parámetro
            param_match = re.match(r'(\w+)\s+(\w+)', part)
            if param_match:
                param_type, param_name = param_match.groups()
                params.append({
                    'type': param_type,
                    'name': param_name
                })
        
        return params
    
    def _extract_usage_examples(self, cs_files: List[Dict]) -> List[Dict]:
        """Extrae ejemplos de uso del código fuente"""
        examples = []
        
        for file_info in cs_files:
            file_path = self.docs_path / file_info['path']
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Buscar llamadas a funciones CP5200
                function_calls = re.findall(r'CP5200_\w+\([^)]*\)', content)
                
                for call in function_calls:
                    examples.append({
                        'function_call': call,
                        'file': file_info['name'],
                        'context': self._extract_context(content, call)
                    })
                    
            except Exception as e:
                print(f"⚠️ Error extrayendo ejemplos de {file_info['name']}: {e}")
        
        return examples
    
    def _extract_context(self, content: str, function_call: str) -> str:
        """Extrae contexto alrededor de una llamada de función"""
        # Buscar líneas alrededor de la llamada
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if function_call in line:
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                return '\n'.join(lines[start:end])
        return ""
    
    def _analyze_pdf_documentation(self):
        """Analiza documentación PDF (información básica)"""
        print("📄 Analizando documentación PDF...")
        
        pdf_files = []
        for file_info in self.analysis_results['directory_structure']['files']:
            if file_info['extension'] == '.pdf':
                pdf_files.append(file_info)
        
        pdf_analysis = {
            'total_pdf_files': len(pdf_files),
            'pdf_files': pdf_files,
            'protocol_documents': [f for f in pdf_files if 'protocol' in f['name'].lower()],
            'example_documents': [f for f in pdf_files if 'example' in f['name'].lower()],
            'basic_documents': [f for f in pdf_files if 'basic' in f['name'].lower()]
        }
        
        self.analysis_results['pdf_analysis'] = pdf_analysis
        print(f"✅ Encontrados {len(pdf_files)} archivos PDF")
    
    def _generate_recommendations(self):
        """Genera recomendaciones basadas en el análisis"""
        print("💡 Generando recomendaciones...")
        
        recommendations = []
        
        # Análisis de funciones encontradas
        functions = self.analysis_results.get('source_analysis', {}).get('functions_extracted', [])
        cp5200_functions = [f for f in functions if f['dll'].lower() == 'cp5200.dll']
        
        if cp5200_functions:
            recommendations.append({
                'type': 'function_implementation',
                'priority': 'high',
                'description': f'Implementar {len(cp5200_functions)} funciones CP5200 identificadas',
                'functions': [f['name'] for f in cp5200_functions]
            })
        
        # Análisis de arquitecturas
        architectures = self.analysis_results.get('binary_analysis', {}).get('architectures', {})
        if architectures['x64'] and architectures['x86']:
            recommendations.append({
                'type': 'architecture_support',
                'priority': 'medium',
                'description': 'Soporte para arquitecturas x86 y x64 disponible',
                'details': architectures
            })
        
        # Análisis de ejemplos
        examples = self.analysis_results.get('source_analysis', {}).get('usage_examples', [])
        if examples:
            recommendations.append({
                'type': 'usage_examples',
                'priority': 'medium',
                'description': f'Utilizar {len(examples)} ejemplos de uso encontrados como referencia',
                'examples_count': len(examples)
            })
        
        # Recomendaciones de implementación
        recommendations.extend([
            {
                'type': 'implementation_strategy',
                'priority': 'high',
                'description': 'Implementar protocolo TCP/IP nativo basado en funciones CP5200',
                'approach': 'Direct socket communication using extracted function signatures'
            },
            {
                'type': 'testing_strategy',
                'priority': 'high',
                'description': 'Crear pruebas unitarias basadas en ejemplos de código encontrados',
                'approach': 'Use extracted function calls as test cases'
            },
            {
                'type': 'documentation_strategy',
                'priority': 'medium',
                'description': 'Documentar implementación basándose en PDFs de protocolo',
                'approach': 'Reference protocol PDFs for detailed specifications'
            }
        ])
        
        self.analysis_results['recommendations'] = recommendations
        print(f"✅ Generadas {len(recommendations)} recomendaciones")
    
    def generate_implementation_plan(self) -> Dict[str, Any]:
        """Genera plan de implementación basado en el análisis"""
        print("📋 Generando plan de implementación...")
        
        functions = self.analysis_results.get('source_analysis', {}).get('functions_extracted', [])
        cp5200_functions = [f for f in functions if f['dll'].lower() == 'cp5200.dll']
        
        # Categorizar funciones por tipo
        function_categories = {
            'connection': [],
            'text': [],
            'image': [],
            'clock': [],
            'control': [],
            'status': []
        }
        
        for func in cp5200_functions:
            name = func['name'].lower()
            if 'init' in name or 'connect' in name or 'close' in name:
                function_categories['connection'].append(func)
            elif 'text' in name:
                function_categories['text'].append(func)
            elif 'picture' in name or 'image' in name:
                function_categories['image'].append(func)
            elif 'clock' in name or 'time' in name:
                function_categories['clock'].append(func)
            elif 'restart' in name or 'clear' in name or 'program' in name:
                function_categories['control'].append(func)
            elif 'status' in name or 'get' in name:
                function_categories['status'].append(func)
        
        implementation_plan = {
            'phase_1': {
                'name': 'Funciones de Conexión',
                'functions': function_categories['connection'],
                'priority': 'high',
                'estimated_effort': '2-3 días'
            },
            'phase_2': {
                'name': 'Envío de Texto',
                'functions': function_categories['text'],
                'priority': 'high',
                'estimated_effort': '3-4 días'
            },
            'phase_3': {
                'name': 'Envío de Imágenes',
                'functions': function_categories['image'],
                'priority': 'medium',
                'estimated_effort': '4-5 días'
            },
            'phase_4': {
                'name': 'Configuración de Reloj',
                'functions': function_categories['clock'],
                'priority': 'medium',
                'estimated_effort': '2-3 días'
            },
            'phase_5': {
                'name': 'Comandos de Control',
                'functions': function_categories['control'],
                'priority': 'low',
                'estimated_effort': '2-3 días'
            },
            'phase_6': {
                'name': 'Monitoreo de Estado',
                'functions': function_categories['status'],
                'priority': 'low',
                'estimated_effort': '1-2 días'
            }
        }
        
        return implementation_plan
    
    def save_analysis_report(self, output_file: str = "sdk_analysis_report.json"):
        """Guarda el reporte de análisis en archivo JSON"""
        report = {
            'analysis_results': self.analysis_results,
            'implementation_plan': self.generate_implementation_plan(),
            'summary': {
                'total_functions_found': len(self.analysis_results.get('source_analysis', {}).get('functions_extracted', [])),
                'cp5200_functions': len([f for f in self.analysis_results.get('source_analysis', {}).get('functions_extracted', []) if f['dll'].lower() == 'cp5200.dll']),
                'total_examples': len(self.analysis_results.get('source_analysis', {}).get('usage_examples', [])),
                'total_pdfs': len(self.analysis_results.get('pdf_analysis', {}).get('pdf_files', [])),
                'recommendations_count': len(self.analysis_results.get('recommendations', []))
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Reporte guardado en: {output_file}")
        return output_file
    
    def print_summary(self):
        """Imprime resumen del análisis"""
        print("\n" + "="*80)
        print("📊 RESUMEN DEL ANÁLISIS SDK - PANELES ROTULOSELECTRONICOS.NET")
        print("="*80)
        
        # Estadísticas generales
        summary = self.analysis_results.get('summary', {})
        print(f"📁 Archivos analizados: {len(self.analysis_results.get('directory_structure', {}).get('files', []))}")
        print(f"🔧 Funciones encontradas: {summary.get('total_functions_found', 0)}")
        print(f"🎯 Funciones CP5200: {summary.get('cp5200_functions', 0)}")
        print(f"📝 Ejemplos de uso: {summary.get('total_examples', 0)}")
        print(f"📄 Documentos PDF: {summary.get('total_pdfs', 0)}")
        
        # Funciones CP5200 encontradas
        functions = self.analysis_results.get('source_analysis', {}).get('functions_extracted', [])
        cp5200_functions = [f for f in functions if f['dll'].lower() == 'cp5200.dll']
        
        if cp5200_functions:
            print(f"\n🎯 FUNCIONES CP5200 IDENTIFICADAS:")
            for func in cp5200_functions:
                print(f"  • {func['name']} -> {func['return_type']}")
        
        # Recomendaciones principales
        recommendations = self.analysis_results.get('recommendations', [])
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        
        if high_priority:
            print(f"\n🔥 RECOMENDACIONES DE ALTA PRIORIDAD:")
            for rec in high_priority:
                print(f"  • {rec['description']}")
        
        # Plan de implementación
        plan = self.generate_implementation_plan()
        print(f"\n📋 PLAN DE IMPLEMENTACIÓN:")
        for phase_key, phase_info in plan.items():
            print(f"  {phase_key.upper()}: {phase_info['name']} ({phase_info['estimated_effort']})")
        
        print("\n" + "="*80)

def main():
    """Función principal del script"""
    print("🚀 Iniciando Análisis Técnico de Documentación SDK")
    print("="*80)
    
    # Crear analizador
    analyzer = SDKDocumentationAnalyzer()
    
    # Realizar análisis
    results = analyzer.analyze_documentation()
    
    # Guardar reporte
    report_file = analyzer.save_analysis_report()
    
    # Imprimir resumen
    analyzer.print_summary()
    
    print(f"\n✅ Análisis completado. Reporte guardado en: {report_file}")
    print("📋 Próximos pasos:")
    print("  1. Revisar reporte detallado")
    print("  2. Implementar funciones de conexión (Fase 1)")
    print("  3. Desarrollar protocolo TCP/IP nativo")
    print("  4. Crear pruebas basadas en ejemplos encontrados")

if __name__ == "__main__":
    main() 