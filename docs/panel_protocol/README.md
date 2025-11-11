# Panel LED - Protocolo de Comunicación TCP

Sistema de comunicación con paneles LED mediante protocolo Network TCP (Rotuloselectronicos.net).

## 📋 Descripción

Este proyecto implementa la comunicación con paneles de visualización LED a través del protocolo propietario Rotuloselectronicos.net usando TCP en el puerto 5200.

### Características

- ✅ Envío de texto con múltiples colores (7 colores disponibles)
- ✅ Múltiples tamaños de fuente (8px - 56px)
- ✅ Diferentes alineaciones (izquierda, centro, derecha)
- ✅ Efectos de visualización (estático por defecto)
- ✅ Envío de paquetes hexadecimales directos para testing
- ✅ Soporte para múltiples ventanas (0-7)
- ✅ Cálculo automático de checksums
- ✅ Gestión de conexión TCP robusta

## 🚀 Instalación

### Requisitos

- Python 3.6 o superior
- No se requieren dependencias externas (solo biblioteca estándar)

### Configuración

1. Clona o descarga el repositorio
2. Asegúrate de tener Python 3 instalado:

```bash
python3 --version
```

## 📖 Uso

### Modo Rápido - Script Interactivo

El script `test_panel.py` proporciona un menú interactivo para probar todas las funcionalidades:

```bash
python3 test_panel.py
```

O especifica la IP directamente:

```bash
python3 test_panel.py 192.168.10.110
```

### Uso Programático

#### Ejemplo 1: Enviar texto simple

```python
from panel_protocol import PanelProtocol, TextColor, FontSize

# Crear instancia del protocolo
panel = PanelProtocol(ip_address="192.168.10.110")

# Enviar texto
panel.send_text(
    text="HOLA MUNDO",
    window_number=0,
    color=TextColor.RED,
    font_size=FontSize.SIZE_16
)
```

#### Ejemplo 2: Texto con configuración completa

```python
from panel_protocol import (
    PanelProtocol, 
    TextColor, 
    FontSize, 
    TextAlignment,
    TextEffect
)

panel = PanelProtocol("192.168.10.110")

panel.send_text(
    text="BIENVENIDO",
    window_number=0,
    color=TextColor.GREEN,
    font_size=FontSize.SIZE_24,
    alignment=TextAlignment.CENTER_CENTER,
    effect=TextEffect.STATIC,
    speed=0x03,
    wait_time=0x0003
)
```

#### Ejemplo 3: Enviar hexadecimal directo

Útil para probar ejemplos de la documentación:

```python
panel = PanelProtocol("192.168.10.110")

# Ejemplo de la documentación: "hola" en rojo
hex_string = """
    ff ff ff ff
    21 00 00 00
    68 32 01 7b 01
    16 00 00 00
    02 00 00 00 03 00 03 10 00 68 10 00 6f 10 00 6c 10 00 61 00 00 00
    19 03
"""

panel.send_hex_string(hex_string)
```

## 🎨 Referencia de Parámetros

### Colores Disponibles

| Color   | Valor | Enum             |
|---------|-------|------------------|
| Rojo    | 0x01  | TextColor.RED    |
| Verde   | 0x02  | TextColor.GREEN  |
| Amarillo| 0x03  | TextColor.YELLOW |
| Azul    | 0x04  | TextColor.BLUE   |
| Morado  | 0x05  | TextColor.PURPLE |
| Cyan    | 0x06  | TextColor.CYAN   |
| Blanco  | 0x07  | TextColor.WHITE  |

### Tamaños de Fuente

| Tamaño | Valor | Enum              |
|--------|-------|-------------------|
| 8px    | 0x00  | FontSize.SIZE_8   |
| 12px   | 0x01  | FontSize.SIZE_12  |
| 16px   | 0x02  | FontSize.SIZE_16  |
| 24px   | 0x03  | FontSize.SIZE_24  |
| 32px   | 0x04  | FontSize.SIZE_32  |
| 40px   | 0x05  | FontSize.SIZE_40  |
| 48px   | 0x06  | FontSize.SIZE_48  |
| 56px   | 0x07  | FontSize.SIZE_56  |

