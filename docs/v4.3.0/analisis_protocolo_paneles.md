# Análisis Exhaustivo del Protocolo de Comunicación con Paneles LED

## Información del Proyecto
- **Versión**: v4.3.0
- **Fecha**: 2025-10-02
- **Objetivo**: Implementar servicio de bajo nivel para comunicación directa con paneles LED Rotuloselectronicos.net

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo Principal
Desarrollar un servicio Python que implemente el protocolo de comunicación a bajo nivel para controlar paneles LED, permitiendo:
- Comunicación directa TCP/IP con paneles
- Envío de texto con diferentes colores y tamaños
- Control de texto fijo y scroll
- Envío de imágenes simples
- Gestión de ventanas del panel

### 1.2 Estado Actual del Sistema
El sistema actual utiliza:
- **Servicio Java** en puerto 8888 como intermediario
- **PanelCommunicationService** (Python) que se comunica con el servicio Java
- **Protocolo indirecto** a través de HTTP REST

### 1.3 Objetivo del Nuevo Servicio
Implementar comunicación **directa TCP/IP** con los paneles, eliminando la dependencia del servicio Java y proporcionando control total del protocolo.

---

## 2. Análisis del Protocolo de Comunicación

### 2.1 Formato de Paquete de Red (Network)

#### 2.1.1 Estructura del Paquete de Envío

```
┌─────────────────────────────────────────────────────────────┐
│ ID Code              │ 4 bytes │ 0xFFFFFFFF (255.255.255.255)│
├─────────────────────────────────────────────────────────────┤
│ Network data length  │ 2 bytes │ Longitud desde Packet Type  │
│                      │         │ hasta Packet data checksum  │
├─────────────────────────────────────────────────────────────┤
│ Reservation          │ 2 bytes │ 0x0000 (fijo)               │
├─────────────────────────────────────────────────────────────┤
│ Packet type          │ 1 byte  │ 0x68 (enviar)               │
├─────────────────────────────────────────────────────────────┤
│ Card type            │ 1 byte  │ 0x32 (fijo)                 │
├─────────────────────────────────────────────────────────────┤
│ Card ID              │ 1 byte  │ 0x01-0xFE (ID panel)        │
│                      │         │ 0xFF (broadcast)            │
├─────────────────────────────────────────────────────────────┤
│ Command code (CMD)   │ 1 byte  │ Ver lista de comandos       │
├─────────────────────────────────────────────────────────────┤
│ Additional info      │ 1 byte  │ Bit 0: confirmación (0/1)   │
│                      │         │ Bits 1-7: reservados (0)    │
├─────────────────────────────────────────────────────────────┤
│ Packet data          │ Variable│ Datos del comando           │
├─────────────────────────────────────────────────────────────┤
│ Packet data checksum │ 2 bytes │ Suma desde Packet Type      │
│                      │         │ hasta Packet data (16-bit)  │
└─────────────────────────────────────────────────────────────┘
```

#### 2.1.2 Estructura del Paquete de Respuesta

```
┌─────────────────────────────────────────────────────────────┐
│ ID Code              │ 4 bytes │ 0xFFFFFFFF                  │
├─────────────────────────────────────────────────────────────┤
│ Network data length  │ 2 bytes │ Longitud del paquete        │
├─────────────────────────────────────────────────────────────┤
│ Reservation          │ 2 bytes │ 0x0000                      │
├─────────────────────────────────────────────────────────────┤
│ Packet type          │ 1 byte  │ 0xE8 (respuesta)            │
├─────────────────────────────────────────────────────────────┤
│ Card type            │ 1 byte  │ 0x32                        │
├─────────────────────────────────────────────────────────────┤
│ Card ID              │ 1 byte  │ ID del panel                │
├─────────────────────────────────────────────────────────────┤
│ Command code (CMD)   │ 1 byte  │ Mismo que en envío          │
├─────────────────────────────────────────────────────────────┤
│ Return value         │ 1 byte  │ 0x00: éxito                 │
│                      │         │ 0x01-0xFF: código de error  │
├─────────────────────────────────────────────────────────────┤
│ Packet data          │ Variable│ Datos de respuesta          │
├─────────────────────────────────────────────────────────────┤
│ Packet data checksum │ 2 bytes │ Checksum                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Cálculo de Checksum

**Reglas importantes:**
- Checksum es la suma de todos los bytes desde "Packet type" hasta "Packet data"
- Se usa formato 16-bit (2 bytes) sin signo
- Si la suma excede 0xFFFF, se toma solo el valor de 16 bits
- **Ejemplo**: 0xFFFA + 0x09 = 0x0003
- Formato: Low Byte primero, High Byte segundo

**Algoritmo:**
```python
def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum = (checksum + byte) & 0xFFFF
    return checksum.to_bytes(2, 'little')  # Low byte first
