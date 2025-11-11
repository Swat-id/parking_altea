# Análisis Previo: Migración Paneles Tipo 4 y Configuración de Ventanas

**Fecha:** 2025-11-10  
**Versión:** v4.3.0  
**Estado:** Análisis Previo - Pendiente de Ejecución

---

## 📋 RESUMEN EJECUTIVO

Esta migración introduce el **Panel Tipo 4** con soporte para hasta **16 ventanas** (0-15), permite asignar parkings y **grupos de sensores agrupados por tipo** (PMR, Caravanas, Eléctrico) a ventanas específicas, e integra el nuevo protocolo de comunicación con paneles LED.

**IMPORTANTE:** Los sensores se gestionan **agrupados por tipo a nivel de parking** (usando `parking_sensor_summary`), no individualmente. Esto permite asignar, por ejemplo, "todos los sensores PMR del Parking 1" a una ventana, en lugar de sensores individuales.

---

## 🎯 OBJETIVOS PRINCIPALES

1. **Crear Panel Tipo 4** con soporte para 16 ventanas (0-15)
2. **Migración de Base de Datos** para soportar asignación de parkings y **grupos de sensores agrupados por tipo** a ventanas
3. **Integración del Protocolo de Paneles** desde `/docs/panel_protocol`
4. **Frontend: Configuración de Ventanas** con porcentajes de visibilidad y tiempo de refresco
5. **Compatibilidad Retroactiva** con paneles existentes (Tipos 1, 2, 3)
6. **Integración con `parking_sensor_summary`** para obtener datos de sensores agrupados por tipo

---

## 📊 ANÁLISIS DE LA SITUACIÓN ACTUAL

### Estructura Actual de Paneles

**Tabla `panels`:**
- `id`, `parking_id`, `name`, `ip`, `status`
- `panel_type_id` (FK a `panel_types`)
- `port`, `window_config` (JSON), `protocol_version`
- `last_message_window_0`, `last_message_window_1` (solo 2 ventanas)
- `window_config_json` (JSON)

**Tabla `panel_types`:**
- `id`, `manufacturer_id`, `name`, `description`
- `protocol_type` ('old', 'new')
- `windows_count` (actualmente máximo 2 para Tipo 3)
- `window_width`, `window_height`, `total_width`, `total_height`
- `port`, `service_endpoint`

**Relación Actual:**
- `Panel` → `Parking` (1:N) - Un panel pertenece a un parking
- `Panel` → `PanelType` (N:1) - Un panel tiene un tipo

### Estructura Actual de Sensores

**Tabla `individual_sensors`:**
- `id`, `serial_number`, `name`
- `sensor_type` ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
- `parking_id` (FK a `parkings`)

**Tabla `parking_sensor_summary`:**
- `parking_id`, `sensor_type` (UNIQUE constraint)
- `total_sensors`, `free_sensors`, `busy_sensors`, `error_sensors`
- **Agrupa sensores por tipo a nivel de parking**

**Relación Actual:**
- `IndividualSensor` → `Parking` (N:1) - Un sensor pertenece a un parking
- `ParkingSensorSummary` → `Parking` (N:1) - Resumen agrupado por tipo de sensor
- **NO HAY** relación directa entre sensores y paneles/ventanas
- **IMPORTANTE:** Los sensores se gestionan **agrupados por tipo a nivel de parking**, no individualmente

---

## 🔧 TRABAJOS A REALIZAR

### 1. MIGRACIÓN DE BASE DE DATOS

#### 1.1. Crear Panel Tipo 4

**Archivo:** `src/migrate_panel_type_4.py` (nuevo)

**Acciones:**
- Insertar nuevo `PanelType` con:
  - `name`: "Panel Tipo 4 - Protocolo Nuevo - 16 Ventanas"
  - `protocol_type`: "new"
  - `windows_count`: 16
  - `window_width`: 64 (o según especificaciones)
  - `window_height`: 8 (o según especificaciones)
  - `total_width`: 1024 (o según especificaciones)
  - `total_height`: 128 (o según especificaciones)
  - `port`: 5200
  - `service_endpoint`: `http://localhost:7110/api/v1/panels/send-text`

