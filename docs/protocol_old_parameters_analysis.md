# Análisis de Parámetros para Protocolo Antiguo (v1.2.6)

## Resumen Ejecutivo

Este documento analiza en detalle cómo se gestionan los parámetros (color, tamaño, efecto) para el protocolo antiguo en todas las llamadas a la API, identificando inconsistencias y proponiendo correcciones.

## 1. Parámetros Según Documentación

### 1.1 Colores (Protocolo Antiguo)
| Color | Valor | Descripción |
|-------|-------|-------------|
| 1 | Rojo | Color rojo |
| 2 | Verde | Color verde |
| 3 | Amarillo | Color amarillo |
| 4 | Azul | Color azul |
| 5 | Magenta | Color magenta |
| 6 | Cian | Color cian |
| 7 | Blanco | Color blanco |

### 1.2 Tamaños de Fuente (Protocolo Antiguo)
| Valor | Tamaño (píxeles) | Descripción |
|-------|------------------|-------------|
| 0 | 8 | Fuente pequeña |
| 1 | 12 | Fuente mediana |
| **2** | **16** | **Fuente estándar** |
| 3 | 24 | Fuente grande |
| 4 | 32 | Fuente extra grande |
| 5 | 40 | Fuente muy grande |
| 6 | 48 | Fuente enorme |
| 7 | 56 | Fuente máxima |

### 1.3 Efectos (Protocolo Antiguo)
| Efecto | Valor | Descripción |
|--------|-------|-------------|
| "fijo" | 2 | Texto estático sin movimiento |
| "scroll" | 12 | Texto con desplazamiento |

## 2. Análisis de Implementación Actual

### 2.1 PanelCommunicationService (`src/panel_communication_service.py`)

#### ✅ Valores por Defecto Correctos
```python
# Valores por defecto
if colors is None:
    colors = [1] * len(texts)  # Rojo por defecto
if font_sizes is None:
    font_sizes = [2] * len(texts)  # Tamaño 16 (valor 2) por defecto
if show_effects is None:
    show_effects = [1] * len(texts)  # Scroll hacia arriba por defecto
```

**Problema identificado**: ❌ **EFECTO INCORRECTO**
- Usa `1` como efecto por defecto
- Según documentación: `1` no está definido para protocolo antiguo
- Debería usar `2` (fijo) o `12` (scroll)

#### ✅ Estructura de Payload Correcta
```python
window = {
    "id": i,
    "text": text,
    "color": colors[i] if i < len(colors) else 1,
    "fontSize": font_sizes[i] if i < len(font_sizes) else 2,
    "speed": 100,
    "effect": show_effects[i] if i < len(show_effects) else 1,
    "stayTime": 50,
    "alignmentH": 1,
    "alignmentV": 1
}
```

### 2.2 API Server - Endpoint `/panel/<ip>/message` (`src/api_server.py`)

#### ✅ Conversión de Colores Correcta
```python
# Convertir colores de texto a códigos numéricos
color_codes = {
    'VERDE': 2,
    'ROJO': 1,
    'AMARILLO': 3
}
color_code = color_codes.get(color, 2)  # Verde por defecto
```

#### ❌ Conversión de Efectos INCORRECTA
```python
# Convertir scroll a efecto
effect_code = 12 if scroll else 2  # 12=scroll, 2=fijo
```

**Problema identificado**: ✅ **CORRECTO** - Esta conversión es correcta según documentación

#### ✅ Tamaño de Fuente Correcto
```python
font_size=2,  # Tamaño 16 píxeles
```

### 2.3 API Server - Endpoint `/panel/<int:panel_id>/message` (`src/api_server.py`)

#### ❌ Tamaño de Fuente INCORRECTO
```python
fontSize = req.get('fontSize', 16)  # Cambiar por defecto de 2 a 16
```

**Problema identificado**: ❌ **INCONSISTENCIA**
- Recibe `fontSize` como píxeles (16)
- Pero la API espera códigos numéricos (2 para 16px)
- Debería convertir: `16px` → `2`

#### ❌ Efecto SIN VALIDACIÓN
```python
showEffect = req.get('showEffect', 1)
```

**Problema identificado**: ❌ **EFECTO INCORRECTO**
- Usa `1` como efecto por defecto
- `1` no está definido para protocolo antiguo
- Debería usar `2` (fijo) o `12` (scroll)

### 2.4 Panel Communication (`src/panel_communication.py`)

#### ✅ Parámetros Correctos
```python
"color": 2,  # Verde (valor 2)
"fontSize": 2,  # Tamaño 16 píxeles (valor 2)
"effect": 1,  # Scroll hacia arriba
```

**Problema identificado**: ❌ **EFECTO INCORRECTO**
- Usa `1` como efecto
- `1` no está definido para protocolo antiguo
- Debería usar `2` (fijo) o `12` (scroll)

## 3. Inconsistencias Identificadas

