# API REST - Parking Altea

## Base URL
```
http://157.180.91.63:6001
```

## Endpoints Disponibles

### 1. Obtener Datos de Todos los Aparcamientos

**GET** `/parkings`

Obtiene información completa de todos los aparcamientos.

**Ejemplo de Respuesta Real:**
```json
[
  {
    "estado": "LIBRE",
    "id": 3,
    "location": "38.60068791931671,-0.056068180693698816",
    "name": "3 - P. Poble antic/Belles Arts 1",
    "plazas_libres": 200,
    "plazas_ocupadas": 0,
    "threshold_dense": 25,
    "threshold_full": 5,
    "total_plazas": 200
  },
  {
    "estado": "DESCUADRE_NEGATIVO",
    "id": 1,
    "location": "38.607426920203615,-0.04519652478288384",
    "name": "1 - P. Ciutat Esportiva",
    "plazas_libres": -50,
    "plazas_ocupadas": 500,
    "threshold_dense": 25,
    "threshold_full": 5,
    "total_plazas": 450
  },
  {
    "estado": "COMPLETO",
    "id": 5,
    "location": "38.598974152477396,-0.056511992285348776",
    "name": "5 - P. Poble antic/Palau Altea",
    "plazas_libres": 0,
    "plazas_ocupadas": 90,
    "threshold_dense": 10,
    "threshold_full": 4,
    "total_plazas": 90
  }
]
```

**Estados Posibles:**
- `LIBRE`: Plazas libres suficientes
- `DENSO`: Ocupación alta pero no completa
- `COMPLETO`: Parking lleno
- `DESCUADRE_NEGATIVO`: Ocupación mayor que capacidad máxima
- `DESCUADRE_POSITIVO`: Ocupación negativa (error de datos)

### 2. Obtener Datos de un Parking Específico

**GET** `/parking/{id}`

Obtiene información detallada de un parking específico.

**Parámetros:**
- `id`: ID del parking

**Ejemplo de Respuesta Real:**
```json
{
  "estado": "DESCUADRE_NEGATIVO",
  "id": 1,
  "location": "38.607426920203615,-0.04519652478288384",
  "name": "1 - P. Ciutat Esportiva",
  "plazas_libres": -50,
  "plazas_ocupadas": 500,
  "threshold_dense": 25,
  "threshold_full": 5,
  "total_plazas": 450
}
```

### 3. Actualizar Ocupación Manual

**POST** `/parking/{id}/occupancy`

Actualiza la ocupación de un parking de forma manual.

**Parámetros:**
- `id`: ID del parking

**Body:**
```json
{
  "occupancy": 480
}
```

**Ejemplo de Respuesta Real:**
```json
{
  "new_occupancy": 480,
  "parking": "1 - P. Ciutat Esportiva",
  "previous_occupancy": 500,
  "status": "DESCUADRE_NEGATIVO"
}
```

**Nota:** El sistema permite ocupaciones superiores a la capacidad máxima y las registra como descuadres para su posterior corrección.

### 4. Actualizar Configuración del Parking

**POST** `/parking/{id}/config`

Actualiza la capacidad máxima y los umbrales de un parking.

**Parámetros:**
- `id`: ID del parking

**Body:**
```json
{
  "max_capacity": 500,
  "threshold_dense": 30,
  "threshold_full": 10
}
```

**Ejemplo de Respuesta Real:**
```json
{
  "current_status": "DENSO",
  "max_capacity": 500,
  "parking": "1 - P. Ciutat Esportiva",
  "status": "ok",
  "threshold_dense": 30,
  "threshold_full": 10
}
```

### 5. Enviar Mensaje a Todos los Paneles de un Parking

**POST** `/parking/{id}/message`

Envía un mensaje a todos los paneles de un parking específico.

**Parámetros:**
- `id`: ID del parking

**Body:**
```json
{
  "message": "Test mensaje paneles",
  "color": "AMARILLO",
  "scroll": true
}
```

