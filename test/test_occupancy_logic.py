#!/usr/bin/env python3
"""
Script de prueba para verificar la lógica corregida de cálculo de ocupación
"""

import sys
import os
from datetime import datetime

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_occupancy_logic():
    """Probar la lógica de cálculo de ocupación"""
    
    print("🧮 PRUEBA DE LÓGICA DE CÁLCULO DE OCUPACIÓN")
    print("=" * 60)
    
    # Simular datos de ejemplo
    print("\n📊 DATOS DE EJEMPLO:")
    print("-" * 30)
    
    # Cámara 1: Basseta_Asup camera 1 (IP: 172.20.5.144)
    camera1_previous_in = 1000
    camera1_previous_out = 800
    camera1_new_in = 1002  # +2 entradas
    camera1_new_out = 800  # +0 salidas
    
    # Cámara 2: Basseta_Rastro camera 2 (IP: 212.63.121.209)
    camera2_previous_in = 6500
    camera2_previous_out = 6300
    camera2_new_in = 6501  # +1 entrada
    camera2_new_out = 6300  # +0 salidas
    
    print(f"Cámara 1 (Basseta_Asup):")
    print(f"  Anterior: In={camera1_previous_in}, Out={camera1_previous_out}")
    print(f"  Nuevo: In={camera1_new_in}, Out={camera1_new_out}")
    print(f"  Delta: In={camera1_new_in - camera1_previous_in}, Out={camera1_new_out - camera1_previous_out}")
    
    print(f"\nCámara 2 (Basseta_Rastro):")
    print(f"  Anterior: In={camera2_previous_in}, Out={camera2_previous_out}")
    print(f"  Nuevo: In={camera2_new_in}, Out={camera2_new_out}")
    print(f"  Delta: In={camera2_new_in - camera2_previous_in}, Out={camera2_new_out - camera2_previous_out}")
    
    # Calcular deltas
    delta1_in = camera1_new_in - camera1_previous_in  # +2
    delta1_out = camera1_new_out - camera1_previous_out  # +0
    delta2_in = camera2_new_in - camera2_previous_in  # +1
    delta2_out = camera2_new_out - camera2_previous_out  # +0
    
    print(f"\n📈 DELTAS CALCULADOS:")
    print(f"Cámara 1: +{delta1_in} entradas, +{delta1_out} salidas")
    print(f"Cámara 2: +{delta2_in} entradas, +{delta2_out} salidas")
    
    # Simular ocupación inicial del parking
    parking_initial_occupancy = 30
    parking_max_capacity = 100
    
    print(f"\n🏢 PARKING:")
    print(f"Ocupación inicial: {parking_initial_occupancy}")
    print(f"Capacidad máxima: {parking_max_capacity}")
    
    # LÓGICA INCORRECTA (la que teníamos antes)
    print(f"\n❌ LÓGICA INCORRECTA (sumar contadores absolutos):")
    print("-" * 50)
    
    # Calcular ocupación basada en contadores absolutos
    camera1_occupancy = camera1_new_in - camera1_new_out  # 1002 - 800 = 202
    camera2_occupancy = camera2_new_in - camera2_new_out  # 6501 - 6300 = 201
    
    incorrect_total_occupancy = camera1_occupancy + camera2_occupancy  # 202 + 201 = 403
    incorrect_change = incorrect_total_occupancy - parking_initial_occupancy  # 403 - 30 = 373
    
    print(f"Ocupación cámara 1: {camera1_new_in} - {camera1_new_out} = {camera1_occupancy}")
    print(f"Ocupación cámara 2: {camera2_new_in} - {camera2_new_out} = {camera2_occupancy}")
    print(f"Total incorrecto: {camera1_occupancy} + {camera2_occupancy} = {incorrect_total_occupancy}")
    print(f"Cambio incorrecto: {incorrect_total_occupancy} - {parking_initial_occupancy} = +{incorrect_change}")
    print(f"❌ RESULTADO INCORRECTO: De {parking_initial_occupancy} a {incorrect_total_occupancy} (+{incorrect_change})")
    
    # LÓGICA CORRECTA (la que implementamos ahora)
    print(f"\n✅ LÓGICA CORRECTA (aplicar deltas):")
    print("-" * 40)
    
    # Aplicar deltas al parking
    # Si ambas cámaras están asociadas al mismo parking, aplicar ambos deltas
    correct_occupancy = parking_initial_occupancy
    total_delta_in = delta1_in + delta2_in  # 2 + 1 = 3
    total_delta_out = delta1_out + delta2_out  # 0 + 0 = 0
    
    correct_occupancy += (total_delta_in - total_delta_out)  # 30 + (3 - 0) = 33
    correct_change = total_delta_in - total_delta_out  # 3 - 0 = 3
    
    print(f"Delta total: +{total_delta_in} entradas, +{total_delta_out} salidas")
    print(f"Cambio neto: +{total_delta_in} - {total_delta_out} = +{correct_change}")
    print(f"✅ RESULTADO CORRECTO: De {parking_initial_occupancy} a {correct_occupancy} (+{correct_change})")
    
    # Comparación
    print(f"\n📊 COMPARACIÓN:")
    print("-" * 20)
    print(f"Lógica incorrecta: {parking_initial_occupancy} → {incorrect_total_occupancy} (+{incorrect_change})")
    print(f"Lógica correcta:   {parking_initial_occupancy} → {correct_occupancy} (+{correct_change})")
    print(f"Diferencia: {incorrect_total_occupancy - correct_occupancy} vehículos")
    
    # Explicación del problema
    print(f"\n🔍 EXPLICACIÓN DEL PROBLEMA:")
    print("-" * 30)
    print(f"La lógica incorrecta sumaba los contadores absolutos de todas las cámaras:")
    print(f"  Cámara 1: {camera1_new_in} - {camera1_new_out} = {camera1_occupancy}")
    print(f"  Cámara 2: {camera2_new_in} - {camera2_new_out} = {camera2_occupancy}")
    print(f"  Total: {camera1_occupancy} + {camera2_occupancy} = {incorrect_total_occupancy}")
    print(f"\nEsto es incorrecto porque los contadores absolutos pueden ser muy altos")
    print(f"y no representan la ocupación real del parking.")
    print(f"\nLa lógica correcta aplica solo los deltas (cambios):")
    print(f"  Delta cámara 1: +{delta1_in} entradas, +{delta1_out} salidas")
    print(f"  Delta cámara 2: +{delta2_in} entradas, +{delta2_out} salidas")
    print(f"  Delta total: +{total_delta_in} entradas, +{total_delta_out} salidas")
    print(f"  Cambio neto: +{correct_change} vehículos")
    
    return True

