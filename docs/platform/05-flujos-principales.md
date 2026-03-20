# Flujos Principales del Sistema

## 1. Flujo de Actualización de Paneles

### 1.1 Diagrama General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE ACTUALIZACIÓN DE PANELES                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌───────────────────┐     ┌──────────────────────────┐
│  panel_worker_   │     │  panel_type3_and_ │     │ schedule_monitor_        │
│  service.py      │     │  4_worker_service │     │ service.py               │
│  (Tipo 1, 2)     │     │  .py (Tipo 3, 4)  │     │ (Verificar programaciones)│
└────────┬─────────┘     └─────────┬─────────┘     └────────────┬─────────────┘
         │                         │                            │
         │ cada 120s               │ cada 120s                  │ cada 300s
         ▼                         ▼                            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              ¿PROGRAMACIÓN ACTIVA?                           │
│                                                                              │
│    SELECT * FROM panel_schedules WHERE is_active = true                      │
│    AND parking_id = ? AND start_time <= now() AND end_time >= now()          │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼ SÍ                                ▼ NO
    ┌───────────────────────────┐       ┌───────────────────────────┐
    │   Enviar mensaje de       │       │   Calcular estado de      │
    │   programación activa     │       │   ocupación del parking   │
    │   (schedule.message)      │       │   (LIBRE/DENSO/COMPLETO)  │
    └─────────────┬─────────────┘       └─────────────┬─────────────┘
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       panel_communication_service.py                          │
│                              send_custom_text()                               │
│                                                                              │
│    1. Obtener protocol_version del panel desde BD                            │
│    2. Mapear effect string a código numérico                                 │
│    3. Routing basado en protocol_version                                     │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼ protocol='new'                    ▼ protocol='old'
    ┌───────────────────────────┐       ┌───────────────────────────┐
    │   _send_to_new_protocol_  │       │   _send_to_unified_api()  │
    │   api()                   │       │                           │
    │   Puerto 7110             │       │   Puerto 8888             │
    │   (Python directo)        │       │   (SDK Java)              │
    └─────────────┬─────────────┘       └─────────────┬─────────────┘
                  │                                   │
                  ▼                                   ▼
    ┌───────────────────────────┐       ┌───────────────────────────┐
    │  panel_protocol/          │       │  /opt/panelSender/        │
    │  packet_builder.py        │       │  main.py                  │
    │                           │       │                           │
    │  Genera paquete           │       │  Llama a protocol.jar     │
    │  hexadecimal              │       │  (Java SDK)               │
    └─────────────┬─────────────┘       └─────────────┬─────────────┘
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                    ┌───────────────────────────┐
                    │     PANEL LED FÍSICO      │
                    │     TCP Puerto 5200       │
                    └───────────────────────────┘
```

### 1.2 Mapeo de Efectos

#### Para protocolo NUEVO (7110)
```python
effect_map_new = {
    0: 0,    # Draw/Fijo -> Draw (0x00)
    1: 0,    # Instant -> Draw
    2: 11,   # Scroll_left (auto) -> Scroll to left (0x0B)
    11: 11,  # Ya es código directo
    12: 11,  # Scroll antiguo -> Scroll to left
    14: 14,  # Continuous scroll left (0x0E)
    15: 15,  # Continuous scroll right (0x0F)
    55: 14,  # SDK Scrollleft_continuously -> Continuous scroll left
    56: 15,  # SDK Scroll_right_continuously -> Continuous scroll right
}
```

#### Para protocolo ANTIGUO (8888)
```python
effect_map_old = {
    1: 1,    # Instant (estático)
    2: 2,    # Scroll_left (auto-scroll si texto largo)
    3: 3,    # Scroll_right
    55: 55,  # Scroll continuo izquierda
    56: 56,  # Scroll continuo derecha
}
```

### 1.3 Códigos de Efecto (Protocolo Directo)

| Código | Hex | Nombre | Comportamiento |
|--------|-----|--------|----------------|
| 0 | 0x00 | DRAW | Texto estático, nunca hace scroll |
| 11 | 0x0B | SCROLL_LEFT | Scroll con pausa (stay_time > 0) |
| 12 | 0x0C | SCROLL_RIGHT | Scroll derecha con pausa |
| 14 | 0x0E | CONTINUOUS_SCROLL_LEFT | Scroll continuo (stay_time = 0) |
| 15 | 0x0F | CONTINUOUS_SCROLL_RIGHT | Scroll continuo derecha |

## 2. Flujo de Conteo de Vehículos

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          FLUJO DE CONTEO                                   │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     HTTP POST      ┌──────────────────┐
│   CÁMARA     │ ──────────────────→│  camera_server   │
│  (Conteo)    │  /api/camera/event │  Puerto 3535     │
└──────────────┘                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Parsear mensaje  │
                                    │ JSON de cámara   │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Buscar cámara    │
                                    │ en tabla accesses│
                                    │ por IP + Line    │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Calcular delta   │
                                    │ entradas/salidas │
                                    │                  │
                                    │ delta_in =       │
                                    │   vehicle_in -   │
                                    │   last_vehicle_in│
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Actualizar       │
                                    │ parking:         │
                                    │                  │
                                    │ occupancy +=     │
                                    │   delta_in -     │
                                    │   delta_out      │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Aplicar límites: │
                                    │ 0 <= occupancy   │
                                    │   <= max_capacity│
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Calcular estado: │
                                    │                  │
                                    │ if occ >= full:  │
                                    │   COMPLETO       │
                                    │ elif occ >=dense:│
                                    │   DENSO          │
                                    │ else:            │
                                    │   LIBRE          │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Guardar en       │
                                    │ occupancy_history│
                                    │ y camera_logs    │
                                    └──────────────────┘
```

