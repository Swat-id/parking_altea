# Análisis del Protocolo de Paneles LED - v5.0.1

## IMPORTANTE: Formato CPower Real vs Documentación

### Descubrimiento Crítico (2026-05-20)

La documentación del fabricante describe un formato de paquete que **NO funciona** con los paneles CPower reales. El SDK Java usa un formato diferente que **SÍ funciona**.

#### Formato Documentado (NO FUNCIONA):
```
FF FF FF FF + NetworkLength + Reserved + PacketType + ... + Checksum
```

#### Formato CPower Real (FUNCIONA):
```
A5 + DeviceID (ASCII) + 00 + PacketType + CardType + CardID + ProtocolCode + 
AdditionalInfo + PackedDataLength + PO + TP + PacketData + Checksum + AE
```

| Campo | Tamaño | Descripción |
|-------|--------|-------------|
| Start Marker | 1 byte | `0xA5` (fijo) |
| Device ID | 12 bytes | ID del dispositivo en ASCII (ej: "00606ed81e7e") |
| Separator | 1 byte | `0x00` |
| Packet Type | 1 byte | `0x68` (envío) |
| Card Type | 1 byte | `0x32` (LED) |
| Card ID | 1 byte | `0xFF` (broadcast) |
| Protocol Code | 1 byte | `0x7B` |
| Additional Info | 1 byte | `0x01` (confirmación) |
| Packed Data Len | 2 bytes | Little-endian |
| PO, TP | 2 bytes | `0x00 0x00` |
| Packet Data | Variable | CC + datos |
| Checksum | 2 bytes | Little-endian |
| **Terminator** | 1 byte | **`0xAE`** (crítico!) |

### Descubrimiento de Device ID via UDP

Los paneles CPower responden a solicitudes UDP en el puerto 57274:

```bash
echo -n -e 'CPower~?\x00' | nc -u -w 2 PANEL_IP 57274
```

Respuesta: `CP~:IP\tDeviceID\tModelo\t...`

### Paneles Configurados

**Protocolo NUEVO (CPower - puerto 7110):**
| Panel | IP | Device ID |
|-------|-----|-----------|
| PANEL PALAU | 172.20.4.50 | 00606ed81e79 |
| PANEL COCOLISO | 172.20.4.51 | 00606ed81e68 |
| BELLES ARTS 2 | 172.20.4.52 | 00606ed81e7e |
| BELLES ARTS | 172.20.4.53 | 00606ed81e60 |

**Protocolo ANTIGUO (Java SDK - puerto 8888):**
| Panel | IP | Notas |
|-------|-----|-------|
| PANEL ALTEA VELLA | 172.20.1.50 | No soporta CPower |
| PANEL C. ESPORTIVA | 172.20.17.50 | No soporta CPower |
| PANEL RENFE | 172.20.2.50 | No soporta CPower |
| PANEL BASSETA 1 | 172.20.5.50 | No soporta CPower |
| PANEL BASSETA 2 | 172.20.5.51 | No soporta CPower |
| PANEL PITERES | 172.20.8.50 | Tiene device_id pero usa old |
| PANEL PITERES 2 | 172.20.8.51 | Tiene device_id pero usa old |

---

## 1. Códigos de Efecto (Documentación vs Implementación)

### 1.1 Tabla Completa de Efectos según Documentación

| Código | Efecto | Implementado | Notas |
|--------|--------|--------------|-------|
| 0 (0x00) | Draw | ✅ `Effect.DRAW` | Texto instantáneo |
| 1 (0x01) | Open from left | ✅ `Effect.OPEN_FROM_LEFT` | |
| 2 (0x02) | Open from right | ✅ `Effect.OPEN_FROM_RIGHT` | |
| 3 (0x03) | Open from center (Horizontal) | ❌ No implementado | |
| 4 (0x04) | Open from center (Vertical) | ❌ No implementado | |
| 5 (0x05) | Shutter (vertical) | ❌ No implementado | |
| 6 (0x06) | Move to left | ✅ `Effect.MOVE_TO_LEFT` | |
| 7 (0x07) | Move to right | ✅ `Effect.MOVE_TO_RIGHT` | |
| 8 (0x08) | Move up | ❌ No implementado | |
| 9 (0x09) | Move down | ❌ No implementado | |
| 10 (0x0A) | Scroll up | ✅ `Effect.SCROLL_UP` | |
| **11 (0x0B)** | **Scroll to left** | ✅ `Effect.SCROLL_LEFT` | **Usado actualmente** |
| **12 (0x0C)** | **Scroll to right** | ✅ `Effect.SCROLL_RIGHT` | |
| 13 (0x0D) | Flicker | ✅ `Effect.FLICKER` | |
| **14 (0x0E)** | **Continuous scroll to left** | ✅ `Effect.CONTINUOUS_SCROLL_LEFT` | Scroll sin pausa |
| **15 (0x0F)** | **Continuous scroll to right** | ✅ `Effect.CONTINUOUS_SCROLL_RIGHT` | Scroll sin pausa |
| 16 (0x10) | Shutter (horizontal) | ❌ No implementado | |
| 17 (0x11) | Clockwise open out | ❌ No implementado | |
| 18 (0x12) | Anticlockwise open out | ❌ No implementado | |
| ... | ... | ... | |
| 53 (0x35) | Continuous scroll up | ❌ No implementado | |
| 54 (0x36) | Continuous scroll down | ❌ No implementado | |
| **55 (0x37)** | **Reserved** | ❌ | **NO usar** |
| **56 (0x38)** | **Reserved** | ❌ | **NO usar** |
| ... | ... | ... | |
| 255 (0xFF) | Random (1 byte) | ❌ No implementado | |
| 32768 (0x8000) | Random (2 bytes) | ❌ No implementado | |

