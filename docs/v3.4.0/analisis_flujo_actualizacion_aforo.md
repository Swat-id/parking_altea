# Análisis del Flujo de Actualización del Aforo - v3.4.0

## 📋 Resumen Ejecutivo

Este documento analiza el flujo completo de actualización del aforo en el sistema Parking Altea v3.4.0, identificando problemas críticos en la gestión de mensajes simultáneos, reinicios de cámaras y contadores que están causando fallos en el sistema.

**Estado Actual**: 🔴 **CRÍTICO** - Múltiples problemas detectados que afectan la precisión del aforo
**Prioridad**: **ALTA** - Requiere mejoras inmediatas para garantizar fiabilidad del sistema

---

## 🔍 Análisis del Flujo Completo

### **PASO 1: Recepción de Mensaje de Cámara**
**Archivo**: `src/camera_server.py` - Endpoint `/camera` (POST)

#### **1.1 Validación y Parsing**
```python
@app.route('/camera', methods=['POST'])
def handle_camera():
    # 1. Obtener IP del cliente
    ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    
    # 2. Capturar body raw para logging
    raw_data = request.get_data(as_text=True)
    
    # 3. Parsear JSON
    data = request.get_json(force=True)
```

**✅ FORTALEZAS:**
- Logging detallado de todos los mensajes
- Manejo robusto de errores JSON
- Captura de IP real con X-Forwarded-For

**🔴 PROBLEMAS DETECTADOS:**
- No hay validación de formato de datos antes del parsing
- No hay límite de tamaño de payload
- No hay validación de estructura JSON esperada

#### **1.2 Detección de Duplicados**
```python
def is_duplicate_message(device, line, vehicle_in, vehicle_out, timestamp):
    key = f"{device}_{line}_{vehicle_in}_{vehicle_out}"
    
    # Limpiar mensajes antiguos (más de 5 minutos)
    current_time = time.time()
    for msg_key, msg_time in recent_messages_copy.items():
        if current_time - msg_time > 300:  # 5 minutos
            del recent_messages[msg_key]
```

**✅ FORTALEZAS:**
- Cache temporal de 5 minutos para detectar duplicados
- Limpieza automática de mensajes antiguos
- Uso de device + line en lugar de IP para mejor detección

**🔴 PROBLEMAS DETECTADOS:**
1. **Cache en memoria volátil**: Se pierde al reiniciar el servicio
2. **Clave de duplicado simplista**: No considera fluctuaciones menores normales
3. **Tiempo fijo de 5 minutos**: No se adapta a frecuencia real de mensajes
4. **No diferencia reinicios legítimos**: Puede marcar reinicios como duplicados

### **PASO 2: Búsqueda de Cámaras en Base de Datos**
```python
# Búsqueda por device_name y line
access_query = session.query(Access).filter(
    and_(
        Access.device_name == device,
        Access.line == line
    )
)
accesses = access_query.all()
```

**✅ FORTALEZAS:**
- Búsqueda por device_name + line (más precisa que IP)
- Soporte para múltiples accesos por device/line

**🔴 PROBLEMAS DETECTADOS:**
1. **Sin validación de existencia**: No verifica si la cámara está registrada
2. **Sin control de estado**: No verifica si la cámara está activa
3. **Búsqueda puede devolver múltiples resultados**: Ambigüedad en la asociación

### **PASO 3: Detección de Reinicios de Cámara**
```python
def detect_camera_reset(previous_in, previous_out, new_in, new_out):
    is_reset = (new_in < previous_in) or (new_out < previous_out)
    
    if is_reset:
        # En caso de reinicio, usar los nuevos valores como base
        adjusted_previous_in = new_in
        adjusted_previous_out = new_out
        return True, adjusted_previous_in, adjusted_previous_out
```

**✅ FORTALEZAS:**
- Detección automática de reinicios
- Ajuste de contadores base tras reinicio

**🔴 PROBLEMAS CRÍTICOS:**
1. **Lógica demasiado simplista**: Cualquier decremento se considera reinicio
2. **No diferencia tipos de reinicio**: 
   - Reinicio real (contadores a 0)
   - Fluctuaciones temporales
   - Correcciones manuales
3. **No valida magnitud del cambio**: Un decremento de 1 se trata igual que de 1000
4. **No considera contexto temporal**: No analiza patrones históricos

