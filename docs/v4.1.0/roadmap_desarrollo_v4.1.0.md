# Roadmap de Desarrollo v4.1.0 - Sistema de Gestión de Parking

## Estado General del Proyecto
- **Versión**: 4.1.0
- **Fecha de inicio**: 19/09/2025
- **Estimación total**: 121 horas (15 días laborables)
- **Progreso general**: 0% (0/121 horas completadas)

## Resumen de Funcionalidades

### 1. Gestión de Paneles - Selección de Ventanas (10h)
- **Progreso**: 0% (0/10 horas)
- **Prioridad**: Media
- **Descripción**: Permitir selección de ventana 0 o 1 en paneles Tipo 3

### 2. Sistema de Plazas Individuales PMR (74h)
- **Progreso**: 0% (0/74 horas)
- **Prioridad**: Alta
- **Descripción**: Sistema completo de gestión de sensores individuales

### 3. Servicio Push de Sensores (37h)
- **Progreso**: 0% (0/37 horas)
- **Prioridad**: Alta
- **Descripción**: Servicio en puerto 3535 para recepción de push de sensores

---

## FASE 1: ACTUALIZACIÓN DE BASE DE DATOS
**Duración**: 1 día (8 horas)  
**Progreso**: 0% (0/8 horas)  
**Estado**: ⏳ Pendiente

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 1.1 | Actualizar tabla panels para ventanas | 2h | 0% | ⏳ Pendiente | Backend |
| 1.2 | Crear tablas sensores individuales | 3h | 0% | ⏳ Pendiente | Backend |
| 1.3 | Crear índices y optimizaciones | 1h | 0% | ⏳ Pendiente | Backend |
| 1.4 | Ejecutar migración y validar | 2h | 0% | ⏳ Pendiente | Backend |

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
- ✅ Tabla `panels` actualizada con campos para ventanas 0 y 1
- ✅ Tablas de sensores individuales creadas correctamente
- ✅ Índices de optimización aplicados
- ✅ Datos de ejemplo insertados y validados
- ✅ Integridad referencial verificada
- ✅ Triggers de actualización automática funcionando

---

