# Workflow de Aforo - Flujo Completo de Cámara a Panel

## Resumen Ejecutivo

Este documento describe el flujo completo desde que una cámara envía un mensaje de ocupación hasta que se actualiza el panel correspondiente. El objetivo es identificar posibles puntos de fallo en la lógica de actualización de aforo.

## 1. Recepción del Mensaje de Cámara

### 1.1 Endpoint de Recepción
- **URL**: `/camera` (NO `/cameras/update_occupancy`)
- **Método**: POST
- **Archivo**: `src/camera_server.py`
- **Puerto**: 6400 (servicio separado del API principal)

### 1.2 Parámetros del Mensaje
```json
{
  "event": "Object Counting",
  "device": "ciutat_esportiva camera 1",
  "time": "2025-04-22 18:38:09",
  "line": 0,
  "Vehicle In": 163,
  "Vehicle Out": 312,
  "Vehicle Capacity": 0,
  "Vehicle Sum": 475
}
```

### 1.3 Identificación de la Cámara
El sistema identifica la cámara mediante:
1. **IP de origen**: Extraída del header `X-Forwarded-For` o `remote_addr`
2. **Línea**: Campo `line` del mensaje JSON
3. **Combinación IP + línea** debe coincidir con un registro en la tabla `accesses`

### 1.4 Validación Inicial
- Verificar que la cámara existe en la tabla `accesses` (IP + línea)
- Validar formato JSON del mensaje
- Comprobar campos requeridos (`line`, `Vehicle In`, `Vehicle Out`)
- Verificar que no sea un mensaje duplicado (cache de 5 minutos)

## 2. Procesamiento del Mensaje

### 2.1 Actualización de Estado de Cámara
```python
# Actualizar estado de la cámara a ONLINE y timestamp
access.status = 'ONLINE'
access.last_message_received = datetime.now()
```

### 2.2 Cálculo de Delta de Ocupación
```python
# Obtener contadores anteriores
previous_vehicle_in = access.last_vehicle_in
previous_vehicle_out = access.last_vehicle_out

# Calcular deltas con manejo de reinicios
delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
    previous_vehicle_in, previous_vehicle_out, veh_in, veh_out
)

# Actualizar contadores de acceso
access.last_vehicle_in = veh_in
access.last_vehicle_out = veh_out
```

### 2.3 Manejo de Reinicios de Cámara
- Si los contadores nuevos son menores que los anteriores, se detecta un reinicio
- Se ajusta el cálculo de deltas para manejar el reinicio
- Se registra en logs como "reset_processed"

## 3. Actualización de Base de Datos

### 3.1 Actualización de Parking
```python
# Obtener parking asociado a la cámara
parking = access.parking
previous_occupancy = parking.current_occupancy

# Actualizar ocupación
parking.current_occupancy += (delta_in - delta_out)

# PERMITIR OCUPACIÓN POR ENCIMA DEL MÁXIMO Y VALORES NEGATIVOS
# No limitar la ocupación al máximo de capacidad
```

### 3.2 Cálculo de Estado del Parking
```python
free_spaces = parking.max_capacity - parking.current_occupancy

if parking.fixed_message_flag:
    # Si hay mensaje fijo activo, NO actualizar estado
    parking_status = parking.status
else:
    # NUEVA LÓGICA: Descuadre negativo = COMPLETO
    if free_spaces < 0:
        parking.status = 'COMPLETO'
    elif free_spaces <= parking.threshold_full:
        parking.status = 'COMPLETO'
    elif free_spaces <= parking.threshold_dense:
        parking.status = 'DENSO'
    else:
        parking.status = 'LIBRE'
```

### 3.3 Registro en Historial
```python
# Registrar en occupancy_history
hist = OccupancyHistory(
    parking_id=parking.id,
    occupancy=parking.current_occupancy,
    source='camera'
)
session.add(hist)

# Registrar log detallado en camera_logs
log_camera_message(
    session=session,
    camera_ip=ip,
    camera_line=original_line,
    camera_name=device,
    raw_message=raw_data,
    vehicle_in=veh_in,
    vehicle_out=veh_out,
    status="processed" if not is_reset else "reset_processed",
    delta_in=delta_in,
    delta_out=delta_out,
    new_occupancy=occ,
    occupancy_change=occ - previous_occupancy,
    parking_status=parking_status
)
```

## 4. Verificación de Programaciones Activas

### 4.1 Comprobación de Programaciones
```python
# VERIFICAR SI HAY PROGRAMACIONES ACTIVAS
schedule_service = PanelScheduleService(session)
active_schedules = schedule_service.get_active_schedules_for_parking(parking_id)

if active_schedules:
    logger.info(f"Active schedules found for parking {parking_id}, skipping panel update for occupancy change")
    return "SCHEDULE_ACTIVE"  # NO actualizar paneles si hay programación activa
```

## 5. Preparación del Mensaje para Panel

### 5.1 Conversión a Valenciano
```python
# Convertir estado a valenciano según especificaciones
if status == "LIBRE":
    valenciano_status = "LLIURE"
elif status == "DENSO":
    valenciano_status = "DENS"
elif status == "COMPLETO":
    valenciano_status = "COMPLET"
else:
    valenciano_status = status

# Construir mensaje para los paneles - SOLO EL ESTADO EN VALENCIANO
message = valenciano_status
```

