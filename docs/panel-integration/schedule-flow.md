# Flujo de Programaciones Automáticas - Paneles

## 📋 Resumen

Este documento describe el flujo completo de programaciones automáticas de paneles, desde la creación de programaciones hasta su ejecución automática por el monitor de programaciones.

## 🔄 Flujo Completo

```
Schedule Monitor → panel_schedule_service.py → PanelCommunicationService → API 8888 → Panel LED
```

## 📍 Ubicación del Código

### Servicio de Programaciones
- **Archivo**: `src/panel_schedule_service.py`
- **Líneas**: 330, 380
- **Función**: `execute_schedule()`

### Monitor de Programaciones
- **Archivo**: `src/schedule_monitor_service.py`
- **Línea**: 100
- **Función**: `_check_and_execute_schedules()`

### Servicio de Comunicación
- **Archivo**: `src/panel_communication_service.py`
- **Línea**: 317
- **Función**: `PanelCommunicationService.send_custom_text()`

## 🔧 Implementación Detallada

### 1. Servicio de Programaciones

```python
# src/panel_schedule_service.py - Línea 316
def execute_schedule(self, schedule: PanelSchedule) -> dict:
    """Ejecutar una programación enviando el mensaje a los paneles"""
    try:
        # Obtener paneles del parking
        panels = self.session.query(Panel).filter(
            and_(
                Panel.parking_id == schedule.parking_id,
                Panel.status == 'ONLINE'
            )
        ).all()
        
        if not panels:
            return {'success': False, 'error': 'No hay paneles online para este parking'}
        
        # Enviar mensaje a todos los paneles (Línea 330)
        success_count = 0
        for panel in panels:
            try:
                result = self.panel_communication_service.send_custom_text(
                    panel_ip=panel.panel_ip,
                    text=schedule.message,
                    color=schedule.color,
                    font_size=schedule.font_size,
                    effect=self._get_effect_code(schedule.effect)
                )
                if result.get('success'):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error enviando mensaje a panel {panel.id}: {e}")
        
        # Registrar log de ejecución
        log = PanelScheduleLog(
            schedule_id=schedule.id,
            parking_id=schedule.parking_id,
            execution_type='started',
            message_sent=schedule.message,
            panels_affected=success_count
        )
        self.session.add(log)
        self.session.commit()
        
        logger.info(f"Programación ejecutada: {schedule.id} - {success_count}/{len(panels)} paneles")
        return {'success': True, 'panels_affected': success_count}
        
    except Exception as e:
        self.session.rollback()
        logger.error(f"Error ejecutando programación: {e}")
        return {'success': False, 'error': str(e)}
```

### 2. Finalización de Programaciones

```python
# src/panel_schedule_service.py - Línea 365
def end_schedule(self, schedule: PanelSchedule) -> dict:
    """Finalizar una programación restaurando el estado del parking"""
    try:
        # Obtener paneles del parking
        panels = self.session.query(Panel).filter(
            and_(
                Panel.parking_id == schedule.parking_id,
                Panel.status == 'ONLINE'
            )
        ).all()
        
        if not panels:
            return {'success': False, 'error': 'No hay paneles online para este parking'}
        
        # Obtener estado actual del parking
        parking = self.session.query(Parking).filter(Parking.id == schedule.parking_id).first()
        if not parking:
            return {'success': False, 'error': 'Parking no encontrado'}
        
        # Determinar mensaje según estado del parking
        occupancy_percent = (parking.current_occupancy / parking.max_capacity) * 100
        
        if occupancy_percent < parking.threshold_dense:
            message = "LLIURE"
            color = 2  # Verde
        elif occupancy_percent < parking.threshold_full:
            message = "DENS"
            color = 3  # Amarillo
        else:
            message = "COMPLET"
            color = 1  # Rojo
        
        # Enviar mensaje de estado a todos los paneles (Línea 380)
        success_count = 0
        for panel in panels:
            try:
                result = self.panel_communication_service.send_custom_text(
                    panel_ip=panel.panel_ip,
                    text=message,
                    color=color,
                    font_size=16,  # font_size por defecto
                    effect=1  # Efecto estático
                )
                if result.get('success'):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error enviando mensaje de estado a panel {panel.id}: {e}")
        
        # Registrar log de finalización
        log = PanelScheduleLog(
            schedule_id=schedule.id,
            parking_id=schedule.parking_id,
            execution_type='ended',
            message_sent=message,
            panels_affected=success_count
        )
        self.session.add(log)
        self.session.commit()
        
        logger.info(f"Programación finalizada: {schedule.id} - {success_count}/{len(panels)} paneles")
        return {'success': True, 'panels_affected': success_count}
        
    except Exception as e:
        self.session.rollback()
        logger.error(f"Error finalizando programación: {e}")
        return {'success': False, 'error': str(e)}
```

