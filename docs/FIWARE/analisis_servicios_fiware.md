# Análisis de Servicios FIWARE - Parking Altea

## Resumen Ejecutivo

Este documento analiza los servicios del sistema Parking Altea que potencialmente integran datos en plataformas FIWARE para el monitoreo del estado de los parkings. El análisis se centra en identificar los servicios de datos, su operativa, campos enviados y lógica de integración.

## Arquitectura General del Sistema

### Servicios Identificados

El sistema Parking Altea está compuesto por los siguientes servicios principales:

1. **API Server** (`src/api_server.py`) - Servidor principal de API REST
2. **Panel Communication Service** (`src/panel_communication_service.py`) - Comunicación con paneles LED
3. **Statistics Service** (`src/statistics.py`) - Gestión de estadísticas y logs
4. **Schedule Monitor Service** (`src/schedule_monitor_service.py`) - Monitorización de programaciones
5. **Alarm Monitor Service** (`src/alarm_monitor_service.py`) - Monitorización de alarmas
6. **Email Service** (`src/email_service.py`) - Notificaciones por email
7. **Camera Server** (`src/camera_server.py`) - Servidor de cámaras

## Análisis Detallado por Servicio

### 1. API Server (src/api_server.py)

**Propósito**: Servidor principal que expone endpoints REST para el frontend y potenciales integraciones externas.

**Endpoints Relevantes para FIWARE**:

#### 1.1 Estado de Parkings
```python
@api_bp.route('/parkings/status', methods=['GET'])
def get_parkings_status():
    """Obtener estado actual de todos los parkings"""
```

**Campos Enviados**:
- `parking_id`: ID del parking
- `name`: Nombre del parking
- `current_occupancy`: Ocupación actual
- `max_capacity`: Capacidad máxima
- `status`: Estado del parking (COMPLETO, LIBRE, etc.)
- `last_update`: Última actualización

#### 1.2 Estadísticas de Parking
```python
@api_bp.route('/parking/<int:pid>/statistics', methods=['GET'])
def get_parking_statistics(pid):
    """Obtener estadísticas detalladas de un parking"""
```

**Campos Enviados**:
- `parking_id`: ID del parking
- `daily_statistics`: Estadísticas diarias
- `hourly_statistics`: Estadísticas por hora
- `occupancy_history`: Historial de ocupación
- `vehicle_counts`: Conteos de vehículos

#### 1.3 Estado de Cámaras
```python
@api_bp.route('/cameras/status', methods=['GET'])
def get_all_cameras_status():
    """Obtener estado de todas las cámaras"""
```

**Campos Enviados**:
- `camera_id`: ID de la cámara
- `name`: Nombre de la cámara
- `ip`: IP de la cámara
- `status`: Estado (ONLINE/OFFLINE)
- `ping_status`: Estado del ping
- `last_message_received`: Último mensaje recibido
- `parking_id`: Parking asociado

### 2. Statistics Service (src/statistics.py)

**Propósito**: Gestión centralizada de estadísticas y logs del sistema.

**Funciones Principales**:

#### 2.1 Log de Actividades
```python
def log_activity(self, user_id=None, parking_id=None, panel_id=None, 
                action_type='', action_details=None, ip_address=None, user_agent=None):
```

**Campos Registrados**:
- `user_id`: ID del usuario
- `parking_id`: ID del parking
- `panel_id`: ID del panel
- `action_type`: Tipo de acción
- `action_details`: Detalles de la acción (JSON)
- `ip_address`: IP del usuario
- `user_agent`: User agent del navegador
- `timestamp`: Timestamp automático

#### 2.2 Estadísticas por Hora
```python
def update_hourly_statistics(self, parking_id, date=None):
```

**Campos Calculados**:
- `parking_id`: ID del parking
- `date`: Fecha
- `hour`: Hora (0-23)
- `total_vehicles_in`: Total vehículos entrantes
- `total_vehicles_out`: Total vehículos salientes
- `max_occupancy`: Ocupación máxima
- `min_occupancy`: Ocupación mínima
- `avg_occupancy`: Ocupación promedio

#### 2.3 Estadísticas Diarias
```python
def update_daily_statistics(self, parking_id, date=None):
```

