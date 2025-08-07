# API Extensions v3.3.0

## Introducción

La versión v3.3.0 extiende la API existente con nuevos endpoints para gestión de sensores, alarmas evolucionadas y funcionalidades predictivas, manteniendo compatibilidad total con versiones anteriores.

## Estructura de la API

### Base URL
```
Production: https://parking.altea.es/api/
Development: http://localhost:6001/api/
```

### Autenticación
Mantiene el mismo sistema de autenticación JWT de versiones anteriores:
```http
Authorization: Bearer <jwt_token>
```

## Nuevos Endpoints v3.3.0

### 1. Gestión de Sensores

#### GET /api/sensors
Obtiene lista de todos los sensores

**Parámetros de consulta:**
- `parking_id` (opcional): Filtrar por parking
- `status` (opcional): Filtrar por estado
- `sensor_type` (opcional): Filtrar por tipo
- `page` (opcional): Página (default: 1)
- `per_page` (opcional): Elementos por página (default: 50)

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "sensors": [
      {
        "id": 1,
        "sensor_id": "SNS001",
        "parking_id": 1,
        "parking_name": "P. Ciutat Esportiva",
        "plaza_number": 15,
        "sensor_type": "ultrasonic",
        "status": "active",
        "last_ping": "2025-08-07T10:30:00Z",
        "battery_level": 85,
        "signal_strength": 95,
        "current_state": "occupied",
        "confidence_level": 0.95,
        "created_at": "2025-08-01T09:00:00Z",
        "updated_at": "2025-08-07T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 150,
      "pages": 3
    }
  }
}
```

#### POST /api/sensors
Crear nuevo sensor

**Cuerpo de la petición:**
```json
{
  "sensor_id": "SNS151",
  "parking_id": 2,
  "plaza_number": 1,
  "sensor_type": "magnetic",
  "configuration": {
    "detection_threshold": 25.0,
    "sampling_interval": 60,
    "alert_threshold_battery": 20,
    "alert_threshold_signal": 30
  }
}
```

**Respuesta:**
```json
{
  "status": "success",
  "message": "Sensor creado exitosamente",
  "data": {
    "id": 151,
    "sensor_id": "SNS151",
    "status": "active"
  }
}
```

#### GET /api/sensors/{sensor_id}
Obtener detalles de un sensor específico

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "sensor": {
      "id": 1,
      "sensor_id": "SNS001",
      "parking_id": 1,
      "plaza_number": 15,
      "sensor_type": "ultrasonic",
      "status": "active",
      "configuration": {
        "detection_threshold": 20.0,
        "sampling_interval": 60,
        "calibration_offset": 0.5,
        "alert_threshold_battery": 20,
        "alert_threshold_signal": 30
      },
      "statistics": {
        "uptime_percentage": 99.5,
        "avg_battery_level": 82,
        "avg_signal_strength": 91,
        "last_readings": [
          {
            "occupied": true,
            "confidence_level": 0.95,
            "timestamp": "2025-08-07T10:30:00Z"
          }
        ]
      }
    }
  }
}
```

#### PUT /api/sensors/{sensor_id}
Actualizar configuración de sensor

**Cuerpo de la petición:**
```json
{
  "status": "maintenance",
  "configuration": {
    "detection_threshold": 22.5,
    "sampling_interval": 45,
    "alert_threshold_battery": 15
  }
}
```

#### DELETE /api/sensors/{sensor_id}
Desactivar sensor (soft delete)

### 2. Datos de Sensores

#### POST /api/sensors/data
Recibir datos de un sensor individual

**Cuerpo de la petición:**
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

**Respuesta:**
```json
{
  "status": "success",
  "message": "Datos procesados correctamente",
  "data": {
    "sensor_id": "SNS001",
    "processed": true,
    "plaza_updated": true,
    "parking_occupancy_updated": true,
    "alerts_triggered": []
  }
}
```

#### POST /api/sensors/batch
Recibir datos de múltiples sensores

**Cuerpo de la petición:**
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

#### GET /api/sensors/{sensor_id}/readings
Obtener historial de lecturas

