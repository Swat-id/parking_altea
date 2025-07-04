# Análisis de Flujos de Actualización de Paneles

## Resumen Ejecutivo

Este documento analiza los cuatro flujos principales que actualizan los paneles electrónicos en el sistema de gestión de parkings, validando que todos usen las mismas llamadas y protocolos tanto para el protocolo antiguo como el nuevo.

## Flujos Analizados

1. **Flujo de Mensajes de Cámara** - Actualización automática por detección de vehículos
2. **Flujo de Página de Paneles** - Envío manual de mensajes desde la interfaz web
3. **Flujo de Detalle de Parking** - Actualización manual del aforo
4. **Flujo de Servicio de Programaciones** - Actualización automática por programaciones temporales

---

## 1. Flujo de Mensajes de Cámara

### Ubicación del Código
- **Archivo**: `src/camera_server.py`
- **Función**: `handle_camera()` (línea 189)
- **Llamada a paneles**: Línea 492

### Flujo Detallado

```python
# 1. Procesamiento del mensaje de cámara
@app.route('/camera', methods=['POST'])
def handle_camera():
    # ... procesamiento de datos de cámara ...
    
    # 2. Actualización de ocupación del parking
    parking.current_occupancy = occ
    parking.status = 'LIBRE' | 'DENSO' | 'COMPLETO'
    
    # 3. Llamada a actualización de paneles
    update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
```

### Parámetros Enviados
- `parking_id`: ID del parking
- `current_occupancy`: Ocupación actual calculada
- `max_capacity`: Capacidad máxima del parking
- `status`: Estado calculado ('LIBRE', 'DENSO', 'COMPLETO')

### Protocolo Utilizado
- **Función**: `update_parking_panels()` de `panel_communication_service.py`
- **API Destino**: `http://localhost:8888/api/v1/panels/send`
- **Protocolo**: Detectado automáticamente por IP del panel

---

## 2. Flujo de Página de Paneles

### Ubicación del Código
- **Frontend**: `client/src/pages/Panels.jsx`
- **Servicio**: `client/src/services/panelService.js`
- **Backend**: `src/api_server.py` - Endpoint `/panel/<panel_id>/message`

### Flujo Detallado

#### Frontend (Panels.jsx)
```javascript
// 1. Envío de mensaje desde la interfaz
const sendMessageMutation = useMutation(
  ({ panelId, messageData }) => panelService.sendMessageToPanel(panelId, messageData)
);

// 2. Construcción del payload
const messageData = {
  message: messageText,
  duration: messageDuration,
  color: selectedColor,
  fontSize: 2,
  showEffect: "fijo"
};
```

#### Servicio Frontend (panelService.js)
```javascript
// 3. Envío al backend
const response = await api.post('/panel/' + panelId + '/message', {
  message: messageData.message,
  duration: messageData.duration,
  color: messageData.color || 1,
  fontSize: messageData.fontSize || 2,
  showEffect: messageData.showEffect || "fijo",
  window: messageData.window || 1
});
```

#### Backend (api_server.py)
```python
# 4. Procesamiento en el backend
@app.route('/panel/<int:panel_id>/message', methods=['POST'])
def send_message_to_panel(panel_id):
    # ... validación y procesamiento ...
    
    # 5. Llamada al servicio de comunicación
    result = panel_service.send_custom_text(
        panel_ip=panel.ip,
        text=message,
        color=color,
        font_size=font_size,
        effect=effect
    )
```

### Parámetros Enviados
- `panel_ip`: IP del panel específico
- `text`: Mensaje personalizado
- `color`: Código de color (1=Rojo, 2=Verde, 3=Amarillo)
- `font_size`: Tamaño de fuente (2=16px)
- `effect`: Efecto (2=fijo)

### Protocolo Utilizado
- **Función**: `send_custom_text()` de `PanelCommunicationService`
- **API Destino**: `http://localhost:8888/api/v1/panels/send`
- **Protocolo**: Detectado automáticamente por IP del panel

---

## 3. Flujo de Detalle de Parking (Actualización Manual de Aforo)

### Ubicación del Código
- **Frontend**: `client/src/pages/ParkingDetail.jsx`
- **Servicio**: `client/src/services/parkingService.js`
- **Backend**: `src/api_server.py` - Endpoint `/parking/<pid>/occupancy`

### Flujo Detallado

#### Frontend (ParkingDetail.jsx)
```javascript
// 1. Actualización manual de ocupación
const updateOccupancyMutation = useMutation(
  ({ occupancy }) => parkingService.updateOccupancy(id, occupancy)
);

// 2. Llamada al servicio
await parkingService.updateOccupancy(id, occupancy);
```

#### Servicio Frontend (parkingService.js)
```javascript
// 3. Envío al backend
async updateOccupancy(parkingId, occupancy) {
  const response = await api.post(`/parking/${parkingId}/occupancy`, { occupancy });
  return response.data;
}
```

#### Backend (api_server.py)
```python
# 4. Procesamiento en el backend
@app.route('/parking/<int:pid>/occupancy', methods=['POST'])
def set_occupancy(pid):
    # ... validación y actualización de ocupación ...
    
    # 5. Llamada a actualización de paneles
    update_parking_panels(pid, final_occupancy, final_free_spaces + final_occupancy, final_status)
```

### Parámetros Enviados
- `parking_id`: ID del parking
- `current_occupancy`: Nueva ocupación manual
- `max_capacity`: Capacidad máxima del parking
- `status`: Estado recalculado ('LIBRE', 'DENSO', 'COMPLETO')

### Protocolo Utilizado
- **Función**: `update_parking_panels()` de `panel_communication_service.py`
- **API Destino**: `http://localhost:8888/api/v1/panels/send`
- **Protocolo**: Detectado automáticamente por IP del panel

