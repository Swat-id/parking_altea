# Integración entre Programaciones y Actualización de Paneles

## Resumen de Implementación

Se ha implementado un sistema completo de integración entre las programaciones de paneles y la actualización automática de ocupación, siguiendo los requerimientos especificados:

### 1. Verificación de Programaciones Activas al Crear

**Archivo modificado:** `src/panel_schedule_service.py`

**Función:** `create_schedule()`

**Comportamiento:**
- Al crear una nueva programación, se verifica si es operativa en el momento actual
- Si la programación está activa y coincide con la fecha, día de la semana y horario actual, se ejecuta automáticamente
- Se actualizan los paneles afectados inmediatamente con el mensaje de la programación

**Lógica de verificación:**
```python
should_execute_now = (
    schedule.start_date <= current_time <= schedule.end_date and
    getattr(schedule, current_weekday_field, False) and
    schedule.start_time <= current_time_str <= schedule.end_time
)
```

### 2. Bloqueo de Actualización de Ocupación con Programaciones Activas

**Archivo modificado:** `src/panel_communication.py`

**Función:** `update_parking_panels()`

**Comportamiento:**
- Antes de actualizar los paneles con el estado de ocupación, se verifica si hay programaciones activas
- Si hay programaciones activas, se bloquea la actualización y se retorna `"SCHEDULE_ACTIVE"`
- Si no hay programaciones activas, se procede con la actualización normal del estado del parking

**Lógica de verificación:**
```python
active_schedules = schedule_service.get_active_schedules_for_parking(parking_id)
if active_schedules:
    logger.info(f"Active schedules found for parking {parking_id}, skipping panel update for occupancy change")
    return "SCHEDULE_ACTIVE"
```

### 3. Restauración Automática del Estado al Finalizar Programaciones

**Archivo modificado:** `src/schedule_monitor_service.py`

**Función:** `check_schedule_endings()`

**Comportamiento:**
- El monitor verifica periódicamente las programaciones que han terminado
- Cuando una programación termina, automáticamente restaura el estado normal del parking en los paneles
- Se envía el mensaje correspondiente al estado actual (LLIURE, DENS, COMPLET)

**Lógica de detección:**
```python
def _schedule_just_ended(self, schedule_data, current_time, current_time_str, current_weekday_field):
    # Verificar si el horario acaba de terminar (hace menos de 1 minuto)
    end_hour, end_minute = map(int, end_time.split(':'))
    today_end = current_time.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    time_diff = current_time - today_end
    return 0 <= time_diff.total_seconds() <= 60
```

## Flujo Completo del Sistema

### 1. Creación de Programación
```
Usuario crea programación → Verificar si es operativa ahora → 
Si es operativa: Ejecutar automáticamente y actualizar paneles
Si no es operativa: Programar para ejecución futura
```

### 2. Actualización de Ocupación (Mensajes de Cámaras)
```
Mensaje de cámara → Actualizar ocupación en BD → 
Verificar programaciones activas → 
Si hay programaciones activas: NO actualizar paneles
Si no hay programaciones activas: Actualizar paneles con estado
```

### 3. Finalización de Programaciones
```
Monitor detecta programación terminada → 
Restaurar estado normal del parking → 
Actualizar paneles con estado actual (LLIURE/DENS/COMPLET)
```

## Archivos Modificados

### `src/panel_schedule_service.py`
- **Función `create_schedule()`**: Agregada verificación de ejecución automática
- **Función `get_active_schedules_for_parking()`**: Obtiene programaciones activas para un parking

### `src/panel_communication.py`
- **Función `update_parking_panels()`**: Agregada verificación de programaciones activas antes de actualizar

### `src/schedule_monitor_service.py`
- **Función `_monitor_loop()`**: Agregada llamada a `check_schedule_endings()`
- **Función `check_schedule_endings()`**: Detecta y finaliza programaciones terminadas
- **Función `_schedule_just_ended()`**: Verifica si una programación acaba de terminar

## Logs y Monitoreo

El sistema genera logs detallados para cada operación:

- **Creación automática**: `"Programación {id} ejecutada automáticamente: {panels_affected} paneles afectados"`
- **Bloqueo de actualización**: `"Active schedules found for parking {id}, skipping panel update for occupancy change"`
- **Finalización**: `"Programación {id} finalizada exitosamente: {panels_affected} paneles actualizados"`

## Configuración del Monitor

El monitor de programaciones se ejecuta con las siguientes características:

- **Intervalo de verificación**: 60 segundos (configurable)
- **Detección de finalización**: Dentro de 1 minuto después del horario de fin
- **Prevención de duplicados**: Cache de ejecuciones para evitar duplicados
- **Limpieza automática**: Elimina ejecuciones antiguas (más de 1 hora)

## Pruebas

Se ha creado un script de prueba (`test/test_schedule_panel_integration.py`) que verifica:

1. Verificación de programaciones activas
2. Creación y ejecución automática de programaciones
3. Bloqueo de actualización de ocupación con programaciones activas
4. Finalización automática y restauración de estado
5. Funcionamiento del monitor de programaciones

## Estado del Sistema

El sistema está completamente implementado y funcional, cumpliendo todos los requerimientos especificados:

✅ **Al crear una programación**: Se verifica si es operativa y se ejecuta automáticamente si corresponde

✅ **Tras llegada de mensajes de cámaras**: Se verifica programaciones activas y se bloquea la actualización de paneles si las hay

✅ **Tras finalizar horarios**: Se restauran automáticamente los paneles con el estado del parking

El sistema está listo para producción y maneja correctamente todos los casos de uso especificados. 