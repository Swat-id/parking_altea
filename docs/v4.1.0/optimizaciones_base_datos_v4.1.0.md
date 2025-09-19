# Optimizaciones de Base de Datos v4.1.0

## Análisis de Patrones de Consulta

Basándome en el análisis del código actual, he identificado los siguientes patrones de consulta frecuentes:

### 1. Consultas Frecuentes Identificadas
- **Estado agrupado de parkings** con conteo de paneles
- **Información de sensores individuales** por parking y tipo
- **Estados actuales** de sensores con batería y timestamp
- **Resúmenes por tipo** de sensor (PMR, Eléctrico, etc.)
- **Programaciones activas** por parking
- **Historial de cambios** de sensores

### 2. Problemas de Rendimiento Potenciales
- Múltiples JOINs para obtener estado completo de parkings
- Consultas repetitivas para conteos agrupados
- Cálculos en tiempo real de estadísticas
- Consultas complejas con múltiples filtros

## Propuestas de Optimización

### 1. VISTAS MATERIALIZADAS

#### Vista: Resumen Completo de Parkings
```sql
-- Vista materializada para estado completo de parkings
CREATE MATERIALIZED VIEW parking_complete_status AS
SELECT 
    p.id as parking_id,
    p.name as parking_name,
    p.location,
    p.max_capacity,
    p.current_occupancy,
    p.status,
    p.threshold_dense,
    p.threshold_full,
    
    -- Conteo de paneles
    COUNT(DISTINCT pan.id) as total_panels,
    COUNT(DISTINCT CASE WHEN pan.status = 'online' THEN pan.id END) as online_panels,
    COUNT(DISTINCT CASE WHEN pan.status = 'offline' THEN pan.id END) as offline_panels,
    
    -- Conteo de sensores individuales por tipo
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'PMR' THEN s.id END) as pmr_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Electrico' THEN s.id END) as electric_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Caravanas' THEN s.id END) as caravan_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Emergencias' THEN s.id END) as emergency_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Policia' THEN s.id END) as police_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Otros' THEN s.id END) as other_sensors,
    
    -- Estados de sensores individuales
    COUNT(DISTINCT CASE WHEN scs.current_status = 'free' THEN s.id END) as free_individual_sensors,
    COUNT(DISTINCT CASE WHEN scs.current_status = 'busy' THEN s.id END) as busy_individual_sensors,
    COUNT(DISTINCT CASE WHEN scs.current_status = 'error' THEN s.id END) as error_individual_sensors,
    COUNT(DISTINCT CASE WHEN scs.current_status = 'unknown' THEN s.id END) as unknown_individual_sensors,
    
    -- Información de batería
    AVG(CASE WHEN scs.battery_capacity IS NOT NULL THEN scs.battery_capacity END) as avg_battery_level,
    COUNT(DISTINCT CASE WHEN scs.battery_capacity < 20 THEN s.id END) as low_battery_sensors,
    
    -- Timestamps
    MAX(pan.last_update) as last_panel_update,
    MAX(scs.last_update) as last_sensor_update,
    NOW() as view_updated_at
    
FROM parkings p
LEFT JOIN panels pan ON pan.parking_id = p.id AND pan.is_active = true
LEFT JOIN individual_sensors s ON s.parking_id = p.id AND s.is_active = true
LEFT JOIN sensor_current_status scs ON scs.sensor_id = s.id
GROUP BY p.id, p.name, p.location, p.max_capacity, p.current_occupancy, 
         p.status, p.threshold_dense, p.threshold_full;

-- Índices para la vista materializada
CREATE UNIQUE INDEX idx_parking_complete_status_parking_id 
ON parking_complete_status(parking_id);

CREATE INDEX idx_parking_complete_status_updated_at 
ON parking_complete_status(view_updated_at DESC);
```

