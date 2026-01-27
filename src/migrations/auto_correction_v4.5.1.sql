-- Migración v4.5.1: Algoritmo de corrección mejorado
-- Añade campos para corrección basada en ratio y transacciones

-- 1. Añadir campo adjustment_type a occupancy_history si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'occupancy_history' AND column_name = 'adjustment_type') THEN
        ALTER TABLE occupancy_history ADD COLUMN adjustment_type VARCHAR(50);
        COMMENT ON COLUMN occupancy_history.adjustment_type IS 'Tipo de ajuste: manual, camera, camera_limited_*, auto_scheduled, limit_*';
    END IF;
END $$;

-- 2. Añadir nuevos campos a correction_calculations si no existen
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'correction_calculations' AND column_name = 'transactions_count') THEN
        ALTER TABLE correction_calculations ADD COLUMN transactions_count INTEGER DEFAULT 0;
        COMMENT ON COLUMN correction_calculations.transactions_count IS 'Entradas + salidas desde último ajuste';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'correction_calculations' AND column_name = 'error_per_transaction') THEN
        ALTER TABLE correction_calculations ADD COLUMN error_per_transaction FLOAT;
        COMMENT ON COLUMN correction_calculations.error_per_transaction IS 'Tasa de error por transacción';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'correction_calculations' AND column_name = 'correction_ratio') THEN
        ALTER TABLE correction_calculations ADD COLUMN correction_ratio FLOAT;
        COMMENT ON COLUMN correction_calculations.correction_ratio IS 'Ratio occupancy_after/occupancy_before';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'correction_calculations' AND column_name = 'expected_occupancy') THEN
        ALTER TABLE correction_calculations ADD COLUMN expected_occupancy INTEGER;
        COMMENT ON COLUMN correction_calculations.expected_occupancy IS 'Ocupación esperada basada en histórico';
    END IF;
END $$;

-- 3. Añadir nuevos campos a parking_correction_config si no existen
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'parking_correction_config' AND column_name = 'avg_correction_ratio_by_weekday') THEN
        ALTER TABLE parking_correction_config ADD COLUMN avg_correction_ratio_by_weekday JSONB 
            DEFAULT '{"0": 1.0, "1": 1.0, "2": 1.0, "3": 1.0, "4": 1.0, "5": 1.0, "6": 1.0}'::jsonb;
        COMMENT ON COLUMN parking_correction_config.avg_correction_ratio_by_weekday IS 'Ratio de corrección promedio por día (after/before)';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'parking_correction_config' AND column_name = 'avg_error_per_transaction') THEN
        ALTER TABLE parking_correction_config ADD COLUMN avg_error_per_transaction FLOAT DEFAULT 0;
        COMMENT ON COLUMN parking_correction_config.avg_error_per_transaction IS 'Error promedio por transacción';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'parking_correction_config' AND column_name = 'avg_transactions_per_day') THEN
        ALTER TABLE parking_correction_config ADD COLUMN avg_transactions_per_day FLOAT DEFAULT 0;
        COMMENT ON COLUMN parking_correction_config.avg_transactions_per_day IS 'Transacciones promedio por día';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'parking_correction_config' AND column_name = 'expected_occupancy_by_weekday') THEN
        ALTER TABLE parking_correction_config ADD COLUMN expected_occupancy_by_weekday JSONB 
            DEFAULT '{"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}'::jsonb;
        COMMENT ON COLUMN parking_correction_config.expected_occupancy_by_weekday IS 'Ocupación esperada después de corrección por día';
    END IF;
END $$;

-- 4. Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_correction_calc_weekday_occupancy 
ON correction_calculations(parking_id, day_of_week, occupancy_before_adjustment);

CREATE INDEX IF NOT EXISTS idx_correction_calc_transactions 
ON correction_calculations(parking_id, transactions_count);

-- 5. Comentarios de documentación
COMMENT ON TABLE correction_calculations IS 'Histórico de ajustes para aprendizaje del algoritmo de corrección v4.5.1';
COMMENT ON TABLE parking_correction_config IS 'Configuración de corrección automática con parámetros de algoritmo v4.5.1';
