# Análisis del Sistema de Alarmas - v3.2.0_alarms

## 📋 Información General

- **Versión**: v3.2.0_alarms
- **Fecha de Análisis**: 28/07/2025
- **Objetivo**: Implementar sistema completo de alarmas para paneles, cámaras y aparcamientos
- **Estado**: Análisis y planificación

## 🎯 Objetivos del Sistema de Alarmas

### Funcionalidades Principales
1. **Gestión de Alarmas por Usuario**
   - Creación de alarmas personalizadas
   - Histórico de alarmas generadas
   - Notificaciones por email al usuario creador

2. **Tipos de Alarmas**
   - **Alarmas de Paneles**: Desconexión por rangos de tiempo
   - **Alarmas de Cámaras**: Desconexión por rangos de tiempo
   - **Alarmas de Aparcamientos**: Ocupación fuera de rangos y sin información

3. **Sistema de Gravedad**
   - **LEVE**: Primer rango de tiempo/valores
   - **NORMAL**: Segundo rango de tiempo/valores
   - **GRAVE**: Tercer rango de tiempo/valores

4. **Validación de Comunicación**
   - Ping a IPs de equipos
   - Verificación periódica (cada 5 minutos)
   - Prevención de alarmas duplicadas

## 🏗️ Arquitectura del Sistema

### Componentes Nuevos

1. **Alarm Service** (`src/alarm_service.py`)
   - Gestión de alarmas activas
   - Validación de condiciones
   - Generación de notificaciones

2. **Alarm Monitor Service** (`src/alarm_monitor_service.py`)
   - Servicio de monitorización continua
   - Verificación periódica de equipos
   - Ejecución de pings y validaciones

3. **Email Service** (`src/email_service.py`)
   - Envío de notificaciones por email
   - Plantillas de mensajes
   - Configuración SMTP

4. **Frontend - Alarmas**
   - Página de gestión de alarmas
   - Formularios de creación
   - Histórico y resolución

### Componentes Modificados

1. **API Server** (`src/api_server.py`)
   - Nuevos endpoints para alarmas
   - Integración con servicios de alarmas

2. **Models** (`src/models.py`)
   - Nuevas tablas para alarmas
   - Relaciones con usuarios y equipos

## 📊 Análisis de Base de Datos

### Nuevas Tablas Requeridas

