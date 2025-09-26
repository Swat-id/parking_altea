# Sistema de Endpoints Agrupados con Control de Permisos v4.2.0

## Análisis del Sistema Actual

### Endpoints Existentes de Sensores
- `GET /api/sensors/summary` - Resumen básico (sin filtrado por usuario)
- `GET /api/sensors/status/grouped` - Estados agrupados (sin permisos)
- `GET /api/sensors/status/complete` - Estado completo (sin permisos)

### Sistema de Permisos Actual
- **Modelo UserParking**: Relación usuario-parking en tabla intermedia
- **Decoradores**: `@require_auth`, `@require_parking_access`
- **Frontend**: Contexto de autenticación con `hasParkingAccess()`

## Nuevos Endpoints Propuestos

### 1. Endpoints Agrupados por Parking con Permisos

#### **A. Resumen por Parking Específico**
```python
@api_bp.route('/parkings/<int:parking_id>/sensors/summary', methods=['GET'])
@require_parking_access('parking_id')
def get_parking_sensors_summary(parking_id):
    """
    Obtener resumen de sensores de un parking específico agrupado por tipo
    - Solo usuarios con acceso al parking pueden ver los datos
    - Superadmin ve todos los parkings
    """
```

**Respuesta esperada:**
```json
{
  "parking_id": 1,
  "parking_name": "P. Ciutat Esportiva",
  "sensor_types": {
    "PMR": {
      "total": 10,
      "free": 7,
      "busy": 2,
      "error": 1,
      "occupancy_rate": 20.0,
      "health_score": 90.0
    },
    "Electrico": {
      "total": 5,
      "free": 3,
      "busy": 2,
      "error": 0,
      "occupancy_rate": 40.0,
      "health_score": 100.0
    }
  },
  "totals": {
    "total_sensors": 15,
    "total_free": 10,
    "total_busy": 4,
    "total_error": 1,
    "overall_occupancy": 26.7,
    "overall_health": 93.3
  },
  "last_update": "2025-09-26T10:30:00Z"
}
```

#### **B. Resumen Global Filtrado por Usuario**
```python
@api_bp.route('/sensors/summary/user', methods=['GET'])
@require_auth
def get_user_sensors_summary():
    """
    Obtener resumen de sensores de todos los parkings del usuario
    - Filtra automáticamente por parkings asignados al usuario
    - Agrupa por parking y tipo de sensor
    """
```

**Respuesta esperada:**
```json
{
  "user_parkings": [
    {
      "parking_id": 1,
      "parking_name": "P. Ciutat Esportiva",
      "sensor_types": {
        "PMR": {"total": 10, "free": 7, "busy": 2, "error": 1},
        "Electrico": {"total": 5, "free": 3, "busy": 2, "error": 0}
      }
    },
    {
      "parking_id": 2,
      "parking_name": "P. Basseta Centre",
      "sensor_types": {
        "PMR": {"total": 8, "free": 5, "busy": 3, "error": 0}
      }
    }
  ],
  "global_totals": {
    "total_sensors": 23,
    "total_free": 15,
    "total_busy": 7,
    "total_error": 1
  }
}
```

#### **C. Estado Detallado por Parking**
```python
@api_bp.route('/parkings/<int:parking_id>/sensors/detailed', methods=['GET'])
@require_parking_access('parking_id')
def get_parking_sensors_detailed(parking_id):
    """
    Obtener estado detallado de todos los sensores de un parking
    - Incluye información de batería, última actualización, etc.
    - Permite filtrar por tipo de sensor
    """
```

### 2. Endpoints por Tipo de Sensor

#### **A. Resumen por Tipo Específico**
```python
@api_bp.route('/sensors/type/<sensor_type>/summary', methods=['GET'])
@require_auth
def get_sensors_by_type_summary(sensor_type):
    """
    Obtener resumen de sensores de un tipo específico
    - Filtra por parkings del usuario
    - Agrupa por parking
    """
```

#### **B. Estados por Tipo Específico**
```python
@api_bp.route('/sensors/type/<sensor_type>/status', methods=['GET'])
@require_auth
def get_sensors_by_type_status(sensor_type):
    """
    Obtener estado detallado de sensores de un tipo específico
    - Solo parkings del usuario
    - Lista individual de cada sensor
    """
```

### 3. Endpoints de Estadísticas con Permisos

