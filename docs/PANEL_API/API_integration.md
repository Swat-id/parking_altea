# API Integration Guide - PanelSender Service

## Información General

**URL Base:** `http://localhost:8888`  
**Puerto:** 8888  
**Servicio:** PanelSender Service - Gestión de paneles informativos LED

## Endpoint Principal

### POST `/api/v1/panels/send`

Endpoint principal para enviar contenido a paneles LED usando protocolos nuevo (v1.4.7) y antiguo (v1.2.6).

**Headers:**
```
Content-Type: application/json
```

**Estructura de la petición:**
```json
{
  "panels": [
    {
      "ip": "IP_DEL_PANEL",
      "port": PUERTO,
      "protocol": "new|old",
      "windows": [
        {
          "id": ID_VENTANA,
          "text": "TEXTO_A_ENVIAR",
          "color": COLOR,
          "fontSize": TAMAÑO_FUENTE,
          "effect": "fijo|scroll",
          "stayTime": TIEMPO_PERMANENCIA,
          "alignmentH": ALINEACION_HORIZONTAL,
          "alignmentV": ALINEACION_VERTICAL
        }
      ]
    }
  ],
  "options": {
    "sequential": false,
    "timeout": 30000,
    "retryAttempts": 3
  }
}
```

**Nota importante:** El parámetro `speed` no se incluye en la petición. La velocidad se determina automáticamente según el efecto:
- Para efecto `"fijo"`: velocidad 0 (no aplicable)
- Para efecto `"scroll"`: velocidad 5 (lenta)

### Opciones de Envío (Opcional)

El campo `options` es opcional y permite configurar el comportamiento del envío:

| Parámetro | Tipo | Valor por defecto | Descripción |
|-----------|------|-------------------|-------------|
| `sequential` | boolean | false | Si es true, envía los paneles secuencialmente en lugar de en paralelo |
| `timeout` | integer | 30000 | Timeout en milisegundos para cada operación |
| `retryAttempts` | integer | 3 | Número de intentos de reintento en caso de fallo |

---

## Protocolo Antiguo (v1.2.6)

### Configuración del Protocolo Antiguo

- **Puerto por defecto:** 5200 (según SDK del fabricante)
- **Clase principal:** `com.lumen.ledcenter3.protocol.ExtSendUtil`
- **Flujo:** `initNetwork` → `setListener` → `sendText`

### Parámetros de Color (Protocolo Antiguo)

| Color | Valor | Descripción |
|-------|-------|-------------|
| 1 | Rojo | Color rojo |
| 2 | Verde | Color verde |
| 3 | Amarillo | Color amarillo |
| 4 | Azul | Color azul |
| 5 | Magenta | Color magenta |
| 6 | Cian | Color cian |
| 7 | Blanco | Color blanco |

### Parámetros de Tamaño de Fuente (Protocolo Antiguo)

| Valor | Tamaño (píxeles) | Descripción |
|-------|------------------|-------------|
| 0 | 8 | Fuente pequeña |
| 1 | 12 | Fuente mediana |
| **2** | **16** | **Fuente estándar** |
| 3 | 24 | Fuente grande |
| 4 | 32 | Fuente extra grande |
| 5 | 40 | Fuente muy grande |
| 6 | 48 | Fuente enorme |
| 7 | 56 | Fuente máxima |

### Efectos de Texto Disponibles

| Efecto | Valor | Descripción |
|--------|-------|-------------|
| "fijo" | 2 | Texto estático sin movimiento |
| "scroll" | 12 | Texto con desplazamiento |

**Nota sobre velocidad:**
- Para efecto **"fijo"**: La velocidad se establece automáticamente en 0 (no aplicable)
- Para efecto **"scroll"**: La velocidad se establece automáticamente en 5 (lenta)

### Ejemplos de Uso - Protocolo Antiguo

#### 1. Enviar Texto Rojo Fijo, Tamaño 16

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "old",
        "windows": [
          {
            "id": 0,
            "text": "MENSAJE ROJO FIJO",
            "color": 1,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          }
        ]
      }
    ]
  }'
```

#### 2. Enviar Texto Verde Fijo, Tamaño 16

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "old",
        "windows": [
          {
            "id": 0,
            "text": "MENSAJE VERDE FIJO",
            "color": 2,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          }
        ]
      }
    ]
  }'
```