### 1.2 Verificación de Constantes Implementadas

**Archivo**: `src/panel_protocol/constants.py`

```python
class Effect:
    DRAW = 0x00              # ✅ Correcto (0)
    OPEN_FROM_LEFT = 0x01    # ✅ Correcto (1)
    OPEN_FROM_RIGHT = 0x02   # ✅ Correcto (2)
    MOVE_TO_LEFT = 0x06      # ✅ Correcto (6)
    MOVE_TO_RIGHT = 0x07     # ✅ Correcto (7)
    SCROLL_UP = 0x0A         # ✅ Correcto (10)
    SCROLL_LEFT = 0x0B       # ✅ Correcto (11)
    SCROLL_RIGHT = 0x0C      # ✅ Correcto (12)
    FLICKER = 0x0D           # ✅ Correcto (13)
    CONTINUOUS_SCROLL_LEFT = 0x0E   # ✅ Correcto (14)
    CONTINUOUS_SCROLL_RIGHT = 0x0F  # ✅ Correcto (15)
```

**Estado**: ✅ Los códigos de efecto están correctamente implementados según la documentación.

---

## 2. Formato del Paquete de Red (Documentación vs Implementación)

### 2.1 Estructura según Documentación

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PAQUETE DE RED (Protocolo 0x7B)                      │
├─────────────────┬──────────────────┬────────────────────────────────────┤
│ Campo           │ Valor/Tamaño     │ Descripción                        │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ ID Code         │ 4 bytes          │ 0x00000000 ~ 0xFFFFFFFF            │
│                 │                  │ High byte in the former            │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Network Length  │ 2 bytes          │ Longitud desde Packet Type hasta   │
│                 │                  │ Checksum (inclusive)               │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Reserved        │ 2 bytes          │ 0x0000                             │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Packet Type     │ 1 byte           │ 0x68 (envío)                       │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Card Type       │ 1 byte           │ 0x32 (fijo)                        │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Card ID         │ 1 byte           │ 0x01~0xFE (específico)             │
│                 │                  │ 0xFF (broadcast)                   │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Protocol Code   │ 1 byte           │ 0x7B                               │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Additional Info │ 1 byte           │ bit 0: confirmación (1=sí, 0=no)   │
│                 │                  │ bit 1-7: reservado (0)             │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Packed Data Len │ 2 bytes (LL LH)  │ Longitud de CC... (Lower byte      │
│                 │                  │ in the former = little-endian)     │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Packet Number   │ 1 byte (PO)      │ 0x00~0xFF                          │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Last Packet Num │ 1 byte (TP)      │ Total paquetes - 1                 │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Packet Data     │ Variable (CC...) │ Subcomando y datos                 │
├─────────────────┼──────────────────┼────────────────────────────────────┤
│ Checksum        │ 2 bytes (SH SL)  │ Suma desde Packet Type hasta       │
│                 │                  │ Packet Data. Lower byte former     │
└─────────────────┴──────────────────┴────────────────────────────────────┘
```

### 2.2 Verificación de Implementación

**Archivo**: `src/panel_protocol/packet_builder.py` - Método `build_network_packet()`

| Campo | Doc | Implementación | Estado |
|-------|-----|----------------|--------|
| ID Code | 4 bytes, high byte former | `ID_CODE = [0xFF, 0xFF, 0xFF, 0xFF]` | ✅ |
| Network Length | 2 bytes | `struct.pack('<H', network_length)` | ✅ Little-endian |
| Reserved | 2 bytes, 0x0000 | `b'\x00\x00'` | ✅ |
| Packet Type | 0x68 | `PACKET_TYPE_SEND = 0x68` | ✅ |
| Card Type | 0x32 | `CARD_TYPE = 0x32` | ✅ |
| Card ID | 1 byte | `card_id` parámetro | ✅ |
| Protocol Code | 0x7B | `CMD_PROTOCOL_CONTROL = 0x7B` | ✅ |
| Additional Info | 1 byte | `CONFIRMATION_REQUESTED = 0x01` | ✅ |
| Packed Data Len | 2 bytes LL LH | `struct.pack('<H', packet_data_length)` | ✅ Little-endian |
| Packet Number (PO) | 1 byte | `packet_number` parámetro | ✅ |
| Last Packet (TP) | 1 byte | `last_packet_number` parámetro | ✅ |
| Packet Data | Variable | `packet_data` parámetro | ✅ |
| Checksum | 2 bytes, lower former | `calculate_checksum()` little-endian | ✅ |

**Estado**: ✅ La estructura del paquete está correctamente implementada.

---

## 3. Subcomando CC=0x02 (Enviar Texto)

### 3.1 Estructura según Documentación

```
CC=0x02: Send Text to Window
┌─────────────────┬──────────────┬───────────────────────────────────────┐
│ Campo           │ Tamaño       │ Descripción                           │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ CC              │ 1 byte       │ 0x02 (comando enviar texto)           │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ Window ID       │ 1 byte       │ 0x00~0x07                             │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ Mode (Effect)   │ 1 byte       │ 0~70 (ver tabla de efectos)           │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ Alignment       │ 1 byte       │ 0=Left, 1=Center, 2=Right             │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ Speed           │ 1 byte       │ 1~100 (1=más rápido)                  │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ Stay Time       │ 2 bytes      │ High byte in the former (big-endian)  │
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ Text Data       │ Variable     │ Formato Rich3: [color_font, 0x00, char]│
├─────────────────┼──────────────┼───────────────────────────────────────┤
│ End Marker      │ 3 bytes      │ 0x00, 0x00, 0x00                      │
└─────────────────┴──────────────┴───────────────────────────────────────┘
```

### 3.2 Verificación de Implementación

**Archivo**: `src/panel_protocol/packet_builder.py` - Método `build_send_text_packet()`

| Campo | Doc | Implementación | Estado |
|-------|-----|----------------|--------|
| CC | 0x02 | `SUB_CMD_SEND_TEXT = 0x02` | ✅ |
| Window ID | 0-7 | `window_id` parámetro | ✅ |
| Mode (Effect) | 0-70 | `effect` parámetro | ✅ |
| Alignment | 0-2 | Validación incluida | ✅ |
| Speed | 1-100 | Validación incluida | ✅ |
| Stay Time | 2 bytes big-endian | `struct.pack('>H', stay_time)` | ✅ |
| Text Data | Rich3 format | `[color_font, 0x00, ord(char)]` | ✅ |
| End Marker | 0x00, 0x00, 0x00 | `b'\x00\x00\x00'` | ✅ |

**Estado**: ✅ El subcomando CC=0x02 está correctamente implementado.

---

## 4. Análisis de Problemas Potenciales

### 4.1 Diferencia entre Scroll (11) y Continuous Scroll (14)

| Código | Nombre | Comportamiento Esperado |
|--------|--------|-------------------------|
| 11 (0x0B) | Scroll to left | Hace scroll y **pausa** al final según `stay_time` |
| 14 (0x0E) | Continuous scroll to left | Hace scroll **sin pausa**, repite continuamente |

**Recomendación**: 
- Para texto largo que debe ser visible siempre: usar **14 (Continuous)**
- Para mensaje que aparece, hace scroll, y luego desaparece: usar **11 (Scroll)**

### 4.2 Parámetro `stay_time` según Efecto

| Efecto | stay_time recomendado |
|--------|----------------------|
| 0 (Draw) | > 0 (tiempo que permanece visible) |
| 11 (Scroll) | > 0 (tiempo de pausa al final del scroll) |
| 14 (Continuous scroll) | **0 o bajo** (no necesita pausa) |

### 4.3 Parámetro `speed`

- Rango válido: **1 a 100**
- **1** = Muy rápido
- **100** = Muy lento
- Valor por defecto recomendado: **3-5** para velocidad moderada

---

## 5. Códigos Reservados (NO USAR)

| Código | Estado | Notas |
|--------|--------|-------|
| 55 (0x37) | **Reserved** | NO usar - comportamiento indefinido |
| 56 (0x38) | **Reserved** | NO usar - comportamiento indefinido |
| 59 (0x3B) | **Reserved** | NO usar |
| 68 (0x44) | **Reserved** | NO usar |

**IMPORTANTE**: Los códigos 55 y 56 fueron usados incorrectamente en versiones anteriores pensando que eran "Continuous scroll" del SDK Java. Según la documentación del protocolo, estos están **reservados** y no deben usarse.

---

## 6. Ejemplo de Paquete Correcto

### 6.1 Enviar "HOLA" con Scroll Continuo a la Izquierda

**Parámetros**:
- Card ID: 0x01
- Window ID: 0
- Text: "HOLA"
- Color: Rojo (0x01)
- Font Size: 16px (0x02)
- Effect: Continuous scroll left (14 = 0x0E)
- Alignment: Center (1)
- Speed: 3
- Stay Time: 0 (sin pausa para scroll continuo)

**Paquete CC (datos)**:
```
02          CC = Send Text
00          Window ID = 0
0E          Effect = 14 (Continuous scroll left)
01          Alignment = Center
03          Speed = 3
00 00       Stay time = 0 (big-endian)
12 00 48    'H' (color_font=0x12, 0x00, 0x48)
12 00 4F    'O' (color_font=0x12, 0x00, 0x4F)
12 00 4C    'L' (color_font=0x12, 0x00, 0x4C)
12 00 41    'A' (color_font=0x12, 0x00, 0x41)
00 00 00    End marker
```

**Nota**: `color_font = (color << 4) | font_size = (0x01 << 4) | 0x02 = 0x12`

---

## 7. Resumen de Validación

| Componente | Estado | Notas |
|------------|--------|-------|
| Códigos de efecto | ✅ Correcto | 0-15 implementados correctamente |
| Estructura paquete | ✅ Correcto | Según documentación |
| Checksum | ✅ Correcto | Little-endian, suma de bytes |
| Stay time endianness | ✅ Correcto | Big-endian ('>H') |
| Speed range | ✅ Correcto | Validación 1-100 |
| Alignment range | ✅ Correcto | Validación 0-2 |
| Text encoding | ✅ Correcto | Rich3 format |

---

## 8. Mapeo de Efectos en el Sistema

### 8.1 panel_schedule_service.py

```python
effect_codes_new = {
    'static': 0,          # Draw - texto instantáneo
    'center': 0,          # Draw - texto instantáneo
    'fijo': 0,            # Draw - texto instantáneo
    'scroll_left': 11,    # Scroll to left (con pausa)
    'scroll_right': 12,   # Scroll to right (con pausa)
    'scroll': 11          # Alias para scroll_left
}
```

### 8.2 Recomendación para Scroll Continuo

Si se requiere scroll continuo (sin pausas), cambiar a:
```python
'scroll_left': 14,    # Continuous scroll to left
'scroll_right': 15,   # Continuous scroll to right
```

---

## 9. Próximos Pasos Recomendados

1. **Probar efecto 11 (Scroll)** con `stay_time > 0` para ver si hace scroll con pausa
2. **Probar efecto 14 (Continuous scroll)** con `stay_time = 0` para scroll continuo
3. **Verificar logs** del servicio 7110 para confirmar qué valores se envían
4. **Comparar paquetes** generados con ejemplos de la documentación

---

## 10. Ejemplo de Paquete CPower Correcto

### Enviar "HOLA" en verde a panel 172.20.4.52

```bash
curl -X POST http://localhost:7110/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -d '{
    "panel_ip": "172.20.4.52",
    "panel_port": 5200,
    "card_id": 255,
    "window_id": 0,
    "text": "HOLA",
    "color": 2,
    "font_size": 2,
    "effect": 255,
    "alignment": 0,
    "speed": 5,
    "stay_time": 50,
    "device_id": "00606ed81e7e"
  }'
```

### Paquete hex generado:
```
a5 30 30 36 30 36 65 64 38 31 65 37 65 00   # A5 + DeviceID + 00
68 32 ff 7b 01                               # PacketType, CardType, CardID, Protocol, Confirm
16 00                                        # PackedDataLen (22 little-endian)
00 00                                        # PO, TP
02 00 ff 00 05 00 32                         # CC, WindowID, Effect, Align, Speed, StayTime
22 00 48 22 00 4f 22 00 4c 22 00 41          # HOLA (color_font + 00 + char)
00 00 00                                     # End marker
XX XX                                        # Checksum
ae                                           # Terminator
```

---

*Documento actualizado: 2026-05-20*
*Versión del análisis: v5.0.1*
*Cambios: Descubierto formato CPower real vs documentación, añadido terminador 0xAE*
