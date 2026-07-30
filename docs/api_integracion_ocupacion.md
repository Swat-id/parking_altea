# API de Integración - Ocupación de Parkings

**Versión**: 5.0.0  
**Última actualización**: Julio 2026  
**Servidor**: `http://localhost:6001` (desde la misma máquina)

---

## 1. Credenciales de Superadmin

| Campo | Valor |
|-------|-------|
| **Email** | `info@swat-id.com` |
| **Password** | `admin123!` |
| **Rol** | `superadmin` |

> **Nota**: Se recomienda cambiar la contraseña en producción.

---

## 2. Autenticación

Todas las llamadas a la API requieren un token JWT en el header `Authorization`.

### 2.1 Obtener Token

**Endpoint**: `POST /api/auth/login`

**Comando**:
```bash
curl -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}'
```

**Respuesta exitosa**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImluZm9Ac3dhdC1pZC5jb20iLCJyb2xlIjoic3VwZXJhZG1pbiIsImV4cCI6MTcyMjUwMDAwMH0.xxxxx",
  "user": {
    "id": 1,
    "email": "info@swat-id.com",
    "name": "Administrador",
    "role": "superadmin"
  }
}
```

**Uso del token**: Incluir en todas las llamadas posteriores:
```
Authorization: Bearer <token>
```

---

## 3. Obtener Estado de Ocupación de Todos los Parkings

**Endpoint**: `GET /api/parkings/status`

**Descripción**: Obtiene el estado completo de ocupación de todos los parkings accesibles por el usuario.

### 3.1 Comando

```bash
# Primero obtener el token
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | jq -r '.token')

# Luego consultar el estado
curl -s -X GET http://localhost:6001/api/parkings/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

### 3.2 Respuesta

```json
{
  "success": true,
  "total_parkings": 3,
  "timestamp": "2026-07-30T10:20:00.123456",
  "parkings": [
    {
      "id": 1,
      "name": "P. Ciutat Esportiva",
      "location": "Calle Principal 1",
      "total_plazas": 100,
      "plazas_ocupadas": 45,
      "plazas_libres": 55,
      "estado": "LIBRE",
      "estado_valenciano": "LLIURE",
      "panel_display_text": "LLIURE",
      "has_active_schedules": false,
      "active_schedules_count": 0,
      "threshold_dense": 20,
      "threshold_full": 5,
      "panels": [
        {
          "id": 1,
          "name": "PANEL ENTRADA",
          "ip": "172.20.17.50",
          "status": "online",
          "protocol_version": "old",
          "last_message": "LLIURE",
          "last_update": "2026-07-30T10:15:00.000000"
        }
      ],
      "last_update": "2026-07-30T10:20:00.123456"
    },
    {
      "id": 5,
      "name": "P. Poble antic/Palau Altea",
      "location": "Plaza Mayor",
      "total_plazas": 50,
      "plazas_ocupadas": 48,
      "plazas_libres": 2,
      "estado": "COMPLETO",
      "estado_valenciano": "COMPLET",
      "panel_display_text": "COMPLET",
      "has_active_schedules": false,
      "active_schedules_count": 0,
      "threshold_dense": 10,
      "threshold_full": 3,
      "panels": [
        {
          "id": 4,
          "name": "PANEL PALAU",
          "ip": "172.20.4.50",
          "status": "online",
          "protocol_version": "new",
          "last_message": "COMPLET",
          "last_update": "2026-07-30T10:18:00.000000"
        }
      ],
      "last_update": "2026-07-30T10:20:00.123456"
    }
  ]
}
```

### 3.3 Campos de Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID único del parking |
| `name` | string | Nombre del parking |
| `total_plazas` | int | Capacidad máxima |
| `plazas_ocupadas` | int | Plazas actualmente ocupadas |
| `plazas_libres` | int | Plazas disponibles |
| `estado` | string | Estado en español: `LIBRE`, `DENSO`, `COMPLETO` |
| `estado_valenciano` | string | Estado en valenciano: `LLIURE`, `DENS`, `COMPLET` |
| `panel_display_text` | string | Texto actualmente mostrado en paneles |
| `has_active_schedules` | bool | Si hay programaciones activas |
| `threshold_dense` | int | Umbral para estado DENSO |
| `threshold_full` | int | Umbral para estado COMPLETO |

---

## 4. Actualizar Ocupación de un Parking

**Endpoint**: `POST /api/parkings/{parking_id}/occupancy`

