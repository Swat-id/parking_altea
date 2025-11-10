# Desarrollo v4.3.0 - Servicio de Protocolo de Paneles LED

## 📋 Resumen

Esta rama implementa un nuevo servicio de bajo nivel para comunicación directa con paneles LED Rotuloselectronicos.net, eliminando la dependencia del servicio Java intermedio y proporcionando control total del protocolo TCP/IP.

## 🎯 Objetivos

### Objetivos Principales
- ✅ Implementar comunicación TCP/IP directa con paneles
- ✅ Control completo del protocolo de bajo nivel
- ✅ Envío de texto con colores y tamaños configurables
- ✅ Soporte para texto fijo y scroll
- ✅ Envío de imágenes simples

### Objetivos Secundarios (Futuras versiones)
- Efectos avanzados de animación
- Colores RGB personalizados
- Gestión de programas guardados
- Consulta de estado del panel
- Control de brillo

## 📚 Documentación

### Documentos Principales
- **[Análisis del Protocolo](./analisis_protocolo_paneles.md)** - Análisis exhaustivo del protocolo de comunicación
- **[Arquitectura del Servicio](./arquitectura_servicio.md)** - Diseño detallado de la arquitectura (pendiente)
- **[Plan de Implementación](./plan_implementacion.md)** - Plan detallado por fases (pendiente)

### Documentos de Referencia
- `docs/Rotulosv147/protocol/` - Documentación oficial del protocolo
- `docs/Rotulosv147/protocol/The-communication-protocol-for-Rotuloselectronicos.net.txt`
- `docs/Rotulosv147/protocol/Basic-Protocol-of-Rotuloselectronicos.net-LED-Display-Controller.txt`
- `docs/Rotulosv147/protocol/Rotuloselectronicos.net-external-calls-communication-protocol.txt`

## 🔧 Estado del Desarrollo

### ✅ Completado
- [x] Creación de rama v4.3.0
- [x] Análisis exhaustivo de la documentación del protocolo
- [x] Documento de análisis del protocolo

### ⏳ En Progreso
- [ ] Diseño de arquitectura del servicio
- [ ] Plan de implementación detallado

### 📅 Pendiente
- [ ] Implementación Fase 1: Infraestructura Base
- [ ] Implementación Fase 2: Comandos Básicos
- [ ] Implementación Fase 3: Texto Avanzado
- [ ] Implementación Fase 4: Imágenes
- [ ] Implementación Fase 5: Testing y Documentación

## 🏗️ Arquitectura Propuesta

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

## 📝 Protocolo de Comunicación

### Formato de Paquete de Red

```
ID Code (4 bytes) + Network Length (2 bytes) + Reservation (2 bytes) +
Packet Type (1 byte) + Card Type (1 byte) + Card ID (1 byte) +
Command Code (1 byte) + Additional Info (1 byte) +
Packet Data (variable) + Checksum (2 bytes)
```

### Comandos Principales

- **0x7B**: Protocolo de control de ventanas y contenido
  - **0x01**: Crear ventana
  - **0x02**: Enviar texto a ventana
  - **0x03**: Enviar imagen a ventana
  - **0x08**: Ejecutar programa

- **0x04**: Texto estático (alternativo)

### Configuración

- **Puerto estándar**: 5200 (TCP)
- **ID Code**: 0xFFFFFFFF (255.255.255.255)
- **Timeout**: 5-10 segundos

## 🚀 Uso Previsto

```python
# Ejemplo de uso futuro
from src.panel_protocol_service import PanelProtocolClient
from src.panel_protocol.colors import Color
from src.panel_protocol.fonts import FontSize
from src.panel_protocol.effects import Effect

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

client.disconnect()
```

## 📊 Comparación con Sistema Actual

| Aspecto | Sistema Actual | Nuevo Servicio v4.3.0 |
|---------|----------------|------------------------|
| Comunicación | HTTP → Java Service → TCP | TCP directo |
| Dependencias | Servicio Java (puerto 8888) | Sin dependencias externas |
| Control | Limitado por API Java | Control total del protocolo |
| Performance | Intermediario añade latencia | Comunicación directa |
| Mantenimiento | Dos servicios (Python + Java) | Un solo servicio Python |

## 🔗 Enlaces Relacionados

- [Documentación del Protocolo](./analisis_protocolo_paneles.md)
- [Sistema Actual de Paneles](../panel-integration/index.md)
- [API de Paneles Actual](../PANEL_API/API_integration.md)

## 📅 Fechas Importantes

- **Inicio**: 2025-10-02
- **Análisis completado**: 2025-10-02
- **Implementación prevista**: Pendiente

---

**Versión**: 1.0  
**Última actualización**: 2025-10-02