**Parámetros:**
- `from_date`: Fecha inicio (ISO 8601)
- `to_date`: Fecha fin (ISO 8601)
- `limit`: Número máximo de registros

### 3. Alarmas de Sensores

#### GET /api/alarms/sensors
Obtener alarmas de sensores

**Parámetros:**
- `severity`: Filtrar por severidad
- `status`: active, acknowledged, resolved
- `sensor_id`: Filtrar por sensor
- `parking_id`: Filtrar por parking

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "alarms": [
      {
        "id": 1,
        "sensor_id": "SNS001",
        "alarm_type": "battery_low",
        "severity": "warning",
        "threshold_value": 20.0,
        "current_value": 18.0,
        "is_active": true,
        "triggered_at": "2025-08-07T10:30:00Z",
        "acknowledged_at": null,
        "resolved_at": null,
        "parking_name": "P. Ciutat Esportiva",
        "plaza_number": 15,
        "estimated_resolution": "2025-08-08T10:00:00Z"
      }
    ]
  }
}
```

#### POST /api/alarms/sensors/{alarm_id}/acknowledge
Reconocer una alarma

**Cuerpo de la petición:**
```json
{
  "notes": "Revisión programada para mañana",
  "estimated_resolution": "2025-08-08T10:00:00Z"
}
```

#### POST /api/alarms/sensors/{alarm_id}/resolve
Resolver una alarma

### 4. Alarmas Predictivas

#### GET /api/alarms/predictive
Obtener predicciones de alarmas

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "predictions": [
      {
        "id": 1,
        "parking_id": 1,
        "prediction_type": "overflow_risk",
        "probability": 0.85,
        "predicted_time": "2025-08-07T14:30:00Z",
        "confidence_level": 0.92,
        "model_version": "v2.1",
        "factors": [
          "Historical pattern",
          "Weather forecast",
          "Local events"
        ],
        "recommendations": [
          "Activar señalización de parking alternativo",
          "Notificar a servicios municipales"
        ]
      }
    ]
  }
}
```

#### POST /api/alarms/predictive/feedback
Proporcionar feedback sobre predicciones

**Cuerpo de la petición:**
```json
{
  "prediction_id": 1,
  "actual_outcome": "overflow_occurred",
  "accuracy_rating": 4,
  "notes": "Predicción muy acertada, pero 30 minutos antes"
}
```

### 5. Configuración de Alarmas

#### GET /api/alarms/configurations
Obtener configuraciones de alarmas

#### PUT /api/alarms/configurations/{parking_id}
Actualizar configuración de alarmas para un parking

**Cuerpo de la petición:**
```json
{
  "configuration": {
    "sensor_based_alerts": true,
    "occupancy_prediction": true,
    "trend_analysis": true,
    "thresholds": {
      "battery_low": 20,
      "signal_weak": 30,
      "sensor_offline_timeout": 300
    },
    "notification_settings": {
      "channels": ["email", "dashboard", "sms"],
      "escalation_enabled": true,
      "escalation_delay_minutes": 15
    }
  }
}
```

### 6. Perfiles de Alarmas

#### GET /api/alarms/profiles
Obtener perfiles de configuración

#### POST /api/alarms/profiles
Crear nuevo perfil

#### PUT /api/alarms/profiles/{profile_id}
Actualizar perfil existente

#### POST /api/alarms/profiles/{profile_id}/apply
Aplicar perfil a parking(s)

### 7. Analytics y Reportes