## FASE 2: BACKEND - GESTIÓN DE PANELES
**Duración**: 2 días (10 horas)  
**Progreso**: 0% (0/10 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 1 completada

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 2.1 | Actualizar modelos Python para ventanas | 2h | 0% | ⏳ Pendiente | Backend |
| 2.2 | Modificar API endpoints de paneles | 3h | 0% | ⏳ Pendiente | Backend |
| 2.3 | Implementar lógica de selección de ventana | 3h | 0% | ⏳ Pendiente | Backend |
| 2.4 | Validaciones y compatibilidad | 2h | 0% | ⏳ Pendiente | Backend |

### Criterios de Aceptación Fase 2
- ✅ Modelos actualizados para soportar múltiples ventanas
- ✅ API acepta parámetro `window` en endpoints de mensaje
- ✅ Validación de ventana según tipo de panel
- ✅ Retrocompatibilidad mantenida

---

## FASE 3: FRONTEND - GESTIÓN DE PANELES
**Duración**: 1 día (4 horas)  
**Progreso**: 0% (0/4 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 2 completada

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 3.1 | Agregar selector de ventana en modal | 2h | 0% | ⏳ Pendiente | Frontend |
| 3.2 | Detectar paneles Tipo 3 automáticamente | 1h | 0% | ⏳ Pendiente | Frontend |
| 3.3 | Testing y validación UI | 1h | 0% | ⏳ Pendiente | Frontend |

### Criterios de Aceptación Fase 3
- ✅ Selector de ventana aparece solo para paneles Tipo 3
- ✅ Interfaz es intuitiva y fácil de usar
- ✅ Mensajes se envían a la ventana seleccionada

---

## FASE 4: BACKEND - SISTEMA SENSORES INDIVIDUALES
**Duración**: 4 días (32 horas)  
**Progreso**: 0% (0/32 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 1 completada

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 4.1 | Implementar modelos SQLAlchemy | 4h | 0% | ⏳ Pendiente | Backend |
| 4.2 | Crear endpoints CRUD sensores | 8h | 0% | ⏳ Pendiente | Backend |
| 4.3 | Endpoints de consulta y resúmenes | 6h | 0% | ⏳ Pendiente | Backend |
| 4.4 | Sistema de autenticación y permisos | 4h | 0% | ⏳ Pendiente | Backend |
| 4.5 | Servicios de actualización de estados | 6h | 0% | ⏳ Pendiente | Backend |
| 4.6 | Endpoints para página de parking | 4h | 0% | ⏳ Pendiente | Backend |

### Criterios de Aceptación Fase 4
- ✅ CRUD completo de sensores individuales
- ✅ Consultas por parking funcionando
- ✅ Autenticación y permisos correctos
- ✅ Servicios de actualización de estados operativos

---

## FASE 5: SERVICIO PUSH DE SENSORES
**Duración**: 5 días (37 horas)  
**Progreso**: 0% (0/37 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 4 completada

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 5.1 | Crear servicio Flask base | 6h | 0% | ⏳ Pendiente | Backend |
| 5.2 | Implementar procesamiento de push | 8h | 0% | ⏳ Pendiente | Backend |
| 5.3 | Endpoint actualización manual | 4h | 0% | ⏳ Pendiente | Backend |
| 5.4 | Middleware y seguridad | 4h | 0% | ⏳ Pendiente | Backend |
| 5.5 | Métricas y monitorización | 4h | 0% | ⏳ Pendiente | Backend |
| 5.6 | Scripts de despliegue | 3h | 0% | ⏳ Pendiente | DevOps |
| 5.7 | Testing completo | 6h | 0% | ⏳ Pendiente | QA |
| 5.8 | Documentación API | 2h | 0% | ⏳ Pendiente | Docs |

### Criterios de Aceptación Fase 5
- ✅ Servicio en puerto 3535 operativo
- ✅ Procesamiento de push funcionando
- ✅ Actualización manual implementada
- ✅ Métricas y monitorización activas

---

## FASE 6: FRONTEND - GESTIÓN SENSORES INDIVIDUALES
**Duración**: 4 días (28 horas)  
**Progreso**: 0% (0/28 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 4 completada

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 6.1 | Página principal gestión sensores | 8h | 0% | ⏳ Pendiente | Frontend |
| 6.2 | Formularios CRUD | 6h | 0% | ⏳ Pendiente | Frontend |
| 6.3 | Dashboard estados básico | 4h | 0% | ⏳ Pendiente | Frontend |
| 6.4 | Sistema de filtros y búsquedas | 4h | 0% | ⏳ Pendiente | Frontend |
| 6.5 | Integración con API backend | 4h | 0% | ⏳ Pendiente | Frontend |
| 6.6 | Testing y validación UI | 2h | 0% | ⏳ Pendiente | Frontend |

### Criterios de Aceptación Fase 6
- ✅ Gestión completa de sensores desde interfaz
- ✅ Estados en tiempo real
- ✅ Filtros y búsquedas funcionando
- ✅ Interfaz intuitiva y responsiva

---

## FASE 7: INTEGRACIÓN PÁGINA DETALLE PARKING
**Duración**: 2 días (14 horas)  
**Progreso**: 0% (0/14 horas)  
**Estado**: ⏳ Pendiente  
**Dependencias**: Fase 5 y 6 completadas

### Tareas Específicas

| ID | Tarea | Estimación | Progreso | Estado | Responsable |
|----|-------|------------|----------|--------|-------------|
| 7.1 | Componente sección sensores | 6h | 0% | ⏳ Pendiente | Frontend |
| 7.2 | Modal actualización manual | 3h | 0% | ⏳ Pendiente | Frontend |
| 7.3 | Integración tiempo real | 3h | 0% | ⏳ Pendiente | Frontend |
| 7.4 | Testing integración completa | 2h | 0% | ⏳ Pendiente | QA |

### Criterios de Aceptación Fase 7
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
- **Completadas**: 0/9 fases (0%)
- **En progreso**: 0/9 fases (0%)
- **Pendientes**: 9/9 fases (100%)

### Por Horas
- **Completadas**: 0/121 horas (0%)
- **En progreso**: 0/121 horas (0%)
- **Pendientes**: 121/121 horas (100%)

### Por Funcionalidad
- **Gestión Paneles**: 0/14 horas (0%)
- **Sensores Individuales**: 0/70 horas (0%)
- **Servicio Push**: 0/37 horas (0%)

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
