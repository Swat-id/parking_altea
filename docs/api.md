# API REST - Parking Altea

## Información General

- **URL Base**: `http://157.180.91.63:6001`
- **Formato**: JSON
- **Autenticación**: No requerida (pública)
- **Versión**: 1.1

## Endpoints Disponibles

### 1. Listar Aparcamientos

**GET** `/parkings`

Obtiene la lista de todos los aparcamientos con información completa.

#### Respuesta Exitosa (200)

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
  },
  {
    "id": 2,
    "name": "2 - P. Basseta Centre",
    "location": "38.60350663228926,-0.05041100707116167",
    "total_plazas": 500,
    "plazas_ocupadas": 450,
    "plazas_libres": 50,
    "estado": "DENSO",
    "threshold_dense": 30,
    "threshold_full": 10
  }
]
```

#### Ejemplo de Uso

```bash
curl http://157.180.91.63:6001/parkings
```

### 2. Obtener Detalle de Aparcamiento

**GET** `/parking/{id}`

Obtiene información detallada de un aparcamiento específico.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Respuesta Exitosa (200)

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

#### Respuesta de Error (404)

```json
{
  "error": "Parking not found"
}
```

#### Ejemplo de Uso

```bash
curl http://157.180.91.63:6001/parking/1
```

### 3. Actualizar Ocupación Manual

**POST** `/parking/{id}/occupancy`

Permite actualizar manualmente la ocupación de un aparcamiento. **Permite valores por encima del máximo y plazas libres negativas**.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Cuerpo de la Petición

```json
{
  "occupancy": 200
}
```

#### Respuesta Exitosa (200)

```json
{
  "status": "ok",
  "parking": "1 - P. Ciutat Esportiva",
  "previous_occupancy": 150,
  "new_occupancy": 200,
  "status": "DENSO"
}
```

#### Respuesta de Error (400)

```json
{
  "error": "Missing occupancy field"
}
```

#### Respuesta de Error (404)

```json
{
  "error": "Parking not found"
}
```

#### Ejemplo de Uso

```bash
curl -X POST http://157.180.91.63:6001/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 200}'
```

### 4. Actualizar Configuración del Parking

**POST** `/parking/{id}/config`

Actualiza la capacidad máxima y los umbrales de un aparcamiento.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Cuerpo de la Petición

```json
{
  "max_capacity": 500,
  "threshold_dense": 30,
  "threshold_full": 10
}
```

**Nota**: Todos los campos son opcionales. Solo se actualizarán los campos proporcionados.

#### Respuesta Exitosa (200)

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

#### Ejemplo de Uso

```bash
curl -X POST http://157.180.91.63:6001/parking/1/config \
  -H "Content-Type: application/json" \
  -d '{
    "max_capacity": 500,
    "threshold_dense": 30,
    "threshold_full": 10
  }'
```

### 5. Enviar Mensaje a Todos los Paneles de un Parking

**POST** `/parking/{id}/message`

Envía un mensaje a todos los paneles de un aparcamiento específico.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Cuerpo de la Petición

```json
{
  "message": "Parking cerrado por mantenimiento",
  "color": "ROJO",
  "scroll": true
}
```

#### Opciones de Color

- `VERDE`: Color verde (por defecto)
- `ROJO`: Color rojo
- `AMARILLO`: Color amarillo

#### Opciones de Scroll

- `true`: Texto con scroll
- `false`: Texto centrado (por defecto)

#### Respuesta Exitosa (200)

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

#### Respuesta de Error (404)

```json
{
  "error": "No panels found for this parking"
}
```

#### Ejemplo de Uso

```bash
curl -X POST http://157.180.91.63:6001/parking/1/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Parking casi completo",
    "color": "AMARILLO",
    "scroll": true
  }'
```

### 6. Enviar Mensaje a un Panel Específico

**POST** `/panel/{ip}/message`

Envía un mensaje a un panel específico por su IP.

#### Parámetros

- `ip` (string, requerido): IP del panel

#### Cuerpo de la Petición

```json
{
  "message": "Mensaje personalizado",
  "color": "AMARILLO",
  "scroll": false
}
```

#### Respuesta Exitosa (200)

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

#### Respuesta de Error (404)

```json
{
  "error": "Panel not found"
}
```

#### Ejemplo de Uso

```bash
curl -X POST http://157.180.91.63:6001/panel/192.168.1.100/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mantenimiento en curso",
    "color": "ROJO",
    "scroll": false
  }'