```

### 2.3 Configuración de Red

- **Puerto estándar**: 5200 (TCP)
- **ID Code**: 0xFFFFFFFF (255.255.255.255) - común para todos los paneles
- **Protocolo**: TCP/IP
- **Timeout recomendado**: 5-10 segundos

---

## 3. Comandos Principales del Protocolo

### 3.1 Comando 0x7B - Protocolo de Control de Ventanas y Contenido

Este es el comando principal para enviar contenido a los paneles.

#### 3.1.1 Crear Ventana (Subcomando 0x01)

**Estructura:**
```
┌─────────────────────────────────────────────────────────────┐
│ Comando CC                  │ 1 byte │ 0x01                  │
├─────────────────────────────────────────────────────────────┤
│ Número de ventanas          │ 1 byte │ Cantidad a crear      │
├─────────────────────────────────────────────────────────────┤
│ Para cada ventana:                                         │
│   - Coordenada X            │ 2 bytes│ Posición X (little)   │
│   - Coordenada Y            │ 2 bytes│ Posición Y (little)   │
│   - Ancho                   │ 2 bytes│ Ancho (little)        │
│   - Alto                    │ 2 bytes│ Alto (little)         │
└─────────────────────────────────────────────────────────────┘
```

**Ejemplo - Crear 1 ventana de 64x8 en (0,0):**
```
0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x08, 0x00
```

**Ejemplo - Crear 2 ventanas:**
```
0x01, 0x02, 
  0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x08, 0x00,  // Ventana 0: 32x8 en (0,0)
  0x00, 0x00, 0x00, 0x08, 0x20, 0x00, 0x08, 0x00   // Ventana 1: 32x8 en (0,8)
```

#### 3.1.2 Enviar Texto a Ventana (Subcomando 0x02)

**Estructura:**
```
┌─────────────────────────────────────────────────────────────┐
│ Comando CC                  │ 1 byte │ 0x02                  │
├─────────────────────────────────────────────────────────────┤
│ Número de ventana           │ 1 byte │ 0x00, 0x01, ...       │
├─────────────────────────────────────────────────────────────┤
│ Efecto texto                │ 1 byte │ 0x00: Instantáneo     │
│                             │         │ Otros: efectos       │
├─────────────────────────────────────────────────────────────┤
│ Alineación                  │ 1 byte │ 0x00: Left Top        │
│                             │         │ 0x04: Left Center    │
│                             │         │ 0x05: Center Center  │
│                             │         │ 0x06: Right Center   │
├─────────────────────────────────────────────────────────────┤
│ Velocidad efecto            │ 1 byte │ 0x00: más rápido      │
├─────────────────────────────────────────────────────────────┤
│ Tiempo espera               │ 2 bytes│ Tiempo en segundos    │
│                             │         │ (little endian)      │
├─────────────────────────────────────────────────────────────┤
│ Para cada carácter:                                        │
│   - Carácter                │ 1 byte │ Código ASCII          │
│   - Color + Tamaño          │ 1 byte │ (color << 4) | font   │
│   - Reservado               │ 1 byte │ 0x00                  │
├─────────────────────────────────────────────────────────────┤
│ Fin de texto                │ 3 bytes│ 0x00, 0x00, 0x00      │
└─────────────────────────────────────────────────────────────┘
```

**Cálculo de Color + Tamaño:**
```python
# Colores (1 byte)
RED = 0x01
GREEN = 0x02
YELLOW = 0x03
BLUE = 0x04
PURPLE = 0x05
CYAN = 0x06
WHITE = 0x07

# Tamaños de fuente (hex)
FONT_8 = 0x00
FONT_12 = 0x01
FONT_16 = 0x02
FONT_24 = 0x03
FONT_32 = 0x04
FONT_40 = 0x05
FONT_48 = 0x06
FONT_56 = 0x07

# Cálculo: (color << 4) | font
color_font_byte = (color << 4) | font
```

**Ejemplo - Enviar "hola" en rojo, tamaño 8px a ventana 0:**
```
0x02, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03,
  0x68, 0x10, 0x00,  // 'h' rojo 8px
  0x6f, 0x10, 0x00,  // 'o' rojo 8px
  0x6c, 0x10, 0x00,  // 'l' rojo 8px
  0x61, 0x10, 0x00,  // 'a' rojo 8px
  0x00, 0x00, 0x00   // Fin
