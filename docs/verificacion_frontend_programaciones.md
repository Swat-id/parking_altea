# Verificación del Comportamiento del Frontend con Programaciones

## 📋 Resumen de la Verificación

Se ha realizado una verificación completa del comportamiento del frontend con el sistema de programaciones para validar que:

1. **Al guardar una programación**: Se ejecuta automáticamente si es operativa en ese momento
2. **Al pulsar el botón "Play"**: Se ejecuta la programación inmediatamente
3. **Intervalo de verificación**: Cada cuánto tiempo se revisa y reenvía el mensaje programado

## 🔍 Análisis del Comportamiento Actual

### 1. **Ejecución Automática al Crear Programaciones**

**Ubicación**: `src/panel_schedule_service.py` - Función `create_schedule()` (líneas 90-140)

**Comportamiento**:
- ✅ Al crear una programación, se verifica si es operativa en el momento actual
- ✅ Si la programación está activa y coincide con fecha, día y horario, se ejecuta automáticamente
- ✅ Se retorna información sobre si se ejecutó automáticamente y cuántos paneles fueron afectados

**Código relevante**:
```python
# Verificar si debe ejecutarse ahora
should_execute_now = (
    schedule.start_date <= current_time <= schedule.end_date and
    getattr(schedule, current_weekday_field, False) and
    schedule.start_time <= current_time_str <= schedule.end_time
)

if should_execute_now:
    logger.info(f"Programación {schedule.id} es operativa ahora, ejecutando automáticamente")
    execution_result = self.execute_schedule(schedule)
```

### 2. **Ejecución Manual con Botón "Play"**

**Ubicación**: 
- Frontend: `client/src/pages/Schedules.jsx` - Función `handleExecute()` (línea 257)
- Backend: `src/api_server.py` - Endpoint `/schedules/<id>/execute` (línea 2412)

**Comportamiento**:
- ✅ El botón "Play" (▶️) ejecuta la programación inmediatamente
- ✅ Se envía una petición POST al endpoint `/api/schedules/{id}/execute`
- ✅ Se ejecuta la programación sin importar si está en su horario programado
- ✅ Se retorna el número de paneles afectados

**Código del frontend**:
```javascript
const handleExecute = (id) => {
  executeScheduleMutation.mutate(id)
}

const executeScheduleMutation = useMutation(
  (id) => fetch(`${API_BASE_URL}/api/schedules/${id}/execute`, { method: 'POST' }).then(res => res.json()),
  {
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Programación ejecutada exitosamente (${data.panels_affected} paneles afectados)`)
      }
    }
  }
)
```

### 3. **Intervalo de Verificación del Monitor**

**Ubicación**: `src/schedule_monitor_service.py` - Clase `ScheduleMonitorService`

**Configuración**:
- ✅ **Intervalo por defecto**: 60 segundos
- ✅ **Configurable**: Se puede cambiar en el constructor
- ✅ **Verificación automática**: Cada intervalo se revisan todas las programaciones activas

**Comportamiento del monitor**:
```python
class ScheduleMonitorService:
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval  # 60 segundos por defecto
    
    def _monitor_loop(self):
        while self.running:
            # Verificar y ejecutar programaciones activas
            self._check_and_execute_schedules()
            
            # Verificar programaciones que han terminado
            self.check_schedule_endings()
            
            time.sleep(self.check_interval)  # Esperar 60 segundos
```

### 4. **Prevención de Ejecuciones Duplicadas**

**Ubicación**: `src/schedule_monitor_service.py` - Función `_check_and_execute_schedules()`

**Comportamiento**:
- ✅ Se evitan ejecuciones duplicadas en el mismo minuto
- ✅ Se usa un sistema de cache con claves únicas por programación y minuto
- ✅ Se limpian ejecuciones antiguas (más de 1 hora)

**Código relevante**:
```python
# Evitar ejecuciones duplicadas en el mismo minuto
execution_key = f"{schedule_id}_{current_time.strftime('%Y%m%d_%H%M')}"

if execution_key not in self.executed_schedules:
    # Ejecutar la programación
    execution_result = schedule_service.execute_schedule(schedule)
    self.executed_schedules.add(execution_key)