#### 1.2. Crear Tabla de Asignación Parking-Panel-Ventana

**Nueva Tabla:** `parking_panel_windows`

**IMPORTANTE:** Los sensores se asignan **agrupados por tipo a nivel de parking**, no individualmente. 
Los datos de sensores se obtienen de la tabla `parking_sensor_summary` que ya agrupa por tipo.

**Estructura:**
```sql
CREATE TABLE parking_panel_windows (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    panel_id INTEGER NOT NULL REFERENCES panels(id) ON DELETE CASCADE,
    window_id INTEGER NOT NULL CHECK (window_id >= 0 AND window_id <= 15),
    sensor_type VARCHAR(20) CHECK (sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros', NULL)),
    -- NULL = mostrar datos del parking (ocupación general)
    -- 'PMR' = mostrar sensores PMR agrupados del parking
    -- 'Electrico' = mostrar sensores Eléctricos agrupados del parking
    -- 'Caravanas' = mostrar sensores Caravanas agrupados del parking
    -- etc.
    display_type VARCHAR(20) DEFAULT 'parking' CHECK (display_type IN ('parking', 'sensor_group', 'mixed')),
    -- 'parking' = mostrar ocupación general del parking
    -- 'sensor_group' = mostrar resumen de sensores del tipo especificado
    -- 'mixed' = rotar entre parking y sensores
    priority INTEGER DEFAULT 0,  -- Para ordenar cuando hay múltiples asignaciones en la misma ventana
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(panel_id, window_id, parking_id, sensor_type)  -- Evitar duplicados
    -- Permite: mismo panel+ventana+parking con diferentes sensor_type
    -- Ejemplo: Panel 1, Ventana 0, Parking 1, NULL (parking) y Panel 1, Ventana 0, Parking 1, 'PMR'
);
```

**Índices:**
```sql
CREATE INDEX idx_parking_panel_windows_parking_id ON parking_panel_windows(parking_id);
CREATE INDEX idx_parking_panel_windows_panel_id ON parking_panel_windows(panel_id);
CREATE INDEX idx_parking_panel_windows_window_id ON parking_panel_windows(window_id);
CREATE INDEX idx_parking_panel_windows_sensor_type ON parking_panel_windows(sensor_type);
CREATE INDEX idx_parking_panel_windows_panel_window ON parking_panel_windows(panel_id, window_id);
```

**Casos de Uso:**
- **Panel 1 (tipo 4), Ventana 0:** Parking 1 (ocupación general) - `parking_id=1, sensor_type=NULL`
- **Panel 1 (tipo 4), Ventana 1:** Parking 1 PMR (sensores PMR agrupados) - `parking_id=1, sensor_type='PMR'`
- **Panel 2 (tipo 4), Ventana 0:** Parking 2 (ocupación general) - `parking_id=2, sensor_type=NULL`
- **Panel 2 (tipo 4), Ventana 0 (rotación):** Parking 2 PMR + Parking 2 Caravanas - Dos registros:
  - `parking_id=2, sensor_type='PMR'` (con configuración de rotación)
  - `parking_id=2, sensor_type='Caravanas'` (con configuración de rotación)

**Nota:** Los datos de sensores se obtienen de `parking_sensor_summary` que ya contiene:
- `total_sensors`, `free_sensors`, `busy_sensors`, `error_sensors` agrupados por tipo

#### 1.3. Crear Tabla de Configuración de Ventanas

**Nueva Tabla:** `panel_window_configurations`

**IMPORTANTE:** Esta tabla configura cómo se muestran los datos en una ventana específica de un panel.
Los datos de sensores se obtienen de `parking_sensor_summary` (agrupados por tipo).