**Opciones de Color:**
- `VERDE`: Color verde
- `ROJO`: Color rojo
- `AMARILLO`: Color amarillo

**Opciones de Scroll:**
- `true`: Texto con scroll
- `false`: Texto centrado

**Ejemplo de Respuesta Real:**
```json
{
  "color": "AMARILLO",
  "message": "Test mensaje paneles",
  "panels_failed": ["172.20.17.50"],
  "panels_success": 0,
  "panels_total": 1,
  "parking": "1 - P. Ciutat Esportiva",
  "scroll": true,
  "status": "ok"
}
```

**Nota:** Si algún panel no responde, se incluye en `panels_failed` con su IP.

### 6. Enviar Mensaje a un Panel Específico

**POST** `/panel/{ip}/message`

Envía un mensaje a un panel específico por su IP.

**Parámetros:**
- `ip`: IP del panel

**Body:**
```json
{
  "message": "Mensaje personalizado",
  "color": "AMARILLO",
  "scroll": false
}
```

**Respuesta:**
```json
{
  "status": "ok",
  "panel_ip": "192.168.1.100",
  "panel_name": "Panel Principal",
  "parking": "1 - P. Ciutat Esportiva",
  "message": "Mensaje personalizado",
  "color": "AMARILLO",
  "scroll": false
}
```

### 7. Obtener Mensajes Programados

**GET** `/parking/{id}/message`

Obtiene los mensajes programados de un parking.

**Parámetros:**
- `id`: ID del parking

**Ejemplo de Respuesta Real:**
```json
[]
```

**Nota:** Si no hay mensajes programados, devuelve una lista vacía.

### 8. Programar Mensaje

**POST** `/parking/{id}/schedule`

Programa un mensaje para ser enviado en una fecha y hora específica.

**Parámetros:**
- `id`: ID del parking

**Body:**
```json
{
  "message": "Mantenimiento programado",
  "color": "ROJO",
  "scroll": true,
  "start_time": "2024-01-15T10:00:00",
  "end_time": "2024-01-15T12:00:00"
}
```

**Respuesta:**
```json
{
  "status": "ok",
  "id": 1,
  "message": "Mensaje programado correctamente"
}
```

### 9. Eliminar Mensaje Programado

**DELETE** `/schedule/{id}`

Elimina un mensaje programado.

**Parámetros:**
- `id`: ID del mensaje programado

**Respuesta:**
```json
{
  "status": "ok",
  "message": "Mensaje eliminado correctamente"
}
```

## Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `400 Bad Request`: Datos de entrada incorrectos
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error interno del servidor

## Manejo de Errores

**Ejemplo de Error:**
```json
{
  "error": "Internal server error"
}
```

## Notas Importantes

1. **Descuadres de Ocupación:** El sistema permite y registra ocupaciones que superan la capacidad máxima o son negativas, marcándolas como descuadres para su posterior corrección.

2. **Paneles No Responsivos:** Si un panel no responde al envío de mensajes, se incluye en la lista `panels_failed` pero no se considera un error crítico.

3. **Estados de Parking:** Los estados se calculan automáticamente basándose en la ocupación actual y los umbrales configurados.

4. **Logging:** Todas las operaciones se registran en logs para auditoría y debugging.

## Autenticación

### POST /auth/login
Autenticar usuario y obtener token JWT.

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "name": "Usuario Ejemplo",
    "email": "usuario@ejemplo.com"
  }
}
```

### POST /auth/register
Crear nuevo usuario.

**Body:**
```json
{
  "name": "Nuevo Usuario",
  "email": "nuevo@ejemplo.com",
  "password": "contraseña123"
}
```

### PUT /auth/password
Cambiar contraseña (requiere autenticación).

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "current_password": "contraseña_actual",
  "new_password": "nueva_contraseña"
}
```

### GET /auth/permissions
Obtener permisos del usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

