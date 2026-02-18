# Contexto del Sistema Parking Altea

**Versión**: v4.4.0+  
**Última actualización**: 2026-02-18  
**Servidor de producción**: 157.180.91.63

---

## 1. Servicios del Sistema (systemd)

| Servicio | Puerto | Descripción | Estado |
|----------|--------|-------------|--------|
| `parking-api.service` | 6001 | API REST principal (Flask) | ✅ Activo |
| `parking-camera.service` | 6400 | Servidor cámaras de conteo (gunicorn) | ✅ Activo |
| `parking-spot-detection.service` | 6401 | Servidor cámaras detección por plaza | ✅ Activo |
| `parking-panel-protocol.service` | 7110 | Protocolo de comunicación con paneles LED | ✅ Activo |
| `parking-panel-worker.service` | - | Worker actualización paneles (cada 2 min) | ✅ Activo |
| `parking-panel-type3-and-4-worker.service` | - | Worker paneles Tipo 3 y 4 | ✅ Activo |
| `parking-alarm-monitor.service` | - | Monitor de alarmas | ✅ Activo |
| `parking-auto-correction.service` | - | Corrección automática de ocupación | ✅ Activo |
| `parking-schedule-monitor.service` | - | Monitor de programaciones | ✅ Activo |
| `parking-sensor-push.service` | - | Servicio push de sensores | ✅ Activo |
| `parking-sync.service` | - | Integración FIWARE Smart Cities | ✅ Activo |
| `parking-eye-control-system.service` | - | Sistema de control Eye | ✅ Activo |

### Comandos útiles

```bash
# Ver estado de todos los servicios de parking
systemctl list-units --type=service | grep -i parking

# Reiniciar un servicio
sudo systemctl restart parking-api.service

# Ver logs de un servicio
sudo journalctl -u parking-api.service -f

# Ver logs con filtro
sudo journalctl -u parking-api.service -n 100 --no-pager | grep "ERROR"
```

---

## 2. URLs y Endpoints

### Servidor de Producción

| Componente | URL/Puerto | Protocolo |
|------------|------------|-----------|
| **Frontend Web** | `http://157.180.91.63:6001` | HTTP |
| **API REST** | `http://157.180.91.63:6001/api/` | HTTP |
| **Cámaras Conteo** | `http://157.180.91.63:6400/camera` | HTTP POST |
| **Cámaras Detección** | `http://157.180.91.63:6401/detection` | HTTP POST |
| **Panel Protocol** | `http://157.180.91.63:7110` | HTTP |

### Endpoints Principales de la API

```
# Autenticación
POST /api/login
POST /api/logout
GET  /api/me

# Parkings
GET  /api/parkings
GET  /api/parkings/{id}
POST /api/parkings/{id}/occupancy
POST /api/parkings/{id}/config
PUT  /api/parkings/{id}/cameras
GET  /api/parkings/{id}/cameras

# Paneles
GET  /api/panels
POST /api/panels/{id}/test
GET  /api/panels/{id}/status

# Usuarios
GET  /api/users
POST /api/users
PUT  /api/users/{id}
```

---

## 3. Base de Datos

### Conexión

```
Host: localhost
Puerto: 5432
Base de datos: parking_altea
Usuario: postgres
URL: postgresql://postgres@localhost:5432/parking_altea
```

### Tablas Principales

| Tabla | Descripción |
|-------|-------------|
| `parkings` | Configuración de parkings |
| `accesses` | Cámaras (conteo y detección) |
| `camera_parkings` | Relación N:M cámaras-parkings |
| `panels` | Paneles LED informativos |
| `panel_types` | Tipos de paneles (1, 2, 3, 4) |
| `users` | Usuarios del sistema |
| `user_parkings` | Permisos usuario-parking |
| `monitored_spots` | Plazas monitorizadas individualmente |
| `occupancy_history` | Histórico de ocupación |
| `camera_logs` | Logs de mensajes de cámaras |
| `scheduled_messages` | Mensajes programados para paneles |

### Campos Importantes en `accesses` (Cámaras)

```sql
camera_type VARCHAR(20)         -- 'counting' o 'spot_detection'
monitored_spots_count INTEGER   -- Solo para spot_detection
status VARCHAR                  -- 'ONLINE' o 'OFFLINE'
last_message_received TIMESTAMP
```

### Campos Importantes en `parkings`

```sql
max_capacity INTEGER            -- Capacidad total
current_occupancy INTEGER       -- Ocupación actual
status VARCHAR                  -- 'LIBRE', 'DENSO', 'COMPLETO'
threshold_dense INTEGER         -- Umbral para estado DENSO
threshold_full INTEGER          -- Umbral para estado COMPLETO
spot_monitoring_enabled BOOLEAN -- Monitorización plaza a plaza activa
total_monitored_spots INTEGER   -- Total plazas monitorizadas
message_type VARCHAR            -- 'ESTADO' o 'PLAZAS_LIBRES'
```

---

## 4. Tipos de Cámaras

### Cámara de Conteo (`counting`)
- **Puerto**: 6400
- **Función**: Cuenta entradas y salidas de vehículos
- **NO tiene**: plazas monitorizadas
- **Formato mensaje**:
```json
{
  "device": "NOMBRE_CAMARA",
  "line": "1",
  "Vehicle In": 150,
  "Vehicle Out": 120
}
```