**Estructura:**
```sql
CREATE TABLE panel_window_configurations (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    panel_id INTEGER NOT NULL REFERENCES panels(id) ON DELETE CASCADE,
    window_id INTEGER NOT NULL CHECK (window_id >= 0 AND window_id <= 15),
    company_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- NULL = usuario normal, ID = superadmin config para empresa
    -- Configuración de rotación cuando hay múltiples tipos en la misma ventana
    rotation_enabled BOOLEAN DEFAULT TRUE,
    rotation_order JSONB,  
    -- Ejemplo: [
    --   {"type": "parking", "percentage": 50, "sensor_type": null},
    --   {"type": "sensor_group", "percentage": 30, "sensor_type": "PMR"},
    --   {"type": "sensor_group", "percentage": 20, "sensor_type": "Caravanas"}
    -- ]
    -- Los porcentajes deben sumar 100
    refresh_time_seconds INTEGER DEFAULT 5 CHECK (refresh_time_seconds > 0),
    -- Tiempo total de ciclo de rotación en segundos
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(panel_id, window_id, parking_id)  -- Una configuración por panel/ventana/parking
);
```

**Índices:**
```sql
CREATE INDEX idx_panel_window_config_parking_id ON panel_window_configurations(parking_id);
CREATE INDEX idx_panel_window_config_panel_id ON panel_window_configurations(panel_id);
CREATE INDEX idx_panel_window_config_company_id ON panel_window_configurations(company_id);
CREATE INDEX idx_panel_window_config_window_id ON panel_window_configurations(window_id);
CREATE INDEX idx_panel_window_config_panel_window ON panel_window_configurations(panel_id, window_id);
```

**Casos de Uso:**
- **Parking 1, Panel 1, Ventana 0:** 
  - Rotación: 50% tiempo mostrar parking, 30% PMR, 20% Caravanas
  - Tiempo de refresco: 5 segundos (ciclo completo)
- **Parking 1, Panel 1, Ventana 0:** 
  - Tiempo de refresco: 3 segundos (más rápido)
- **Superadmin configura para toda la empresa:** 
  - `company_id` = ID empresa (aplica a todos los parkings de esa empresa)
- **Usuario configura solo sus parkings:** 
  - `company_id` = NULL (configuración individual por parking)

#### 1.4. Actualizar Tabla `panels`

**Modificaciones:**
```sql
-- Agregar campo para soportar hasta 16 ventanas
ALTER TABLE panels 
ADD COLUMN IF NOT EXISTS windows_count INTEGER DEFAULT 1 CHECK (windows_count >= 1 AND windows_count <= 16);

-- Actualizar paneles tipo 4 para tener 16 ventanas
UPDATE panels 
SET windows_count = 16 
WHERE panel_type_id = (SELECT id FROM panel_types WHERE name LIKE '%Tipo 4%' OR windows_count = 16);
```

#### 1.5. Integración con `parking_sensor_summary`

**IMPORTANTE:** Los datos de sensores se obtienen de la tabla `parking_sensor_summary` que ya agrupa los sensores por tipo a nivel de parking.

**Estructura de `parking_sensor_summary`:**
- `parking_id`: ID del parking
- `sensor_type`: Tipo de sensor ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
- `total_sensors`: Total de sensores de ese tipo en el parking
- `free_sensors`: Sensores libres
- `busy_sensors`: Sensores ocupados
- `error_sensors`: Sensores con error

**Consulta para obtener datos de sensores:**
```sql
SELECT 
    sensor_type,
    total_sensors,
    free_sensors,
    busy_sensors,
    error_sensors
FROM parking_sensor_summary
WHERE parking_id = :parking_id
  AND sensor_type = :sensor_type;
```

**Ejemplo de uso:**
- Para mostrar sensores PMR del Parking 1:
  - Consultar `parking_sensor_summary` donde `parking_id=1` y `sensor_type='PMR'`
  - Obtener `free_sensors` y `total_sensors`
  - Mostrar: "PMR: 5 libres / 10 totales"

#### 1.6. Migración de Datos Existentes

