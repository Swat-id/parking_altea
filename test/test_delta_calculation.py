#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del cálculo de deltas
"""

import sys
import os

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def detect_camera_reset(previous_in, previous_out, new_in, new_out):
    """
    Detectar si la cámara se ha reiniciado basándose en los contadores.
    
    Args:
        previous_in: Contador anterior de vehículos entrando
        previous_out: Contador anterior de vehículos saliendo
        new_in: Nuevo contador de vehículos entrando
        new_out: Nuevo contador de vehículos saliendo
    
    Returns:
        tuple: (is_reset, adjusted_previous_in, adjusted_previous_out)
    """
    # Si es la primera vez (contadores anteriores son None), no es reinicio
    if previous_in is None or previous_out is None:
        return False, 0, 0
    
    # Detectar reinicio: nuevos contadores son menores que los anteriores
    # Esto incluye cuando uno o ambos contadores van a 0
    is_reset = (new_in < previous_in) or (new_out < previous_out)
    
    if is_reset:
        print(f"CAMERA RESET DETECTED - Previous: In={previous_in}, Out={previous_out} -> New: In={new_in}, Out={new_out}")
        
        # En caso de reinicio, ajustar los contadores anteriores
        # CORRECCIÓN: Si hay reinicio, siempre usar 0 como contador anterior
        # para calcular correctamente el delta desde el nuevo valor
        adjusted_previous_in = 0
        adjusted_previous_out = 0
        
        print(f"Reset adjustment - Adjusted previous: In={adjusted_previous_in}, Out={adjusted_previous_out}")
        return True, adjusted_previous_in, adjusted_previous_out
    
    return False, previous_in, previous_out

def calculate_deltas_with_reset_handling(previous_in, previous_out, new_in, new_out):
    """
    Calcular deltas considerando posibles reinicios de cámara.
    
    Args:
        previous_in: Contador anterior de vehículos entrando
        previous_out: Contador anterior de vehículos saliendo
        new_in: Nuevo contador de vehículos entrando
        new_out: Nuevo contador de vehículos saliendo
    
    Returns:
        tuple: (delta_in, delta_out, is_reset, reset_info)
    """
    # Detectar si hay reinicio
    is_reset, adjusted_previous_in, adjusted_previous_out = detect_camera_reset(
        previous_in, previous_out, new_in, new_out
    )
    
    # Calcular deltas usando los contadores ajustados
    delta_in = new_in - adjusted_previous_in
    delta_out = new_out - adjusted_previous_out
    
    # Validar que los deltas sean positivos (excepto en reinicios)
    if not is_reset:
        if delta_in < 0:
            print(f"Negative delta_in detected (non-reset): {delta_in}. Setting to 0.")
            delta_in = 0
        if delta_out < 0:
            print(f"Negative delta_out detected (non-reset): {delta_out}. Setting to 0.")
            delta_out = 0
    
    reset_info = {
        "is_reset": is_reset,
        "previous_in": previous_in,
        "previous_out": previous_out,
        "adjusted_previous_in": adjusted_previous_in,
        "adjusted_previous_out": adjusted_previous_out,
        "new_in": new_in,
        "new_out": new_out
    }
    
    print(f"Deltas calculated - Delta In: {delta_in}, Delta Out: {delta_out}, Reset: {is_reset}")
    
    return delta_in, delta_out, is_reset, reset_info

def test_normal_increment():
    """Probar incremento normal (sin reinicio)"""
    print("\n" + "="*50)
    print("TEST: Incremento normal")
    print("="*50)
    
    # Caso del ejemplo: 408 -> 409
    previous_in = 408
    previous_out = 55
    new_in = 409
    new_out = 55
    
    print(f"Previous: In={previous_in}, Out={previous_out}")
    print(f"New: In={new_in}, Out={new_out}")
    
    delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
        previous_in, previous_out, new_in, new_out
    )
    
    print(f"Result: Delta In={delta_in}, Delta Out={delta_out}, Is Reset={is_reset}")
    print(f"Expected: Delta In=1, Delta Out=0, Is Reset=False")
    
    # Verificar que el resultado es correcto
    assert delta_in == 1, f"Expected delta_in=1, got {delta_in}"
    assert delta_out == 0, f"Expected delta_out=0, got {delta_out}"
    assert is_reset == False, f"Expected is_reset=False, got {is_reset}"
    
    print("✅ Test passed!")

def test_camera_reset():
    """Probar reinicio de cámara"""
    print("\n" + "="*50)
    print("TEST: Reinicio de cámara")
    print("="*50)
    
    # Caso de reinicio: 1000 -> 5
    previous_in = 1000
    previous_out = 500
    new_in = 5
    new_out = 2
    
    print(f"Previous: In={previous_in}, Out={previous_out}")
    print(f"New: In={new_in}, Out={new_out}")
    
    delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
        previous_in, previous_out, new_in, new_out
    )
    
    print(f"Result: Delta In={delta_in}, Delta Out={delta_out}, Is Reset={is_reset}")
    print(f"Expected: Delta In=5, Delta Out=2, Is Reset=True")
    
    # Verificar que el resultado es correcto
    assert delta_in == 5, f"Expected delta_in=5, got {delta_in}"
    assert delta_out == 2, f"Expected delta_out=2, got {delta_out}"
    assert is_reset == True, f"Expected is_reset=True, got {is_reset}"
    
    print("✅ Test passed!")

def test_first_time():
    """Probar primera vez (contadores None)"""
    print("\n" + "="*50)
    print("TEST: Primera vez (contadores None)")
    print("="*50)
    
    # Caso primera vez
    previous_in = None
    previous_out = None
    new_in = 10
    new_out = 5
    
    print(f"Previous: In={previous_in}, Out={previous_out}")
    print(f"New: In={new_in}, Out={new_out}")
    
    delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
        previous_in, previous_out, new_in, new_out
    )
    
    print(f"Result: Delta In={delta_in}, Delta Out={delta_out}, Is Reset={is_reset}")
    print(f"Expected: Delta In=10, Delta Out=5, Is Reset=False")
    
    # Verificar que el resultado es correcto
    assert delta_in == 10, f"Expected delta_in=10, got {delta_in}"
    assert delta_out == 5, f"Expected delta_out=5, got {delta_out}"
    assert is_reset == False, f"Expected is_reset=False, got {is_reset}"
    
    print("✅ Test passed!")

def test_negative_delta():
    """Probar delta negativo (error de contador)"""
    print("\n" + "="*50)
    print("TEST: Delta negativo (error de contador)")
    print("="*50)
    
    # Caso de error: 100 -> 95 (debería ser 0)
    previous_in = 100
    previous_out = 50
    new_in = 95
    new_out = 45
    
    print(f"Previous: In={previous_in}, Out={previous_out}")
    print(f"New: In={new_in}, Out={new_out}")
    
    delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
        previous_in, previous_out, new_in, new_out
    )
    
    print(f"Result: Delta In={delta_in}, Delta Out={delta_out}, Is Reset={is_reset}")
    print(f"Expected: Delta In=0, Delta Out=0, Is Reset=False")
    
    # Verificar que el resultado es correcto
    assert delta_in == 0, f"Expected delta_in=0, got {delta_in}"
    assert delta_out == 0, f"Expected delta_out=0, got {delta_out}"
    assert is_reset == False, f"Expected is_reset=False, got {is_reset}"
    
    print("✅ Test passed!")

def test_multiple_scenarios():
    """Probar múltiples escenarios"""
    print("\n" + "="*50)
    print("TEST: Múltiples escenarios")
    print("="*50)
    
    test_cases = [
        # (previous_in, previous_out, new_in, new_out, expected_delta_in, expected_delta_out, expected_reset)
        (100, 50, 101, 50, 1, 0, False),      # Incremento normal
        (100, 50, 100, 51, 0, 1, False),      # Solo salida
        (100, 50, 99, 50, 0, 0, False),       # Decremento (error)
        (100, 50, 0, 0, 0, 0, True),          # Reinicio a 0
        (100, 50, 5, 2, 5, 2, True),          # Reinicio a valores bajos
        (None, None, 10, 5, 10, 5, False),    # Primera vez
    ]
    
    for i, (prev_in, prev_out, new_in, new_out, exp_delta_in, exp_delta_out, exp_reset) in enumerate(test_cases):
        print(f"\nTest case {i+1}:")
        print(f"  Previous: In={prev_in}, Out={prev_out}")
        print(f"  New: In={new_in}, Out={new_out}")
        
        delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
            prev_in, prev_out, new_in, new_out
        )
        
        print(f"  Result: Delta In={delta_in}, Delta Out={delta_out}, Is Reset={is_reset}")
        print(f"  Expected: Delta In={exp_delta_in}, Delta Out={exp_delta_out}, Is Reset={exp_reset}")
        
        # Verificar resultado
        assert delta_in == exp_delta_in, f"Case {i+1}: Expected delta_in={exp_delta_in}, got {delta_in}"
        assert delta_out == exp_delta_out, f"Case {i+1}: Expected delta_out={exp_delta_out}, got {delta_out}"
        assert is_reset == exp_reset, f"Case {i+1}: Expected is_reset={exp_reset}, got {is_reset}"
        
        print(f"  ✅ Test case {i+1} passed!")
    
    print("\n✅ All test cases passed!")

if __name__ == "__main__":
    print("Testing Delta Calculation Logic")
    print("="*50)
    
    try:
        test_normal_increment()
        test_camera_reset()
        test_first_time()
        test_negative_delta()
        test_multiple_scenarios()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("The delta calculation logic is working correctly.")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 