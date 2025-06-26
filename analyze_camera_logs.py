#!/usr/bin/env python3
"""
Script para analizar logs de cámaras y verificar cálculos de deltas
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
API_BASE_URL = "http://157.180.91.63:6001"
PARKING_ID = 3  # Parking Poble antic/Belles Arts

def analyze_camera_logs():
    """Analizar logs de cámaras para verificar cálculos"""
    print("🔍 Analizando logs de cámaras para verificar cálculos...")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Parking ID: {PARKING_ID}")
    print("=" * 80)
    
    try:
        # Obtener logs de cámaras
        response = requests.get(f"{API_BASE_URL}/camera/logs?parking_id={PARKING_ID}&limit=20")
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo logs: {response.status_code}")
            return
            
        data = response.json()
        logs = data.get('logs', [])
        
        print(f"📊 Total de logs obtenidos: {len(logs)}")
        print()
        
        # Analizar logs procesados
        processed_logs = [log for log in logs if log.get('status') == 'processed']
        print(f"📝 Logs procesados: {len(processed_logs)}")
        print()
        
        # Mostrar detalles de cada log procesado
        for i, log in enumerate(processed_logs):
            print(f"--- Log #{i+1} ---")
            print(f"Timestamp: {log.get('received_at')}")
            print(f"Cámara: {log.get('camera_name')} ({log.get('camera_ip')})")
            print(f"Contadores actuales: In={log.get('vehicle_in')}, Out={log.get('vehicle_out')}")
            print(f"Contadores anteriores: In={log.get('previous_vehicle_in')}, Out={log.get('previous_vehicle_out')}")
            print(f"Deltas calculados: In={log.get('delta_in')}, Out={log.get('delta_out')}")
            print(f"Cambio de ocupación: {log.get('occupancy_change')}")
            print(f"Nueva ocupación: {log.get('new_occupancy')}")
            
            # Verificar cálculos
            vehicle_in = log.get('vehicle_in', 0)
            vehicle_out = log.get('vehicle_out', 0)
            prev_in = log.get('previous_vehicle_in')
            prev_out = log.get('previous_vehicle_out')
            delta_in = log.get('delta_in', 0)
            delta_out = log.get('delta_out', 0)
            
            # Calcular deltas esperados
            expected_delta_in = vehicle_in - prev_in if prev_in is not None else 0
            expected_delta_out = vehicle_out - prev_out if prev_out is not None else 0
            
            print(f"Deltas esperados: In={expected_delta_in}, Out={expected_delta_out}")
            
            # Verificar si hay discrepancia
            if delta_in != expected_delta_in or delta_out != expected_delta_out:
                print("⚠️  DISCREPANCIA EN CÁLCULOS DETECTADA!")
                print(f"   Delta In - Calculado: {delta_in}, Esperado: {expected_delta_in}")
                print(f"   Delta Out - Calculado: {delta_out}, Esperado: {expected_delta_out}")
            
            # Verificar lógica de "Sin cambios"
            if delta_in == 0 and delta_out == 0:
                print("✅ Correcto: Sin cambios")
            elif delta_in > 0 and delta_out == 0:
                print("✅ Correcto: +{delta_in} entradas")
            elif delta_in == 0 and delta_out > 0:
                print("✅ Correcto: +{delta_out} salidas")
            elif delta_in > 0 and delta_out > 0:
                print("✅ Correcto: +{delta_in} entradas, +{delta_out} salidas")
            else:
                print("❓ Caso no esperado")
            
            print()
        
        # Análisis de patrones
        print("📈 ANÁLISIS DE PATRONES")
        print("=" * 40)
        
        delta_in_counts = {}
        delta_out_counts = {}
        
        for log in processed_logs:
            delta_in = log.get('delta_in', 0)
            delta_out = log.get('delta_out', 0)
            
            delta_in_counts[delta_in] = delta_in_counts.get(delta_in, 0) + 1
            delta_out_counts[delta_out] = delta_out_counts.get(delta_out, 0) + 1
        
        print("Distribución de deltas IN:")
        for delta, count in sorted(delta_in_counts.items()):
            print(f"  Delta IN = {delta}: {count} veces")
        
        print()
        print("Distribución de deltas OUT:")
        for delta, count in sorted(delta_out_counts.items()):
            print(f"  Delta OUT = {delta}: {count} veces")
        
        # Verificar casos problemáticos
        print()
        print("🔍 CASOS PROBLEMÁTICOS")
        print("=" * 30)
        
        problematic_logs = []
        for log in processed_logs:
            delta_in = log.get('delta_in', 0)
            delta_out = log.get('delta_out', 0)
            
            # Caso 1: Delta IN > 0 pero no se muestra como entrada
            if delta_in > 0 and delta_out == 0:
                problematic_logs.append({
                    'type': 'entrada_no_mostrada',
                    'log': log,
                    'description': f"Delta IN = {delta_in} pero debería mostrar entrada"
                })
            
            # Caso 2: Delta OUT > 0 pero no se muestra como salida
            elif delta_in == 0 and delta_out > 0:
                problematic_logs.append({
                    'type': 'salida_no_mostrada',
                    'log': log,
                    'description': f"Delta OUT = {delta_out} pero debería mostrar salida"
                })
        
        if problematic_logs:
            print(f"Se encontraron {len(problematic_logs)} casos problemáticos:")
            for case in problematic_logs:
                print(f"  - {case['description']}")
                print(f"    Timestamp: {case['log'].get('received_at')}")
                print(f"    Contadores: In={case['log'].get('vehicle_in')}, Out={case['log'].get('vehicle_out')}")
                print(f"    Deltas: In={case['log'].get('delta_in')}, Out={case['log'].get('delta_out')}")
                print()
        else:
            print("✅ No se encontraron casos problemáticos en los cálculos")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

def test_frontend_logic():
    """Probar la lógica del frontend con datos reales"""
    print("\n🧪 PROBANDO LÓGICA DEL FRONTEND")
    print("=" * 40)
    
    # Casos de prueba basados en los logs reales
    test_cases = [
        {'delta_in': 1, 'delta_out': 0, 'expected': 'entrada'},
        {'delta_in': 0, 'delta_out': 1, 'expected': 'salida'},
        {'delta_in': 0, 'delta_out': 0, 'expected': 'sin_cambios'},
        {'delta_in': 1, 'delta_out': 1, 'expected': 'ambos'},
        {'delta_in': 2, 'delta_out': 0, 'expected': 'entrada'},
    ]
    
    for i, case in enumerate(test_cases):
        delta_in = case['delta_in']
        delta_out = case['delta_out']
        expected = case['expected']
        
        print(f"Caso {i+1}: delta_in={delta_in}, delta_out={delta_out}")
        
        # Simular lógica del frontend
        changes = []
        if delta_in > 0:
            changes.append(f"+{delta_in} entradas")
        if delta_out > 0:
            changes.append(f"+{delta_out} salidas")
        if delta_in == 0 and delta_out == 0:
            changes.append("Sin cambios")
        
        result = ", ".join(changes) if changes else "Sin cambios"
        print(f"  Resultado: {result}")
        print(f"  Esperado: {expected}")
        print()

if __name__ == "__main__":
    analyze_camera_logs()
    test_frontend_logic() 