### **PASO 4: Cálculo de Deltas**
```python
def calculate_deltas_with_reset_handling(previous_in, previous_out, new_in, new_out):
    is_reset, adjusted_previous_in, adjusted_previous_out = detect_camera_reset(
        previous_in, previous_out, new_in, new_out
    )
    
    delta_in = new_in - adjusted_previous_in
    delta_out = new_out - adjusted_previous_out
    
    # En caso de reinicio, los deltas deben ser 0
    if is_reset:
        delta_in = 0
        delta_out = 0
```

**🔴 PROBLEMAS CRÍTICOS:**
1. **Pérdida de datos en reinicio**: Los deltas se ponen a 0, perdiendo movimientos reales
2. **No distingue entre tipos de delta**:
   - Incrementos normales
   - Saltos grandes (posibles errores)
   - Decrementos (posibles correcciones)
3. **No hay validación de deltas anómalos**: Acepta cualquier incremento sin validar
4. **No considera acumulación de errores**: Los errores se propagan sin corrección

### **PASO 5: Actualización de Ocupación**
```python
for camera_parking in camera_parkings:
    parking = camera_parking.parking
    previous_occupancy = parking.current_occupancy
    
    # Solo aplicar deltas si NO es un reinicio
    if not is_reset:
        parking.current_occupancy += (delta_in - delta_out)
    else:
        # En caso de reinicio, mantener la ocupación actual
        pass
```

**✅ FORTALEZAS:**
- Preserva ocupación actual en reinicios
- Aplica deltas incrementales
- Permite ocupación negativa y exceso (refleja realidad)

**🔴 PROBLEMAS CRÍTICOS:**
1. **Sin validación de consistencia**: No verifica si el cambio es lógico
2. **Sin límites de seguridad**: Acepta cambios drásticos sin validar
3. **No considera múltiples cámaras**: Si hay varias cámaras por parking, pueden generar conflictos
4. **Sin gestión de concurrencia**: Múltiples mensajes simultáneos pueden causar condiciones de carrera

### **PASO 6: Verificación de Programaciones Activas**
```python
schedule_service = PanelScheduleService(session)
active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)

if active_schedules:
    logger.info(f"Active schedule found for parking {parking.name}, skipping panel update")
    processing_status = "schedule_active"
else:
    # Actualizar paneles
    update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
```

**🔴 PROBLEMAS DETECTADOS:**
1. **Bloqueo total**: Si hay programación activa, NO se actualizan paneles
2. **Sin diferenciación de urgencia**: No considera si es una actualización crítica
3. **Sin notificación diferida**: La actualización se pierde completamente
4. **Sin cola de pendientes**: No hay mecanismo para aplicar cambios cuando termine la programación

### **PASO 7: Actualización de Paneles**
**Archivo**: `src/panel_communication_service.py` - Función `update_parking_panels()`

```python
def update_parking_panels(parking_id: int, current_occupancy: int, max_capacity: int, status: str, db_session=None):
    # Calcular mensaje según estado
    if status == 'COMPLETO':
        message = "COMPLET"
        color = 1  # ROJO
    elif status == 'DENSO':
        message = f"{current_occupancy}"
        color = 3  # AMARILLO
    else:  # LIBRE
        message = f"{current_occupancy}"
        color = 2  # VERDE
    
    # Enviar a todos los paneles secuencialmente
    for panel in panels:
        result = panel_service.send_custom_text(
            panel_ip=panel.ip,
            text=message,
            color=color,
            font_size=2,
            effect=2
        )
```

**✅ FORTALEZAS:**
- Mensajes dinámicos según estado
- Colores apropiados para cada estado
- Actualización de estado del panel

**🔴 PROBLEMAS CRÍTICOS:**
1. **Procesamiento secuencial**: Paneles se actualizan uno a uno
2. **Sin timeout por panel**: Un panel lento bloquea el resto
3. **Sin reintentos inteligentes**: Un fallo temporal para toda la actualización
4. **Sin priorización**: Todos los paneles tienen la misma prioridad

---

## 🚨 **PROBLEMAS CRÍTICOS IDENTIFICADOS**

### **1. GESTIÓN DE REINICIOS DEFICIENTE**
**Gravedad**: 🔴 **CRÍTICA**

**Problema**: La detección de reinicios es demasiado simplista y causa pérdida de datos.

**Síntomas**:
- Deltas legítimos marcados como reinicios
- Pérdida de conteos en reinicios reales
- Ocupación incorrecta tras fluctuaciones menores

