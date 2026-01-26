-- =====================================================
-- MIGRACIÓN: Sistema de Corrección Automática v4.5.0
-- =====================================================
-- Fecha: 2026-01-26
-- Descripción: Tablas para corrección automática de ocupación
--              basada en patrones históricos de ajustes manuales
-- =====================================================

-- 1. Tabla de configuración de corrección por parking
CREATE TABLE IF NOT EXISTS parking_correction_config (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE UNIQUE,
    
    -- Configuración de corrección automática
    auto_correction_enabled BOOLEAN DEFAULT TRUE,  -- Habilitado por defecto
    correction_hour INTEGER DEFAULT 6,             -- Hora del día (0-23)
    correction_minute INTEGER DEFAULT 0,           -- Minuto (0-59)
    
    -- Parámetros calculados globales
    avg_hourly_drift FLOAT DEFAULT 0,              -- Desviación promedio por hora
    avg_daily_drift FLOAT DEFAULT 0,               -- Desviación promedio diaria (24h)
    confidence_level FLOAT DEFAULT 0,              -- Confianza del cálculo (0-1)
    sample_count INTEGER DEFAULT 0,                -- Número total de muestras
    
    -- Parámetros por día de semana (JSONB)
    -- Formato: {"0": 0.5, "1": 0.6, ...} donde 0=Lunes, 6=Domingo
    drift_by_weekday JSONB DEFAULT '{"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}',
    samples_by_weekday JSONB DEFAULT '{"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}',
    avg_occupancy_by_weekday JSONB DEFAULT '{"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}',
    
    -- Corrección sugerida actual
    suggested_correction INTEGER DEFAULT 0,
    last_calculation_at TIMESTAMP WITH TIME ZONE,
    
    -- Última corrección aplicada
    last_auto_correction_at TIMESTAMP WITH TIME ZONE,
    last_auto_correction_amount INTEGER DEFAULT 0,
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_correction_config_parking ON parking_correction_config(parking_id);
CREATE INDEX IF NOT EXISTS idx_correction_config_enabled ON parking_correction_config(auto_correction_enabled);

-- 2. Tabla de cálculos de corrección (histórico para aprendizaje)
CREATE TABLE IF NOT EXISTS correction_calculations (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
    
    -- Timestamp del ajuste que generó este cálculo
    adjustment_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Datos temporales
    hours_since_last_correction FLOAT,             -- Horas desde última corrección
    time_of_day INTEGER,                           -- Hora del día (0-23)
    day_of_week INTEGER,                           -- Día de la semana (0-6, 0=Lunes)
    
    -- Datos de ocupación (IMPORTANTE: no solo el descuadre)
    occupancy_before_adjustment INTEGER,           -- Ocupación antes del ajuste
    occupancy_after_adjustment INTEGER,            -- Ocupación después del ajuste
    correction_applied INTEGER,                    -- Diferencia aplicada
    
    -- Métricas calculadas
    drift_per_hour FLOAT,                          -- Desviación por hora
    drift_total FLOAT,                             -- Desviación total del período
    
    -- Contexto
    parking_capacity INTEGER,                      -- Capacidad del parking en ese momento
    occupancy_percentage_before FLOAT,             -- % ocupación antes
    occupancy_percentage_after FLOAT,              -- % ocupación después
    
    -- Tipo de ajuste que generó este registro
    trigger_type VARCHAR(30) NOT NULL,             -- 'manual', 'auto_scheduled', 'bootstrap', etc.
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para análisis
CREATE INDEX IF NOT EXISTS idx_calculations_parking ON correction_calculations(parking_id);
CREATE INDEX IF NOT EXISTS idx_calculations_timestamp ON correction_calculations(adjustment_timestamp);
CREATE INDEX IF NOT EXISTS idx_calculations_weekday ON correction_calculations(day_of_week);
CREATE INDEX IF NOT EXISTS idx_calculations_trigger ON correction_calculations(trigger_type);

-- 3. Tabla de historial de correcciones automáticas aplicadas
CREATE TABLE IF NOT EXISTS auto_correction_history (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
    
    -- Timestamp de la corrección
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Datos de la corrección
    occupancy_before INTEGER NOT NULL,
    occupancy_after INTEGER NOT NULL,
    correction_amount INTEGER NOT NULL,
    
    -- Parámetros usados para el cálculo
    drift_used FLOAT,                              -- Drift usado (específico día o general)
    hours_elapsed FLOAT,                           -- Horas desde última corrección
    confidence_at_time FLOAT,                      -- Confianza en el momento
    day_of_week INTEGER,                           -- Día de semana
    
    -- Resultado
    adjustment_type VARCHAR(30) NOT NULL,          -- 'auto_scheduled', 'limit_floor', 'limit_ceiling'
    was_limited BOOLEAN DEFAULT FALSE,             -- Si se aplicó límite
    original_suggestion INTEGER,                   -- Sugerencia original (antes de límites)
    
    -- Validación posterior (se actualiza cuando hay siguiente ajuste manual)
    validated BOOLEAN DEFAULT FALSE,
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    actual_correction_needed INTEGER,              -- Corrección real que necesitaba
    prediction_error INTEGER,                      -- Diferencia entre predicción y realidad
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auto_history_parking ON auto_correction_history(parking_id);
CREATE INDEX IF NOT EXISTS idx_auto_history_applied ON auto_correction_history(applied_at);

-- 4. Añadir campo adjustment_type a occupancy_history si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'occupancy_history' AND column_name = 'adjustment_type'
    ) THEN
        ALTER TABLE occupancy_history ADD COLUMN adjustment_type VARCHAR(30) DEFAULT NULL;
        
        -- Actualizar registros existentes según source
        UPDATE occupancy_history SET adjustment_type = source WHERE adjustment_type IS NULL;
    END IF;
END $$;

-- 5. Inicializar configuración para todos los parkings existentes
INSERT INTO parking_correction_config (parking_id, auto_correction_enabled)
SELECT id, TRUE FROM parkings
WHERE id NOT IN (SELECT parking_id FROM parking_correction_config WHERE parking_id IS NOT NULL)
ON CONFLICT (parking_id) DO NOTHING;

-- 6. Comentarios de documentación
COMMENT ON TABLE parking_correction_config IS 'Configuración de corrección automática por parking';
COMMENT ON TABLE correction_calculations IS 'Histórico de cálculos para aprendizaje del algoritmo';
COMMENT ON TABLE auto_correction_history IS 'Historial de correcciones automáticas aplicadas';
COMMENT ON COLUMN parking_correction_config.drift_by_weekday IS 'Drift promedio por día: {"0": drift_lunes, ..., "6": drift_domingo}';
COMMENT ON COLUMN correction_calculations.trigger_type IS 'Tipo: manual, auto_scheduled, bootstrap, limit_floor, limit_ceiling';