### 5.2 Determinación de Color
```python
# Determinar color según umbrales del parking
if free_spaces < 0:
    # Descuadre negativo - rojo
    color = 1  # Rojo
elif free_spaces <= parking.threshold_full:
    # Completo - rojo
    color = 1  # Rojo
elif free_spaces <= parking.threshold_dense:
    # Denso - amarillo
    color = 3  # Amarillo
else:
    # Libre - verde
    color = 2  # Verde
```

## 6. Envío al Panel

### 6.1 Servicio de Comunicación
```python
# Importar el servicio de comunicación
from panel_communication_service import PanelCommunicationService

# Crear instancia del servicio
service = PanelCommunicationService()

# Obtener paneles del parking
panels = session.query(Panel).filter(Panel.parking_id == parking_id).all()
```

### 6.2 Llamada al Servicio
```python
# Enviar mensaje a cada panel
for panel in panels:
    try:
        result = service.send_custom_text(
            panel_ip=panel.ip,
            text=message,
            color=color,
            font_size=2,  # Tamaño de texto 2 por defecto
            effect=1      # Efecto centrado
        )
        
        if result.get('success'):
            success_count += 1
            logger.info(f"Message sent to panel {panel.ip}: {message} (color: {color})")
        else:
            logger.error(f"Failed to send message to panel {panel.ip}: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error sending message to panel {panel.ip}: {e}")
```

### 6.3 API del Servicio de Paneles
- **URL**: `http://127.0.0.1:5656/sendMulti`
- **Método**: POST
- **Payload**:
```json
{
    "ip": "172.20.17.50",
    "itemNum": 1,
    "texts": ["LLIURE"],
    "colors": [2],
    "fontSizes": [2],
    "showEffects": [1]
}
```

## 7. Logging y Monitoreo

### 7.1 Logs de Éxito
```python
logger.info(f"Message sent to panels: {parking.current_occupancy}/{parking.max_capacity} ({parking.status})")
logger.info(f"Panel messages sent for parking {parking_id}: {success_count}/{len(panels)} successful")
```

### 7.2 Logs de Error
```python
logger.error(f"Error sending to panels: {e}")
logger.error(f"Failed to send message to panel {panel.ip}: {result.get('error', 'Unknown error')}")
```

### 7.3 Logs Detallados
- **camera_logs**: Registro completo de cada mensaje de cámara
- **occupancy_history**: Historial de cambios de ocupación
- **panel_schedule_logs**: Logs de programaciones activas

## 8. Puntos de Fallo Potenciales

### 8.1 Identificación de Cámara
- **Problema**: IP o línea no coinciden con `accesses`
- **Síntoma**: "Access not found" en logs
- **Solución**: Verificar configuración en tabla `accesses`

### 8.2 Programaciones Activas
- **Problema**: Programación activa bloquea actualización de paneles
- **Síntoma**: "Active schedules found, skipping panel update"
- **Solución**: Verificar programaciones en `panel_schedules`

### 8.3 Servicio de Paneles
- **Problema**: API en puerto 5656 no responde
- **Síntoma**: Timeouts o errores de conexión
- **Solución**: Verificar estado del servicio `parking-panel-service`

### 8.4 Cálculo de Deltas
- **Problema**: Reinicios de cámara mal manejados
- **Síntoma**: Deltas irrealistas
- **Solución**: Verificar función `calculate_deltas_with_reset_handling`

### 8.5 Mensaje Fijo
- **Problema**: `fixed_message_flag` activo
- **Síntoma**: No se actualiza estado del parking
- **Solución**: Verificar flag en tabla `parkings`

## 9. Flujo de Diagnóstico

### 9.1 Verificar Recepción de Mensaje
```bash
# Revisar logs del camera_server
tail -f /var/log/parking-camera.log

# Verificar servicio
systemctl status parking-camera
```

### 9.2 Verificar Actualización de Base de Datos
```sql
-- Verificar ocupación actual
SELECT id, name, occupancy, last_update, fixed_message_flag
FROM parkings 
WHERE id = parking_id;

-- Verificar historial reciente
SELECT * FROM occupancy_history 
WHERE parking_id = parking_id 
ORDER BY timestamp DESC 
LIMIT 5;

-- Verificar logs de cámara
SELECT * FROM camera_logs 
WHERE parking_id = parking_id 
ORDER BY processed_at DESC 
LIMIT 5;
```

### 9.3 Verificar Programaciones Activas
```sql
-- Verificar programaciones activas
SELECT * FROM panel_schedules 
WHERE is_active = true 
AND start_time <= NOW() 
AND end_time >= NOW();
```

### 9.4 Verificar Estado de Paneles
```sql
-- Verificar paneles del parking
SELECT p.id, p.name, p.status, p.last_message, p.last_update,
       pt.name as panel_type, pt.protocol_type
FROM panels p
JOIN panel_types pt ON p.panel_type_id = pt.id
WHERE p.parking_id = parking_id;
```

