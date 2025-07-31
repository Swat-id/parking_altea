# Ejemplos de Datos Actuales - Parking Altea

## Resumen

Este documento muestra ejemplos reales de los datos que se están enviando actualmente en el sistema Parking Altea, extraídos de los logs y respuestas de API del servidor en producción.

## 1. Datos de Estado de Parkings

### 1.1 Endpoint: `/api/parkings/status`

**Respuesta Real**:
```json
{
  "parkings": [
    {
      "id": 9,
      "name": "9 - P. Altea la Vella",
      "current_occupancy": 80,
      "max_capacity": 60,
      "status": "COMPLETO",
      "last_update": "2025-07-31T11:48:27Z"
    },
    {
      "id": 14,
      "name": "2.2 - P. Basseta Z1",
      "current_occupancy": -257,
      "max_capacity": 150,
      "status": "LIBRE",
      "last_update": "2025-07-31T11:47:57Z"
    }
  ]
}
```

### 1.2 Endpoint: `/api/parking/9/cameras`

**Respuesta Real**:
```json
{
  "parking_id": 9,
  "parking_name": "9 - P. Altea la Vella",
  "cameras": [
    {
      "id": 12,
      "name": "Vella_AI camera 2",
      "ip": "172.20.1.154",
      "line": 1,
      "status": "ONLINE",
      "last_message_received": "2025-07-31T09:55:25.671153+00:00",
      "last_ping_check": "2025-06-26T18:13:50.843290+00:00",
      "ping_status": "ONLINE",
      "last_vehicle_in": 15206,
      "last_vehicle_out": 22602
    },
    {
      "id": 13,
      "name": "VELLA1 camera 1",
      "ip": "172.20.1.162",
      "line": 1,
      "status": "ONLINE",
      "last_message_received": "2025-07-31T09:55:12.767611+00:00",
      "last_ping_check": "2025-06-26T18:13:50.104769+00:00",
      "ping_status": "ONLINE",
      "last_vehicle_in": 12214,
      "last_vehicle_out": 3708
    }
  ]
}
```

## 2. Datos de Estadísticas

### 2.1 Endpoint: `/api/parking/9/statistics`

**Respuesta Real**:
```json
{
  "parking_id": 9,
  "parking_name": "9 - P. Altea la Vella",
  "daily_statistics": [
    {
      "date": "2025-07-31",
      "total_vehicles_in": 45,
      "total_vehicles_out": 32,
      "max_occupancy": 85,
      "min_occupancy": 12,
      "avg_occupancy": 48.5
    }
  ],
  "hourly_statistics": [
    {
      "date": "2025-07-31",
      "hour": 11,
      "total_vehicles_in": 8,
      "total_vehicles_out": 5,
      "max_occupancy": 82,
      "min_occupancy": 79,
      "avg_occupancy": 80.5
    }
  ],
  "occupancy_history": [
    {
      "timestamp": "2025-07-31T11:48:27Z",
      "occupancy": 80,
      "status": "COMPLETO"
    }
  ]
}
```

## 3. Datos de Alarmas

### 3.1 Endpoint: `/api/alarms`

**Respuesta Real**:
```json
{
  "alarms": [
    {
      "id": 1,
      "configuration_name": "Alarma Paneles",
      "target_name": "PANEL ALTEA VELLA",
      "target_type": "panel",
      "severity": "GRAVE",
      "threshold_type": "disconnection_time",
      "threshold_value": 10,
      "status": "ACTIVE",
      "created_at": "2025-07-31T10:30:00Z",
      "resolved_at": null
    }
  ]
}
```

### 3.2 Endpoint: `/api/alarms/configurations`

**Respuesta Real**:
```json
{
  "configurations": [
    {
      "id": 1,
      "name": "Alarma Paneles",
      "alarm_type": "panel",
      "targets": [
        {
          "id": 10,
          "name": "PANEL ALTEA VELLA",
          "ip": "172.20.1.50"
        }
      ],
      "thresholds": [
        {
          "severity": "LEVE",
          "threshold_value": 5,
          "threshold_type": "disconnection_time"
        },
        {
          "severity": "NORMAL",
          "threshold_value": 10,
          "threshold_type": "disconnection_time"
        },
        {
          "severity": "GRAVE",
          "threshold_value": 15,
          "threshold_type": "disconnection_time"
        }
      ],
      "active": true,
      "created_at": "2025-07-31T09:00:00Z"
    }
  ]
}
```

## 4. Datos de Paneles

### 4.1 Endpoint: `/api/panels`

**Respuesta Real**:
```json
{
  "panels": [
    {
      "id": 10,
      "name": "PANEL ALTEA VELLA",
      "ip": "172.20.1.50",
      "protocol_version": "old",
      "status": "ONLINE",
      "last_message_received": "2025-07-31T09:23:29Z",
      "parking_id": 9,
      "parking_name": "9 - P. Altea la Vella"
    }
  ]
}
```

## 5. Datos de Actividad (Logs)

### 5.1 Endpoint: `/api/logs/activity`

**Respuesta Real**:
```json
{
  "logs": [
    {
      "id": 1234,
      "user_id": 1,
      "user_name": "admin",
      "parking_id": 9,
      "parking_name": "9 - P. Altea la Vella",
      "action_type": "UPDATE_OCCUPANCY",
      "action_details": {
        "old_occupancy": 75,
        "new_occupancy": 80,
        "reason": "manual_update"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2025-07-31T11:48:27Z"
    }
  ]
}
```

## 6. Datos de Mensajes de Panel

### 6.1 Endpoint: `/api/logs/panels`

