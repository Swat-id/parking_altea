# Backup del Estado Actual - Camera Server v4.0.0

## 📋 Información del Documento

- **Rama**: v4.0.0
- **Fecha**: 12 de septiembre de 2025
- **Propósito**: Documentación del estado actual del servicio de cámaras ANTES de implementar nueva lógica de cálculo de deltas
- **Estado**: Backup completo para rollback

---

## 🎯 Resumen del Estado Actual

Este documento registra el estado exacto del servicio de cámaras antes de implementar los cambios propuestos en `analisis_nueva_logica_calculo_deltas.md`. Permite hacer rollback completo en caso de problemas.

---

## 📁 Archivos Principales Afectados

### 1. `src/camera_server.py` (Archivo Principal)
- **Líneas críticas**: 111-181 (funciones de cálculo de deltas)
- **Funciones principales**:
  - `detect_camera_reset()` (líneas 111-136)
  - `calculate_deltas_with_reset_handling()` (líneas 138-181)
  - `handle_camera()` (líneas 183-585) - lógica principal

### 2. Archivos de Soporte (si existen)
- `src/camera_detection_methods.py`
- `src/camera_message_processor.py` 
- `src/camera_atomic_operations.py`

---

## 🔧 Lógica Actual de Cálculo de Deltas

### Función: `detect_camera_reset()`

```python
def detect_camera_reset(previous_in, previous_out, new_in, new_out):
    """
    Detectar si la cámara se ha reiniciado basándose en los contadores.
    
    UNIFICACIÓN: Lógica mejorada para reinicios que evita cálculos incorrectos
    """
    # Si es la primera vez (contadores anteriores son None), no es reinicio
    if previous_in is None or previous_out is None:
        return False, 0, 0
    
    # Detectar reinicio: nuevos contadores son menores que los anteriores
    # Esto incluye cuando uno o ambos contadores van a 0
    is_reset = (new_in < previous_in) or (new_out < previous_out)
    
    if is_reset:
        logger.info(f"CAMERA RESET DETECTED - Previous: In={previous_in}, Out={previous_out} -> New: In={new_in}, Out={new_out}")
        
        # UNIFICACIÓN: En caso de reinicio, usar los nuevos valores como base
        # No ajustar a 0, sino usar los nuevos valores directamente
        adjusted_previous_in = new_in
        adjusted_previous_out = new_out
        
        logger.info(f"Reset adjustment - Using new values as base: In={adjusted_previous_in}, Out={adjusted_previous_out}")
        return True, adjusted_previous_in, adjusted_previous_out
    
    return False, previous_in, previous_out
```

### Función: `calculate_deltas_with_reset_handling()`

```python
def calculate_deltas_with_reset_handling(previous_in, previous_out, new_in, new_out):
    """
    Calcular deltas considerando posibles reinicios de cámara.
    
    UNIFICACIÓN: Lógica mejorada para evitar cálculos incorrectos
    """
    # Detectar si hay reinicio
    is_reset, adjusted_previous_in, adjusted_previous_out = detect_camera_reset(
        previous_in, previous_out, new_in, new_out
    )
    
    # Calcular deltas usando los contadores ajustados
    delta_in = new_in - adjusted_previous_in
    delta_out = new_out - adjusted_previous_out
    
    # UNIFICACIÓN: En caso de reinicio, los deltas deben ser 0
    # porque estamos usando los nuevos valores como base
    if is_reset:
        delta_in = 0
        delta_out = 0
        logger.info(f"Reset detected - Setting deltas to 0 to avoid incorrect calculations")
    
    # Validar que los deltas sean positivos (excepto en reinicios)
    if not is_reset:
        if delta_in < 0:
            logger.warning(f"Negative delta_in detected (non-reset): {delta_in}. Setting to 0.")
            delta_in = 0
        if delta_out < 0:
            logger.warning(f"Negative delta_out detected (non-reset): {delta_out}. Setting to 0.")
            delta_out = 0
    
    reset_info = {
        "is_reset": is_reset,
        "previous_in": previous_in,
        "previous_out": previous_out,
        "adjusted_previous_in": adjusted_previous_in,
        "adjusted_previous_out": adjusted_previous_out,
        "new_in": new_in,
        "new_out": new_out
    }
    
    logger.info(f"Deltas calculated - Delta In: {delta_in}, Delta Out: {delta_out}, Reset: {is_reset}")
    
    return delta_in, delta_out, is_reset, reset_info
```

---

## 🔄 Flujo Actual de Procesamiento

### Orden de Operaciones (ACTUAL):
1. **Recepción del mensaje** con `vehicle_in` y `vehicle_out`
2. **Obtención de valores anteriores** desde la base de datos
3. **Cálculo de deltas** usando `calculate_deltas_with_reset_handling()`
4. **Actualización de contadores** en BD (líneas 408-413)
5. **Aplicación al aforo** usando deltas calculados (líneas 426-434)

### Código Crítico de Aplicación de Deltas:

```python
# Líneas 426-434 en handle_camera()
if not is_reset:
    # Aplicar el delta de esta cámara al parking
    parking.current_occupancy += (delta_in - delta_out)
    logger.info(f"Occupancy updated for parking {parking.name} - Previous: {previous_occupancy}, Delta applied: +{delta_in} -{delta_out} = {delta_in - delta_out}, New: {parking.current_occupancy}")
else:
    # En caso de reinicio, mantener la ocupación actual
    logger.info(f"Reset detected for parking {parking.name} - Keeping current occupancy: {parking.current_occupancy}")
```