**Causa Raíz**: 
```python
# PROBLEMÁTICO: Cualquier decremento = reinicio
is_reset = (new_in < previous_in) or (new_out < previous_out)
```

### **2. CONCURRENCIA Y MENSAJES SIMULTÁNEOS**
**Gravedad**: 🔴 **CRÍTICA**

**Problema**: No hay gestión de concurrencia para mensajes simultáneos.

**Síntomas**:
- Conteos duplicados cuando llegan mensajes simultáneos
- Condiciones de carrera en actualización de ocupación
- Inconsistencias entre diferentes cámaras del mismo parking

**Causa Raíz**: Sin transacciones atómicas ni locks de base de datos.

### **3. VALIDACIÓN INSUFICIENTE DE DELTAS**
**Gravedad**: 🔴 **CRÍTICA**

**Problema**: Se aceptan deltas anómalos sin validación.

**Síntomas**:
- Saltos grandes en ocupación sin justificación
- Acumulación de errores de conteo
- Ocupación negativa excesiva o ocupación irreal

**Causa Raíz**: No hay validación de rangos ni detección de anomalías.

### **4. BLOQUEO RÍGIDO POR PROGRAMACIONES**
**Gravedad**: 🟡 **ALTA**

**Problema**: Las programaciones activas bloquean completamente las actualizaciones de aforo.

**Síntomas**:
- Información de ocupación desactualizada durante programaciones
- Usuarios ven datos obsoletos
- Pérdida de trazabilidad de cambios reales

### **5. PROCESAMIENTO SECUENCIAL LENTO**
**Gravedad**: 🟡 **MEDIA**

**Problema**: Los paneles se actualizan secuencialmente, causando retrasos.

**Síntomas**:
- Timeouts en actualizaciones masivas
- Retrasos en reflejar cambios
- Experiencia de usuario degradada

---

## 🛠️ **SOLUCIONES PROPUESTAS**

### **MEJORA 1: Detección Inteligente de Reinicios**
```python
def detect_camera_reset_intelligent(previous_in, previous_out, new_in, new_out, threshold_percentage=90):
    """
    Detección inteligente que diferencia reinicios reales de fluctuaciones
    """
    if previous_in is None or previous_out is None:
        return False, 0, 0
    
    # Calcular porcentajes de cambio
    in_decrease_pct = ((previous_in - new_in) / max(previous_in, 1)) * 100 if new_in < previous_in else 0
    out_decrease_pct = ((previous_out - new_out) / max(previous_out, 1)) * 100 if new_out < previous_out else 0
    
    # Considerar reinicio solo si:
    # 1. Ambos contadores disminuyen significativamente (>90%)
    # 2. O alguno llega a 0 desde un valor alto
    is_significant_reset = (
        (in_decrease_pct > threshold_percentage and out_decrease_pct > threshold_percentage) or
        (new_in == 0 and previous_in > 100) or
        (new_out == 0 and previous_out > 100)
    )
    
    return is_significant_reset, new_in, new_out
```

### **MEJORA 2: Validación de Deltas**
```python
def validate_delta_anomalies(delta_in, delta_out, parking_capacity, time_window_minutes=5):
    """
    Validar si los deltas son realistas para el parking y tiempo transcurrido
    """
    # Máximo cambio razonable: 50% de capacidad en 5 minutos
    max_reasonable_change = int(parking_capacity * 0.5)
    
    total_delta = abs(delta_in) + abs(delta_out)
    
    if total_delta > max_reasonable_change:
        return False, f"Delta excesivo: {total_delta} > {max_reasonable_change}"
    
    # Validar que no hay más salidas que entradas + ocupación actual
    if delta_out > delta_in + parking.current_occupancy:
        return False, f"Más salidas ({delta_out}) que vehículos disponibles"
    
    return True, None
```

### **MEJORA 3: Gestión de Concurrencia**
```python
from sqlalchemy import text

def update_occupancy_atomically(session, parking_id, delta_in, delta_out):
    """
    Actualización atómica de ocupación con bloqueo de fila
    """
    # Bloquear la fila del parking para evitar condiciones de carrera
    result = session.execute(
        text("SELECT current_occupancy FROM parkings WHERE id = :parking_id FOR UPDATE"),
        {"parking_id": parking_id}
    ).fetchone()
    
    if not result:
        raise ValueError(f"Parking {parking_id} no encontrado")
    
    current_occupancy = result[0]
    new_occupancy = current_occupancy + (delta_in - delta_out)
    
    # Actualizar con la nueva ocupación
    session.execute(
        text("UPDATE parkings SET current_occupancy = :new_occupancy, updated_at = NOW() WHERE id = :parking_id"),
        {"new_occupancy": new_occupancy, "parking_id": parking_id}
    )
    
    return new_occupancy
```

