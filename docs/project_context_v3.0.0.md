# Contexto del Proyecto - Parking Altea v3.0.0

## 🎯 Objetivo del Proyecto

El sistema de gestión de parkings de Altea es una plataforma integral para el monitoreo y control de aparcamientos públicos en tiempo real. El sistema integra cámaras de conteo de vehículos, paneles informativos LED y una interfaz web para la gestión administrativa.

**Fecha de actualización**: Enero 2025  
**Versión**: v3.0.0  
**Estado**: ✅ **PRODUCCIÓN - ESTABLE**

## 🏗️ Arquitectura del Sistema

### Componentes Principales

#### 1. **Backend (Python Flask)**
- **API Server** (Puerto 6001): Gestión de datos, autenticación y endpoints REST
- **Camera Server** (Puerto 6400): Recepción y procesamiento de mensajes de cámaras
- **Base de Datos**: PostgreSQL con SQLAlchemy ORM
- **Panel Communication Service**: Comunicación unificada con paneles informativos

#### 2. **Frontend (React + Vite)**
- **Dashboard**: Vista general de todos los parkings
- **Parking Detail**: Gestión individual de parkings
- **Camera Logs**: Visualización de logs de cámaras
- **Statistics**: Estadísticas y reportes
- **Profile**: Gestión de usuarios
- **Schedules**: Gestión de programaciones de paneles

#### 3. **Servicios de Paneles**
- **Panel Communication Service** (Python): API unificada para comunicación con paneles
- **Java Panel Service** (Puerto 5656): Servicio Java para protocolo CP5200
- **Schedule Monitor Service**: Monitoreo y ejecución de programaciones

#### 4. **Infraestructura**
- **Servidor**: Ubuntu en 157.180.91.63
- **Proxy**: Nginx para frontend y balanceo
- **Servicios**: Systemd para gestión de procesos
- **Base de Datos**: PostgreSQL en localhost:5432

## 📊 Estructura de Base de Datos

### Diagrama ER Completo

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    parkings     │     │    accesses     │     │     panels      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────┤ parking_id (FK) │     │ parking_id (FK) │
│ name            │     │ ip              │     │ name            │
│ location        │     │ line            │     │ ip              │
│ max_capacity    │     │ name            │     │ status          │
│ threshold_dense │     │ last_vehicle_in │     │ last_message    │
│ threshold_full  │     │ last_vehicle_out│     │ last_update     │
│ current_occupancy│    │ status          │     │ panel_type_id   │
│ status          │     │ last_message_received│ └─────────────────┘
│ fixed_message_flag│   └─────────────────┘             │
│ created_at      │                                     │
│ updated_at      │                                     ▼
└─────────────────┘     ┌─────────────────┐     ┌─────────────────┐
         │              │occupancy_history│     │  panel_types    │
         ▼              ├─────────────────┤     ├─────────────────┤
