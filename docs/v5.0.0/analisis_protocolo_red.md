# Análisis Completo del Protocolo de Red v5.0.0

## Documento de Referencia
- **Fuente**: Rotuloselectronicos.net external calls communication protocol.pdf
- **Versión**: v1.4.7
- **Sección analizada**: 2.2 Network data packet format

---

## 1. Estructura del Paquete de Red (2.2.1)

### 1.1 Formato de Envío

| Campo | Valor | Tamaño | Endianness | Descripción |
|-------|-------|--------|------------|-------------|
| **ID Code** | 0x00000000 ~ 0xFFFFFFFF | 4 bytes | Big-endian | ID de la tarjeta controladora |
| **Network Length** | 0x0000 ~ 0xFFFF | 2 bytes | Little-endian | Longitud desde Packet Type hasta Checksum |
| **Reserved** | 0x0000 | 2 bytes | - | Reservado, siempre 0x00 0x00 |
| **Packet Type** | 0x68 | 1 byte | - | Tipo de paquete (envío) |
| **Card Type** | 0x32 | 1 byte | - | Tipo fijo de tarjeta |
| **Card ID** | 0x01~0xFE / 0xFF | 1 byte | - | ID específico o 0xFF=broadcast |
| **Protocol Code** | 0x7B | 1 byte | - | Identificador del protocolo |
| **Additional Info** | 0x00~0xFF | 1 byte | - | bit 0: confirmación (1=sí) |
| **Packed Data Length** | 0x0000~0xFFFF | 2 bytes | **Little-endian** (LL LH) | Longitud de CC + datos |
| **Packet Number (PO)** | 0x00~0xFF | 1 byte | - | Número de paquete actual |
| **Last Packet (TP)** | 0x00~0xFF | 1 byte | - | Total paquetes - 1 |
| **Packet Data (CC...)** | Variable | Variable | - | Subcomando y datos |
| **Checksum (SH SL)** | 0x0000~0xFFFF | 2 bytes | **Little-endian** | Suma desde Packet Type hasta Packet Data |

### 1.2 Formato de Respuesta (2.2.2)

| Campo | Valor | Descripción |
|-------|-------|-------------|
| Packet Type | 0xE8 | 0x68 \| 0x80 (respuesta) |
| Return Value (RR) | 0x00 = éxito, 0x01~0xFF = error | Código de resultado |

**Códigos de error:**
- 0x00: Éxito
- 0x01: Error de checksum
- 0x02: Error de secuencia de paquete
- Sin respuesta: Fallo de comunicación

---

## 2. Subcomandos (CC) Disponibles

### 2.1 Comandos Generales

| CC | Nombre | Descripción |
|----|--------|-------------|
| 0x01 | Division of display window | Crear/dividir ventanas |
| 0x02 | Send text to window | Enviar texto con formato Rich3 |
| 0x03 | Send image to window | Enviar imagen |
| 0x04 | Static text | Texto estático con RGB |
| 0x05 | Send clock | Mostrar reloj |
| 0x06 | Exit show | Volver a programa interno |
| 0x07 | Save/clear data | Guardar/limpiar flash |
| 0x08 | Select program (1 byte) | Ejecutar programa guardado |
| 0x09 | Select program (2 bytes) | Ejecutar programa (número grande) |
| 0x0A | Set variable value | Establecer variables |
| 0x0B | Select program + variable | Programa + variable |
| 0x0C | Set global display area | Área de display global |
| 0x0D | Push user variable data | Datos de variable usuario |
| 0x0E | Set timer control | Control de temporizador |
| 0x0F | Set global area + variables | Área global + variables |
| 0x12 | Send pure text | Texto puro sin formato |

### 2.2 Comandos de Programa Template