## 3. Flujo de Programaciones

### 3.1 Ejecución Automática

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE PROGRAMACIONES AUTOMÁTICAS                     │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│ schedule_monitor_    │
│ service.py           │
│ (cada 5 minutos)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Consultar            │
│ panel_schedules      │
│ WHERE is_active=true │
│ AND now() BETWEEN    │
│ start_time AND       │
│ end_time             │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐     ┌──────────────────────┐
│ Para cada            │────→│ panel_schedule_      │
│ programación activa  │     │ service.py           │
└──────────────────────┘     │ execute_schedule()   │
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │ Obtener paneles      │
                             │ del parking asociado │
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │ Por cada panel:      │
                             │                      │
                             │ 1. Detectar protocol │
                             │ 2. Mapear effect     │
                             │ 3. Enviar mensaje    │
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │ Registrar en         │
                             │ panel_schedule_logs  │
                             └──────────────────────┘
```

### 3.2 Ejecución Manual (API)

```
POST /api/schedules/{id}/execute
         │
         ▼
┌──────────────────────┐
│ panel_schedule_      │
│ service.py           │
│ execute_schedule()   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ _execute_schedule_   │
│ thread_safe()        │
│                      │
│ 1. Obtener schedule  │
│ 2. Obtener parking   │
│ 3. Obtener paneles   │
│ 4. Detectar protocol │
│ 5. Mapear effect     │
│ 6. Enviar a cada     │
│    panel             │
└──────────────────────┘
```

## 4. Flujo de Envío de Mensaje a Panel

### 4.1 Protocolo Nuevo (Puerto 7110)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FLUJO PROTOCOLO NUEVO (7110)                            │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│ panel_communication_ │
│ service.py           │
│ send_custom_text()   │
└──────────┬───────────┘
           │ HTTP POST
           ▼
┌──────────────────────┐     ┌──────────────────────────────────────────┐
│ POST localhost:7110/ │     │                                          │
│ api/v1/panels/send-  │────→│  panel_protocol/api_server.py            │
│ text                 │     │                                          │
└──────────────────────┘     └──────────────────┬───────────────────────┘
                                                │
                                                ▼
                             ┌──────────────────────────────────────────┐
                             │  panel_protocol_service.py               │
                             │  PanelProtocolService.send_text()        │
                             └──────────────────┬───────────────────────┘
                                                │
                                                ▼
                             ┌──────────────────────────────────────────┐
                             │  packet_builder.py                       │
                             │  build_text_packet()                     │
                             │                                          │
                             │  1. Construir header (0xFF x 4)          │
                             │  2. Calcular longitud                    │
                             │  3. Añadir card_id, comando 0x7B         │
                             │  4. Añadir subcomando 0x02               │
                             │  5. Codificar texto Rich3                │
                             │     (3 bytes por char)                   │
                             │  6. Calcular checksum                    │
                             └──────────────────┬───────────────────────┘
                                                │
                                                ▼
                             ┌──────────────────────────────────────────┐
                             │  connection_pool.py                      │
                             │                                          │
                             │  1. Conectar TCP a panel_ip:5200         │
                             │  2. Enviar paquete hexadecimal           │
                             │  3. Esperar respuesta                    │
                             │  4. Parsear respuesta                    │
                             └──────────────────────────────────────────┘
```

