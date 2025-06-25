# Protocolo de Comunicación con Cámaras

## Información General

El sistema recibe mensajes HTTP POST de las cámaras de conteo de vehículos en el puerto **6400**. Cada cámara envía datos de conteo que se procesan automáticamente para actualizar la ocupación de los aparcamientos.

## Endpoint de Recepción

- **URL**: `http://157.180.91.63:6400/`
- **Método**: POST
- **Content-Type**: `application/json`
- **Puerto**: 6400

## Formato del Mensaje

### Headers HTTP Requeridos

```
POST / HTTP/1.0
Host: 157.180.91.63:6400
X-Forwarded-For: [IP_REAL_CAMARA]
X-Forwarded-Host: 157.180.91.63:6400
X-Forwarded-Port: 6400
Connection: close
Content-Type: application/json
```

### Cuerpo JSON del Mensaje

```json
{
  "event": "Object Counting",
  "device": "ciutat_esportiva camera 1",
  "time": "2025-04-22 18:38:09",
  "time_msec": "2025-04-22 18:38:09.910",
  "line": 0,
  "Vehicle In": 163,
  "Vehicle Out": 312,
  "Vehicle Capacity": 0,
  "Vehicle Sum": 475,
  "resolution_w": 1920,
  "resolution_h": 1080,
  "coordinate_x1": 1230,
  "coordinate_y1": 436,
  "coordinate_x2": 1302,
  "coordinate_y2": 571
}
```

## Campos del Mensaje

### Campos Requeridos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `line` | integer | Número de línea de la cámara (identifica el acceso) |
| `Vehicle In` | integer | Contador total de vehículos que han entrado |
| `Vehicle Out` | integer | Contador total de vehículos que han salido |

### Campos Opcionales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `event` | string | Tipo de evento (ej: "Object Counting") |
| `device` | string | Nombre identificativo de la cámara |
| `time` | string | Timestamp del evento |
| `time_msec` | string | Timestamp con milisegundos |
| `Vehicle Capacity` | integer | Capacidad actual (no usado) |
| `Vehicle Sum` | integer | Suma total de vehículos |
| `resolution_w` | integer | Resolución horizontal de la cámara |
| `resolution_h` | integer | Resolución vertical de la cámara |
| `coordinate_x1` | integer | Coordenada X1 del área de detección |
| `coordinate_y1` | integer | Coordenada Y1 del área de detección |
| `coordinate_x2` | integer | Coordenada X2 del área de detección |
| `coordinate_y2` | integer | Coordenada Y2 del área de detección |

## Identificación de la Cámara

El sistema identifica la cámara mediante:

1. **IP de origen**: Extraída del header `X-Forwarded-For` o `remote_addr`
2. **Línea**: Campo `line` del mensaje JSON

La combinación de IP + línea debe coincidir con un registro en la tabla `accesses` de la base de datos.

## Procesamiento del Mensaje

### 1. Validación
- Verificar que la cámara existe en la base de datos
- Validar formato JSON del mensaje
- Comprobar campos requeridos

### 2. Cálculo de Deltas
```python
delta_in = vehicle_in - last_vehicle_in
delta_out = vehicle_out - last_vehicle_out
```

### 3. Actualización de Ocupación
```python
new_occupancy = current_occupancy + (delta_in - delta_out)
new_occupancy = max(0, min(new_occupancy, max_capacity))
```

### 4. Actualización de Estado
- **LIBRE**: occupancy < threshold_dense
- **DENSO**: threshold_dense ≤ occupancy < threshold_full
- **OCUPADO**: occupancy ≥ threshold_full

### 5. Envío a Paneles
Si no hay mensaje fijo activo, se envía el estado actualizado a todos los paneles del aparcamiento.

## Respuesta del Servidor

### Respuesta Exitosa (200)
```json
{
  "status": "ok"
}
```

### Respuesta de Error (404)
```json
{
  "error": "Access not found"
}
```

## Ejemplo de Mensaje Completo

```bash
curl -X POST http://157.180.91.63:6400/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 172.20.17.146" \
  -d '{
    "event": "Object Counting",
    "device": "ciutat_esportiva camera 1",
    "time": "2025-04-22 18:38:09",
    "time_msec": "2025-04-22 18:38:09.910",
    "line": 1,
    "Vehicle In": 163,
    "Vehicle Out": 312,
    "Vehicle Capacity": 0,
    "Vehicle Sum": 475,
    "resolution_w": 1920,
    "resolution_h": 1080,
    "coordinate_x1": 1230,
    "coordinate_y1": 436,
    "coordinate_x2": 1302,
    "coordinate_y2": 571
  }'
```

## Configuración de Cámaras

### Cámaras Registradas

| Parking | IP | Línea | Nombre |
|---------|----|-------|--------|
| 1 - P. Ciutat Esportiva | 172.20.17.146 | 1 | ciutat_esportiva camera 1 |
| 2 - P. Basseta Centre | 172.20.5.144 | 1 | Basseta_Asup camera 1 |
| 2 - P. Basseta Centre | 172.20.5.133 | 1 | Basseta_Rastro camera 2 |
| 6 - P. Poble antic/Conservatori | 172.20.3.182 | 1 | Piteres_2 camera 2 |
| 6 - P. Poble antic/Conservatori | 172.20.3.185 | 1 | Piteres_1 camera 1 |
| 8 - P. Estació Altea | 172.20.2.181 | 1 | RENFE1 camera 1 |
| 5 - P. Poble antic/Palau Altea | 172.20.4.139 | 1 | cocoliso2 camera 2 |
| 5 - P. Poble antic/Palau Altea | 172.20.4.140 | 1 | Cocoliso1 camera 1 |
| 5 - P. Poble antic/Palau Altea | 172.20.4.157 | 1 | Cocoliso3 camera 3 |
| 4 - P. Poble antic/Belles Arts 2 | 172.20.4.148 | 1 | INSTITUT camera 1 |
| 3 - P. Poble antic/Belles Arts 1 | 172.20.4.138 | 1 | palau1 camera 1 |
| 9 - P. Altea la Vella | 172.20.1.154 | 1 | Vella_AI camera 2 |
| 9 - P. Altea la Vella | 172.20.1.162 | 1 | VELLA1 camera 1 |

## Consideraciones Técnicas

### Frecuencia de Envío
- **Recomendado**: Cada 30-60 segundos
- **Mínimo**: Cada 5 minutos
- **Máximo**: Cada 10 segundos

### Manejo de Errores
- Si la cámara no está registrada, se devuelve error 404
- Los contadores se actualizan solo si son mayores que los anteriores
- En el primer arranque (contadores = 0), no se actualiza la ocupación

### Logs y Monitoreo
- Todos los mensajes se registran en logs del sistema
- Se mantiene histórico de ocupación por 15 días
- Los cambios se registran con fuente "camera"

### Seguridad
- No hay autenticación implementada
- Se recomienda configurar firewall para limitar acceso
- Solo se aceptan conexiones desde IPs de cámaras conocidas

## Troubleshooting

### Problema: "Access not found"
**Causa**: La combinación IP + línea no existe en la base de datos
**Solución**: Verificar configuración de la cámara en `accesses.csv`

### Problema: Contadores no se actualizan
**Causa**: Los nuevos contadores son menores que los anteriores
**Solución**: Verificar funcionamiento de la cámara y resetear contadores si es necesario

### Problema: Ocupación no cambia
**Causa**: Deltas calculados son 0
**Solución**: Verificar que los contadores estén incrementando correctamente 