#### **A. Estadísticas Históricas por Parking**
```python
@api_bp.route('/parkings/<int:parking_id>/sensors/statistics', methods=['GET'])
@require_parking_access('parking_id')
def get_parking_sensors_statistics(parking_id):
    """
    Obtener estadísticas históricas de sensores de un parking
    - Parámetros: date_from, date_to, sensor_type
    - Incluye ocupación promedio, picos, tendencias
    """
```

#### **B. Dashboard de Usuario**
```python
@api_bp.route('/dashboard/user/sensors', methods=['GET'])
@require_auth
def get_user_sensors_dashboard():
    """
    Dashboard personalizado con todos los datos de sensores del usuario
    - Resumen por parking
    - Alertas y notificaciones
    - Estadísticas rápidas
    """
```

## Modificaciones a Endpoints Existentes

### 1. Aplicar Filtrado por Usuario

**Endpoints a modificar:**
- `GET /sensors/summary` → Filtrar por parkings del usuario
- `GET /sensors/status/grouped` → Filtrar por parkings del usuario  
- `GET /sensors/status/complete` → Filtrar por parkings del usuario
- `GET /sensors` → Filtrar por parkings del usuario

### 2. Nuevos Parámetros de Filtrado

Todos los endpoints deben soportar:
- `parking_ids[]` - Array de IDs de parkings específicos
- `sensor_types[]` - Array de tipos de sensores
- `status[]` - Array de estados (free, busy, error)
- `include_inactive` - Incluir sensores inactivos

## Control de Acceso Implementado

### 1. Función Auxiliar para Filtrado
```python
def get_user_accessible_parking_ids(user_id: int, user_role: str) -> list:
    """
    Obtener IDs de parkings accesibles para un usuario
    - Superadmin: todos los parkings
    - Usuario regular: solo parkings asignados
    """
    if user_role == 'superadmin':
        return session.query(Parking.id).all()
    
    return session.query(UserParking.parking_id)\
                  .filter(UserParking.user_id == user_id)\
                  .all()
```

### 2. Decorador de Filtrado Automático
```python
def filter_by_user_parkings(f):
    """
    Decorador que automáticamente filtra queries por parkings del usuario
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.user_data.get('user_id')
        user_role = request.user_data.get('role')
        
        parking_ids = get_user_accessible_parking_ids(user_id, user_role)
        request.accessible_parking_ids = parking_ids
        
        return f(*args, **kwargs)
    return decorated_function
```

## Extensión del Sistema de Permisos

### 1. Otros Recursos Filtrados

**Aplicar el mismo filtrado a:**
- **Logs**: Solo logs de parkings asignados
- **Paneles**: Solo paneles de parkings asignados  
- **Programaciones**: Solo schedules de parkings asignados
- **Estadísticas**: Solo stats de parkings asignados
- **Cámaras**: Solo accesos de parkings asignados

### 2. Frontend - Filtrado Automático

**Modificar servicios frontend:**
```javascript
// client/src/services/sensorService.js
export const sensorService = {
  // Automáticamente filtra por parkings del usuario
  getAllSensors: () => api.get('/api/sensors'),
  
  // Nuevo: resumen del usuario
  getUserSummary: () => api.get('/api/sensors/summary/user'),
  
  // Nuevo: por parking específico
  getParkingSummary: (parkingId) => 
    api.get(`/api/parkings/${parkingId}/sensors/summary`),
}
```

## Implementación por Fases

### **Fase 1**: Filtrado Básico
- Modificar endpoints existentes para filtrar por usuario
- Implementar función auxiliar de parkings accesibles
- Testear con usuarios regulares vs superadmin

### **Fase 2**: Nuevos Endpoints
- Implementar endpoints por parking específico
- Implementar endpoints por tipo de sensor
- Agregar parámetros de filtrado avanzado

### **Fase 3**: Dashboard Personalizado
- Endpoint de dashboard de usuario
- Estadísticas históricas con permisos
- Alertas y notificaciones personalizadas

### **Fase 4**: Extensión Completa
- Aplicar filtrado a logs, paneles, schedules
- Actualizar frontend para usar nuevos endpoints
- Documentación y testing completo

## Beneficios del Sistema

### **Seguridad**
- Cada usuario solo ve sus parkings asignados
- Previene acceso no autorizado a datos
- Auditoría completa de accesos

### **Rendimiento**
- Queries más eficientes (menos datos)
- Caché específico por usuario
- Reducción de transferencia de datos

### **Usabilidad**
- Dashboard personalizado por usuario
- Información relevante únicamente
- Mejor experiencia de usuario

### **Escalabilidad**
- Fácil agregar nuevos tipos de sensores
- Sistema de permisos extensible
- Preparado para multi-tenant
