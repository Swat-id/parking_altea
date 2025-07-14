# Integración de Paneles - Parking Altea v3.1.0

## 📋 Resumen Ejecutivo

Este documento analiza y valida la integración completa del sistema Parking Altea con los paneles electrónicos LED a través del puerto 8888, siguiendo la API unificada descrita en la documentación técnica.

**ESTADO**: ✅ **INTEGRACIÓN CORRECTA** - Todos los flujos principales usan la API unificada correctamente.

## 🎯 API de Paneles - Configuración Base

### Servicio PanelSender
- **URL Base**: `http://localhost:8888`
- **Endpoint Principal**: `/api/v1/panels/send`
- **Protocolos Soportados**: Nuevo (v1.4.7) y Antiguo (v1.2.6)
- **Puerto Estándar**: 5200

### Estructura de Payload Estándar
```json
{
  "panels": [
    {
      "ip": "IP_DEL_PANEL",
      "port": 5200,
      "protocol": "new|old",
      "windows": [
        {
          "id": 0,
          "text": "TEXTO_A_ENVIAR",
          "color": 2,
          "fontSize": 2,
          "effect": "fijo|scroll",
          "stayTime": 50,
          "alignmentH": 1,
          "alignmentV": 1
        }
      ]
    }
  ]
}
```

## 🔄 Flujos de Integración Identificados

### 1. Flujo de Actualización por Cámaras

**Archivo**: `src/camera_server.py`  
**Línea**: 494  
**Función**: `update_parking_panels()`

**Proceso**:
1. Cámara envía datos de ocupación
2. Se actualiza la ocupación del parking
3. Se recalcula el estado (LIBRE/DENSO/COMPLETO)
4. Se llama a `update_parking_panels()` para actualizar paneles

**Integración**:
```python
# Línea 494 en camera_server.py
update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
```

**Estado**: ✅ **CORRECTO** - Usa la función correcta `update_parking_panels()`

### 2. Flujo de Actualización Manual de Ocupación

**Archivo**: `src/api_server.py`  
**Líneas**: 645, 728  
**Función**: `update_parking_panels()`

**Proceso**:
1. Usuario ajusta ocupación en frontend
2. API Server recibe POST `/parking/{id}/occupancy`
3. Validación de datos y permisos
4. Actualización en base de datos
5. Cálculo automático de estado
6. Envío a paneles vía `update_parking_panels()`
7. Respuesta con datos actualizados

**Integración**:
```python
# Línea 645 en api_server.py
update_parking_panels(pid, final_occupancy, final_max_capacity, final_status)

# Línea 728 en api_server.py
update_parking_panels(pid, p.current_occupancy, p.max_capacity, p.status)
```

**Estado**: ✅ **CORRECTO** - Usa la función correcta `update_parking_panels()`

### 3. Flujo de Envío Directo de Mensajes

**Archivo**: `src/api_server.py`  
**Líneas**: 1114, 1166  
**Función**: `PanelCommunicationService.send_custom_text()`

**Proceso**:
1. Usuario envía mensaje desde frontend
2. API Server recibe POST `/panel/{id}/message`
3. Validación de datos y permisos
4. Envío vía `PanelCommunicationService`
5. Respuesta con resultado del envío

**Integración**:
```python
# Línea 1114 en api_server.py
result = panel_service.send_custom_text(
    panel_ip=panel_ip,
    text=message,
    color=color,
    font_size=font_size_code,
    effect=showEffect
)
```

**Estado**: ✅ **CORRECTO** - Usa `PanelCommunicationService` correctamente

### 4. Flujo de Programaciones Automáticas

**Archivo**: `src/panel_schedule_service.py`  
**Líneas**: 330, 380  
**Función**: `PanelCommunicationService.send_custom_text()`

**Proceso**:
1. Schedule Monitor verifica programaciones activas
2. Ejecuta mensajes programados
3. Envía vía `PanelCommunicationService`
4. Registra ejecución en logs

**Integración**:
```python
# Línea 330 en panel_schedule_service.py
result = self.panel_communication_service.send_custom_text(
    panel_ip=panel.panel_ip,
    text=schedule.message,
    color=schedule.color,
    font_size=schedule.font_size,
    effect=self._get_effect_code(schedule.effect)
)
```

**Estado**: ✅ **CORRECTO** - Usa `PanelCommunicationService` correctamente

## 🔧 Servicios de Comunicación

### 1. PanelCommunicationService - ✅ CORRECTO

**Archivo**: `src/panel_communication_service.py`  
**Estado**: ✅ Implementado correctamente

