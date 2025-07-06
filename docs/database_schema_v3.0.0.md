# Esquema de Base de Datos - Parking Altea v3.0.0

## Información General

- **Sistema**: PostgreSQL 13+
- **Host**: localhost
- **Puerto**: 5432
- **Base de Datos**: parking_db
- **Usuario**: parking_user
- **Contraseña**: parking_pass
- **ORM**: SQLAlchemy 2.0
- **Migraciones**: Automáticas

## Diagrama ER Completo

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
│scheduled_messages│     │ timestamp       │     │ protocol        │
├─────────────────┤     │ occupancy       │     │ default_color   │
│ parking_id (FK) │     │ source          │     │ default_font_size│
│ start_time      │     │ previous_occupancy│   │ default_effect  │
│ end_time        │     │ change_amount   │     │
│ message         │     │ adjustment_type │     └─────────────────┘
│ color           │     └─────────────────┘
│ scroll          │
│ is_active       │
└─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   camera_logs   │     │     users       │     │  user_parkings  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ access_id (FK)  │     │ id (PK)         │     │ user_id (FK)    │
│ parking_id (FK) │     │ email           │     │ parking_id (FK) │
│ camera_ip       │     │ password_hash   │     │ UNIQUE(user_id, │
│ camera_line     │     │ name            │     │  parking_id)    │
│ raw_message     │     │ role            │     └─────────────────┘
│ vehicle_in      │     │ created_at      │
│ vehicle_out     │     │ updated_at      │
│ delta_in        │     └─────────────────┘
│ delta_out       │
│ status          │
│ error_message   │
│ processing_time │
│ new_occupancy   │
│ occupancy_change│
│ parking_status  │
│ processed_at    │
└─────────────────┘
```

## Tablas Detalladas

### 1. Tabla: `parkings`

Almacena la información principal de cada aparcamiento.

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `name` | VARCHAR | Nombre del aparcamiento | UNIQUE, NOT NULL | Texto único |
| `location` | VARCHAR | Coordenadas GPS | Opcional | Texto |
| `max_capacity` | INTEGER | Capacidad máxima de plazas | NOT NULL | > 0 |
| `threshold_dense` | INTEGER | Umbral para estado DENSO | NOT NULL | ≥ 0 |
| `threshold_full` | INTEGER | Umbral para estado COMPLETO | NOT NULL | ≥ 0 |
| `current_occupancy` | INTEGER | Ocupación actual | DEFAULT 0, NOT NULL | ≥ 0 |
| `status` | VARCHAR | Estado calculado | DEFAULT 'LIBRE', NOT NULL | LIBRE/DENSO/COMPLETO |
| `fixed_message_flag` | BOOLEAN | Flag para mensaje fijo | DEFAULT FALSE, NOT NULL | true/false |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT NOW() | Auto |
| `updated_at` | TIMESTAMP | Fecha de actualización | DEFAULT NOW() | Auto |

#### Estados Posibles

- `LIBRE`: Plazas libres > threshold_dense
- `DENSO`: threshold_dense ≤ Plazas libres < threshold_full
- `COMPLETO`: Plazas libres ≤ threshold_full o descuadre negativo

#### Índices

```sql
CREATE INDEX idx_parkings_status ON parkings(status);
CREATE INDEX idx_parkings_updated_at ON parkings(updated_at);
```

### 2. Tabla: `accesses`

Almacena la información de las cámaras de acceso a cada aparcamiento.

```sql
CREATE TABLE accesses (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    ip VARCHAR NOT NULL,
    line INTEGER NOT NULL,
    name VARCHAR,
    last_vehicle_in INTEGER DEFAULT 0 NOT NULL,
    last_vehicle_out INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR DEFAULT 'OFFLINE',
    last_message_received TIMESTAMP WITH TIME ZONE,
    UNIQUE(ip, line)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL | Referencia a parkings |
| `ip` | VARCHAR | IP de la cámara | NOT NULL | IPv4/IPv6 |
| `line` | INTEGER | Número de línea de la cámara | NOT NULL | ≥ 0 |
| `name` | VARCHAR | Nombre descriptivo de la cámara | Opcional | Texto |
| `last_vehicle_in` | INTEGER | Último contador de entrada | DEFAULT 0, NOT NULL | ≥ 0 |
| `last_vehicle_out` | INTEGER | Último contador de salida | DEFAULT 0, NOT NULL | ≥ 0 |
| `status` | VARCHAR | Estado de la cámara | DEFAULT 'OFFLINE' | ONLINE/OFFLINE |
| `last_message_received` | TIMESTAMP | Último mensaje recibido | Opcional | Timestamp |

#### Índices Únicos

```sql
CREATE UNIQUE INDEX idx_access_ip_line ON accesses(ip, line);
CREATE INDEX idx_access_parking_id ON accesses(parking_id);
CREATE INDEX idx_access_status ON accesses(status);
```

### 3. Tabla: `panels`

Almacena la información de los paneles electrónicos de cada aparcamiento.

```sql
CREATE TABLE panels (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    ip VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'OFFLINE',
    last_message TEXT,
    last_update TIMESTAMP WITH TIME ZONE,
    panel_type_id INTEGER REFERENCES panel_types(id)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL | Referencia a parkings |
| `name` | VARCHAR | Nombre del panel | NOT NULL | Texto |
| `ip` | VARCHAR | IP del panel | NOT NULL | IPv4/IPv6 |
| `status` | VARCHAR | Estado del panel | DEFAULT 'OFFLINE' | ONLINE/OFFLINE |
| `last_message` | TEXT | Último mensaje enviado | Opcional | Texto |
| `last_update` | TIMESTAMP | Última actualización | Opcional | Timestamp |
| `panel_type_id` | INTEGER | Tipo de panel | FOREIGN KEY | Referencia a panel_types |

#### Índices

```sql
CREATE INDEX idx_panels_parking_id ON panels(parking_id);
CREATE INDEX idx_panels_status ON panels(status);
CREATE INDEX idx_panels_panel_type_id ON panels(panel_type_id);
```

### 4. Tabla: `panel_types`

Almacena los tipos de paneles y sus configuraciones por defecto.

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

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `name` | VARCHAR | Nombre del tipo | NOT NULL | Texto |
| `protocol` | VARCHAR | Protocolo de comunicación | NOT NULL | CP5200/OTRO |
| `default_color` | INTEGER | Color por defecto | DEFAULT 2 | 1=Rojo, 2=Verde, 3=Amarillo |
| `default_font_size` | INTEGER | Tamaño de fuente por defecto | DEFAULT 2 | 1=12px, 2=16px, 3=20px |
| `default_effect` | INTEGER | Efecto por defecto | DEFAULT 1 | 1=Fijo, 2=Scroll |

### 5. Tabla: `occupancy_history`

Registra el histórico de ocupación de los aparcamientos.

```sql
CREATE TABLE occupancy_history (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    occupancy INTEGER NOT NULL,
    source VARCHAR NOT NULL,
    previous_occupancy INTEGER,
    change_amount INTEGER,
    adjustment_type VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL | Referencia a parkings |
| `occupancy` | INTEGER | Ocupación registrada | NOT NULL | ≥ 0 |
| `source` | VARCHAR | Fuente del cambio | NOT NULL | camera/manual/scheduled_adjust |
| `previous_occupancy` | INTEGER | Ocupación anterior | Opcional | ≥ 0 |
| `change_amount` | INTEGER | Cantidad de cambio | Opcional | Entero |
| `adjustment_type` | VARCHAR | Tipo de ajuste | Opcional | increase/decrease/set |
| `created_at` | TIMESTAMP | Fecha y hora del registro | DEFAULT NOW() | Auto |

#### Fuentes Posibles

- `camera`: Cambio por mensaje de cámara
- `manual`: Cambio manual vía API
- `scheduled_adjust`: Ajuste programado automático

#### Índices

```sql
CREATE INDEX idx_occupancy_history_parking_id ON occupancy_history(parking_id);
CREATE INDEX idx_occupancy_history_created_at ON occupancy_history(created_at);
CREATE INDEX idx_occupancy_history_source ON occupancy_history(source);
```

### 6. Tabla: `scheduled_messages`

Almacena los mensajes programados para mostrar en los paneles.

```sql
CREATE TABLE scheduled_messages (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    color VARCHAR DEFAULT 'VERDE',
    scroll BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL | Referencia a parkings |
| `start_time` | TIMESTAMP | Fecha/hora de inicio | NOT NULL | Timestamp futuro |
| `end_time` | TIMESTAMP | Fecha/hora de fin | NOT NULL | Timestamp > start_time |
| `message` | TEXT | Mensaje a mostrar | NOT NULL | Texto |
| `color` | VARCHAR | Color del mensaje | DEFAULT 'VERDE' | VERDE/ROJO/AMARILLO |
| `scroll` | BOOLEAN | Efecto de scroll | DEFAULT FALSE | true/false |
| `is_active` | BOOLEAN | Estado activo | DEFAULT TRUE | true/false |

#### Índices

```sql
CREATE INDEX idx_scheduled_messages_parking_id ON scheduled_messages(parking_id);
CREATE INDEX idx_scheduled_messages_time_range ON scheduled_messages(start_time, end_time);
CREATE INDEX idx_scheduled_messages_is_active ON scheduled_messages(is_active);
```

### 7. Tabla: `camera_logs`

Registra logs detallados de todos los mensajes de cámaras.

```sql
CREATE TABLE camera_logs (
    id SERIAL PRIMARY KEY,
    access_id INTEGER REFERENCES accesses(id) ON DELETE SET NULL,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
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
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `access_id` | INTEGER | ID de la cámara | FOREIGN KEY | Referencia a accesses |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY | Referencia a parkings |
| `camera_ip` | VARCHAR | IP de la cámara | Opcional | IPv4/IPv6 |
| `camera_line` | INTEGER | Línea de la cámara | Opcional | ≥ 0 |
| `camera_name` | VARCHAR | Nombre de la cámara | Opcional | Texto |
| `raw_message` | TEXT | Mensaje raw recibido | Opcional | JSON/Texto |
| `vehicle_in` | INTEGER | Contador de entrada | Opcional | ≥ 0 |
| `vehicle_out` | INTEGER | Contador de salida | Opcional | ≥ 0 |
| `previous_vehicle_in` | INTEGER | Contador anterior entrada | Opcional | ≥ 0 |
| `previous_vehicle_out` | INTEGER | Contador anterior salida | Opcional | ≥ 0 |
| `delta_in` | INTEGER | Diferencia de entrada | Opcional | Entero |
| `delta_out` | INTEGER | Diferencia de salida | Opcional | Entero |
| `status` | VARCHAR | Estado del procesamiento | Opcional | processed/error/reset |
| `error_message` | TEXT | Mensaje de error | Opcional | Texto |
| `processing_time` | INTEGER | Tiempo de procesamiento (ms) | Opcional | ≥ 0 |
| `new_occupancy` | INTEGER | Nueva ocupación | Opcional | ≥ 0 |
| `occupancy_change` | INTEGER | Cambio de ocupación | Opcional | Entero |
| `parking_status` | VARCHAR | Estado del parking | Opcional | LIBRE/DENSO/COMPLETO |
| `processed_at` | TIMESTAMP | Fecha de procesamiento | DEFAULT NOW() | Auto |

#### Índices

```sql
CREATE INDEX idx_camera_logs_access_id ON camera_logs(access_id);
CREATE INDEX idx_camera_logs_parking_id ON camera_logs(parking_id);
CREATE INDEX idx_camera_logs_processed_at ON camera_logs(processed_at);
CREATE INDEX idx_camera_logs_status ON camera_logs(status);
CREATE INDEX idx_camera_logs_camera_ip ON camera_logs(camera_ip);
```

### 8. Tabla: `users`

Almacena los usuarios del sistema.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `email` | VARCHAR | Email del usuario | UNIQUE, NOT NULL | Email válido |
| `password_hash` | VARCHAR | Hash de la contraseña | NOT NULL | Hash bcrypt |
| `name` | VARCHAR | Nombre del usuario | NOT NULL | Texto |
| `role` | VARCHAR | Rol del usuario | DEFAULT 'user' | user/admin/superadmin |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT NOW() | Auto |
| `updated_at` | TIMESTAMP | Fecha de actualización | DEFAULT NOW() | Auto |

#### Índices

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### 9. Tabla: `user_parkings`

Almacena la asignación de parkings a usuarios.

```sql
CREATE TABLE user_parkings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parking_id INTEGER NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    UNIQUE(user_id, parking_id)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones | Valores |
|-------|------|-------------|---------------|---------|
| `id` | SERIAL | Identificador único | PRIMARY KEY | Auto-increment |
| `user_id` | INTEGER | ID del usuario | FOREIGN KEY, NOT NULL | Referencia a users |
| `parking_id` | INTEGER | ID del parking | FOREIGN KEY, NOT NULL | Referencia a parkings |

#### Índices

```sql
CREATE UNIQUE INDEX idx_user_parkings_unique ON user_parkings(user_id, parking_id);
CREATE INDEX idx_user_parkings_user_id ON user_parkings(user_id);
CREATE INDEX idx_user_parkings_parking_id ON user_parkings(parking_id);
```

## Modelos SQLAlchemy

### Parking

```python
class Parking(Base):
    __tablename__ = 'parkings'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String)
    max_capacity = Column(Integer, nullable=False)
    threshold_dense = Column(Integer, nullable=False)
    threshold_full = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, default=0, nullable=False)
    status = Column(String, default='LIBRE', nullable=False)
    fixed_message_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    
    # Relaciones
    accesses = relationship("Access", back_populates="parking", cascade="all, delete-orphan")
    panels = relationship("Panel", back_populates="parking", cascade="all, delete-orphan")
    occupancy_history = relationship("OccupancyHistory", back_populates="parking", cascade="all, delete-orphan")
    scheduled_messages = relationship("ScheduledMessage", back_populates="parking", cascade="all, delete-orphan")
    camera_logs = relationship("CameraLog", back_populates="parking")
    user_parkings = relationship("UserParking", back_populates="parking", cascade="all, delete-orphan")
```

### Access

```python
class Access(Base):
    __tablename__ = 'accesses'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    ip = Column(String, nullable=False)
    line = Column(Integer, nullable=False)
    name = Column(String)
    last_vehicle_in = Column(Integer, default=0, nullable=False)
    last_vehicle_out = Column(Integer, default=0, nullable=False)
    status = Column(String, default='OFFLINE')
    last_message_received = Column(DateTime(timezone=True))
    
    # Relaciones
    parking = relationship("Parking", back_populates="accesses")
    camera_logs = relationship("CameraLog", back_populates="access")
    
    __table_args__ = (UniqueConstraint('ip', 'line'),)
```

### Panel

```python
class Panel(Base):
    __tablename__ = 'panels'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    status = Column(String, default='OFFLINE')
    last_message = Column(Text)
    last_update = Column(DateTime(timezone=True))
    panel_type_id = Column(Integer, ForeignKey('panel_types.id'))
    
    # Relaciones
    parking = relationship("Parking", back_populates="panels")
    panel_type = relationship("PanelType", back_populates="panels")
```

## Configuración de Base de Datos

### Variables de Entorno

```bash
# config.py
DB_URL = "postgresql://parking_user:parking_pass@localhost:5432/parking_db"
```

### Configuración PostgreSQL

```sql
-- Crear base de datos
CREATE DATABASE parking_db;

-- Crear usuario
CREATE USER parking_user WITH PASSWORD 'parking_pass';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE parking_db TO parking_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parking_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parking_user;
```

### Backup Automático

```bash
#!/bin/bash
# backup_database.sh
pg_dump -h localhost -U parking_user -d parking_db > /backup/parking_db_$(date +%Y%m%d_%H%M%S).sql
```

---

**Documentación actualizada**: Enero 2025  
**Versión del esquema**: v3.0.0  
**Estado**: ✅ Producción estable 