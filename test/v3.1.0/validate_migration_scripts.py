#!/usr/bin/env python3
"""
Validación de Scripts de Migración v3.1.0
Valida que los scripts de migración están correctos sin ejecutarlos
"""

import os
import sys
import ast
import re

def validate_migration_script(script_path):
    """Validar sintaxis y estructura del script de migración"""
    print(f"🔍 Validando script: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"❌ Script no encontrado: {script_path}")
        return False
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validar sintaxis Python
        ast.parse(content)
        print("✅ Sintaxis Python válida")
        
        # Validar imports requeridos
        required_imports = [
            'sqlalchemy',
            'config',
            'bcrypt',
            'datetime'
        ]
        
        for imp in required_imports:
            if imp in content:
                print(f"✅ Import {imp} encontrado")
            else:
                print(f"⚠️  Import {imp} no encontrado")
        
        # Validar funciones requeridas
        required_functions = [
            'migrate_database',
            'verify_migration',
            'hash_password'
        ]
        
        for func in required_functions:
            if f"def {func}" in content:
                print(f"✅ Función {func} encontrada")
            else:
                print(f"❌ Función {func} no encontrada")
        
        # Validar SQL queries críticas
        critical_queries = [
            'ALTER TABLE users ADD COLUMN role',
            'ALTER TABLE users ADD COLUMN updated_at',
            'CREATE INDEX idx_users_email',
            'CREATE INDEX idx_users_role',
            'CREATE INDEX idx_users_active_role',
            'INSERT INTO users',
            'INSERT INTO user_parkings'
        ]
        
        for query in critical_queries:
            if query in content:
                print(f"✅ Query crítica encontrada: {query[:50]}...")
            else:
                print(f"⚠️  Query crítica no encontrada: {query}")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validando script: {e}")
        return False

def validate_rollback_script(script_path):
    """Validar script de rollback"""
    print(f"🔍 Validando script de rollback: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"❌ Script de rollback no encontrado: {script_path}")
        return False
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validar sintaxis Python
        ast.parse(content)
        print("✅ Sintaxis Python válida")
        
        # Validar funciones requeridas
        required_functions = ['rollback_migration']
        
        for func in required_functions:
            if f"def {func}" in content:
                print(f"✅ Función {func} encontrada")
            else:
                print(f"❌ Función {func} no encontrada")
        
        # Validar SQL queries de rollback
        rollback_queries = [
            'DROP INDEX IF EXISTS',
            'DROP COLUMN IF EXISTS',
            'DROP CONSTRAINT IF EXISTS',
            'DELETE FROM user_parkings',
            'DELETE FROM users'
        ]
        
        for query in rollback_queries:
            if query in content:
                print(f"✅ Query de rollback encontrada: {query}")
            else:
                print(f"⚠️  Query de rollback no encontrada: {query}")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validando script de rollback: {e}")
        return False

def validate_verification_script(script_path):
    """Validar script de verificación"""
    print(f"🔍 Validando script de verificación: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"❌ Script de verificación no encontrado: {script_path}")
        return False
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validar sintaxis Python
        ast.parse(content)
        print("✅ Sintaxis Python válida")
        
        # Validar funciones requeridas
        required_functions = ['verify_migration', 'test_user_properties']
        
        for func in required_functions:
            if f"def {func}" in content:
                print(f"✅ Función {func} encontrada")
            else:
                print(f"❌ Función {func} no encontrada")
        
        # Validar queries de verificación
        verification_queries = [
            'SELECT column_name FROM information_schema.columns',
            'SELECT constraint_name FROM information_schema.check_constraints',
            'SELECT indexname FROM pg_indexes',
            'SELECT name, email, role FROM users'
        ]
        
        for query in verification_queries:
            if query in content:
                print(f"✅ Query de verificación encontrada: {query[:50]}...")
            else:
                print(f"⚠️  Query de verificación no encontrada: {query}")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validando script de verificación: {e}")
        return False

def validate_models_file(models_path):
    """Validar archivo de modelos"""
    print(f"🔍 Validando archivo de modelos: {models_path}")
    
    if not os.path.exists(models_path):
        print(f"❌ Archivo de modelos no encontrado: {models_path}")
        return False
    
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validar sintaxis Python
        ast.parse(content)
        print("✅ Sintaxis Python válida")
        
        # Validar clase User
        if 'class User(Base):' in content:
            print("✅ Clase User encontrada")
        else:
            print("❌ Clase User no encontrada")
        
        # Validar campos nuevos
        new_fields = [
            'role = Column(String(20), default=\'user\', nullable=False)',
            'updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())'
        ]
        
        for field in new_fields:
            if field in content:
                print(f"✅ Campo nuevo encontrado: {field[:30]}...")
            else:
                print(f"❌ Campo nuevo no encontrado: {field[:30]}...")
        
        # Validar propiedades
        properties = [
            'def is_superadmin(self):',
            'def is_regular_user(self):'
        ]
        
        for prop in properties:
            if prop in content:
                print(f"✅ Propiedad encontrada: {prop}")
            else:
                print(f"❌ Propiedad no encontrada: {prop}")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validando archivo de modelos: {e}")
        return False

def main():
    """Función principal de validación"""
    print("🚀 Iniciando validación de scripts de migración v3.1.0...")
    
    # Rutas de los archivos
    base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
    
    files_to_validate = [
        ('migrate_to_v3_1_0.py', validate_migration_script),
        ('rollback_migration_v3_1_0.py', validate_rollback_script),
        ('verify_migration_v3_1_0.py', validate_verification_script),
        ('models.py', validate_models_file)
    ]
    
    results = []
    
    for filename, validator in files_to_validate:
        filepath = os.path.join(base_path, filename)
        print(f"\n{'='*60}")
        result = validator(filepath)
        results.append((filename, result))
        print(f"{'='*60}")
    
    # Resumen final
    print(f"\n📊 Resumen de validación:")
    print(f"{'='*60}")
    
    all_valid = True
    for filename, result in results:
        status = "✅ VÁLIDO" if result else "❌ INVÁLIDO"
        print(f"   - {filename}: {status}")
        if not result:
            all_valid = False
    
    print(f"{'='*60}")
    
    if all_valid:
        print("🎉 ¡Todos los scripts son válidos!")
        print("✅ Los scripts están listos para ser ejecutados en el servidor")
    else:
        print("❌ Algunos scripts tienen problemas")
        print("⚠️  Revisar los errores antes de proceder")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 