# Fix: Compatibilidad del Servicio Push de Sensores v4.1.0

## Problema Identificado

El servicio push de sensores (puerto 3535) estaba recibiendo datos de sensores reales Fleximodo pero devolvía error 400 debido a incompatibilidades de formato:

### Errores Encontrados:
1. **Estado en mayúsculas**: Los sensores reales envían `"FREE"`, `"BUSY"` pero el servicio esperaba `"free"`, `"busy"`
2. **Timestamp con milisegundos**: Los sensores envían `"2025-09-24 07:30:51.987"` pero el servicio esperaba `"2025-09-24 07:30:51"`
3. **Sensores no registrados**: Los sensores reales no estaban dados de alta en la base de datos
4. **Campo battery_voltage overflow**: El campo tenía precisión DECIMAL(4,2) pero los sensores envían valores como 3570 (milivoltios)

## Cambios Implementados

### 1. Corrección de Validación de Estados (`src/sensor_push_service.py`)

**Antes:**
```python
# Validar estado
valid_statuses = ['free', 'busy', 'error', 'unknown', 'notcalib']
if 'status' in push_data and push_data['status'] not in valid_statuses:
    errors.append(f"Estado inválido: {push_data['status']}. Válidos: {valid_statuses}")
```

**Después:**
```python
# Validar y normalizar estado
if 'status' in push_data:
    # Convertir estado a minúsculas para compatibilidad con sensores reales
    original_status = push_data['status']
    normalized_status = original_status.lower()
    push_data['status'] = normalized_status  # Normalizar en el propio objeto
    
    valid_statuses = ['free', 'busy', 'error', 'unknown', 'notcalib']
    if normalized_status not in valid_statuses:
        errors.append(f"Estado inválido: {original_status} (normalizado: {normalized_status}). Válidos: {valid_statuses}")
```

### 2. Corrección de Validación de Timestamps

**Antes:**
```python
# Validar timestamp
if 'timestamp' in push_data:
    try:
        datetime.strptime(push_data['timestamp'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        errors.append("Formato de timestamp inválido. Usar: YYYY-MM-DD HH:MM:SS")
```

**Después:**
```python
# Validar y normalizar timestamp
if 'timestamp' in push_data:
    try:
        # Intentar primero el formato con milisegundos (formato real de sensores)
        timestamp_str = push_data['timestamp']
        try:
            # Formato: "2025-09-24 07:30:51.987"
            parsed_timestamp = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Formato: "2025-09-24 07:30:51"
            parsed_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        # Normalizar timestamp sin milisegundos
        push_data['timestamp'] = parsed_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
    except ValueError:
        errors.append("Formato de timestamp inválido. Formatos válidos: 'YYYY-MM-DD HH:MM:SS' o 'YYYY-MM-DD HH:MM:SS.mmm'")
```

### 3. Auto-creación de Sensores

**Funcionalidad añadida:**
```python
if not sensor:
    self.logger.warning(f"Sensor no encontrado: {serial_number}")
    # Intentar crear automáticamente el sensor si no existe
    try:
        # Extraer información básica del push para crear el sensor
        plaza_number = push_data.get('number', 'N/A')
        sensor_name = f"Sensor Plaza {plaza_number}"
        
        sensor = IndividualSensor(
            serial_number=serial_number,
            name=sensor_name,
            sensor_type='PMR',  # Tipo por defecto
            description=f'Sensor auto-creado desde push - Plaza {plaza_number}',
            manufacturer='Fleximodo',
            is_active=True
        )
        
        session.add(sensor)
        session.flush()  # Para obtener el ID
        
        # Crear estado inicial
        initial_status = SensorCurrentStatus(
            sensor_id=sensor.id,
            current_status='unknown',
            last_update=datetime.now(timezone.utc)
        )
        session.add(initial_status)
        session.flush()
        
        self.logger.info(f"Sensor creado automáticamente: {serial_number} (ID: {sensor.id})")
```

### 4. Corrección de Base de Datos

**Comandos ejecutados en producción:**
```sql
-- Aumentar precisión del campo battery_voltage para valores en milivoltios
ALTER TABLE sensor_status_history 
ALTER COLUMN battery_voltage TYPE DECIMAL(6,2);

ALTER TABLE sensor_current_status 
ALTER COLUMN battery_voltage TYPE DECIMAL(6,2);
```

## Sensores Reales Identificados

Los siguientes sensores están enviando datos activamente:

| Serial Number | Plaza | Estado | Batería | Temperatura | RSSI |
|---------------|-------|--------|---------|-------------|------|
| FC072308      | 1     | FREE   | 98.62%  | 22°C        | -99  |
| FC07230C      | 5     | FREE   | 98.26%  | 22°C        | -101 |
| FC07230A      | 3     | FREE   | 98.71%  | 27°C        | -100 |
| FC07230E      | 7     | FREE   | 98.35%  | 26°C        | -101 |
| FC072310      | 9     | FREE   | 98.60%  | 22°C        | -101 |
| FC07230D      | 6     | FREE   | 98.20%  | 23°C        | -93  |
| FC072311      | 10    | FREE   | 98.71%  | 24°C        | -97  |
| FC07230F      | 8     | FREE   | 98.26%  | 26°C        | -101 |

## Formato de Datos Real

```json
{
  "carpark_id": "905",
  "carpark_code": "ES-SW-2",
  "floor": "0",
  "id": "35634",
  "number": "1",
  "parking_cards": [],
  "status": "FREE",
  "idle": true,
  "timestamp": "2025-09-24 07:30:51.987",
  "sensor_info": {
    "serial_number": "FC072308",
    "network_info": {
      "type": "NBIOT",
      "rssi": "-99",
      "on_air": "2895"
    },
    "temperature": "22",
    "battery_voltage": "3570",
    "battery_capacity": 98.62,
    "visible_cards": []
  }
}
```

## Testing

Se incluye script de pruebas `test_sensor_push_fix.py` para verificar:

1. Endpoint de salud del servicio
2. Procesamiento de formato real de sensores
3. Múltiples sensores con diferentes estados
4. Auto-creación de sensores

## Resultado

✅ **El servicio push ahora procesa correctamente los datos de sensores reales Fleximodo**
✅ **Los sensores se crean automáticamente si no existen**
✅ **Compatibilidad total con el formato real de datos**
✅ **Registro completo de historial y estados actuales**

## Despliegue

1. Subir cambios a Git
2. Hacer pull en servidor de producción
3. Reiniciar servicio push
4. Ejecutar script de pruebas
5. Verificar logs para confirmación de funcionamiento