### POST /auth/assign
Asignar recursos a un usuario (requiere autenticación).

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "user_id": 2,
  "parking_ids": [1, 2, 3],
  "panel_ids": [1, 2],
  "access_ids": [1, 2, 3]
}
```

## Parkings

### GET /parkings
Listar todos los parkings (público).

**Response:**
```json
[
  {
    "id": 1,
    "name": "Parking Centro",
    "location": "Calle Mayor, 1",
    "total_plazas": 100,
    "plazas_ocupadas": 75,
    "plazas_libres": 25,
    "estado": "DENSO"
  }
]
```

### GET /parking/{id}
Obtener un parking específico (público).

**Response:**
```json
{
  "id": 1,
  "name": "Parking Centro",
  "location": "Calle Mayor, 1",
  "total_plazas": 100,
  "plazas_ocupadas": 75,
  "plazas_libres": 25,
  "estado": "DENSO",
  "threshold_dense": 20,
  "threshold_full": 5
}
```

### POST /parking/{id}/occupancy
Actualizar ocupación de un parking (público).

**Body:**
```json
{
  "occupancy": 80
}
```

**Response:**
```json
{
  "status": "ok",
  "parking": "Parking Centro",
  "occupancy": 80,
  "free_spaces": 20,
  "status": "COMPLETO"
}
```

### POST /parking/{id}/config
Actualizar configuración de un parking (público).

**Body:**
```json
{
  "total_plazas": 120,
  "threshold_dense": 25,
  "threshold_full": 10
}
```

### POST /parking/{id}/message
Enviar mensaje a todos los paneles de un parking (público).

**Body:**
```json
{
  "message": "PARKING COMPLETO",
  "color": "ROJO",
  "scroll": true
}
```

## Paneles

### GET /panels
Obtener todos los paneles con su estado actual (público).

**Response:**
```json
[
  {
    "id": 1,
    "name": "Panel Entrada",
    "ip_address": "192.168.1.100",
    "parking_id": 1,
    "parking_name": "Parking Centro",
    "status": "ONLINE",
    "last_message": "PARKING COMPLETO",
    "last_update": "2024-01-15T10:30:00"
  }
]
```

### POST /panel/{id}/message
Enviar mensaje a un panel específico (público).

**Body:**
```json
{
  "message": "PRUEBA MENSAJE",
  "duration": 30
}
```

**Response:**
```json
{
  "status": "ok",
  "panel_id": 1,
  "panel_name": "Panel Entrada",
  "message": "PRUEBA MENSAJE",
  "duration": 30,
  "response_time": 150.5
}
```

### POST /panel/{id}/test
Probar comunicación con un panel (público).

**Response:**
```json
{
  "status": "ok",
  "panel_id": 1,
  "panel_name": "Panel Entrada",
  "response_time": 120.3
}
```

## Estadísticas

### GET /statistics
Obtener estadísticas de todos los parkings (público).

**Query Parameters:**
- `days` (opcional): Número de días (default: 7)

**Response:**
```json
{
  "days": 7,
  "statistics": {
    "1": {
      "parking_name": "Parking Centro",
      "statistics": {
        "daily_stats": [
          {
            "date": "2024-01-15",
            "avg_occupancy": 65.5,
            "max_occupancy": 95,
            "min_occupancy": 30,
            "peak_hour": 14,
            "total_vehicles_in": 250,
            "total_vehicles_out": 245,
            "time_libre": 300,
            "time_denso": 600,
            "time_completo": 180
          }
        ],
        "hourly_stats": [
          {
            "hour": 10,
            "avg_occupancy": 45.2,
            "max_occupancy": 60,
            "min_occupancy": 35,
            "total_vehicles_in": 15,
            "total_vehicles_out": 12
          }
        ]
      }
    }
  }
}
```

### GET /parking/{id}/statistics
Obtener estadísticas de un parking específico (público).

**Query Parameters:**
- `days` (opcional): Número de días (default: 7)

**Response:**
```json
{
  "parking_id": 1,
  "parking_name": "Parking Centro",
  "days": 7,
  "daily_stats": [...],
  "hourly_stats": [...]
}
```

### GET /parking/{id}/history
Obtener historial de ocupación de un parking (público).

**Query Parameters:**
- `limit` (opcional): Número máximo de registros (default: 100)

**Response:**
```json
{
  "parking_id": 1,
  "parking_name": "Parking Centro",
  "history": [
    {
      "id": 123,
      "timestamp": "2024-01-15T10:30:00",
      "occupancy": 75,
      "source": "manual",
      "previous_occupancy": 70,
      "change_amount": 5
    }
  ]
}
```

## Logs (Requieren Autenticación)

### GET /logs/activity
Obtener logs de actividad.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `user_id` (opcional): Filtrar por usuario
- `parking_id` (opcional): Filtrar por parking
- `action_type` (opcional): Filtrar por tipo de acción
- `limit` (opcional): Número máximo de registros (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "parking_id": 1,
      "panel_id": null,
      "action_type": "occupancy_update",
      "action_details": {
        "previous_occupancy": 70,
        "new_occupancy": 75,
        "source": "manual"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "total": 1
}
```

