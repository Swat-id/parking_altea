# Integración del Panel Protocol Service con el Backend

## Resumen

El Panel Protocol Service se ejecuta en el **puerto 7000** como servicio HTTP/REST independiente. El backend puede comunicarse con él de dos formas:

1. **Cliente HTTP** (recomendado) - Usando `PanelProtocolClient`
2. **Peticiones HTTP directas** - Usando `requests` o `curl`

## Arquitectura

```
┌─────────────────┐         HTTP REST          ┌──────────────────────┐
│   Backend       │ ──────────────────────────▶ │  Panel Protocol      │
│   (Puerto 6001) │                             │  Service (Puerto 7000)│
│                 │                             │                      │
│  API Server     │                             │  PanelProtocol       │
│  (api_server.py)│                             │  Service             │
└─────────────────┘                             └──────────────────────┘
                                                          │
                                                          │ TCP/IP
                                                          ▼
                                                 ┌──────────────────────┐
                                                 │   Paneles LED        │
                                                 │   (Puerto 5200)      │
                                                 └──────────────────────┘
```

## Uso desde el Backend

### Opción 1: Cliente HTTP (Recomendado)

El cliente `PanelProtocolClient` simplifica la comunicación con el servicio:

```python
from src.panel_protocol.client import get_panel_protocol_client

# Obtener instancia del cliente
client = get_panel_protocol_client()

# Enviar texto a un panel
task_id = client.send_text(
    panel_ip="192.168.1.221",
    window_id=0,
    text="PARKING LLIURE",
    color=2,  # Verde
    font_size=2,  # 16px
    effect=11,  # Scroll izquierda
    wait_for_response=False  # No bloquea
)

# Si necesitas el resultado, puedes consultarlo después
result = client.get_task_result(task_id)
```

### Opción 2: Peticiones HTTP Directas

```python
import requests

# Enviar texto
response = requests.post(
    'http://localhost:7000/api/v1/panels/send-text',
    json={
        'panel_ip': '192.168.1.221',
        'window_id': 0,
        'text': 'PARKING LLIURE',
        'color': 2,
        'font_size': 2,
        'effect': 11
    },
    headers={'Content-Type': 'application/json'}
)

task_id = response.json()['task_id']
```

## Ejemplo de Integración en api_server.py

### Reemplazar PanelCommunicationService

**Antes (usando servicio Java en puerto 8888):**
```python
from panel_communication_service import get_panel_service

panel_service = get_panel_service()
result = panel_service.send_custom_text(
    panel_ip=panel_ip,
    text=message,
    color=color,
    font_size=font_size_code,
    effect=effect_code
)
```

**Después (usando nuevo servicio en puerto 7000):**
```python
from src.panel_protocol.client import get_panel_protocol_client

client = get_panel_protocol_client()
task_id = client.send_text(
    panel_ip=panel_ip,
    window_id=window_id,
    text=message,
    color=color,
    font_size=font_size_code,
    effect=effect_code,
    wait_for_response=False  # No bloquea, retorna task_id
)

# Opcional: Verificar resultado
result = client.get_task_result(task_id)
if result['success']:
    # Operación exitosa
    pass
```

## Endpoints Disponibles

### POST `/api/v1/panels/send-text`
Envía texto a un panel.

**Request:**
```json
{
  "panel_ip": "192.168.1.221",
  "panel_port": 5200,
  "window_id": 0,
  "text": "PARKING LLIURE",
  "color": 2,
  "font_size": 2,
  "effect": 11,
  "alignment": 5,
  "speed": 0,
  "stay_time": 3,
  "wait_for_response": false
}
```

**Response:**
```json
{
  "success": true,
  "task_id": "uuid-de-la-tarea",
  "message": "Texto enviado"
}
```

### POST `/api/v1/panels/create-window`
Crea ventanas en un panel.

**Request:**
```json
{
  "panel_ip": "192.168.1.221",
  "panel_port": 5200,
  "windows": [
    {"x": 0, "y": 0, "width": 64, "height": 8}
  ],
  "wait_for_response": false
}
```

### GET `/api/v1/tasks/<task_id>`
Obtiene el resultado de una tarea.

