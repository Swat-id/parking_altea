#!/usr/bin/env python3
"""
Script de migración para Camera Server v3.4.0
Realiza backup del camera_server.py actual y lo reemplaza con la nueva versión
"""

import os
import shutil
import sys
from datetime import datetime

def main():
    """Función principal de migración"""
    print("=== Migración Camera Server v3.4.0 ===")
    
    # Rutas de archivos
    current_file = "src/camera_server.py"
    new_file = "src/camera_server_v3_4_0.py"
    backup_file = f"src/camera_server_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    # Verificar que existe el archivo actual
    if not os.path.exists(current_file):
        print(f"❌ Error: {current_file} no existe")
        return False
    
    # Verificar que existe el nuevo archivo
    if not os.path.exists(new_file):
        print(f"❌ Error: {new_file} no existe")
        return False
    
    try:
        # 1. Crear backup del archivo actual
        print(f"📦 Creando backup: {backup_file}")
        shutil.copy2(current_file, backup_file)
        print(f"✅ Backup creado exitosamente")
        
        # 2. Reemplazar con la nueva versión
        print(f"🔄 Reemplazando {current_file} con {new_file}")
        shutil.copy2(new_file, current_file)
        print(f"✅ Archivo reemplazado exitosamente")
        
        # 3. Verificar que el reemplazo fue exitoso
        if os.path.exists(current_file):
            file_size = os.path.getsize(current_file)
            print(f"✅ Verificación: {current_file} existe ({file_size} bytes)")
        
        print("\n🎉 Migración completada exitosamente!")
        print(f"📦 Backup disponible en: {backup_file}")
        print(f"🔄 Camera Server actualizado a v3.4.0")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        
        # Intentar restaurar backup si existe
        if os.path.exists(backup_file):
            try:
                print(f"🔄 Restaurando backup...")
                shutil.copy2(backup_file, current_file)
                print(f"✅ Backup restaurado")
            except Exception as restore_error:
                print(f"❌ Error restaurando backup: {restore_error}")
        
        return False

def show_differences():
    """Mostrar diferencias principales entre versiones"""
    print("\n📋 PRINCIPALES CAMBIOS EN v3.4.0:")
    print("✅ Integración completa con CameraMessageProcessor")
    print("✅ Procesamiento 100% concurrente (10 workers)")
    print("✅ Eliminación del código de actualización de paneles")
    print("✅ Respuestas inmediatas <200ms")
    print("✅ Nuevos endpoints: /camera/stats, /camera/health, /camera/version")
    print("✅ Compatibilidad hacia atrás mantenida")
    print("✅ Logging optimizado y estructurado")
    print("✅ Manejo robusto de errores y timeouts")

if __name__ == "__main__":
    print("Camera Server Migration Tool v3.4.0")
    print("====================================")
    
    # Mostrar diferencias
    show_differences()
    
    # Confirmar migración
    response = input("\n¿Proceder con la migración? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'sí', 'si']:
        success = main()
        sys.exit(0 if success else 1)
    else:
        print("Migración cancelada por el usuario")
        sys.exit(0)
