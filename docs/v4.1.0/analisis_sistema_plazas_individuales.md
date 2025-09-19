# Análisis: Sistema de Gestión de Plazas Individuales PMR

## Descripción General

El sistema de plazas individuales permitirá gestionar sensores de parking individuales con diferentes tipos (PMR, Eléctrico, Caravanas, Emergencias, Policía, Otros), vinculados opcionalmente a parkings existentes, con capacidad de agrupación y consulta de estados.

## Análisis del Sistema Actual

### Estructura Existente de Parkings

**Modelo Parking** (`src/models.py`, líneas 40-61):
- `max_capacity`: Capacidad total del parking
- `current_occupancy`: Ocupación actual
- `status`: Estado global ('LIBRE', 'DENSO', 'COMPLETO')
- Relaciones con paneles y cámaras

**Sistema de Ocupación Actual**:
- Basado en contadores globales por parking
- Actualización mediante cámaras de acceso (`Access` model)
- Sin granularidad individual por plaza

## Diseño del Nuevo Sistema

### 1. Nuevos Modelos de Base de Datos

#### Tabla `individual_sensors`

```sql
CREATE TABLE individual_sensors (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    sensor_type VARCHAR(20) DEFAULT 'PMR' NOT NULL,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE SET NULL,
    description TEXT,
    location_coordinates POINT, -- Coordenadas GPS
    manufacturer VARCHAR(50) DEFAULT 'Fleximodo' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para optimización
CREATE INDEX idx_individual_sensors_parking_id ON individual_sensors(parking_id);
CREATE INDEX idx_individual_sensors_type ON individual_sensors(sensor_type);
CREATE INDEX idx_individual_sensors_active ON individual_sensors(is_active);
CREATE INDEX idx_individual_sensors_serial ON individual_sensors(serial_number);
```

#### Tabla `sensor_status_history`

```sql
CREATE TABLE sensor_status_history (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES individual_sensors(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL, -- 'free', 'busy', 'error', 'unknown'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER, -- Porcentaje 0-100
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER, -- dBm
    radar_only BOOLEAN DEFAULT FALSE,
    raw_data JSONB -- Datos completos del sensor
);

-- Índices para consultas frecuentes
CREATE INDEX idx_sensor_status_sensor_id ON sensor_status_history(sensor_id);
CREATE INDEX idx_sensor_status_timestamp ON sensor_status_history(timestamp DESC);
CREATE INDEX idx_sensor_status_current ON sensor_status_history(sensor_id, timestamp DESC);
```

#### Tabla `sensor_current_status`

```sql
CREATE TABLE sensor_current_status (
    sensor_id INTEGER PRIMARY KEY REFERENCES individual_sensors(id) ON DELETE CASCADE,
    current_status VARCHAR(20) NOT NULL,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER,
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    consecutive_errors INTEGER DEFAULT 0,
    last_successful_ping TIMESTAMP WITH TIME ZONE
);
```

#### Tabla `parking_sensor_summary`

```sql
CREATE TABLE parking_sensor_summary (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
    sensor_type VARCHAR(20) NOT NULL,
    total_sensors INTEGER DEFAULT 0,
    free_sensors INTEGER DEFAULT 0,
    busy_sensors INTEGER DEFAULT 0,
    error_sensors INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parking_id, sensor_type)
);

-- Índice para consultas por parking
CREATE INDEX idx_parking_sensor_summary_parking ON parking_sensor_summary(parking_id);
```

### 2. Nuevos Endpoints de API

#### Gestión de Sensores Individuales

```python
# CRUD para sensores individuales
POST   /api/individual-sensors          # Crear sensor
GET    /api/individual-sensors          # Listar sensores (con filtros)
GET    /api/individual-sensors/{id}     # Obtener sensor específico
PUT    /api/individual-sensors/{id}     # Actualizar sensor
DELETE /api/individual-sensors/{id}     # Eliminar sensor

# Consultas de estado
GET    /api/individual-sensors/{id}/status        # Estado actual del sensor
GET    /api/individual-sensors/{id}/history       # Historial de estados
GET    /api/individual-sensors/status/summary     # Resumen global de estados
```

#### Consultas por Parking

