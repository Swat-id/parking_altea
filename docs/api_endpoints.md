# API REST - Parking Altea

## Base URL
```
http://157.180.91.63:6001
```

## Endpoints Disponibles

### 1. Obtener Datos de Todos los Aparcamientos

**GET** `/parkings`

Obtiene información completa de todos los aparcamientos.

**Respuesta:**
```json
[
  {
    "id": 1,
    "name": "1 - P. Ciutat Esportiva",
    "location": "38.607426920203615,-0.04519652478288384",
    "total_plazas": 400,
    "plazas_ocupadas": 150,
    "plazas_libres": 250,
    "estado": "LIBRE",
    "threshold_dense": 25,
    "threshold_full": 5
  }
]
```

### 2. Obtener Datos de un Parking Específico

**GET** `/parking/{id}`

Obtiene información detallada de un parking específico.

**Parámetros:**
- `id`: ID del parking

**Respuesta:**
```json
{
  "id": 1,
  "name": "1 - P. Ciutat Esportiva",
  "location": "38.607426920203615,-0.04519652478288384",
  "total_plazas": 400,
  "plazas_ocupadas": 150,
  "plazas_libres": 250,
  "estado": "LIBRE",
  "threshold_dense": 25,
  "threshold_full": 5
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
  "occupancy": 200
}
```

**Respuesta:**
```json
{
  "status": "ok",
  "parking": "1 - P. Ciutat Esportiva",
  "previous_occupancy": 150,
  "new_occupancy": 200,
  "status": "DENSO"
}
```

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

**Respuesta:**
```json
{
  "status": "ok",
  "parking": "1 - P. Ciutat Esportiva",
  "max_capacity": 500,
  "threshold_dense": 30,
  "threshold_full": 10,
  "current_status": "DENSO"
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
  "message": "Parking cerrado por mantenimiento",
  "color": "ROJO",
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

**Respuesta:**
```json
{
  "status": "ok",
  "parking": "1 - P. Ciutat Esportiva",
  "message": "Parking cerrado por mantenimiento",
  "color": "ROJO",
  "scroll": true,
  "panels_total": 2,
  "panels_success": 2,
  "panels_failed": []
}
```

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

**Respuesta:**
```json
[
  {
    "id": 1,
    "start_time": "2024-01-15T10:00:00",
    "end_time": "2024-01-15T18:00:00",
    "message": "Mantenimiento programado"
  }
]
```

### 8. Eliminar Mensaje Programado

**DELETE** `/parking/{id}/message`

Elimina un mensaje programado de un parking.

**Parámetros:**
- `id`: ID del parking

**Body:**
```json
{
  "message_id": 1
}
```

**Respuesta:**
```json
{
  "status": "ok"
}
```

## Estados de Parking

Los parkings pueden tener los siguientes estados:

- **LIBRE**: Más de `threshold_dense` plazas libres
- **DENSO**: Entre `threshold_full` y `threshold_dense` plazas libres
- **COMPLETO**: Menos de `threshold_full` plazas libres
- **COMPLETO_EXCESO**: Ocupación por encima de la capacidad máxima (exceso de vehículos)
- **DESCUADRE_NEGATIVO**: Plazas libres negativas (error de conteo o overflow)

### Gestión de Descuadres

El sistema permite y registra automáticamente los siguientes descuadres:

1. **Exceso de Ocupación**: Cuando hay más vehículos que plazas disponibles
   - Se registra como `EXCESS:{número_de_vehículos_extra}`
   - Estado: `COMPLETO_EXCESO`

2. **Plazas Libres Negativas**: Cuando el conteo indica más vehículos que capacidad
   - Se registra como `NEGATIVE_FREE:{número_de_vehículos_extra}`
   - Estado: `DESCUADRE_NEGATIVO`

Estos descuadres se registran en el histórico de ocupación para:
- Análisis estadístico posterior
- Correcciones automáticas diarias
- Identificación de problemas en el sistema de conteo
- Auditoría de la precisión del sistema

## Códigos de Error

- **400**: Bad Request - Datos incorrectos o faltantes
- **404**: Not Found - Recurso no encontrado
- **500**: Internal Server Error - Error interno del servidor

## Ejemplos de Uso

### Actualizar ocupación del parking 1
```bash
curl -X POST http://157.180.91.63:6001/parking/1/occupancy \
  -H 'Content-Type: application/json' \
  -d '{"occupancy": 300}'
```

### Enviar mensaje a todos los paneles del parking 1
```bash
curl -X POST http://157.180.91.63:6001/parking/1/message \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Parking casi completo",
    "color": "AMARILLO",
    "scroll": true
  }'
```

### Enviar mensaje a un panel específico
```bash
curl -X POST http://157.180.91.63:6001/panel/192.168.1.100/message \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Mantenimiento en curso",
    "color": "ROJO",
    "scroll": false
  }'
```

### Actualizar configuración del parking
```bash
curl -X POST http://157.180.91.63:6001/parking/1/config \
  -H 'Content-Type: application/json' \
  -d '{
    "max_capacity": 450,
    "threshold_dense": 30,
    "threshold_full": 10
  }'
``` 