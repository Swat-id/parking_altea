# Documentación para Instaladores de Cámaras - Parking Altea

## Información del Servidor

- **IP del servidor**: 157.180.91.63
- **Puerto**: 6400
- **Endpoint**: `/camera`
- **URL completa**: `http://157.180.91.63:6400/camera`

## Protocolo de Comunicación

### Método HTTP
- **POST**

### Headers Requeridos
```
Content-Type: application/json
X-Forwarded-For: [IP_DE_LA_CAMARA] (opcional, se usa para identificación)
```

### Formato de Datos JSON

El servidor acepta el formato completo de las cámaras:

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

### Campos Requeridos

- **line**: Número de línea de la cámara (entero)
- **Vehicle In**: Contador total de vehículos que han entrado (entero)
- **Vehicle Out**: Contador total de vehículos que han salido (entero)

### Campos Opcionales

- **device**: Nombre de la cámara (se usa como respaldo para identificación)
- **event**: Tipo de evento (ej: "Object Counting")
- **time**: Timestamp del evento
- **time_msec**: Timestamp con milisegundos
- **Vehicle Capacity**: Capacidad del vehículo
- **Vehicle Sum**: Suma total de vehículos
- **resolution_w/h**: Resolución de la cámara
- **coordinate_x1/y1/x2/y2**: Coordenadas de detección

### Ejemplo de Petición

```bash
curl -X POST http://157.180.91.63:6400/camera \
  -H 'Content-Type: application/json' \
  -H 'X-Forwarded-For: 212.63.121.4' \
  -d '{
    "event": "Object Counting",
    "device": "ciutat_esportiva camera 1",
    "time": "2025-04-22 18:38:09",
    "line": 0,
    "Vehicle In": 163,
    "Vehicle Out": 312
  }'
```

## Respuestas del Servidor

### Respuesta Exitosa
```json
{
    "status": "ok",
    "parking": "1 - P. Ciutat Esportiva",
    "occupancy": 45
}
```

### Error - Acceso no encontrado
```json
{
    "error": "Access not found"
}
```

### Error - JSON inválido
```json
{
    "error": "Invalid JSON format"
}
```

### Error - Campos faltantes
```json
{
    "error": "Missing required fields: line, Vehicle In, Vehicle Out"
}
```

## Configuración de Cámaras

### Requisitos Previos

1. **Registro en Base de Datos**: La cámara debe estar previamente registrada en la base de datos del sistema
2. **Identificación**: El sistema identifica las cámaras por:
   - IP de origen + número de línea
   - Nombre del dispositivo (campo `device`)
3. **Número de Línea**: El campo `line` debe coincidir con el configurado en la base de datos

### Frecuencia de Envío

- **Recomendado**: Enviar datos cada 30-60 segundos
- **Mínimo**: No enviar más de una petición por segundo
- **Máximo**: No enviar menos de una petición cada 5 minutos

### Manejo de Errores

1. **Timeout**: Configurar timeout de 10 segundos para las peticiones
2. **Reintentos**: Implementar reintentos automáticos en caso de fallo
3. **Logs**: Mantener logs de las peticiones enviadas y respuestas recibidas
4. **Robustez**: El servidor maneja JSON mal formados y errores sin interrumpir el servicio

## Ejemplos de Implementación

### Python
```python
import requests
import json
import time

def send_camera_data(device, line, vehicle_in, vehicle_out, ip=None):
    url = "http://157.180.91.63:6400/camera"
    headers = {"Content-Type": "application/json"}
    
    if ip:
        headers["X-Forwarded-For"] = ip
    
    data = {
        "event": "Object Counting",
        "device": device,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "line": line,
        "Vehicle In": vehicle_in,
        "Vehicle Out": vehicle_out
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"Datos enviados correctamente - Parking: {result.get('parking')}, Ocupación: {result.get('occupancy')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error de conexión: {e}")

# Ejemplo de uso
send_camera_data("ciutat_esportiva camera 1", 0, 163, 312, "212.63.121.4")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function sendCameraData(device, line, vehicleIn, vehicleOut, ip = null) {
    const url = 'http://157.180.91.63:6400/camera';
    const headers = { 'Content-Type': 'application/json' };
    
    if (ip) {
        headers['X-Forwarded-For'] = ip;
    }
    
    const data = {
        event: 'Object Counting',
        device: device,
        time: new Date().toISOString().replace('T', ' ').substring(0, 19),
        line: line,
        'Vehicle In': vehicleIn,
        'Vehicle Out': vehicleOut
    };
    
    try {
        const response = await axios.post(url, data, {
            headers: headers,
            timeout: 10000
        });
        console.log(`Datos enviados correctamente - Parking: ${response.data.parking}, Ocupación: ${response.data.occupancy}`);
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

// Ejemplo de uso
sendCameraData('ciutat_esportiva camera 1', 0, 163, 312, '212.63.121.4');
```

## Verificación de Instalación

### Test de Conectividad
```bash
# Verificar que el puerto está abierto
telnet 157.180.91.63 6400

# O usando curl
curl -v http://157.180.91.63:6400/camera
```

### Test de Funcionamiento
```bash
# Enviar datos de prueba con formato completo
curl -X POST http://157.180.91.63:6400/camera \
  -H 'Content-Type: application/json' \
  -H 'X-Forwarded-For: 212.63.121.4' \
  -d '{
    "event": "Object Counting",
    "device": "ciutat_esportiva camera 1",
    "time": "2025-04-22 18:38:09",
    "line": 0,
    "Vehicle In": 0,
    "Vehicle Out": 0
  }'
```

### Test de Robustez
```bash
# Test con JSON mal formado (debe ser manejado sin errores)
curl -X POST http://157.180.91.63:6400/camera \
  -H 'Content-Type: application/json' \
  -d '{"line": 0, "Vehicle In": 0, "Vehicle Out": 0,}'
```

## Contacto y Soporte

Para problemas técnicos o consultas sobre la integración:

- **Email**: info@swat-id.com
- **Documentación**: Consultar `/docs` en el repositorio del proyecto
- **Logs del Servidor**: Verificar logs del servicio `parking-camera` en el servidor

## Notas Importantes

1. **Seguridad**: El servidor está configurado para aceptar conexiones desde cualquier IP
2. **Rendimiento**: El sistema está optimizado para manejar múltiples cámaras simultáneamente
3. **Backup**: Los datos se almacenan en PostgreSQL con respaldos automáticos
4. **Monitoreo**: El sistema registra todas las peticiones recibidas para auditoría
5. **Robustez**: El servidor maneja errores de forma robusta sin interrumpir el servicio
6. **Identificación**: Las cámaras se identifican por IP+línea o por nombre de dispositivo 