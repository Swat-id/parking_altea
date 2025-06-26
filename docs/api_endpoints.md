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