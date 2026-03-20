# Descripción de la Base de Datos

## 1. Información General

- **Motor**: PostgreSQL 14+
- **Nombre**: `parking_db`
- **Usuario**: `parking_user`
- **ORM**: SQLAlchemy
- **Ubicación modelos**: `src/models.py`

## 2. Diagrama de Relaciones (Simplificado)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              ENTIDADES PRINCIPALES                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐       ┌──────────┐       ┌─────────┐       ┌──────────────────┐│
│  │  Users  │───────│ Parkings │───────│ Panels  │───────│   Panel Types    ││
│  └─────────┘       └──────────┘       └─────────┘       └──────────────────┘│
│       │                 │                  │                     │          │
│       │                 │                  │                     │          │
│       ▼                 ▼                  ▼                     ▼          │
│  ┌─────────┐       ┌──────────┐       ┌─────────┐       ┌──────────────────┐│
│  │ Alarms  │       │ Accesses │       │Schedules│       │  Manufacturers   ││
│  └─────────┘       └──────────┘       └─────────┘       └──────────────────┘│
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 3. Tablas Principales

### 3.1 users
Usuarios del sistema.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | No | PK, autoincrement |
| name | VARCHAR | No | Nombre del usuario |
| email | VARCHAR | No | Email único |
| password_hash | VARCHAR | No | Hash de contraseña |
| role | VARCHAR(20) | No | Rol: 'superadmin', 'user' |
| is_active | BOOLEAN | No | Usuario activo |
| created_at | TIMESTAMP | No | Fecha creación |
| updated_at | TIMESTAMP | No | Fecha actualización |

### 3.2 parkings
Aparcamientos gestionados.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | No | PK |
| name | VARCHAR | No | Nombre único |
| location | VARCHAR | Sí | Ubicación |
| max_capacity | INTEGER | No | Capacidad máxima |
| threshold_dense | INTEGER | No | Umbral estado DENSO |
| threshold_full | INTEGER | No | Umbral estado COMPLETO |
| current_occupancy | INTEGER | No | Ocupación actual |
| status | VARCHAR | No | Estado: LIBRE, DENSO, COMPLETO |
| fixed_message_flag | BOOLEAN | No | Mensaje fijo activo |
| message_type | VARCHAR(20) | No | Tipo: 'ESTADO', 'PLAZAS_LIBRES' |
| spot_monitoring_enabled | BOOLEAN | Sí | Monitorización plaza a plaza |
| total_monitored_spots | INTEGER | Sí | Total plazas monitorizadas |
| total_spot_occupied | INTEGER | Sí | Plazas ocupadas (detección) |
| pending_entries | INTEGER | Sí | Entradas pendientes validación |
| pending_exits | INTEGER | Sí | Salidas pendientes validación |

### 3.3 panels
Paneles LED informativos.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | No | PK |
| parking_id | INTEGER | No | FK a parkings |
| name | VARCHAR | No | Nombre del panel |
| ip | VARCHAR | No | Dirección IP |
| status | VARCHAR | No | ONLINE, OFFLINE |
| last_message | TEXT | Sí | Último mensaje enviado |
| last_update | TIMESTAMP | Sí | Última actualización |
| **panel_type_id** | INTEGER | Sí | FK a panel_types |
| port | INTEGER | Sí | Puerto (default: 5200) |
| **protocol_version** | VARCHAR(20) | Sí | **'old' o 'new'** |
| service_endpoint | VARCHAR(255) | Sí | URL del servicio |
| is_active | BOOLEAN | Sí | Panel activo |
| windows_count | INTEGER | Sí | Número de ventanas (1-16) |
| last_message_window_0 | TEXT | Sí | Mensaje ventana 0 |
| last_message_window_1 | TEXT | Sí | Mensaje ventana 1 |

**Importante**: El campo `protocol_version` determina el routing:
- `'old'` → Puerto 8888 (SDK Java)
- `'new'` → Puerto 7110 (Python directo)

### 3.4 panel_types
Tipos de paneles disponibles.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | No | PK |
| manufacturer_id | INTEGER | No | FK a manufacturers |
| name | VARCHAR(100) | No | Nombre del tipo |
| description | TEXT | Sí | Descripción |
| protocol_type | VARCHAR(50) | No | 'old' o 'new' |
| windows_count | INTEGER | No | Número de ventanas |
| window_width | INTEGER | No | Ancho ventana |
| window_height | INTEGER | No | Alto ventana |
| total_width | INTEGER | No | Ancho total |
| total_height | INTEGER | No | Alto total |
| port | INTEGER | No | Puerto (default: 5200) |
| is_active | BOOLEAN | Sí | Tipo activo |