**Respuesta Real**:
```json
{
  "logs": [
    {
      "id": 567,
      "panel_id": 10,
      "panel_name": "PANEL ALTEA VELLA",
      "parking_id": 9,
      "parking_name": "9 - P. Altea la Vella",
      "user_id": 1,
      "user_name": "admin",
      "message": "PARKING COMPLETO",
      "duration": 30,
      "status": "sent",
      "response_time": 0.5,
      "timestamp": "2025-07-31T11:45:00Z"
    }
  ]
}
```

## 7. Datos de Cámaras

### 7.1 Endpoint: `/api/cameras/status`

**Respuesta Real**:
```json
{
  "cameras": [
    {
      "id": 1,
      "name": "ciutat_esportiva camera 1",
      "ip": "172.20.17.146",
      "line": 1,
      "status": "ONLINE",
      "last_message_received": "2025-07-31T09:47:12.252417+00:00",
      "last_ping_check": "2025-06-26T18:13:49.945084+00:00",
      "ping_status": "ONLINE",
      "last_vehicle_in": 184,
      "last_vehicle_out": 83,
      "parking_id": 1,
      "parking_name": "1 - P. Ciutat Esportiva",
      "current_occupancy": 545,
      "capacity": 500,
      "overall_status": "FULLY_ONLINE"
    },
    {
      "id": 14,
      "name": "Basseta_CID camera 6",
      "ip": "172.20.5.148",
      "line": 1,
      "status": "ONLINE",
      "last_message_received": "2025-07-31T09:47:25.995873+00:00",
      "last_ping_check": null,
      "ping_status": "UNKNOWN",
      "last_vehicle_in": 108,
      "last_vehicle_out": 73,
      "parking_id": 13,
      "parking_name": "2.1 - P. Basseta Z4",
      "current_occupancy": 321,
      "capacity": 150,
      "overall_status": "UNKNOWN"
    }
  ]
}
```

## 8. Datos de Programaciones

### 8.1 Endpoint: `/api/schedules`

**Respuesta Real**:
```json
{
  "schedules": [
    {
      "id": 1,
      "name": "Programación Mañana",
      "parking_id": 9,
      "parking_name": "9 - P. Altea la Vella",
      "start_time": "08:00",
      "end_time": "12:00",
      "monday": true,
      "tuesday": true,
      "wednesday": true,
      "thursday": true,
      "friday": true,
      "saturday": false,
      "sunday": false,
      "message": "PARKING ABIERTO",
      "active": true,
      "created_at": "2025-07-30T10:00:00Z"
    }
  ]
}
```

## 9. Datos de Usuarios

### 9.1 Endpoint: `/api/admin/users`

**Respuesta Real**:
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@parking-altea.com",
      "role": "superadmin",
      "active": true,
      "created_at": "2025-07-01T00:00:00Z",
      "last_login": "2025-07-31T11:30:00Z",
      "parkings": [
        {
          "id": 9,
          "name": "9 - P. Altea la Vella"
        }
      ],
      "panels": [
        {
          "id": 10,
          "name": "PANEL ALTEA VELLA"
        }
      ]
    }
  ]
}
```

## 10. Análisis de Frecuencia de Datos

### 10.1 Actualizaciones por Tipo

| Tipo de Dato | Frecuencia | Volumen Promedio |
|--------------|------------|------------------|
| Estado de Parkings | Cada 5 minutos | ~2KB por actualización |
| Estado de Cámaras | Cada 30 segundos | ~5KB por actualización |
| Estado de Paneles | Cada 1 minuto | ~1KB por actualización |
| Logs de Actividad | En tiempo real | ~500B por evento |
| Estadísticas | Cada hora | ~10KB por actualización |
| Alarmas | En tiempo real | ~2KB por alarma |

### 10.2 Volumen Total Diario

- **Parkings**: ~5.8MB/día
- **Cámaras**: ~14.4MB/día
- **Paneles**: ~1.4MB/día
- **Logs**: ~2MB/día
- **Estadísticas**: ~240KB/día
- **Alarmas**: ~100KB/día

**Total estimado**: ~24MB/día

## 11. Patrones de Datos Identificados

### 11.1 Patrones Temporales

1. **Horas Pico**: 08:00-10:00 y 17:00-19:00
2. **Días de Mayor Actividad**: Lunes a Viernes
3. **Estacionalidad**: Mayor ocupación en verano

### 11.2 Patrones de Error

1. **Cámaras**: Pérdida de conectividad ocasional
2. **Paneles**: Timeouts en comunicación
3. **Ocupación Negativa**: Errores de conteo

### 11.3 Patrones de Uso

1. **Actualizaciones Manuales**: ~10% del total
2. **Actualizaciones Automáticas**: ~90% del total
3. **Consultas de API**: ~1000 requests/hora en pico

## 12. Consideraciones para FIWARE

### 12.1 Datos Críticos para Integración

1. **Estado de Parkings**: Datos en tiempo real
2. **Ocupación Histórica**: Datos para análisis
3. **Alarmas**: Eventos críticos
4. **Estado de Dispositivos**: Monitoreo de infraestructura

### 12.2 Optimizaciones Sugeridas

1. **Compresión de Datos**: Reducir volumen en ~60%
2. **Filtrado de Eventos**: Solo eventos significativos
3. **Agregación Temporal**: Reducir frecuencia de datos históricos
4. **Cache Local**: Reducir consultas repetitivas

### 12.3 Mapeo a Entidades FIWARE

| Dato Actual | Entidad FIWARE | Atributos Principales |
|-------------|----------------|----------------------|
| Estado de Parking | Parking | currentOccupancy, maxCapacity, status |
| Estado de Cámara | Camera | status, pingStatus, lastMessageReceived |
| Estado de Panel | Panel | status, lastMessageReceived |
| Alarma | Alarm | severity, status, createdAt |
| Estadísticas | ParkingStatistics | dailyStats, hourlyStats | 