### 9.5 Verificar Servicio de Paneles
```bash
# Verificar estado del servicio
systemctl status parking-panel-service

# Probar conectividad
curl -X POST http://localhost:5656/sendMulti \
  -H "Content-Type: application/json" \
  -d '{"ip":"172.20.17.50","itemNum":1,"texts":["TEST"],"colors":[2],"fontSizes":[2],"showEffects":[1]}'
```

## 10. Recomendaciones de Mejora

### 10.1 Implementar Queue de Mensajes
- Usar Redis o RabbitMQ para cola de mensajes
- Procesar actualizaciones de forma asíncrona
- Implementar reintentos automáticos

### 10.2 Mejorar Monitoreo
- Implementar health checks para todos los servicios
- Crear dashboards de métricas
- Configurar alertas automáticas

### 10.3 Optimizar Base de Datos
- Crear índices apropiados
- Usar particionado para tablas grandes
- Implementar cleanup automático de datos antiguos

### 10.4 Validación Robusta
- Validar todos los inputs
- Implementar circuit breakers
- Usar timeouts apropiados

## 11. Scripts de Diagnóstico

### 11.1 Verificar Estado Completo
```bash
#!/bin/bash
# check_workflow_status.sh

echo "=== Estado del Workflow de Aforo ==="
echo "1. Verificando servicios..."
systemctl status parking-api
systemctl status parking-camera
systemctl status parking-panel-service

echo "2. Verificando base de datos..."
PGPASSWORD=parking_pass psql -h localhost -U parking_user -d parking_db -c "
SELECT p.id, p.name, p.occupancy, p.last_update, p.fixed_message_flag,
       COUNT(oh.id) as history_count
FROM parkings p
LEFT JOIN occupancy_history oh ON p.id = oh.parking_id 
  AND oh.timestamp > NOW() - INTERVAL '1 hour'
GROUP BY p.id, p.name, p.occupancy, p.last_update, p.fixed_message_flag
ORDER BY p.id;"

echo "3. Verificando programaciones activas..."
PGPASSWORD=parking_pass psql -h localhost -U parking_user -d parking_db -c "
SELECT * FROM panel_schedules 
WHERE is_active = true 
AND start_time <= NOW() 
AND end_time >= NOW();"

echo "4. Verificando paneles..."
PGPASSWORD=parking_pass psql -h localhost -U parking_user -d parking_db -c "
SELECT p.id, p.name, p.status, p.last_message, p.last_update,
       pt.name as panel_type, pt.protocol_type
FROM panels p
JOIN panel_types pt ON p.panel_type_id = pt.id
ORDER BY p.parking_id, p.id;"
```

### 11.2 Simular Mensaje de Cámara
```bash
#!/bin/bash
# test_camera_message.sh

PARKING_ID=1
CAMERA_IP="172.20.17.50"
CAMERA_LINE=0
VEHICLE_IN=163
VEHICLE_OUT=312

echo "Simulando mensaje de cámara..."
curl -X POST http://localhost:6400/camera \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: $CAMERA_IP" \
  -d "{
    \"event\": \"Object Counting\",
    \"device\": \"test_camera\",
    \"time\": \"$(date '+%Y-%m-%d %H:%M:%S')\",
    \"line\": $CAMERA_LINE,
    \"Vehicle In\": $VEHICLE_IN,
    \"Vehicle Out\": $VEHICLE_OUT
  }"

echo -e "\nVerificando resultado..."
sleep 2
PGPASSWORD=parking_pass psql -h localhost -U parking_user -d parking_db -c "
SELECT p.name, p.occupancy, p.last_update, p.status,
       p.last_message, p.status
FROM panels p
WHERE p.parking_id = $PARKING_ID;"
```

### 11.3 Verificar Logs de Cámara
```bash
#!/bin/bash
# check_camera_logs.sh

echo "=== Últimos Logs de Cámara ==="
PGPASSWORD=parking_pass psql -h localhost -U parking_user -d parking_db -c "
SELECT 
    cl.camera_ip,
    cl.camera_line,
    cl.vehicle_in,
    cl.vehicle_out,
    cl.delta_in,
    cl.delta_out,
    cl.status,
    cl.new_occupancy,
    cl.parking_status,
    cl.processed_at
FROM camera_logs cl
ORDER BY cl.processed_at DESC
LIMIT 10;"
```

## 12. Conclusión

Este workflow es complejo y tiene múltiples puntos de fallo. La clave para un funcionamiento correcto es:

1. **Monitoreo continuo** de todos los componentes
2. **Logging detallado** en cada paso del proceso
3. **Validación robusta** de datos y respuestas
4. **Manejo de errores** con reintentos y fallbacks
5. **Testing regular** del flujo completo

### Puntos Críticos Identificados:
- **Programaciones activas** pueden bloquear actualizaciones de paneles
- **Mensaje fijo** puede impedir cambios de estado
- **Servicio de paneles** (puerto 5656) debe estar funcionando
- **Identificación de cámara** debe coincidir exactamente con `accesses`

El documento debe actualizarse conforme se identifiquen y resuelvan problemas específicos en el sistema. 