#### 3. Enviar Texto Amarillo Fijo, Tamaño 16

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "old",
        "windows": [
          {
            "id": 0,
            "text": "MENSAJE AMARILLO FIJO",
            "color": 3,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          }
        ]
      }
    ]
  }'
```

#### 4. Texto con Scroll

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "old",
        "windows": [
          {
            "id": 0,
            "text": "TEXTO CON SCROLL",
            "color": 1,
            "fontSize": 2,
            "effect": "scroll",
            "stayTime": 100,
            "alignmentH": 1,
            "alignmentV": 1
          }
        ]
      }
    ]
  }'
```

---

## Protocolo Nuevo (v1.4.7)

### Configuración del Protocolo Nuevo

- **Puerto por defecto:** 5200
- **Clase principal:** `com.lumen.ledcenter3.protocol.ExtSendUtil`
- **Flujo:** `initNetwork` → `setListener` → `splitScreen` (opcional) → `sendText`

### Parámetros de Color (Protocolo Nuevo)

| Color | Valor | Descripción |
|-------|-------|-------------|
| 1 | Rojo | Color rojo |
| 2 | Verde | Color verde |
| 3 | Amarillo | Color amarillo |
| 4 | Azul | Color azul |
| 5 | Magenta | Color magenta |
| 6 | Cian | Color cian |
| 7 | Blanco | Color blanco |

### Parámetros de Tamaño de Fuente (Protocolo Nuevo)

| Valor | Tamaño (píxeles) | Descripción |
|-------|------------------|-------------|
| 0 | 8 | Fuente pequeña |
| 1 | 12 | Fuente mediana |
| **2** | **16** | **Fuente estándar** |
| 3 | 24 | Fuente grande |
| 4 | 32 | Fuente extra grande |

### Efectos de Texto Disponibles (Protocolo Nuevo)

| Efecto | Valor | Descripción |
|--------|-------|-------------|
| "fijo" | 2 | Texto estático sin movimiento |
| "scroll" | 12 | Texto con desplazamiento |

**Nota sobre velocidad:**
- Para efecto **"fijo"**: La velocidad se establece automáticamente en 0 (no aplicable)
- Para efecto **"scroll"**: La velocidad se establece automáticamente en 5 (lenta)

### Ejemplos de Uso - Protocolo Nuevo

#### 1. Pantalla Completa 64x16 (Ventana 0)

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "new",
        "windows": [
          {
            "id": 0,
            "text": "PANTALLA COMPLETA 64x16",
            "color": 1,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 1,
            "alignmentV": 1
          }
        ]
      }
    ]
  }'
```

#### 2. Dos Pantallas 32x16 (Ventanas 0 y 1)

**IMPORTANTE:** Para dividir la pantalla en dos ventanas de 32x16, el sistema automáticamente:
- Ejecuta `initNetwork` para inicializar la conexión
- Configura `setListener` para monitorear el estado
- Ejecuta `splitScreen` con las coordenadas correctas:
  - Ventana 0: (0, 0, 32, 16) - Mitad izquierda
  - Ventana 1: (32, 0, 64, 16) - Mitad derecha

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "new",
        "windows": [
          {
            "id": 0,
            "text": "VENTANA IZQUIERDA",
            "color": 1,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 1,
            "alignmentV": 1
          },
          {
            "id": 1,
            "text": "VENTANA DERECHA",
            "color": 2,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 1,
            "alignmentV": 1
          }
        ]
      }
    ]
  }'
```

#### 3. Múltiples Paneles con Diferentes Protocolos

```bash
curl -X POST "http://localhost:8888/api/v1/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "172.20.4.52",
        "port": 5200,
        "protocol": "new",
        "windows": [
          {
            "id": 0,
            "text": "PANEL NUEVO",
            "color": 1,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 1,
            "alignmentV": 1
          }
        ]
      },
      {
        "ip": "172.20.4.53",
        "port": 5200,
        "protocol": "old",
        "windows": [
          {
            "id": 0,
            "text": "PANEL ANTIGUO",
            "color": 2,
            "fontSize": 2,
            "effect": "fijo",
            "stayTime": 50,
            "alignmentH": 1,
            "alignmentV": 1
          }
        ]
      }
    ]
  }'
```