**Campos Calculados**:
- `parking_id`: ID del parking
- `date`: Fecha
- `total_vehicles_in`: Total vehículos entrantes del día
- `total_vehicles_out`: Total vehículos salientes del día
- `max_occupancy`: Ocupación máxima del día
- `min_occupancy`: Ocupación mínima del día
- `avg_occupancy`: Ocupación promedio del día

### 3. Alarm Monitor Service (src/alarm_monitor_service.py)

**Propósito**: Monitorización continua de dispositivos y generación de alarmas.

**Funciones Principales**:

#### 3.1 Verificación de Dispositivos
```python
def _check_all_alarm_conditions(self):
    """Verificar todas las condiciones de alarma configuradas"""
```

**Campos Monitoreados**:
- `device_ip`: IP del dispositivo
- `device_type`: Tipo (panel/cámara)
- `ping_status`: Estado del ping
- `last_ping_check`: Última verificación de ping
- `disconnection_duration`: Duración de desconexión

#### 3.2 Generación de Alarmas
```python
def _create_alarm(self, config_id, target_id, target_type, severity, threshold_type, threshold_value):
```

**Campos de Alarma**:
- `configuration_id`: ID de la configuración
- `target_id`: ID del objetivo
- `target_type`: Tipo de objetivo
- `severity`: Severidad (LEVE/NORMAL/GRAVE)
- `threshold_type`: Tipo de umbral
- `threshold_value`: Valor del umbral
- `created_at`: Timestamp de creación

### 4. Email Service (src/email_service.py)

**Propósito**: Envío de notificaciones por email para alarmas y eventos del sistema.

**Funciones Principales**:

#### 4.1 Notificación de Alarmas
```python
def send_alarm_notification(self, user_email: str, alarm_data: Dict[str, Any]) -> bool:
```

**Campos Enviados**:
- `severity`: Severidad de la alarma
- `configuration_name`: Nombre de la configuración
- `target_name`: Nombre del objetivo
- `target_type`: Tipo de objetivo
- `threshold_type`: Tipo de umbral
- `threshold_value`: Valor del umbral
- `created_at`: Timestamp de creación
- `details`: Detalles adicionales

## Integración Potencial con FIWARE

### 1. Context Broker (Orion)

**Endpoints Sugeridos para Integración**:

#### 1.1 Entidad Parking
```json
{
  "id": "Parking:Altea:001",
  "type": "Parking",
  "name": {
    "value": "9 - P. Altea la Vella",
    "type": "Text"
  },
  "currentOccupancy": {
    "value": 80,
    "type": "Number"
  },
  "maxCapacity": {
    "value": 60,
    "type": "Number"
  },
  "occupancyPercentage": {
    "value": 133.33,
    "type": "Number"
  },
  "status": {
    "value": "COMPLETO",
    "type": "Text"
  },
  "location": {
    "value": {
      "type": "Point",
      "coordinates": [38.5989, -0.0513]
    },
    "type": "geo:json"
  },
  "dateModified": {
    "value": "2025-07-31T11:48:27Z",
    "type": "DateTime"
  }
}
```

#### 1.2 Entidad Camera
```json
{
  "id": "Camera:Altea:012",
  "type": "Camera",
  "name": {
    "value": "Vella_AI camera 2",
    "type": "Text"
  },
  "ip": {
    "value": "172.20.1.154",
    "type": "Text"
  },
  "status": {
    "value": "ONLINE",
    "type": "Text"
  },
  "pingStatus": {
    "value": "ONLINE",
    "type": "Text"
  },
  "lastMessageReceived": {
    "value": "2025-07-31T09:55:25.671153Z",
    "type": "DateTime"
  },
  "parkingId": {
    "value": "Parking:Altea:009",
    "type": "Text"
  },
  "location": {
    "value": {
      "type": "Point",
      "coordinates": [38.5989, -0.0513]
    },
    "type": "geo:json"
  }
}
```

#### 1.3 Entidad Alarm
```json
{
  "id": "Alarm:Altea:001",
  "type": "Alarm",
  "severity": {
    "value": "GRAVE",
    "type": "Text"
  },
  "configurationName": {
    "value": "Alarma Paneles",
    "type": "Text"
  },
  "targetName": {
    "value": "PANEL ALTEA VELLA",
    "type": "Text"
  },
  "targetType": {
    "value": "panel",
    "type": "Text"
  },
  "thresholdType": {
    "value": "disconnection_time",
    "type": "Text"
  },
  "thresholdValue": {
    "value": 10,
    "type": "Number"
  },
  "status": {
    "value": "ACTIVE",
    "type": "Text"
  },
  "createdAt": {
    "value": "2025-07-31T10:30:00Z",
    "type": "DateTime"
  }
}
```

