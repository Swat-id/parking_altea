# API REST - Parking Altea

## Información General

- **URL Base**: `http://157.180.91.63:6001`
- **Formato**: JSON
- **Autenticación**: No requerida (pública)
- **Versión**: 1.0

## Endpoints Disponibles

### 1. Listar Aparcamientos

**GET** `/parkings`

Obtiene la lista de todos los aparcamientos con información básica.

#### Respuesta Exitosa (200)

```json
[
  {
    "id": 1,
    "name": "1 - P. Ciutat Esportiva",
    "location": "38.607426920203615,-0.04519652478288384",
    "max_capacity": 400,
    "current_occupancy": 150,
    "status": "LIBRE"
  },
  {
    "id": 2,
    "name": "2 - P. Basseta Centre",
    "location": "38.60350663228926,-0.05041100707116167",
    "max_capacity": 500,
    "current_occupancy": 450,
    "status": "DENSO"
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
  "max_capacity": 400,
  "current_occupancy": 150,
  "free_spaces": 250,
  "status": "LIBRE"
}
```

#### Respuesta de Error (404)

```json
{
  "error": "Not found"
}
```

#### Ejemplo de Uso

```bash
curl http://157.180.91.63:6001/parking/1
```

### 3. Actualizar Ocupación Manual

**POST** `/parking/{id}/occupancy`

Permite actualizar manualmente la ocupación de un aparcamiento.

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
  "status": "ok"
}
```

#### Respuesta de Error (404)

```json
{
  "error": "Not found"
}
```

#### Ejemplo de Uso

```bash
curl -X POST http://157.180.91.63:6001/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 200}'
```

### 4. Programar Mensaje en Paneles

**POST** `/parking/{id}/message`

Programa un mensaje personalizado para mostrar en los paneles de un aparcamiento durante un período específico.

#### Parámetros

- `id` (integer, requerido): ID del aparcamiento

#### Cuerpo de la Petición

```json
{
  "start": "2025-01-15T10:00:00",
  "end": "2025-01-15T18:00:00",
  "message": "Mantenimiento programado"
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
curl -X POST http://157.180.91.63:6001/parking/1/message \
  -H "Content-Type: application/json" \
  -d '{
    "start": "2025-01-15T10:00:00",
    "end": "2025-01-15T18:00:00",
    "message": "Mantenimiento programado"
  }'
```

## Códigos de Estado HTTP

- **200**: Operación exitosa
- **400**: Error en la petición (datos inválidos)
- **404**: Recurso no encontrado
- **500**: Error interno del servidor

## Estados de Aparcamiento

Los aparcamientos pueden tener los siguientes estados calculados automáticamente:

- **LIBRE**: Ocupación por debajo del umbral denso
- **DENSO**: Ocupación entre el umbral denso y el umbral completo
- **OCUPADO**: Ocupación igual o superior al umbral completo

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
  return response.json();
}
```

### Python (requests)

```python
import requests

# Obtener lista de aparcamientos
def get_parkings():
    response = requests.get('http://157.180.91.63:6001/parkings')
    return response.json()

# Actualizar ocupación
def update_occupancy(parking_id, occupancy):
    data = {'occupancy': occupancy}
    response = requests.post(
        f'http://157.180.91.63:6001/parking/{parking_id}/occupancy',
        json=data
    )
    return response.json()
```

## Limitaciones y Consideraciones

1. **Rate Limiting**: No implementado actualmente
2. **Caché**: No implementado, todas las consultas son en tiempo real
3. **Paginación**: No implementada para listas grandes
4. **Filtros**: No implementados, se obtienen todos los aparcamientos
5. **Ordenación**: No implementada

## Próximas Mejoras

- [ ] Autenticación y autorización
- [ ] Rate limiting
- [ ] Paginación para listas grandes
- [ ] Filtros por estado, ubicación, etc.
- [ ] Endpoints para histórico de ocupación
- [ ] Webhooks para notificaciones
- [ ] Documentación OpenAPI/Swagger 