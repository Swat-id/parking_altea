#!/usr/bin/env python3
"""
Script para generar el hash de la contraseña admin123!
"""

from werkzeug.security import generate_password_hash

password = 'admin123!'
password_hash = generate_password_hash(password)

print(f"Contraseña: {password}")
print(f"Hash generado: {password_hash}")

# También generar el SQL completo
sql = f"""
-- Script para crear usuario superadmin info@swat-id.com
-- Contraseña: admin123!

-- Verificar si el usuario ya existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'info@swat-id.com') THEN
        -- Insertar usuario superadmin
        INSERT INTO users (
            email, 
            name, 
            password_hash, 
            role, 
            is_active, 
            created_at
        ) VALUES (
            'info@swat-id.com',
            'Superadmin SWAT-ID',
            '{password_hash}',
            'superadmin',
            true,
            NOW()
        );
        
        RAISE NOTICE 'Usuario superadmin info@swat-id.com creado exitosamente';
    ELSE
        RAISE NOTICE 'El usuario info@swat-id.com ya existe';
    END IF;
END $$;

-- Mostrar usuarios existentes
SELECT 
    id,
    email,
    name,
    role,
    is_active,
    created_at
FROM users 
ORDER BY id;
"""

print("\n" + "="*60)
print("SQL COMPLETO:")
print("="*60)
print(sql) 