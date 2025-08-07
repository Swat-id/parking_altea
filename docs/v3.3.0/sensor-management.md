# Gestión de Sensores de Parking v3.3.0

## Introducción

El sistema de gestión de sensores permite monitorizar en tiempo real el estado de ocupación de plazas individuales de parking mediante sensores IoT, complementando el sistema de cámaras existente.

## Arquitectura del Sistema

### Componentes Principales

1. **Sensor Hardware**
   - Sensores de ultrasonidos
   - Sensores magnéticos
   - Sensores de radar
   - Gateway de comunicación

2. **API de Sensores**
   - Endpoint de recepción de datos
   - Procesamiento de señales
   - Validación de datos
   - Almacenamiento en base de datos

3. **Sistema de Monitorización**
   - Estado en tiempo real
   - Detección de fallos
   - Calibración automática
   - Alertas de mantenimiento

## Modelo de Datos

### Tabla: sensors
```sql
CREATE TABLE sensors (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) UNIQUE NOT NULL,
    parking_id INTEGER REFERENCES parkings(id),
    plaza_number INTEGER NOT NULL,
    sensor_type VARCHAR(20) NOT NULL, -- 'ultrasonic', 'magnetic', 'radar'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'maintenance'
    last_ping TIMESTAMP,
    battery_level INTEGER DEFAULT 100,
    signal_strength INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: sensor_readings
```sql
CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES sensors(sensor_id),
    occupied BOOLEAN NOT NULL,
    confidence_level DECIMAL(3,2) DEFAULT 1.0,
    signal_strength INTEGER,
    battery_level INTEGER,
    temperature DECIMAL(5,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
```

### Tabla: sensor_configurations
```sql
CREATE TABLE sensor_configurations (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES sensors(sensor_id),
    detection_threshold DECIMAL(5,2) DEFAULT 20.0,
    sampling_interval INTEGER DEFAULT 60, -- segundos
    calibration_offset DECIMAL(5,2) DEFAULT 0.0,
    alert_threshold_battery INTEGER DEFAULT 20,
    alert_threshold_signal INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Gestión de Sensores

#### GET /api/sensors
```json
{
  "sensors": [
    {
      "id": 1,
      "sensor_id": "SNS001",
      "parking_id": 1,
      "plaza_number": 1,
      "sensor_type": "ultrasonic",
      "status": "active",
      "last_ping": "2025-08-07T10:30:00Z",
      "battery_level": 85,
      "signal_strength": 95
    }
  ]
}
```

#### POST /api/sensors
```json
{
  "sensor_id": "SNS002",
  "parking_id": 1,
  "plaza_number": 2,
  "sensor_type": "magnetic",
  "detection_threshold": 25.0,
  "sampling_interval": 30
}
```

#### PUT /api/sensors/{sensor_id}
```json
{
  "status": "maintenance",
  "detection_threshold": 22.5,
  "sampling_interval": 45
}
```

#### DELETE /api/sensors/{sensor_id}
- Desactiva el sensor (no elimina datos históricos)

### Recepción de Datos

#### POST /api/sensors/data
```json
{
  "sensor_id": "SNS001",
  "occupied": true,
  "confidence_level": 0.95,
  "signal_strength": 88,
  "battery_level": 82,
  "temperature": 23.5,
  "timestamp": "2025-08-07T10:35:00Z"
}
```

#### POST /api/sensors/batch
```json
{
  "readings": [
    {
      "sensor_id": "SNS001",
      "occupied": true,
      "confidence_level": 0.95,
      "timestamp": "2025-08-07T10:35:00Z"
    },
    {
      "sensor_id": "SNS002",
      "occupied": false,
      "confidence_level": 0.98,
      "timestamp": "2025-08-07T10:35:05Z"
    }
  ]
}
```

### Monitorización

#### GET /api/sensors/{sensor_id}/status
```json
{
  "sensor_id": "SNS001",
  "status": "active",
  "current_state": "occupied",
  "last_reading": "2025-08-07T10:35:00Z",
  "battery_level": 82,
  "signal_strength": 88,
  "alerts": []
}
```

#### GET /api/sensors/health
```json
{
  "total_sensors": 150,
  "active_sensors": 148,
  "offline_sensors": 2,
  "low_battery": 5,
  "poor_signal": 3,
  "last_update": "2025-08-07T10:40:00Z"
}
```

## Lógica de Procesamiento

### Integración con Sistema Existente

1. **Prioridad de Datos**
   ```
   Programaciones Activas > Sensores Individuales > Cámaras Globales
   ```

2. **Validación Cruzada**
   - Comparar datos de sensores con cámaras
   - Detectar inconsistencias
   - Aplicar algoritmos de consenso

3. **Actualización de Estado**
   - Los sensores actualizan el estado de plazas individuales
   - El sistema recalcula la ocupación global
   - Se envían actualizaciones a paneles si no hay programaciones activas

### Algoritmo de Detección

```python
def process_sensor_reading(sensor_data):
    # 1. Validar datos de entrada
    if not validate_sensor_data(sensor_data):
        return False
    
    # 2. Aplicar filtros de ruido
    filtered_data = apply_noise_filter(sensor_data)
    
    # 3. Determinar estado de ocupación
    occupied = determine_occupancy(filtered_data)
    
    # 4. Validar con datos históricos
    if validate_with_history(sensor_data.sensor_id, occupied):
        # 5. Actualizar base de datos
        update_plaza_status(sensor_data.sensor_id, occupied)
        
        # 6. Recalcular ocupación del parking
        update_parking_occupancy(sensor_data.parking_id)
        
        # 7. Enviar notificaciones si es necesario
        check_and_send_alerts(sensor_data.parking_id)
        
        return True
    
    return False
```

## Configuración y Calibración

### Calibración Automática

1. **Periodo de Aprendizaje**
   - 24-48 horas de monitorización
   - Análisis de patrones de ocupación
   - Ajuste automático de umbrales

2. **Validación Cruzada**
   - Comparación con datos de cámaras
   - Detección de falsos positivos/negativos
   - Ajuste de parámetros

3. **Optimización Continua**
   - Machine learning para mejora de precisión
   - Adaptación a condiciones ambientales
   - Ajuste estacional

### Configuración Manual

```json
{
  "sensor_id": "SNS001",
  "calibration": {
    "detection_threshold": 25.0,
    "noise_filter_level": 3,
    "confidence_threshold": 0.8,
    "validation_samples": 5,
    "timeout_seconds": 300
  },
  "alerts": {
    "battery_threshold": 20,
    "signal_threshold": 30,
    "offline_timeout": 600
  }
}
```

## Alertas y Mantenimiento

### Tipos de Alertas

1. **Operacionales**
   - Sensor desconectado
   - Batería baja
   - Señal débil
   - Lecturas inconsistentes

2. **Mantenimiento**
   - Calibración requerida
   - Limpieza necesaria
   - Reemplazo de batería
   - Fallo de hardware

3. **Sistema**
   - Gateway desconectado
   - Pérdida de comunicación
   - Sobrecarga de datos
   - Errores de sincronización

### Configuración de Alertas

```json
{
  "alert_rules": [
    {
      "type": "battery_low",
      "threshold": 20,
      "severity": "warning",
      "notification_channels": ["email", "dashboard"]
    },
    {
      "type": "sensor_offline",
      "threshold": 300,
      "severity": "critical",
      "notification_channels": ["email", "sms", "dashboard"]
    }
  ]
}
```

## Frontend - Dashboard de Sensores

### Componentes UI

1. **Vista General**
   - Mapa de parking con estado de sensores
   - Estadísticas en tiempo real
   - Alertas activas

2. **Gestión Individual**
   - Lista de sensores
   - Configuración por sensor
   - Historial de lecturas

3. **Monitorización**
   - Gráficos de estado
   - Alertas y notificaciones
   - Reportes de mantenimiento

### Funcionalidades

- Visualización en tiempo real
- Configuración de umbrales
- Gestión de alertas
- Reportes y análisis
- Calibración manual
- Mantenimiento programado

## Integración con Sistema Existente

### Compatibilidad

- Mantiene compatibilidad con sistema de cámaras
- Respeta prioridad de programaciones activas
- Se integra con sistema de alarmas v3.2.0
- Compatible con API unificada existente

### Migración

1. **Fase 1:** Instalación de infraestructura de sensores
2. **Fase 2:** Configuración y calibración
3. **Fase 3:** Integración con sistema existente
4. **Fase 4:** Activación gradual por zonas

## Testing

### Unit Tests
- Validación de datos de sensores
- Algoritmos de detección
- Lógica de calibración

### Integration Tests
- Integración con API existente
- Compatibilidad con sistema de cámaras
- Flujo completo de datos

### Performance Tests
- Carga de datos en tiempo real
- Respuesta del sistema
- Escalabilidad

---

**Versión:** v3.3.0
**Estado:** En desarrollo
**Última actualización:** 7 de agosto de 2025
