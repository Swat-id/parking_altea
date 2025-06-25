# Parking Altea - Sistema de Gestión de Aparcamientos

## Descripción

Sistema de gestión inteligente de aparcamientos para Altea que integra cámaras de conteo de vehículos, paneles informativos electrónicos y una API REST para la gestión y consulta de datos de ocupación en tiempo real.

## Características Principales

- 🚗 **Conteo Automático**: Recepción de datos de cámaras de conteo de vehículos
- 📊 **Gestión en Tiempo Real**: Actualización automática de ocupación de aparcamientos
- 🖥️ **Paneles Informativos**: Comunicación automática con paneles electrónicos
- 🔌 **API REST**: Endpoints públicos para consulta y gestión
- 📈 **Histórico**: Registro de 15 días de evolución de ocupación
- 🎯 **Estados Inteligentes**: LIBRE, DENSO, OCUPADO según umbrales configurables
- 📝 **Mensajes Programados**: Sistema de mensajes temporales en paneles
- 🔧 **Monitoreo**: Sistema completo de monitoreo y alertas

## Arquitectura

```
┌─────────────────┐    HTTP POST    ┌─────────────────┐
│   Cámaras IP    │ ──────────────► │ Servidor Cámaras│
│                 │                 │   Puerto 6400   │
└─────────────────┘                 └─────────────────┘
                                              │
                                              ▼
┌─────────────────┐                 ┌─────────────────┐
│   API REST      │ ◄────────────── │   Base de       │
│  Puerto 6001    │                 │   Datos         │
└─────────────────┘                 │  PostgreSQL     │
       │                            └─────────────────┘
       ▼
┌─────────────────┐
│  Paneles        │
│  Electrónicos   │
└─────────────────┘
```

## Tecnologías

- **Backend**: Python 3.x con Flask
- **Base de Datos**: PostgreSQL 12+
- **ORM**: SQLAlchemy 2.0
- **Servidor WSGI**: Gunicorn
- **Gestión de Servicios**: Systemd
- **Comunicación**: HTTP REST

## Instalación Rápida

### Requisitos
- Ubuntu 20.04 LTS o superior
- Python 3.8+
- PostgreSQL 12+
- 4 GB RAM mínimo
- 20 GB disco mínimo

### Despliegue Automático

```bash
# Clonar repositorio
git clone https://github.com/Swat-id/parking_altea.git
cd parking_altea

# Ejecutar script de instalación
chmod +x deploy/setup.sh
./deploy/setup.sh
```

### Instalación Manual

```bash
# 1. Instalar dependencias del sistema
apt update && apt install -y python3-venv python3-pip postgresql libpq-dev build-essential git

# 2. Configurar PostgreSQL
sudo -u postgres psql <<EOF
CREATE USER parking_user WITH PASSWORD 'parking_pass';
CREATE DATABASE parking_db OWNER parking_user;
\q
EOF

# 3. Configurar entorno Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Inicializar base de datos
cd src
python3 init_db.py
python3 load_data.py

# 5. Configurar servicios
cp deploy/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable parking-api.service parking-camera.service
systemctl start parking-api.service parking-camera.service
```

## Uso

### API REST

```bash
# Listar aparcamientos
curl http://157.180.91.63:6001/parkings

# Obtener detalle de aparcamiento
curl http://157.180.91.63:6001/parking/1

# Actualizar ocupación manual
curl -X POST http://157.180.91.63:6001/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 100}'

# Programar mensaje
curl -X POST http://157.180.91.63:6001/parking/1/message \
  -H "Content-Type: application/json" \
  -d '{
    "start": "2025-01-15T10:00:00",
    "end": "2025-01-15T18:00:00",
    "message": "Mantenimiento programado"
  }'
```

### Servidor de Cámaras

```bash
# Enviar mensaje de cámara
curl -X POST http://157.180.91.63:6400/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 172.20.17.146" \
  -d '{
    "event": "Object Counting",
    "device": "ciutat_esportiva camera 1",
    "line": 1,
    "Vehicle In": 10,
    "Vehicle Out": 5
  }'
```

## Configuración

### Variables de Entorno

Crear archivo `.env`:

```env
DATABASE_URL=postgresql://parking_user:parking_pass@localhost:5432/parking_db
CAMERA_PORT=6400
API_PORT=6001
LOG_RETENTION_DAYS=15
```

