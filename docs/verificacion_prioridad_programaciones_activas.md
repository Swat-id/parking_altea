# Verificación de Prioridad de Programaciones Activas

## Resumen Ejecutivo

Este documento verifica que **cuando existe una programación activa, el mensaje que se muestra en los paneles es efectivamente el de la programación activa**, respetando la prioridad de programaciones sobre los mensajes automáticos de estado del parking.

## Flujo de Prioridad de Programaciones

### 1. Flujo Principal: Actualización desde Cámaras

Cuando llega un mensaje de cámara (`camera_server.py`):

```python
# 1. Se calcula el delta y se actualiza la ocupación
# 2. Se determina el estado del parking (COMPLETO, DENSO, LIBRE)
# 3. Se llama a update_parking_panels()
```

### 2. Verificación de Programaciones Activas

En `update_parking_panels()` (líneas 460-470 de `panel_communication_service.py`):

```python
# VERIFICAR SI HAY PROGRAMACIONES ACTIVAS ANTES DE ACTUALIZAR PANELES
from panel_schedule_service import PanelScheduleService
schedule_service = PanelScheduleService(db_session)
active_schedules = schedule_service.get_active_schedules_for_parking(parking_id)

if active_schedules:
    logger.info(f"Active schedules found for parking {parking_id}, skipping panel update for occupancy change")
    return "SCHEDULE_ACTIVE"  # NO actualizar paneles si hay programación activa
```

**✅ CONFIRMADO**: Si hay programaciones activas, la función retorna `"SCHEDULE_ACTIVE"` y **NO actualiza los paneles** con el estado del parking.

### 3. Flujo de Programaciones Activas

El `ScheduleMonitorService` ejecuta cada 60 segundos:

```python
def _check_and_execute_schedules(self):
    # Obtiene programaciones activas
    # Para cada programación que debe ejecutarse:
    schedule_service.execute_schedule(schedule)
```

### 4. Ejecución de Programaciones

En `execute_schedule()` (líneas 316-365 de `panel_schedule_service.py`):

```python
def execute_schedule(self, schedule: PanelSchedule) -> dict:
    # Obtener paneles del parking
    panels = self.session.query(Panel).filter(
        Panel.parking_id == schedule.parking_id
    ).all()
    
    # Enviar mensaje de la programación a todos los paneles
    for panel in panels:
        result = self.panel_communication_service.send_custom_text(
            panel_ip=panel.ip,
            text=schedule.message,  # ← MENSAJE DE LA PROGRAMACIÓN
            color=schedule.color,
            font_size=2,
            effect=self._get_effect_code(schedule.effect)
        )
```

**✅ CONFIRMADO**: Cuando se ejecuta una programación, se envía `schedule.message` (el mensaje de la programación) a los paneles.

## Verificación de la Lógica

### Caso 1: Con Programación Activa

1. **Cámara envía datos** → `camera_server.py` procesa
2. **Se llama `update_parking_panels()`** → Verifica programaciones activas
3. **Encuentra programación activa** → Retorna `"SCHEDULE_ACTIVE"`
4. **NO se actualizan paneles** → Se mantiene el mensaje de la programación
5. **ScheduleMonitor ejecuta programación** → Envía mensaje de programación a paneles

**Resultado**: Los paneles muestran el mensaje de la programación activa.

### Caso 2: Sin Programación Activa

1. **Cámara envía datos** → `camera_server.py` procesa
2. **Se llama `update_parking_panels()`** → Verifica programaciones activas
3. **NO encuentra programaciones activas** → Continúa con actualización
4. **Convierte estado a mensaje valenciano** → Envía a paneles
5. **Paneles muestran estado del parking**

**Resultado**: Los paneles muestran el estado actual del parking (LLIURE, DENS, COMPLET).

## Código de Verificación

Se ha creado el script `test/verify_schedule_priority.py` que:

1. **Verifica programaciones activas** para cada parking
2. **Simula llamadas a `update_parking_panels()`**
3. **Confirma que retorna `"SCHEDULE_ACTIVE"`** cuando hay programaciones
4. **Verifica la lógica de ejecución** de programaciones

## Confirmación de Funcionamiento

### ✅ Verificaciones Realizadas:

1. **Prioridad de Programaciones**: `update_parking_panels()` retorna `"SCHEDULE_ACTIVE"` cuando hay programaciones activas
2. **No Interferencia**: Los cambios de estado del parking NO sobrescriben programaciones activas
3. **Ejecución Correcta**: `execute_schedule()` envía el mensaje de la programación a los paneles
4. **Monitorización**: `ScheduleMonitorService` ejecuta programaciones cada 60 segundos

### 🔍 Puntos Clave del Código:

**En `panel_communication_service.py` (líneas 460-470):**
```python
if active_schedules:
    logger.info(f"Active schedules found for parking {parking_id}, skipping panel update for occupancy change")
    return "SCHEDULE_ACTIVE"  # NO actualizar paneles si hay programación activa
```

**En `panel_schedule_service.py` (líneas 330-340):**
```python
result = self.panel_communication_service.send_custom_text(
    panel_ip=panel.ip,
    text=schedule.message,  # ← Mensaje de la programación
    color=schedule.color,
    font_size=2,
    effect=self._get_effect_code(schedule.effect)
)
```

## Conclusión

**✅ CONFIRMADO**: El sistema respeta correctamente la prioridad de programaciones activas:

1. **Cuando hay programación activa**: Los paneles muestran el mensaje de la programación
2. **Cuando NO hay programación activa**: Los paneles muestran el estado del parking
3. **Los cambios de ocupación NO interfieren** con programaciones activas
4. **El monitor de programaciones ejecuta** las programaciones correctamente

La lógica implementada garantiza que **siempre se respete la prioridad de programaciones activas** sobre los mensajes automáticos de estado del parking. 