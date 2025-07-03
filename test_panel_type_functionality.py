#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del selector de tipo de panel
"""

import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"

def test_panel_types_endpoint():
    """Probar el endpoint de tipos de panel"""
    print("🔍 Probando endpoint /panel-types...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/panel-types", timeout=10)
        
        if response.status_code == 200:
            panel_types = response.json()
            print(f"✅ GET /panel-types - {len(panel_types)} tipos de panel encontrados")
            
            for pt in panel_types:
                print(f"  - {pt['manufacturer']} - {pt['name']} ({pt['protocol']})")
            
            return panel_types
        else:
            print(f"❌ GET /panel-types - Error {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando a /panel-types: {e}")
        return None

def test_panels_with_types():
    """Probar el endpoint de paneles con información de tipos"""
    print("\n🔍 Probando endpoint /panels con tipos...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        
        if response.status_code == 200:
            panels = response.json()
            print(f"✅ GET /panels - {len(panels)} paneles encontrados")
            
            panels_with_types = [p for p in panels if p.get('panel_type')]
            print(f"  - Paneles con tipo asignado: {len(panels_with_types)}")
            
            for panel in panels:
                panel_type = panel.get('panel_type')
                if panel_type:
                    print(f"  - Panel {panel['name']}: {panel_type['manufacturer']} - {panel_type['name']} ({panel_type['protocol']})")
                else:
                    print(f"  - Panel {panel['name']}: Sin tipo asignado")
            
            return panels
        else:
            print(f"❌ GET /panels - Error {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando a /panels: {e}")
        return None

def test_update_panel_type():
    """Probar la actualización del tipo de panel"""
    print("\n🔍 Probando actualización de tipo de panel...")
    
    # Primero obtener paneles y tipos
    panels = test_panels_with_types()
    panel_types = test_panel_types_endpoint()
    
    if not panels or not panel_types:
        print("❌ No se pueden obtener paneles o tipos de panel")
        return False
    
    # Buscar un panel sin tipo asignado o con tipo diferente
    panel_to_update = None
    new_type = None
    
    for panel in panels:
        if not panel.get('panel_type'):
            panel_to_update = panel
            new_type = panel_types[0]  # Usar el primer tipo disponible
            break
    
    if not panel_to_update:
        print("❌ No se encontró un panel sin tipo asignado para probar")
        return False
    
    print(f"🔄 Actualizando panel {panel_to_update['name']} al tipo {new_type['name']}...")
    
    try:
        response = requests.put(
            f"{API_BASE_URL}/panel/{panel_to_update['id']}/type",
            json={'panel_type_id': new_type['id']},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ PUT /panel/{panel_to_update['id']}/type - Actualización exitosa")
            print(f"  - Panel: {result['name']}")
            print(f"  - Nuevo tipo: {result['panel_type']['manufacturer']} - {result['panel_type']['name']}")
            return True
        else:
            print(f"❌ PUT /panel/{panel_to_update['id']}/type - Error {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando tipo de panel: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de funcionalidad de tipos de panel")
    print("=" * 60)
    
    # Probar endpoints
    test_panel_types_endpoint()
    test_panels_with_types()
    test_update_panel_type()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    main() 