#### Vista: Sensores por Tipo y Estado
```sql
-- Vista materializada para sensores agrupados por tipo
CREATE MATERIALIZED VIEW sensors_by_type_status AS
SELECT 
    s.parking_id,
    s.sensor_type,
    COUNT(*) as total_sensors,
    COUNT(CASE WHEN scs.current_status = 'free' THEN 1 END) as free_count,
    COUNT(CASE WHEN scs.current_status = 'busy' THEN 1 END) as busy_count,
    COUNT(CASE WHEN scs.current_status = 'error' THEN 1 END) as error_count,
    COUNT(CASE WHEN scs.current_status = 'unknown' THEN 1 END) as unknown_count,
    COUNT(CASE WHEN scs.current_status = 'notcalib' THEN 1 END) as notcalib_count,
    
    -- Estadísticas de batería por tipo
    AVG(scs.battery_capacity) as avg_battery,
    MIN(scs.battery_capacity) as min_battery,
    MAX(scs.battery_capacity) as max_battery,
    COUNT(CASE WHEN scs.battery_capacity < 20 THEN 1 END) as low_battery_count,
    
    -- Estadísticas temporales
    MAX(scs.last_update) as last_update,
    COUNT(CASE WHEN scs.last_update < NOW() - INTERVAL '1 hour' THEN 1 END) as stale_sensors,
    
    NOW() as view_updated_at
    
FROM individual_sensors s
LEFT JOIN sensor_current_status scs ON scs.sensor_id = s.id
WHERE s.is_active = true
GROUP BY s.parking_id, s.sensor_type;

-- Índices
CREATE UNIQUE INDEX idx_sensors_by_type_parking_type 
ON sensors_by_type_status(parking_id, sensor_type);

CREATE INDEX idx_sensors_by_type_updated_at 
ON sensors_by_type_status(view_updated_at DESC);
```

### 2. FUNCIONES DE ACCESO RÁPIDO

#### Función: Obtener Estado Completo de Parking
```sql
-- Función para obtener estado completo de un parking
CREATE OR REPLACE FUNCTION get_parking_complete_status(parking_id_param INTEGER)
RETURNS TABLE (
    parking_id INTEGER,
    parking_name VARCHAR,
    location VARCHAR,
    max_capacity INTEGER,
    current_occupancy INTEGER,
    status VARCHAR,
    total_panels BIGINT,
    online_panels BIGINT,
    offline_panels BIGINT,
    total_individual_sensors BIGINT,
    free_individual_sensors BIGINT,
    busy_individual_sensors BIGINT,
    error_individual_sensors BIGINT,
    avg_battery_level NUMERIC,
    low_battery_sensors BIGINT,
    last_update TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pcs.parking_id,
        pcs.parking_name,
        pcs.location,
        pcs.max_capacity,
        pcs.current_occupancy,
        pcs.status,
        pcs.total_panels,
        pcs.online_panels,
        pcs.offline_panels,
        (pcs.pmr_sensors + pcs.electric_sensors + pcs.caravan_sensors + 
         pcs.emergency_sensors + pcs.police_sensors + pcs.other_sensors) as total_individual_sensors,
        pcs.free_individual_sensors,
        pcs.busy_individual_sensors,
        pcs.error_individual_sensors,
        pcs.avg_battery_level,
        pcs.low_battery_sensors,
        GREATEST(pcs.last_panel_update, pcs.last_sensor_update) as last_update
    FROM parking_complete_status pcs
    WHERE pcs.parking_id = parking_id_param;
END;
$$ LANGUAGE plpgsql;
```