**Script de Migración:**
- Para paneles existentes (Tipos 1, 2, 3): Mantener compatibilidad
- Para paneles sin `panel_type_id`: Asignar Tipo 1 por defecto
- Crear registros en `parking_panel_windows` para paneles existentes:
  - Panel → Parking (ventana 0, `sensor_type=NULL`)
  - Si tiene ventana 1 configurada → crear registro adicional (ventana 1, `sensor_type=NULL`)

---

### 2. INTEGRACIÓN DEL PROTOCOLO DE PANELES

#### 2.1. Revisar Archivos en `/docs/panel_protocol`

**Archivos a Revisar:**
- `panel_protocol.py` (~67 KB)
- `panel_backend.py` (~28 KB)
- `panel_advanced.py` (~26 KB) - Opcional
- `INTEGRACION_BACKEND.md`
- `backend-integration.md`
- `README.md`

#### 2.2. Copiar Archivos a Ubicación Apropiada

**Ubicación Propuesta:**
```
src/
└── panel_protocol_v4/
    ├── __init__.py
    ├── protocol.py          (copiar desde panel_protocol.py)
    ├── backend.py           (copiar desde panel_backend.py)
    └── advanced.py          (copiar desde panel_advanced.py, opcional)
```

**O integrar en estructura existente:**
```
src/
└── panel_protocol/
    ├── __init__.py
    ├── constants.py         (existente)
    ├── packet_builder.py    (existente)
    ├── connection_pool.py   (existente)
    ├── panel_protocol_service.py  (existente)
    ├── protocol_v4.py       (nuevo - desde panel_protocol.py)
    ├── backend_v4.py        (nuevo - desde panel_backend.py)
    └── advanced_v4.py       (nuevo - desde panel_advanced.py, opcional)
```

**Decisión:** Integrar en estructura existente para mantener coherencia.

#### 2.3. Adaptar Protocolo a Estructura Actual

**Tareas:**
- Revisar compatibilidad entre protocolo nuevo y `panel_protocol_service.py`
- Crear adaptador si es necesario
- Integrar funciones de `panel_backend.py` en servicios existentes
- Mantener compatibilidad con protocolo antiguo (Tipos 1, 2, 3)

---

### 3. BACKEND: SERVICIOS Y API

#### 3.1. Crear Servicio de Gestión de Ventanas

**Archivo:** `src/panel_window_service.py` (nuevo)

**Funciones:**
- `assign_parking_to_window(panel_id, window_id, parking_id, sensor_type=None)`
  - `sensor_type=None`: Asignar ocupación general del parking
  - `sensor_type='PMR'`: Asignar sensores PMR agrupados del parking (desde `parking_sensor_summary`)
  - `sensor_type='Electrico'`: Asignar sensores Eléctricos agrupados del parking
  - `sensor_type='Caravanas'`: Asignar sensores Caravanas agrupados del parking
- `get_window_assignments(panel_id)` - Obtener todas las asignaciones de un panel
- `get_parking_windows(parking_id)` - Obtener todas las ventanas asignadas a un parking
- `remove_window_assignment(panel_id, window_id, parking_id, sensor_type=None)` - Eliminar asignación específica
- `update_window_configuration(panel_id, window_id, parking_id, config)` - Actualizar configuración de rotación
- `get_window_configuration(panel_id, window_id, parking_id, company_id=None)` - Obtener configuración
- `get_sensor_data_for_window(panel_id, window_id)` - Obtener datos de sensores agrupados desde `parking_sensor_summary`

#### 3.2. Actualizar Servicio de Envío a Paneles

**Archivo:** `src/panel_protocol/panel_protocol_service.py` (modificar)

**Modificaciones:**
- Detectar si panel es Tipo 4
- Usar protocolo nuevo para Tipo 4
- Enviar a ventana específica según `parking_panel_windows`
- Manejar rotación de contenido según `panel_window_configurations`
- **Obtener datos de sensores desde `parking_sensor_summary`** (agrupados por tipo)
- Para `sensor_type=NULL`: Mostrar ocupación general del parking
- Para `sensor_type='PMR'`: Mostrar `free_sensors` y `busy_sensors` de `parking_sensor_summary` donde `sensor_type='PMR'`
- Para `sensor_type='Electrico'`: Mostrar datos de sensores eléctricos agrupados
- Para `sensor_type='Caravanas'`: Mostrar datos de sensores caravanas agrupados