---

## Respuestas de la API

### Respuesta Exitosa

```json
{
  "success": true,
  "message": "Contenido enviado correctamente",
  "data": {
    "totalPanels": 1,
    "totalWindows": 1,
    "results": [
      {
        "ip": "172.20.4.52",
        "success": true,
        "windows": [
          {
            "id": 0,
            "success": true,
            "message": "Texto enviado correctamente"
          }
        ]
      }
    ]
  },
  "timestamp": "2025-07-04T14:51:01.206525"
}
```

### Respuesta con Errores

```json
{
  "success": false,
  "message": "Algunos comandos fallaron",
  "data": {
    "totalPanels": 1,
    "totalWindows": 1,
    "results": [
      {
        "ip": "172.20.4.52",
        "success": false,
        "windows": [
          {
            "id": 0,
            "success": false,
            "message": "Error enviando texto",
            "errorMessage": "Detalles del error..."
          }
        ],
        "errorMessage": "Algunas ventanas fallaron"
      }
    ]
  },
  "timestamp": "2025-07-04T14:51:01.206525"
}
```

---

## Códigos de Estado HTTP

- **200 OK:** Petición procesada correctamente
- **422 Unprocessable Entity:** Error de validación en los parámetros
- **500 Internal Server Error:** Error interno del servidor

---

## Notas Importantes

### Para el Protocolo Antiguo:
- El puerto por defecto es **5200** (no 5005)
- El método `initNetwork` requiere 3 parámetros: `(ip, port, idcode)`
- El `idcode` por defecto es `"255.255.255.255"`

### Para el Protocolo Nuevo:
- Soporta división automática de pantalla
- Las coordenadas se calculan automáticamente según el `window_id`
- Ventana 0: pantalla completa o mitad izquierda
- Ventana 1: mitad derecha (requiere splitScreen automático)

### Consideraciones de Red:
- Asegúrese de que el panel esté accesible en la IP y puerto especificados
- Los timeouts de conexión pueden variar según la red
- Se recomienda usar el puerto 5200 para ambos protocolos

---

## Endpoints Adicionales

### GET `/api/v1/panels/list`

Endpoint para listar los paneles disponibles y su configuración.

**Respuesta:**
```json
{
  "panels": [
    {
      "ip": "192.168.1.221",
      "port": 5200,
      "protocol": "new",
      "description": "Panel 1 - 1 línea, 2 ventanas (32x16 cada una)",
      "windows": [
        {"id": 0, "coordinates": [0, 0, 32, 16], "description": "Ventana Izquierda"},
        {"id": 1, "coordinates": [32, 0, 32, 16], "description": "Ventana Derecha"}
      ]
    },
    {
      "ip": "192.168.1.222", 
      "port": 5200,
      "protocol": "new",
      "description": "Panel 2 - 1 línea, 2 ventanas (32x16 cada una)",
      "windows": [
        {"id": 0, "coordinates": [0, 0, 32, 16], "description": "Ventana Izquierda"},
        {"id": 1, "coordinates": [32, 0, 32, 16], "description": "Ventana Derecha"}
      ]
    },
    {
      "ip": "192.168.1.223",
      "port": 5200, 
      "protocol": "new",
      "description": "Panel 3 - 1 línea, 1 ventana (64x16)",
      "windows": [
        {"id": 0, "coordinates": [0, 0, 64, 16], "description": "Ventana Completa"}
      ]
    },
    {
      "ip": "192.168.1.224",
      "port": 5200,
      "protocol": "old", 
      "description": "Panel 4 - Protocolo antiguo",
      "windows": [
        {"id": 0, "coordinates": [0, 0, 64, 16], "description": "Ventana Completa"}
      ]
    }
  ]
}
```

---

## Health Check

Para verificar el estado del servicio:

```bash
curl -X GET "http://localhost:8888/health"
```

Respuesta:
```json
{
  "status": "running",
  "timestamp": "2025-07-04T14:17:34.800697",
  "version": "1.0.0",
  "protocols": {
    "new": true,
    "old": true
  }
}
```

---

## Documentación Interactiva

Acceda a la documentación interactiva de la API en:
```
http://localhost:8888/docs
``` 