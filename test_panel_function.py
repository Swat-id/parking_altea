#!/usr/bin/env python3
"""Script para probar la función update_parking_panels completa"""

import sys
import os
sys.path.append('src')

try:
    from panel_communication import update_parking_panels
    print("✅ Import successful")
    
    # Probar la función con un parking que existe
    print("\n🧪 Probando función update_parking_panels...")
    result = update_parking_panels(1, 330, 500, "LIBRE")
    
    if result:
        print(f"✅ Función ejecutada correctamente")
        print(f"   Resultado: {result}")
    else:
        print(f"❌ Función no devolvió resultado")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 