#### 3.3. Crear Endpoints API

**Archivo:** `src/api_server.py` (modificar)

**Nuevos Endpoints:**
```
POST   /api/v1/panels/{panel_id}/windows/{window_id}/assign
DELETE /api/v1/panels/{panel_id}/windows/{window_id}/unassign
GET    /api/v1/panels/{panel_id}/windows
GET    /api/v1/parkings/{parking_id}/windows
POST   /api/v1/parkings/{parking_id}/windows/{window_id}/config
GET    /api/v1/parkings/{parking_id}/windows/{window_id}/config
PUT    /api/v1/parkings/{parking_id}/windows/{window_id}/config
```

**Endpoints Modificados:**
- `POST /api/v1/panels` - Agregar validación para Tipo 4
- `GET /api/v1/panels` - Incluir información de ventanas
- `POST /api/v1/panels/send-text` - Soportar `window_id` para Tipo 4

---

### 4. FRONTEND: INTERFAZ DE USUARIO

#### 4.1. Página de Configuración de Ventanas

**Archivo:** `client/src/pages/ParkingWindowConfig.jsx` (nuevo)

**Funcionalidades:**
- Listar parkings del usuario (o empresa si superadmin)
- Para cada parking, mostrar paneles asignados
- Para cada panel Tipo 4, mostrar ventanas (0-15)
- Asignar parking/sensores agrupados a ventanas:
  - Opción: "Ocupación general del parking"
  - Opción: "Sensores PMR" (agrupados del parking)
  - Opción: "Sensores Eléctricos" (agrupados del parking)
  - Opción: "Sensores Caravanas" (agrupados del parking)
  - Opción: "Sensores Emergencias" (agrupados del parking)
  - Opción: "Sensores Policía" (agrupados del parking)
  - Opción: "Sensores Otros" (agrupados del parking)
- Configurar rotación con porcentajes de visibilidad
- Configurar tiempo de refresco (ciclo completo)
- Guardar configuración

**Componentes:**
- `ParkingWindowConfig.jsx` - Página principal
- `WindowAssignmentModal.jsx` - Modal para asignar parking/sensor a ventana
- `WindowConfigModal.jsx` - Modal para configurar porcentajes y tiempo
- `WindowList.jsx` - Lista de ventanas con estado

#### 4.2. Botón de Configuración en Página de Parkings

**Archivo:** `client/src/pages/Parkings.jsx` (modificar)

**Modificaciones:**
- Agregar botón "Configurar Ventanas" en la parte superior
- Botón visible solo si hay paneles Tipo 4 asignados
- Al hacer clic, abrir modal o redirigir a página de configuración

#### 4.3. Selector de Empresa para Superadmin

**Archivo:** `client/src/components/CompanySelector.jsx` (nuevo)

**Funcionalidades:**
- Combo para seleccionar empresa (solo superadmin)
- Al seleccionar empresa, filtrar datos
- Mostrar configuración de esa empresa

#### 4.4. Servicios Frontend

**Archivo:** `client/src/services/windowService.js` (nuevo)

**Funciones:**
- `assignParkingToWindow(panelId, windowId, parkingId, sensorType)`
  - `sensorType=null`: Asignar ocupación general del parking
  - `sensorType='PMR'`: Asignar sensores PMR agrupados
  - `sensorType='Electrico'`: Asignar sensores Eléctricos agrupados
  - `sensorType='Caravanas'`: Asignar sensores Caravanas agrupados
  - etc.