```

**Ejemplo - Enviar "hola" en verde, tamaño 8px a ventana 1:**
```
0x02, 0x01, 0x00, 0x00, 0x03, 0x00, 0x03,
  0x68, 0x20, 0x00,  // 'h' verde 8px
  0x6f, 0x20, 0x00,  // 'o' verde 8px
  0x6c, 0x20, 0x00,  // 'l' verde 8px
  0x61, 0x20, 0x00,  // 'a' verde 8px
  0x00, 0x00, 0x00   // Fin
```

#### 3.1.3 Enviar Imagen a Ventana (Subcomando 0x03)

**Estructura:**
```
┌─────────────────────────────────────────────────────────────┐
│ Comando CC                  │ 1 byte │ 0x03                  │
├─────────────────────────────────────────────────────────────┤
│ Número de ventana           │ 1 byte │ ID ventana            │
├─────────────────────────────────────────────────────────────┤
│ Modo de mostrar             │ 1 byte │ 0x00: Draw            │
│                             │         │ Otros: efectos       │
├─────────────────────────────────────────────────────────────┤
│ Velocidad mostrar           │ 1 byte │ Velocidad             │
├─────────────────────────────────────────────────────────────┤
│ Tiempo de espera            │ 2 bytes│ Tiempo (little)       │
├─────────────────────────────────────────────────────────────┤
│ Referencia archivo          │ 1 byte │ 0x02: GIF             │
├─────────────────────────────────────────────────────────────┤
│ Coordenada X                │ 2 bytes│ X (little)            │
├─────────────────────────────────────────────────────────────┤
│ Coordenada Y                │ 2 bytes│ Y (little)            │
├─────────────────────────────────────────────────────────────┤
│ Nombre archivo              │ Variable│ ASCII, terminado 0x00│
└─────────────────────────────────────────────────────────────┘
```

**Ejemplo - Mostrar imagen "test.gif" en ventana 0:**
```
0x03, 0x00, 0x00, 0x01, 0x00, 0x03, 0x02, 
  0x00, 0x00, 0x00, 0x00,
  't', 'e', 's', 't', '.', 'g', 'i', 'f', 0x00
```

#### 3.1.4 Ejecutar Programa (Subcomando 0x08)

**Estructura:**
```
┌─────────────────────────────────────────────────────────────┐
│ Comando CC                  │ 1 byte │ 0x08                  │
├─────────────────────────────────────────────────────────────┤
│ Reservado                   │ 1 byte │ 0x00                  │
├─────────────────────────────────────────────────────────────┤
│ Cantidad de programas       │ 1 byte │ Número                │
├─────────────────────────────────────────────────────────────┤
│ Número de programa          │ 1 byte │ ID programa (1-N)     │
└─────────────────────────────────────────────────────────────┘
```

**Ejemplo - Ejecutar programa 1:**
```
0x08, 0x00, 0x01, 0x01
```

### 3.2 Comando 0x04 - Texto Estático (Alternativo)

**Estructura simplificada para texto estático:**
```
┌─────────────────────────────────────────────────────────────┐
│ Número de paquete           │ 1 byte │ 0x00                  │
├─────────────────────────────────────────────────────────────┤
│ Último paquete              │ 1 byte │ 0x00                  │
├─────────────────────────────────────────────────────────────┤
│ Tipo de dato                │ 1 byte │ 0x04: Texto estático  │
├─────────────────────────────────────────────────────────────┤
│ Número de ventana           │ 1 byte │ ID ventana            │
├─────────────────────────────────────────────────────────────┤
│ Tipo de dato                │ 1 byte │ 0x01                  │
├─────────────────────────────────────────────────────────────┤
│ Alineación                  │ 1 byte │ 0x00: Left Top        │
├─────────────────────────────────────────────────────────────┤
│ Área X                      │ 2 bytes│ X (little)            │
├─────────────────────────────────────────────────────────────┤
│ Área Y                      │ 2 bytes│ Y (little)            │
├─────────────────────────────────────────────────────────────┤
│ Ancho área                  │ 2 bytes│ Ancho (little)        │
├─────────────────────────────────────────────────────────────┤
│ Alto área                   │ 2 bytes│ Alto (little)         │
├─────────────────────────────────────────────────────────────┤
│ Fuente                      │ 1 byte │ Código fuente         │
├─────────────────────────────────────────────────────────────┤
│ Color R                     │ 1 byte │ 0x00-0xFF             │
├─────────────────────────────────────────────────────────────┤
│ Color G                     │ 1 byte │ 0x00-0xFF             │
├─────────────────────────────────────────────────────────────┤
│ Color B                     │ 1 byte │ 0x00-0xFF             │
├─────────────────────────────────────────────────────────────┤
│ Texto                       │ Variable│ ASCII, terminado 0x00│
└─────────────────────────────────────────────────────────────┘
```

**Ejemplo - Texto "hola" en coordenadas (32,0), área 32x8, color rojo:**
```
0x00, 0x00, 0x04, 0x00, 0x01, 0x00, 
  0x20, 0x00, 0x00, 0x00, 0x20, 0x00, 0x08, 0x00,
  0x00, 0xFF, 0xFF, 0x00,
  'h', 'o', 'l', 'a', 0x00
