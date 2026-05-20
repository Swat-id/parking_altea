# Changelog v5.0.0 - Mejoras de Protocolo

## Resumen

Esta versión se enfoca en corregir bugs críticos del protocolo de comunicación con paneles LED y añadir soporte completo para todos los comandos y efectos según la documentación oficial del fabricante.

## Bugs Corregidos

### 1. ❌ BUG CRÍTICO: Endianness en `build_create_window_packet`

**Problema**: Las coordenadas de ventana (x, y, width, height) se enviaban en little-endian cuando la documentación especifica big-endian ("high byte in the former").

**Archivo**: `src/panel_protocol/packet_builder.py`

**Antes**:
```python
packet_data += struct.pack('<HHHH', x, y, width, height)  # Little-endian ❌
```

**Después**:
```python
packet_data += struct.pack('>HHHH', x, y, width, height)  # Big-endian ✅
```

**Impacto**: Los paneles no procesaban correctamente la creación de ventanas, causando que el texto no se mostrara.

### 2. ❌ BUG: Endianness en `build_send_image_packet`

**Problema**: Los campos stay_time y coordenadas x, y se enviaban en little-endian cuando deberían ser big-endian.

**Antes**:
```python
packet_data += struct.pack('<H', stay_time)
packet_data += struct.pack('<HH', x, y)
```

**Después**:
```python
packet_data += struct.pack('>H', stay_time)
packet_data += struct.pack('>HH', x, y)
```

## Nuevas Funcionalidades

### 1. Tabla Completa de Efectos (70+ efectos)

Se añadieron todos los códigos de efecto según la documentación oficial:

| Rango | Descripción |
|-------|-------------|
| 0-15 | Efectos básicos (Draw, Scroll, Open, Move, etc.) |
| 16-54 | Efectos avanzados (Shutter, Windmill, Mosaic, etc.) |
| 55-56 | **RESERVADOS** - NO USAR |
| 57-70 | Efectos adicionales |
| 255 | Efecto aleatorio |

### 2. Subcomandos Completos (CC)

Se añadieron todos los subcomandos del protocolo 0x7B:

**Comandos Generales:**
- CC=0x01 a CC=0x0F: Ventanas, texto, imágenes, variables, etc.
- CC=0x12: Texto puro con RGB

**Comandos de Program Template:**
- CC=0x81 a CC=0x8D: Gestión de programas y templates

## Documentación

Se creó documentación completa del protocolo:

- `docs/v5.0.0/analisis_protocolo_red.md`: Análisis detallado del formato de paquetes
- `docs/v5.0.0/CHANGELOG.md`: Este archivo

## Archivos Modificados

1. `src/panel_protocol/packet_builder.py`
   - Corregido endianness en `build_create_window_packet`
   - Corregido endianness en `build_send_image_packet`

2. `src/panel_protocol/constants.py`
   - Añadida tabla completa de 70+ efectos
   - Añadidos todos los subcomandos CC
   - Documentación inline de cada código

## Testing Recomendado

Antes de desplegar en producción:

1. Probar creación de ventanas con coordenadas específicas
2. Probar envío de imágenes con stay_time > 255
3. Verificar que los efectos 11, 14, 15 funcionan correctamente
4. Confirmar que los efectos 55, 56 siguen sin usarse

## Compatibilidad

- **Backwards compatible**: Los cambios de endianness corrigen comportamiento incorrecto
- **Paneles afectados**: Todos los que usan protocolo nuevo (puerto 7110)
- **No afecta**: Paneles con protocolo antiguo (puerto 8888)

---

*Versión: v5.0.0*
*Fecha: 2026-05-20*
*Referencia: Rotuloselectronicos.net external calls communication protocol v1.4.7*