### 4.2 Estructura del Paquete Hexadecimal

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    ESTRUCTURA PAQUETE 0x7B (SEND_TEXT)                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────┬──────────┬──────────┬───────────┬─────────────┬───────────┐  │
│  │  Header  │  Length  │  Card ID │  Command  │    Data     │  Checksum │  │
│  │  4 bytes │  4 bytes │  1 byte  │  1 byte   │   N bytes   │  2 bytes  │  │
│  │  0xFFx4  │ (little) │   0x68   │   0x7B    │             │  (sum)    │  │
│  └──────────┴──────────┴──────────┴───────────┴─────────────┴───────────┘  │
│                                                                            │
│  Estructura de Data para 0x7B (subcomando 0x02):                          │
│                                                                            │
│  ┌───────────┬────────────┬─────────┬──────────┬───────────┬────────────┐  │
│  │ Packed    │ PO   │ TP  │ Window  │ Sub-cmd  │  Effect   │ Stay Time  │  │
│  │ Len (2B)  │ 1B   │ 1B  │   ID    │  0x02    │   Code    │  (2 bytes) │  │
│  └───────────┴──────┴─────┴─────────┴──────────┴───────────┴────────────┘  │
│                                                                            │
│  ┌───────────┬───────────┬───────────┬────────────────────────────────┐   │
│  │ Alignment │   Speed   │ Text Len  │         Text (Rich3)           │   │
│  │   (1B)    │   (1B)    │  (2 bytes)│    (3 bytes por caracter)      │   │
│  └───────────┴───────────┴───────────┴────────────────────────────────┘   │
│                                                                            │
│  Rich3 Text Encoding: [color_font] [0x00] [character]                      │
│  Ejemplo: 'A' verde = 0x12 0x00 0x41                                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Protocolo Antiguo (Puerto 8888)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FLUJO PROTOCOLO ANTIGUO (8888)                          │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│ panel_communication_ │
│ service.py           │
│ send_custom_text()   │
└──────────┬───────────┘
           │ HTTP POST
           ▼
┌──────────────────────┐     ┌──────────────────────────────────────────┐
│ POST localhost:8888/ │     │                                          │
│ api/v1/panels/send   │────→│  /opt/panelSender/main.py                │
└──────────────────────┘     │  FastAPI                                 │
                             └──────────────────┬───────────────────────┘
                                                │
                                                ▼
                             ┌──────────────────────────────────────────┐
                             │  sender_oldProtocol/panel_controller.py  │
                             │                                          │
                             │  1. Preparar parámetros                  │
                             │  2. Llamar a subprocess con Java         │
                             │  3. Ejecutar protocol.jar                │
                             └──────────────────┬───────────────────────┘
                                                │
                                                ▼
                             ┌──────────────────────────────────────────┐
                             │  Java SDK (protocol.jar)                 │
                             │                                          │
                             │  1. Inicializar red                      │
                             │  2. Conectar a panel_ip:5200             │
                             │  3. Enviar comando con SDK               │
                             │  4. Retornar resultado                   │
                             └──────────────────────────────────────────┘
```

## 5. Flujo de Autenticación

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          FLUJO DE AUTENTICACIÓN                            │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     POST /api/auth/login     ┌──────────────────┐
│   Frontend   │ ────────────────────────────→│   API Backend    │
│   (React)    │  {email, password}           │   Puerto 6001    │
└──────────────┘                              └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ auth.py          │
                                              │ verify_password()│
                                              └────────┬─────────┘
                                                       │
                                              ┌────────┴────────┐
                                              │                 │
                                              ▼ Correcto        ▼ Incorrecto
                                    ┌──────────────────┐  ┌──────────────┐
                                    │ Generar JWT      │  │ Error 401    │
                                    │ create_access_   │  │ Unauthorized │
                                    │ token()          │  └──────────────┘
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Retornar:        │
                                    │ {                │
                                    │   access_token,  │
                                    │   user: {...}    │
                                    │ }                │
                                    └──────────────────┘

                    Peticiones Protegidas:

┌──────────────┐     GET /api/protected      ┌──────────────────┐
│   Frontend   │ ───────────────────────────→│   API Backend    │
│   (React)    │  Header: Bearer {token}     │                  │
└──────────────┘                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │ @token_required  │
                                             │ decorator        │
                                             │                  │
                                             │ 1. Extraer token │
                                             │ 2. Validar JWT   │
                                             │ 3. Obtener user  │
                                             └──────────────────┘
```

## 6. Flujo de Detección por Plaza (Spot Detection)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FLUJO DETECCIÓN POR PLAZA                               │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     HTTP POST           ┌──────────────────┐
│   CÁMARA         │ ───────────────────────→│  camera_server   │
│  (Spot Detection)│  /api/camera/spots      │  Puerto 3535     │
└──────────────────┘                         └────────┬─────────┘
                                                      │
                                                      ▼
                                            ┌──────────────────────┐
                                            │ Parsear mensaje:     │
                                            │ {                    │
                                            │   "A_1": 0,          │
                                            │   "A_2": 1,          │
                                            │   "B_1": 0,          │
                                            │   ...                │
                                            │ }                    │
                                            └────────┬─────────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────────┐
                                            │ Actualizar           │
                                            │ monitored_spots      │
                                            │ para cada plaza      │
                                            └────────┬─────────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────────┐
                                            │ Calcular:            │
                                            │ total_spot_occupied  │
                                            │ = SUM(ocupadas)      │
                                            └────────┬─────────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────────┐
                                            │ Sincronizar con      │
                                            │ parking.occupancy    │
                                            │ si spot_monitoring   │
                                            │ está habilitado      │
                                            └──────────────────────┘
```

---

*Anterior: [04-base-de-datos.md](./04-base-de-datos.md)*
*Siguiente: [06-despliegue.md](./06-despliegue.md)*