```

## 🧪 Tests de Validación Creados

### Test 1: Creación y Ejecución Automática
- **Archivo**: `test/test_frontend_schedule_execution.py`
- **Función**: `test_schedule_creation_and_execution()`
- **Propósito**: Verificar que al crear una programación se ejecuta automáticamente si es operativa

### Test 2: Ejecución Manual via API
- **Archivo**: `test/test_frontend_schedule_execution.py`
- **Función**: `test_manual_execution_via_api()`
- **Propósito**: Verificar que el botón "Play" ejecuta la programación manualmente

### Test 3: Intervalo de Monitor
- **Archivo**: `test/test_frontend_schedule_execution.py`
- **Función**: `test_schedule_monitor_interval()`
- **Propósito**: Verificar la configuración del intervalo de verificación

### Test 4: Comportamiento de Botones
- **Archivo**: `test/test_frontend_schedule_execution.py`
- **Función**: `test_frontend_button_behavior()`
- **Propósito**: Verificar que los endpoints del frontend están disponibles

## 🔄 Flujo Completo de Programaciones

### Flujo de Creación
```
Frontend → Crear Programación → Backend → Verificar si es operativa → Ejecutar automáticamente → Paneles
```

### Flujo de Ejecución Manual
```
Frontend → Botón Play → API Execute → Backend → Ejecutar programación → Paneles
```

### Flujo de Monitor Automático
```
Monitor (cada 60s) → Verificar programaciones activas → Ejecutar si es operativa → Paneles
```

### Flujo de Finalización
```
Monitor (cada 60s) → Verificar programaciones terminadas → Restaurar estado normal → Paneles
```

## 📊 Estados y Respuestas

### Respuestas de Creación
```json
{
  "success": true,
  "schedule_id": 123,
  "auto_executed": true,
  "panels_affected": 3
}
```

### Respuestas de Ejecución Manual
```json
{
  "success": true,
  "panels_affected": 3
}
```

### Respuestas de Toggle
```json
{
  "success": true,
  "is_active": true
}
```

## ✅ Validación de Funcionalidades

### ✅ Funcionalidades Verificadas

1. **Creación automática**: ✅ Las programaciones se ejecutan automáticamente si son operativas
2. **Botón Play**: ✅ Ejecuta la programación inmediatamente
3. **Botón Toggle**: ✅ Activa/desactiva programaciones
4. **Intervalo de monitor**: ✅ 60 segundos por defecto, configurable
5. **Prevención de duplicados**: ✅ Evita ejecuciones múltiples en el mismo minuto
6. **Restauración automática**: ✅ Al finalizar programaciones, vuelve al estado normal

### ⚠️ Consideraciones Importantes

1. **Intervalo de 60 segundos**: Si se envía un mensaje individual a un panel, el monitor verificará y reenviará el mensaje programado en máximo 60 segundos
2. **Ejecución inmediata**: El botón "Play" ejecuta la programación sin verificar horarios
3. **Prioridad de programaciones**: Las programaciones de mayor prioridad tienen precedencia
4. **Bloqueo de ocupación**: Las actualizaciones de ocupación se bloquean cuando hay programaciones activas

## 🚀 Para Ejecutar los Tests

```bash
# Ejecutar tests de frontend
python test/test_frontend_schedule_execution.py

# Ejecutar tests de integración
python test/test_schedule_occupancy_integration.py

# Ejecutar diagnóstico
python test/diagnose_schedule_occupancy_issue.py
```

## 📝 Notas Técnicas

### Configuración del Monitor
- **Intervalo por defecto**: 60 segundos
- **Configuración**: Se puede cambiar en el constructor de `ScheduleMonitorService`
- **Ejecución**: Se ejecuta en un thread separado como daemon

### Endpoints del Frontend
- `POST /api/schedules` - Crear programación
- `POST /api/schedules/{id}/execute` - Ejecutar programación
- `POST /api/schedules/{id}/toggle` - Activar/desactivar
- `PUT /api/schedules/{id}` - Actualizar programación

### Logs de Ejecución
- Se registran logs detallados de cada ejecución
- Se incluye información de paneles afectados
- Se registran errores y excepciones

El sistema de programaciones del frontend está funcionando correctamente con ejecución automática al crear programaciones, ejecución manual con el botón "Play", y verificación automática cada 60 segundos por el monitor. 