**Tipos predefinidos:**
| ID | Nombre | Ventanas | Protocolo | Descripción |
|----|--------|----------|-----------|-------------|
| 1 | Tipo 1 | 1 | old | Protocolo antiguo, 1 ventana |
| 2 | Tipo 2 | 1 | new | Protocolo nuevo, 1 ventana |
| 3 | Tipo 3 | 2 | new | Protocolo nuevo, 2 ventanas |
| 4 | Tipo 4 | 16 | new | Protocolo nuevo, 16 ventanas |

### 3.5 accesses
Cámaras/accesos de conteo.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | No | PK |
| ip | VARCHAR | No | Dirección IP |
| line | INTEGER | No | Línea de la cámara |
| name | VARCHAR | Sí | Nombre descriptivo |
| last_vehicle_in | INTEGER | No | Último contador entradas |
| last_vehicle_out | INTEGER | No | Último contador salidas |
| status | VARCHAR | No | ONLINE, OFFLINE |
| camera_type | VARCHAR(20) | No | 'counting' o 'spot_detection' |
| monitored_spots_count | INTEGER | Sí | Plazas que monitoriza |

### 3.6 panel_schedules
Programaciones de mensajes en paneles.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | No | PK |
| parking_id | INTEGER | No | FK a parkings |
| user_id | INTEGER | Sí | FK a users |
| name | VARCHAR | No | Nombre programación |
| description | TEXT | Sí | Descripción |
| start_date | TIMESTAMP | No | Fecha inicio vigencia |
| end_date | TIMESTAMP | No | Fecha fin vigencia |
| start_time | VARCHAR | No | Hora inicio (HH:MM) |
| end_time | VARCHAR | No | Hora fin (HH:MM) |
| monday - sunday | BOOLEAN | Sí | Días activos |
| message | TEXT | No | Mensaje a mostrar |
| color | INTEGER | Sí | Color del texto |
| font_size | INTEGER | Sí | Tamaño fuente |
| **effect** | VARCHAR | Sí | **Efecto visual** |
| is_active | BOOLEAN | Sí | Programación activa |
| priority | INTEGER | Sí | Prioridad (1-5) |

**Valores de effect:**
| Valor | Descripción |
|-------|-------------|
| `'static'` | Texto estático (auto-scroll si largo) |
| `'center'` | Texto centrado (auto-scroll si largo) |
| `'fijo'` | Texto fijo (nunca scroll) |
| `'scroll_left'` | Scroll continuo izquierda |
| `'scroll_right'` | Scroll continuo derecha |

## 4. Tablas de Relación

### 4.1 camera_parkings
Relación muchos-a-muchos entre cámaras y parkings.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| camera_id | INTEGER | FK a accesses |
| parking_id | INTEGER | FK a parkings |
| created_at | TIMESTAMP | Fecha creación |

### 4.2 user_parkings
Permisos de usuarios sobre parkings.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| user_id | INTEGER | FK a users |
| parking_id | INTEGER | FK a parkings |

### 4.3 user_panels / user_accesses
Similar a user_parkings para paneles y accesos.

## 5. Tablas de Histórico y Logs

### 5.1 occupancy_history
Histórico de ocupación.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| parking_id | INTEGER | FK a parkings |
| timestamp | TIMESTAMP | Momento del registro |
| occupancy | INTEGER | Ocupación registrada |
| source | VARCHAR | 'camera', 'manual', 'scheduled_adjust' |
| adjustment_type | VARCHAR | Tipo de ajuste |

### 5.2 camera_logs
Logs de mensajes de cámaras.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| access_id | INTEGER | FK a accesses |
| camera_ip | VARCHAR | IP origen |
| raw_message | TEXT | Mensaje JSON completo |
| vehicle_in / out | INTEGER | Contadores |
| status | VARCHAR | 'processed', 'discarded', 'error' |
| new_occupancy | INTEGER | Nueva ocupación |

### 5.3 panel_message_logs
Logs de mensajes enviados a paneles.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| panel_id | INTEGER | FK a panels |
| message | TEXT | Mensaje enviado |
| status | VARCHAR | 'sent', 'delivered', 'failed' |
| response_time | FLOAT | Tiempo respuesta (ms) |