#### Función: Obtener Sensores por Tipo para Dashboard
```sql
-- Función para obtener resumen de sensores por tipo para dashboard
CREATE OR REPLACE FUNCTION get_sensors_dashboard_data(parking_id_param INTEGER DEFAULT NULL)
RETURNS TABLE (
    parking_id INTEGER,
    parking_name VARCHAR,
    sensor_type VARCHAR,
    total_sensors BIGINT,
    free_count BIGINT,
    busy_count BIGINT,
    error_count BIGINT,
    occupancy_rate NUMERIC,
    avg_battery NUMERIC,
    low_battery_count BIGINT,
    stale_sensors BIGINT,
    health_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sbts.parking_id,
        p.name as parking_name,
        sbts.sensor_type,
        sbts.total_sensors,
        sbts.free_count,
        sbts.busy_count,
        sbts.error_count,
        CASE 
            WHEN sbts.total_sensors > 0 
            THEN ROUND((sbts.busy_count::NUMERIC / sbts.total_sensors::NUMERIC) * 100, 2)
            ELSE 0 
        END as occupancy_rate,
        ROUND(sbts.avg_battery, 1) as avg_battery,
        sbts.low_battery_count,
        sbts.stale_sensors,
        -- Health score basado en batería, errores y sensores obsoletos
        CASE 
            WHEN sbts.total_sensors = 0 THEN 0
            ELSE ROUND(
                (100 - 
                 (sbts.error_count::NUMERIC / sbts.total_sensors::NUMERIC * 30) -
                 (sbts.low_battery_count::NUMERIC / sbts.total_sensors::NUMERIC * 20) -
                 (sbts.stale_sensors::NUMERIC / sbts.total_sensors::NUMERIC * 25)
                ), 1
            )
        END as health_score
    FROM sensors_by_type_status sbts
    JOIN parkings p ON p.id = sbts.parking_id
    WHERE (parking_id_param IS NULL OR sbts.parking_id = parking_id_param)
    ORDER BY sbts.parking_id, sbts.sensor_type;
END;
$$ LANGUAGE plpgsql;
```

### 3. FUNCIONES DE ACTUALIZACIÓN AUTOMÁTICA

#### Función: Refrescar Vistas Materializadas
```sql
-- Función para refrescar vistas materializadas
CREATE OR REPLACE FUNCTION refresh_parking_views()
RETURNS VOID AS $$
BEGIN
    -- Refrescar vistas materializadas
    REFRESH MATERIALIZED VIEW parking_complete_status;
    REFRESH MATERIALIZED VIEW sensors_by_type_status;
    
    -- Log de actualización
    INSERT INTO system_logs (level, message, timestamp) 
    VALUES ('INFO', 'Vistas materializadas actualizadas', NOW());
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log de error
        INSERT INTO system_logs (level, message, timestamp) 
        VALUES ('ERROR', 'Error actualizando vistas: ' || SQLERRM, NOW());
        RAISE;
END;
$$ LANGUAGE plpgsql;
```

### 4. TRIGGERS PARA ACTUALIZACIÓN AUTOMÁTICA

#### Trigger: Actualizar Vista al Cambiar Estado de Sensor
```sql
-- Función trigger para actualizar vista cuando cambia estado de sensor
CREATE OR REPLACE FUNCTION trigger_refresh_sensor_views()
RETURNS TRIGGER AS $$
BEGIN
    -- Actualizar solo la vista de sensores (más rápido que refrescar todo)
    REFRESH MATERIALIZED VIEW sensors_by_type_status;
    
    -- Si el sensor cambió de parking, actualizar vista completa
    IF (TG_OP = 'UPDATE' AND OLD.parking_id != NEW.parking_id) OR TG_OP = 'INSERT' THEN
        REFRESH MATERIALIZED VIEW parking_complete_status;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers
CREATE TRIGGER sensor_status_change_trigger
    AFTER INSERT OR UPDATE OR DELETE ON sensor_current_status
    FOR EACH ROW EXECUTE FUNCTION trigger_refresh_sensor_views();

CREATE TRIGGER individual_sensor_change_trigger
    AFTER INSERT OR UPDATE OR DELETE ON individual_sensors
    FOR EACH ROW EXECUTE FUNCTION trigger_refresh_sensor_views();
```

### 5. ÍNDICES ADICIONALES DE OPTIMIZACIÓN