```

---

## 4. Efectos y Animaciones

### 4.1 Efectos de Texto

| Código | Efecto                    | Descripción                    |
|--------|---------------------------|--------------------------------|
| 0x00   | Draw                      | Instantáneo                    |
| 0x01   | Open from left            | Abrir desde izquierda          |
| 0x02   | Open from right           | Abrir desde derecha            |
| 0x06   | Move to left              | Mover a izquierda              |
| 0x07   | Move to right             | Mover a derecha                |
| 0x0A   | Scroll up                 | Scroll hacia arriba            |
| 0x0B   | Scroll to left            | Scroll a izquierda             |
| 0x0C   | Scroll to right           | Scroll a derecha               |
| 0x0D   | Flicker                   | Parpadeo                       |
| 0x0E   | Continuous scroll left    | Scroll continuo izquierda      |
| 0x0F   | Continuous scroll right   | Scroll continuo derecha        |

### 4.2 Velocidad de Efectos

- **0x00**: Más rápido
- **0x01-0xFF**: Velocidades progresivamente más lentas

### 4.3 Tiempo de Espera

- **Formato**: 2 bytes (little endian)
- **Unidad**: Segundos
- **Ejemplo**: 0x03, 0x00 = 3 segundos

---

## 5. Colores y Fuentes

### 5.1 Colores (1 byte)

| Valor | Color   | RGB        |
|-------|---------|------------|
| 0x01  | Red     | (255,0,0)  |
| 0x02  | Green   | (0,255,0)  |
| 0x03  | Yellow  | (255,255,0)|
| 0x04  | Blue    | (0,0,255)  |
| 0x05  | Purple  | (255,0,255)|
| 0x06  | Cyan    | (0,255,255)|
| 0x07  | White   | (255,255,255)|

### 5.2 Tamaños de Fuente

| Código | Tamaño (px) |
|--------|-------------|
| 0x00   | 8           |
| 0x01   | 12          |
| 0x02   | 16          |
| 0x03   | 24          |
| 0x04   | 32          |
| 0x05   | 40          |
| 0x06   | 48          |
| 0x07   | 56          |

### 5.3 Colores RGB (3 bytes)

Para colores personalizados:
- **Byte 1**: Red (0x00-0xFF)
- **Byte 2**: Green (0x00-0xFF)
- **Byte 3**: Blue (0x00-0xFF)

---

## 6. Alineación de Texto

| Código | Alineación        |
|--------|-------------------|
| 0x00   | Left Top          |
| 0x04   | Left Center       |
| 0x05   | Center Center     |
| 0x06   | Right Center      |

---

## 7. Requisitos Funcionales para v4.3.0

### 7.1 Funcionalidades Mínimas (MVP)

1. **Comunicación TCP/IP**
   - Conexión directa con paneles por IP
   - Manejo de timeouts y reconexión
   - Validación de respuestas

2. **Gestión de Ventanas**
   - Crear ventanas con dimensiones y posición
   - Identificar ventanas por ID

3. **Envío de Texto**
   - Texto con color (rojo, verde, amarillo, azul, etc.)
   - Tamaños de fuente (8, 12, 16, 24, 32, 40, 48, 56px)
   - Texto fijo (sin scroll)
   - Texto con scroll (izquierda, derecha, arriba, abajo)
   - Alineación (izquierda, centro, derecha)

4. **Envío de Imágenes**
   - Enviar imágenes GIF pre-cargadas en el panel
   - Especificar posición y ventana

### 7.2 Funcionalidades Avanzadas (Futuras)

1. Efectos avanzados de animación
2. Colores RGB personalizados
3. Gestión de programas guardados
4. Consulta de estado del panel
5. Control de brillo
6. Sincronización de tiempo

---

## 8. Arquitectura Propuesta

### 8.1 Estructura del Servicio

```
src/
├── panel_protocol_service.py    # Servicio principal
├── panel_protocol/
│   ├── __init__.py
│   ├── packet_builder.py        # Construcción de paquetes
│   ├── packet_parser.py         # Análisis de respuestas
│   ├── checksum.py              # Cálculo de checksum
│   ├── commands.py              # Definición de comandos
│   ├── colors.py                # Gestión de colores
│   ├── fonts.py                 # Gestión de fuentes
│   └── effects.py               # Efectos y animaciones
└── tests/
    └── test_panel_protocol.py
