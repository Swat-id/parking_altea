-- ============================================================================
-- MIGRACIÓN v4.4.0: Sistema de Detección de Plazas Individuales
-- ============================================================================
-- Fecha: 2026-01-26
-- Descripción: Añade soporte para cámaras de detección por plaza individual
-- ============================================================================

-- ============================================================================
-- 1. MODIFICAR TABLA accesses (cámaras)
-- ============================================================================

-- Tipo de cámara: 'counting' (conteo accesos) o 'spot_detection' (detección por plaza)
ALTER TABLE accesses ADD COLUMN IF NOT EXISTS camera_type VARCHAR(20) DEFAULT 'counting';

-- Número de plazas que monitoriza esta cámara (solo para spot_detection)
ALTER TABLE accesses ADD COLUMN IF NOT EXISTS monitored_spots_count INTEGER DEFAULT 0;

-- Índice para filtrar por tipo de cámara
CREATE INDEX IF NOT EXISTS idx_accesses_camera_type ON accesses(camera_type);

-- Comentarios para documentación
COMMENT ON COLUMN accesses.camera_type IS 'Tipo de cámara: counting=conteo en accesos, spot_detection=detección por plaza';
COMMENT ON COLUMN accesses.monitored_spots_count IS 'Número de plazas que monitoriza esta cámara (solo para spot_detection)';


-- ============================================================================
-- 2. MODIFICAR TABLA parkings
-- ============================================================================

-- Habilitar monitorización plaza a plaza
ALTER TABLE parkings ADD COLUMN IF NOT EXISTS spot_monitoring_enabled BOOLEAN DEFAULT FALSE;

-- Total de plazas monitorizadas (suma de todas las cámaras de detección)
ALTER TABLE parkings ADD COLUMN IF NOT EXISTS total_monitored_spots INTEGER DEFAULT 0;

-- Plazas ocupadas según detección por plaza
ALTER TABLE parkings ADD COLUMN IF NOT EXISTS total_spot_occupied INTEGER DEFAULT 0;

-- Última sincronización de plazas
ALTER TABLE parkings ADD COLUMN IF NOT EXISTS last_spot_sync TIMESTAMP WITH TIME ZONE;

-- Comentarios para documentación
COMMENT ON COLUMN parkings.spot_monitoring_enabled IS 'Indica si el parking tiene monitorización plaza a plaza activa';
COMMENT ON COLUMN parkings.total_monitored_spots IS 'Total de plazas monitorizadas por cámaras de detección';
COMMENT ON COLUMN parkings.total_spot_occupied IS 'Plazas ocupadas según detección por plaza';
COMMENT ON COLUMN parkings.last_spot_sync IS 'Última sincronización de datos de detección por plaza';


-- ============================================================================
-- 3. CREAR TABLA monitored_spots (plazas individuales)
-- ============================================================================

