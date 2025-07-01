#!/usr/bin/env python3
"""Script para probar la importación de update_parking_panels"""

import sys
import os
sys.path.append('src')

try:
    from panel_communication import update_parking_panels
    print("✅ Import successful")
    print(f"Function: {update_parking_panels}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc() 