### Alineaciones

| Alineación         | Valor | Enum                           |
|--------------------|-------|--------------------------------|
| Izquierda Arriba   | 0x00  | TextAlignment.LEFT_TOP         |
| Izquierda Centro   | 0x04  | TextAlignment.LEFT_CENTER      |
| Centro Centro      | 0x05  | TextAlignment.CENTER_CENTER    |
| Derecha Centro     | 0x06  | TextAlignment.RIGHT_CENTER     |

### Efectos

| Efecto    | Valor | Enum                |
|-----------|-------|---------------------|
| Estático  | 0x00  | TextEffect.STATIC   |

## 🔧 Configuración del Panel

### Puerto TCP

- **Puerto por defecto**: 5200
- Configurable en la clase PanelProtocol

### Ventanas

- El sistema soporta hasta 8 ventanas (0-7)
- Las ventanas deben estar pre-creadas en el panel
- Por defecto se usa la ventana 0

## 📊 Estructura del Proyecto

```
04 - PROTOCOLO_PANEL/
├── panel_protocol.py      # Módulo principal del protocolo
├── test_panel.py           # Script de pruebas interactivo
├── README.md               # Este archivo
└── docs/                   # Documentación del protocolo
    ├── The-communication-protocol-for-Rotuloselectronicos.net.txt
    ├── Basic-Protocol-of-Rotuloselectronicos.net-LED-Display-Controller.txt
    ├── Rotuloselectronicos.net-external-calls-communication-protocol.txt
    ├── Ejemplo-protocolos-texto-network.txt
    └── Protocolo-cambio-de-programa.txt
```

## 🧪 Testing

### IP de Prueba

```python
IP_PRUEBA = "192.168.10.110"
PUERTO = 5200
```

### Verificar Conectividad

Antes de usar el sistema, verifica que el panel esté accesible:

```bash
ping 192.168.10.110
```

### Menú de Pruebas

El script `test_panel.py` incluye un menú interactivo con las siguientes opciones:

1. Enviar texto simple
2. Probar diferentes colores
3. Probar diferentes tamaños
4. Probar diferentes alineaciones
5. Enviar ejemplo hexadecimal (rojo)
6. Enviar ejemplo hexadecimal (verde)
7. Mensaje personalizado
8. Ver tablas de referencia

## 📝 Notas Técnicas

### Formato de Paquete Network TCP

```
[ID Code: 4 bytes] [Network Length: 2 bytes] [Reserved: 2 bytes]
[Packet Type: 1 byte] [Card Type: 1 byte] [Card ID: 1 byte]
[Protocol Code: 1 byte] [Confirmation: 1 byte]
[Command Length: 4 bytes] [Command Data: variable]
[Checksum: 2 bytes]
```

### Cálculo de Checksum

- Suma de todos los bytes desde "Packet Type" hasta el final de "Packet Data"
- Formato: Little-endian (Low Byte, High Byte)
- Se trunca a 16 bits (0xFFFF)

### Codificación Color + Fuente

```
byte = (color << 4) | font_size
```

Ejemplo: Rojo (0x01) + 16px (0x02) = 0x12

## 🐛 Troubleshooting

### Error: Connection Refused

- Verifica que el panel esté encendido
- Verifica la IP del panel
- Verifica que el puerto 5200 esté abierto
- Comprueba la conectividad de red

### No se muestra el texto

- Verifica que la ventana especificada exista
- Comprueba que el tamaño de texto no sea muy grande para la ventana
- Verifica que el panel no esté reproduciendo otro programa

### Timeout al conectar

- Aumenta el timeout en PanelProtocol (default: 5 segundos)
- Verifica la latencia de red

## 📄 Licencia

Este proyecto está desarrollado para ALTEA - PROTOCOLO_PANEL

## 👥 Contacto

Para soporte o consultas sobre este proyecto, contacta con el equipo de desarrollo.

## 🔄 Versión

**Versión**: 1.0.0
**Fecha**: 2025-11-10
**Estado**: Primera versión funcional

---

**Nota**: Este es un sistema de primera versión que asume que las ventanas ya están creadas en el panel. Versiones futuras podrán incluir la creación dinámica de ventanas.