### Aparcamientos Configurados

| ID | Nombre | Capacidad | Umbral Denso | Umbral Completo |
|----|--------|-----------|--------------|-----------------|
| 1 | P. Ciutat Esportiva | 400 | 25 | 5 |
| 2 | P. Basseta Centre | 500 | 25 | 5 |
| 3 | P. Poble antic/Belles Arts 1 | 200 | 25 | 5 |
| 4 | P. Poble antic/Belles Arts 2 | 45 | 5 | 5 |
| 5 | P. Poble antic/Palau Altea | 90 | 10 | 4 |
| 6 | P. Poble antic/Conservatori | 120 | 10 | 4 |
| 7 | P. Port Altea | 166 | 10 | 4 |
| 8 | P. Estació Altea | 80 | 10 | 4 |
| 9 | P. Altea la Vella | 60 | 10 | 4 |

## Monitoreo

### Verificar Estado del Sistema

```bash
# Estado de servicios
systemctl status parking-api.service parking-camera.service

# Logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f

# Verificar API
curl http://157.180.91.63:6001/parkings
```

### Script de Monitoreo Automático

```bash
# Ejecutar verificación
/opt/parking_altea/check_status.sh
```

## Documentación

La documentación completa está disponible en el directorio [`/docs`](./docs/):

- [📋 Documentación Principal](./docs/README.md)
- [🔌 API REST](./docs/api.md)
- [📹 Protocolo de Cámaras](./docs/cameras.md)
- [🖥️ Comunicación con Paneles](./docs/panels.md)
- [🗄️ Base de Datos](./docs/database.md)
- [🚀 Guía de Despliegue](./docs/deployment.md)
- [🔧 Mantenimiento](./docs/maintenance.md)

## Estructura del Proyecto

```
parking_altea/
├── docs/                          # Documentación completa
├── src/                           # Código fuente
│   ├── api_server.py             # Servidor API REST
│   ├── camera_server.py          # Servidor de cámaras
│   ├── panel_client.py           # Cliente de paneles
│   ├── models.py                 # Modelos de BD
│   ├── config.py                 # Configuración
│   ├── init_db.py                # Inicialización BD
│   └── load_data.py              # Carga de datos
├── csv_templates/                 # Plantillas CSV
├── deploy/                        # Archivos de despliegue
├── requirements.txt               # Dependencias Python
└── README.md                      # Este archivo
```

## Servicios

### Puertos Utilizados
- **6001**: API REST pública
- **6400**: Servidor de recepción de cámaras
- **5432**: PostgreSQL (interno)

### Servicios Systemd
- `parking-api.service`: Servidor API REST
- `parking-camera.service`: Servidor de cámaras

## Mantenimiento

### Tareas Diarias
- Verificación de servicios
- Monitoreo de recursos
- Revisión de logs de errores

### Tareas Semanales
- Limpieza de logs
- Verificación de base de datos
- Limpieza de histórico (15 días)

### Tareas Mensuales
- Backup completo
- Análisis de rendimiento
- Actualización de sistema

## Soporte

### Información de Contacto
- **Email**: admin@swat-id.com
- **Servidor**: 157.180.91.63
- **Usuario**: root

### Troubleshooting
- [Guía de Troubleshooting](./docs/maintenance.md#troubleshooting-avanzado)
- [Logs del Sistema](./docs/maintenance.md#monitoreo-diario)
- [Verificación de Estado](./docs/deployment.md#verificación-de-la-instalación)

## Estado del Proyecto

### ✅ Completado
- Arquitectura base del sistema
- Servidor de recepción de cámaras
- API REST pública
- Base de datos PostgreSQL
- Comunicación con paneles
- Scripts de despliegue
- Documentación técnica completa
- Sistema de monitoreo y alertas

### 🔄 En Desarrollo
- Pruebas de integración
- Optimización de rendimiento
- Monitoreo avanzado

### 📋 Pendiente
- Panel de administración web
- Reportes y analytics avanzados
- Integración con sistemas externos
- Autenticación y autorización

## Licencia

Este proyecto es propiedad de Swat-id y está destinado al uso exclusivo del Ayuntamiento de Altea.

---

**Versión**: 1.0  
**Fecha**: Enero 2025  
**Estado**: Producción  
**Última actualización**: Documentación completa
