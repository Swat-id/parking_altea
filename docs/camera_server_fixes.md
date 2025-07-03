# Correcciones en Camera Server - Problemas Identificados y Soluciones

## Resumen de Problemas Identificados

### 1. **Identificación Incorrecta de Cámaras**
**Problema**: El sistema identificaba las cámaras por IP + línea, pero según el contexto debe ser por **device + línea**.

**Impacto**: 
- Las cámaras no se identificaban correctamente cuando cambiaba su IP
- Mensajes de cámara se perdían o se procesaban incorrectamente

**Solución Aplicada**:
```python
# ANTES: Identificación por IP + línea
access = session.query(Access).filter_by(ip=ip, line=line).first()

# DESPUÉS: Identificación por device + línea (principal)
access = session.query(Access).filter(
    func.lower(Access.name) == func.lower(device),
    Access.line == line
).first()

# Fallback a IP + línea si no se encuentra por device
if not access:
    access = session.query(Access).filter_by(ip=ip, line=line).first()
```

### 2. **Detección de Duplicados Incorrecta**
**Problema**: Los duplicados se detectaban por IP + línea, pero deben detectarse por **valores de contadores**.

**Impacto**:
- Mensajes duplicados se procesaban múltiples veces
- Ocupación se incrementaba incorrectamente

**Solución Aplicada**:
```python
# ANTES: Detección por IP + línea
def is_duplicate_message(camera_ip, camera_line, vehicle_in, vehicle_out, timestamp):
    key = f"{camera_ip}_{camera_line}_{vehicle_in}_{vehicle_out}"

# DESPUÉS: Detección por device + línea + contadores
def is_duplicate_message(device, line, vehicle_in, vehicle_out, timestamp):
    key = f"{device}_{line}_{vehicle_in}_{vehicle_out}"
```

### 3. **Cálculo Incorrecto de Ocupación**
**Problema**: El cálculo de ocupación tenía errores lógicos que causaban descuadres.

**Ejemplo del Problema**:
```
Contadores: In:132 Out:122 → Ocupación: 119
Siguiente mensaje: In:134 Out:123
Cálculo incorrecto: +2 entradas, +1 salida = +1 neto → Ocupación: 120
Cálculo correcto: +2 entradas, +1 salida = +1 neto → Ocupación: 120 ✅
```

**Solución Aplicada**:
```python
# CORRECCIÓN: Actualizar contadores ANTES de calcular ocupación
access.last_vehicle_in = veh_in
access.last_vehicle_out = veh_out

# Solo aplicar deltas si NO es un reinicio
if not is_reset:
    parking.current_occupancy += (delta_in - delta_out)
    logger.info(f"Occupancy updated - Previous: {previous_occupancy}, Delta: +{delta_in} -{delta_out} = {delta_in - delta_out}, New: {parking.current_occupancy}")
else:
    # En caso de reinicio, mantener la ocupación actual
    logger.info(f"Reset detected - Keeping current occupancy: {parking.current_occupancy}")
```

### 4. **Lógica de Reinicios Incorrecta**
**Problema**: En caso de reinicio de cámara, se ajustaban los contadores anteriores a 0, causando cálculos incorrectos.

**Ejemplo del Problema**:
```
Contadores anteriores: In:120, Out:100
Reinicio: In:2, Out:1
Cálculo incorrecto: Delta In = 2-0 = 2, Delta Out = 1-0 = 1 → +1 neto
Cálculo correcto: Es un reinicio, no aplicar deltas → +0 neto
```

**Solución Aplicada**:
```python
def detect_camera_reset(previous_in, previous_out, new_in, new_out):
    # Detectar reinicio: nuevos contadores son menores que los anteriores
    is_reset = (new_in < previous_in) or (new_out < previous_out)
    
    if is_reset:
        # CORRECCIÓN: Usar los nuevos valores como base
        adjusted_previous_in = new_in
        adjusted_previous_out = new_out
        return True, adjusted_previous_in, adjusted_previous_out
    
    return False, previous_in, previous_out

def calculate_deltas_with_reset_handling(previous_in, previous_out, new_in, new_out):
    # ... código de detección ...
    
    # CORRECCIÓN: En caso de reinicio, los deltas deben ser 0
    if is_reset:
        delta_in = 0
        delta_out = 0
        logger.info(f"Reset detected - Setting deltas to 0 to avoid incorrect calculations")
```

