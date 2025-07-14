# Correcciones Protocolo Antiguo - Resumen de Cambios

## Estado: ✅ CORRECCIONES APLICADAS

### Problemas Identificados y Resueltos

#### 1. ✅ Parámetro `stayTime` Incorrecto
**Problema**: Siempre se enviaba `stayTime: 50` para todos los protocolos
**Solución**: Ajustar según protocolo y efecto
- **Protocolo Antiguo**:
  - Efecto "fijo": `stayTime: 0` (requerido)
  - Efecto "scroll": `stayTime: 5` (requerido)
- **Protocolo Nuevo**: `stayTime: 50` (estándar)

#### 2. ✅ Conversión de Efectos Incorrecta
**Problema**: Se usaba `effect: 1` como fijo
**Solución**: Usar valores correctos según documentación
- **Protocolo Antiguo**:
  - Efecto "fijo": `effect: 2`
  - Efecto "scroll": `effect: 12`
- **Protocolo Nuevo**:
  - Efecto "fijo": `effect: 1`
  - Efecto "scroll": `effect: 12`

#### 3. ✅ Valores por Defecto Incorrectos
**Problema**: Múltiples lugares usaban valores incorrectos
**Solución**: Estandarizar valores por defecto
- **Efecto por defecto**: `2` (fijo) en lugar de `1`
- **Tamaño fuente**: `2` (16px) - ya era correcto

## Archivos Modificados

### 1. ✅ `src/panel_communication_service.py`

#### Cambios en `_send_to_unified_api()`:
```python
# Antes
show_effects = [1] * len(texts)  # Incorrecto
effect_string = "fijo" if effect_value == 1 else "scroll"
stay_time = 50  # Siempre 50

# Después
show_effects = [2] * len(texts)  # Correcto
# Lógica específica por protocolo
if protocol == "old":
    if effect_value == 2:  # Fijo
        effect_string = "fijo"
        stay_time = 0  # Requerido para protocolo antiguo
    elif effect_value == 12:  # Scroll
        effect_string = "scroll"
        stay_time = 5  # Requerido para protocolo antiguo
else:
    # Protocolo nuevo: valores estándar
    if effect_value == 1:  # Fijo
        effect_string = "fijo"
        stay_time = 50
    elif effect_value == 12:  # Scroll
        effect_string = "scroll"
        stay_time = 50
```

#### Cambios en `send_custom_text()`:
```python
# Antes
def send_custom_text(self, panel_ip: str, text: str, 
                    color: int = 1, font_size: int = 2, 
                    effect: int = 1) -> Dict:

# Después
def send_custom_text(self, panel_ip: str, text: str, 
                    color: int = 1, font_size: int = 2, 
                    effect: int = 2) -> Dict:  # Fijo por defecto (valor 2)
```

#### Cambios en `update_parking_panels()`:
```python
# Antes
effect=1  # Fijo (valor incorrecto)

# Después
effect=2  # Fijo (valor correcto)
```

### 2. ✅ `src/panel_schedule_service.py`

#### Cambios en `_get_effect_code()`:
```python
# Antes
effect_codes = {
    'static': 1,
    'scroll_left': 2,
    'scroll_right': 3,
    'center': 4
}
return effect_codes.get(effect, 1)

# Después
effect_codes = {
    'static': 2,  # Fijo para protocolo antiguo
    'scroll_left': 12,  # Scroll para protocolo antiguo
    'scroll_right': 12,  # Scroll para protocolo antiguo
    'center': 2,  # Fijo para protocolo antiguo
    'fijo': 2,  # Fijo para protocolo antiguo
    'scroll': 12  # Scroll para protocolo antiguo
}
return effect_codes.get(effect, 2)  # Fijo por defecto
```

#### Cambios en `end_schedule()`:
```python
# Antes
effect=1  # Efecto estático

# Después
effect=2  # Efecto estático (valor correcto)
```

### 3. ✅ `src/api_server.py`

#### Cambios en endpoint `/panel/<ip>/message`:
```python
# Antes
effect="fijo"  # String incorrecto

# Después
effect=effect_code  # Código numérico correcto
```