```sql
-- Índices compuestos para consultas frecuentes
CREATE INDEX idx_individual_sensors_parking_type_active 
ON individual_sensors(parking_id, sensor_type, is_active);

CREATE INDEX idx_sensor_current_status_composite 
ON sensor_current_status(current_status, last_update DESC, battery_capacity);

CREATE INDEX idx_sensor_status_history_sensor_timestamp 
ON sensor_status_history(sensor_id, timestamp DESC);

-- Índice para consultas de batería baja
CREATE INDEX idx_sensor_current_status_low_battery 
ON sensor_current_status(battery_capacity) 
WHERE battery_capacity < 30;

-- Índice para sensores obsoletos
CREATE INDEX idx_sensor_current_status_stale 
ON sensor_current_status(last_update) 
WHERE last_update < NOW() - INTERVAL '2 hours';
```

### 6. PROCEDIMIENTO DE MANTENIMIENTO

```sql
-- Procedimiento de mantenimiento diario
CREATE OR REPLACE FUNCTION daily_maintenance()
RETURNS VOID AS $$
BEGIN
    -- Actualizar estadísticas de tablas
    ANALYZE individual_sensors;
    ANALYZE sensor_current_status;
    ANALYZE sensor_status_history;
    ANALYZE parking_sensor_summary;
    
    -- Refrescar vistas materializadas
    PERFORM refresh_parking_views();
    
    -- Limpiar datos antiguos del historial (mantener 90 días)
    DELETE FROM sensor_status_history 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Actualizar resúmenes por parking
    INSERT INTO parking_sensor_summary (parking_id, sensor_type, total_sensors, free_sensors, busy_sensors, error_sensors, last_update)
    SELECT 
        s.parking_id,
        s.sensor_type,
        COUNT(*) as total_sensors,
        COUNT(CASE WHEN scs.current_status = 'free' THEN 1 END) as free_sensors,
        COUNT(CASE WHEN scs.current_status = 'busy' THEN 1 END) as busy_sensors,
        COUNT(CASE WHEN scs.current_status = 'error' THEN 1 END) as error_sensors,
        NOW()
    FROM individual_sensors s
    LEFT JOIN sensor_current_status scs ON scs.sensor_id = s.id
    WHERE s.is_active = true AND s.parking_id IS NOT NULL
    GROUP BY s.parking_id, s.sensor_type
    ON CONFLICT (parking_id, sensor_type) DO UPDATE SET
        total_sensors = EXCLUDED.total_sensors,
        free_sensors = EXCLUDED.free_sensors,
        busy_sensors = EXCLUDED.busy_sensors,
        error_sensors = EXCLUDED.error_sensors,
        last_update = EXCLUDED.last_update;
    
    -- Log de mantenimiento
    INSERT INTO system_logs (level, message, timestamp) 
    VALUES ('INFO', 'Mantenimiento diario completado', NOW());
    
END;
$$ LANGUAGE plpgsql;
```

## Beneficios Esperados

### 1. Rendimiento
- **Consultas 5-10x más rápidas** para dashboards
- **Reducción de carga** en consultas complejas
- **Acceso instantáneo** a datos agrupados

### 2. Escalabilidad
- **Soporte para miles de sensores** sin degradación
- **Consultas optimizadas** para grandes volúmenes
- **Mantenimiento automático** de estadísticas

### 3. Funcionalidad
- **Dashboards en tiempo real** más eficientes
- **APIs más rápidas** para frontend
- **Alertas automáticas** por batería baja

## Plan de Implementación

### Fase 1: Vistas Básicas (1 hora)
- Crear vista `parking_complete_status`
- Crear vista `sensors_by_type_status`
- Aplicar índices básicos

### Fase 2: Funciones de Acceso (1 hora)
- Implementar funciones de consulta rápida
- Crear funciones de dashboard

### Fase 3: Automatización (30 minutos)
- Configurar triggers de actualización
- Implementar mantenimiento automático

### Fase 4: Testing y Validación (30 minutos)
- Probar rendimiento de consultas
- Validar integridad de datos
- Configurar monitorización

**Total estimado: 3 horas**

## Comandos de Implementación

Los comandos SQL están listos para ejecutar en la sesión psql actual. ¿Quieres que proceda con la implementación?
