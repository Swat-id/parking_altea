# Evolución del Sistema de Alarmas v3.3.0

## Introducción

La versión v3.3.0 evoluciona el sistema de alarmas existente de v3.2.0, añadiendo nuevas funcionalidades, mayor granularidad en la configuración y mejor integración con el nuevo sistema de sensores.

## Nuevas Funcionalidades

### 1. Alarmas Basadas en Sensores Individuales

Monitorización granular de cada plaza de parking:

```sql
-- Nueva tabla para alarmas de sensores
CREATE TABLE sensor_alarms (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES sensors(sensor_id),
    alarm_type VARCHAR(50) NOT NULL, -- 'sensor_offline', 'battery_low', 'signal_weak', 'malfunction'
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical', 'emergency'
    threshold_value DECIMAL(10,2),
    current_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    acknowledged_by INTEGER REFERENCES users(id),
    notes TEXT
);
```

### 2. Alarmas de Ocupación Avanzadas

Sistema más sofisticado para detección de anomalías:

```sql
-- Extender tabla de configuraciones de alarma
ALTER TABLE alarm_configurations ADD COLUMN sensor_based_alerts BOOLEAN DEFAULT FALSE;
ALTER TABLE alarm_configurations ADD COLUMN occupancy_prediction BOOLEAN DEFAULT FALSE;
ALTER TABLE alarm_configurations ADD COLUMN trend_analysis BOOLEAN DEFAULT TRUE;
ALTER TABLE alarm_configurations ADD COLUMN seasonal_adjustment BOOLEAN DEFAULT FALSE;
```

### 3. Alarmas Predictivas

Algoritmos de machine learning para predecir problemas:

```sql
-- Nueva tabla para alarmas predictivas
CREATE TABLE predictive_alarms (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id),
    prediction_type VARCHAR(50) NOT NULL, -- 'overflow_risk', 'sensor_failure', 'maintenance_needed'
    probability DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
    predicted_time TIMESTAMP NOT NULL,
    confidence_level DECIMAL(3,2) NOT NULL,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Tipos de Alarmas Expandidos

### 1. Alarmas de Hardware

#### Sensores
- **Sensor Offline:** Sensor no responde en tiempo esperado
- **Batería Baja:** Nivel de batería por debajo del umbral
- **Señal Débil:** Calidad de señal insuficiente
- **Mal funcionamiento:** Lecturas inconsistentes o erróneas
- **Calibración requerida:** Deriva en las mediciones

#### Paneles
- **Panel Desconectado:** (heredado de v3.2.0)
- **Error de Comunicación:** Fallos en el protocolo
- **Hardware Fault:** Problemas físicos del panel

#### Cámaras
- **Cámara Offline:** (heredado de v3.2.0)
- **Calidad de Imagen:** Degradación en la calidad
- **Oclusión Detectada:** Obstrucción de la vista

### 2. Alarmas Operacionales

#### Ocupación
- **Ocupación Crítica:** Parking cerca del límite
- **Ocupación Anómala:** Patrones inusuales de ocupación
- **Discrepancia de Datos:** Diferencias entre sensores y cámaras
- **Tiempo de Permanencia:** Vehículos con estancia excesiva

#### Sistema
- **Sobrecarga de Datos:** Volumen de datos excesivo
- **Latencia Alta:** Retrasos en el procesamiento
- **Error de Sincronización:** Descoordinación entre servicios
- **Fallo de Backup:** Problemas en respaldo de datos

### 3. Alarmas Predictivas

#### Mantenimiento
- **Mantenimiento Preventivo:** Basado en uso y tiempo
- **Reemplazo de Componentes:** Predicción de fallos
- **Limpieza Programada:** Según condiciones ambientales

#### Operación
- **Predicción de Saturación:** Análisis de tendencias
- **Optimización de Rutas:** Sugerencias de mejora
- **Gestión de Demanda:** Predicción de picos de uso

## Configuración Avanzada

### 1. Configuración por Niveles

```json
{
  "alarm_configuration": {
    "global": {
      "enabled": true,
      "severity_levels": ["info", "warning", "critical", "emergency"],
      "notification_delay": 30,
      "auto_acknowledgment": false
    },
    "parking_level": {
      "parking_id": 1,
      "override_global": true,
      "custom_thresholds": {
        "occupancy_critical": 95,
        "occupancy_warning": 85,
        "sensor_offline_timeout": 300
      }
    },
    "sensor_level": {
      "sensor_id": "SNS001",
      "battery_threshold": 15,
      "signal_threshold": 25,
      "malfunction_sensitivity": 0.8
    }
  }
}
```

### 2. Perfiles de Configuración

```sql
-- Tabla para perfiles de alarmas
CREATE TABLE alarm_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    configuration JSONB NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asignación de perfiles
CREATE TABLE parking_alarm_profiles (
    parking_id INTEGER REFERENCES parkings(id),
    profile_id INTEGER REFERENCES alarm_profiles(id),
    effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effective_until TIMESTAMP,
    PRIMARY KEY (parking_id, profile_id, effective_from)
);
```

### 3. Horarios de Alarmas

```json
{
  "schedule_based_alarms": {
    "working_hours": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "start_time": "08:00",
      "end_time": "18:00",
      "severity_multiplier": 1.0,
      "notification_channels": ["email", "dashboard", "sms"]
    },
    "evening_hours": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "start_time": "18:00",
      "end_time": "22:00",
      "severity_multiplier": 0.8,
      "notification_channels": ["email", "dashboard"]
    },
    "weekend": {
      "days": ["saturday", "sunday"],
      "start_time": "00:00",
      "end_time": "23:59",
      "severity_multiplier": 0.6,
      "notification_channels": ["dashboard"]
    }
  }
}
```

## API Extensions

### Nuevos Endpoints

#### Gestión de Alarmas de Sensores

```http
GET /api/alarms/sensors
POST /api/alarms/sensors
PUT /api/alarms/sensors/{alarm_id}
DELETE /api/alarms/sensors/{alarm_id}
```

#### Alarmas Predictivas

```http
GET /api/alarms/predictive
POST /api/alarms/predictive/configure
GET /api/alarms/predictive/models
```

#### Configuración Avanzada

```http
GET /api/alarms/profiles
POST /api/alarms/profiles
PUT /api/alarms/profiles/{profile_id}
DELETE /api/alarms/profiles/{profile_id}