- `getWindowAssignments(panelId)` - Obtener todas las asignaciones de un panel
- `getParkingWindows(parkingId)` - Obtener todas las ventanas asignadas a un parking
- `getParkingSensorTypes(parkingId)` - Obtener tipos de sensores disponibles del parking (desde `parking_sensor_summary`)
- `updateWindowConfig(panelId, windowId, parkingId, config)` - Actualizar configuración de rotación
- `getWindowConfig(panelId, windowId, parkingId, companyId)` - Obtener configuración

---

### 5. LÓGICA DE ROTACIÓN Y VISUALIZACIÓN

#### 5.1. Servicio de Rotación de Contenido

**Archivo:** `src/panel_content_rotation_service.py` (nuevo)

**Funcionalidades:**
- Leer configuración de `panel_window_configurations`
- Leer asignaciones de `parking_panel_windows` para la ventana
- **Obtener datos de sensores desde `parking_sensor_summary`** (agrupados por tipo)
- Calcular qué contenido mostrar según porcentajes en `rotation_order`
- Rotar contenido según tiempo de refresco
- Manejar múltiples tipos en la misma ventana (parking + grupos de sensores)

**Algoritmo:**
1. Leer `parking_panel_windows` para obtener asignaciones de la ventana
2. Leer `panel_window_configurations` para obtener configuración de rotación
3. Leer `rotation_order` JSONB que contiene:
   - `{"type": "parking", "percentage": 50, "sensor_type": null}` → Ocupación general
   - `{"type": "sensor_group", "percentage": 30, "sensor_type": "PMR"}` → Sensores PMR agrupados
   - `{"type": "sensor_group", "percentage": 20, "sensor_type": "Caravanas"}` → Sensores Caravanas agrupados
4. Para cada tipo en `rotation_order`:
   - Si `type="parking"`: Obtener `current_occupancy` y `max_capacity` del parking
   - Si `type="sensor_group"`: Obtener datos de `parking_sensor_summary` donde `sensor_type` coincide
5. Calcular tiempo de visualización por tipo: `(percentage / 100) * refresh_time_seconds`
6. Rotar contenido cada `refresh_time_seconds` (ciclo completo)
7. Enviar contenido correspondiente al panel usando protocolo Tipo 4

#### 5.2. Integración con Actualización de Paneles

**Archivo:** `src/panel_update_worker.py` (modificar)

**Modificaciones:**
- Detectar si panel es Tipo 4
- Para cada ventana asignada (0-15):
  - Leer asignaciones de `parking_panel_windows` para la ventana
  - Leer configuración de rotación de `panel_window_configurations`
  - **Obtener datos de sensores desde `parking_sensor_summary`** según `sensor_type`
  - Determinar qué contenido mostrar según `rotation_order` y tiempo actual
  - Formatear mensaje:
    - Si `type="parking"`: "Parking X: Y/Z plazas libres"
    - Si `type="sensor_group"` y `sensor_type="PMR"`: "PMR: X libres / Y totales" (desde `parking_sensor_summary`)
    - Si `type="sensor_group"` y `sensor_type="Electrico"`: "Eléctrico: X libres / Y totales"
    - Si `type="sensor_group"` y `sensor_type="Caravanas"`: "Caravanas: X libres / Y totales"
  - Enviar a ventana específica usando protocolo nuevo (Tipo 4)

---

### 6. COMPATIBILIDAD Y MIGRACIÓN

#### 6.1. Compatibilidad Retroactiva

**Estrategia:**
- Paneles Tipo 1, 2, 3: Mantener comportamiento actual
- Paneles sin `panel_type_id`: Asignar Tipo 1 por defecto
- Paneles Tipo 4: Usar nuevo protocolo y sistema de ventanas

#### 6.2. Script de Migración de Datos

**Archivo:** `src/migrate_to_panel_type_4.py` (nuevo)

**Funcionalidades:**
- Crear Panel Tipo 4 en `panel_types`
- Migrar paneles existentes si es necesario
- Crear registros iniciales en `parking_panel_windows`
- Validar integridad de datos

---

## 📝 ORDEN DE EJECUCIÓN RECOMENDADO

