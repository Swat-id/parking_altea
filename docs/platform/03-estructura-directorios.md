# Estructura de Directorios y Ficheros Clave

## 1. Directorio Principal

```
/opt/parking_altea/
├── client/                      # Frontend React
├── docs/                        # Documentación
├── scripts/                     # Scripts de utilidad
├── src/                         # Código fuente backend
├── tests/                       # Tests unitarios
├── venv/                        # Entorno virtual Python
├── .env                         # Variables de entorno
├── requirements.txt             # Dependencias Python
└── README.md                    # Documentación principal
```

## 2. Directorio /src (Backend)

```
src/
├── __init__.py
├── api_server.py                # API REST Flask principal
├── config.py                    # Configuración de la aplicación
├── models.py                    # Modelos SQLAlchemy
│
├── # === SERVICIOS DE PANELES ===
├── panel_communication_service.py   # Servicio central de comunicación
├── panel_schedule_service.py        # Gestión de programaciones
├── panel_worker_service.py          # Worker paneles Tipo 1 y 2
├── panel_type3_and_4_worker_service.py  # Worker paneles Tipo 3 y 4
├── panel_type4_update_service.py    # Servicio actualización Tipo 3/4
├── panel_update_methods.py          # Métodos de actualización
│
├── # === MÓDULO PROTOCOLO NUEVO ===
├── panel_protocol/
│   ├── __init__.py
│   ├── api_server.py           # API del protocolo nuevo (7110)
│   ├── packet_builder.py       # Construcción paquetes hexadecimal
│   ├── panel_protocol_service.py   # Lógica de protocolo
│   ├── connection_pool.py      # Pool de conexiones TCP
│   └── task_queue.py           # Cola de tareas asíncronas
│
├── # === CÁMARAS Y CONTEO ===
├── camera_server.py            # Servidor de eventos cámaras
├── camera_service.py           # Servicio de cámaras
│
├── # === PROGRAMACIONES ===
├── schedule_monitor_service.py # Monitor de programaciones
│
├── # === AUTENTICACIÓN ===
├── auth.py                     # Autenticación JWT
│
├── # === RUTAS API ===
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py          # /api/auth/*
│   ├── panel_routes.py         # /api/panels/*
│   ├── parking_routes.py       # /api/parkings/*
│   ├── schedule_routes.py      # /api/schedules/*
│   └── user_routes.py          # /api/users/*
│
└── # === UTILIDADES ===
    ├── utils/
    │   ├── __init__.py
    │   ├── db.py               # Conexión a base de datos
    │   └── helpers.py          # Funciones auxiliares
    └── migrations/             # Migraciones de BD
```

## 3. Directorio /client (Frontend)

```
client/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/             # Componentes React
│   │   ├── Dashboard/
│   │   ├── Panels/
│   │   ├── Parkings/
│   │   ├── Schedules/
│   │   └── Users/
│   ├── services/               # Servicios API
│   ├── hooks/                  # Custom hooks
│   ├── contexts/               # Contextos React
│   ├── utils/                  # Utilidades
│   ├── App.jsx
│   └── main.jsx
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 4. Directorio PanelSender (SDK Java)

```
/opt/panelSender/
├── main.py                     # API FastAPI (puerto 8888)
├── sender_oldProtocol/
│   ├── __init__.py
│   ├── panel_controller.py    # Controlador protocolo antiguo
│   └── sdk/
│       └── protocol.jar       # SDK Java
├── sender_newProtocol/
│   ├── __init__.py
│   └── panel_controller.py    # Controlador protocolo nuevo (wrapper)
├── requirements.txt
└── venv/
```

## 5. Ficheros Clave

### 5.1 Configuración

| Fichero | Descripción |
|---------|-------------|
| `/opt/parking_altea/.env` | Variables de entorno (DB, claves, puertos) |
| `/opt/parking_altea/src/config.py` | Configuración de la aplicación |
| `/etc/systemd/system/*.service` | Definición de servicios systemd |
| `/etc/nginx/sites-available/parking_altea` | Configuración Nginx |

### 5.2 Backend Principal

| Fichero | Descripción |
|---------|-------------|
| `src/api_server.py` | Punto de entrada API REST |
| `src/models.py` | Modelos de base de datos SQLAlchemy |
| `src/panel_communication_service.py` | **Clave**: Routing de paneles nuevo/antiguo |
| `src/panel_schedule_service.py` | Gestión y ejecución de programaciones |
| `src/panel_worker_service.py` | Worker actualización Tipo 1/2 |
| `src/panel_type4_update_service.py` | Actualización Tipo 3/4 |

### 5.3 Protocolo Nuevo (7110)

| Fichero | Descripción |
|---------|-------------|
| `src/panel_protocol/api_server.py` | API HTTP protocolo nuevo |
| `src/panel_protocol/packet_builder.py` | **Clave**: Generación paquetes hexadecimal |
| `src/panel_protocol/panel_protocol_service.py` | Lógica de envío |
| `src/panel_protocol/connection_pool.py` | Pool conexiones TCP |

### 5.4 Protocolo Antiguo (8888)

| Fichero | Descripción |
|---------|-------------|
| `/opt/panelSender/main.py` | API FastAPI |
| `/opt/panelSender/sender_oldProtocol/panel_controller.py` | Wrapper Java SDK |
| `/opt/panelSender/sender_oldProtocol/sdk/protocol.jar` | SDK Java (binario) |

## 6. Ficheros de Log

| Fichero | Contenido |
|---------|-----------|
| `/var/log/panel_worker.log` | Logs del worker de paneles |
| `/var/log/panel_type3_4_worker.log` | Logs del worker Tipo 3/4 |
| `/var/log/nginx/access.log` | Accesos HTTP |
| `/var/log/nginx/error.log` | Errores Nginx |
| `/var/log/syslog` | Logs del sistema |

## 7. Variables de Entorno (.env)

```bash
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/parking_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=parking_db
DB_USER=parking_user
DB_PASSWORD=xxxxx

# JWT
JWT_SECRET_KEY=xxxxx
JWT_ACCESS_TOKEN_EXPIRES=86400

# API
API_HOST=0.0.0.0
API_PORT=6001
DEBUG=false

# Paneles
PANEL_PROTOCOL_NEW_PORT=7110
PANEL_PROTOCOL_OLD_PORT=8888
PANEL_DEFAULT_TIMEOUT=10

# Logs
LOG_LEVEL=INFO
```

## 8. Permisos y Propietarios

```bash
# Directorio principal
/opt/parking_altea/
  - Propietario: root:root
  - Permisos: 755

# Ficheros Python
*.py
  - Propietario: root:root
  - Permisos: 644

# Scripts ejecutables
*.sh
  - Propietario: root:root
  - Permisos: 755

# Logs
/var/log/*.log
  - Propietario: root:root
  - Permisos: 644
```

## 9. Comandos Útiles

### Navegación rápida
```bash
# Ir al proyecto
cd /opt/parking_altea

# Activar entorno virtual
source venv/bin/activate

# Ver estructura de un directorio
tree -L 2 src/

# Buscar ficheros
find . -name "*.py" -type f | head -20

# Buscar en código
grep -r "protocol_version" src/
```

### Ver contenido de ficheros
```bash
# Ver fichero con números de línea
cat -n src/api_server.py | head -50

# Buscar función específica
grep -n "def send_text" src/panel_communication_service.py
```

---

*Anterior: [02-servicios-y-puertos.md](./02-servicios-y-puertos.md)*
*Siguiente: [04-base-de-datos.md](./04-base-de-datos.md)*
