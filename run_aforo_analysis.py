#!/usr/bin/env python3
"""
Script temporal para ejecutar el análisis de aforo
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importar y ejecutar el script de análisis
import fix_aforo_calculation
fix_aforo_calculation.main() 