#### 1. `alarm_configurations`
```sql
CREATE TABLE alarm_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    alarm_type VARCHAR(50) NOT NULL, -- 'panel', 'camera', 'parking'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `alarm_configuration_targets`
```sql
CREATE TABLE alarm_configuration_targets (
    id SERIAL PRIMARY KEY,
    alarm_configuration_id INTEGER REFERENCES alarm_configurations(id),
    target_type VARCHAR(50) NOT NULL, -- 'panel', 'camera', 'parking'
    target_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `alarm_configuration_thresholds`
```sql
CREATE TABLE alarm_configuration_thresholds (
    id SERIAL PRIMARY KEY,
    alarm_configuration_id INTEGER REFERENCES alarm_configurations(id),
    severity VARCHAR(20) NOT NULL, -- 'LEVE', 'NORMAL', 'GRAVE'
    threshold_value INTEGER NOT NULL, -- minutos para desconexión o % para ocupación
    threshold_type VARCHAR(50) NOT NULL, -- 'disconnection_time', 'occupancy_high', 'occupancy_low'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. `alarms`
```sql
CREATE TABLE alarms (
    id SERIAL PRIMARY KEY,
    alarm_configuration_id INTEGER REFERENCES alarm_configurations(id),
    user_id INTEGER REFERENCES users(id),
    severity VARCHAR(20) NOT NULL, -- 'LEVE', 'NORMAL', 'GRAVE'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved'
    message TEXT NOT NULL,
    affected_targets JSONB, -- Lista de equipos afectados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_description TEXT
);
```

#### 5. `alarm_history`
```sql
CREATE TABLE alarm_history (
    id SERIAL PRIMARY KEY,
    alarm_id INTEGER REFERENCES alarms(id),
    action VARCHAR(50) NOT NULL, -- 'created', 'resolved', 'escalated'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Relaciones y Constraints
- Un usuario puede tener múltiples configuraciones de alarmas
- Una configuración puede tener múltiples objetivos (paneles, cámaras, aparcamientos)
- Una configuración puede tener múltiples umbrales (LEVE, NORMAL, GRAVE)
- Una alarma activa previene la generación de alarmas duplicadas del mismo tipo y gravedad

## 🔌 API Endpoints

### Gestión de Configuraciones de Alarmas

#### GET `/api/alarms/configurations`
```json
{
  "configurations": [
    {
      "id": 1,
      "name": "Alarma Paneles Centro",
      "description": "Monitorización de paneles del centro",
      "alarm_type": "panel",
      "status": "active",
      "targets": [
        {"id": 1, "name": "PANEL PALAU", "type": "panel"},
        {"id": 2, "name": "PANEL C. ESPORTIVA", "type": "panel"}
      ],
      "thresholds": [
        {"severity": "LEVE", "threshold_value": 5, "threshold_type": "disconnection_time"},
        {"severity": "NORMAL", "threshold_value": 15, "threshold_type": "disconnection_time"},
        {"severity": "GRAVE", "threshold_value": 30, "threshold_type": "disconnection_time"}
      ],
      "created_at": "2025-07-28T15:00:00Z"
    }
  ]
}
```

#### POST `/api/alarms/configurations`
```json
{
  "name": "Nueva Alarma",
  "description": "Descripción de la alarma",
  "alarm_type": "panel",
  "targets": [1, 2, 3],
  "thresholds": [
    {"severity": "LEVE", "threshold_value": 5, "threshold_type": "disconnection_time"},
    {"severity": "NORMAL", "threshold_value": 15, "threshold_type": "disconnection_time"},
    {"severity": "GRAVE", "threshold_value": 30, "threshold_type": "disconnection_time"}
  ]
}
```

#### PUT `/api/alarms/configurations/{id}`
```json
{
  "name": "Alarma Actualizada",
  "status": "paused",
  "thresholds": [...]
}
```

#### DELETE `/api/alarms/configurations/{id}`

### Gestión de Alarmas Activas

#### GET `/api/alarms`
```json
{
  "alarms": [
    {
      "id": 1,
      "configuration_name": "Alarma Paneles Centro",
      "severity": "NORMAL",
      "status": "active",
      "message": "PANEL PALAU desconectado por 15 minutos",
      "affected_targets": [
        {"id": 1, "name": "PANEL PALAU", "type": "panel", "ip": "172.20.4.50"}
      ],
      "created_at": "2025-07-28T15:30:00Z"
    }
  ]
}
```

#### POST `/api/alarms/{id}/resolve`
```json
{
  "resolution_description": "Se reinició el panel y se verificó la conexión"
}
```

### Estado de Equipos

#### GET `/api/alarms/equipment-status`
```json
{
  "panels": [
    {
      "id": 1,
      "name": "PANEL PALAU",
      "ip": "172.20.4.50",
      "status": "online",
      "last_ping": "2025-07-28T15:35:00Z",
      "response_time": 15
    }
  ],
  "cameras": [...],
  "parkings": [...]
}
```

## 🎨 Frontend - Análisis de Componentes

### Páginas Principales

#### 1. `client/src/pages/Alarms.jsx`
- Lista de configuraciones de alarmas
- Estado de alarmas activas
- Acciones rápidas (pausar, editar, eliminar)

#### 2. `client/src/pages/AlarmConfiguration.jsx`
- Formulario de creación/edición de alarmas
- Selector de objetivos (paneles, cámaras, aparcamientos)
- Configuración de umbrales por gravedad

#### 3. `client/src/pages/AlarmHistory.jsx`
- Histórico de alarmas generadas
- Filtros por fecha, tipo, gravedad
- Detalles de resolución

### Componentes Reutilizables

#### 1. `client/src/components/AlarmConfigurationForm.jsx`
```jsx
const AlarmConfigurationForm = ({ 
  alarmType, 
  targets, 
  thresholds, 
  onSubmit 
}) => {
  // Formulario dinámico según tipo de alarma
  // Selector de objetivos
  // Configuración de umbrales
}
```

#### 2. `client/src/components/AlarmSeveritySelector.jsx`
```jsx
const AlarmSeveritySelector = ({ 
  severity, 
  thresholdValue, 
  onChange 
}) => {
  // Selector de gravedad (LEVE, NORMAL, GRAVE)
  // Input para valor del umbral
}
```

#### 3. `client/src/components/AlarmStatusCard.jsx`
```jsx
const AlarmStatusCard = ({ alarm }) => {
  // Tarjeta de estado de alarma
  // Indicadores visuales de gravedad
  // Botones de acción
}
```

### Servicios Frontend

#### 1. `client/src/services/alarmService.js`
```javascript
class AlarmService {
  // Configuraciones
  async getAlarmConfigurations()
  async createAlarmConfiguration(config)
  async updateAlarmConfiguration(id, config)
  async deleteAlarmConfiguration(id)
  
  // Alarmas activas
  async getActiveAlarms()
  async resolveAlarm(id, resolution)
  
  // Estado de equipos
  async getEquipmentStatus()
  
  // Histórico
  async getAlarmHistory(filters)
}
```

## 🔧 Servicios Backend

### 1. Alarm Service (`src/alarm_service.py`)
```python
class AlarmService:
    def __init__(self, session):
        self.session = session
    
    def check_alarm_conditions(self):
        """Verificar condiciones de todas las alarmas activas"""
        
    def create_alarm(self, configuration_id, severity, message, affected_targets):
        """Crear nueva alarma"""
        
    def resolve_alarm(self, alarm_id, resolution_description):
        """Resolver alarma existente"""
        
    def check_duplicate_alarm(self, configuration_id, severity):
        """Verificar si ya existe una alarma activa del mismo tipo y gravedad"""
```

### 2. Alarm Monitor Service (`src/alarm_monitor_service.py`)
```python
class AlarmMonitorService:
    def __init__(self):
        self.alarm_service = None
        self.check_interval = 300  # 5 minutos
        
    def start_monitoring(self):
        """Iniciar monitorización continua"""
        
    def check_panel_connectivity(self, panel):
        """Verificar conectividad de panel mediante ping"""
        
    def check_camera_connectivity(self, camera):
        """Verificar conectividad de cámara mediante ping"""
        
    def check_parking_status(self, parking):
        """Verificar estado de aparcamiento"""
        
    def check_parking_information_availability(self, parking):
        """Verificar disponibilidad de información del aparcamiento"""
```

### 3. Email Service (`src/email_service.py`)
```python
class EmailService:
    def __init__(self):
        self.smtp_config = self.load_smtp_config()
    
    def send_alarm_notification(self, user_email, alarm_data):
        """Enviar notificación de alarma por email"""
        
    def send_alarm_resolution_notification(self, user_email, alarm_data):
        """Enviar notificación de resolución de alarma"""
```

## 📋 Plan de Implementación

### Fase 1: Base de Datos y Modelos
1. **Crear migración de base de datos**
   - Script de migración con nuevas tablas
   - Índices para optimización
   - Constraints de integridad

2. **Actualizar modelos SQLAlchemy**
   - Nuevas clases de modelo
   - Relaciones entre entidades
   - Métodos de utilidad

### Fase 2: Servicios Backend
1. **Implementar Alarm Service**
   - Lógica de verificación de condiciones
   - Gestión de alarmas activas
   - Prevención de duplicados

2. **Implementar Alarm Monitor Service**
   - Servicio de monitorización continua
   - Verificación de conectividad por ping
   - Integración con Alarm Service

3. **Implementar Email Service**
   - Configuración SMTP
   - Plantillas de email
   - Envío de notificaciones

### Fase 3: API Endpoints
1. **Endpoints de configuración de alarmas**
   - CRUD completo de configuraciones
   - Validación de datos
   - Gestión de objetivos y umbrales

2. **Endpoints de alarmas activas**
   - Listado de alarmas activas
   - Resolución de alarmas
   - Histórico de alarmas

3. **Endpoints de estado de equipos**
   - Estado de conectividad
   - Métricas de respuesta
   - Información de equipos

### Fase 4: Frontend
1. **Página principal de alarmas**
   - Lista de configuraciones
   - Estado de alarmas activas
   - Navegación y filtros

2. **Formularios de configuración**
   - Creación de alarmas
   - Edición de configuraciones
   - Selectores de objetivos

3. **Histórico y resolución**
   - Vista de histórico
   - Formulario de resolución
   - Detalles de alarmas

### Fase 5: Integración y Testing
1. **Integración de servicios**
   - Configuración de servicios systemd
   - Logs y monitoreo
   - Manejo de errores

2. **Testing completo**
   - Pruebas unitarias
   - Pruebas de integración
   - Pruebas de usuario

## 🚨 Consideraciones de Seguridad

### Autenticación y Autorización
- Todas las operaciones requieren autenticación
- Los usuarios solo pueden gestionar sus propias alarmas
- Validación de permisos en endpoints

### Validación de Datos
- Validación de IPs en configuraciones
- Límites en valores de umbrales
- Sanitización de mensajes de resolución

### Rate Limiting
- Límites en creación de alarmas
- Protección contra spam de notificaciones
- Control de frecuencia de verificaciones

## 📊 Métricas y Monitoreo

### Métricas del Sistema
- Número de alarmas activas por tipo
- Tiempo promedio de resolución
- Frecuencia de alarmas por usuario
- Estado de conectividad de equipos

### Logs y Auditoría
- Log de todas las operaciones de alarmas
- Auditoría de cambios en configuraciones
- Trazabilidad de resoluciones

## 🔄 Migración y Despliegue

### Script de Migración
```python
# migrate_alarm_system.py
def migrate_alarm_system():
    """Migración completa del sistema de alarmas"""
    # 1. Crear nuevas tablas
    # 2. Crear índices
    # 3. Configurar constraints
    # 4. Datos iniciales si es necesario
```

### Configuración de Servicios
```ini
# /etc/systemd/system/parking-alarm-monitor.service
[Unit]
Description=Parking Alarm Monitor Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea
Environment=PATH=/opt/parking_altea/venv/bin
ExecStart=/opt/parking_altea/venv/bin/python src/alarm_monitor_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📝 Próximos Pasos

1. **Revisión del análisis** - Validar requerimientos y arquitectura
2. **Implementación de Fase 1** - Base de datos y modelos
3. **Implementación de Fase 2** - Servicios backend
4. **Implementación de Fase 3** - API endpoints
5. **Implementación de Fase 4** - Frontend
6. **Implementación de Fase 5** - Integración y testing

---

**Nota**: Este análisis debe ser revisado y aprobado antes de proceder con la implementación. 