### GET /logs/panels
Obtener logs de mensajes de paneles.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `panel_id` (opcional): Filtrar por panel
- `parking_id` (opcional): Filtrar por parking
- `limit` (opcional): Número máximo de registros (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "panel_id": 1,
      "parking_id": 1,
      "user_id": 1,
      "message": "PARKING COMPLETO",
      "duration": 30,
      "status": "sent",
      "response_time": 150.5,
      "sent_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 1
}
```

## Endpoints Protegidos (Requieren Autenticación)

### GET /user/parkings
Obtener parkings a los que tiene acceso el usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

### GET /user/parking/{id}
Obtener un parking específico del usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

## Mensajes Programados

### GET /parking/{id}/message
Obtener mensajes programados de un parking (público).

**Response:**
```json
[
  {
    "id": 1,
    "start_time": "2024-01-15T08:00:00",
    "end_time": "2024-01-15T18:00:00",
    "message": "MANTENIMIENTO"
  }
]
```

### DELETE /parking/{id}/message
Eliminar mensaje programado (público).

**Body:**
```json
{
  "message_id": 1
}
```

## Códigos de Estado

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Datos de entrada inválidos
- `401 Unauthorized`: Autenticación requerida
- `403 Forbidden`: Acceso denegado
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error interno del servidor

## Ejemplos de Uso

### Actualizar ocupación de un parking
```bash
curl -X POST http://157.180.91.63:5000/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 80}'
```

### Obtener estadísticas de un parking
```bash
curl "http://157.180.91.63:5000/parking/1/statistics?days=7"
```

### Enviar mensaje a un panel
```bash
curl -X POST http://157.180.91.63:5000/panel/1/message \
  -H "Content-Type: application/json" \
  -d '{"message": "PRUEBA", "duration": 30}'
```

### Autenticarse y obtener token
```bash
curl -X POST http://157.180.91.63:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "toni@swat-id.com", "password": "admin123!"}' 
```

# API Endpoints - Parking Altea v2.3

## 📋 Resumen de Endpoints

**Base URL**: `http://157.180.91.63:6001`  
**Versión**: v2.3 - Modo Sin Login + Protección Duplicados + Estados Cámaras  
**Total de Endpoints**: 25 endpoints

## 🔐 Autenticación

### POST /auth/login
**Descripción**: Login de usuario  
**Método**: POST  
**Autenticación**: No requerida  
**Body**:
```json
{
  "email": "string",
  "password": "string"
}
```
**Respuesta**:
```json
{
  "token": "jwt_token",
  "user": {
    "id": 1,
    "email": "string",
    "name": "string",
    "role": "string"
  }
}
```

### POST /auth/logout
**Descripción**: Logout de usuario  
**Método**: POST  
**Autenticación**: Requerida  
**Respuesta**: `{"message": "Logged out successfully"}`