```python
# Estados agrupados por parking
GET    /api/parkings/{id}/sensors                 # Sensores del parking
GET    /api/parkings/{id}/sensors/summary         # Resumen agrupado por tipo
GET    /api/parkings/{id}/sensors/status          # Estado actual de todos los sensores

# Estadísticas
GET    /api/parkings/{id}/sensors/statistics      # Estadísticas históricas
```

### 3. Servicio de Recepción de Push (Puerto 3535)

#### Estructura del Servicio

```python
# Archivo: src/sensor_push_service.py
from flask import Flask, request, jsonify
import logging
from datetime import datetime
from models import IndividualSensor, SensorStatusHistory, SensorCurrentStatus

app = Flask(__name__)

@app.route('/push', methods=['POST'])
def receive_sensor_push():
    """
    Endpoint para recibir push de cambios de estado de sensores
    
    Estructura esperada del push:
    {
        "carpark_id": 123,
        "carpark_code": "PARKING_A",
        "floor": "0",
        "id": 456,
        "number": "A01",
        "status": "busy",
        "idle": false,
        "timestamp": "2025-09-19 10:30:00",
        "parking_cards": ["1A2B3C4D"],
        "floor_stats": {
            "slot_count": 50,
            "free_count": 25,
            "busy_count": 23,
            "notcalib_count": 2
        },
        "sensor_info": {
            "serial_number": "FLX001234",
            "network_info": {...},
            "temperature": 23.5,
            "battery_voltage": 3.2,
            "battery_capacity": 85,
            "visible_cards": ["1A2B3C4D"],
            "radar_only": false
        }
    }
    """
```

#### Lógica de Procesamiento

1. **Validación del Push**:
   - Verificar formato del mensaje
   - Validar serial_number contra base de datos
   - Comprobar timestamp para evitar mensajes obsoletos

2. **Actualización de Estado**:
   - Insertar registro en `sensor_status_history`
   - Actualizar `sensor_current_status`
   - Actualizar resumen en `parking_sensor_summary`

3. **Notificaciones**:
   - Generar alertas para sensores con errores
   - Actualizar paneles si es necesario

### 4. Frontend - Nueva Página de Gestión

#### Componente Principal: `IndividualSensors.jsx`

```jsx
// Estructura del componente
const IndividualSensors = () => {
  const [sensors, setSensors] = useState([])
  const [selectedSensor, setSelectedSensor] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [filterType, setFilterType] = useState('all')
  const [filterParking, setFilterParking] = useState('all')

  // Estados para formularios
  const [createForm, setCreateForm] = useState({
    serial_number: '',
    sensor_type: 'PMR',
    parking_id: '',
    description: '',
    location_coordinates: '',
    manufacturer: 'Fleximodo'
  })

  // Funciones CRUD
  const handleCreateSensor = async () => { /* ... */ }
  const handleUpdateSensor = async () => { /* ... */ }
  const handleDeleteSensor = async () => { /* ... */ }

  // Renderizado de tabla con filtros y acciones
}
```

#### Funcionalidades del Frontend

1. **Lista de Sensores**:
   - Tabla con paginación
   - Filtros por tipo, parking, estado
   - Búsqueda por serial number
   - Estados visuales (libre, ocupado, error)

2. **Formularios**:
   - Crear sensor con validaciones
   - Editar información del sensor
   - Vinculación con parkings existentes

3. **Dashboard de Estados**:
   - Resumen por tipo de sensor
   - Estados agrupados por parking
   - Gráficos de ocupación en tiempo real

4. **Historial y Estadísticas**:
   - Gráficos de evolución temporal
   - Alertas de sensores con problemas
   - Reportes de disponibilidad

### 5. Comandos de Base de Datos

#### Comando de Creación de Tablas

```bash
# Archivo: scripts/create_individual_sensors_tables.sql

-- Crear tablas del sistema de sensores individuales
\c parking_db;

-- 1. Tabla principal de sensores
CREATE TABLE IF NOT EXISTS individual_sensors (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    sensor_type VARCHAR(20) DEFAULT 'PMR' NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    parking_id INTEGER REFERENCES parkings(id) ON DELETE SET NULL,
    description TEXT,
    location_coordinates POINT,
    manufacturer VARCHAR(50) DEFAULT 'Fleximodo' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- [Resto de tablas...]

-- Insertar datos de ejemplo
INSERT INTO individual_sensors (serial_number, sensor_type, description) VALUES
('FLX001001', 'PMR', 'Sensor PMR entrada principal'),
('FLX001002', 'Electrico', 'Plaza eléctrica zona A'),
('FLX001003', 'PMR', 'Sensor PMR zona B');

COMMIT;
```