| CC | Nombre |
|----|--------|
| 0x81 | Set program template |
| 0x82 | In/out program template |
| 0x83 | Query program template |
| 0x84 | Delete program |
| 0x85 | Send text to special window |
| 0x86 | Send picture to special window |
| 0x87 | Clock/temperature display |
| 0x88 | Send alone program |
| 0x8A | Set program property |
| 0x8B | Set play plan |
| 0x8C | Delete play plan |
| 0x8D | Query play plan |

---

## 3. Detalle de Comandos Principales

### 3.1 CC=0x01: División de Ventanas

| Campo | Valor | Tamaño | Endianness |
|-------|-------|--------|------------|
| CC | 0x01 | 1 byte | - |
| Window Number | 1~8 | 1 byte | - |
| Window 1 X | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Window 1 Y | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Window 1 Width | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Window 1 Height | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| ... | ... | ... | ... |

**Nota crítica**: La documentación dice "high byte in the former" = **Big-endian**

### 3.2 CC=0x02: Enviar Texto a Ventana

| Campo | Valor | Tamaño | Endianness |
|-------|-------|--------|------------|
| CC | 0x02 | 1 byte | - |
| Window No | 0x00~0x07 | 1 byte | - |
| Mode (Effect) | 0~70 | 1 byte | - |
| Alignment | 0~2 | 1 byte | - |
| Speed | 1~100 | 1 byte | - |
| Stay Time | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| String | Rich3 format | Variable | - |

**Alignment:**
- 0: Left-aligned
- 1: Horizontal center
- 2: Right-aligned

**Speed:**
- 1 = más rápido
- 100 = más lento

**Formato Rich3 del String:**
```
[color_font] [0x00] [char]  → 3 bytes por carácter
...
[0x00] [0x00] [0x00]        → marcador de fin
```

Donde `color_font = (color << 4) | font_size`

### 3.3 CC=0x04: Texto Estático

| Campo | Valor | Tamaño | Endianness |
|-------|-------|--------|------------|
| CC | 0x04 | 1 byte | - |
| Window NO | 0x00~0x07 | 1 byte | - |
| Data type | 0x01 | 1 byte | - |
| Alignment | 0~2 | 1 byte | - |
| Display X | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Display Y | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Display Width | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Display Height | 0x0000~0xFFFF | 2 bytes | **Big-endian** |
| Font | bits 0-3: size, bits 4-6: style | 1 byte | - |
| Color R | 0~255 | 1 byte | - |
| Color G | 0~255 | 1 byte | - |
| Color B | 0~255 | 1 byte | - |
| Text | string + 0x00 | Variable | - |

---

## 4. Tabla de Efectos (Mode)

| Código | Efecto | Descripción |
|--------|--------|-------------|
| 0 (0x00) | Draw | Texto instantáneo |
| 1 (0x01) | Open from left | Abrir desde izquierda |
| 2 (0x02) | Open from right | Abrir desde derecha |
| 3 (0x03) | Open from center (H) | Abrir desde centro horizontal |
| 4 (0x04) | Open from center (V) | Abrir desde centro vertical |
| 5 (0x05) | Shutter (vertical) | Persiana vertical |
| 6 (0x06) | Move to left | Mover a izquierda |
| 7 (0x07) | Move to right | Mover a derecha |
| 8 (0x08) | Move up | Mover arriba |
| 9 (0x09) | Move down | Mover abajo |
| 10 (0x0A) | Scroll up | Scroll arriba |
| **11 (0x0B)** | **Scroll to left** | Scroll izquierda (con pausa) |
| **12 (0x0C)** | **Scroll to right** | Scroll derecha (con pausa) |
| 13 (0x0D) | Flicker | Parpadeo |
| **14 (0x0E)** | **Continuous scroll left** | Scroll continuo izquierda |
| **15 (0x0F)** | **Continuous scroll right** | Scroll continuo derecha |
| 16 (0x10) | Shutter (horizontal) | Persiana horizontal |
| 53 (0x35) | Continuous scroll up | Scroll continuo arriba |
| 54 (0x36) | Continuous scroll down | Scroll continuo abajo |
| **55 (0x37)** | **RESERVED** | ⚠️ NO USAR |
| **56 (0x38)** | **RESERVED** | ⚠️ NO USAR |
| 255 (0xFF) | Random | Efecto aleatorio |