---

## 📊 Comportamiento Actual por Casos

### Caso 1: Funcionamiento Normal
- **Input**: `previous_in=100, previous_out=80, new_in=105, new_out=83`
- **Resultado**: `delta_in=5, delta_out=3, delta_final=2`
- **Ocupación**: `+2 vehículos`

### Caso 2: Mensaje Duplicado
- **Input**: `previous_in=105, previous_out=83, new_in=105, new_out=83`
- **Resultado**: Detectado por `is_duplicate_message()` antes de calcular deltas
- **Ocupación**: Sin cambio

### Caso 3: Reinicio de Cámara
- **Input**: `previous_in=1400, previous_out=1370, new_in=5, new_out=2`
- **Resultado**: `is_reset=True, delta_in=0, delta_out=0`
- **Ocupación**: Sin cambio (mantiene ocupación actual)

---

## 🗃️ Base de Datos - Orden de Operaciones

### Secuencia Actual:
```sql
-- 1. Leer valores anteriores
SELECT last_vehicle_in, last_vehicle_out FROM accesses WHERE ...;

-- 2. Calcular deltas usando valores leídos

-- 3. Actualizar contadores (líneas 408-413)
UPDATE accesses SET 
    last_vehicle_in = ?, 
    last_vehicle_out = ?,
    status = 'ONLINE',
    last_message_received = ?
WHERE ...;

-- 4. Aplicar deltas a ocupación (líneas 426-434)
UPDATE parkings SET current_occupancy = current_occupancy + ? WHERE ...;
```

---

## ⚠️ Puntos Críticos para Rollback

### Funciones que CAMBIARÁN:
1. `detect_camera_reset()` - Nueva lógica de detección
2. `calculate_deltas_with_reset_handling()` - Cálculo unificado
3. Orden de operaciones en `handle_camera()` - Almacenamiento inmediato

### Funciones que NO CAMBIARÁN:
1. `is_duplicate_message()` - Detección de duplicados por cache
2. `log_camera_message()` - Logging de eventos
3. `CameraMonitor` - Monitor de estado de cámaras

### Variables de Entorno/Configuración:
- No hay variables de configuración específicas para la lógica de deltas
- La configuración está hardcodeada en las funciones

---

## 🔄 Procedimiento de Rollback

### Paso 1: Restaurar Funciones Originales
```bash
# Desde este backup, copiar las funciones originales:
# - detect_camera_reset() (líneas 111-136)
# - calculate_deltas_with_reset_handling() (líneas 138-181)
```

### Paso 2: Verificar Orden de Operaciones
```python
# Asegurar que el orden sea:
# 1. Leer BD
# 2. Calcular deltas  
# 3. Escribir BD
# 4. Aplicar al aforo
```

### Paso 3: Validar Comportamiento de Reinicios
```python
# Comportamiento original en reinicios:
# - delta_in = 0
# - delta_out = 0  
# - Ocupación sin cambio
```

---

## 📝 Casos de Test para Validación

### Test 1: Funcionamiento Normal
```python
assert calculate_deltas_with_reset_handling(100, 80, 105, 83) == (5, 3, False, reset_info)
```

### Test 2: Reinicio Detectado
```python
assert calculate_deltas_with_reset_handling(1400, 1370, 5, 2) == (0, 0, True, reset_info)
```

### Test 3: Valores Negativos (No Reinicio)
```python
# Delta negativo debe convertirse a 0
assert calculate_deltas_with_reset_handling(100, 80, 95, 85) == (0, 0, False, reset_info)
```

---

## 🚨 Señales de Alerta para Rollback

### Indicadores de Problemas:
1. **Ocupación errática**: Cambios bruscos no justificados
2. **Deltas excesivos**: Valores superiores a umbrales normales
3. **Reinicios mal procesados**: Cambios de ocupación en reinicios
4. **Logs de error**: Incremento significativo en errores de cálculo

### Métricas a Monitorizar:
- Número de reinicios detectados por hora
- Magnitud promedio de deltas
- Frecuencia de ocupaciones negativas o excesivas
- Tiempo de respuesta del servicio

---

## 📚 Referencias del Estado Actual

### Archivos de Código:
- **Principal**: `src/camera_server.py` (693 líneas)
- **Funciones críticas**: Líneas 111-181, 183-585

### Documentación Relacionada:
- `docs/v4.0.0/analisis_nueva_logica_calculo_deltas.md` - Especificación de cambios
- `docs/cameras.md` - Documentación general de cámaras

### Tests Existentes:
- Revisar `test/test_delta_calculation.py` si existe
- Tests de integración en `test/`

---

## ✅ Checklist de Rollback

- [ ] Restaurar función `detect_camera_reset()`
- [ ] Restaurar función `calculate_deltas_with_reset_handling()`
- [ ] Verificar orden de operaciones en `handle_camera()`
- [ ] Ejecutar tests de regresión
- [ ] Monitorizar métricas durante 24h
- [ ] Validar comportamiento con datos reales

---

*Backup creado el 12 de septiembre de 2025*
*Estado: Código actual documentado - Listo para implementación*
