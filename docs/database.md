# Base de Datos - Esquema y Modelos

## Información General

- **Sistema**: PostgreSQL
- **Host**: localhost
- **Puerto**: 5432
- **Base de Datos**: parking_db
- **Usuario**: parking_user
- **Contraseña**: parking_pass
- **ORM**: SQLAlchemy 2.0

## Esquema de Base de Datos

### Diagrama ER

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    parkings     │     │    accesses     │     │     panels      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────┤ parking_id (FK) │     │ parking_id (FK) │
│ name            │     │ ip              │     │ name            │
│ location        │     │ line            │     │ ip              │
│ max_capacity    │     │ name            │     └─────────────────┘
│ threshold_dense │     │ last_vehicle_in │
│ threshold_full  │     │ last_vehicle_out│
│ current_occupancy│    └─────────────────┘
│ status          │
│ fixed_message_flag│
└─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│occupancy_history│     │scheduled_messages│
├─────────────────┤     ├─────────────────┤
│ parking_id (FK) │     │ parking_id (FK) │
│ timestamp       │     │ start_time      │
│ occupancy       │     │ end_time        │
│ source          │     │ message         │
└─────────────────┘     └─────────────────┘
```

## Tablas y Modelos

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
    fixed_message_flag BOOLEAN DEFAULT FALSE NOT NULL
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | SERIAL | Identificador único | PRIMARY KEY |
| `name` | VARCHAR | Nombre del aparcamiento | UNIQUE, NOT NULL |
| `location` | VARCHAR | Coordenadas GPS | Opcional |
| `max_capacity` | INTEGER | Capacidad máxima de plazas | NOT NULL |
| `threshold_dense` | INTEGER | Umbral para estado DENSO | NOT NULL |
| `threshold_full` | INTEGER | Umbral para estado OCUPADO | NOT NULL |
| `current_occupancy` | INTEGER | Ocupación actual | DEFAULT 0, NOT NULL |
| `status` | VARCHAR | Estado calculado | DEFAULT 'LIBRE', NOT NULL |
| `fixed_message_flag` | BOOLEAN | Flag para mensaje fijo | DEFAULT FALSE, NOT NULL |

#### Estados Posibles

- `LIBRE`: Ocupación < threshold_dense
- `DENSO`: threshold_dense ≤ Ocupación < threshold_full
- `OCUPADO`: Ocupación ≥ threshold_full

### 2. Tabla: `accesses`

Almacena la información de las cámaras de acceso a cada aparcamiento.

```sql
CREATE TABLE accesses (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL,
    ip VARCHAR NOT NULL,
    line INTEGER NOT NULL,
    name VARCHAR,
    last_vehicle_in INTEGER DEFAULT 0 NOT NULL,
    last_vehicle_out INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (parking_id) REFERENCES parkings(id)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | SERIAL | Identificador único | PRIMARY KEY |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL |
| `ip` | VARCHAR | IP de la cámara | NOT NULL |
| `line` | INTEGER | Número de línea de la cámara | NOT NULL |
| `name` | VARCHAR | Nombre descriptivo de la cámara | Opcional |
| `last_vehicle_in` | INTEGER | Último contador de entrada | DEFAULT 0, NOT NULL |
| `last_vehicle_out` | INTEGER | Último contador de salida | DEFAULT 0, NOT NULL |

#### Índices Únicos

```sql
CREATE UNIQUE INDEX idx_access_ip_line ON accesses(ip, line);
```

### 3. Tabla: `panels`

Almacena la información de los paneles electrónicos de cada aparcamiento.

```sql
CREATE TABLE panels (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    ip VARCHAR NOT NULL,
    FOREIGN KEY (parking_id) REFERENCES parkings(id)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | SERIAL | Identificador único | PRIMARY KEY |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL |
| `name` | VARCHAR | Nombre del panel | NOT NULL |
| `ip` | VARCHAR | IP del panel | NOT NULL |

### 4. Tabla: `occupancy_history`

Registra el histórico de ocupación de los aparcamientos.

```sql
CREATE TABLE occupancy_history (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    occupancy INTEGER NOT NULL,
    source VARCHAR NOT NULL,
    FOREIGN KEY (parking_id) REFERENCES parkings(id)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | SERIAL | Identificador único | PRIMARY KEY |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL |
| `timestamp` | TIMESTAMP | Fecha y hora del registro | DEFAULT NOW() |
| `occupancy` | INTEGER | Ocupación registrada | NOT NULL |
| `source` | VARCHAR | Fuente del cambio | NOT NULL |

#### Fuentes Posibles

- `camera`: Cambio por mensaje de cámara
- `manual`: Cambio manual vía API
- `scheduled_adjust`: Ajuste programado automático

### 5. Tabla: `scheduled_messages`

Almacena los mensajes programados para mostrar en los paneles.

```sql
CREATE TABLE scheduled_messages (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (parking_id) REFERENCES parkings(id)
);
```

#### Campos

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | SERIAL | Identificador único | PRIMARY KEY |
| `parking_id` | INTEGER | ID del aparcamiento | FOREIGN KEY, NOT NULL |
| `start_time` | TIMESTAMP | Fecha/hora de inicio | NOT NULL |
| `end_time` | TIMESTAMP | Fecha/hora de fin | NOT NULL |
| `message` | TEXT | Mensaje a mostrar | NOT NULL |

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
    
    # Relaciones
    accesses = relationship('Access', back_populates='parking')
    panels = relationship('Panel', back_populates='parking')
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
    
    # Relaciones
    parking = relationship('Parking', back_populates='accesses')
```

### Panel

```python
class Panel(Base):
    __tablename__ = 'panels'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    
    # Relaciones
    parking = relationship('Parking', back_populates='panels')
```

### OccupancyHistory

```python
class OccupancyHistory(Base):
    __tablename__ = 'occupancy_history'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    occupancy = Column(Integer, nullable=False)
    source = Column(String, nullable=False)
```

### ScheduledMessage

```python
class ScheduledMessage(Base):
    __tablename__ = 'scheduled_messages'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    message = Column(Text, nullable=False)
```

## Consultas Frecuentes

### Obtener Aparcamiento con Relaciones

```sql
SELECT p.*, 
       COUNT(DISTINCT a.id) as num_cameras,
       COUNT(DISTINCT pan.id) as num_panels
FROM parkings p
LEFT JOIN accesses a ON p.id = a.parking_id
LEFT JOIN panels pan ON p.id = pan.parking_id
GROUP BY p.id;
```

### Histórico de Ocupación (Últimos 7 días)

```sql
SELECT parking_id, 
       DATE(timestamp) as date,
       AVG(occupancy) as avg_occupancy,
       MAX(occupancy) as max_occupancy,
       MIN(occupancy) as min_occupancy
FROM occupancy_history
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY parking_id, DATE(timestamp)
ORDER BY parking_id, date;
```

### Mensajes Programados Activos

```sql
SELECT p.name as parking_name,
       sm.message,
       sm.start_time,
       sm.end_time
FROM scheduled_messages sm
JOIN parkings p ON sm.parking_id = p.id
WHERE NOW() BETWEEN sm.start_time AND sm.end_time;
```

## Mantenimiento de Base de Datos

### Limpieza de Histórico

```sql
-- Eliminar registros de ocupación más antiguos de 15 días
DELETE FROM occupancy_history 
WHERE timestamp < NOW() - INTERVAL '15 days';
```

### Backup Automático

```bash
# Script de backup diario
pg_dump parking_db > /backup/parking_$(date +%Y%m%d).sql
```

### Índices Recomendados

```sql
-- Índice para búsquedas por IP y línea
CREATE INDEX idx_access_ip_line ON accesses(ip, line);

-- Índice para histórico por fecha
CREATE INDEX idx_occupancy_timestamp ON occupancy_history(timestamp);

-- Índice para mensajes programados por fecha
CREATE INDEX idx_scheduled_start_end ON scheduled_messages(start_time, end_time);
```

## Configuración de PostgreSQL

### postgresql.conf

```ini
# Configuración de memoria
shared_buffers = 256MB
effective_cache_size = 1GB

# Configuración de conexiones
max_connections = 100

# Configuración de logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
```

### pg_hba.conf

```ini
# Conexiones locales
local   parking_db    parking_user    md5
host    parking_db    parking_user    127.0.0.1/32    md5
host    parking_db    parking_user    ::1/128         md5
``` 