#### Comando de Migración

```bash
# Archivo: scripts/migrate_to_individual_sensors.py

#!/usr/bin/env python3
"""
Migración para añadir el sistema de sensores individuales
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config

def run_migration():
    engine = create_engine(config.DB_URL)
    
    # Ejecutar scripts SQL
    with engine.connect() as conn:
        with open('create_individual_sensors_tables.sql', 'r') as f:
            conn.execute(text(f.read()))
    
    print("✅ Migración completada: Sistema de sensores individuales")

if __name__ == "__main__":
    run_migration()
```

### 6. Integración con Sistema Existente

#### Modificaciones en Modelos Existentes

```python
# Archivo: src/models.py - Nuevos modelos

class IndividualSensor(Base):
    __tablename__ = 'individual_sensors'
    
    id = Column(Integer, primary_key=True)
    serial_number = Column(String(100), unique=True, nullable=False)
    sensor_type = Column(String(20), default='PMR', nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=True)
    description = Column(Text)
    location_coordinates = Column(String)  # Almacenar como string "lat,lng"
    manufacturer = Column(String(50), default='Fleximodo', nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    parking = relationship('Parking', backref='individual_sensors')
    status_history = relationship('SensorStatusHistory', back_populates='sensor')
    current_status = relationship('SensorCurrentStatus', uselist=False, back_populates='sensor')

class SensorStatusHistory(Base):
    __tablename__ = 'sensor_status_history'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey('individual_sensors.id'), nullable=False)
    status = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    battery_voltage = Column(Numeric(4,2))
    battery_capacity = Column(Integer)
    temperature = Column(Numeric(5,2))
    network_signal_strength = Column(Integer)
    radar_only = Column(Boolean, default=False)
    raw_data = Column(JSON)
    
    # Relación
    sensor = relationship('IndividualSensor', back_populates='status_history')

class SensorCurrentStatus(Base):
    __tablename__ = 'sensor_current_status'
    
    sensor_id = Column(Integer, ForeignKey('individual_sensors.id'), primary_key=True)
    current_status = Column(String(20), nullable=False)
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    battery_voltage = Column(Numeric(4,2))
    battery_capacity = Column(Integer)
    temperature = Column(Numeric(5,2))
    network_signal_strength = Column(Integer)
    consecutive_errors = Column(Integer, default=0)
    last_successful_ping = Column(DateTime(timezone=True))
    
    # Relación
    sensor = relationship('IndividualSensor', back_populates='current_status')

class ParkingSensorSummary(Base):
    __tablename__ = 'parking_sensor_summary'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    sensor_type = Column(String(20), nullable=False)
    total_sensors = Column(Integer, default=0)
    free_sensors = Column(Integer, default=0)
    busy_sensors = Column(Integer, default=0)
    error_sensors = Column(Integer, default=0)
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación
    parking = relationship('Parking', backref='sensor_summaries')
    
    __table_args__ = (UniqueConstraint('parking_id', 'sensor_type'),)
```

### 7. Servicios y Lógica de Negocio

#### Servicio de Gestión de Sensores

```python
# Archivo: src/individual_sensor_service.py

class IndividualSensorService:
    def __init__(self, session):
        self.session = session
    
    def create_sensor(self, sensor_data):
        """Crear un nuevo sensor individual"""
        # Validaciones
        # Creación del sensor
        # Inicialización del estado
        pass
    
    def update_sensor_status(self, serial_number, status_data):
        """Actualizar estado de sensor desde push"""
        # Buscar sensor por serial
        # Crear registro histórico
        # Actualizar estado actual
        # Actualizar resumen por parking
        pass
    
    def get_parking_sensor_summary(self, parking_id):
        """Obtener resumen de sensores por parking"""
        # Consultar estados agrupados
        # Calcular estadísticas
        pass
    
    def get_sensor_statistics(self, sensor_id, period='24h'):
        """Obtener estadísticas de un sensor"""
        # Consultar historial
        # Calcular métricas
        pass
```

### 8. Autenticación y Autorización

#### Modificaciones en Sistema de Auth