### GET /auth/me
**Descripción**: Información del usuario actual  
**Método**: GET  
**Autenticación**: Requerida (o modo sin login)  
**Respuesta**:
```json
{
  "id": 1,
  "email": "string",
  "name": "string",
  "role": "string"
}
```

## 🏢 Parkings

### GET /api/parkings
**Descripción**: Lista todos los parkings  
**Método**: GET  
**Autenticación**: Requerida  
**Respuesta**:
```json
[
  {
    "id": 1,
    "name": "string",
    "max_capacity": 500,
    "current_occupancy": 123,
    "threshold_dense": 50,
    "threshold_full": 10,
    "status": "LIBRE",
    "fixed_message_flag": false,
    "created_at": "2025-06-26T10:00:00Z",
    "updated_at": "2025-06-26T10:00:00Z"
  }
]
```

### GET /api/parkings/{id}
**Descripción**: Detalles de parking específico  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**: `id` (int) - ID del parking  
**Respuesta**:
```json
{
  "id": 1,
  "name": "string",
  "max_capacity": 500,
  "current_occupancy": 123,
  "threshold_dense": 50,
  "threshold_full": 10,
  "status": "LIBRE",
  "fixed_message_flag": false,
  "created_at": "2025-06-26T10:00:00Z",
  "updated_at": "2025-06-26T10:00:00Z",
  "accesses": [
    {
      "id": 1,
      "name": "string",
      "ip": "192.168.1.100",
      "line": 0,
      "last_vehicle_in": 1234,
      "last_vehicle_out": 567,
      "status": "ONLINE",
      "last_message_received": "2025-06-26T10:00:00Z"
    }
  ]
}
```

### PUT /api/parkings/{id}/occupancy
**Descripción**: Ajuste manual de ocupación  
**Método**: PUT  
**Autenticación**: Requerida  
**Parámetros**: `id` (int) - ID del parking  
**Body**:
```json
{
  "occupancy": 150,
  "reason": "Ajuste manual"
}
```
**Respuesta**:
```json
{
  "message": "Occupancy updated successfully",
  "parking": {
    "id": 1,
    "current_occupancy": 150,
    "status": "DENSO"
  }
}
```

## 📷 Cámaras

### GET /api/cameras
**Descripción**: Lista todas las cámaras con estado  
**Método**: GET  
**Autenticación**: Requerida  
**Respuesta**:
```json
[
  {
    "id": 1,
    "parking_id": 1,
    "parking_name": "P. Ciutat Esportiva",
    "name": "Camara_Entrada",
    "ip": "192.168.1.100",
    "line": 0,
    "last_vehicle_in": 1234,
    "last_vehicle_out": 567,
    "status": "ONLINE",
    "last_message_received": "2025-06-26T10:00:00Z"
  }
]
```

### GET /api/cameras/{id}
**Descripción**: Detalles de cámara específica  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**: `id` (int) - ID de la cámara  
**Respuesta**:
```json
{
  "id": 1,
  "parking_id": 1,
  "parking_name": "P. Ciutat Esportiva",
  "name": "Camara_Entrada",
  "ip": "192.168.1.100",
  "line": 0,
  "last_vehicle_in": 1234,
  "last_vehicle_out": 567,
  "status": "ONLINE",
  "last_message_received": "2025-06-26T10:00:00Z",
  "recent_logs": [
    {
      "id": 1,
      "raw_message": "{\"device\":\"Camara_Entrada\",\"line\":0,\"Vehicle In\":1234,\"Vehicle Out\":567}",
      "vehicle_in": 1234,
      "vehicle_out": 567,
      "delta_in": 1,
      "delta_out": 0,
      "status": "SUCCESS",
      "processing_time": 0.045,
      "new_occupancy": 124,
      "occupancy_change": 1,
      "parking_status": "LIBRE",
      "processed_at": "2025-06-26T10:00:00Z"
    }
  ]
}
```