**Response:**
```json
{
  "success": true,
  "task_id": "uuid-de-la-tarea",
  "result": {
    "success": true,
    "return_value": 0,
    "response_data": "..."
  }
}
```

### GET `/health`
Verifica el estado del servicio.

**Response:**
```json
{
  "status": "ok",
  "service": "panel-protocol-service",
  "version": "4.3.0",
  "port": 7000
}
```

## Autenticación

El servicio usa **el mismo sistema de autenticación JWT** que el backend principal.

### Login

**POST** `/api/v1/auth/login`

```bash
curl -X POST http://localhost:7000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "info@swat-id.com",
    "password": "admin123!"
  }'
```

### Uso con Token

```python
from src.panel_protocol.client import PanelProtocolClient

# Login (obtiene token automáticamente)
client = PanelProtocolClient()
result = client.login(email="info@swat-id.com", password="admin123!")

# El token se guarda automáticamente
task_id = client.send_text(...)
```

**O con curl:**
```bash
# Primero obtener token
TOKEN=$(curl -X POST http://localhost:7000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' \
  | jq -r '.token')

# Usar token en peticiones
curl -X POST http://localhost:7000/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"panel_ip": "192.168.1.221", "text": "TEST"}'
```

**Nota**: Si no se envía token, el servicio usa superadmin por defecto (igual que el backend).

## Ventajas del Nuevo Servicio

### 1. **No Bloqueante**
- Las operaciones retornan inmediatamente con un `task_id`
- No bloquea el backend mientras se comunica con los paneles

### 2. **Paralelo**
- Múltiples paneles pueden recibir mensajes simultáneamente
- Pool de conexiones reutilizables

### 3. **Trazable**
- Todos los resultados se almacenan
- Estadísticas y métricas disponibles

### 4. **Escalable**
- Configurable para diferentes cargas
- Control de concurrencia

## Migración desde PanelCommunicationService

### Paso 1: Iniciar el nuevo servicio

```bash
# En producción, como servicio systemd
sudo systemctl start parking-panel-protocol

# O manualmente
python src/panel_protocol/api_server.py
```

### Paso 2: Actualizar código del backend

Reemplazar llamadas a `PanelCommunicationService` por `PanelProtocolClient`:

```python
# Antes
from panel_communication_service import get_panel_service
panel_service = get_panel_service()
result = panel_service.send_custom_text(...)

# Después
from src.panel_protocol.client import get_panel_protocol_client
client = get_panel_protocol_client()
task_id = client.send_text(...)
result = client.get_task_result(task_id)
```

### Paso 3: Verificar funcionamiento

```bash
# Verificar que el servicio está corriendo
curl http://localhost:7000/health

# Probar envío de texto
curl -X POST http://localhost:7000/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -d '{
    "panel_ip": "192.168.1.221",
    "window_id": 0,
    "text": "TEST",
    "color": 2,
    "font_size": 2
  }'
```

## Pruebas desde el Exterior

Si el servicio está configurado para aceptar conexiones externas:

```bash
# 1. Login desde otra máquina
TOKEN=$(curl -X POST http://157.180.91.63:7000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "info@swat-id.com",
    "password": "admin123!"
  }' | jq -r '.token')

# 2. Usar token para enviar mensaje
curl -X POST http://157.180.91.63:7000/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "panel_ip": "192.168.1.221",
    "window_id": 0,
    "text": "TEST EXTERNO",
    "color": 2,
    "font_size": 2
  }'
```

**Nota**: Asegurarse de que:
1. El firewall permita conexiones al puerto 7000
2. Se use un usuario válido de la base de datos
3. El token JWT sea válido (expira en 24 horas)

## Configuración del Servicio

### Variables de Entorno

```bash
# Puerto del servicio
PANEL_PROTOCOL_SERVICE_PORT=7000

# Configuración del servicio interno (opcional)
PANEL_PROTOCOL_MAX_CONCURRENT_TASKS=10
PANEL_PROTOCOL_MAX_CONNECTIONS_PER_PANEL=5
```

### Archivo .env

```env
PANEL_PROTOCOL_SERVICE_PORT=7000
```

**Nota**: La autenticación usa el mismo sistema JWT del backend, no requiere configuración adicional.

---

**Fecha**: 2025-10-02  
**Versión**: 4.3.0  
**Puerto**: 7000 (FIJO)

