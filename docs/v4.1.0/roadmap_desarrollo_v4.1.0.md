# Roadmap de Desarrollo v4.1.0 - Sistema de Gestión de Parking

## Estado General del Proyecto
- **Versión**: 4.1.0
- **Fecha de inicio**: 19/09/2025
- **Estimación total**: 124 horas (15.5 días laborables)
- **Progreso general**: 72.6% (90/124 horas completadas)

## Resumen de Funcionalidades

### 1. Gestión de Paneles - Selección de Ventanas (14h)
- **Progreso**: 100% (14/14 horas)
- **Prioridad**: Media
- **Descripción**: ✅ **COMPLETADO** - Selección ventana 0/1 en paneles Tipo 3

### 2. Sistema de Plazas Individuales PMR (55h)
- **Progreso**: 100% (55/55 horas)
- **Prioridad**: Alta
- **Descripción**: ✅ **COMPLETADO** - Sistema completo de gestión de sensores individuales

### 3. Servicio Push de Sensores (33h)
- **Progreso**: 100% (33/33 horas)
- **Prioridad**: Alta
- **Descripción**: ✅ **COMPLETADO** - Servicio en puerto 3535 para recepción de push de sensores

---

## FASE 1: ACTUALIZACIÓN DE BASE DE DATOS
**Duración**: 1 día (8 horas)  
**Progreso**: 100% (8/8 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 1.1 | Actualizar tabla panels para ventanas | 2h | 100% | ✅ Completado | Backend |
| 1.2 | Crear tablas sensores individuales | 3h | 100% | ✅ Completado | Backend |
| 1.3 | Crear índices y optimizaciones | 1h | 100% | ✅ Completado | Backend |
| 1.4 | Ejecutar migración y validar | 2h | 100% | ✅ Completado | Backend |

### ✅ **RESULTADOS VALIDADOS:**
- **15 paneles** actualizados con soporte para ventanas
- **14 paneles** con datos migrados correctamente
- **15 parkings** en vista materializada optimizada
- **18 índices** creados para máximo rendimiento
- **Optimizaciones implementadas**: 5 funciones + 2 vistas + 2 triggers

### Comandos de Actualización de Base de Datos

> **⚠️ IMPORTANTE**: Si encuentras el error "Peer authentication failed for user", usa:
> ```bash
> sudo -u postgres psql parking_db
> ```
> Esto ejecuta psql como el usuario del sistema `postgres` evitando problemas de autenticación.

#### 1.1 Actualización de Tabla Panels (2 horas)

```bash
# Conectar a la base de datos como postgres (usuario por defecto en el servidor)
# Según los scripts de deploy la BD se llama 'parking_db'
sudo -u postgres psql parking_db
```

Una vez conectado, ejecutar los siguientes comandos SQL:

```sql
-- 1. Añadir campos para almacenar último mensaje por ventana
ALTER TABLE panels 
ADD COLUMN IF NOT EXISTS last_message_window_0 TEXT,
ADD COLUMN IF NOT EXISTS last_message_window_1 TEXT,
ADD COLUMN IF NOT EXISTS last_update_window_0 TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_update_window_1 TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS window_config_json JSONB DEFAULT '{"windows": [{"id": 0, "enabled": true}, {"id": 1, "enabled": false}]}'::jsonb;

-- 2. Migrar datos existentes (mover last_message a window_0)
UPDATE panels 
SET last_message_window_0 = last_message,
    last_update_window_0 = last_update
WHERE last_message IS NOT NULL;

-- 3. Crear índices para optimización
CREATE INDEX IF NOT EXISTS idx_panels_window_0_update ON panels(last_update_window_0);
CREATE INDEX IF NOT EXISTS idx_panels_window_1_update ON panels(last_update_window_1);
CREATE INDEX IF NOT EXISTS idx_panels_window_config ON panels USING GIN(window_config_json);

-- 4. Verificar cambios
SELECT id, name, panel_type_id, last_message_window_0, last_message_window_1, window_config_json 
FROM panels 
LIMIT 5;

COMMIT;
```

#### 1.2 Creación de Tablas Sensores Individuales (3 horas)

```sql
-- Continuar en la misma sesión de psql
-- NOTA: La base de datos real es 'parking_db' según scripts de deploy

-- 1. Tabla principal de sensores individuales
CREATE TABLE IF NOT EXISTS individual_sensors (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(20) DEFAULT 'PMR' NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    parking_id INTEGER REFERENCES parkings(id) ON DELETE SET NULL,
    description TEXT,
    location_coordinates VARCHAR(100), -- "lat,lng" format
    manufacturer VARCHAR(50) DEFAULT 'Fleximodo' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- 2. Tabla de historial de estados
CREATE TABLE IF NOT EXISTS sensor_status_history (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES individual_sensors(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('free', 'busy', 'error', 'unknown', 'notcalib')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER CHECK (battery_capacity >= 0 AND battery_capacity <= 100),
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    radar_only BOOLEAN DEFAULT FALSE,
    raw_data JSONB,
    change_source VARCHAR(20) DEFAULT 'push' CHECK (change_source IN ('push', 'manual', 'system')),
    user_id INTEGER REFERENCES users(id), -- Para cambios manuales
    reason TEXT -- Motivo del cambio manual
);

-- 3. Tabla de estado actual
CREATE TABLE IF NOT EXISTS sensor_current_status (
    sensor_id INTEGER PRIMARY KEY REFERENCES individual_sensors(id) ON DELETE CASCADE,
    current_status VARCHAR(20) NOT NULL CHECK (current_status IN ('free', 'busy', 'error', 'unknown', 'notcalib')),
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER CHECK (battery_capacity >= 0 AND battery_capacity <= 100),
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    consecutive_errors INTEGER DEFAULT 0,
    last_successful_ping TIMESTAMP WITH TIME ZONE,
    last_manual_update TIMESTAMP WITH TIME ZONE,
    last_manual_update_by INTEGER REFERENCES users(id)
);

-- 4. Tabla de resumen por parking
CREATE TABLE IF NOT EXISTS parking_sensor_summary (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
    sensor_type VARCHAR(20) NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    total_sensors INTEGER DEFAULT 0,
    free_sensors INTEGER DEFAULT 0,
    busy_sensors INTEGER DEFAULT 0,
    error_sensors INTEGER DEFAULT 0,
    unknown_sensors INTEGER DEFAULT 0,
    notcalib_sensors INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parking_id, sensor_type)
);

-- 5. Verificar creación de tablas
\dt individual_sensors
\dt sensor_status_history
\dt sensor_current_status
\dt parking_sensor_summary

COMMIT;
```

#### 1.3 Creación de Índices y Optimizaciones (1 hora)

```sql
-- Continuar en la misma sesión de psql

-- Índices para individual_sensors
CREATE INDEX IF NOT EXISTS idx_individual_sensors_parking_id ON individual_sensors(parking_id);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_type ON individual_sensors(sensor_type);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_active ON individual_sensors(is_active);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_serial ON individual_sensors(serial_number);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_name ON individual_sensors(name);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_created_at ON individual_sensors(created_at);

-- Índices para sensor_status_history
CREATE INDEX IF NOT EXISTS idx_sensor_status_sensor_id ON sensor_status_history(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensor_status_timestamp ON sensor_status_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_status_current ON sensor_status_history(sensor_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_status_source ON sensor_status_history(change_source);
CREATE INDEX IF NOT EXISTS idx_sensor_status_user ON sensor_status_history(user_id);

-- Índices para parking_sensor_summary
CREATE INDEX IF NOT EXISTS idx_parking_sensor_summary_parking ON parking_sensor_summary(parking_id);
CREATE INDEX IF NOT EXISTS idx_parking_sensor_summary_type ON parking_sensor_summary(sensor_type);
CREATE INDEX IF NOT EXISTS idx_parking_sensor_summary_update ON parking_sensor_summary(last_update);

-- Crear función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a individual_sensors
CREATE TRIGGER update_individual_sensors_updated_at 
    BEFORE UPDATE ON individual_sensors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verificar índices creados
\di idx_individual_sensors*
\di idx_sensor_status*
\di idx_parking_sensor*

COMMIT;
```

#### 1.4 Inserción de Datos de Ejemplo y Validación (2 horas)

```sql
-- Continuar en la misma sesión de psql

-- Insertar datos de ejemplo para testing
INSERT INTO individual_sensors (serial_number, name, sensor_type, description, created_by) VALUES
('FLX001001', 'Plaza PMR-01', 'PMR', 'Sensor PMR entrada principal - EJEMPLO', 1),
('FLX001002', 'Plaza ELE-01', 'Electrico', 'Plaza eléctrica zona A - EJEMPLO', 1),
('FLX001003', 'Plaza PMR-02', 'PMR', 'Sensor PMR zona B - EJEMPLO', 1),
('FLX001004', 'Plaza CAR-01', 'Caravanas', 'Plaza para caravanas - EJEMPLO', 1),
('FLX001005', 'Plaza EME-01', 'Emergencias', 'Plaza de emergencias - EJEMPLO', 1)
ON CONFLICT (serial_number) DO NOTHING;

-- Insertar estados iniciales
INSERT INTO sensor_current_status (sensor_id, current_status, battery_capacity, temperature)
SELECT id, 'unknown', 85, 22.5 FROM individual_sensors
ON CONFLICT (sensor_id) DO NOTHING;

-- Crear resúmenes iniciales por parking (asumiendo parking_id = 1 para ejemplos)
UPDATE individual_sensors SET parking_id = 1 WHERE parking_id IS NULL;

INSERT INTO parking_sensor_summary (parking_id, sensor_type, total_sensors, free_sensors, busy_sensors, error_sensors, unknown_sensors)
SELECT 1, sensor_type, COUNT(*), 0, 0, 0, COUNT(*)
FROM individual_sensors 
WHERE parking_id = 1 
GROUP BY sensor_type
ON CONFLICT (parking_id, sensor_type) DO UPDATE SET
    total_sensors = EXCLUDED.total_sensors,
    unknown_sensors = EXCLUDED.unknown_sensors,
    last_update = NOW();

-- Validaciones finales
SELECT 'Panels con nuevos campos' as tabla, COUNT(*) as registros 
FROM panels 
WHERE last_message_window_0 IS NOT NULL OR window_config_json IS NOT NULL

UNION ALL

SELECT 'Individual sensors' as tabla, COUNT(*) as registros 
FROM individual_sensors

UNION ALL

SELECT 'Sensor current status' as tabla, COUNT(*) as registros 
FROM sensor_current_status

UNION ALL

SELECT 'Parking sensor summary' as tabla, COUNT(*) as registros 
FROM parking_sensor_summary;

-- Verificar integridad referencial
SELECT 
    'Sensores sin estado actual' as check_name,
    COUNT(*) as count
FROM individual_sensors s
LEFT JOIN sensor_current_status scs ON s.id = scs.sensor_id
WHERE scs.sensor_id IS NULL

UNION ALL

SELECT 
    'Paneles con config de ventanas' as check_name,
    COUNT(*) as count
FROM panels 
WHERE window_config_json IS NOT NULL;

-- Mostrar resumen de la migración
SELECT 
    'MIGRACIÓN COMPLETADA' as status,
    NOW() as timestamp,
    'Base de datos actualizada para v4.1.0' as message;

COMMIT;

-- Salir de psql
\q
```

### Criterios de Aceptación Fase 1
- ⏳ Tabla `panels` actualizada con campos para ventanas 0 y 1
- ✅ Tablas de sensores individuales creadas correctamente
- ✅ Índices de optimización aplicados
- ⏳ Datos de ejemplo insertados y validados
- ✅ Integridad referencial verificada
- ⏳ Triggers de actualización automática funcionando

### 🔄 **PRÓXIMOS PASOS PARA COMPLETAR FASE 1:**

**1. Actualizar tabla panels (continuar en la sesión psql actual):**
```sql
-- Añadir campos para almacenar último mensaje por ventana
ALTER TABLE panels 
ADD COLUMN IF NOT EXISTS last_message_window_0 TEXT,
ADD COLUMN IF NOT EXISTS last_message_window_1 TEXT,
ADD COLUMN IF NOT EXISTS last_update_window_0 TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_update_window_1 TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS window_config_json JSONB DEFAULT '{"windows": [{"id": 0, "enabled": true}, {"id": 1, "enabled": false}]}'::jsonb;

-- Migrar datos existentes (mover last_message a window_0)
UPDATE panels 
SET last_message_window_0 = last_message,
    last_update_window_0 = last_update
WHERE last_message IS NOT NULL;

-- Crear índices para optimización
CREATE INDEX IF NOT EXISTS idx_panels_window_0_update ON panels(last_update_window_0);
CREATE INDEX IF NOT EXISTS idx_panels_window_1_update ON panels(last_update_window_1);
CREATE INDEX IF NOT EXISTS idx_panels_window_config ON panels USING GIN(window_config_json);
```

**2. Insertar datos de ejemplo:**
```sql
-- Insertar sensores de ejemplo
INSERT INTO individual_sensors (serial_number, name, sensor_type, description) VALUES
('FLX001001', 'Plaza PMR-01', 'PMR', 'Sensor PMR entrada principal - EJEMPLO'),
('FLX001002', 'Plaza ELE-01', 'Electrico', 'Plaza eléctrica zona A - EJEMPLO'),
('FLX001003', 'Plaza PMR-02', 'PMR', 'Sensor PMR zona B - EJEMPLO'),
('FLX001004', 'Plaza CAR-01', 'Caravanas', 'Plaza para caravanas - EJEMPLO'),
('FLX001005', 'Plaza EME-01', 'Emergencias', 'Plaza de emergencias - EJEMPLO')
ON CONFLICT (serial_number) DO NOTHING;

-- Insertar estados iniciales
INSERT INTO sensor_current_status (sensor_id, current_status, battery_capacity, temperature)
SELECT id, 'unknown', 85, 22.5 FROM individual_sensors
ON CONFLICT (sensor_id) DO NOTHING;
```

**3. Crear trigger de actualización automática:**
```sql
-- Crear función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a individual_sensors
CREATE TRIGGER update_individual_sensors_updated_at 
    BEFORE UPDATE ON individual_sensors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**4. Optimizaciones de rendimiento (RECOMENDADO):**
```sql
-- VISTA MATERIALIZADA: Estado completo de parkings
CREATE MATERIALIZED VIEW parking_complete_status AS
SELECT 
    p.id as parking_id,
    p.name as parking_name,
    p.location,
    p.max_capacity,
    p.current_occupancy,
    p.status,
    
    -- Conteo de paneles
    COUNT(DISTINCT pan.id) as total_panels,
    COUNT(DISTINCT CASE WHEN pan.status = 'online' THEN pan.id END) as online_panels,
    
    -- Conteo de sensores individuales
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'PMR' THEN s.id END) as pmr_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Electrico' THEN s.id END) as electric_sensors,
    COUNT(DISTINCT CASE WHEN s.sensor_type = 'Caravanas' THEN s.id END) as caravan_sensors,
    
    -- Estados de sensores
    COUNT(DISTINCT CASE WHEN scs.current_status = 'free' THEN s.id END) as free_individual_sensors,
    COUNT(DISTINCT CASE WHEN scs.current_status = 'busy' THEN s.id END) as busy_individual_sensors,
    COUNT(DISTINCT CASE WHEN scs.current_status = 'error' THEN s.id END) as error_individual_sensors,
    
    -- Información de batería
    AVG(CASE WHEN scs.battery_capacity IS NOT NULL THEN scs.battery_capacity END) as avg_battery_level,
    COUNT(DISTINCT CASE WHEN scs.battery_capacity < 20 THEN s.id END) as low_battery_sensors,
    
    NOW() as view_updated_at
    