GET /api/alarms/configurations/{parking_id}
PUT /api/alarms/configurations/{parking_id}
```

### Respuestas de API

#### GET /api/alarms/sensors
```json
{
  "sensor_alarms": [
    {
      "id": 1,
      "sensor_id": "SNS001",
      "alarm_type": "battery_low",
      "severity": "warning",
      "threshold_value": 20.0,
      "current_value": 18.0,
      "is_active": true,
      "triggered_at": "2025-08-07T10:30:00Z",
      "parking_name": "P. Ciutat Esportiva",
      "plaza_number": 15
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 23,
    "pages": 1
  }
}
```

#### GET /api/alarms/predictive
```json
{
  "predictive_alarms": [
    {
      "id": 1,
      "parking_id": 1,
      "prediction_type": "overflow_risk",
      "probability": 0.85,
      "predicted_time": "2025-08-07T14:30:00Z",
      "confidence_level": 0.92,
      "model_version": "v2.1",
      "created_at": "2025-08-07T10:00:00Z",
      "recommendations": [
        "Activar señalización de parking alternativo",
        "Notificar a servicios municipales",
        "Preparar gestión de tráfico"
      ]
    }
  ]
}
```

## Sistema de Notificaciones Mejorado

### 1. Canales de Notificación

```python
class NotificationChannel:
    EMAIL = "email"
    SMS = "sms"
    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push_notification"
```

### 2. Plantillas de Notificación

```json
{
  "notification_templates": {
    "sensor_offline": {
      "subject": "🔴 Sensor Offline - {sensor_id}",
      "body": "El sensor {sensor_id} en {parking_name} plaza {plaza_number} no responde desde {offline_time}. Requiere revisión inmediata.",
      "priority": "high",
      "actions": ["acknowledge", "schedule_maintenance", "disable_sensor"]
    },
    "battery_low": {
      "subject": "🔋 Batería Baja - {sensor_id}",
      "body": "El sensor {sensor_id} tiene batería al {battery_level}%. Programar reemplazo antes de {estimated_depletion}.",
      "priority": "medium",
      "actions": ["acknowledge", "schedule_replacement"]
    }
  }
}
```

### 3. Escalado de Alarmas

```json
{
  "escalation_rules": [
    {
      "severity": "critical",
      "steps": [
        {
          "delay_minutes": 0,
          "channels": ["dashboard", "email"],
          "recipients": ["operators"]
        },
        {
          "delay_minutes": 15,
          "channels": ["sms", "email"],
          "recipients": ["supervisors"]
        },
        {
          "delay_minutes": 30,
          "channels": ["sms", "phone"],
          "recipients": ["managers"]
        }
      ]
    }
  ]
}
```

## Machine Learning e IA

### 1. Algoritmos Predictivos

#### Predicción de Ocupación
```python
class OccupancyPredictor:
    def __init__(self):
        self.model = load_trained_model('occupancy_lstm_v2.1')
        
    def predict_occupancy(self, parking_id, hours_ahead=4):
        historical_data = get_historical_occupancy(parking_id, days=30)
        weather_data = get_weather_forecast(hours_ahead)
        events_data = get_scheduled_events(hours_ahead)
        
        features = self.prepare_features(historical_data, weather_data, events_data)
        prediction = self.model.predict(features)
        
        return {
            'predicted_occupancy': prediction,
            'confidence': self.model.confidence,
            'risk_level': self.calculate_risk_level(prediction)
        }
```

#### Detección de Anomalías
```python
class AnomalyDetector:
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1)
        self.autoencoder = load_model('anomaly_autoencoder_v1.3')
        
    def detect_sensor_anomalies(self, sensor_readings):
        # Usar ensemble de métodos
        if_score = self.isolation_forest.decision_function(sensor_readings)
        ae_score = self.autoencoder.predict(sensor_readings)
        
        combined_score = self.combine_scores(if_score, ae_score)
        return self.interpret_anomaly_score(combined_score)
