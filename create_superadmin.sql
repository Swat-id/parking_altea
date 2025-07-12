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
            'pbkdf2:sha256:600000$dK9XmN8v$1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
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