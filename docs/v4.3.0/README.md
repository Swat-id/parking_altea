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
- **[Desarrollo del Servicio Asíncrono](./desarrollo_servicio_asincrono.md)** - Documentación del servicio implementado
- **[Configuración de Puerto](./configuracion_puerto.md)** - Configuración del puerto 7000
- **[Integración con Backend](./integracion_backend.md)** - Cómo usar el servicio desde el backend
- **[Autenticación](./autenticacion.md)** - Sistema de autenticación JWT integrado

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
- [x] Diseño de arquitectura asíncrona
- [x] Implementación de infraestructura base
- [x] Pool de conexiones TCP
- [x] Cola de tareas asíncrona
- [x] Almacenamiento de resultados
- [x] Construcción y análisis de paquetes
- [x] Servicio principal integrado
- [x] Ejemplos de uso

### ⏳ En Progreso
- [ ] Tests unitarios
- [ ] Integración con sistema existente

### 📅 Pendiente
- [ ] API REST para exponer el servicio
- [ ] Persistencia en base de datos
- [ ] Documentación de API completa
- [ ] Tests de integración

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

## 🔌 Configuración de Puertos

### Puerto 7000 - Panel Protocol Service (FIJO)
- **Propósito**: Servicio HTTP/REST para comunicación con paneles LED
- **Tecnología**: Flask + Python asyncio
- **Protocolo**: REST API
- **URL Base**: `http://localhost:7000`
- **Endpoints**: `/api/v1/panels/*`

### Puerto 5200 - Comunicación TCP con Paneles
- **Propósito**: Puerto TCP para comunicación directa con paneles LED
- **Protocolo**: TCP/IP (protocolo Rotuloselectronicos.net)
- **Uso**: Interno del servicio (no expuesto directamente)

## 🚀 Uso del Servicio

### Uso Directo (Python)

```python
import asyncio
from src.panel_protocol import PanelProtocolService
from src.panel_protocol.constants import Color, FontSize, Effect

async def ejemplo():
    service = PanelProtocolService()
    
    # Enviar texto
    task_id = await service.send_text(
        panel_ip="192.168.1.221",
        window_id=0,
        text="PARKING LLIURE",
        color=Color.GREEN,
        font_size=FontSize.SIZE_16,
        effect=Effect.SCROLL_LEFT
    )
    
    await service.close()

asyncio.run(ejemplo())
```

### Uso a través de API REST

```bash
# Enviar texto a un panel
curl -X POST http://localhost:7000/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -d '{
    "panel_ip": "192.168.1.221",
    "window_id": 0,
    "text": "PARKING LLIURE",
    "color": 2,
    "font_size": 2,
    "effect": 11
  }'

# Verificar salud del servicio
curl http://localhost:7000/health
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