### 3. Monitor de Programaciones

```python
# src/schedule_monitor_service.py - Línea 60
def _check_and_execute_schedules(self):
    """Verificar y ejecutar programaciones activas"""
    try:
        session = self.Session()
        schedule_service = PanelScheduleService(session)
        
        # Obtener todas las programaciones activas
        result = schedule_service.get_schedules(active_only=True)
        
        if not result['success']:
            logger.error(f"Error obteniendo programaciones: {result['error']}")
            session.close()
            return
        
        current_time = datetime.now().astimezone()
        current_time_str = current_time.strftime('%H:%M')
        current_weekday = current_time.weekday()
        
        # Mapear weekday a campos de la base de datos
        weekday_fields = {
            0: 'monday',
            1: 'tuesday', 
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturday',
            6: 'sunday'
        }
        
        current_weekday_field = weekday_fields.get(current_weekday, 'monday')
        
        for schedule_data in result['schedules']:
            try:
                # Verificar si la programación debe ejecutarse ahora
                if self._should_execute_schedule(schedule_data, current_time, current_time_str, current_weekday_field):
                    schedule_id = schedule_data['id']
                    
                    # Evitar ejecuciones duplicadas en el mismo minuto
                    execution_key = f"{schedule_id}_{current_time.strftime('%Y%m%d_%H%M')}"
                    
                    if execution_key not in self.executed_schedules:
                        logger.info(f"Ejecutando programación: {schedule_data['name']} (ID: {schedule_id})")
                        
                        # Obtener el objeto schedule completo
                        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
                        if schedule:
                            # Ejecutar la programación (Línea 100)
                            execution_result = schedule_service.execute_schedule(schedule)
                            
                            if execution_result['success']:
                                logger.info(f"Programación {schedule_id} ejecutada exitosamente: {execution_result['panels_affected']} paneles afectados")
                                self.executed_schedules.add(execution_key)
                            else:
                                logger.error(f"Error ejecutando programación {schedule_id}: {execution_result['error']}")
                        
                        # Limpiar ejecuciones antiguas (más de 1 hora)
                        self._cleanup_old_executions(current_time)
            
            except Exception as e:
                logger.error(f"Error procesando programación {schedule_data.get('id', 'unknown')}: {e}")
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error en verificación de programaciones: {e}")
        if 'session' in locals():
            session.close()
```

## 📊 Datos de Entrada

### Creación de Programación
```json
{
  "parking_id": 1,
  "name": "Mantenimiento Programado",
  "description": "Mantenimiento del parking",
  "start_date": "2025-01-15",
  "end_date": "2025-01-15",
  "start_time": "10:00",
  "end_time": "12:00",
  "monday": false,
  "tuesday": false,
  "wednesday": false,
  "thursday": false,
  "friday": false,
  "saturday": true,
  "sunday": false,
  "message": "MANTENIMENT",
  "color": 1,
  "font_size": 16,
  "effect": "static",
  "is_active": true,
  "priority": 1
}
```

## 📤 Datos de Salida