**Características**:
- URL configurada: `http://localhost:8888/api/v1/panels/send`
- Consulta protocolo real del panel desde BD
- Usa la API unificada correctamente
- Estructura de payload estándar
- Manejo de protocolos (nuevo/antiguo)
- Manejo de errores robusto
- Logging detallado

**Métodos Principales**:
```python
class PanelCommunicationService:
    def send_custom_text(self, panel_ip, text, color, font_size, effect)
    def send_parking_status(self, panel_ip, parking_name, free_spaces, total_spaces, language_code)
    def test_connection(self)
```

### 2. update_parking_panels() - ✅ CORRECTO

**Archivo**: `src/panel_communication_service.py`  
**Línea**: 388  
**Estado**: ✅ Implementado correctamente

**Características**:
- Función unificada para actualización de paneles
- Usa la API unificada correctamente
- Manejo de múltiples paneles por parking
- Cálculo automático de mensajes según estado
- Manejo de errores robusto

**Uso**:
```python
update_parking_panels(parking_id, current_occupancy, max_capacity, status)
```

### 3. panel_client.py - ✅ CORRECTO

**Archivo**: `src/panel_client.py`  
**Estado**: ✅ Implementado correctamente

**Características**:
- URL configurada: `http://127.0.0.1:8888/api/v1/panels/send`
- Función `send_to_panels()` para múltiples paneles
- Función `broadcast()` para envío masivo
- Función `test_panel_api_connection()` para verificación

## 📊 Validación de Integración

### ✅ Configuración de URLs
- **PanelCommunicationService**: `http://localhost:8888/api/v1/panels/send`
- **panel_client.py**: `http://127.0.0.1:8888/api/v1/panels/send`
- **Consistencia**: ✅ URLs correctas y consistentes

### ✅ Estructura de Payload
- **Formato JSON**: ✅ Estándar según API
- **Campos requeridos**: ✅ Todos presentes
- **Protocolo dinámico**: ✅ Consulta desde BD
- **Puerto estándar**: ✅ 5200 configurado

### ✅ Manejo de Protocolos
- **Protocolo Antiguo (v1.2.6)**: ✅ Soportado
- **Protocolo Nuevo (v1.4.7)**: ✅ Soportado
- **Detección automática**: ✅ Por IP del panel
- **Fallback**: ✅ Protocolo antiguo por defecto

### ✅ Manejo de Errores
- **Timeouts**: ✅ Configurados (30s)
- **Reintentos**: ✅ 3 intentos
- **Logging**: ✅ Detallado
- **Respuestas**: ✅ Estructuradas

## 🎯 Flujos Validados

### ✅ Flujo 1: Recepción de Cámaras
```
Cámara → camera_server.py → update_parking_panels() → API 8888 → Panel LED
```

### ✅ Flujo 2: Actualización Manual
```
Frontend → api_server.py → update_parking_panels() → API 8888 → Panel LED
```

### ✅ Flujo 3: Mensajes Directos
```
Frontend → api_server.py → PanelCommunicationService → API 8888 → Panel LED
```

### ✅ Flujo 4: Programaciones
```
Schedule Monitor → panel_schedule_service.py → PanelCommunicationService → API 8888 → Panel LED
```

## 📋 Configuración de Producción

### Servicios Activos
- **parking-api.service**: Puerto 6001 (API REST)
- **parking-camera.service**: Puerto 6400 (Servidor de cámaras)
- **parking-schedule-monitor.service**: Monitor de programaciones
- **PanelSender Service**: Puerto 8888 (API de paneles)

### Variables de Entorno
```bash
DATABASE_URL=postgresql://postgres@localhost:5432/parking_altea
CAMERA_PORT=6400
API_PORT=6001
PANEL_API_URL=http://localhost:8888/api/v1/panels/send
```

## 🎯 Conclusiones

### ✅ Integración Correcta
- Todos los flujos principales usan la API unificada
- Configuración de URLs consistente
- Estructura de payload estándar
- Manejo de protocolos dinámico
- Manejo de errores robusto

### ✅ Funcionalidades Validadas
- Actualización automática por cámaras
- Actualización manual de ocupación
- Envío directo de mensajes
- Programaciones automáticas
- Verificación de conectividad

### ✅ Arquitectura Sólida
- Servicios bien separados
- Comunicación unificada
- Logging detallado
- Manejo de errores consistente

**El sistema está completamente integrado y funcionando correctamente con la API de paneles en el puerto 8888.** 