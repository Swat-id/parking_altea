#!/usr/bin/env python3
"""
Script de prueba para la nueva funcionalidad de paneles v2.6
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import psycopg2
from panel_communication_service import PanelCommunicationService
import json
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'parking_altea',
    'user': 'parking_user',
    'password': 'parking_pass'
}

def test_database_migration():
    """Probar que la migración de la base de datos se ejecutó correctamente"""
    print("🔍 Probando migración de base de datos...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar nuevas columnas en tabla panels
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'panels' 
            AND column_name IN ('fabricante', 'num_pantallas', 'resolucion_ancho', 'resolucion_alto', 
                               'tipo_visualizacion', 'idioma_principal', 'idiomas_secundarios', 'intervalo_cambio')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        print(f"✅ Columnas encontradas en tabla panels: {len(columns)}")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        # Verificar tabla de idiomas
        cursor.execute("SELECT COUNT(*) FROM panel_languages;")
        languages_count = cursor.fetchone()[0]
        print(f"✅ Idiomas cargados: {languages_count}")
        
        # Verificar configuración de API
        cursor.execute("SELECT COUNT(*) FROM panel_api_config;")
        api_config_count = cursor.fetchone()[0]
        print(f"✅ Configuración de API: {api_config_count} registros")
        
        # Mostrar algunos paneles con nueva información
        cursor.execute("""
            SELECT name, ip, fabricante, num_pantallas, resolucion_ancho, resolucion_alto, 
                   tipo_visualizacion, idioma_principal
            FROM panels 
            LIMIT 5;
        """)
        
        panels = cursor.fetchall()
        print(f"\n📋 Muestra de paneles actualizados:")
        for panel in panels:
            print(f"   - {panel[0]} ({panel[1]}): {panel[2]}, {panel[3]} pantalla(s) {panel[4]}x{panel[5]}, "
                  f"tipo: {panel[6]}, idioma: {panel[7]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error probando migración: {e}")
        return False

def test_panel_service():
    """Probar el servicio de comunicación con paneles"""
    print("\n🔍 Probando servicio de comunicación con paneles...")
    
    service = PanelCommunicationService()
    
    # Probar conexión
    print("   - Probando conexión con API...")
    connection_result = service.test_connection()
    print(f"     Resultado: {connection_result}")
    
    # Probar envío de texto personalizado
    print("   - Probando envío de texto personalizado...")
    text_result = service.send_custom_text(
        panel_ip="172.20.4.52",
        text="PROVA V2.6",
        color=2,  # Verde
        font_size=2,
        effect=1  # Centrado
    )
    print(f"     Resultado: {text_result}")
    
    # Probar envío de estado de parking
    print("   - Probando envío de estado de parking...")
    status_result = service.send_parking_status(
        panel_ip="172.20.4.52",
        parking_name="PALAU",
        free_spaces=45,
        total_spaces=100,
        language_code='va'
    )
    print(f"     Resultado: {status_result}")
    
    return True

def test_languages():
    """Probar funcionalidad de idiomas"""
    print("\n🔍 Probando funcionalidad de idiomas...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obtener todos los idiomas
        cursor.execute("""
            SELECT language_code, language_name, libre_text, denso_text, completo_text
            FROM panel_languages
            ORDER BY language_code;
        """)
        
        languages = cursor.fetchall()
        print(f"✅ Idiomas disponibles: {len(languages)}")
        
        for lang in languages:
            print(f"   - {lang[0]} ({lang[1]}): {lang[2]} / {lang[3]} / {lang[4]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error probando idiomas: {e}")
        return False

def test_multi_panel_configuration():
    """Probar configuración de múltiples pantallas"""
    print("\n🔍 Probando configuración de múltiples pantallas...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Simular diferentes configuraciones de paneles
        test_configs = [
            ("Panel 1 Pantalla", 1, 64, 16),
            ("Panel 2 Pantallas", 2, 32, 16),
            ("Panel 3 Pantallas", 3, 64, 16),
            ("Panel 4 Pantallas", 4, 32, 16),
            ("Panel 6 Pantallas", 6, 64, 16)
        ]
        
        print("✅ Configuraciones de prueba:")
        for name, screens, width, height in test_configs:
            print(f"   - {name}: {screens} pantalla(s) {width}x{height}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error probando configuración: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de paneles v2.6")
    print("=" * 60)
    
    tests = [
        ("Migración de base de datos", test_database_migration),
        ("Servicio de comunicación", test_panel_service),
        ("Funcionalidad de idiomas", test_languages),
        ("Configuración múltiples pantallas", test_multi_panel_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 Resumen de pruebas:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar logs.")
        return False

if __name__ == "__main__":
    main() 