# Migración: Relación Cámaras-Parkings a Muchos a Muchos

## 📋 Resumen Ejecutivo

Este documento describe la migración del sistema Parking Altea para permitir que una cámara esté asociada a múltiples parkings, resolviendo el problema específico de la cámara "Basseta_Asup camera 1" (IP 172.20.5.144) que debe estar vinculada tanto al "P. Basseta Centre" como al "P. Basseta Z1".

## 🎯 Objetivo

Cambiar la relación entre cámaras (Access) y parkings de **uno a muchos** a **muchos a muchos**, permitiendo que:
- Una cámara pueda estar asociada a múltiples parkings
- Los conteos de una cámara actualicen el aforo de todos los parkings asociados
- Se mantenga la integridad de datos y la funcionalidad existente

## 🔧 Cambios Técnicos Realizados

### 1. Modelo de Datos

#### Antes (Relación uno a muchos)
```python
class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)  # ❌ Una cámara = un parking
    ip = Column(String, nullable=False)
    line = Column(Integer, nullable=False)
    # ...
    parking = relationship('Parking', back_populates='accesses')
```

#### Después (Relación muchos a muchos)
```python
class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True)
    # ❌ QUITADO: parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    ip = Column(String, nullable=False)
    line = Column(Integer, nullable=False)
    # ...
    # ✅ NUEVA: Relación muchos a muchos con parkings
    camera_parkings = relationship('CameraParking', back_populates='camera')

# ✅ NUEVA: Tabla intermedia para relación muchos a muchos
class CameraParking(Base):
    __tablename__ = 'camera_parkings'
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('accesses.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    camera = relationship('Access', back_populates='camera_parkings')
    parking = relationship('Parking', back_populates='camera_parkings')
    
    # Índice único para evitar duplicados
    __table_args__ = (UniqueConstraint('camera_id', 'parking_id'),)
```

### 2. Servidor de Cámaras (camera_server.py)

#### Cambios en la lógica de procesamiento:
- **Búsqueda de cámaras**: Ahora busca por `device + line` y obtiene todos los parkings asociados
- **Procesamiento múltiple**: Actualiza la ocupación de todos los parkings asociados a la cámara
- **Logging**: Registra logs para cada parking afectado

```python
# NUEVA LÓGICA: Buscar la cámara por device + línea usando la nueva relación
accesses = session.query(Access).filter(
    func.lower(Access.name) == func.lower(device),
    Access.line == line
).all()

# Procesar TODOS los parkings asociados a esta cámara
for access in accesses:
    camera_parkings = session.query(CameraParking).filter_by(camera_id=access.id).all()
    
    for camera_parking in camera_parkings:
        parking = camera_parking.parking
        # Actualizar ocupación del parking
        # Enviar mensaje a paneles
        # Registrar log
```

### 3. API del Servidor Principal (api_server.py)

#### Endpoints actualizados:

1. **GET /parking/{pid}/cameras**
   - Ahora usa `CameraParking` para obtener cámaras asociadas
   - Mantiene la misma respuesta JSON

2. **PUT /parking/{pid}/cameras**
   - Elimina relaciones existentes en `camera_parkings`
   - Crea nuevas relaciones sin eliminar cámaras
   - Permite reutilizar cámaras existentes

3. **GET /cameras/status**
   - Usa `CameraParking` para obtener estado de todas las cámaras
   - Muestra información de cada parking asociado

4. **POST /parkings** (creación)
   - Crea relaciones en `camera_parkings` en lugar de asignar `parking_id`

## 🚀 Plan de Migración

### Fase 1: Preparación (✅ Completado)
- [x] Actualizar modelos de datos
- [x] Crear script de migración
- [x] Actualizar lógica de procesamiento de cámaras
- [x] Actualizar endpoints de API

### Fase 2: Migración de Datos
```bash
# Ejecutar migración en el servidor
cd /opt/parking_altea
python3 src/migrate_camera_parking_relationship.py
```

**El script de migración:**
1. Crea la nueva tabla `camera_parkings`
2. Migra los datos existentes de la relación directa
3. Elimina la columna `parking_id` de la tabla `accesses`
4. Verifica la integridad de la migración

