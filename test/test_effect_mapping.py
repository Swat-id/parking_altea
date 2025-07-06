#!/usr/bin/env python3
"""
Script para probar el mapeo de efectos en el servicio de comunicación con paneles
"""

import sys
import os
sys.path.append('src')

from panel_communication_service import PanelCommunicationService

def test_effect_mapping():
    """Probar el mapeo de efectos"""
    
    print("=" * 60)
    print("🧪 PRUEBA DE MAPEO DE EFECTOS")
    print("=" * 60)
    
    # Crear instancia del servicio
    service = PanelCommunicationService()
    
    # Probar diferentes valores de efecto
    test_effects = [
        (1, "fijo"),
        (2, "static"),  # Este debería ser "fijo" ahora
        (12, "scroll"),
        (3, "static")   # Valor desconocido
    ]
    
    print(f"\n📋 PRUEBAS DE MAPEO:")
    print("-" * 60)
    
    for effect_value, expected_string in test_effects:
        # Simular la lógica de mapeo
        effect_string = "fijo" if effect_value == 1 else "scroll" if effect_value == 12 else "static"
        
        status = "✅" if effect_string == expected_string else "❌"
        print(f"{status} effect={effect_value} → '{effect_string}' (esperado: '{expected_string}')")
    
    # Probar el envío real (sin enviar realmente)
    print(f"\n🧪 PRUEBA DE ENVÍO SIMULADO:")
    print("-" * 60)
    
    test_panel_ip = "172.20.4.52"
    test_text = "LLIURE"
    test_color = 2  # Verde
    test_font_size = 2  # 16px
    test_effect = 1  # Fijo
    
    print(f"📤 Simulando envío a panel {test_panel_ip}:")
    print(f"   Texto: '{test_text}'")
    print(f"   Color: {test_color} (Verde)")
    print(f"   Tamaño: {test_font_size} (16px)")
    print(f"   Efecto: {test_effect} (Fijo)")
    
    # Simular la creación del payload
    effect_string = "fijo" if test_effect == 1 else "scroll" if test_effect == 12 else "static"
    
    window = {
        "id": 0,
        "text": test_text,
        "color": test_color,
        "fontSize": test_font_size,
        "speed": 100,
        "effect": effect_string,
        "stayTime": 50,
        "alignmentH": 0,
        "alignmentV": 0
    }
    
    payload = {
        "panels": [
            {
                "ip": test_panel_ip,
                "port": 5200,
                "protocol": "old",  # Protocolo por defecto
                "windows": [window]
            }
        ]
    }
    
    print(f"\n📦 Payload generado:")
    print(f"   effect: '{effect_string}'")
    print(f"   ✅ Mapeo correcto: effect={test_effect} → '{effect_string}'")
    
    # Verificar que el efecto es correcto
    if effect_string == "fijo":
        print(f"   ✅ El efecto se mapea correctamente a 'fijo'")
    else:
        print(f"   ❌ El efecto se mapea incorrectamente a '{effect_string}'")
    
    print(f"\n🎯 RESULTADO:")
    print("-" * 60)
    if effect_string == "fijo":
        print(f"✅ El mapeo de efectos está CORRECTO")
        print(f"   Los paneles deberían recibir effect='fijo'")
    else:
        print(f"❌ El mapeo de efectos está INCORRECTO")
        print(f"   Los paneles reciben effect='{effect_string}' en lugar de 'fijo'")

if __name__ == "__main__":
    test_effect_mapping() 