**Descripción**: Establece manualmente la ocupación actual de un parking específico.

### 4.1 Comando

```bash
# Obtener token (si no lo tienes)
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | jq -r '.token')

# Actualizar ocupación del parking ID=5 a 25 plazas ocupadas
curl -s -X POST http://localhost:6001/api/parkings/5/occupancy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 25}' | jq
```

### 4.2 Parámetros de Entrada

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `occupancy` | int | Sí | Número de plazas ocupadas (>= 0) |

### 4.3 Respuesta Exitosa

```json
{
  "status": "ok",
  "parking": "P. Poble antic/Palau Altea",
  "occupancy": 25,
  "free_spaces": 25,
  "parking_status": "LIBRE",
  "previous_occupancy": 48,
  "change_amount": -23,
  "adjustment_type": "manual"
}
```

### 4.4 Respuesta con Límite Aplicado

Si el valor solicitado excede los límites (0 - 110% de capacidad):

```json
{
  "status": "ok",
  "parking": "P. Ciutat Esportiva",
  "occupancy": 110,
  "free_spaces": -10,
  "parking_status": "COMPLETO",
  "previous_occupancy": 80,
  "change_amount": 30,
  "adjustment_type": "manual_limited_ceiling",
  "warning": "El valor solicitado (150) excedía los límites permitidos (0-110). Se ha ajustado a 110.",
  "requested_occupancy": 150,
  "was_limited": true
}
```

### 4.5 Campos de Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `status` | string | Siempre `"ok"` si exitoso |
| `parking` | string | Nombre del parking actualizado |
| `occupancy` | int | Ocupación final establecida |
| `free_spaces` | int | Plazas libres resultantes |
| `parking_status` | string | Nuevo estado: `LIBRE`, `DENSO`, `COMPLETO` |
| `previous_occupancy` | int | Ocupación anterior |
| `change_amount` | int | Cambio aplicado (positivo = más ocupado) |
| `adjustment_type` | string | Tipo de ajuste realizado |

---

## 5. Códigos de Error

| Código HTTP | Descripción |
|-------------|-------------|
| `400` | Parámetros inválidos o faltantes |
| `401` | Token inválido o expirado |
| `403` | Sin permisos para el recurso |
| `404` | Parking no encontrado |
| `500` | Error interno del servidor |

### Ejemplos de Errores

**Token inválido (401)**:
```json
{
  "error": "Token inválido o expirado"
}
```

**Parking no encontrado (404)**:
```json
{
  "error": "Parking not found"
}
```

**Campo faltante (400)**:
```json
{
  "error": "Missing occupancy field"
}
```

---

## 6. Script Completo de Ejemplo

```bash
#!/bin/bash
# Script de ejemplo para integración con la API de parkings

API_URL="http://localhost:6001/api"
EMAIL="info@swat-id.com"
PASSWORD="admin123!"

# 1. Obtener token
echo "=== Obteniendo token de autenticación ==="
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" | jq -r '.token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "Error: No se pudo obtener el token"
  exit 1
fi
echo "Token obtenido correctamente"

# 2. Obtener estado de todos los parkings
echo ""
echo "=== Estado de todos los parkings ==="
curl -s -X GET "$API_URL/parkings/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.parkings[] | {id, name, plazas_ocupadas, plazas_libres, estado}'

# 3. Actualizar ocupación de un parking específico (ID=5)
echo ""
echo "=== Actualizando ocupación del parking ID=5 a 30 plazas ==="
curl -s -X POST "$API_URL/parkings/5/occupancy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 30}' | jq

echo ""
echo "=== Proceso completado ==="
```

---

## 7. Notas Importantes

1. **Tokens JWT**: Los tokens expiran después de un tiempo. Si recibes error 401, solicita un nuevo token.

2. **Límites de ocupación**: El sistema limita automáticamente los valores entre 0 y 110% de la capacidad máxima.

3. **Actualización de paneles**: Al cambiar la ocupación, los paneles LED se actualizan automáticamente si hay programaciones activas.

4. **Estados calculados automáticamente**:
   - `LIBRE`: plazas_libres > threshold_dense
   - `DENSO`: threshold_full < plazas_libres <= threshold_dense
   - `COMPLETO`: plazas_libres <= threshold_full

5. **Permisos**: El superadmin tiene acceso a todos los parkings. Usuarios normales solo ven los parkings asignados.
