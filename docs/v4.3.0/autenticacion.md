# Sistema de Autenticación - Panel Protocol Service

## Integración con el Sistema de Autenticación del Backend

El Panel Protocol Service utiliza **exactamente el mismo sistema de autenticación** que el resto de la plataforma:

- ✅ **Mismos usuarios y contraseñas** de la base de datos
- ✅ **Mismo sistema JWT** (mismo secret, mismo algoritmo)
- ✅ **Mismos roles** (superadmin, user)
- ✅ **Mismos decoradores** de autenticación

## Autenticación JWT

### Configuración

El servicio usa las mismas constantes de autenticación que el backend:

```python
JWT_SECRET = "parking_altea_secret_key_2025"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
```

### Endpoint de Login

**POST** `/api/v1/auth/login`

Autentica un usuario usando email y contraseña de la base de datos.

**Request:**
```json
{
  "email": "usuario@example.com",
  "password": "contraseña"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "Usuario",
    "email": "usuario@example.com",
    "role": "superadmin",
    "is_active": true
  }
}
```

### Uso del Token

Una vez obtenido el token, debe enviarse en el header `Authorization`:

```
Authorization: Bearer <token>
```

## Ejemplos de Uso

### 1. Login y Obtención de Token

```bash
# Login
curl -X POST http://localhost:7000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "info@swat-id.com",
    "password": "admin123!"
  }'

# Respuesta incluye el token
# Guardar el token para usar en peticiones posteriores
```

### 2. Usar Token en Peticiones

```bash
# Enviar texto usando el token
curl -X POST http://localhost:7000/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "panel_ip": "192.168.1.221",
    "window_id": 0,
    "text": "PARKING LLIURE",
    "color": 2,
    "font_size": 2
  }'
```

### 3. Usar Cliente Python

```python
from src.panel_protocol.client import PanelProtocolClient

# Crear cliente
client = PanelProtocolClient()

# Login (obtiene token automáticamente)
result = client.login(
    email="info@swat-id.com",
    password="admin123!"
)

token = result['token']
print(f"Token obtenido: {token}")

# El token se guarda automáticamente en el cliente
# Ahora todas las peticiones usarán este token

# Enviar texto
task_id = client.send_text(
    panel_ip="192.168.1.221",
    window_id=0,
    text="PARKING LLIURE",
    color=2,
    font_size=2
)
```

### 4. Usar Token Existente

Si ya tienes un token del backend principal:

```python
from src.panel_protocol.client import PanelProtocolClient

# Crear cliente con token existente
client = PanelProtocolClient(token="tu-token-jwt")

# Todas las peticiones usarán este token
task_id = client.send_text(...)
```

## Modo Sin Autenticación (Por Defecto)

Si no se envía token, el servicio asigna automáticamente el usuario superadmin por defecto (igual que el backend):

```python
# Sin token - se usa superadmin por defecto
client = PanelProtocolClient()
task_id = client.send_text(...)  # Funciona sin token
```

**Nota**: Este comportamiento es idéntico al backend principal para mantener compatibilidad.

## Verificar Usuario Autenticado

**GET** `/api/v1/auth/me`

Obtiene información del usuario autenticado actual.

**Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:7000/api/v1/auth/me
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "info@swat-id.com",
    "name": "Super Admin",
    "role": "superadmin"
  }
}
```

## Integración con el Backend

El backend puede usar el mismo token que usa para sus propias peticiones:

```python
# En el backend (api_server.py)
from src.panel_protocol.client import get_panel_protocol_client

# Obtener token del usuario actual
token = request.user_data  # Ya está autenticado en el backend

# Crear cliente con el mismo token
client = get_panel_protocol_client(token=token)

# Enviar texto
task_id = client.send_text(
    panel_ip=panel_ip,
    window_id=window_id,
    text=message,
    color=color,
    font_size=font_size
)
```

## Seguridad

### Tokens JWT

- Los tokens expiran después de 24 horas
- Los tokens son firmados con el mismo secret que el backend
- Los tokens contienen información del usuario (id, email, name, role)

### Validación

- El servicio valida el token usando `verify_token()` del módulo `auth.py`
- Si el token es inválido o expirado, retorna error 401
- Si no hay token, usa superadmin por defecto (comportamiento del backend)

## Comparación con Sistema Actual

| Aspecto | Sistema Actual (Puerto 8888) | Nuevo Servicio (Puerto 7000) |
|---------|------------------------------|-------------------------------|
| Autenticación | No tiene | ✅ JWT (mismo que backend) |
| Usuarios | No aplica | ✅ Mismos usuarios BD |
| Roles | No aplica | ✅ superadmin, user |
| Token | No aplica | ✅ Compatible con backend |

---

**Fecha**: 2025-10-02  
**Versión**: 4.3.0  
**Autenticación**: JWT integrado con backend

