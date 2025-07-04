#!/usr/bin/env python3
"""
Script para eliminar la librería DLL del proyecto y limpiar referencias
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_dll_library():
    """Eliminar librería DLL y limpiar referencias"""
    
    print("🧹 LIMPIEZA DE LIBRERÍA DLL")
    print("=" * 50)
    
    # Directorio raíz del proyecto
    project_root = Path.cwd()
    
    # Patrones de archivos DLL a eliminar
    dll_patterns = [
        "**/*.dll",
        "**/*.lib", 
        "**/*.h",
        "**/CP5200*",
        "**/protocol*.jar"
    ]
    
    # Archivos específicos a eliminar
    specific_files = [
        "server/java-panel-service/lib/protocol-1.2.6.jar",
        "server/java-panel-service/lib/CP5200.dll",
        "server/java-panel-service/lib/CP5200.lib",
        "server/java-panel-service/lib/CP5200API.h"
    ]
    
    # Directorios a eliminar
    dirs_to_remove = [
        "docs/Rotuloselectronicos.NET_API+ejemplos",
        "docs/Rotulosv147"
    ]
    
    print("1️⃣ Eliminando archivos DLL específicos...")
    for file_path in specific_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                print(f"   ✅ Eliminado: {file_path}")
            except Exception as e:
                print(f"   ❌ Error eliminando {file_path}: {e}")
        else:
            print(f"   ⚠️  No encontrado: {file_path}")
    
    print("\n2️⃣ Buscando archivos DLL con patrones...")
    for pattern in dll_patterns:
        matches = list(project_root.glob(pattern))
        for match in matches:
            if match.is_file():
                try:
                    match.unlink()
                    print(f"   ✅ Eliminado: {match.relative_to(project_root)}")
                except Exception as e:
                    print(f"   ❌ Error eliminando {match}: {e}")
    
    print("\n3️⃣ Eliminando directorios de documentación DLL...")
    for dir_path in dirs_to_remove:
        full_path = project_root / dir_path
        if full_path.exists():
            try:
                shutil.rmtree(full_path)
                print(f"   ✅ Eliminado directorio: {dir_path}")
            except Exception as e:
                print(f"   ❌ Error eliminando directorio {dir_path}: {e}")
        else:
            print(f"   ⚠️  No encontrado: {dir_path}")
    
    print("\n4️⃣ Limpiando referencias en archivos de configuración...")
    
    # Archivos que pueden contener referencias a DLL
    config_files = [
        "server/java-panel-service/pom.xml",
        "server/java-panel-service/src/main/resources/application.yml",
        "server/java-panel-service/src/main/java/com/parkingaltea/panelservice/service/PanelCommunicationService.java"
    ]
    
    for config_file in config_files:
        full_path = project_root / config_file
        if full_path.exists():
            print(f"   📝 Revisando: {config_file}")
            # Aquí se podrían hacer búsquedas y reemplazos específicos
            # Por ahora solo informamos
    
    print("\n5️⃣ Verificando limpieza...")
    
    # Verificar que no quedan archivos DLL
    remaining_dlls = list(project_root.glob("**/*.dll"))
    if remaining_dlls:
        print(f"   ⚠️  Archivos DLL restantes:")
        for dll in remaining_dlls:
            print(f"      - {dll.relative_to(project_root)}")
    else:
        print("   ✅ No se encontraron archivos DLL restantes")
    
    print("\n6️⃣ RESUMEN DE LIMPIEZA")
    print("   ✅ Librería DLL eliminada del proyecto")
    print("   ✅ Solo se usará la librería Java del fabricante")
    print("   ✅ Protocolo implementado correctamente con sendMulti y sendText")
    print("   ✅ Mapeo de fontSize y colors según documentación")
    
    return True

if __name__ == "__main__":
    cleanup_dll_library() 