```python
# Archivo: src/auth_decorators.py - Nuevos decoradores

def require_sensor_access(sensor_id_param):
    """Decorador para validar acceso a sensores individuales"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener sensor_id del parámetro
            # Verificar que el usuario tenga acceso al parking del sensor
            # O que sea superadmin
            pass
        return decorated_function
    return decorator
```

#### Endpoints Protegidos

```python
# Archivo: src/api_server.py - Nuevos endpoints

@api_bp.route('/individual-sensors', methods=['GET'])
@require_auth
def list_individual_sensors():
    """Listar sensores según permisos del usuario"""
    pass

@api_bp.route('/individual-sensors/<int:sensor_id>/status', methods=['GET'])
@require_sensor_access('sensor_id')
def get_sensor_status(sensor_id):
    """Obtener estado actual de un sensor"""
    pass

@api_bp.route('/parkings/<int:parking_id>/sensors/summary', methods=['GET'])
@require_parking_access('parking_id')
def get_parking_sensors_summary(parking_id):
    """Obtener resumen de sensores del parking"""
    pass
```

### 9. Testing y Validación

#### Tests Unitarios

```python
# Archivo: tests/test_individual_sensors.py

class TestIndividualSensors(unittest.TestCase):
    def test_create_sensor(self):
        """Test creación de sensor"""
        pass
    
    def test_update_sensor_status(self):
        """Test actualización de estado"""
        pass
    
    def test_parking_summary(self):
        """Test resumen por parking"""
        pass
    
    def test_push_processing(self):
        """Test procesamiento de push"""
        pass
```

#### Tests de Integración

```python
# Archivo: tests/integration/test_sensor_push_service.py

class TestSensorPushService(unittest.TestCase):
    def test_complete_push_flow(self):
        """Test flujo completo de recepción de push"""
        pass
    
    def test_authentication_endpoints(self):
        """Test autenticación en endpoints"""
        pass
```

### 10. Estimación de Esfuerzo

| Componente | Estimación | Descripción |
|------------|------------|-------------|
| **Modelos y Base de Datos** | 8 horas | Creación de tablas, modelos, migraciones |
| **Backend - API Endpoints** | 12 horas | CRUD, consultas, autenticación |
| **Servicio Push (Puerto 3535)** | 6 horas | Servidor Flask, procesamiento |
| **Frontend - Gestión de Sensores** | 16 horas | Componentes, formularios, dashboard |
| **Frontend - Dashboard Estados** | 8 horas | Gráficos, resúmenes, estadísticas |
| **Integración y Testing** | 10 horas | Tests, validaciones, debugging |
| **Documentación y Despliegue** | 4 horas | Docs, scripts de despliegue |
| **Total** | **64 horas** | Aproximadamente 8 días de trabajo |

### 11. Fases de Implementación

#### Fase 1: Base de Datos y Modelos (2 días)
- Crear tablas y modelos
- Scripts de migración
- Tests básicos de modelos

#### Fase 2: Backend y API (3 días)
- Endpoints CRUD
- Servicio de gestión
- Autenticación y autorización

#### Fase 3: Servicio Push (1 día)
- Servidor en puerto 3535
- Procesamiento de mensajes
- Integración con base de datos

#### Fase 4: Frontend Básico (2 días)
- Lista y CRUD de sensores
- Formularios de creación/edición
- Integración con API

#### Fase 5: Dashboard y Estados (1 día)
- Resúmenes por parking
- Estados en tiempo real
- Gráficos básicos

#### Fase 6: Testing y Refinamiento (1 día)
- Tests de integración
- Corrección de bugs
- Optimizaciones

### 12. Riesgos y Consideraciones

1. **Volumen de Datos**: Los sensores pueden generar muchos registros de estado
2. **Rendimiento**: Consultas agrupadas pueden ser costosas
3. **Conectividad**: Manejo de sensores offline o con errores
4. **Escalabilidad**: Diseño debe soportar cientos de sensores
5. **Sincronización**: Mantener consistencia entre estados individuales y resúmenes

### 13. Optimizaciones Futuras

1. **Cache**: Redis para consultas frecuentes
2. **Agregaciones**: Jobs para pre-calcular estadísticas
3. **Alertas**: Sistema de notificaciones por sensores críticos
4. **Reportes**: Generación de informes automáticos
5. **Integración**: APIs para sistemas externos

---

*Análisis completado para el sistema de gestión de plazas individuales PMR y otros tipos de sensores*
