# Configuración de Puerto - Panel Protocol Service v4.3.0

## Puerto Asignado

### Puerto 7000 (FIJO)

El servicio **Panel Protocol Service** se ejecuta en el **puerto 7000** de forma fija.

- **Puerto**: `7000`
- **Protocolo**: HTTP/REST
- **URL Base**: `http://localhost:7000`
- **Configuración**: Definido en `src/panel_protocol/constants.py`

## Configuración

### Variable de Entorno

El puerto puede configurarse mediante variable de entorno:

```bash
export PANEL_PROTOCOL_SERVICE_PORT=7000
```

O en el archivo `.env`:

```env
PANEL_PROTOCOL_SERVICE_PORT=7000
```

### Código

El puerto está definido en:

1. **`src/panel_protocol/constants.py`**:
   ```python
   PANEL_PROTOCOL_SERVICE_PORT = 7000
   ```

2. **`src/config.py`**:
   ```python
   PANEL_PROTOCOL_SERVICE_PORT = int(os.getenv('PANEL_PROTOCOL_SERVICE_PORT', 7000))
   ```

## Puertos del Sistema

### Resumen de Puertos

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| **7000** | **Panel Protocol Service** | Servicio HTTP/REST para paneles LED (v4.3.0) |
| 5789 | Frontend | Interfaz web (nginx) |
| 6001 | API Backend | API principal del sistema |
| 6400 | Camera Service | Servicio de cámaras |
| 8888 | Panel Service (Java) | Servicio Java antiguo (a reemplazar) |
| 3535 | Sensor Push Service | Servicio de sensores |
| 5200 | Paneles TCP | Puerto TCP para comunicación con paneles (interno) |
| 5432 | PostgreSQL | Base de datos |

## Iniciar el Servicio

### Modo Desarrollo

```bash
cd /opt/parking_altea
python src/panel_protocol/api_server.py
```

### Modo Producción (systemd)

Crear servicio systemd en `/etc/systemd/system/parking-panel-protocol.service`:

```ini
[Unit]
Description=Panel Protocol Service v4.3.0
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea
Environment="PYTHONPATH=/opt/parking_altea"
ExecStart=/opt/parking_altea/venv/bin/python src/panel_protocol/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Iniciar servicio:

```bash
sudo systemctl enable parking-panel-protocol
sudo systemctl start parking-panel-protocol
sudo systemctl status parking-panel-protocol
```

## Verificar Puerto

### Verificar que el puerto está libre

```bash
sudo netstat -tlnp | grep 7000
# o
sudo lsof -i :7000
```

### Verificar que el servicio está escuchando

```bash
curl http://localhost:7000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "panel-protocol-service",
  "version": "4.3.0",
  "port": 7000
}
```

## Endpoints Disponibles

### Health Check
- **GET** `/health` - Verificar estado del servicio

### Paneles
- **POST** `/api/v1/panels/create-window` - Crear ventanas
- **POST** `/api/v1/panels/send-text` - Enviar texto
- **POST** `/api/v1/panels/send-image` - Enviar imagen

### Tareas
- **GET** `/api/v1/tasks/<task_id>` - Obtener resultado de tarea
- **GET** `/api/v1/tasks/<task_id>/status` - Obtener estado de tarea

### Estadísticas
- **GET** `/api/v1/panels/<panel_ip>/results` - Resultados de un panel
- **GET** `/api/v1/panels/<panel_ip>/statistics` - Estadísticas de un panel
- **GET** `/api/v1/statistics` - Estadísticas generales

## Autenticación

El servicio usa **el mismo sistema de autenticación JWT** que el backend principal:

- ✅ **Mismos usuarios y contraseñas** de la base de datos
- ✅ **Mismo sistema JWT** (mismo secret, mismo algoritmo)
- ✅ **Mismos roles** (superadmin, user)
- ✅ **Endpoint de login**: `/api/v1/auth/login`

Ver documentación completa en: [Autenticación](./autenticacion.md)

## Notas Importantes

1. **Puerto fijo**: El puerto 7000 está fijado y no debe cambiarse sin actualizar la documentación
2. **Firewall**: Asegurarse de que el puerto 7000 esté abierto si se necesita acceso externo
3. **Proxy**: Si se usa nginx como proxy, configurar redirección desde el puerto 80/443
4. **Concurrencia**: El servicio maneja múltiples conexiones simultáneamente
5. **Autenticación**: Usa el mismo sistema JWT del backend, no requiere configuración adicional

---

**Fecha**: 2025-10-02  
**Versión**: 4.3.0  
**Puerto**: 7000 (FIJO)