### Fase 1: Base de Datos (Backend)
1. ✅ Crear script de migración `migrate_panel_type_4.py`
2. ✅ Crear tabla `parking_panel_windows`
3. ✅ Crear tabla `panel_window_configurations`
4. ✅ Actualizar tabla `panels` (campo `windows_count`)
5. ✅ Insertar Panel Tipo 4 en `panel_types`
6. ✅ Migrar datos existentes

### Fase 2: Integración Protocolo (Backend)
7. ✅ Revisar archivos en `/docs/panel_protocol`
8. ✅ Copiar archivos a estructura existente
9. ✅ Adaptar protocolo a estructura actual
10. ✅ Integrar funciones en servicios existentes

### Fase 3: Servicios Backend
11. ✅ Crear `panel_window_service.py`
12. ✅ Modificar `panel_protocol_service.py`
13. ✅ Crear `panel_content_rotation_service.py`
14. ✅ Modificar `panel_update_worker.py`
15. ✅ Crear endpoints API

### Fase 4: Frontend
16. ✅ Crear servicios frontend (`windowService.js`)
17. ✅ Crear componentes de configuración
18. ✅ Modificar página de Parkings
19. ✅ Crear selector de empresa para superadmin
20. ✅ Integrar en flujo de usuario

### Fase 5: Testing y Validación
21. ✅ Probar migración de base de datos
22. ✅ Probar asignación de ventanas
23. ✅ Probar rotación de contenido
24. ✅ Probar compatibilidad con paneles existentes
25. ✅ Probar frontend completo

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### Compatibilidad
- **NO romper** funcionalidad existente de paneles Tipo 1, 2, 3
- Mantener endpoints antiguos funcionando
- Validar que paneles existentes sigan funcionando

### Rendimiento
- Índices en nuevas tablas para consultas rápidas
- Cachear configuraciones de ventanas si es necesario
- Optimizar consultas de rotación de contenido

### Seguridad
- Validar permisos al asignar ventanas
- Superadmin puede configurar cualquier empresa
- Usuarios solo pueden configurar sus parkings

### Documentación
- Documentar nueva estructura de base de datos
- Documentar nuevos endpoints API
- Documentar uso del frontend
- Actualizar documentación de protocolo

---

## 📊 IMPACTO ESTIMADO

### Archivos a Crear
- `src/migrate_panel_type_4.py`
- `src/panel_window_service.py`
- `src/panel_content_rotation_service.py`
- `client/src/pages/ParkingWindowConfig.jsx`
- `client/src/components/WindowAssignmentModal.jsx`
- `client/src/components/WindowConfigModal.jsx`
- `client/src/components/CompanySelector.jsx`
- `client/src/services/windowService.js`
- `docs/v4.3.0/migracion_paneles_tipo4.md`

### Archivos a Modificar
- `src/models.py` (agregar modelos)
- `src/api_server.py` (nuevos endpoints)
- `src/panel_protocol/panel_protocol_service.py` (soporte Tipo 4)
- `src/panel_update_worker.py` (rotación de contenido)
- `client/src/pages/Parkings.jsx` (botón configuración)
- `client/src/services/api.js` (nuevos endpoints)

### Tablas de Base de Datos
- Nueva: `parking_panel_windows`
- Nueva: `panel_window_configurations`
- Modificar: `panels` (campo `windows_count`)
- Modificar: `panel_types` (insertar Tipo 4)

---

## ✅ CHECKLIST DE VALIDACIÓN

Antes de considerar completada la migración:

- [ ] Panel Tipo 4 creado en base de datos
- [ ] Tablas nuevas creadas y con índices
- [ ] Migración de datos existentes completada
- [ ] Protocolo integrado y funcionando
- [ ] Servicios backend creados y probados
- [ ] Endpoints API funcionando
- [ ] Frontend completo y funcional
- [ ] Compatibilidad con paneles existentes verificada
- [ ] Documentación actualizada
- [ ] Tests realizados

---

## 🚀 SIGUIENTE PASO

Una vez aprobado este análisis, proceder con la **Fase 1: Base de Datos**.
