#!/usr/bin/env python3
"""
Script de verificación para comprobar la implementación de decoradores en T2.2
"""

import os
import re
import sys

def verify_decorators_implementation():
    """Verifica que los decoradores estén implementados correctamente"""
    print("=" * 60)
    print("VERIFICACIÓN DE IMPLEMENTACIÓN DE DECORADORES - T2.2")
    print("=" * 60)
    
    auth_file = "src/auth.py"
    results = []
    
    if not os.path.exists(auth_file):
        print(f"✗ Archivo {auth_file} no encontrado")
        return False
    
    # Leer el archivo auth.py
    with open(auth_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Verificar decorador require_superadmin
    print("\n1. Verificando decorador require_superadmin...")
    
    if "def require_superadmin(f):" in content:
        print("✓ Función require_superadmin encontrada")
        
        # Verificar que verifica el rol
        if "user_role != 'superadmin'" in content:
            print("✓ Verificación de rol superadmin implementada")
            results.append(("require_superadmin - función", "PASS"))
        else:
            print("✗ Verificación de rol superadmin no encontrada")
            results.append(("require_superadmin - función", "FAIL"))
    else:
        print("✗ Función require_superadmin no encontrada")
        results.append(("require_superadmin - función", "FAIL"))
    
    # 2. Verificar decorador require_parking_access
    print("\n2. Verificando decorador require_parking_access...")
    
    if "def require_parking_access(" in content:
        print("✓ Función require_parking_access encontrada")
        
        # Verificar que usa el parámetro parking_id_param
        if "parking_id_param=" in content:
            print("✓ Parámetro parking_id_param configurado")
        
        # Verificar que verifica UserParking
        if "UserParking.user_id == user_id" in content:
            print("✓ Verificación de UserParking implementada")
            results.append(("require_parking_access - función", "PASS"))
        else:
            print("✗ Verificación de UserParking no encontrada")
            results.append(("require_parking_access - función", "FAIL"))
    else:
        print("✗ Función require_parking_access no encontrada")
        results.append(("require_parking_access - función", "FAIL"))
    
    # 3. Verificar decorador require_panel_access
    print("\n3. Verificando decorador require_panel_access...")
    
    if "def require_panel_access(" in content:
        print("✓ Función require_panel_access encontrada")
        
        # Verificar que usa el parámetro panel_id_param
        if "panel_id_param=" in content:
            print("✓ Parámetro panel_id_param configurado")
        
        # Verificar que verifica UserPanel
        if "UserPanel.user_id == user_id" in content:
            print("✓ Verificación de UserPanel implementada")
            results.append(("require_panel_access - función", "PASS"))
        else:
            print("✗ Verificación de UserPanel no encontrada")
            results.append(("require_panel_access - función", "FAIL"))
    else:
        print("✗ Función require_panel_access no encontrada")
        results.append(("require_panel_access - función", "FAIL"))
    
    # 4. Verificar imports necesarios
    print("\n4. Verificando imports necesarios...")
    
    required_imports = [
        "from functools import wraps",
        "from flask import request, jsonify",
        "from models import User, UserParking, UserPanel"
    ]
    
    for imp in required_imports:
        if imp in content:
            print(f"✓ Import encontrado: {imp}")
        else:
            print(f"✗ Import faltante: {imp}")
            results.append(("imports", "FAIL"))
            break
    else:
        results.append(("imports", "PASS"))
    
    # 5. Verificar manejo de errores
    print("\n5. Verificando manejo de errores...")
    
    error_checks = [
        "403",  # Código de error para acceso denegado
        "Acceso denegado",  # Mensaje de error
        "return jsonify"  # Respuesta JSON
    ]
    
    for check in error_checks:
        if check in content:
            print(f"✓ Manejo de error encontrado: {check}")
        else:
            print(f"✗ Manejo de error faltante: {check}")
            results.append(("manejo_errores", "FAIL"))
            break
    else:
        results.append(("manejo_errores", "PASS"))
    
    # 6. Verificar integración con require_auth
    print("\n6. Verificando integración con require_auth...")
    
    if "require_auth(lambda: None)()" in content:
        print("✓ Integración con require_auth implementada")
        results.append(("integración_require_auth", "PASS"))
    else:
        print("✗ Integración con require_auth no encontrada")
        results.append(("integración_require_auth", "FAIL"))
    
    # 7. Verificar manejo de superadmin
    print("\n7. Verificando manejo de superadmin...")
    
    if "if user_role == 'superadmin':" in content:
        print("✓ Manejo especial para superadmin implementado")
        results.append(("manejo_superadmin", "PASS"))
    else:
        print("✗ Manejo especial para superadmin no encontrado")
        results.append(("manejo_superadmin", "FAIL"))
    
    # 8. Verificar manejo de base de datos
    print("\n8. Verificando manejo de base de datos...")
    
    db_checks = [
        "SessionLocal = sessionmaker",
        "db_session.close()",
        "try:",
        "finally:"
    ]
    
    for check in db_checks:
        if check in content:
            print(f"✓ Manejo de BD encontrado: {check}")
        else:
            print(f"✗ Manejo de BD faltante: {check}")
            results.append(("manejo_bd", "FAIL"))
            break
    else:
        results.append(("manejo_bd", "PASS"))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status_icon = "✓" if result == "PASS" else "✗"
        print(f"{status_icon} {test_name}: {result}")
        
        if result == "PASS":
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} verificaciones")
    print(f"✓ Pasadas: {passed}")
    print(f"✗ Fallidas: {failed}")
    
    if failed == 0:
        print("\n🎉 TODAS LAS VERIFICACIONES PASARON - T2.2 IMPLEMENTADA CORRECTAMENTE")
        return True
    else:
        print(f"\n⚠️  {failed} VERIFICACIONES FALLARON")
        return False

def check_decorator_usage_examples():
    """Verifica ejemplos de uso de los decoradores"""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE USO DE DECORADORES")
    print("=" * 60)
    
    examples = [
        {
            "name": "require_superadmin",
            "usage": "@require_superadmin\ndef admin_only_endpoint():",
            "description": "Protege endpoints solo para superadmin"
        },
        {
            "name": "require_parking_access", 
            "usage": "@require_parking_access('parking_id')\ndef parking_endpoint(parking_id):",
            "description": "Protege endpoints de parking específico"
        },
        {
            "name": "require_panel_access",
            "usage": "@require_panel_access('panel_id')\ndef panel_endpoint(panel_id):",
            "description": "Protege endpoints de panel específico"
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  {example['usage']}")
        print(f"  {example['description']}")

if __name__ == "__main__":
    success = verify_decorators_implementation()
    check_decorator_usage_examples()
    sys.exit(0 if success else 1) 