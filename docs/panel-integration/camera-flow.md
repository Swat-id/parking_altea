# Flujo de Integración con Cámaras - Paneles

## 📋 Resumen

Este documento describe el flujo completo de integración entre las cámaras de acceso y los paneles electrónicos, desde la recepción de datos hasta la actualización automática de los paneles.

## 🔄 Flujo Completo

```
Cámara → camera_server.py → update_parking_panels() → API 8888 → Panel LED
```

## 📍 Ubicación del Código

### Archivo Principal
- **Archivo**: `src/camera_server.py`
- **Línea**: 494
- **Función**: `handle_camera()` (POST `/camera`)

### Función de Integración
- **Archivo**: `src/panel_communication_service.py`
- **Línea**: 388
- **Función**: `update_parking_panels()`

## 🔧 Implementación Detallada

### 1. Recepción de Datos de Cámara

```python
# src/camera_server.py - Línea 183
@app.route('/camera', methods=['POST'])
def handle_camera():
    # Procesamiento de datos de cámara
    # ...
    
    # Actualización de ocupación del parking
    parking.current_occupancy = occ
    parking.status = calculate_status(occ, parking.max_capacity)
    
    # Envío a paneles (Línea 494)
    try:
        update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
        logger.info(f"Message sent to panels for {parking.name}: {parking.current_occupancy}/{parking.max_capacity} ({parking.status})")
    except Exception as e:
        logger.error(f"Error sending to panels for {parking.name}: {e}")
```

### 2. Función de Actualización de Paneles

```python
# src/panel_communication_service.py - Línea 388
def update_parking_panels(parking_id: int, current_occupancy: int, max_capacity: int, status: str, db_session=None) -> Dict:
    """
    Actualizar paneles de un parking con el estado actual
    
    Args:
        parking_id: ID del parking
        current_occupancy: Ocupación actual
        max_capacity: Capacidad máxima
        status: Estado del parking (LIBRE/DENSO/COMPLETO)
        db_session: Sesión de base de datos (opcional)
    
    Returns:
        Diccionario con resultado de la operación
    """
    try:
        # Obtener sesión de BD
        if db_session is None:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            import config
            
            engine = create_engine(config.DB_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            close_session = True
        else:
            session = db_session
            close_session = False
        
        try:
            # Obtener parking y sus paneles
            from models import Parking, Panel
            parking = session.query(Parking).filter(Parking.id == parking_id).first()
            
            if not parking:
                return {'success': False, 'error': 'Parking no encontrado'}
            
            panels = session.query(Panel).filter(
                and_(
                    Panel.parking_id == parking_id,
                    Panel.status == 'ONLINE'
                )
            ).all()
            
            if not panels:
                return {'success': False, 'error': 'No hay paneles online para este parking'}
            
            # Calcular mensaje según estado
            free_spaces = max_capacity - current_occupancy
            
            if status == 'LIBRE':
                message = "LLIURE"
                color = 2  # Verde
            elif status == 'DENSO':
                message = "DENS"
                color = 3  # Amarillo
            else:  # COMPLETO
                message = "COMPLET"
                color = 1  # Rojo
            
            # Usar el PanelCommunicationService para enviar mensajes
            panel_service = PanelCommunicationService()
            
            success_count = 0
            for panel in panels:
                try:
                    result = panel_service.send_custom_text(
                        panel_ip=panel.ip,
                        text=message,
                        color=color,
                        font_size=2,  # Tamaño 16 píxeles (código 2)
                        effect=1  # Efecto fijo (valor 1)
                    )
                    
                    if result.get('success'):
                        success_count += 1
                        logger.info(f"Panel {panel.ip} actualizado: {message}")
                    else:
                        logger.error(f"Error actualizando panel {panel.ip}: {result.get('message')}")
                        
                except Exception as e:
                    logger.error(f"Error enviando a panel {panel.ip}: {e}")
            
            logger.info(f"Actualización de paneles completada: {success_count}/{len(panels)} exitosos")
            return {
                'success': True,
                'panels_affected': success_count,
                'total_panels': len(panels),
                'message': message,
                'color': color
            }
            
        finally:
            if close_session:
                session.close()
                
    except Exception as e:
        logger.error(f"Error general en update_parking_panels: {str(e)}")
        return {'success': False, 'error': str(e)}
```

## 📊 Datos de Entrada

### Mensaje de Cámara
```json
{
  "device": "nombre_camara",
  "line": 0,
  "Vehicle In": 1234,
  "Vehicle Out": 567,
  "event": "optional",
  "time": "optional"
}
```

### Parámetros de Actualización
- **parking_id**: ID del parking afectado
- **current_occupancy**: Ocupación actual calculada
- **max_capacity**: Capacidad máxima del parking
- **status**: Estado calculado (LIBRE/DENSO/COMPLETO)

## 📤 Datos de Salida

### Mensaje a Panel
- **Estado LIBRE**: "LLIURE" (Verde)
- **Estado DENSO**: "DENS" (Amarillo)
- **Estado COMPLETO**: "COMPLET" (Rojo)

### Configuración de Panel
- **Color**: Según estado (1=Rojo, 2=Verde, 3=Amarillo)
- **Tamaño de fuente**: 2 (16 píxeles)
- **Efecto**: 1 (Fijo)
- **Protocolo**: Detectado automáticamente por IP

## 🔍 Logging y Monitoreo

### Logs de Éxito
```
INFO: Message sent to panels for P. Ciutat Esportiva: 250/300 (LIBRE)
INFO: Panel 172.20.4.52 actualizado: LLIURE
INFO: Actualización de paneles completada: 2/2 exitosos
```

### Logs de Error
```
ERROR: Error sending to panels for P. Ciutat Esportiva: Connection timeout
ERROR: Error actualizando panel 172.20.4.52: HTTP 500
ERROR: Error general en update_parking_panels: Database connection failed
```

## ⚙️ Configuración

### Variables de Entorno
```bash
CAMERA_PORT=6400
PANEL_API_URL=http://localhost:8888/api/v1/panels/send
```

### Parámetros de Comunicación
- **Timeout**: 30 segundos
- **Reintentos**: 3 intentos
- **Puerto estándar**: 5200
- **Protocolo**: Detectado automáticamente

## 🎯 Validación

### ✅ Funcionalidades Validadas
- Recepción correcta de datos de cámara
- Cálculo automático de ocupación
- Determinación de estado según umbrales
- Envío automático a paneles
- Manejo de errores robusto
- Logging detallado

### ✅ Integración Correcta
- Usa la API unificada en puerto 8888
- Estructura de payload estándar
- Protocolo dinámico por panel
- Manejo de múltiples paneles
- Respuestas estructuradas

## 📋 Casos de Uso

### Caso 1: Entrada de Vehículo
1. Cámara detecta entrada
2. Envía datos al servidor
3. Se incrementa ocupación
4. Se recalcula estado
5. Se actualizan paneles automáticamente

### Caso 2: Salida de Vehículo
1. Cámara detecta salida
2. Envía datos al servidor
3. Se decrementa ocupación
4. Se recalcula estado
5. Se actualizan paneles automáticamente

### Caso 3: Cambio de Estado
1. Ocupación cruza umbral
2. Estado cambia (LIBRE → DENSO)
3. Mensaje cambia (LLIURE → DENS)
4. Color cambia (Verde → Amarillo)
5. Paneles se actualizan automáticamente

## 🎯 Conclusiones

El flujo de integración con cámaras está **completamente funcional** y utiliza correctamente la API unificada de paneles en el puerto 8888. La implementación es robusta, con manejo de errores adecuado y logging detallado para monitoreo. 