┌─────────────────┐     │ parking_id (FK) │     │ id (PK)         │
│scheduled_messages│     │ timestamp       │     │ name            │
├─────────────────┤     │ occupancy       │     │ protocol        │
│ parking_id (FK) │     │ source          │     │ default_color   │
│ start_time      │     │ previous_occupancy│   │ default_font_size│
│ end_time        │     │ change_amount   │     │ default_effect  │
│ message         │     │ adjustment_type │     └─────────────────┘
│ color           │     └─────────────────┘
│ scroll          │
│ is_active       │
└─────────────────┘
```

### Tablas Principales

#### 1. **parkings** - Información de aparcamientos
```sql
CREATE TABLE parkings (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    location VARCHAR,
    max_capacity INTEGER NOT NULL,
    threshold_dense INTEGER NOT NULL,
    threshold_full INTEGER NOT NULL,
    current_occupancy INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR DEFAULT 'LIBRE' NOT NULL,
    fixed_message_flag BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Estados posibles:**
- `LIBRE`: Plazas libres > threshold_dense
- `DENSO`: Plazas libres ≤ threshold_dense
- `COMPLETO`: Plazas libres ≤ threshold_full o descuadre negativo

#### 2. **accesses** - Cámaras de acceso
```sql
CREATE TABLE accesses (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id),
    ip VARCHAR NOT NULL,
    line INTEGER NOT NULL,
    name VARCHAR,
    last_vehicle_in INTEGER DEFAULT 0 NOT NULL,
    last_vehicle_out INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR DEFAULT 'OFFLINE',
    last_message_received TIMESTAMP,
    UNIQUE(ip, line)
);
```

**Estados de cámaras:**
- `ONLINE`: Mensaje recibido en la última hora
- `OFFLINE`: Sin mensajes en la última hora

#### 3. **panels** - Paneles informativos
```sql
CREATE TABLE panels (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id),
    name VARCHAR NOT NULL,
    ip VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'OFFLINE',
    last_message TEXT,
    last_update TIMESTAMP,
    panel_type_id INTEGER REFERENCES panel_types(id)
);
```

**Estados de paneles:**
- `ONLINE`: Ping exitoso
- `OFFLINE`: Ping fallido

#### 4. **panel_types** - Tipos de paneles
```sql
CREATE TABLE panel_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    protocol VARCHAR NOT NULL,
    default_color INTEGER DEFAULT 2,
    default_font_size INTEGER DEFAULT 2,
    default_effect INTEGER DEFAULT 1
);
```

#### 5. **occupancy_history** - Histórico de ocupación
```sql
CREATE TABLE occupancy_history (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id),
    occupancy INTEGER NOT NULL,
    source VARCHAR NOT NULL,
    previous_occupancy INTEGER,
    change_amount INTEGER,
    adjustment_type VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fuentes de cambio:**
- `camera`: Mensaje de cámara
- `manual`: Ajuste manual
- `scheduled_adjust`: Ajuste programado

#### 6. **scheduled_messages** - Programaciones de paneles
```sql
CREATE TABLE scheduled_messages (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    message TEXT NOT NULL,
    color VARCHAR DEFAULT 'VERDE',
    scroll BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 7. **camera_logs** - Logs detallados de cámaras
```sql
CREATE TABLE camera_logs (
    id SERIAL PRIMARY KEY,
    access_id INTEGER REFERENCES accesses(id),
    parking_id INTEGER REFERENCES parkings(id),
    camera_ip VARCHAR,
    camera_line INTEGER,
    camera_name VARCHAR,
    raw_message TEXT,
    vehicle_in INTEGER,
    vehicle_out INTEGER,
    previous_vehicle_in INTEGER,
    previous_vehicle_out INTEGER,
    delta_in INTEGER,
    delta_out INTEGER,
    status VARCHAR,
    error_message TEXT,
    processing_time INTEGER,
    new_occupancy INTEGER,
    occupancy_change INTEGER,
    parking_status VARCHAR,
    processed_at TIMESTAMP DEFAULT NOW()
);
```

#### 8. **users** - Usuarios del sistema
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 9. **user_parkings** - Asignación de parkings a usuarios
```sql
CREATE TABLE user_parkings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    parking_id INTEGER NOT NULL REFERENCES parkings(id),
    UNIQUE(user_id, parking_id)
);
```

## 🔄 Flujos de Datos Principales

### 1. Flujo de Mensajes de Cámaras

```
Cámara → POST /camera → Camera Server → Base de Datos → Paneles
```

**Proceso detallado:**

1. **Recepción**: Cámara envía JSON al endpoint `/camera` (Puerto 6400)
2. **Validación**: Verificación de formato y campos requeridos
3. **Protección Duplicados**: Cache en memoria por 5 minutos
4. **Identificación**: Búsqueda por IP+línea o nombre+línea
5. **Procesamiento**: Cálculo de deltas y actualización de ocupación
6. **Logging**: Registro completo en CameraLog
7. **Actualización de Estado**: Cálculo automático según umbrales
8. **Broadcast a Paneles**: Envío vía PanelCommunicationService
9. **Respuesta**: Confirmación a la cámara

**Formato del mensaje:**
```json
{
  "device": "nombre_camara",
  "line": 0,
  "Vehicle In": 1234,
  "Vehicle Out": 567,
  "event": "optional",
  "time": "optional"
}
```

### 2. Flujo de Actualización Manual de Ocupación

```
Frontend → API Server → Base de Datos → Paneles
```

**Proceso:**
1. Usuario ajusta ocupación en frontend
2. API Server recibe POST `/parking/{id}/occupancy`
3. Validación de datos y permisos
4. Actualización en base de datos
5. Cálculo automático de estado
6. Envío a paneles vía PanelCommunicationService
7. Respuesta con datos actualizados

### 3. Flujo de Comunicación con Paneles

```
API Server → PanelCommunicationService → Java Panel Service → Panel LED
```

**Arquitectura de comunicación:**
- **PanelCommunicationService** (Python): API unificada
- **Java Panel Service** (Puerto 5656): Protocolo CP5200
- **Protocolo TCP**: Conexión directa en puerto 5200
- **Timeout**: 3 segundos por panel
- **Reconexión**: Automática en caso de error

**Mensajes en valenciano:**
- `LLIURE`: Estado libre (Verde)
- `DENS`: Estado denso (Amarillo)
- `COMPLET`: Estado completo (Rojo)

### 4. Flujo de Programaciones de Paneles

```
Schedule Monitor → Base de Datos → PanelCommunicationService → Paneles
```

**Proceso:**
1. Schedule Monitor verifica programaciones activas
2. Ejecuta mensajes programados
3. Envía vía PanelCommunicationService
4. Registra ejecución en logs

## 🔧 Servicios y Puertos

### Servicios Backend
- **parking-api.service**: Puerto 6001 (API REST)
- **parking-camera.service**: Puerto 6400 (Servidor de cámaras)
- **panel-service.service**: Puerto 5656 (Servicio Java de paneles)
- **parking-schedule-monitor.service**: Monitoreo de programaciones

### Servicios Frontend
- **Nginx**: Puerto 80/443 (Proxy y frontend)
- **Frontend React**: Puerto 5789 (Desarrollo)

### Base de Datos
- **PostgreSQL**: Puerto 5432
- **Base de datos**: parking_db
- **Usuario**: parking_user

## 📊 Datos Actuales del Sistema

### Parkings (9 total)
1. **P. Ciutat Esportiva** - 500 plazas
2. **P. Poble antic/Belles Arts 1** - 45 plazas
3. **P. Poble antic/Belles Arts 2** - 45 plazas
4. **P. Poble antic/Belles Arts 3** - 45 plazas
5. **P. Poble antic/Belles Arts 4** - 45 plazas
6. **P. Poble antic/Belles Arts 5** - 45 plazas
7. **P. Port Altea** - 166 plazas
8. **P. Estació Altea** - 80 plazas
9. **P. Altea Hills** - 200 plazas

### Paneles (10 total)
- **PANEL PITERES**: 172.20.8.51 (Parking 6)
- **PANEL PITERES 2**: 172.20.8.51 (Parking 6)
- **PANEL PORT**: 172.20.4.52 (Parking 7)
- **PANEL ESTACIO**: 172.20.4.53 (Parking 8)
- **PANEL HILLS**: 172.20.4.54 (Parking 9)
- **PANEL CIUTAT ESPORTIVA**: 172.20.4.55 (Parking 1)
- **PANEL BELLES ARTS 1**: 172.20.4.56 (Parking 2)
- **PANEL BELLES ARTS 2**: 172.20.4.57 (Parking 3)
- **PANEL BELLES ARTS 3**: 172.20.4.58 (Parking 4)
- **PANEL BELLES ARTS 4**: 172.20.4.59 (Parking 5)

### Cámaras (13 total)
- **Cámaras distribuidas** en los 9 parkings
- **Protocolo**: Mensajes JSON vía HTTP POST
- **Frecuencia**: En tiempo real según tráfico

### Usuarios (2 total)
- **Superadmin**: info@swat-id.com
- **Usuario de prueba**: test@example.com

## 🛠️ Funcionalidades Implementadas v3.0.0

### ✅ Gestión de Ocupación
- [x] Recepción de mensajes de cámaras en tiempo real
- [x] Cálculo automático de deltas y ocupación
- [x] Protección contra mensajes duplicados
- [x] Ajuste manual de ocupación
- [x] Histórico completo de cambios
- [x] Estados automáticos según umbrales

### ✅ Comunicación con Paneles
- [x] API unificada para comunicación con paneles
- [x] Protocolo CP5200 implementado
- [x] Mensajes en valenciano (LLIURE, DENS, COMPLET)
- [x] Colores dinámicos según estado
- [x] Verificación de conectividad por ping
- [x] Manejo de errores y timeouts

### ✅ Programaciones de Paneles
- [x] Sistema de programaciones temporales
- [x] Monitor automático de programaciones
- [x] Mensajes personalizados con colores
- [x] Activación/desactivación de programaciones
- [x] Logs de ejecución

### ✅ Autenticación y Autorización
- [x] Sistema JWT para autenticación
- [x] Control de acceso granular por parking
- [x] Modo sin login para desarrollo
- [x] Gestión de usuarios y roles
- [x] Cambio seguro de contraseñas

### ✅ Monitoreo y Logs
- [x] Logs detallados de cámaras
- [x] Estados de cámaras (ONLINE/OFFLINE)
- [x] Estados de paneles (ONLINE/OFFLINE)
- [x] Estadísticas de ocupación por hora
- [x] Histórico de cambios de ocupación

### ✅ Frontend Completo
- [x] Dashboard con vista general
- [x] Gestión individual de parkings
- [x] Configuración de umbrales
- [x] Visualización de logs de cámaras
- [x] Estadísticas con gráficos
- [x] Gestión de programaciones
- [x] Interfaz responsive

## 🔄 Integraciones Existentes

### 1. **Integración con Cámaras**
- **Protocolo**: HTTP POST con JSON
- **Endpoint**: `/camera` en puerto 6400
- **Validación**: Formato y campos requeridos
- **Protección**: Anti-duplicados con cache
- **Logging**: Registro completo de operaciones

### 2. **Integración con Paneles LED**
- **Protocolo**: CP5200 vía TCP
- **Puerto**: 5200 (estándar del fabricante)
- **Servicio**: Java Panel Service (Puerto 5656)
- **API**: PanelCommunicationService unificada
- **Mensajes**: Texto en valenciano con colores

### 3. **Integración con Base de Datos**
- **Sistema**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Migraciones**: Automáticas
- **Backup**: Configurado
- **Monitoreo**: Logs de operaciones

### 4. **Integración Frontend-Backend**
- **API**: REST con JWT
- **CORS**: Configurado para desarrollo
- **Estado**: React Query para cache
- **Autenticación**: Context global
- **Errores**: Manejo centralizado

## 📈 Métricas y Monitoreo

### Métricas de Rendimiento
- **Tiempo de respuesta API**: < 500ms
- **Tiempo de actualización paneles**: < 3s
- **Uptime servicios**: > 99.9%
- **Latencia base de datos**: < 50ms

### Logs y Auditoría
- **Camera Logs**: Registro completo de mensajes
- **Occupancy History**: Histórico de cambios
- **Panel Logs**: Operaciones con paneles
- **Schedule Logs**: Ejecución de programaciones

## 🚀 Despliegue y Mantenimiento

### Servidor de Producción
- **IP**: 157.180.91.63
- **Sistema**: Ubuntu
- **Servicios**: Systemd
- **Proxy**: Nginx
- **Base de datos**: PostgreSQL local

### Comandos de Mantenimiento
```bash
# Reiniciar servicios
systemctl restart parking-api.service
systemctl restart parking-camera.service
systemctl restart panel-service.service

# Ver logs
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u panel-service.service -f

# Verificar estado
systemctl status parking-api.service
systemctl status parking-camera.service
systemctl status panel-service.service
```

### Scripts de Despliegue
- `deploy/update.sh`: Actualización completa
- `deploy/verify_v3.0.0_deployment.sh`: Verificación de despliegue
- `deploy/rollback_v3.0.0.sh`: Rollback en caso de problemas

## 🔮 Próximos Pasos y Evolución

### Mejoras Planificadas
1. **Dashboard avanzado** con métricas en tiempo real
2. **Notificaciones push** para eventos importantes
3. **API pública** para integración con aplicaciones externas
4. **Móvil app** para gestión remota
5. **Analytics avanzados** con machine learning

### Mantenimiento Continuo
- Monitoreo de rendimiento
- Actualización de dependencias
- Backup automático de base de datos
- Logs de auditoría
- Tests automatizados

---

**Documentación actualizada**: Enero 2025  
**Versión del sistema**: v3.0.0  
**Estado**: ✅ Producción estable 