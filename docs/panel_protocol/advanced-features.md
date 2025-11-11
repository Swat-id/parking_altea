# Funcionalidades Avanzadas - Paneles LED

Documentación completa de las funcionalidades avanzadas implementadas en `panel_advanced.py`.

## 📋 Índice

- [Introducción](#introducción)
- [Funcionalidades Implementadas](#funcionalidades-implementadas)
- [Envío de Imágenes](#envío-de-imágenes)
- [Creación de Ventanas](#creación-de-ventanas)
- [Cambio de Programas](#cambio-de-programas)
- [Guardar/Limpiar Datos](#guardarlimpiar-datos)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Compatibilidad](#compatibilidad)
- [API Reference](#api-reference)

---

## Introducción

El módulo `panel_advanced.py` proporciona funcionalidades avanzadas adicionales que complementan `panel_protocol.py` y `panel_backend.py` **sin afectar su funcionamiento**.

### Características

✅ **Compatibilidad Total**:  Las funciones existentes no se ven afectadas  
✅ **Herencia**: `PanelAdvanced` hereda de `PanelProtocol`  
✅ **Sin Conflictos**: Todas las APIs coexisten sin problemas  
✅ **Retrocompatible**: Código existente sigue funcionando  

### Nuevas Funcionalidades

| Comando | Descripción | Método |
|---------|-------------|--------|
| **CC=0x03** | Envío de imágenes | `send_image()` |
| **CC=0x01** | Creación de ventanas | `create_windows()` |
| **CC=0x08** | Cambio de programas | `select_program()` |
| **CC=0x07** | Guardar/limpiar datos | `save_data_to_flash()` |

---

## Funcionalidades Implementadas

### 1. Envío de Imágenes (CC=0x03)

Permite mostrar imágenes GIF almacenadas en el panel.

**Formatos soportados:**
- GIF_FILE_DATA (0x01): Datos del archivo GIF completo
- GIF_FILE_REFERENCE (0x02): Referencia a archivo GIF guardado en el panel ⭐
- PACKAGE_REFERENCE (0x03): Referencia a paquete de imágenes
- SIMPLE_FORMAT (0x04): Formato simple de imagen

**Modos de visualización:**
- DRAW (0x00): Dibujar directamente
- CENTER (0x00): Centrar
- ZOOM (0x01): Zoom
- STRETCH (0x02): Estirar
- TILE (0x03): Mosaico

### 2. Creación de Ventanas (CC=0x01)

Permite definir dinámicamente hasta 8 ventanas en el panel.

**Especificación:**
- Cada ventana se define por: (x, y, width, height)
- Máximo 8 ventanas
- Coordenadas relativas a la pantalla completa

### 3. Cambio de Programas (CC=0x08)

Cambia entre programas guardados en el panel.

**Especificación:**
- Programas numerados del 1 al 254
- El programa debe estar previamente guardado en el panel

### 4. Guardar/Limpiar Datos (CC=0x07)

Guarda datos actuales en flash o limpia la memoria.

**Operaciones:**
- Guardar datos actuales
- Limpiar memoria flash

---

## Envío de Imágenes

### Uso Básico

```python
from panel_advanced import PanelAdvanced, ImageFormat

panel = PanelAdvanced("192.168.10.110")

# Mostrar imagen guardada en el panel
panel.send_image(
    window_number=0,
    image_filename="logo.gif",
    image_format=ImageFormat.GIF_FILE_REFERENCE,
    stay_time=5  # segundos
)
```

### Función Rápida

```python
from panel_advanced import quick_send_image

quick_send_image(
    ip="192.168.10.110",
    window=0,
    image_filename="logo.gif",
    stay_time=5
)
```

### Parámetros Completos

```python
panel.send_image(
    window_number=0,
    image_filename="test.gif",
    image_format=ImageFormat.GIF_FILE_REFERENCE,
    mode=ImageMode.CENTER,
    speed=1,
    stay_time=3,
    x_position=0,
    y_position=0,
    verbose=True
)
```

### Ejemplo con Hexadecimal

Basado en el ejemplo de la documentación:

```python
# Ejemplo: mostrar "test.gif" en ventana 0
hex_image = """
ff ff ff ff
1f 00 00 00
68 32 01 7b 01
14 00 00 00
03 00 00 01 00 03 02 00 00 00 00 74 65 73 74 2e 67 69 66 00
58 04
"""

panel.send_hex_string(hex_image)
```

---

## Creación de Ventanas

### Uso Básico

```python
from panel_advanced import PanelAdvanced

panel = PanelAdvanced("192.168.10.110")

# Crear 2 ventanas de 64x8
windows = [
    (0, 0, 64, 8),    # Ventana 0: x=0, y=0, ancho=64, alto=8
    (0, 8, 64, 8)     # Ventana 1: x=0, y=8, ancho=64, alto=8
]

panel.create_windows(windows)
```

### Función Rápida

```python
from panel_advanced import quick_create_windows

quick_create_windows(
    ip="192.168.10.110",
    windows=[(0, 0, 64, 8), (0, 8, 64, 8)]
)
```

### Ejemplo: 7 Ventanas Horizontales

```python
# Crear 7 ventanas horizontales en un panel de 64x16
windows = []
for i in range(7):
    windows.append((
        i * 9,      # x
        0,          # y
        9,          # width
        16          # height
    ))

panel.create_windows(windows)
```

### ⚠️ Advertencias

- **Redefinir ventanas reemplaza la configuración actual**
- **Usar con precaución en producción**
- **Probar primero en panel de test**
- **Las ventanas se numeran del 0 al 7 en orden de definición**

---

## Cambio de Programas

### Uso Básico

```python
from panel_advanced import PanelAdvanced

panel = PanelAdvanced("192.168.10.110")

# Cambiar al programa 1
panel.select_program(1)
```

### Función Rápida

```python
from panel_advanced import quick_select_program

quick_select_program(
    ip="192.168.10.110",
    program_number=1
)
```

### Ejemplo con Múltiples Programas

```python
import time

panel = PanelAdvanced("192.168.10.110")

# Rotar entre programas
programas = [1, 2, 3, 4]

for programa in programas:
    print(f"Mostrando programa {programa}...")
    panel.select_program(programa)
    time.sleep(10)  # Mostrar cada programa 10 segundos
```

### Ejemplo con Hexadecimal

```python
# Ejemplo de documentación: reproducir programa 1
hex_program = """
ff ff ff ff
0f 00 00 00
68 32 01 7b 01
04 00 00 00
08 00 01 01
25 01
"""

panel.send_hex_string(hex_program)
```

---

## Guardar/Limpiar Datos

### Guardar Datos en Flash

```python
from panel_advanced import PanelAdvanced

panel = PanelAdvanced("192.168.10.110")

# Enviar contenido
panel.send_text("MENSAJE PERSISTENTE", 0)

# Guardar en flash
panel.save_data_to_flash()

# Ahora el mensaje permanecerá después de reiniciar el panel
```

### Limpiar Flash

```python
panel.clear_flash_data()
```

### Flujo Completo de Trabajo

```python
panel = PanelAdvanced("192.168.10.110")

# 1. Configurar ventanas
windows = [(0, 0, 64, 8), (0, 8, 64, 8)]
panel.create_windows(windows)

# 2. Enviar contenido
panel.send_text("VENTANA 0", 0)
panel.send_text("VENTANA 1", 1)

# 3. Guardar configuración y datos
panel.save_data_to_flash()

# Ahora la configuración persiste al reiniciar
```

---

## Ejemplos de Uso

### Ejemplo 1: Panel con Imagen y Texto

```python
from panel_advanced import PanelAdvanced
from panel_protocol import TextColor, FontSize

panel = PanelAdvanced("192.168.10.110")

# Ventana 0: Logo (imagen)
panel.send_image(
    window_number=0,
    image_filename="logo.gif",
    stay_time=0  # Sin timeout, permanente
)

# Ventana 1: Texto
panel.send_text(
    text="BIENVENIDO",
    window_number=1,
    color=TextColor.GREEN,
    font_size=FontSize.SIZE_24
)
```

### Ejemplo 2: Rotación de Contenido

```python
import time

panel = PanelAdvanced("192.168.10.110")

contenidos = [
    {"tipo": "texto", "data": "MENSAJE 1"},
    {"tipo": "imagen", "data": "promo1.gif"},
    {"tipo": "texto", "data": "MENSAJE 2"},
    {"tipo": "imagen", "data": "promo2.gif"}
]

for contenido in contenidos:
    if contenido["tipo"] == "texto":
        panel.send_text(contenido["data"], 0)
    else:
        panel.send_image(0, contenido["data"], stay_time=5)
    
    time.sleep(5)
```

### Ejemplo 3: Configuración Inicial de Panel

```python
panel = PanelAdvanced("192.168.10.110")

# 1. Limpiar configuración anterior
panel.clear_flash_data()

# 2. Crear estructura de ventanas
windows = [
    (0, 0, 64, 4),    # Header
    (0, 4, 64, 8),    # Contenido principal
    (0, 12, 64, 4)    # Footer
]
panel.create_windows(windows)

# 3. Configurar contenido inicial
panel.send_text("EMPRESA XYZ", 0, color=TextColor.YELLOW)
panel.send_text("BIENVENIDO", 1, color=TextColor.GREEN)
panel.send_text("www.empresa.com", 2, color=TextColor.CYAN)

# 4. Guardar configuración
panel.save_data_to_flash()
```

---

## Compatibilidad

### Herencia de PanelProtocol

`PanelAdvanced` hereda de `PanelProtocol`, por lo que **todos los métodos existentes están disponibles**:

```python
from panel_advanced import PanelAdvanced
from panel_protocol import TextColor, TextEffect

panel = PanelAdvanced("192.168.10.110")

# Métodos heredados (todos funcionan)
panel.send_text("TEXTO", 0, TextColor.GREEN)
panel.send_hex_string("ff ff ff ff ...")
packet = panel.build_text_packet("TEST")

# Métodos nuevos
panel.send_image(0, "logo.gif")
panel.create_windows([(0, 0, 64, 8)])
panel.select_program(1)
```

### Coexistencia con Otros Módulos

Todos los módulos funcionan juntos sin conflictos:

```python
# Usar panel_protocol
from panel_protocol import PanelProtocol
panel_basic = PanelProtocol("192.168.10.110")
panel_basic.send_text("BASICO", 0)

# Usar panel_backend
from panel_backend import PanelBackend
backend = PanelBackend("192.168.10.110")
backend.send_to_window(0, "BACKEND")

# Usar panel_advanced
from panel_advanced import PanelAdvanced
advanced = PanelAdvanced("192.168.10.110")
advanced.send_image(0, "logo.gif")
advanced.send_text("AVANZADO", 1)  # Método heredado
```

### Tests de Validación

Ejecutar tests para verificar compatibilidad:

```bash
python3 test_advanced_functions.py
```

El script ejecuta 6 suites de tests:
1. Funciones Básicas (panel_protocol)
2. Funciones Backend (panel_backend)
3. Funciones Avanzadas (panel_advanced)
4. Compatibilidad y Herencia
5. Funciones Rápidas
6. Integración Completa

---

## API Reference

### Clase PanelAdvanced

```python
class PanelAdvanced(PanelProtocol):
    """Clase extendida con funcionalidades avanzadas"""
```

#### Métodos de Envío

**send_image()**
```python
def send_image(
    self,
    window_number: int,
    image_filename: str,
    image_format: ImageFormat = ImageFormat.GIF_FILE_REFERENCE,
    mode: ImageMode = ImageMode.DRAW,
    speed: int = 0x01,
    stay_time: int = 0x0003,
    x_position: int = 0x0000,
    y_position: int = 0x0000,
    verbose: bool = True
) -> bool
```

**create_windows()**
```python
def create_windows(
    self,
    windows: List[Tuple[int, int, int, int]],
    verbose: bool = True
) -> bool
```

**select_program()**
```python
def select_program(
    self,
    program_number: int,
    verbose: bool = True
) -> bool
```

**save_data_to_flash()**
```python
def save_data_to_flash(
    self,
    verbose: bool = True
) -> bool
```

**clear_flash_data()**
```python
def clear_flash_data(
    self,
    verbose: bool = True
) -> bool
```

#### Métodos de Construcción

**build_image_packet()**
```python
def build_image_packet(
    self,
    window_number: int,
    image_filename: str,
    image_format: ImageFormat = ImageFormat.GIF_FILE_REFERENCE,
    mode: ImageMode = ImageMode.DRAW,
    speed: int = 0x01,
    stay_time: int = 0x0003,
    x_position: int = 0x0000,
    y_position: int = 0x0000
) -> bytes
```

**build_create_windows_packet()**
```python
def build_create_windows_packet(
    self,
    windows: List[Tuple[int, int, int, int]]
) -> bytes
```

**build_select_program_packet()**
```python
def build_select_program_packet(
    self,
    program_number: int
) -> bytes
```

**build_save_data_packet()**
```python
def build_save_data_packet(
    self,
    save: bool = True
) -> bytes
```

### Funciones Rápidas

**quick_send_image()**
```python
def quick_send_image(
    ip: str,
    window: int,
    image_filename: str,
    stay_time: int = 3,
    verbose: bool = False
) -> bool
```

**quick_create_windows()**
```python
def quick_create_windows(
    ip: str,
    windows: List[Tuple[int, int, int, int]],
    verbose: bool = False
) -> bool
```

**quick_select_program()**
```python
def quick_select_program(
    ip: str,
    program_number: int,
    verbose: bool = False
) -> bool
```

### Enumeraciones

**ImageFormat**
```python
class ImageFormat(IntEnum):
    GIF_FILE_DATA = 0x01
    GIF_FILE_REFERENCE = 0x02  # Más común
    PACKAGE_REFERENCE = 0x03
    SIMPLE_FORMAT = 0x04
```

**ImageMode**
```python
class ImageMode(IntEnum):
    DRAW = 0x00
    CENTER = 0x00
    ZOOM = 0x01
    STRETCH = 0x02
    TILE = 0x03
```

---

## Mejores Prácticas

### 1. Preparar Archivos de Imagen

Antes de usar `send_image()`, asegúrate de que la imagen está en el panel:

```python
# Opción 1: Subir imagen previamente usando el software del fabricante
# Opción 2: Usar comando de escritura de archivos (futuro)
```

### 2. Testar Ventanas en Panel de Prueba

Antes de redefinir ventanas en producción:

```python
# Siempre probar en panel de test primero
if ENVIRONMENT == "test":
    panel.create_windows(new_layout)
else:
    logger.warning("Redefining windows in production - use caution")
    panel.create_windows(new_layout)
```

### 3. Guardar Configuraciones Importantes

```python
# Después de configurar el panel
panel.create_windows(windows)
panel.send_text("CONFIG", 0)

# Guardar para que persista
panel.save_data_to_flash()
```

### 4. Manejo de Errores

```python
try:
    success = panel.send_image(0, "logo.gif")
    if not success:
        logger.error("Failed to send image")
        # Fallback a texto
        panel.send_text("LOGO", 0)
except Exception as e:
    logger.exception("Error sending image")
    # Implementar fallback
```

---

## Troubleshooting

### Imagen no se muestra

**Posibles causas:**
- Archivo no existe en el panel
- Formato incompatible
- Nombre de archivo incorrecto

**Solución:**
```python
# Verificar formato y nombre
panel.send_image(
    window_number=0,
    image_filename="test.gif",  # Verificar nombre exacto
    image_format=ImageFormat.GIF_FILE_REFERENCE,
    verbose=True  # Ver detalles del error
)
```

### Ventanas no se crean

**Posibles causas:**
- Coordenadas fuera de rango
- Solapamiento de ventanas
- Más de 8 ventanas

**Solución:**
```python
# Validar coordenadas
screen_width = 64
screen_height = 16

windows = [
    (0, 0, 32, 16),    # OK
    (32, 0, 32, 16)    # OK
]

panel.create_windows(windows, verbose=True)
```

### Programa no cambia

**Posibles causas:**
- Programa no existe en el panel
- Número de programa incorrecto

**Solución:**
```python
# Verificar que el programa existe
try:
    panel.select_program(1, verbose=True)
except Exception as e:
    print(f"Programa no disponible: {e}")
```

---

## Roadmap Futuro

### Próximas Funcionalidades

- [ ] Subida de archivos de imagen (CC=0x30/0x32/0x33)
- [ ] Texto estático (CC=0x04)
- [ ] Reloj (CC=0x05)
- [ ] Control de brillo (CMD=0x46)
- [ ] Sincronización de hora (CMD=0x47)
- [ ] Configuración de red (CMD=0x3C)

---

## Resumen

### ✅ Lo que se implementó

- **Envío de imágenes** (CC=0x03)
- **Creación de ventanas** (CC=0x01)
- **Cambio de programas** (CC=0x08)
- **Guardar/limpiar datos** (CC=0x07)

### ✅ Garantías

- Funciones existentes no afectadas
- Herencia correcta de PanelProtocol
- Sin conflictos entre módulos
- Tests de validación completos

### 📚 Documentación Relacionada

- [README.md](../README.md) - Guía general
- [backend-integration.md](backend-integration.md) - Integración backend
- [DESARROLLO_PROTOCOLO_PANEL.md](DESARROLLO_PROTOCOLO_PANEL.md) - Detalles técnicos

---

**Versión**: 1.1.0  
**Fecha**: 10 de Noviembre de 2025  
**Mantenido por**: Equipo ALTEA - PROTOCOLO_PANEL