### 2. Cygnus (Histórico de Datos)

**Configuración Sugerida**:

#### 2.1 Sink de MongoDB
```yaml
cygnus-ngsi:
  sources:
    - type: http
      port: 5050
  sinks:
    - type: com.telefonica.iot.cygnus.sinks.OrionMongoSink
      channel: mongo-channel
      mongo_hosts: localhost:27017
      mongo_database: parking_altea
      mongo_collection: parking_data
```

#### 2.2 Sink de PostgreSQL
```yaml
cygnus-ngsi:
  sources:
    - type: http
      port: 5050
  sinks:
    - type: com.telefonica.iot.cygnus.sinks.OrionPostgreSQLSink
      channel: postgresql-channel
      postgresql_host: localhost
      postgresql_port: 5432
      postgresql_database: fiware_parking
      postgresql_username: fiware_user
      postgresql_password: fiware_pass
```

### 3. QuantumLeap (API de Consulta Temporal)

**Endpoints Sugeridos**:

#### 3.1 Consulta de Ocupación Histórica
```bash
GET /v2/entities/Parking:Altea:001/attrs/currentOccupancy?type=Parking&lastN=24
```

#### 3.2 Consulta de Alarmas por Período
```bash
GET /v2/entities?type=Alarm&q=createdAt>=2025-07-31T00:00:00Z;createdAt<=2025-07-31T23:59:59Z
```

## Implementación Recomendada

### 1. Adaptador de Datos

Crear un servicio adaptador que transforme los datos del sistema Parking Altea al formato NGSI-LD:

```python
# fiware_adapter.py
import requests
import json
from datetime import datetime
from typing import Dict, List

class FIWAREAdapter:
    def __init__(self, orion_url: str, quantumleap_url: str):
        self.orion_url = orion_url
        self.quantumleap_url = quantumleap_url
    
    def update_parking_status(self, parking_data: Dict):
        """Actualizar estado de parking en Orion"""
        entity = {
            "id": f"Parking:Altea:{parking_data['id']:03d}",
            "type": "Parking",
            "currentOccupancy": {
                "value": parking_data['current_occupancy'],
                "type": "Number"
            },
            "maxCapacity": {
                "value": parking_data['max_capacity'],
                "type": "Number"
            },
            "status": {
                "value": parking_data['status'],
                "type": "Text"
            },
            "dateModified": {
                "value": datetime.now().isoformat() + "Z",
                "type": "DateTime"
            }
        }
        
        response = requests.post(
            f"{self.orion_url}/v2/entities",
            json=entity,
            headers={"Content-Type": "application/json"}
        )
        return response.status_code == 201
```

### 2. Configuración de Suscripciones

Configurar suscripciones en Orion para notificaciones automáticas:

```json
{
  "description": "Suscripción a cambios de ocupación de parkings",
  "subject": {
    "entities": [
      {
        "idPattern": "Parking:Altea:.*",
        "type": "Parking"
      }
    ],
    "condition": {
      "attrs": ["currentOccupancy", "status"]
    }
  },
  "notification": {
    "http": {
      "url": "http://localhost:6001/api/fiware/notifications"
    },
    "attrs": ["currentOccupancy", "maxCapacity", "status", "dateModified"]
  }
}
```

## Conclusión

El sistema Parking Altea tiene una arquitectura sólida para la integración con FIWARE. Los servicios existentes ya proporcionan:

1. **Datos estructurados** de parkings, cámaras y alarmas
2. **APIs REST** bien definidas
3. **Sistema de logging** completo
4. **Monitorización en tiempo real** de dispositivos

La implementación de la integración con FIWARE requeriría:

1. **Adaptador de datos** para transformar al formato NGSI-LD
2. **Configuración de Orion** para entidades y suscripciones
3. **Cygnus** para almacenamiento histórico
4. **QuantumLeap** para consultas temporales

Esta integración permitiría el intercambio de datos con otros sistemas smart city y la participación en ecosistemas FIWARE más amplios. 