## Archivos Modificados

### 1. `src/camera_server_fixed.py`
- **Nuevo archivo** con todas las correcciones aplicadas
- **Reemplaza** `src/camera_server.py` en producción

### 2. `docs/workflow_aforo.md`
- **Actualizado** con la información real del sistema
- **Documenta** el flujo correcto de cámara a panel

## Verificación de Correcciones

### 1. **Test de Identificación**
```bash
# Simular mensaje de cámara con device + línea
curl -X POST http://localhost:6400/camera \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -d '{
    "device": "RENFE1 camera 1",
    "line": 0,
    "Vehicle In": 134,
    "Vehicle Out": 123
  }'
```

### 2. **Test de Duplicados**
```bash
# Enviar el mismo mensaje dos veces
# El segundo debe ser detectado como duplicado y ignorado
```

### 3. **Test de Reinicio**
```bash
# Simular reinicio de cámara
curl -X POST http://localhost:6400/camera \
  -H "Content-Type: application/json" \
  -d '{
    "device": "RENFE1 camera 1",
    "line": 0,
    "Vehicle In": 2,    # Menor que el anterior (134)
    "Vehicle Out": 1    # Menor que el anterior (123)
  }'
```

## Instrucciones de Despliegue

### 1. **Backup del Archivo Original**
```bash
cp src/camera_server.py src/camera_server_backup.py
```

### 2. **Reemplazar con Versión Corregida**
```bash
cp src/camera_server_fixed.py src/camera_server.py
```

### 3. **Reiniciar Servicio**
```bash
systemctl restart parking-camera
```

### 4. **Verificar Funcionamiento**
```bash
# Verificar logs
tail -f /var/log/parking-camera.log

# Verificar estado del servicio
systemctl status parking-camera
```

## Monitoreo Post-Despliegue

### 1. **Métricas a Observar**
- **Tasa de duplicados detectados**: Debe aumentar
- **Errores de identificación**: Debe disminuir
- **Descuadres de ocupación**: Debe estabilizarse
- **Tiempo de procesamiento**: Debe mantenerse estable

### 2. **Logs a Revisar**
```bash
# Buscar mensajes de reinicio
grep "CAMERA RESET" /var/log/parking-camera.log

# Buscar duplicados detectados
grep "DUPLICATE MESSAGE" /var/log/parking-camera.log

# Buscar errores de identificación
grep "Device not found" /var/log/parking-camera.log
```

### 3. **Validación de Base de Datos**
```sql
-- Verificar ocupación actual vs contadores
SELECT 
    p.name,
    p.current_occupancy,
    a.last_vehicle_in,
    a.last_vehicle_out,
    (a.last_vehicle_in - a.last_vehicle_out) as calculated_occupancy,
    ABS(p.current_occupancy - (a.last_vehicle_in - a.last_vehicle_out)) as discrepancy
FROM parkings p
JOIN accesses a ON a.parking_id = p.id
ORDER BY discrepancy DESC;
```

## Rollback Plan

Si se detectan problemas después del despliegue:

```bash
# Restaurar versión anterior
cp src/camera_server_backup.py src/camera_server.py

# Reiniciar servicio
systemctl restart parking-camera

# Verificar funcionamiento
systemctl status parking-camera
```

## Conclusión

Estas correcciones abordan los problemas fundamentales identificados:

1. ✅ **Identificación correcta** por device + línea
2. ✅ **Detección de duplicados** por valores de contadores
3. ✅ **Cálculo correcto** de ocupación
4. ✅ **Manejo adecuado** de reinicios de cámara

El sistema ahora debería funcionar de manera más estable y precisa, reduciendo significativamente los descuadres de ocupación. 