```

### 2. Optimización Automática

#### Auto-tuning de Umbrales
```python
class ThresholdOptimizer:
    def optimize_thresholds(self, parking_id, alarm_type):
        # Analizar histórico de alarmas
        alarm_history = get_alarm_history(parking_id, alarm_type, days=90)
        
        # Calcular métricas de rendimiento
        false_positives = calculate_false_positives(alarm_history)
        false_negatives = calculate_false_negatives(alarm_history)
        
        # Optimizar usando algoritmo genético
        optimal_thresholds = genetic_algorithm_optimization(
            objective_function=minimize_false_alarms,
            constraints=maintain_sensitivity
        )
        
        return optimal_thresholds
```

## Dashboard y UI

### 1. Panel de Control de Alarmas

Componentes principales:
- **Vista en tiempo real:** Alarmas activas y su estado
- **Mapa de calor:** Distribución geográfica de alarmas
- **Timeline:** Historial cronológico de eventos
- **Métricas:** KPIs y estadísticas de rendimiento

### 2. Configuración Intuitiva

Interfaces para:
- Configuración de umbrales por tipo de alarma
- Gestión de perfiles de notificación
- Programación de horarios de alarmas
- Configuración de escalado

### 3. Dashboards Especializados

#### Dashboard de Sensores
- Estado de todos los sensores
- Alertas de mantenimiento
- Estadísticas de rendimiento
- Predicciones de fallos

#### Dashboard Predictivo
- Predicciones de ocupación
- Alertas tempranas
- Recomendaciones automáticas
- Análisis de tendencias

## Integración con Sistema Existente

### Compatibilidad hacia atrás
- Mantiene todas las funcionalidades de v3.2.0
- API endpoints existentes siguen funcionando
- Configuraciones existentes se migran automáticamente
- Dashboard actual se extiende con nuevas funcionalidades

### Migración
1. **Fase 1:** Actualización de base de datos
2. **Fase 2:** Despliegue de nuevos servicios
3. **Fase 3:** Migración de configuraciones
4. **Fase 4:** Activación de nuevas funcionalidades

## Testing Strategy

### Unit Tests
- Algoritmos de detección de anomalías
- Lógica de escalado de alarmas
- Predicciones de machine learning
- Configuración de umbrales

### Integration Tests
- Integración con sistema de sensores
- Compatibilidad con alarmas v3.2.0
- Flujo completo de notificaciones
- API backward compatibility

### Performance Tests
- Carga de alarmas en tiempo real
- Rendimiento de algoritmos ML
- Escalabilidad del sistema de notificaciones

---

**Versión:** v3.3.0
**Estado:** En desarrollo
**Última actualización:** 7 de agosto de 2025
