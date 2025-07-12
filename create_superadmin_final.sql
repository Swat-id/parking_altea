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
            'scrypt:32768:8:1$sb9QDOK9tjbRwN5R$0dfdff0a050e7b0e6828f4e3648fa36234bfcafdff0db5e0ee351e30dc8fe013da9dec917a5e161cb2e088483142923541ae73a0d72ea01e388a7a2d8dbeb84a',
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