### GET /api/cameras/{id}/logs
**Descripción**: Logs de cámara específica  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**: 
- `id` (int) - ID de la cámara
- `limit` (int, opcional) - Número de logs (default: 100)
- `offset` (int, opcional) - Offset para paginación (default: 0)
**Respuesta**:
```json
{
  "logs": [
    {
      "id": 1,
      "raw_message": "{\"device\":\"Camara_Entrada\",\"line\":0,\"Vehicle In\":1234,\"Vehicle Out\":567}",
      "vehicle_in": 1234,
      "vehicle_out": 567,
      "delta_in": 1,
      "delta_out": 0,
      "status": "SUCCESS",
      "error_message": null,
      "processing_time": 0.045,
      "new_occupancy": 124,
      "occupancy_change": 1,
      "parking_status": "LIBRE",
      "processed_at": "2025-06-26T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

## 📺 Paneles

### GET /api/panels
**Descripción**: Lista todos los paneles con estado  
**Método**: GET  
**Autenticación**: Requerida  
**Respuesta**:
```json
[
  {
    "id": 1,
    "parking_id": 1,
    "parking_name": "P. Ciutat Esportiva",
    "name": "Panel_Entrada",
    "ip": "192.168.1.200",
    "status": "ONLINE",
    "last_message": "LIBRE",
    "last_update": "2025-06-26T10:00:00Z"
  }
]
```

### POST /api/panels/verify
**Descripción**: Verificar estado de todos los paneles por ping  
**Método**: POST  
**Autenticación**: Requerida  
**Respuesta**:
```json
{
  "message": "Panel verification completed",
  "results": [
    {
      "panel_id": 1,
      "panel_name": "Panel_Entrada",
      "ip": "192.168.1.200",
      "status": "ONLINE",
      "ping_time": 0.045,
      "verified_at": "2025-06-26T10:00:00Z"
    }
  ],
  "summary": {
    "total": 10,
    "online": 8,
    "offline": 2
  }
}
```

### POST /api/panel/{id}/message
**Descripción**: Enviar mensaje a panel específico  
**Método**: POST  
**Autenticación**: Requerida  
**Parámetros**: `id` (int) - ID del panel  
**Body**:
```json
{
  "message": "LIBRE",
  "priority": "normal"
}
```
**Respuesta**:
```json
{
  "message": "Message sent successfully",
  "panel": {
    "id": 1,
    "name": "Panel_Entrada",
    "last_message": "LIBRE",
    "last_update": "2025-06-26T10:00:00Z"
  }
}
```

### POST /api/panel/{id}/test
**Descripción**: Probar comunicación con panel  
**Método**: POST  
**Autenticación**: Requerida  
**Parámetros**: `id` (int) - ID del panel  
**Respuesta**:
```json
{
  "message": "Panel test completed",
  "panel": {
    "id": 1,
    "name": "Panel_Entrada",
    "ip": "192.168.1.200",
    "status": "ONLINE",
    "ping_time": 0.045,
    "tested_at": "2025-06-26T10:00:00Z"
  }
}
```

## 📝 Logs de Cámaras

### GET /api/camera-logs
**Descripción**: Logs de todas las cámaras  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**:
- `parking_id` (int, opcional) - Filtrar por parking
- `camera_id` (int, opcional) - Filtrar por cámara
- `status` (string, opcional) - Filtrar por estado (SUCCESS, ERROR, DUPLICATE)
- `limit` (int, opcional) - Número de logs (default: 100)
- `offset` (int, opcional) - Offset para paginación (default: 0)
- `date_from` (string, opcional) - Fecha desde (YYYY-MM-DD)
- `date_to` (string, opcional) - Fecha hasta (YYYY-MM-DD)
**Respuesta**:
```json
{
  "logs": [
    {
      "id": 1,
      "access_id": 1,
      "parking_id": 1,
      "parking_name": "P. Ciutat Esportiva",
      "camera_ip": "192.168.1.100",
      "camera_line": 0,
      "camera_name": "Camara_Entrada",
      "raw_message": "{\"device\":\"Camara_Entrada\",\"line\":0,\"Vehicle In\":1234,\"Vehicle Out\":567}",
      "vehicle_in": 1234,
      "vehicle_out": 567,
      "delta_in": 1,
      "delta_out": 0,
      "status": "SUCCESS",
      "error_message": null,
      "processing_time": 0.045,
      "new_occupancy": 124,
      "occupancy_change": 1,
      "parking_status": "LIBRE",
      "processed_at": "2025-06-26T10:00:00Z"
    }
  ],
  "total": 50000,
  "limit": 100,
  "offset": 0,
  "filters": {
    "parking_id": null,
    "camera_id": null,
    "status": null,
    "date_from": null,
    "date_to": null
  }
}
```

### GET /api/camera-logs/{parking_id}
**Descripción**: Logs por parking específico  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**: 
- `parking_id` (int) - ID del parking
- `limit` (int, opcional) - Número de logs (default: 100)
- `offset` (int, opcional) - Offset para paginación (default: 0)
**Respuesta**: Misma estructura que `/api/camera-logs`

### GET /api/camera-logs/camera/{access_id}
**Descripción**: Logs por cámara específica  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**: 
- `access_id` (int) - ID de la cámara
- `limit` (int, opcional) - Número de logs (default: 100)
- `offset` (int, opcional) - Offset para paginación (default: 0)
**Respuesta**: Misma estructura que `/api/camera-logs`

## 📊 Estadísticas

### GET /api/statistics/daily
**Descripción**: Estadísticas diarias de ocupación  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**:
- `parking_id` (int, opcional) - Filtrar por parking
- `date` (string, opcional) - Fecha específica (YYYY-MM-DD, default: hoy)
**Respuesta**:
```json
{
  "date": "2025-06-26",
  "parking_id": 1,
  "parking_name": "P. Ciutat Esportiva",
  "statistics": {
    "max_occupancy": 450,
    "min_occupancy": 50,
    "avg_occupancy": 250,
    "total_vehicles_in": 1200,
    "total_vehicles_out": 1150,
    "peak_hour": "14:00",
    "peak_occupancy": 450
  },
  "hourly_data": [
    {
      "hour": "00:00",
      "occupancy": 100,
      "vehicles_in": 50,
      "vehicles_out": 45
    }
  ]
}
```

### GET /api/statistics/hourly
**Descripción**: Estadísticas por hora de ocupación  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**:
- `parking_id` (int, opcional) - Filtrar por parking
- `date` (string, opcional) - Fecha específica (YYYY-MM-DD, default: hoy)
- `hour_from` (int, opcional) - Hora desde (0-23, default: 0)
- `hour_to` (int, opcional) - Hora hasta (0-23, default: 23)
**Respuesta**:
```json
{
  "date": "2025-06-26",
  "parking_id": 1,
  "parking_name": "P. Ciutat Esportiva",
  "hourly_data": [
    {
      "hour": "00:00",
      "occupancy": 100,
      "vehicles_in": 50,
      "vehicles_out": 45,
      "net_change": 5,
      "status": "LIBRE"
    }
  ],
  "summary": {
    "total_hours": 24,
    "avg_occupancy": 250,
    "total_vehicles_in": 1200,
    "total_vehicles_out": 1150,
    "peak_hour": "14:00",
    "peak_occupancy": 450
  }
}
```

### GET /api/statistics/occupancy
**Descripción**: Historial de ocupación  
**Método**: GET  
**Autenticación**: Requerida  
**Parámetros**:
- `parking_id` (int, opcional) - Filtrar por parking
- `days` (int, opcional) - Número de días (default: 7)
- `limit` (int, opcional) - Número de registros (default: 100)
**Respuesta**:
```json
{
  "parking_id": 1,
  "parking_name": "P. Ciutat Esportiva",
  "history": [
    {
      "id": 1,
      "occupancy": 150,
      "source": "MANUAL",
      "previous_occupancy": 140,
      "change_amount": 10,
      "created_at": "2025-06-26T10:00:00Z"
    }
  ],
  "total": 100,
  "limit": 100
}
```

## 🔧 Endpoints de Sistema

### GET /api/health
**Descripción**: Estado de salud del sistema  
**Método**: GET  
**Autenticación**: No requerida  
**Respuesta**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-26T10:00:00Z",
  "version": "v2.3",
  "services": {
    "api": "running",
    "camera_server": "running",
    "database": "connected"
  }
}
```