### 3.1 ❌ Efecto por Defecto Incorrecto
**Problema**: Múltiples lugares usan `1` como efecto por defecto
**Impacto**: Los paneles pueden no mostrar el efecto esperado
**Ubicaciones**:
- `panel_communication_service.py` línea 75
- `panel_communication.py` línea 85
- `api_server.py` línea 870

### 3.2 ❌ Conversión de Tamaño de Fuente Inconsistente
**Problema**: Endpoint `/panel/<int:panel_id>/message` recibe píxeles pero no convierte
**Impacto**: Tamaño de fuente incorrecto en paneles
**Ubicación**: `api_server.py` línea 870

### 3.3 ❌ Falta de Validación de Efectos
**Problema**: No se valida que los efectos sean válidos para protocolo antiguo
**Impacto**: Efectos no válidos pueden causar errores
**Ubicaciones**: Múltiples endpoints

## 4. Correcciones Necesarias

### 4.1 Corregir Efecto por Defecto
**Cambio**: Usar `2` (fijo) en lugar de `1` como efecto por defecto

**Archivos a modificar**:
1. `src/panel_communication_service.py` línea 75
2. `src/panel_communication.py` línea 85
3. `src/api_server.py` línea 870

### 4.2 Corregir Conversión de Tamaño de Fuente
**Cambio**: Convertir píxeles a códigos numéricos

**Función de conversión necesaria**:
```python
def pixels_to_font_code(pixels):
    """Convertir píxeles a código de fuente para protocolo antiguo"""
    font_map = {
        8: 0,    # 8px -> 0
        12: 1,   # 12px -> 1
        16: 2,   # 16px -> 2
        24: 3,   # 24px -> 3
        32: 4,   # 32px -> 4
        40: 5,   # 40px -> 5
        48: 6,   # 48px -> 6
        56: 7    # 56px -> 7
    }
    return font_map.get(pixels, 2)  # 16px por defecto
```

### 4.3 Agregar Validación de Efectos
**Cambio**: Validar que los efectos sean válidos para protocolo antiguo

**Efectos válidos**: `[2, 12]` (fijo, scroll)

### 4.4 Estandarizar Parámetros por Defecto
**Cambio**: Usar valores consistentes en todos los lugares

**Valores recomendados**:
- Color: `2` (Verde)
- Tamaño: `2` (16px)
- Efecto: `2` (Fijo)

## 5. Implementación de Correcciones

### 5.1 Función de Utilidad para Conversiones
```python
def get_old_protocol_parameters(color=None, font_size_pixels=None, effect=None):
    """
    Obtener parámetros correctos para protocolo antiguo
    
    Args:
        color: Color (1=Rojo, 2=Verde, 3=Amarillo, etc.)
        font_size_pixels: Tamaño en píxeles (8, 12, 16, 24, 32, 40, 48, 56)
        effect: Efecto (2=fijo, 12=scroll)
    
    Returns:
        Tuple (color_code, font_size_code, effect_code)
    """
    # Color por defecto: Verde
    color_code = color if color in [1, 2, 3, 4, 5, 6, 7] else 2
    
    # Convertir píxeles a código de fuente
    font_map = {8: 0, 12: 1, 16: 2, 24: 3, 32: 4, 40: 5, 48: 6, 56: 7}
    font_size_code = font_map.get(font_size_pixels, 2)  # 16px por defecto
    
    # Efecto por defecto: Fijo
    effect_code = effect if effect in [2, 12] else 2
    
    return color_code, font_size_code, effect_code
```

### 5.2 Aplicar Correcciones en PanelCommunicationService
```python
# En _send_to_unified_api
if show_effects is None:
    show_effects = [2] * len(texts)  # Fijo por defecto (valor 2)
```

### 5.3 Aplicar Correcciones en API Server
```python
# En send_message_to_panel
fontSize = req.get('fontSize', 16)  # Recibir píxeles
font_size_code = pixels_to_font_code(fontSize)  # Convertir a código
showEffect = req.get('showEffect', 2)  # Fijo por defecto (valor 2)
```

## 6. Testing Recomendado

### 6.1 Tests de Parámetros
1. **Test de colores**: Verificar que todos los colores (1-7) funcionen
2. **Test de tamaños**: Verificar que todos los tamaños (0-7) funcionen
3. **Test de efectos**: Verificar que efectos 2 y 12 funcionen

### 6.2 Tests de Conversión
1. **Test de píxeles a código**: Verificar conversión correcta
2. **Test de valores por defecto**: Verificar valores por defecto
3. **Test de validación**: Verificar rechazo de valores inválidos

## 7. Conclusión

**Estado actual**: ⚠️ **INCONSISTENCIAS IDENTIFICADAS**

**Problemas críticos**:
1. Efecto por defecto incorrecto (`1` en lugar de `2`)
2. Conversión de tamaño de fuente inconsistente
3. Falta de validación de parámetros

**Impacto**: Los paneles con protocolo antiguo pueden no mostrar correctamente los efectos y tamaños de fuente.

**Prioridad**: **ALTA** - Corregir antes de producción para asegurar funcionamiento correcto de paneles antiguos. 