---

## 5. Análisis de la Implementación Actual

### 5.1 Archivo: `packet_builder.py`

#### ❌ BUG CRÍTICO: `build_create_window_packet`

```python
# ACTUAL (INCORRECTO):
packet_data += struct.pack('<HHHH', x, y, width, height)  # Little-endian

# CORRECTO según documentación:
packet_data += struct.pack('>HHHH', x, y, width, height)  # Big-endian
```

**Impacto**: Las coordenadas de ventana se envían invertidas, causando que el panel no procese correctamente la creación de ventanas.

#### ✅ CORRECTO: `build_send_text_packet`

```python
# Stay time usa Big-endian correctamente:
command_data += struct.pack('>H', stay_time)  # ✅ Correcto
```

#### ❌ BUG: `build_send_image_packet`

```python
# ACTUAL (POSIBLEMENTE INCORRECTO):
packet_data += struct.pack('<H', stay_time)   # Little-endian
packet_data += struct.pack('<HH', x, y)       # Little-endian

# La documentación sugiere Big-endian para stay_time
```

### 5.2 Resumen de Correcciones Necesarias

| Función | Campo | Actual | Correcto | Estado |
|---------|-------|--------|----------|--------|
| `build_create_window_packet` | x, y, width, height | Little-endian | **Big-endian** | ❌ BUG |
| `build_send_text_packet` | stay_time | Big-endian | Big-endian | ✅ OK |
| `build_send_image_packet` | stay_time | Little-endian | **Big-endian** | ❌ BUG |
| `build_send_image_packet` | x, y | Little-endian | **Big-endian** | ❌ BUG |
| `build_static_text_packet` | display area | Big-endian | Big-endian | ✅ OK |

---

## 6. Plan de Corrección v5.0.0

### 6.1 Fase 1: Correcciones Críticas

1. **Corregir `build_create_window_packet`**
   - Cambiar endianness de coordenadas a Big-endian

2. **Corregir `build_send_image_packet`**
   - Cambiar endianness de stay_time, x, y a Big-endian

### 6.2 Fase 2: Validación

1. Crear tests unitarios para cada paquete
2. Comparar paquetes generados con ejemplos de la documentación
3. Probar en paneles reales

### 6.3 Fase 3: Mejoras

1. Implementar todos los comandos CC no implementados
2. Añadir soporte para programa templates (CC=0x81-0x8D)
3. Implementar manejo de respuestas y códigos de error

---

## 7. Ejemplo de Paquete Correcto

### Enviar "HOLA" en rojo a ventana 0

**Parámetros:**
- Card ID: 0x01
- Window ID: 0
- Text: "HOLA"
- Color: 0x01 (rojo)
- Font Size: 0x02 (16px)
- Effect: 0 (Draw)
- Alignment: 1 (Center)
- Speed: 3
- Stay Time: 3 segundos

**Paquete generado:**
```
ID Code:         FF FF FF FF
Network Length:  XX XX (little-endian)
Reserved:        00 00
Packet Type:     68
Card Type:       32
Card ID:         01
Protocol:        7B
Additional:      01 (confirmación)
Data Length:     XX XX (little-endian)
PO:              00
TP:              00
CC:              02
Window:          00
Effect:          00
Alignment:       01
Speed:           03
Stay Time:       00 03 (big-endian = 3 segundos)
Text:            12 00 48  ('H' con color/font 0x12)
                 12 00 4F  ('O')
                 12 00 4C  ('L')
                 12 00 41  ('A')
                 00 00 00  (fin de texto)
Checksum:        XX XX (little-endian)
```

---

*Documento creado: v5.0.0*
*Fecha: 2026-05-20*
