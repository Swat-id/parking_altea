#!/usr/bin/env python3
"""
Script temporal para formatear la respuesta JSON del endpoint de parkings
"""

import json
import sys

def format_parkings_response():
    """Formatear la respuesta del endpoint /parkings/status"""
    
    try:
        # Leer JSON desde stdin
        data = json.load(sys.stdin)
        
        # Formatear y mostrar
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    format_parkings_response() 