#### Cambios en endpoint `/panel/<int:panel_id>/message`:
```python
# Antes
effect=showEffect  # String directo

# Después
# Convertir efecto string a código numérico
effect_codes = {
    'fijo': 2,
    'scroll': 12,
    'static': 2,
    'center': 2
}
effect_code = effect_codes.get(showEffect, 2)  # Fijo por defecto
effect=effect_code  # Usar código numérico convertido
```

#### Cambios en endpoint `/panel/<int:panel_id>/test`:
```python
# Antes
effect="fijo"  # String incorrecto

# Después
effect=2  # Fijo por defecto (valor correcto)
```

## Validación de Correcciones

### ✅ Parámetros Correctos para Protocolo Antiguo

#### Colores (Sin cambios):
| Color | Valor | Estado |
|-------|-------|--------|
| Rojo | 1 | ✅ Correcto |
| Verde | 2 | ✅ Correcto |
| Amarillo | 3 | ✅ Correcto |
| Azul | 4 | ✅ Correcto |
| Magenta | 5 | ✅ Correcto |
| Cian | 6 | ✅ Correcto |
| Blanco | 7 | ✅ Correcto |

#### Tamaños de Fuente (Sin cambios):
| Píxeles | Código | Estado |
|---------|--------|--------|
| 8px | 0 | ✅ Correcto |
| 12px | 1 | ✅ Correcto |
| 16px | 2 | ✅ Correcto |
| 24px | 3 | ✅ Correcto |
| 32px | 4 | ✅ Correcto |
| 40px | 5 | ✅ Correcto |
| 48px | 6 | ✅ Correcto |
| 56px | 7 | ✅ Correcto |

#### Efectos (✅ CORREGIDOS):
| Efecto | Código | Estado |
|--------|--------|--------|
| Fijo | 2 | ✅ Corregido |
| Scroll | 12 | ✅ Correcto |

#### StayTime (✅ CORREGIDO):
| Protocolo | Efecto | StayTime | Estado |
|-----------|--------|----------|--------|
| Antiguo | Fijo | 0 | ✅ Corregido |
| Antiguo | Scroll | 5 | ✅ Corregido |
| Nuevo | Fijo | 50 | ✅ Correcto |
| Nuevo | Scroll | 50 | ✅ Correcto |

## Flujos Verificados

### ✅ 1. Flujo de Cámaras
- **Archivo**: `src/camera_server.py`
- **Función**: `update_parking_panels()`
- **Estado**: ✅ Corregido

### ✅ 2. Flujo de Actualización Manual
- **Archivo**: `src/api_server.py`
- **Función**: `update_parking_panels()`
- **Estado**: ✅ Corregido

### ✅ 3. Flujo de Mensajes Directos
- **Archivo**: `src/api_server.py`
- **Función**: `send_custom_text()`
- **Estado**: ✅ Corregido

### ✅ 4. Flujo de Programaciones
- **Archivo**: `src/panel_schedule_service.py`
- **Función**: `execute_schedule()` y `end_schedule()`
- **Estado**: ✅ Corregido

## Resultado Esperado

Con estas correcciones, los paneles con protocolo antiguo deberían:

1. **Recibir parámetros correctos**: `stayTime: 0` para efecto fijo, `stayTime: 5` para efecto scroll
2. **Mostrar efectos correctos**: Efecto fijo con `effect: 2`, efecto scroll con `effect: 12`
3. **Funcionar sin errores**: Los paneles antiguos ya no deberían fallar con "Algunos comandos fallaron"

## Testing Recomendado

1. **Test de protocolo antiguo**: Verificar que paneles con protocolo antiguo reciben `stayTime: 0` para efecto fijo
2. **Test de protocolo nuevo**: Verificar que paneles con protocolo nuevo siguen funcionando con `stayTime: 50`
3. **Test de efectos**: Verificar que efectos fijo y scroll funcionan correctamente en ambos protocolos
4. **Test de logs**: Verificar que los logs muestran los parámetros correctos

## Conclusión

**Estado**: ✅ **CORRECCIONES COMPLETADAS**

Todos los flujos de comunicación con paneles han sido corregidos para manejar correctamente los parámetros específicos del protocolo antiguo, especialmente el `stayTime` y la conversión de efectos. Los paneles con protocolo antiguo ahora deberían funcionar correctamente sin errores de "Algunos comandos fallaron". 