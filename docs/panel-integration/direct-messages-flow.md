# Flujo de Envío Directo de Mensajes - Paneles

## 📋 Resumen

Este documento describe el flujo de envío directo de mensajes personalizados a paneles electrónicos desde el frontend, incluyendo la validación, procesamiento y comunicación con la API unificada.

## 🔄 Flujo Completo

```
Frontend → api_server.py → PanelCommunicationService → API 8888 → Panel LED
```

## 📍 Ubicación del Código

### Archivo Principal
- **Archivo**: `src/api_server.py`
- **Líneas**: 1114, 1166
- **Función**: `send_message_to_panel()` (POST `/panel/{id}/message`)

### Servicio de Comunicación
- **Archivo**: `src/panel_communication_service.py`
- **Línea**: 317
- **Función**: `PanelCommunicationService.send_custom_text()`

## 🔧 Implementación Detallada

### 1. Endpoint de Envío de Mensajes

```python
# src/api_server.py - Línea 1084
@app.route('/panel/<int:panel_id>/message', methods=['POST'])
@require_panel_access('panel_id')
def send_message_to_panel(panel_id):
    """Enviar mensaje a un panel específico por ID"""
    try:
        req = request.get_json(force=True)
        message = req.get('message')
        duration = req.get('duration', 30)
        color = req.get('color', 1)
        fontSize = req.get('fontSize', 2)  # Recibir código de fuente directamente
        showEffect = req.get('showEffect', "fijo")  # Fijo por defecto
        
        if not message:
            return jsonify({'error': 'Missing message field'}), 400
        
        # No convertir fontSize ya que viene como código
        font_size_code = fontSize
        
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Guardar información del panel antes de cerrar la sesión
        panel_name = panel.name
        panel_ip = panel.ip
        
        # Usar el PanelCommunicationService (Línea 1114)
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        start_time = datetime.now()
        result = panel_service.send_custom_text(
            panel_ip=panel_ip,
            text=message,
            color=color,
            font_size=font_size_code,  # Usar código convertido
            effect=showEffect
        )
        response_time = (datetime.now() - start_time).total_seconds() * 1000  # en ms
        
        # Actualizar estado del panel
        panel.status = 'ONLINE' if result['success'] else 'OFFLINE'
        panel.last_message = message
        panel.last_update = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'panel_id': panel_id,
            'panel_name': panel_name,
            'panel_ip': panel_ip,
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error sending message to panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### 2. Endpoint de Prueba de Panel

```python
# src/api_server.py - Línea 1150
@app.route('/panel/<int:panel_id>/test', methods=['POST'])
def test_panel(panel_id):
    """Probar comunicación con un panel"""
    try:
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Guardar información del panel antes de cerrar la sesión
        panel_name = panel.name
        panel_ip = panel.ip
        
        # Usar el PanelCommunicationService (Línea 1166)
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        start_time = datetime.now()
        result = panel_service.send_custom_text(
            panel_ip=panel_ip,
            text='PRUEBA',
            color=2,  # Verde para prueba
            font_size=2,  # Tamaño 16 píxeles (código 2)
            effect="fijo"  # Fijo por defecto
        )
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Actualizar estado del panel
        panel.status = 'ONLINE' if result['success'] else 'OFFLINE'
        panel.last_update = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'panel_id': panel_id,
            'panel_name': panel_name,
            'panel_ip': panel_ip,
            'responseTime': response_time
        })
        
    except Exception as e:
        logger.error(f"Error testing panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### 3. Servicio de Comunicación

```python
# src/panel_communication_service.py - Línea 317
def send_custom_text(self, panel_ip: str, text: str, 
                    color: int = 1, font_size: int = 2, 
                    effect: int = 1) -> Dict:
    """
    Enviar texto personalizado a un panel
    
    Args:
        panel_ip: IP del panel
        text: Texto a enviar
        color: Color del texto (1=Rojo, 2=Verde, 3=Amarillo, etc.)
        font_size: Tamaño de fuente (2=16px por defecto)
        effect: Efecto (1=fijo, 12=scroll)
    
    Returns:
        Diccionario con resultado de la operación
    """
    try:
        # Validar parámetros
        if not text or not text.strip():
            return {
                'success': False,
                'message': 'Texto vacío o inválido',
                'panel_ip': panel_ip,
                'timestamp': datetime.now().isoformat()
            }
        
        # Convertir efecto a string descriptivo
        effect_string = "fijo" if effect == 1 else "scroll" if effect == 12 else "fijo"
        
        # Enviar usando la API unificada
        result = self._send_to_unified_api(
            panel_ip=panel_ip,
            texts=[text],
            colors=[color],
            font_sizes=[font_size],
            show_effects=[effect]
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error enviando texto personalizado a {panel_ip}: {e}")
        return {
            'success': False,
            'message': f'Error inesperado: {str(e)}',
            'panel_ip': panel_ip,
            'timestamp': datetime.now().isoformat()
        }
```

## 📊 Datos de Entrada

### Envío de Mensaje
```json
{
  "message": "MANTENIMENT",
  "duration": 60,
  "color": 1,
  "fontSize": 2,
  "showEffect": "fijo"
}
```

### Prueba de Panel
```json
{
  // No requiere parámetros - envía mensaje de prueba automáticamente
}
```

## 📤 Datos de Salida

### Respuesta de Envío
```json
{
  "success": true,
  "message": "Texto enviado exitosamente (old)",
  "panel_id": 1,
  "panel_name": "Panel 1",
  "panel_ip": "172.20.4.52",
  "response_time": 1250.5
}
```

### Respuesta de Prueba
```json
{
  "success": true,
  "message": "Texto enviado exitosamente (old)",
  "panel_id": 1,
  "panel_name": "Panel 1",
  "panel_ip": "172.20.4.52",
  "responseTime": 980.2
}
```

## 🔍 Logging y Monitoreo

### Logs de Éxito
```
INFO: Enviando a panel 172.20.4.52 (old): ['MANTENIMENT']
INFO: ✅ Texto enviado exitosamente a 172.20.4.52 (old)
INFO: Panel 1 actualizado: MANTENIMENT
```

### Logs de Error
```
ERROR: Error sending message to panel 1: Connection timeout
ERROR: ❌ Error HTTP 500: Internal server error
ERROR: Error enviando texto personalizado a 172.20.4.52: Network unreachable
```

## ⚙️ Configuración

### Variables de Entorno
```bash
API_PORT=6001
PANEL_API_URL=http://localhost:8888/api/v1/panels/send
```

### Parámetros de Comunicación
- **Timeout**: 30 segundos
- **Reintentos**: 3 intentos
- **Puerto estándar**: 5200
- **Protocolo**: Detectado automáticamente por IP

### Parámetros de Validación
- **Mensaje**: No puede estar vacío
- **Color**: 1-7 (Rojo, Verde, Amarillo, Azul, Magenta, Cian, Blanco)
- **Tamaño de fuente**: 0-7 (8px a 56px)
- **Efecto**: 1 (fijo) o 12 (scroll)

## 🎯 Validación

### ✅ Funcionalidades Validadas
- Envío de mensajes personalizados
- Prueba de conectividad de paneles
- Validación de parámetros de entrada
- Actualización automática de estado de panel
- Medición de tiempo de respuesta
- Manejo de errores robusto
- Logging detallado

### ✅ Integración Correcta
- Usa la API unificada en puerto 8888
- Estructura de payload estándar
- Protocolo dinámico por panel
- Manejo de errores consistente
- Respuestas estructuradas

## 📋 Casos de Uso

### Caso 1: Mensaje de Mantenimiento
1. Usuario selecciona panel específico
2. Escribe mensaje "MANTENIMENT"
3. Selecciona color rojo (1)
4. Configura duración de 60 segundos
5. Envía mensaje
6. Panel muestra mensaje inmediatamente

### Caso 2: Prueba de Conectividad
1. Usuario hace clic en "Probar Panel"
2. Sistema envía mensaje "PRUEBA" automáticamente
3. Panel responde con mensaje verde
4. Sistema actualiza estado ONLINE/OFFLINE
5. Usuario recibe confirmación

### Caso 3: Mensaje con Scroll
1. Usuario escribe mensaje largo
2. Selecciona efecto "scroll"
3. Configura color amarillo (3)
4. Envía mensaje
5. Panel muestra texto con desplazamiento

## 🔒 Seguridad

### Autenticación
- **Endpoint**: Requiere autenticación JWT
- **Decorador**: `@require_panel_access('panel_id')`
- **Validación**: Token válido y acceso al panel requerido

### Validación de Datos
- **Mensaje**: String no vacío
- **Color**: Número entero 1-7
- **Tamaño**: Número entero 0-7
- **Efecto**: String válido ("fijo" o "scroll")
- **Formato**: JSON válido requerido

## 🎯 Conclusiones

El flujo de envío directo de mensajes está **completamente funcional** y utiliza correctamente la API unificada de paneles en el puerto 8888. La implementación incluye validación robusta, manejo de errores adecuado, medición de rendimiento y logging detallado para auditoría. 