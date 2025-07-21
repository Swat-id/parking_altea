#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del frontend de programaciones
Específicamente prueba el combo de aparcamientos y la creación de programaciones
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://157.180.91.63:5789"
API_URL = f"{BASE_URL}/api"

def test_api_endpoints():
    """Probar todos los endpoints de la API necesarios para programaciones"""
    
    print("🌐 PRUEBA DE ENDPOINTS DE LA API")
    print("=" * 50)
    
    endpoints = [
        "/parkings",
        "/schedules",
        "/panels"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {endpoint}: {len(data)} elementos")
                elif isinstance(data, dict) and 'schedules' in data:
                    print(f"✅ {endpoint}: {len(data['schedules'])} programaciones")
                else:
                    print(f"✅ {endpoint}: Respuesta válida")
            else:
                print(f"❌ {endpoint}: Error {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    return True

def test_parkings_data():
    """Probar específicamente los datos de parkings"""
    
    print(f"\n🏢 PRUEBA DE DATOS DE PARKINGS")
    print("=" * 40)
    
    try:
        response = requests.get(f"{API_URL}/parkings")
        if response.status_code == 200:
            parkings = response.json()
            print(f"✅ Parkings encontrados: {len(parkings)}")
            
            # Mostrar los primeros 5 parkings
            for i, parking in enumerate(parkings[:5]):
                print(f"  {i+1}. {parking['name']} (ID: {parking['id']}) - Estado: {parking['estado']}")
            
            # Verificar estructura de datos
            if parkings:
                required_fields = ['id', 'name', 'estado', 'total_plazas']
                sample_parking = parkings[0]
                missing_fields = [field for field in required_fields if field not in sample_parking]
                
                if missing_fields:
                    print(f"⚠️  Campos faltantes: {missing_fields}")
                else:
                    print("✅ Estructura de datos correcta")
            
            return parkings
        else:
            print(f"❌ Error obteniendo parkings: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error en test_parkings_data: {e}")
        return None

def test_schedules_data():
    """Probar específicamente los datos de programaciones"""
    
    print(f"\n📅 PRUEBA DE DATOS DE PROGRAMACIONES")
    print("=" * 45)
    
    try:
        response = requests.get(f"{API_URL}/schedules")
        if response.status_code == 200:
            data = response.json()
            schedules = data.get('schedules', [])
            print(f"✅ Programaciones encontradas: {len(schedules)}")
            
            # Mostrar las primeras 3 programaciones
            for i, schedule in enumerate(schedules[:3]):
                print(f"  {i+1}. {schedule['name']} (ID: {schedule['id']}) - Activa: {schedule['is_active']}")
            
            return schedules
        else:
            print(f"❌ Error obteniendo programaciones: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error en test_schedules_data: {e}")
        return None

def test_create_schedule():
    """Probar la creación de una programación"""
    
    print(f"\n🧪 PRUEBA DE CREACIÓN DE PROGRAMACIÓN")
    print("=" * 45)
    
    # Obtener un parking para la prueba
    parkings = test_parkings_data()
    if not parkings:
        print("❌ No se pueden obtener parkings para la prueba")
        return False
    
    parking = parkings[0]  # Usar el primer parking
    
    # Crear datos de prueba
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    schedule_data = {
        "parking_id": parking['id'],
        "name": f"Prueba Frontend - {now.strftime('%H:%M:%S')}",
        "description": "Programación de prueba para verificar frontend",
        "start_date": tomorrow.strftime('%Y-%m-%d'),
        "end_date": (tomorrow + timedelta(days=7)).strftime('%Y-%m-%d'),
        "start_time": "10:00",
        "end_time": "18:00",
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
        "saturday": False,
        "sunday": False,
        "message": "PRUEBA FRONTEND",
        "color": 2,
        "font_size": 16,
        "effect": "static",
        "is_active": True,
        "priority": 1
    }
    
    try:
        response = requests.post(
            f"{API_URL}/schedules",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(schedule_data)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Programación creada exitosamente: {result.get('schedule_id')}")
                return True
            else:
                print(f"❌ Error creando programación: {result.get('error')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test_create_schedule: {e}")
        return False

def test_frontend_accessibility():
    """Probar la accesibilidad del frontend"""
    
    print(f"\n🌐 PRUEBA DE ACCESIBILIDAD DEL FRONTEND")
    print("=" * 45)
    
    try:
        # Probar acceso al frontend principal
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Frontend principal accesible")
            
            # Verificar que contiene elementos del frontend
            content = response.text.lower()
            if 'parking' in content and 'html' in content:
                print("✅ Contenido del frontend correcto")
            else:
                print("⚠️  Contenido del frontend inesperado")
        else:
            print(f"❌ Frontend no accesible: {response.status_code}")
            return False
        
        # Probar acceso a assets
        response = requests.get(f"{BASE_URL}/assets/")
        if response.status_code == 200:
            print("✅ Assets del frontend accesibles")
        else:
            print(f"⚠️  Assets no accesibles: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test_frontend_accessibility: {e}")
        return False

def test_schedule_form_data():
    """Probar que los datos necesarios para el formulario estén disponibles"""
    
    print(f"\n📝 PRUEBA DE DATOS PARA FORMULARIO")
    print("=" * 40)
    
    # Verificar que tenemos parkings
    parkings = test_parkings_data()
    if not parkings:
        print("❌ No hay parkings disponibles para el formulario")
        return False
    
    # Verificar que tenemos paneles
    try:
        response = requests.get(f"{API_URL}/panels")
        if response.status_code == 200:
            panels = response.json()
            print(f"✅ Paneles disponibles: {len(panels)}")
            
            # Verificar paneles por parking
            parking_panels = {}
            for panel in panels:
                parking_id = panel.get('parking_id')
                if parking_id not in parking_panels:
                    parking_panels[parking_id] = []
                parking_panels[parking_id].append(panel)
            
            print(f"✅ Parkings con paneles: {len(parking_panels)}")
            
            # Mostrar algunos ejemplos
            for parking_id, panels_list in list(parking_panels.items())[:3]:
                parking_name = next((p['name'] for p in parkings if p['id'] == parking_id), 'Desconocido')
                print(f"  - {parking_name}: {len(panels_list)} paneles")
            
        else:
            print(f"❌ Error obteniendo paneles: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test_schedule_form_data: {e}")
        return False
    
    return True

def main():
    """Función principal de pruebas"""
    
    print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN DEL FRONTEND DE PROGRAMACIONES")
    print("=" * 70)
    
    tests = [
        ("Endpoints de API", test_api_endpoints),
        ("Datos de Parkings", test_parkings_data),
        ("Datos de Programaciones", test_schedules_data),
        ("Accesibilidad Frontend", test_frontend_accessibility),
        ("Datos para Formulario", test_schedule_form_data),
        ("Creación de Programación", test_create_schedule)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print(f"\n{'='*70}")
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 TODAS LAS PRUEBAS PASARON - SISTEMA FUNCIONAL")
    else:
        print("⚠️  ALGUNAS PRUEBAS FALLARON - REVISAR PROBLEMAS")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 