```

### 8.2 Clases Principales

```python
class PanelProtocolClient:
    """Cliente TCP/IP para comunicación con paneles"""
    - connect(ip, port)
    - disconnect()
    - send_packet(packet)
    - receive_response()
    
class PacketBuilder:
    """Constructor de paquetes del protocolo"""
    - build_window_create_packet()
    - build_text_packet()
    - build_image_packet()
    - build_program_execute_packet()
    
class PanelWindow:
    """Representación de una ventana del panel"""
    - id
    - x, y, width, height
    - send_text()
    - send_image()
```

### 8.3 API Pública Propuesta

```python
# Ejemplo de uso
client = PanelProtocolClient(ip="192.168.1.221", port=5200)
client.connect()

# Crear ventana
window = client.create_window(0, 0, 64, 8)

# Enviar texto
window.send_text(
    text="PARKING LLIURE",
    color=Color.GREEN,
    font_size=FontSize.SIZE_16,
    effect=Effect.SCROLL_LEFT,
    alignment=Alignment.CENTER
)

# Enviar imagen
window.send_image("test.gif", x=0, y=0)

client.disconnect()
```

---

## 9. Plan de Implementación

### Fase 1: Infraestructura Base
- [ ] Clase PanelProtocolClient (conexión TCP/IP)
- [ ] Cálculo de checksum
- [ ] Construcción de paquetes básicos
- [ ] Análisis de respuestas
- [ ] Manejo de errores y timeouts

### Fase 2: Comandos Básicos
- [ ] Crear ventanas (comando 0x01)
- [ ] Enviar texto simple (comando 0x02)
- [ ] Validación de respuestas

### Fase 3: Texto Avanzado
- [ ] Colores predefinidos
- [ ] Tamaños de fuente
- [ ] Efectos de scroll
- [ ] Alineación

### Fase 4: Imágenes
- [ ] Envío de imágenes (comando 0x03)
- [ ] Gestión de archivos en panel

### Fase 5: Testing y Documentación
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Documentación de API
- [ ] Ejemplos de uso

---

## 10. Consideraciones Técnicas

### 10.1 Manejo de Errores
- Timeout de conexión: 5 segundos
- Timeout de respuesta: 10 segundos
- Reintentos: 3 intentos
- Logging detallado de errores

### 10.2 Thread Safety
- El servicio debe ser thread-safe
- Pool de conexiones para múltiples paneles
- Lock para operaciones concurrentes

### 10.3 Performance
- Conexiones persistentes cuando sea posible
- Pool de conexiones TCP
- Cache de configuraciones de ventanas

### 10.4 Compatibilidad
- Python 3.8+
- Sin dependencias externas pesadas
- Compatible con sistema actual

---

## 11. Referencias

### 11.1 Documentos de Protocolo
- `docs/Rotulosv147/protocol/The-communication-protocol-for-Rotuloselectronicos.net.txt`
- `docs/Rotulosv147/protocol/Basic-Protocol-of-Rotuloselectronicos.net-LED-Display-Controller.txt`
- `docs/Rotulosv147/protocol/Rotuloselectronicos.net-external-calls-communication-protocol.txt`

### 11.2 Ejemplos
- `docs/Rotulosv147/protocol/Ejemplo-protocolos-texto-network.txt`
- `docs/Rotulosv147/protocol/Ejemplo-texto-estatico-protocolos-network.txt`
- `docs/Rotulosv147/protocol/Protocolo-cambio-de-programa.txt`

---

## 12. Próximos Pasos

1. ✅ Crear rama v4.3.0
2. ✅ Análisis exhaustivo de documentación
3. ⏳ Diseñar arquitectura detallada
4. ⏳ Implementar Fase 1 (Infraestructura Base)
5. ⏳ Tests y validación

---

**Documento creado**: 2025-10-02  
**Última actualización**: 2025-10-02  
**Versión**: 1.0