### GET /api/system/status
**Descripción**: Estado detallado del sistema  
**Método**: GET  
**Autenticación**: Requerida  
**Respuesta**:
```json
{
  "system": {
    "version": "v2.3",
    "uptime": "5 days, 3 hours",
    "memory_usage": "129MB",
    "cpu_usage": "2%"
  },
  "database": {
    "status": "connected",
    "parkings": 9,
    "cameras": 13,
    "panels": 10,
    "logs": 50000
  },
  "cameras": {
    "total": 13,
    "online": 8,
    "offline": 5
  },
  "panels": {
    "total": 10,
    "online": 8,
    "offline": 2
  },
  "processing": {
    "messages_per_hour": 500,
    "duplicates_filtered": 25,
    "avg_processing_time": "0.045s"
  }
}
```

## 📡 Endpoints de Cámaras (Camera Server)

### POST /camera
**Descripción**: Recepción de mensajes de cámaras  
**Método**: POST  
**Autenticación**: No requerida  
**Puerto**: 6400  
**Body**:
```json
{
  "device": "Camara_Entrada",
  "line": 0,
  "Vehicle In": 1234,
  "Vehicle Out": 567,
  "event": "optional",
  "time": "optional"
}
```
**Respuesta**:
```json
{
  "status": "success",
  "message": "Message processed successfully",
  "parking_id": 1,
  "parking_name": "P. Ciutat Esportiva",
  "new_occupancy": 124,
  "occupancy_change": 1,
  "processing_time": 0.045,
  "duplicate": false
}
```