FROM parkings p
LEFT JOIN panels pan ON pan.parking_id = p.id AND pan.is_active = true
LEFT JOIN individual_sensors s ON s.parking_id = p.id AND s.is_active = true
LEFT JOIN sensor_current_status scs ON scs.sensor_id = s.id
GROUP BY p.id, p.name, p.location, p.max_capacity, p.current_occupancy, p.status;

-- Índices para la vista
CREATE UNIQUE INDEX idx_parking_complete_status_parking_id 
ON parking_complete_status(parking_id);

-- FUNCIÓN: Acceso rápido a estado de parking
CREATE OR REPLACE FUNCTION get_parking_quick_status(parking_id_param INTEGER)
RETURNS TABLE (
    parking_id INTEGER,
    parking_name VARCHAR,
    total_panels BIGINT,
    total_sensors BIGINT,
    free_sensors BIGINT,
    busy_sensors BIGINT,
    error_sensors BIGINT,
    avg_battery NUMERIC,
    occupancy_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pcs.parking_id,
        pcs.parking_name,
        pcs.total_panels,
        (pcs.pmr_sensors + pcs.electric_sensors + pcs.caravan_sensors) as total_sensors,
        pcs.free_individual_sensors,
        pcs.busy_individual_sensors,
        pcs.error_individual_sensors,
        ROUND(pcs.avg_battery_level, 1),
        CASE 
            WHEN (pcs.pmr_sensors + pcs.electric_sensors + pcs.caravan_sensors) > 0
            THEN ROUND((pcs.busy_individual_sensors::NUMERIC / (pcs.pmr_sensors + pcs.electric_sensors + pcs.caravan_sensors)::NUMERIC) * 100, 2)
            ELSE 0 
        END as occupancy_rate
    FROM parking_complete_status pcs
    WHERE pcs.parking_id = parking_id_param;
END;
$$ LANGUAGE plpgsql;

-- FUNCIÓN: Refrescar vistas (para usar en cron)
CREATE OR REPLACE FUNCTION refresh_parking_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW parking_complete_status;
    INSERT INTO system_logs (level, message, timestamp) 
    VALUES ('INFO', 'Vistas materializadas actualizadas', NOW())
    ON CONFLICT DO NOTHING;
END;
$$ LANGUAGE plpgsql;
```

**5. Validación final:**
```sql
-- Verificar tablas creadas
SELECT 'Panels actualizados' as tabla, COUNT(*) as registros 
FROM panels 
WHERE window_config_json IS NOT NULL

UNION ALL

SELECT 'Sensores individuales' as tabla, COUNT(*) as registros 
FROM individual_sensors

UNION ALL

SELECT 'Estados actuales' as tabla, COUNT(*) as registros 
FROM sensor_current_status

UNION ALL

SELECT 'Vista materializada' as tabla, COUNT(*) as registros 
FROM parking_complete_status;

-- Test de función rápida (usar ID de parking existente)
SELECT * FROM get_parking_quick_status(1);

-- Mostrar resumen
SELECT 
    'FASE 1 COMPLETADA' as status,
    NOW() as timestamp,
    'Base de datos optimizada para v4.1.0' as message;
```

---

## FASE 2: BACKEND - GESTIÓN DE PANELES
**Duración**: 2 días (10 horas)  
**Progreso**: 100% (10/10 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 2.1 | Actualizar modelos Python para ventanas | 2h | 100% | ✅ Completado | Backend |
| 2.2 | Modificar API endpoints de paneles | 3h | 100% | ✅ Completado | Backend |
| 2.3 | Implementar lógica de selección de ventana | 3h | 100% | ✅ Completado | Backend |
| 2.4 | Validaciones y compatibilidad | 2h | 100% | ✅ Completado | Backend |

### ✅ **RESULTADOS IMPLEMENTADOS:**
- **Modelos actualizados**: Campos `window_0/1`, métodos `supports_multiple_windows()`
- **API mejorado**: Parámetro `window`, validaciones robustas
- **Nuevos endpoints**: `/panels/{id}/windows`, `/panels/{id}/validate`
- **Servicio comunicación**: `send_custom_text_to_window()` para Tipo 3
- **Rebrand completado**: SWATID en lugar de Parking Altea
- **Validaciones**: Longitud mensaje, colores, fuentes, capacidades panel

### Criterios de Aceptación Fase 2
- ✅ Modelos actualizados para soportar múltiples ventanas
- ✅ API acepta parámetro `window` en endpoints de mensaje
- ✅ Validación de ventana según tipo de panel
- ✅ Retrocompatibilidad mantenida

---

## FASE 3: FRONTEND - GESTIÓN DE PANELES
**Duración**: 1 día (4 horas)  
**Progreso**: 100% (4/4 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 3.1 | Agregar selector de ventana en modal | 2h | 100% | ✅ Completado | Frontend |
| 3.2 | Detectar paneles Tipo 3 automáticamente | 1h | 100% | ✅ Completado | Frontend |
| 3.3 | Testing y validación UI | 1h | 100% | ✅ Completado | Frontend |

### ✅ **RESULTADOS IMPLEMENTADOS:**
- **Selector inteligente**: Radio buttons para Ventana 0/1 (solo Tipo 3)
- **Detección automática**: Campo `supports_multiple_windows` del backend
- **APIs integrados**: `validatePanelMessage()`, `getPanelWindowsInfo()`
- **Modal validación**: Errores, warnings y confirmación antes envío
- **Tabla mejorada**: Nueva columna "Ventanas" con badges visuales
- **UX optimizado**: Flujo Validar → Revisar → Enviar

### Criterios de Aceptación Fase 3
- ✅ Selector de ventana aparece solo para paneles Tipo 3
- ✅ Interfaz es intuitiva y fácil de usar
- ✅ Mensajes se envían a la ventana seleccionada

---

## FASE 4: BACKEND - SISTEMA SENSORES INDIVIDUALES
**Duración**: 3 días (15 horas)  
**Progreso**: 100% (15/15 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 4.1 | Implementar modelos SQLAlchemy | 3h | 100% | ✅ Completado | Backend |
| 4.2 | Crear endpoints CRUD sensores | 4h | 100% | ✅ Completado | Backend |
| 4.3 | Endpoints de consulta y resúmenes | 3h | 100% | ✅ Completado | Backend |
| 4.4 | Sistema de autenticación y permisos | 2h | 100% | ✅ Completado | Backend |
| 4.5 | Servicios de actualización de estados | 2h | 100% | ✅ Completado | Backend |
| 4.6 | Endpoints para página de parking | 1h | 100% | ✅ Completado | Backend |

### ✅ **RESULTADOS IMPLEMENTADOS:**
- **4 Modelos Python**: IndividualSensor, SensorStatusHistory, SensorCurrentStatus, ParkingSensorSummary
- **APIs CRUD completas**: GET, POST, PUT, DELETE con validaciones robustas
- **Endpoints agrupación**: /sensors/summary, /sensors/status/complete, /sensors/status/grouped
- **Actualización manual**: PUT /sensors/{id}/status con historial automático
- **Propiedades inteligentes**: is_online, needs_attention, battery_info, occupancy_rate
- **Validaciones**: tipos de sensor, estados, serial numbers únicos, autenticación
- **Optimizaciones**: fallback queries, vistas materializadas, funciones auxiliares

### Criterios de Aceptación Fase 4
- ✅ CRUD completo de sensores individuales
- ✅ Consultas por parking funcionando
- ✅ Autenticación y permisos correctos
- ✅ Servicios de actualización de estados operativos

---

## FASE 8: SERVICIO PUSH DE SENSORES
**Duración**: 4 días (33 horas)  
**Progreso**: 100% (33/33 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 8.1 | Crear servicio Flask base | 6h | 100% | ✅ Completado | Backend |
| 8.2 | Implementar procesamiento de push | 8h | 100% | ✅ Completado | Backend |
| 8.3 | Endpoint actualización manual | 4h | 100% | ✅ Completado | Backend |
| 8.4 | Middleware y seguridad | 4h | 100% | ✅ Completado | Backend |
| 8.5 | Métricas y monitorización | 4h | 100% | ✅ Completado | Backend |
| 8.6 | Scripts de despliegue | 3h | 100% | ✅ Completado | DevOps |
| 8.7 | Testing completo | 4h | 100% | ✅ Completado | QA |

### ✅ **RESULTADOS IMPLEMENTADOS:**
- **sensor_push_service.py**: Servicio Flask completo puerto 3535
- **SensorPushProcessor**: Clase procesamiento CarparkSlotStatusBody
- **Endpoints REST**: /push, /manual-update, /health, /stats
- **Validación robusta**: Estructura mensajes + estados válidos
- **Base de datos**: Integración SQLAlchemy + actualización automática
- **Logging**: Sistema estructurado + configuración por variables entorno
- **Despliegue**: parking-sensor-push.service + script automático
- **Testing**: Suite completa validación + integración

### Criterios de Aceptación Fase 8
- ✅ Servicio en puerto 3535 operativo
- ✅ Procesamiento de push funcionando
- ✅ Actualización manual implementada
- ✅ Métricas y monitorización activas

---

## FASE 5: FRONTEND - GESTIÓN SENSORES INDIVIDUALES
**Duración**: 2.5 días (12 horas)  
**Progreso**: 100% (12/12 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 5.1 | Página principal gestión sensores | 3h | 100% | ✅ Completado | Frontend |
| 5.2 | Formularios CRUD | 2h | 100% | ✅ Completado | Frontend |
| 5.3 | Dashboard estados básico | 2h | 100% | ✅ Completado | Frontend |
| 5.4 | Sistema de filtros y búsquedas | 2h | 100% | ✅ Completado | Frontend |
| 5.5 | Integración con API backend | 2h | 100% | ✅ Completado | Frontend |
| 5.6 | Testing y validación UI | 1h | 100% | ✅ Completado | Frontend |

### ✅ **RESULTADOS IMPLEMENTADOS:**
- **Página completa**: /sensors con diseño consistente y look&feel del sistema
- **sensorService.js**: 15 métodos API + utilidades de formateo
- **Formularios CRUD**: Crear, editar, eliminar con validaciones
- **Dashboard tiempo real**: Estadísticas, filtros, búsqueda
- **Modales reutilizables**: EditSensorModal, StatusUpdateModal, SensorDetailModal
- **Actualización manual**: Estados, batería, temperatura con historial
- **Navegación integrada**: Icono Cpu en menú principal
- **UX avanzado**: Loading states, toast notifications, permisos por rol

### Criterios de Aceptación Fase 6
- ✅ Gestión completa de sensores desde interfaz
- ✅ Estados en tiempo real
- ✅ Filtros y búsquedas funcionando
- ✅ Interfaz intuitiva y responsiva

---

## FASE 6: INTEGRACIÓN PÁGINA DETALLE PARKING
**Duración**: 1 día (8 horas)  
**Progreso**: 100% (8/8 horas)  
**Estado**: ✅ **COMPLETADA**

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 6.1 | Componente sección sensores | 3h | 100% | ✅ Completado | Frontend |
| 6.2 | Vista agrupada por tipos | 2h | 100% | ✅ Completado | Frontend |
| 6.3 | Modal actualización manual | 2h | 100% | ✅ Completado | Frontend |
| 6.4 | Integración tiempo real | 1h | 100% | ✅ Completado | Frontend |

### ✅ **RESULTADOS IMPLEMENTADOS:**
- **ParkingSensorSection.jsx**: Componente completo integrado en ParkingDetail
- **Vista agrupada**: Sensores organizados por tipo (PMR, Eléctrico, etc.) con expansión
- **Cards resumen**: Total, libres, ocupados, batería baja con iconografía
- **Lista detallada**: Estado, batería, timestamp por sensor individual
- **Actualización manual**: Modal integrado para cambio estado desde parking
- **Auto-refresh**: Sincronización cada 30s con datos backend
- **Navegación**: Botón "Gestionar" abre página /sensors completa

### Criterios de Aceptación Fase 6
- ✅ Sensores mostrados por tipo en página parking
- ✅ Información detallada visible (batería, timestamp)
- ✅ Actualización manual funcional
- ✅ Auto-refresh cada 30 segundos

---

## FASE 8: DASHBOARD Y ESTADÍSTICAS
**Duración**: 2 días (12 horas)  
**Progreso**: 0% (0/12 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 7 completada

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 8.1 | Gráficos de ocupación | 4h | 0% | ⏳ Pendiente | Frontend |
| 8.2 | Estadísticas históricas | 4h | 0% | ⏳ Pendiente | Frontend |
| 8.3 | Alertas visuales | 2h | 0% | ⏳ Pendiente | Frontend |
| 8.4 | Reportes básicos | 2h | 0% | ⏳ Pendiente | Frontend |

### Criterios de Aceptación Fase 8
- ✅ Gráficos actualizados en tiempo real
- ✅ Estadísticas precisas
- ✅ Alertas para sensores problemáticos
- ✅ Reportes descargables

---

## FASE 9: TESTING Y FINALIZACIÓN
**Duración**: 1 día (8 horas)  
**Progreso**: 0% (0/8 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Todas las fases anteriores

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 9.1 | Testing integración completa | 4h | 0% | ⏳ Pendiente | QA |
| 9.2 | Optimizaciones rendimiento | 2h | 0% | ⏳ Pendiente | Backend |
| 9.3 | Documentación final | 1h | 0% | ⏳ Pendiente | Docs |
| 9.4 | Preparación despliegue | 1h | 0% | ⏳ Pendiente | DevOps |

### Criterios de Aceptación Fase 9
- ✅ Todos los tests pasan
- ✅ Rendimiento optimizado
- ✅ Documentación completa
- ✅ Listo para despliegue

---

## CRONOGRAMA GENERAL

### Semana 1 (40 horas)
- **Día 1**: Fase 1 - Actualización BD (8h) ✅ 100%
- **Días 2-3**: Fase 2 - Backend Paneles (10h) + Fase 3 - Frontend Paneles (4h)
- **Días 4-5**: Fase 4 - Backend Sensores (16h de 32h)

### Semana 2 (40 horas)
- **Días 1-2**: Fase 4 - Backend Sensores (16h restantes)
- **Días 3-5**: Fase 5 - Servicio Push (24h de 37h)

### Semana 3 (40 horas)
- **Día 1**: Fase 5 - Servicio Push (13h restantes)
- **Días 2-4**: Fase 6 - Frontend Sensores (24h de 28h)
- **Día 5**: Fase 6 - Frontend Sensores (4h restantes) + Fase 7 - Integración (10h de 14h)

### Día Final (8 horas)
- **Mañana**: Fase 7 - Integración (4h restantes) + Fase 8 - Dashboard (4h de 12h)
- **Tarde**: Fase 8 - Dashboard (8h restantes) + Fase 9 - Testing (8h)

---

## MÉTRICAS DE SEGUIMIENTO

### Por Fase
- **Completadas**: 7/9 fases (78%)
- **En progreso**: 0/9 fases (0%)
- **Pendientes**: 2/9 fases (22%)

### Por Horas
- **Completadas**: 90/124 horas (72.6%)
- **En progreso**: 0/124 horas (0%)
- **Pendientes**: 34/124 horas (27.4%)

### Por Funcionalidad
- **Gestión Paneles**: 14/14 horas (100%)
- **Sensores Individuales**: 55/55 horas (100%)
- **Servicio Push**: 33/33 horas (100%)

---

## INSTRUCCIONES DE ACTUALIZACIÓN

### Después de Cada Iteración:
1. Actualizar el progreso de las tareas completadas
2. Cambiar estado de ⏳ Pendiente a 🟡 En progreso o ✅ Completado
3. Actualizar porcentajes de cada fase
4. Recalcular métricas generales
5. Añadir notas sobre problemas encontrados
6. Actualizar estimaciones si es necesario

### Estados Posibles:
- ⏳ **Pendiente**: No iniciado
- 🟡 **En progreso**: Iniciado pero no completado
- ✅ **Completado**: Finalizado y validado
- ❌ **Bloqueado**: No puede continuar por dependencias
- ⚠️ **Con problemas**: Necesita atención

---

## CONTACTOS Y RESPONSABLES

- **Backend**: Desarrollador Python/Flask/SQLAlchemy
- **Frontend**: Desarrollador React/JavaScript
- **DevOps**: Administrador sistemas y despliegue
- **QA**: Testing y validación
- **Docs**: Documentación técnica

---

*Documento de seguimiento v4.1.0 - Actualizado: 19/09/2025*  
*Próxima actualización: Después de completar Fase 1*