#### GET /api/analytics/sensors/health
Dashboard de salud de sensores

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "overview": {
      "total_sensors": 150,
      "active_sensors": 148,
      "offline_sensors": 2,
      "low_battery_sensors": 5,
      "poor_signal_sensors": 3
    },
    "by_parking": [
      {
        "parking_id": 1,
        "parking_name": "P. Ciutat Esportiva",
        "total_sensors": 50,
        "active_sensors": 49,
        "issues": ["SNS025: battery_low"]
      }
    ],
    "trends": {
      "uptime_trend": [
        {"date": "2025-08-01", "uptime": 99.2},
        {"date": "2025-08-02", "uptime": 99.5}
      ]
    }
  }
}
```

#### GET /api/analytics/occupancy/predictions
Predicciones de ocupación

#### GET /api/analytics/alarms/statistics
Estadísticas de alarmas

### 8. Configuración del Sistema

#### GET /api/system/sensor-types
Obtener tipos de sensores soportados

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "sensor_types": [
      {
        "type": "ultrasonic",
        "name": "Ultrasonic Distance Sensor",
        "description": "Measures distance using ultrasonic waves",
        "typical_range": "2-400 cm",
        "accuracy": "±1 cm",
        "power_consumption": "Low"
      },
      {
        "type": "magnetic",
        "name": "Magnetic Field Sensor",
        "description": "Detects metal objects via magnetic field changes",
        "typical_range": "0-2 m",
        "accuracy": "±5 cm",
        "power_consumption": "Very Low"
      }
    ]
  }
}
```

#### GET /api/system/alarm-types
Obtener tipos de alarmas disponibles

#### PUT /api/system/ml-models/{model_name}
Actualizar modelos de machine learning

## Webhooks

### Configuración de Webhooks

#### POST /api/webhooks
Crear webhook para alarmas

**Cuerpo de la petición:**
```json
{
  "url": "https://external-system.com/parking-alerts",
  "events": ["sensor_offline", "battery_low", "prediction_high_risk"],
  "headers": {
    "Authorization": "Bearer external-token",
    "Content-Type": "application/json"
  },
  "retry_policy": {
    "max_retries": 3,
    "retry_delay": 60
  }
}
```

### Formato de Webhook

```json
{
  "event_type": "sensor_offline",
  "timestamp": "2025-08-07T10:30:00Z",
  "data": {
    "sensor_id": "SNS001",
    "parking_id": 1,
    "parking_name": "P. Ciutat Esportiva",
    "plaza_number": 15,
    "severity": "critical",
    "last_seen": "2025-08-07T10:25:00Z"
  },
  "webhook_id": "webhook_123",
  "delivery_id": "delivery_456"
}
```

## Rate Limiting

### Límites por Endpoint

- **Sensor Data:** 1000 requests/minute por sensor
- **Batch Data:** 100 requests/minute
- **Query Endpoints:** 100 requests/minute por usuario
- **Configuration:** 10 requests/minute por usuario

### Headers de Rate Limiting

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1691396400
```

## Códigos de Error

### Nuevos Códigos Específicos

- `SENSOR_001`: Sensor no encontrado
- `SENSOR_002`: Sensor ya existe
- `SENSOR_003`: Configuración inválida
- `SENSOR_004`: Sensor offline
- `ALARM_001`: Alarma no encontrada
- `ALARM_002`: Configuración de alarma inválida
- `PREDICT_001`: Modelo de predicción no disponible
- `PREDICT_002`: Datos insuficientes para predicción

### Formato de Error

```json
{
  "status": "error",
  "error": {
    "code": "SENSOR_001",
    "message": "Sensor not found",
    "details": "Sensor with ID 'SNS999' does not exist",
    "suggestion": "Check sensor ID and try again"
  },
  "timestamp": "2025-08-07T10:30:00Z",
  "request_id": "req_12345"
}
```

## Versionado

### Estrategia de Versionado

- **URL Versioning:** `/api/v3/sensors`
- **Header Versioning:** `API-Version: 3.3.0`
- **Backward Compatibility:** Endpoints v3.2.0 siguen funcionando

### Migración

```http
# Antigua API (sigue funcionando)
GET /api/alarms

# Nueva API
GET /api/v3/alarms
GET /api/alarms (con header API-Version: 3.3.0)
```

## Testing de API

### Endpoints de Testing

#### POST /api/test/sensors/simulate
Simular datos de sensores para testing

#### POST /api/test/alarms/trigger
Disparar alarma de prueba

### Ambiente de Desarrollo

```bash
# Configurar variables de entorno
export API_BASE_URL=http://localhost:6001/api
export API_VERSION=3.3.0
export TEST_MODE=true
```

---

**Versión:** v3.3.0
**Estado:** En desarrollo
**Última actualización:** 7 de agosto de 2025