## 🔍 Códigos de Error

### Errores de Autenticación
- `401 Unauthorized`: Token inválido o expirado
- `403 Forbidden`: Sin permisos para el recurso

### Errores de Validación
- `400 Bad Request`: Datos de entrada inválidos
- `422 Unprocessable Entity`: Datos de entrada no procesables

### Errores de Recurso
- `404 Not Found`: Recurso no encontrado
- `409 Conflict`: Conflicto de datos

### Errores de Servidor
- `500 Internal Server Error`: Error interno del servidor
- `503 Service Unavailable`: Servicio no disponible

## 📋 Ejemplos de Uso

### Ejemplo: Obtener logs de cámara con filtros
```bash
curl -X GET "http://157.180.91.63:6001/api/camera-logs/camera/1?limit=50&status=SUCCESS" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Ejemplo: Verificar estado de paneles
```bash
curl -X POST "http://157.180.91.63:6001/api/panels/verify" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Ejemplo: Enviar mensaje a panel
```bash
curl -X POST "http://157.180.91.63:6001/api/panel/1/message" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "LIBRE", "priority": "normal"}'
```

### Ejemplo: Obtener estadísticas por hora
```bash
curl -X GET "http://157.180.91.63:6001/api/statistics/hourly?parking_id=1&date=2025-06-26" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 Modo Sin Login

En la versión v2.3, el sistema incluye un modo sin login para desarrollo:

- **Usuario por defecto**: `info@swat-id.com`
- **Token automático**: Se asigna automáticamente
- **Compatibilidad**: Mantiene funcionalidad de login normal
- **Configuración**: En `src/auth.py`

Para usar el modo sin login, simplemente no incluir el header `Authorization` en las peticiones. El sistema asignará automáticamente el usuario superadmin.