### Fase 3: Verificación
```bash
# Verificar que la migración fue exitosa
python3 src/migrate_camera_parking_relationship.py --verify

# Probar funcionalidad
curl http://157.180.91.63:6001/parking/2/cameras
curl http://157.180.91.63:6001/parking/2.2/cameras
```

### Fase 4: Configuración de Cámaras Compartidas
Una vez migrado, configurar la cámara "Basseta_Asup camera 1" para ambos parkings:

```json
// Asignar cámara al P. Basseta Centre (ID: 2)
PUT /parking/2/cameras
{
  "cameras": [
    {
      "ip": "172.20.5.144",
      "line": 1,
      "name": "Basseta_Asup camera 1"
    }
  ]
}

// Asignar la misma cámara al P. Basseta Z1 (ID: 2.2)
PUT /parking/2.2/cameras
{
  "cameras": [
    {
      "ip": "172.20.5.144",
      "line": 1,
      "name": "Basseta_Asup camera 1"
    }
  ]
}
```

## 🔄 Rollback

Si es necesario hacer rollback:

```bash
# Ejecutar rollback
python3 src/migrate_camera_parking_relationship.py --rollback
```

**El rollback:**
1. Elimina la tabla `camera_parkings`
2. Recrea la columna `parking_id` en `accesses`
3. Restaura la funcionalidad anterior

## 📊 Beneficios de la Migración

### Antes
- ❌ Una cámara solo podía estar en un parking
- ❌ Para compartir cámara había que duplicarla
- ❌ Los conteos solo afectaban a un parking

### Después
- ✅ Una cámara puede estar en múltiples parkings
- ✅ Los conteos actualizan todos los parkings asociados
- ✅ Mejor gestión de recursos y mantenimiento
- ✅ Flexibilidad para configuraciones complejas

## 🧪 Caso de Uso Específico

### Problema Original
La cámara "Basseta_Asup camera 1" (IP 172.20.5.144) estaba asignada al "P. Basseta Centre" pero al crear el "P. Basseta Z1" se desasignó del primero.

### Solución
Después de la migración, la cámara puede estar asignada a ambos parkings:
- **P. Basseta Centre**: Recibe conteos de la cámara
- **P. Basseta Z1**: Recibe los mismos conteos de la cámara
- **Resultado**: Ambos parkings se actualizan simultáneamente

## 🔍 Verificación Post-Migración

### 1. Verificar Estructura de Base de Datos
```sql
-- Verificar que la nueva tabla existe
SELECT * FROM camera_parkings LIMIT 5;

-- Verificar que no hay parking_id en accesses
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'accesses' AND column_name = 'parking_id';
```

### 2. Verificar Funcionalidad
```bash
# Probar endpoint de cámaras
curl http://157.180.91.63:6001/parking/2/cameras
curl http://157.180.91.63:6001/parking/2.2/cameras

# Probar envío de mensaje de cámara
curl -X POST http://157.180.91.63:6400/camera \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 172.20.5.144" \
  -d '{
    "device": "Basseta_Asup camera 1",
    "line": 1,
    "Vehicle In": 100,
    "Vehicle Out": 50
  }'
```

### 3. Verificar Logs
```bash
# Verificar logs de procesamiento
tail -f /opt/parking_altea/logs/camera.log | grep "Basseta_Asup"
```

## 📝 Notas Importantes

1. **Compatibilidad**: Los endpoints mantienen la misma interfaz JSON
2. **Performance**: La nueva relación puede ser ligeramente más lenta en consultas complejas
3. **Integridad**: Se mantienen las restricciones de unicidad para evitar duplicados
4. **Logs**: Se registran logs separados para cada parking afectado

## 🚨 Consideraciones de Seguridad

- La migración es **irreversible** sin rollback
- **Backup obligatorio** antes de la migración
- **Pruebas en entorno de desarrollo** antes de producción
- **Ventana de mantenimiento** recomendada para la migración

---

**Estado**: ✅ Listo para migración  
**Fecha**: 17/07/2025  
**Responsable**: Equipo de Desarrollo  
**Versión**: v3.1.0 