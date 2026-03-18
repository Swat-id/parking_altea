# Arquitectura del Sistema de Paneles LED

## Índice

1. [Visión General](#1-visión-general)
2. [Arquitectura de Alto Nivel](#2-arquitectura-de-alto-nivel)
3. [Protocolo Nuevo (Puerto 7110)](#3-protocolo-nuevo-puerto-7110)
4. [Protocolo Antiguo - PanelSender (Puerto 8888)](#4-protocolo-antiguo---panelsender-puerto-8888)
5. [Flujo de Datos Completo](#5-flujo-de-datos-completo)
6. [Archivos del Sistema](#6-archivos-del-sistema)
7. [Generación del Hexadecimal](#7-generación-del-hexadecimal)
8. [Servicios Systemd](#8-servicios-systemd)

---

## 1. Visión General

El sistema de paneles LED soporta dos protocolos de comunicación:

| Característica | Protocolo Nuevo (7110) | Protocolo Antiguo (8888) |
|---------------|------------------------|--------------------------|
| Puerto | 7110 | 8888 |
| Implementación | Python directo | Java SDK (protocol.jar) |
| Servicio | `parking-panel-protocol.service` | `panelsender.service` |
| Framework | Flask + asyncio | FastAPI |
| Generación Hex | `packet_builder.py` | SDK Java |

---

## 2. Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│                          client/src/pages/Panels.jsx                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API BACKEND (Flask)                                │
│                          src/api_server.py                                   │
│                                                                              │
│  Endpoints:                                                                  │
│  - /api/parkings/<pid>/panels                                               │
│  - /api/panels/verify                                                        │
│  - /api/panel-schedules                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SERVICIO DE PROGRAMACIONES                            │
│                      src/panel_schedule_service.py                           │
│                                                                              │
│  Responsabilidades:                                                          │
│  - Gestionar horarios de programaciones                                      │
│  - Determinar qué mensaje enviar                                             │
│  - Convertir efectos de texto a códigos numéricos                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SERVICIO DE COMUNICACIÓN                                │
│                   src/panel_communication_service.py                         │
│                                                                              │
│  Responsabilidades:                                                          │
│  - Detectar protocolo del panel (old/new)                                    │
│  - Enrutar al servicio correcto (7110 o 8888)                               │
│  - Formatear parámetros según protocolo                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                          │                           │
           ┌──────────────┴──────────────┐            │
           │     Si protocol = "new"     │            │ Si protocol = "old"
           ▼                             │            ▼
┌──────────────────────────┐             │  ┌──────────────────────────┐
│   PROTOCOLO NUEVO        │             │  │   PROTOCOLO ANTIGUO      │
│   Puerto 7110            │             │  │   Puerto 8888            │
│                          │             │  │                          │
│   parking-panel-protocol │             │  │   panelsender.service    │
│   .service               │             │  │   (FastAPI + Java SDK)   │
└──────────────────────────┘             │  └──────────────────────────┘
           │                             │            │
           ▼                             │            ▼
┌──────────────────────────┐             │  ┌──────────────────────────┐
│  src/panel_protocol/     │             │  │  deploy/panelSender_*.py │
│  - api_server.py         │             │  │  - main.py               │
│  - panel_protocol_service│             │  │  - panel_controller.py   │
│  - packet_builder.py ◄───┼─ GENERA HEX │  │  + protocol.jar          │
│  - connection_pool.py    │             │  └──────────────────────────┘
│  - checksum.py           │             │            │
│  - constants.py          │             │            ▼
└──────────────────────────┘             │  ┌──────────────────────────┐
           │                             │  │  Java SDK (protocol.jar) │
           │                             │  │  Genera hexadecimal      │
           └─────────────┬───────────────┘  └──────────────────────────┘
                         │                             │
                         ▼                             ▼
              ┌───────────────────────────────────────────────┐
              │              PANEL LED FÍSICO                  │
              │              Puerto TCP 5200                   │
              │         (Comunicación via socket TCP)          │
              └───────────────────────────────────────────────┘
```

---

## 3. Protocolo Nuevo (Puerto 7110)

### 3.1 Archivos Involucrados

```
src/panel_protocol/
├── __init__.py              # Exportaciones del módulo
├── api_server.py            # Servidor Flask REST (puerto 7110)
├── panel_protocol_service.py # Servicio principal asíncrono
├── packet_builder.py        # ⭐ GENERA EL HEXADECIMAL
├── packet_parser.py         # Parsea respuestas del panel
├── connection_pool.py       # Pool de conexiones TCP
├── task_queue.py            # Cola de tareas asíncronas
├── result_storage.py        # Almacenamiento de resultados
├── checksum.py              # Cálculo de checksum
├── constants.py             # Constantes del protocolo
├── client.py                # Cliente para consumir la API
├── protocol_v4.py           # Protocolo v4 (16 ventanas)
└── backend_v4.py            # Backend v4
```

### 3.2 Endpoints de la API (7110)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del servicio |
| `/api/v1/panels/create-window` | POST | Crear ventanas |
| `/api/v1/panels/send-text` | POST | Enviar texto |
| `/api/v1/panels/send-image` | POST | Enviar imagen |
| `/api/v1/panels/send-raw` | POST | Enviar paquete hex crudo |
| `/api/v1/tasks/<task_id>` | GET | Resultado de tarea |

### 3.3 Flujo de Envío de Texto

```python
# 1. API recibe petición (api_server.py)
@app.route('/api/v1/panels/send-text', methods=['POST'])
def send_text():
    data = request.json
    # ...

# 2. Llama al servicio (panel_protocol_service.py)
async def send_text(self, panel_ip, panel_port, window_id, text, ...):
    # Construir paquete
    packet = PacketBuilder.build_send_text_packet(...)
    
    # Agregar a cola de tareas
    task_id = await self.task_queue.add_task(...)
    return task_id

# 3. Genera hexadecimal (packet_builder.py)
@staticmethod
def build_send_text_packet(...):
    # Construir datos del comando CC=0x02
    command_data = bytes([
        0x02,           # CC = Send Text
        window_id,      # Ventana
        effect,         # Efecto (0-70)
        alignment,      # Alineación (0-2)
        speed           # Velocidad (1-100)
    ])
    
    # Stay time (2 bytes, big-endian)
    command_data += struct.pack('>H', stay_time)
    
    # Texto en formato Rich3
    for char in text:
        command_data += bytes([color_font, 0x00, ord(char)])
    
    # Construir paquete de red
    return build_network_packet(card_id, 0x7B, command_data)

# 4. Envía via TCP (connection_pool.py)
async def send_data(self, ip, port, data):
    conn = await self.get_connection(ip, port)
    conn.sendall(data)
    response = await self._read_response(conn)
    return response
```

---

## 4. Protocolo Antiguo - PanelSender (Puerto 8888)

### 4.1 Archivos Involucrados

```
deploy/
├── panelSender_main.py           # Servidor FastAPI (puerto 8888)
├── panelSender_panel_controller.py  # Controlador que usa Java SDK

/opt/panelSender/ (en servidor)
├── main.py                       # Copia de panelSender_main.py
├── sender_newProtocol/
│   ├── panel_controller.py       # Copia de panelSender_panel_controller.py
│   └── lib/
│       └── protocol.jar          # SDK Java del fabricante
└── sender_oldProtocol/
    └── panel_controller.py       # Protocolo v1.2.6
```

### 4.2 Endpoints de la API (8888)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del servicio |
| `/api/v1/panels/send` | POST | Enviar a múltiples paneles |
| `/api/v1/panels/old/send` | POST | Enviar con protocolo antiguo |
| `/api/v1/panels/new/send` | POST | Enviar con protocolo nuevo (SDK) |

### 4.3 Flujo de Envío con SDK Java

```python
# 1. API recibe petición (main.py)
@app.post("/api/v1/panels/send")
async def send_to_panels(request: SendRequest):
    for panel in request.panels:
        if panel.protocol == "new":
            controller = new_protocol_controller
        else:
            controller = old_protocol_controller
        
        result = await controller.send_text(...)

# 2. Controlador prepara y envía (panel_controller.py)
async def send_text(self, ip, port, window_id, text, color, font_size, effect, speed):
    # Crear script Java dinámicamente
    java_script = f"""
    import com.ledare.protocol.ext.ExtSendUtil;
    ExtSendUtil extSend = new ExtSendUtil();
    extSend.sendText("{ip}", {port}, {window_id}, "{text}", 
                     {color}, {font_size}, {effect}, {speed});
    """
    
    # Ejecutar con Java
    subprocess.run(['java', '-cp', self.protocol_jar_path, ...])

# 3. Java SDK genera hexadecimal y envía directamente al panel
# (El SDK maneja internamente la generación del paquete)
```

---

## 5. Flujo de Datos Completo

### 5.1 Desde Programación hasta Panel

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PROGRAMACIÓN ACTIVA                                                  │
│    panel_schedule_service.py::_execute_schedule()                       │
│    - Detecta programación activa por horario                            │
│    - Obtiene mensaje y efecto configurados                              │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. CONVERSIÓN DE EFECTO                                                 │
│    panel_schedule_service.py::_get_effect_code()                        │
│                                                                          │
│    Entrada: "scroll_left", protocol="new"                               │
│    Salida:  14 (código 0x0E = Continuous scroll to left)                │
│                                                                          │
│    Mapeo para protocolo nuevo (Python directo, puerto 7110):            │
│    - 'static'/'center' → 11 (Scroll to left - auto-scroll)             │
│    - 'fijo' → 0 (Draw - texto fijo)                                     │
│    - 'scroll_left'/'scroll' → 14 (Continuous scroll left)              │
│    - 'scroll_right' → 15 (Continuous scroll right)                      │
│                                                                          │
│    Mapeo para protocolo antiguo (SDK Java, puerto 8888):                │
│    - 'static'/'center'/'fijo' → 2 (Fijo)                               │
│    - 'scroll_left'/'scroll_right'/'scroll' → 12 (Scroll)               │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. SERVICIO DE COMUNICACIÓN                                             │
│    panel_communication_service.py::send_custom_text()                   │
│                                                                          │
│    Detecta automáticamente el protocolo del panel desde BD:            │
│                                                                          │
│    Si protocol == "new":                                                │
│        → Llamar a _send_to_new_protocol_api() [Puerto 7110]             │
│        → Genera hexadecimal con packet_builder.py                       │
│    Si protocol == "old":                                                │
│        → Llamar a _send_to_unified_api() [Puerto 8888]                  │
│        → Usa SDK Java (protocol.jar)                                    │
└────────────────────────────────────────────────────────────────────────┘
                          │                           │
           ┌──────────────┴──────────────┐            │
           ▼                             ▼            ▼
┌─────────────────────┐      ┌─────────────────────────────┐
│ PROTOCOLO NUEVO     │      │ PROTOCOLO ANTIGUO           │
│ Puerto 7110         │      │ Puerto 8888                 │
│                     │      │                             │
│ packet_builder.py   │      │ Java SDK (protocol.jar)     │
│ genera el hex:      │      │ genera el hex internamente  │
│                     │      │                             │
│ FF FF FF FF         │      │                             │
│ [length][reserved]  │      │                             │
│ 68 32 01 7B 01      │      │                             │
│ [CC=02][params]     │      │                             │
│ [texto Rich3]       │      │                             │
│ [checksum]          │      │                             │
└─────────────────────┘      └─────────────────────────────┘
           │                             │
           └──────────────┬──────────────┘
                          ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. CONEXIÓN TCP AL PANEL                                                │
│    connection_pool.py::send_data()                                      │
│                                                                          │
│    - Conectar a panel_ip:5200                                           │
│    - Enviar paquete hexadecimal                                         │
│    - Recibir y parsear respuesta                                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. PANEL LED FÍSICO                                                     │
│    - Recibe paquete TCP                                                 │
│    - Interpreta comando 0x7B                                            │
│    - Muestra texto con efecto especificado                              │
│    - Envía respuesta de confirmación                                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Archivos del Sistema

### 6.1 Servicios de Alto Nivel

| Archivo | Ubicación | Función |
|---------|-----------|---------|
| `panel_schedule_service.py` | `src/` | Gestión de programaciones horarias |
| `panel_communication_service.py` | `src/` | Enrutamiento a protocolo correcto |
| `panel_window_service.py` | `src/` | Gestión de ventanas de paneles |
| `panel_content_rotation_service.py` | `src/` | Rotación de contenido |

### 6.2 Protocolo Nuevo (7110)

| Archivo | Ubicación | Función |
|---------|-----------|---------|
| `api_server.py` | `src/panel_protocol/` | API REST Flask |
| `panel_protocol_service.py` | `src/panel_protocol/` | Servicio asíncrono principal |
| `packet_builder.py` | `src/panel_protocol/` | **Generación de hexadecimal** |
| `packet_parser.py` | `src/panel_protocol/` | Parseo de respuestas |
| `connection_pool.py` | `src/panel_protocol/` | Pool de conexiones TCP |
| `checksum.py` | `src/panel_protocol/` | Cálculo de checksum |
| `constants.py` | `src/panel_protocol/` | Constantes y códigos de efecto |
| `task_queue.py` | `src/panel_protocol/` | Cola de tareas asíncronas |
| `result_storage.py` | `src/panel_protocol/` | Almacenamiento de resultados |

### 6.3 Protocolo Antiguo (8888 - SDK Java)

| Archivo | Ubicación | Función |
|---------|-----------|---------|
| `panelSender_main.py` | `deploy/` | API FastAPI principal |
| `panelSender_panel_controller.py` | `deploy/` | Controlador que usa SDK Java |
| `protocol.jar` | `/opt/panelSender/lib/` | SDK Java del fabricante |

### 6.4 Archivos de Configuración

| Archivo | Ubicación | Función |
|---------|-----------|---------|
| `parking-panel-protocol.service` | `deploy/` | Systemd service (7110) |
| `panelsender.service` | Servidor | Systemd service (8888) |

---

## 7. Generación del Hexadecimal

### 7.1 Estructura del Paquete (Protocolo 0x7B)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        PAQUETE DE RED COMPLETO                           │
├──────────────┬──────────┬────────────────────────────────────────────────┤
│ Offset       │ Tamaño   │ Descripción                                    │
├──────────────┼──────────┼────────────────────────────────────────────────┤
│ 0x00         │ 4 bytes  │ ID Code: 0xFFFFFFFF                            │
│ 0x04         │ 2 bytes  │ Network Length (little-endian)                 │
│ 0x06         │ 2 bytes  │ Reserved: 0x0000                               │
│ 0x08         │ 1 byte   │ Packet Type: 0x68                              │
│ 0x09         │ 1 byte   │ Card Type: 0x32                                │
│ 0x0A         │ 1 byte   │ Card ID: 0x01-0xFE (0xFF=broadcast)            │
│ 0x0B         │ 1 byte   │ Protocol Code: 0x7B                            │
│ 0x0C         │ 1 byte   │ Additional Info: 0x01 (confirmación)           │
│ 0x0D         │ 2 bytes  │ Packed Data Length (little-endian)             │
│ 0x0F         │ 1 byte   │ Packet Number (PO)                             │
│ 0x10         │ 1 byte   │ Last Packet Number (TP)                        │
│ 0x11         │ Variable │ Packet Data (CC + datos)                       │
│ Último       │ 2 bytes  │ Checksum (little-endian)                       │
└──────────────┴──────────┴────────────────────────────────────────────────┘
```

### 7.2 Subcomando CC=0x02 (Enviar Texto)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DATOS DEL COMANDO CC=0x02                        │
├──────────────┬──────────┬────────────────────────────────────────────────┤
│ Offset       │ Tamaño   │ Descripción                                    │
├──────────────┼──────────┼────────────────────────────────────────────────┤
│ 0x00         │ 1 byte   │ CC: 0x02 (Send Text)                           │
│ 0x01         │ 1 byte   │ Window ID: 0-7                                 │
│ 0x02         │ 1 byte   │ Effect: 0-70 (ver tabla de efectos)            │
│ 0x03         │ 1 byte   │ Alignment: 0=left, 1=center, 2=right           │
│ 0x04         │ 1 byte   │ Speed: 1-100 (1=rápido)                        │
│ 0x05         │ 2 bytes  │ Stay Time (big-endian)                         │
│ 0x07         │ Variable │ Texto en formato Rich3                         │
│ Último       │ 3 bytes  │ End marker: 0x00 0x00 0x00                     │
└──────────────┴──────────┴────────────────────────────────────────────────┘
```

### 7.3 Formato Rich3 para Texto

```
Por cada carácter:
┌─────────────┬─────────────┬─────────────┐
│ color_font  │    0x00     │   char      │
│  (1 byte)   │  (1 byte)   │  (1 byte)   │
└─────────────┴─────────────┴─────────────┘

color_font = (color << 4) | font_size

Ejemplo: "HOLA" en rojo (color=1), tamaño 16px (font_size=2)
color_font = (1 << 4) | 2 = 0x12

H: 0x12 0x00 0x48
O: 0x12 0x00 0x4F
L: 0x12 0x00 0x4C
A: 0x12 0x00 0x41
End: 0x00 0x00 0x00
```

### 7.4 Ejemplo de Paquete Completo

```
Texto: "HOLA"
Color: Rojo (1)
Font Size: 16px (2)
Effect: Continuous scroll left (14)
Window: 0
Speed: 3
Stay Time: 0

Paquete hexadecimal:
FF FF FF FF    <- ID Code
21 00          <- Network Length (33 bytes)
00 00          <- Reserved
68             <- Packet Type
32             <- Card Type
01             <- Card ID
7B             <- Protocol Code
01             <- Additional Info (con confirmación)
16 00          <- Packed Data Length (22 bytes)
00             <- Packet Number (PO)
00             <- Last Packet Number (TP)
02             <- CC = Send Text
00             <- Window ID = 0
0E             <- Effect = 14 (Continuous scroll left)
01             <- Alignment = center
03             <- Speed = 3
00 00          <- Stay Time = 0 (big-endian)
12 00 48       <- 'H'
12 00 4F       <- 'O'
12 00 4C       <- 'L'
12 00 41       <- 'A'
00 00 00       <- End marker
XX XX          <- Checksum
```

---

## 8. Servicios Systemd

### 8.1 parking-panel-protocol.service (Puerto 7110)

```ini
[Unit]
Description=Parking Panel Protocol Service v4.3.0
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea/src
ExecStart=/usr/bin/gunicorn -w 2 -b 0.0.0.0:7110 panel_protocol_service:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8.2 panelsender.service (Puerto 8888)

```ini
[Unit]
Description=PanelSender Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/panelSender
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8.3 Comandos de Gestión

```bash
# Protocolo nuevo (7110)
sudo systemctl status parking-panel-protocol.service
sudo systemctl restart parking-panel-protocol.service
sudo journalctl -u parking-panel-protocol.service -f

# Protocolo antiguo (8888)
sudo systemctl status panelsender.service
sudo systemctl restart panelsender.service
sudo journalctl -u panelsender.service -f

# Servicio de programaciones
sudo systemctl restart parking-schedule-monitor.service
```

---

## Resumen

| Componente | Protocolo Nuevo | Protocolo Antiguo |
|------------|-----------------|-------------------|
| **Puerto** | 7110 | 8888 |
| **Servicio** | parking-panel-protocol | panelsender |
| **Generador Hex** | `packet_builder.py` | `protocol.jar` (Java SDK) |
| **Framework** | Flask + asyncio | FastAPI |
| **Conexión TCP** | `connection_pool.py` | SDK Java interno |
| **Códigos Efecto** | 0-70 (documentación) | 1-56 (SDK interno) |

---

### Cambios v4.7

- **Routing restaurado**: `send_custom_text()` y `send_text_to_panel()` detectan automáticamente el protocolo del panel
- **Protocolo nuevo (7110)**: Paneles con `protocol_version = 'new'` usan Python directo y `packet_builder.py`
- **Protocolo antiguo (8888)**: Paneles con `protocol_version = 'old'` usan SDK Java
- **Códigos de efecto corregidos**: El protocolo nuevo usa códigos de documentación del fabricante (0, 11, 14, 15)

---

*Documento generado: 2026-03-13*
*Versión: v4.7*
