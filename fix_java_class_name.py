#!/usr/bin/env python3
"""
Script para corregir el problema del nombre de clase Java en panel_controller.py
"""

import os
import re

def fix_java_class_name():
    """Corregir el problema del nombre de clase Java"""
    
    # Ruta del archivo a corregir
    file_path = "/opt/panelSender/sender_newProtocol/panel_controller.py"
    
    # Leer el archivo
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Buscar la línea problemática
    pattern = r'script_file = f"SendText_\{int\(time\.time\(\)\)\}\.java"'
    replacement = '''script_file = f"SendText_{int(time.time())}.java"
            class_name = "SendText"'''
    
    # Reemplazar
    new_content = re.sub(pattern, replacement, content)
    
    # También corregir la línea donde se ejecuta la clase
    pattern2 = r"'SendText'"
    replacement2 = "class_name"
    
    new_content = re.sub(pattern2, replacement2, new_content)
    
    # Escribir el archivo corregido
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"Archivo {file_path} corregido exitosamente")
    print("Cambios realizados:")
    print("1. Agregada variable class_name = 'SendText'")
    print("2. Cambiado 'SendText' por class_name en la ejecución")

if __name__ == "__main__":
    fix_java_class_name() 