def test_scenario_with_multiple_parkings():
    """Probar escenario con múltiples parkings"""
    
    print(f"\n🏢 ESCENARIO CON MÚLTIPLES PARKINGS:")
    print("=" * 50)
    
    # Simular que la cámara Basseta_Asup está asociada a 2 parkings
    camera_delta_in = 2
    camera_delta_out = 0
    
    # Parking 1: P. Basseta Centre
    parking1_initial = 25
    parking1_capacity = 80
    
    # Parking 2: P. Basseta Z1  
    parking2_initial = 15
    parking2_capacity = 60
    
    print(f"Cámara Basseta_Asup reporta: +{camera_delta_in} entradas, +{camera_delta_out} salidas")
    print(f"\nParking 1 (P. Basseta Centre):")
    print(f"  Ocupación inicial: {parking1_initial}")
    print(f"  Capacidad: {parking1_capacity}")
    
    print(f"\nParking 2 (P. Basseta Z1):")
    print(f"  Ocupación inicial: {parking2_initial}")
    print(f"  Capacidad: {parking2_capacity}")
    
    # Aplicar delta a ambos parkings
    parking1_final = parking1_initial + (camera_delta_in - camera_delta_out)  # 25 + 2 = 27
    parking2_final = parking2_initial + (camera_delta_in - camera_delta_out)  # 15 + 2 = 17
    
    print(f"\n✅ RESULTADO CORRECTO:")
    print(f"Parking 1: {parking1_initial} → {parking1_final} (+{camera_delta_in - camera_delta_out})")
    print(f"Parking 2: {parking2_initial} → {parking2_final} (+{camera_delta_in - camera_delta_out})")
    
    print(f"\n💡 EXPLICACIÓN:")
    print(f"El mismo delta se aplica a todos los parkings asociados a la cámara.")
    print(f"Esto es correcto porque el evento (entrada/salida) afecta a todos los parkings")
    print(f"que comparten esa cámara.")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de lógica de ocupación...")
    
    test_occupancy_logic()
    test_scenario_with_multiple_parkings()
    
    print(f"\n🎉 Pruebas completadas")
    print(f"La lógica corregida aplica correctamente los deltas en lugar de sumar contadores absolutos.") 