CREATE TABLE IF NOT EXISTS monitored_spots (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    camera_id INTEGER NOT NULL REFERENCES accesses(id) ON DELETE CASCADE,
    area_name VARCHAR(10) NOT NULL,
    spot_number INTEGER NOT NULL,
    current_status INTEGER DEFAULT 0,  -- 0=libre, 1=ocupado
    last_status_change TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Única combinación cámara + área + número de plaza
    CONSTRAINT unique_camera_area_spot UNIQUE(camera_id, area_name, spot_number)
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_monitored_spots_parking ON monitored_spots(parking_id);
CREATE INDEX IF NOT EXISTS idx_monitored_spots_camera ON monitored_spots(camera_id);
CREATE INDEX IF NOT EXISTS idx_monitored_spots_status ON monitored_spots(current_status);
CREATE INDEX IF NOT EXISTS idx_monitored_spots_parking_status ON monitored_spots(parking_id, current_status);

-- Comentarios
COMMENT ON TABLE monitored_spots IS 'Plazas individuales monitorizadas por cámaras de detección';
COMMENT ON COLUMN monitored_spots.area_name IS 'Nombre del área (A, B, C, etc.) según configuración de la cámara';
COMMENT ON COLUMN monitored_spots.spot_number IS 'Número de plaza dentro del área';
COMMENT ON COLUMN monitored_spots.current_status IS '0=libre, 1=ocupado';


-- ============================================================================
-- 4. CREAR TABLA spot_status_history (histórico de eventos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS spot_status_history (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL REFERENCES monitored_spots(id) ON DELETE CASCADE,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES accesses(id) ON DELETE SET NULL,
    previous_status INTEGER,
    new_status INTEGER NOT NULL,
    report_type VARCHAR(20),  -- 'trigger' o 'interval'
    device_name VARCHAR(100),  -- Nombre del device que reportó
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para consultas y análisis
CREATE INDEX IF NOT EXISTS idx_spot_history_spot ON spot_status_history(spot_id);
CREATE INDEX IF NOT EXISTS idx_spot_history_parking ON spot_status_history(parking_id);
CREATE INDEX IF NOT EXISTS idx_spot_history_camera ON spot_status_history(camera_id);
CREATE INDEX IF NOT EXISTS idx_spot_history_timestamp ON spot_status_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_spot_history_parking_timestamp ON spot_status_history(parking_id, timestamp);

-- Comentarios
COMMENT ON TABLE spot_status_history IS 'Histórico de cambios de estado de plazas individuales';
COMMENT ON COLUMN spot_status_history.report_type IS 'Tipo de reporte: trigger (evento individual) o interval (reporte periódico)';


-- ============================================================================
-- 5. CREAR TABLA spot_occupancy_corrections (histórico de correcciones)
-- ============================================================================

CREATE TABLE IF NOT EXISTS spot_occupancy_corrections (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    previous_occupancy INTEGER NOT NULL,
    new_occupancy INTEGER NOT NULL,
    correction_amount INTEGER NOT NULL,
    correction_reason VARCHAR(100),  -- 'spot_sync', 'limit_max', 'limit_min', 'manual'
    spot_occupied_count INTEGER,
    total_monitored_spots INTEGER,
    max_capacity INTEGER,
    raw_calculated_occupancy INTEGER,  -- Ocupación calculada antes de aplicar límites
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_corrections_parking ON spot_occupancy_corrections(parking_id);
CREATE INDEX IF NOT EXISTS idx_corrections_timestamp ON spot_occupancy_corrections(timestamp);
CREATE INDEX IF NOT EXISTS idx_corrections_parking_timestamp ON spot_occupancy_corrections(parking_id, timestamp);

-- Comentarios
COMMENT ON TABLE spot_occupancy_corrections IS 'Histórico de correcciones de ocupación basadas en monitorización por plaza';
COMMENT ON COLUMN spot_occupancy_corrections.raw_calculated_occupancy IS 'Ocupación calculada antes de aplicar límites (0 a 110%)';
COMMENT ON COLUMN spot_occupancy_corrections.correction_reason IS 'Razón: spot_sync, limit_max (>110%), limit_min (<0), manual';


-- ============================================================================
-- 6. CREAR TABLA spot_detection_logs (logs de mensajes recibidos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS spot_detection_logs (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES accesses(id) ON DELETE SET NULL,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE SET NULL,
    device_name VARCHAR(100),
    camera_ip VARCHAR(50),
    report_type VARCHAR(20),  -- 'trigger' o 'interval'
    total_occupied INTEGER,
    total_available INTEGER,
    spots_processed INTEGER,
    status VARCHAR(20) NOT NULL,  -- 'processed', 'error', 'camera_not_found', 'parking_disabled'
    error_message TEXT,
    processing_time_ms FLOAT,
    raw_message JSONB,  -- Mensaje JSON completo (sin snapshot)
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_spot_logs_camera ON spot_detection_logs(camera_id);
CREATE INDEX IF NOT EXISTS idx_spot_logs_parking ON spot_detection_logs(parking_id);
CREATE INDEX IF NOT EXISTS idx_spot_logs_status ON spot_detection_logs(status);
CREATE INDEX IF NOT EXISTS idx_spot_logs_received ON spot_detection_logs(received_at);

-- Comentarios
COMMENT ON TABLE spot_detection_logs IS 'Logs de todos los mensajes recibidos de cámaras de detección por plaza';
COMMENT ON COLUMN spot_detection_logs.raw_message IS 'Mensaje JSON completo recibido (sin campo snapshot para ahorrar espacio)';


-- ============================================================================
-- 7. VERIFICACIÓN DE LA MIGRACIÓN
-- ============================================================================

-- Verificar que todas las tablas fueron creadas
DO $$
BEGIN
    -- Verificar columnas en accesses
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'accesses' AND column_name = 'camera_type') THEN
        RAISE EXCEPTION 'Columna camera_type no encontrada en accesses';
    END IF;
    
    -- Verificar columnas en parkings
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'parkings' AND column_name = 'spot_monitoring_enabled') THEN
        RAISE EXCEPTION 'Columna spot_monitoring_enabled no encontrada en parkings';
    END IF;
    
    -- Verificar tabla monitored_spots
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'monitored_spots') THEN
        RAISE EXCEPTION 'Tabla monitored_spots no encontrada';
    END IF;
    
    -- Verificar tabla spot_status_history
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'spot_status_history') THEN
        RAISE EXCEPTION 'Tabla spot_status_history no encontrada';
    END IF;
    
    -- Verificar tabla spot_occupancy_corrections
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'spot_occupancy_corrections') THEN
        RAISE EXCEPTION 'Tabla spot_occupancy_corrections no encontrada';
    END IF;
    
    -- Verificar tabla spot_detection_logs
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'spot_detection_logs') THEN
        RAISE EXCEPTION 'Tabla spot_detection_logs no encontrada';
    END IF;
    
    RAISE NOTICE '✅ Migración v4.4.0 completada correctamente';
END $$;


-- ============================================================================
-- FIN DE LA MIGRACIÓN v4.4.0
-- ============================================================================