---

## 4. Flujo de Servicio de Programaciones

### Ubicación del Código
- **Monitor**: `src/schedule_monitor_service.py`
- **Servicio**: `src/panel_schedule_service.py`
- **Función**: `execute_schedule()` y `end_schedule()`

### Flujo Detallado

#### Monitor de Programaciones (schedule_monitor_service.py)
```python
# 1. Verificación periódica de programaciones
def _check_and_execute_schedules(self):
    # ... verificación de horarios ...
    
    # 2. Ejecución de programaciones activas
    execution_result = schedule_service.execute_schedule(schedule)
```

#### Servicio de Programaciones (panel_schedule_service.py)
```python
# 3. Ejecución de programación
def execute_schedule(self, schedule: PanelSchedule) -> dict:
    # ... obtención de paneles ...
    
    # 4. Envío a cada panel
    for panel in panels:
        result = self.panel_communication_service.send_custom_text(
            panel_ip=panel.panel_ip,
            text=schedule.message,
            color=schedule.color,
            font_size=schedule.font_size,
            effect=self._get_effect_code(schedule.effect)
        )

# 5. Finalización de programación (restauración de estado)
def end_schedule(self, schedule: PanelSchedule) -> dict:
    # ... cálculo de estado actual ...
    
    # 6. Envío de estado normal
    result = self.panel_communication_service.send_custom_text(
        panel_ip=panel.panel_ip,
        text=message,  # "LLIURE", "DENS", "COMPLET"
        color=color,
        font_size=16,
        effect=1
    )
```

### Parámetros Enviados
- **Ejecución**: Mensaje personalizado de la programación
- **Finalización**: Estado actual del parking ("LLIURE", "DENS", "COMPLET")
- `panel_ip`: IP del panel
- `color`: Código de color según estado
- `font_size`: Tamaño de fuente
- `effect`: Efecto de visualización

### Protocolo Utilizado
- **Función**: `send_custom_text()` de `PanelCommunicationService`
- **API Destino**: `http://localhost:8888/api/v1/panels/send`
- **Protocolo**: Detectado automáticamente por IP del panel

---

## Análisis de Consistencia

### ✅ Puntos de Consistencia

1. **API Unificada**: Todos los flujos usan la misma API `http://localhost:8888/api/v1/panels/send`

2. **Servicio Centralizado**: Todos los flujos utilizan `PanelCommunicationService` para la comunicación

3. **Detección Automática de Protocolo**: Todos los flujos detectan automáticamente el protocolo del panel por IP

4. **Formato de Payload Consistente**: Todos envían el mismo formato JSON:
```json
{
  "panels": [
    {
      "ip": "xxx.xxx.xxx.xxx",
      "port": 5200,
      "protocol": "old|new",
      "windows": [
        {
          "id": 0,
          "text": "MENSAJE",
          "color": 1,
          "fontSize": 2,
          "speed": 100,
          "effect": "fijo",
          "stayTime": 50,
          "alignmentH": 0,
          "alignmentV": 0
        }
      ]
    }
  ]
}
```

5. **Manejo de Errores**: Todos los flujos implementan manejo de errores y reintentos

### ⚠️ Diferencias Identificadas

1. **Formato de Mensaje**:
   - **Cámaras y Manual**: `"171/200 - LLIURE"` (ocupación + estado)
   - **Página Paneles**: Mensaje personalizado completo
   - **Programaciones**: Mensaje personalizado o estado según contexto

2. **Parámetros de Efecto**:
   - **Cámaras y Manual**: Efecto fijo (2)
   - **Página Paneles**: Efecto configurable
   - **Programaciones**: Efecto configurable en programación

3. **Colores**:
   - **Cámaras y Manual**: Color según estado (2=Verde, 3=Amarillo, 1=Rojo)
   - **Página Paneles**: Color seleccionable por usuario
   - **Programaciones**: Color configurado en programación

### 🔧 Recomendaciones de Mejora

1. **Unificar Formato de Mensaje**: Establecer un formato estándar para todos los flujos
2. **Documentar Parámetros**: Crear documentación clara de los códigos de color y efecto
3. **Validación Centralizada**: Implementar validación de parámetros en el servicio central
4. **Logging Unificado**: Estandarizar el formato de logs para todos los flujos

---

## Conclusión

**Todos los flujos utilizan correctamente las mismas llamadas y protocolos**. La arquitectura está bien diseñada con:

- ✅ **API unificada** para todos los paneles
- ✅ **Servicio centralizado** de comunicación
- ✅ **Detección automática** de protocolos
- ✅ **Formato consistente** de payload
- ✅ **Manejo de errores** estandarizado

Las diferencias identificadas son principalmente en el contenido del mensaje y parámetros específicos, pero la infraestructura de comunicación es consistente en todos los flujos.

**Estado**: ✅ **VALIDADO** - Todos los flujos usan las mismas llamadas y protocolos correctamente.

---

## Archivos Revisados

- `src/camera_server.py` - Flujo de cámaras
- `src/api_server.py` - Flujos de API (manual y paneles)
- `src/panel_communication_service.py` - Servicio central de comunicación
- `src/panel_schedule_service.py` - Servicio de programaciones
- `src/schedule_monitor_service.py` - Monitor de programaciones
- `client/src/pages/Panels.jsx` - Interfaz de paneles
- `client/src/pages/ParkingDetail.jsx` - Interfaz de detalle de parking
- `client/src/services/panelService.js` - Servicio frontend de paneles
- `client/src/services/parkingService.js` - Servicio frontend de parkings

---

*Documento generado el: 2025-07-04*
*Versión del sistema: v3.0.0* 