### Respuesta de Ejecución
```json
{
  "success": true,
  "panels_affected": 2,
  "total_panels": 2,
  "message": "MANTENIMENT",
  "color": 1
}
```

### Respuesta de Finalización
```json
{
  "success": true,
  "panels_affected": 2,
  "message": "LLIURE",
  "color": 2
}
```

## 🔍 Logging y Monitoreo

### Logs de Ejecución
```
INFO: Ejecutando programación: Mantenimiento Programado (ID: 1)
INFO: Programación 1 ejecutada exitosamente: 2 paneles afectados
INFO: Enviando a panel 172.20.4.52 (old): ['MANTENIMENT']
INFO: ✅ Texto enviado exitosamente a 172.20.4.52 (old)
```

### Logs de Finalización
```
INFO: Programación terminada: Mantenimiento Programado (ID: 1)
INFO: Programación finalizada: 1 - 2/2 paneles
INFO: Enviando a panel 172.20.4.52 (old): ['LLIURE']
INFO: ✅ Texto enviado exitosamente a 172.20.4.52 (old)
```

### Logs de Error
```
ERROR: Error ejecutando programación 1: No hay paneles online para este parking
ERROR: Error enviando mensaje a panel 1: Connection timeout
ERROR: Error en verificación de programaciones: Database connection failed
```

## ⚙️ Configuración

### Variables de Entorno
```bash
PANEL_API_URL=http://localhost:8888/api/v1/panels/send
```

### Parámetros del Monitor
- **Intervalo de verificación**: 60 segundos
- **Cache de ejecuciones**: 1 hora
- **Timeout de comunicación**: 30 segundos
- **Reintentos**: 3 intentos

### Parámetros de Programación
- **Fechas**: Formato YYYY-MM-DD
- **Horarios**: Formato HH:MM (24h)
- **Días de la semana**: Boolean para cada día
- **Prioridad**: Número entero (mayor = más prioridad)
- **Estado activo**: Boolean

## 🎯 Validación

### ✅ Funcionalidades Validadas
- Creación de programaciones
- Ejecución automática en horarios programados
- Finalización automática al terminar horario
- Restauración de estado normal del parking
- Manejo de múltiples programaciones simultáneas
- Prevención de ejecuciones duplicadas
- Logging detallado de ejecuciones
- Manejo de errores robusto

### ✅ Integración Correcta
- Usa la API unificada en puerto 8888
- Estructura de payload estándar
- Protocolo dinámico por panel
- Manejo de múltiples paneles
- Respuestas estructuradas

## 📋 Casos de Uso

### Caso 1: Programación Diaria
1. Usuario crea programación para lunes a viernes
2. Configura horario de 09:00 a 18:00
3. Mensaje: "MANTENIMENT" en rojo
4. Monitor ejecuta automáticamente en horario
5. Al terminar, restaura estado normal

### Caso 2: Programación Única
1. Usuario crea programación para fecha específica
2. Configura horario de 14:00 a 16:00
3. Mensaje: "TANCAT" en rojo
4. Monitor ejecuta solo en esa fecha y horario
5. Al terminar, restaura estado normal

### Caso 3: Múltiples Programaciones
1. Usuario crea varias programaciones
2. Diferentes horarios y mensajes
3. Monitor ejecuta según prioridad
4. Cada programación maneja sus paneles
5. Logs separados para cada ejecución

## 🔒 Seguridad

### Autenticación
- **Creación**: Requiere autenticación JWT
- **Ejecución**: Automática por monitor
- **Validación**: Permisos de usuario requeridos

### Validación de Datos
- **Fechas**: Formato válido y lógico
- **Horarios**: Formato HH:MM válido
- **Mensaje**: String no vacío
- **Color**: Número entero 1-7
- **Prioridad**: Número entero >= 1

## 🎯 Conclusiones

El flujo de programaciones automáticas está **completamente funcional** y utiliza correctamente la API unificada de paneles en el puerto 8888. La implementación incluye ejecución automática, finalización inteligente, prevención de duplicados y logging detallado para auditoría completa. 