```

### 7. Obtener Mensajes Programados

**GET** `/parking/{id}/message`

Obtiene los mensajes programados de un aparcamiento.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Respuesta Exitosa (200)

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

#### Ejemplo de Uso

```bash
curl http://157.180.91.63:6001/parking/1/message
```

### 8. Eliminar Mensaje Programado

**DELETE** `/parking/{id}/message`

Elimina un mensaje programado de un aparcamiento.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Cuerpo de la Petición

```json
{
  "message_id": 1
}
```

#### Respuesta Exitosa (200)

```json
{
  "status": "ok"
}
```

#### Ejemplo de Uso

```bash
curl -X DELETE http://157.180.91.63:6001/parking/1/message \
  -H "Content-Type: application/json" \
  -d '{"message_id": 1}'
```

## Estados de Aparcamiento

Los aparcamientos pueden tener los siguientes estados:

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

## Códigos de Estado HTTP

- **200**: Operación exitosa
- **400**: Error en la petición (datos inválidos o faltantes)
- **404**: Recurso no encontrado
- **500**: Error interno del servidor

## Ejemplos de Integración

### JavaScript (Fetch API)

```javascript
// Obtener lista de aparcamientos
async function getParkings() {
  const response = await fetch('http://157.180.91.63:6001/parkings');
  const parkings = await response.json();
  return parkings;
}

// Actualizar ocupación
async function updateOccupancy(parkingId, occupancy) {
  const response = await fetch(`http://157.180.91.63:6001/parking/${parkingId}/occupancy`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ occupancy })
  });
  return await response.json();
}

// Enviar mensaje a paneles
async function sendMessage(parkingId, message, color = 'VERDE', scroll = false) {
  const response = await fetch(`http://157.180.91.63:6001/parking/${parkingId}/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, color, scroll })
  });
  return await response.json();
}

// Actualizar configuración
async function updateConfig(parkingId, config) {
  const response = await fetch(`http://157.180.91.63:6001/parking/${parkingId}/config`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  });
  return await response.json();
}
```

### Python (requests)

```python
import requests

BASE_URL = "http://157.180.91.63:6001"

# Obtener parkings
def get_parkings():
    response = requests.get(f"{BASE_URL}/parkings")
    return response.json()

# Actualizar ocupación
def update_occupancy(parking_id, occupancy):
    response = requests.post(
        f"{BASE_URL}/parking/{parking_id}/occupancy",
        json={"occupancy": occupancy}
    )
    return response.json()

# Enviar mensaje
def send_message(parking_id, message, color="VERDE", scroll=False):
    response = requests.post(
        f"{BASE_URL}/parking/{parking_id}/message",
        json={"message": message, "color": color, "scroll": scroll}
    )
    return response.json()

# Actualizar configuración
def update_config(parking_id, max_capacity=None, threshold_dense=None, threshold_full=None):
    config = {}
    if max_capacity is not None:
        config["max_capacity"] = max_capacity
    if threshold_dense is not None:
        config["threshold_dense"] = threshold_dense
    if threshold_full is not None:
        config["threshold_full"] = threshold_full
    
    response = requests.post(
        f"{BASE_URL}/parking/{parking_id}/config",
        json=config
    )
    return response.json()
```

## Casos de Uso Comunes

### 1. Monitoreo de Ocupación

```bash
# Obtener estado actual de todos los parkings
curl http://157.180.91.63:6001/parkings

# Obtener detalle de un parking específico
curl http://157.180.91.63:6001/parking/1
```

### 2. Corrección Manual de Ocupación

```bash
# Corregir ocupación por exceso
curl -X POST http://157.180.91.63:6001/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 400}'

# Corregir ocupación por descuadre negativo
curl -X POST http://157.180.91.63:6001/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 0}'
```

### 3. Gestión de Mensajes

```bash
# Mensaje de emergencia
curl -X POST http://157.180.91.63:6001/parking/1/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "PARKING CERRADO - EMERGENCIA",
    "color": "ROJO",
    "scroll": true
  }'

# Mensaje informativo
curl -X POST http://157.180.91.63:6001/parking/1/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mantenimiento programado mañana",
    "color": "AMARILLO",
    "scroll": false
  }'
```

### 4. Ajuste de Configuración

```bash
# Aumentar capacidad por excesos frecuentes
curl -X POST http://157.180.91.63:6001/parking/1/config \
  -H "Content-Type: application/json" \
  -d '{"max_capacity": 450}'

# Ajustar umbrales
curl -X POST http://157.180.91.63:6001/parking/1/config \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_dense": 30,
    "threshold_full": 10
  }'
``` 