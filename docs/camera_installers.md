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
```

### Formato de Datos JSON

El servidor espera recibir datos en el siguiente formato:

```json
{
    "line": 1,
    "Vehicle In": 5,
    "Vehicle Out": 2
}
```

### Campos Requeridos

- **line**: Número de línea de la cámara (entero)
- **Vehicle In**: Contador total de vehículos que han entrado (entero)
- **Vehicle Out**: Contador total de vehículos que han salido (entero)

### Ejemplo de Petición

```bash
curl -X POST http://157.180.91.63:6400/camera \
  -H 'Content-Type: application/json' \
  -d '{
    "line": 1,
    "Vehicle In": 150,
    "Vehicle Out": 120
  }'
```

## Respuestas del Servidor

### Respuesta Exitosa
```json
{
    "status": "ok"
}
```

### Error - Acceso no encontrado
```json
{
    "error": "Access not found"
}
```

## Configuración de Cámaras

### Requisitos Previos

1. **Registro en Base de Datos**: La cámara debe estar previamente registrada en la base de datos del sistema
2. **IP de la Cámara**: La IP desde donde se envían los datos debe coincidir con la registrada
3. **Número de Línea**: El campo `line` debe coincidir con el configurado en la base de datos

### Frecuencia de Envío

- **Recomendado**: Enviar datos cada 30-60 segundos
- **Mínimo**: No enviar más de una petición por segundo
- **Máximo**: No enviar menos de una petición cada 5 minutos

### Manejo de Errores

1. **Timeout**: Configurar timeout de 10 segundos para las peticiones
2. **Reintentos**: Implementar reintentos automáticos en caso de fallo
3. **Logs**: Mantener logs de las peticiones enviadas y respuestas recibidas

## Ejemplos de Implementación

### Python
```python
import requests
import json
import time

def send_camera_data(line, vehicle_in, vehicle_out):
    url = "http://157.180.91.63:6400/camera"
    headers = {"Content-Type": "application/json"}
    data = {
        "line": line,
        "Vehicle In": vehicle_in,
        "Vehicle Out": vehicle_out
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print("Datos enviados correctamente")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error de conexión: {e}")

# Ejemplo de uso
send_camera_data(1, 150, 120)
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function sendCameraData(line, vehicleIn, vehicleOut) {
    const url = 'http://157.180.91.63:6400/camera';
    const data = {
        line: line,
        'Vehicle In': vehicleIn,
        'Vehicle Out': vehicleOut
    };
    
    try {
        const response = await axios.post(url, data, {
            headers: { 'Content-Type': 'application/json' },
            timeout: 10000
        });
        console.log('Datos enviados correctamente');
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

// Ejemplo de uso
sendCameraData(1, 150, 120);
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
# Enviar datos de prueba
curl -X POST http://157.180.91.63:6400/camera \
  -H 'Content-Type: application/json' \
  -d '{"line": 1, "Vehicle In": 0, "Vehicle Out": 0}'
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