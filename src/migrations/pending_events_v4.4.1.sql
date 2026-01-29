-- ============================================================================
-- MIGRACIÓN v4.4.1: Sistema de Eventos Pendientes de Validación
-- ============================================================================
-- Este sistema permite sincronizar el conteo de accesos con la detección
-- plaza a plaza, manejando los desfases temporales entre eventos.
-- ============================================================================

-- Añadir columnas a parkings para tracking de eventos pendientes
ALTER TABLE parkings ADD COLUMN IF NOT EXISTS pending_entries INTEGER DEFAULT 0;
ALTER TABLE parkings ADD COLUMN IF NOT EXISTS pending_exits INTEGER DEFAULT 0;

-- Tabla para registro detallado de eventos pendientes
CREATE TABLE IF NOT EXISTS pending_parking_events (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    event_type VARCHAR(10) NOT NULL CHECK (event_type IN ('entry', 'exit')),
    
    -- Datos del evento original
    source VARCHAR(50) NOT NULL,  -- 'camera_access' o 'spot_detection'
    camera_id INTEGER,            -- ID de la cámara que generó el evento
    spot_id INTEGER,              -- ID de la plaza (si aplica)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,      -- Cuando se validó con el evento complementario
    expired_at TIMESTAMP WITH TIME ZONE,        -- Cuando expiró sin validación
    
    -- Estado
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'validated', 'expired', 'cancelled')),
    
    -- Datos adicionales para debugging
    occupancy_at_creation INTEGER,              -- Ocupación del parking al crear el evento
    notes TEXT
);

-- Índices para búsqueda eficiente
CREATE INDEX IF NOT EXISTS idx_pending_events_parking_status 
    ON pending_parking_events(parking_id, status);
CREATE INDEX IF NOT EXISTS idx_pending_events_type_status 
    ON pending_parking_events(event_type, status);
CREATE INDEX IF NOT EXISTS idx_pending_events_created 
    ON pending_parking_events(created_at);

-- Función para limpiar eventos expirados (llamar periódicamente)
CREATE OR REPLACE FUNCTION cleanup_expired_pending_events(
    entry_timeout_minutes INTEGER DEFAULT 5,
    exit_timeout_minutes INTEGER DEFAULT 10
) RETURNS TABLE(
    expired_entries INTEGER,
    expired_exits INTEGER
) AS $$
DECLARE
    v_expired_entries INTEGER := 0;
    v_expired_exits INTEGER := 0;
BEGIN
    -- Expirar entradas pendientes (vehículo entró a zona no monitorizada)
    UPDATE pending_parking_events
    SET status = 'expired',
        expired_at = NOW(),
        notes = COALESCE(notes, '') || ' | Expirado automáticamente tras ' || entry_timeout_minutes || ' minutos'
    WHERE event_type = 'entry'
      AND status = 'pending'
      AND created_at < NOW() - (entry_timeout_minutes || ' minutes')::INTERVAL;
    
    GET DIAGNOSTICS v_expired_entries = ROW_COUNT;
    
    -- Expirar salidas pendientes (vehículo cambió de plaza, no salió)
    UPDATE pending_parking_events
    SET status = 'expired',
        expired_at = NOW(),
        notes = COALESCE(notes, '') || ' | Expirado automáticamente tras ' || exit_timeout_minutes || ' minutos'
    WHERE event_type = 'exit'
      AND status = 'pending'
      AND created_at < NOW() - (exit_timeout_minutes || ' minutes')::INTERVAL;
    
    GET DIAGNOSTICS v_expired_exits = ROW_COUNT;
    
    -- Actualizar contadores en parkings
    UPDATE parkings p
    SET pending_entries = (
        SELECT COUNT(*) FROM pending_parking_events 
        WHERE parking_id = p.id AND event_type = 'entry' AND status = 'pending'
    ),
    pending_exits = (
        SELECT COUNT(*) FROM pending_parking_events 
        WHERE parking_id = p.id AND event_type = 'exit' AND status = 'pending'
    );
    
    RETURN QUERY SELECT v_expired_entries, v_expired_exits;
END;
$$ LANGUAGE plpgsql;

-- Comentarios
COMMENT ON TABLE pending_parking_events IS 'Eventos de entrada/salida pendientes de validación cruzada entre conteo de accesos y detección de plazas';
COMMENT ON COLUMN parkings.pending_entries IS 'Número de entradas por acceso pendientes de validación por ocupación de plaza';
COMMENT ON COLUMN parkings.pending_exits IS 'Número de plazas liberadas pendientes de validación por salida de acceso';

-- Conceder permisos
GRANT ALL PRIVILEGES ON TABLE pending_parking_events TO parking_user;
GRANT USAGE, SELECT ON SEQUENCE pending_parking_events_id_seq TO parking_user;
GRANT EXECUTE ON FUNCTION cleanup_expired_pending_events TO parking_user;