### 5.4 panel_schedule_logs
Logs de ejecución de programaciones.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| schedule_id | INTEGER | FK a panel_schedules |
| execution_type | VARCHAR | 'started', 'ended', 'skipped', 'error' |
| panels_affected | INTEGER | Paneles afectados |

## 6. Sistema de Alarmas

### 6.1 alarm_configurations
Configuraciones de alarmas por usuario.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| user_id | INTEGER | FK a users |
| name | VARCHAR | Nombre configuración |
| alarm_type | VARCHAR | 'panel', 'camera', 'parking' |
| status | VARCHAR | 'active', 'paused' |

### 6.2 alarms
Alarmas generadas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| alarm_configuration_id | INTEGER | FK |
| severity | VARCHAR | 'LEVE', 'NORMAL', 'GRAVE' |
| status | VARCHAR | 'active', 'resolved' |
| message | TEXT | Mensaje de alarma |
| affected_targets | JSON | Equipos afectados |

## 7. Sensores Individuales (PMR, Eléctricos)

### 7.1 individual_sensors
Sensores de plazas especiales.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| serial_number | VARCHAR | Número serie único |
| name | VARCHAR | Nombre plaza |
| sensor_type | VARCHAR | 'PMR', 'Electrico', etc. |
| parking_id | INTEGER | FK a parkings |
| is_active | BOOLEAN | Sensor activo |

### 7.2 sensor_current_status
Estado actual de sensores.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| sensor_id | INTEGER | PK, FK |
| current_status | VARCHAR | 'free', 'busy', 'error' |
| battery_voltage | FLOAT | Voltaje batería |
| battery_capacity | INTEGER | Capacidad (%) |

## 8. Configuración de Ventanas (Paneles Tipo 3/4)

### 8.1 parking_panel_windows
Asignación parking→ventana.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| parking_id | INTEGER | FK |
| panel_id | INTEGER | FK |
| window_id | INTEGER | 0-15 |
| sensor_type | VARCHAR | NULL o 'PMR', 'Electrico' |
| display_type | VARCHAR | 'parking', 'sensor_group' |

### 8.2 panel_window_configurations
Configuración de rotación y visualización.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| panel_id | INTEGER | FK |
| window_id | INTEGER | 0-15 |
| rotation_enabled | BOOLEAN | Rotación activa |
| rotation_order | JSON | Orden de rotación |
| refresh_time_seconds | INTEGER | Tiempo ciclo |

## 9. Corrección Automática de Ocupación

### 9.1 parking_correction_config
Configuración de corrección por parking.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| parking_id | INTEGER | FK único |
| auto_correction_enabled | BOOLEAN | Corrección activa |
| correction_hour | INTEGER | Hora corrección (0-23) |
| avg_daily_drift | FLOAT | Deriva diaria promedio |
| drift_by_weekday | JSON | Deriva por día semana |

### 9.2 correction_calculations
Histórico de cálculos.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | PK |
| parking_id | INTEGER | FK |
| occupancy_before_adjustment | INTEGER | Ocupación antes |
| occupancy_after_adjustment | INTEGER | Ocupación después |
| correction_applied | INTEGER | Corrección aplicada |
| trigger_type | VARCHAR | Tipo de ajuste |

## 10. Comandos Útiles

### Conexión
```bash
sudo -u postgres psql -d parking_db
```

### Consultas comunes
```sql
-- Ver paneles y su protocolo
SELECT ip, name, protocol_version, panel_type_id, status 
FROM panels ORDER BY parking_id;

-- Ver programaciones activas
SELECT id, name, message, effect, is_active 
FROM panel_schedules WHERE is_active = true;

-- Ver ocupación de parkings
SELECT id, name, current_occupancy, max_capacity, status 
FROM parkings ORDER BY id;

-- Ver tipos de panel
SELECT id, name, protocol_type, windows_count 
FROM panel_types;

-- Ver cámaras por parking
SELECT a.ip, a.name, cp.parking_id 
FROM accesses a 
JOIN camera_parkings cp ON a.id = cp.camera_id;
```

### Backup
```bash
sudo -u postgres pg_dump parking_db > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
sudo -u postgres psql -d parking_db < backup_20260318.sql
```

---

*Anterior: [03-estructura-directorios.md](./03-estructura-directorios.md)*
*Siguiente: [05-flujos-principales.md](./05-flujos-principales.md)*
