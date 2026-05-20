-- Migración: Añadir columna device_id a la tabla panels
-- Fecha: 2026-05-20
-- Descripción: El device_id es necesario para el formato de paquete CPower correcto

-- Añadir columna device_id
ALTER TABLE panels ADD COLUMN IF NOT EXISTS device_id VARCHAR(20);

-- Crear índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_panels_device_id ON panels(device_id);

-- Comentario explicativo
COMMENT ON COLUMN panels.device_id IS 'ID del dispositivo CPower (ej: 00606ed81e7e). Obtenido via UDP discovery.';

-- Panel conocido: BELLES ARTS 2 (172.20.4.52)
UPDATE panels SET device_id = '00606ed81e7e' WHERE ip = '172.20.4.52';