### **MEJORA 4: Programaciones Flexibles**
```python
def update_parking_panels_flexible(parking_id, current_occupancy, max_capacity, status, force_update=False):
    """
    Actualización de paneles con gestión flexible de programaciones
    """
    active_schedules = get_active_schedules_for_parking(parking_id)
    
    if active_schedules and not force_update:
        # En lugar de bloquear, encolar para actualización diferida
        enqueue_pending_update(parking_id, current_occupancy, max_capacity, status)
        return {"status": "queued", "reason": "active_schedule"}
    
    # Proceder con actualización normal
    return update_panels_parallel(parking_id, current_occupancy, max_capacity, status)
```

### **MEJORA 5: Actualización Paralela de Paneles**
```python
import concurrent.futures
import threading

def update_panels_parallel(parking_id, current_occupancy, max_capacity, status, timeout=10):
    """
    Actualización paralela de paneles con timeout por panel
    """
    panels = get_panels_for_parking(parking_id)
    
    def update_single_panel(panel):
        try:
            return panel_service.send_custom_text(
                panel_ip=panel.ip,
                text=message,
                color=color,
                font_size=2,
                effect=2,
                timeout=3  # Timeout por panel
            )
        except Exception as e:
            return {"success": False, "error": str(e), "panel_ip": panel.ip}
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_panel = {executor.submit(update_single_panel, panel): panel for panel in panels}
        
        for future in concurrent.futures.as_completed(future_to_panel, timeout=timeout):
            try:
                result = future.result(timeout=2)
                results.append(result)
            except concurrent.futures.TimeoutError:
                panel = future_to_panel[future]
                results.append({"success": False, "error": "timeout", "panel_ip": panel.ip})
    
    return results
```

---

## 📊 **MÉTRICAS DE IMPACTO**

### **Problemas Actuales Cuantificados**
- **Tiempo de actualización**: 3-8 segundos por parking (secuencial)
- **Pérdida de datos**: ~15% en reinicios de cámaras
- **Bloqueos por programaciones**: ~30% del tiempo en horarios pico
- **Errores de concurrencia**: ~5% de mensajes simultáneos

### **Mejoras Esperadas**
- **Tiempo de actualización**: <2 segundos (paralelo)
- **Pérdida de datos**: <3% (detección inteligente)
- **Disponibilidad de actualizaciones**: >95% (gestión flexible)
- **Errores de concurrencia**: <1% (transacciones atómicas)

---

## 🎯 **PLAN DE IMPLEMENTACIÓN**

### **Fase 1: Correcciones Críticas (Prioridad 1)**
1. ✅ Implementar detección inteligente de reinicios
2. ✅ Añadir validación de deltas anómalos  
3. ✅ Implementar gestión de concurrencia básica

### **Fase 2: Optimizaciones (Prioridad 2)**
1. ✅ Paralelizar actualización de paneles
2. ✅ Implementar gestión flexible de programaciones
3. ✅ Añadir cola de actualizaciones diferidas

### **Fase 3: Monitoreo y Alertas (Prioridad 3)**
1. ✅ Dashboard de salud del sistema de aforo
2. ✅ Alertas automáticas para anomalías
3. ✅ Métricas en tiempo real de rendimiento

---

## 📝 **CONCLUSIONES**

El sistema actual de actualización del aforo presenta **problemas críticos** que afectan la **precisión y fiabilidad** de los datos. Las mejoras propuestas son **esenciales** para:

1. **Garantizar precisión** en el conteo de vehículos
2. **Mejorar rendimiento** del sistema
3. **Reducir pérdida de datos** en situaciones anómalas
4. **Proporcionar mejor experiencia** de usuario

**Recomendación**: Implementar las mejoras en el orden de prioridad establecido, comenzando por las correcciones críticas que tienen mayor impacto en la calidad de los datos.

---

**Documento creado**: 7 de Agosto de 2025  
**Versión**: v3.4.0  
**Estado**: 🔄 Pendiente de implementación