### Cámara de Detección por Plaza (`spot_detection`)
- **Puerto**: 6401
- **Función**: Monitoriza plazas individuales
- **SÍ tiene**: plazas monitorizadas (ej: 56)
- **Formato mensaje trigger**:
```json
{
  "device": "NOMBRE_CAMARA",
  "report_type": "trigger",
  "parking_area": "ZONA_A",
  "index_number": 15,
  "occupancy": 1
}
```
- **Formato mensaje interval**:
```json
{
  "device": "NOMBRE_CAMARA",
  "report_type": "interval",
  "total_occupied": 45,
  "total_available": 11,
  "parking_detail": [
    {
      "area_name": "ZONA_A",
      "numbering_scheme": [1, 2, 3, 4, 5],
      "occupancy": [1, 0, 1, 1, 0]
    }
  ]
}
```

---

## 5. Estructura del Proyecto

```
/opt/parking_altea/
├── src/                          # Código backend Python
│   ├── api_server.py             # API REST principal
│   ├── camera_server.py          # Servidor cámaras conteo (6400)
│   ├── spot_detection_server.py  # Servidor detección plaza (6401)
│   ├── panel_protocol_service.py # Protocolo paneles LED
│   ├── panel_worker_service.py   # Worker actualización paneles
│   ├── models.py                 # Modelos SQLAlchemy
│   ├── auth.py                   # Autenticación y permisos
│   └── config.py                 # Configuración
├── client/                       # Frontend React
│   ├── src/
│   │   ├── pages/               # Páginas principales
│   │   ├── components/          # Componentes reutilizables
│   │   └── services/            # Servicios API
│   └── dist/                    # Build de producción
├── venv/                        # Entorno virtual Python
└── docs/                        # Documentación
```

---

## 6. Configuración (config.py)

```python
DB_URL = 'postgresql://postgres@localhost:5432/parking_altea'
API_PORT = 6001
CAMERA_PORT = 6400
SPOT_DETECTION_PORT = 6401
PANEL_PROTOCOL_SERVICE_PORT = 7110
LOG_RETENTION_DAYS = 15
OCCUPANCY_MAX_LIMIT_PERCENT = 110  # Límite máximo 110%
OCCUPANCY_MIN_LIMIT = 0            # Límite mínimo 0
```

---

## 7. Relación Cámaras-Parkings (Muchos a Muchos)

Una cámara puede pertenecer a **múltiples parkings** (subzonas + parking global).

```
Tabla: camera_parkings
- camera_id (FK -> accesses.id)
- parking_id (FK -> parkings.id)
```

**Ejemplo**: Una cámara de detección puede estar asignada a:
- Parking "Zona A" (subzona)
- Parking "Basseta Global" (parking completo)

Cuando llega un mensaje, se procesa para **TODOS** los parkings asociados.

---

## 8. Roles y Permisos

| Rol | Descripción |
|-----|-------------|
| `superadmin` | Acceso total a todos los parkings y funciones |
| `admin` | Administrador de parkings asignados |
| `user` | Usuario con acceso limitado a parkings asignados |

### Tablas de Permisos
- `user_parkings`: Asignación usuario-parking
- `user_panels`: Asignación usuario-panel (directa)
- `user_accesses`: Asignación usuario-cámara

---

## 9. Comandos de Despliegue

### Actualizar desde Git

```bash
cd /opt/parking_altea
git fetch origin
git reset --hard origin/v4.4.0
```

### Reconstruir Frontend

```bash
cd /opt/parking_altea/client
chmod +x node_modules/.bin/*
npx vite build
```

### Reiniciar Servicios

```bash
# Backend API
sudo systemctl restart parking-api.service

# Servidor cámaras conteo
sudo systemctl restart parking-camera.service

# Servidor detección por plaza
sudo systemctl restart parking-spot-detection.service

# Workers de paneles
sudo systemctl restart parking-panel-worker.service
sudo systemctl restart parking-panel-type3-and-4-worker.service
```

### Ver Logs

```bash
# API principal
sudo journalctl -u parking-api.service -f

# Cámaras de conteo
sudo journalctl -u parking-camera.service -f

# Detección por plaza
sudo journalctl -u parking-spot-detection.service -f

# Todos los logs de parking
sudo journalctl | grep -i parking
```

---

## 10. Archivos de Servicio (systemd)

Ubicación: `/etc/systemd/system/`

```bash
# Listar archivos de servicio de parking
ls -la /etc/systemd/system/parking*.service

# Ver contenido de un servicio
cat /etc/systemd/system/parking-api.service
```

---

## 11. Puertos en Uso

```bash
# Ver todos los puertos de parking
ss -tlnp | grep -E "6001|6400|6401|7110"

# Resultado típico:
# 6001 - API REST
# 6400 - Cámaras Conteo
# 6401 - Cámaras Detección
# 7110 - Panel Protocol
```

---

## 12. Troubleshooting

### El servicio no arranca
```bash
sudo journalctl -u NOMBRE_SERVICIO -n 50 --no-pager
```

### Error de permisos en vite
```bash
cd /opt/parking_altea/client
chmod +x node_modules/.bin/*
npx vite build
```

### Verificar conexión a base de datos
```bash
psql -U postgres -d parking_altea -c "SELECT 1"
```

### Verificar que los servidores responden
```bash
curl http://localhost:6001/api/health
curl http://localhost:6400/camera
curl http://localhost:6401/detection/health
```

---

## 13. Contacto y Repositorio

- **Repositorio**: https://github.com/Swat-id/parking_altea
- **Branch producción**: v4.4.0
