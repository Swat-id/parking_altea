# Integración Backend - Paneles LED

Guía completa para integrar el sistema de paneles LED en aplicaciones backend Python.

## 📋 Tabla de Contenidos

- [Opciones de Integración](#opciones-de-integración)
- [Módulo panel_backend.py](#módulo-panel_backendpy)
- [Funciones Disponibles](#funciones-disponibles)
- [Estructuras de Datos](#estructuras-de-datos)
- [Ejemplos de Integración](#ejemplos-de-integración)
- [Manejo de Errores](#manejo-de-errores)
- [Respuestas del Panel](#respuestas-del-panel)
- [Mejores Prácticas](#mejores-prácticas)
- [Integración con Frameworks](#integración-con-frameworks)

---

## Opciones de Integración

### Opción 1: Funciones Python Directas ⭐ (Recomendada)

**Ventajas:**
- ✅ Integración directa, sin overhead
- ✅ Menor latencia
- ✅ Fácil debugging
- ✅ Control total de errores y timeouts
- ✅ Ideal para backends Python (Django, Flask, FastAPI)

**Cuándo usar:**
- Tu backend está en Python
- Necesitas bajo tiempo de respuesta
- Quieres control directo sobre la comunicación

### Opción 2: Servicio Web (API REST)

**Ventajas:**
- ✅ Desacoplamiento total
- ✅ Escalabilidad horizontal
- ✅ Múltiples aplicaciones pueden usar el servicio
- ✅ Útil para backends en otros lenguajes

**Desventajas:**
- ⚠️ Mayor latencia (HTTP overhead)
- ⚠️ Más complejo de mantener
- ⚠️ Necesita otro servicio corriendo

**Cuándo usar:**
- Tienes múltiples aplicaciones que necesitan controlar paneles
- Tu backend no es Python
- Necesitas escalabilidad horizontal

### Recomendación

**Para backends Python**: Usar `panel_backend.py` directamente ⭐

**Para otros lenguajes o arquitectura de microservicios**: Crear API REST con FastAPI

---

## Módulo panel_backend.py

### Instalación

```python
# Importar el módulo en tu proyecto
from panel_backend import PanelBackend, WindowMessage, quick_send, quick_send_all
from panel_protocol import TextColor, FontSize, TextAlignment, TextEffect
```

### Configuración Básica

```python
from panel_backend import PanelBackend

# Crear instancia del backend
backend = PanelBackend(
    ip_address="192.168.10.110",
    port=5200,                    # Puerto por defecto
    timeout=5,                    # Timeout en segundos
    retry_attempts=3,             # Reintentos automáticos
    retry_delay=0.5               # Delay entre reintentos
)

# Probar conexión
success, error = backend.test_connection()
if success:
    print("✓ Panel conectado")
else:
    print(f"✗ Error: {error}")
```

---

## Funciones Disponibles

### 1. quick_send() - Envío Rápido Simple

**Uso más simple para enviar a una ventana**

```python
from panel_backend import quick_send

# Envío básico
success = quick_send(
    ip="192.168.10.110",
    window=0,
    text="HOLA MUNDO"
)

# Con parámetros
success = quick_send(
    ip="192.168.10.110",
    window=0,
    text="LIBRE",
    color="green",              # red, green, yellow, blue, purple, cyan, white
    effect="scroll_left",       # static, scroll_left, scroll_right, etc
    speed=10                    # 1-100 (mayor = más lento)
)
```

**Parámetros:**
- `ip` (str): IP del panel
- `window` (int): Número de ventana (0-7)
- `text` (str): Texto a mostrar
- `color` (str): Color del texto (default: "green")
- `effect` (str): Efecto de visualización (default: "static")
- `speed` (int): Velocidad 1-100 (default: 5)

**Retorna:** `bool` - True si fue exitoso

---

### 2. quick_send_all() - Envío Rápido a Múltiples Ventanas

**Función optimizada para enviar el mismo texto a varias ventanas**

```python
from panel_backend import quick_send_all

# Enviar a múltiples ventanas
result = quick_send_all(
    ip="192.168.10.110",
    windows=[0, 1, 2, 3, 4, 5, 6],
    text="LIBRE",
    color="green",
    effect="static",
    speed=5
)

# Verificar resultado
print(f"Exitosos: {result['successful']}/{result['total']}")
print(f"Tasa de éxito: {result['success_rate']:.1f}%")
print(f"Tiempo: {result['execution_time']:.2f}s")
```

**Parámetros:**
- `ip` (str): IP del panel
- `windows` (List[int]): Lista de ventanas
- `text` (str): Texto a mostrar
- `color` (str): Color del texto
- `effect` (str): Efecto de visualización
- `speed` (int): Velocidad 1-100

**Retorna:** `Dict` con:
```python
{
    "success": bool,              # True si todos exitosos
    "total": int,                 # Total de envíos
    "successful": int,            # Envíos exitosos
    "failed": int,                # Envíos fallidos
    "success_rate": float,        # Porcentaje de éxito
    "execution_time": float       # Tiempo en segundos
}
```

---

### 3. PanelBackend.send_to_window() - Envío Completo

**Control total con tipos enumerados**

```python
from panel_backend import PanelBackend
from panel_protocol import TextColor, FontSize, TextAlignment, TextEffect

backend = PanelBackend("192.168.10.110")

result = backend.send_to_window(
    window_number=0,
    text="BIENVENIDO",
    color=TextColor.GREEN,
    font_size=FontSize.SIZE_24,
    alignment=TextAlignment.CENTER_CENTER,
    effect=TextEffect.SCROLL_LEFT,
    speed=10,
    wait_time=0x0003
)

# Verificar resultado
if result.success:
    print(f"✓ Enviado a ventana {result.window_number}")
    print(f"Respuesta: {result.response.hex()}")
else:
    print(f"✗ Error: {result.error_message}")
```

**Parámetros:**
- `window_number` (int): Ventana (0-7)
- `text` (str): Texto a mostrar
- `color` (TextColor): Enum de color
- `font_size` (FontSize): Enum de tamaño
- `alignment` (TextAlignment): Enum de alineación
- `effect` (TextEffect): Enum de efecto
- `speed` (int): Velocidad del efecto
- `wait_time` (int): Tiempo de espera

**Retorna:** `SendResult`
```python
@dataclass
class SendResult:
    window_number: int            # Ventana enviada
    success: bool                 # Si fue exitoso
    error_message: Optional[str]  # Mensaje de error si falla
    response: Optional[bytes]     # Respuesta del panel
```

**Características:**
- ✅ Reintentos automáticos (configurables)
- ✅ Validación de respuesta del panel
- ✅ Manejo robusto de errores

---

### 4. PanelBackend.send_batch() - Envío Batch Completo

**Para enviar mensajes diferentes a múltiples ventanas**

```python
from panel_backend import PanelBackend, WindowMessage
from panel_protocol import TextColor, FontSize, TextEffect

backend = PanelBackend("192.168.10.110")

# Crear lista de mensajes
messages = [
    WindowMessage(
        window_number=0,
        text="LIBRE",
        color=TextColor.GREEN,
        effect=TextEffect.STATIC
    ),
    WindowMessage(
        window_number=1,
        text="OCUPADO",
        color=TextColor.RED,
        effect=TextEffect.FLICKER
    ),
    WindowMessage(
        window_number=2,
        text="CERRADO",
        color=TextColor.YELLOW,
        effect=TextEffect.SCROLL_LEFT,
        speed=15
    )
]

# Enviar batch
result = backend.send_batch(
    messages=messages,
    delay_between_sends=0.1  # Delay entre envíos
)

# Analizar resultados
print(f"Total: {result.total}")
print(f"Exitosos: {result.successful}")
print(f"Fallidos: {result.failed}")
print(f"Tasa éxito: {result.success_rate:.1f}%")
print(f"Tiempo: {result.execution_time:.2f}s")

# Ver resultados individuales
for res in result.results:
    if res.success:
        print(f"✓ Ventana {res.window_number}")
    else:
        print(f"✗ Ventana {res.window_number}: {res.error_message}")
```

**Retorna:** `BatchResult`
```python
@dataclass
class BatchResult:
    total: int                    # Total de mensajes
    successful: int               # Exitosos
    failed: int                   # Fallidos
    results: List[SendResult]     # Resultados individuales
    execution_time: float         # Tiempo total
    success_rate: float          # Propiedad: tasa de éxito
    all_successful: bool         # Propiedad: todos exitosos
```

---

### 5. PanelBackend.send_same_to_all_windows() - Optimizado

**Versión optimizada de send_batch para el mismo texto**

```python
backend = PanelBackend("192.168.10.110")

result = backend.send_same_to_all_windows(
    text="LIBRE",
    windows=[0, 1, 2, 3, 4, 5, 6],
    color=TextColor.GREEN,
    font_size=FontSize.SIZE_16,
    alignment=TextAlignment.CENTER_CENTER,
    effect=TextEffect.STATIC,
    speed=5,
    delay_between_sends=0.1
)

if result.all_successful:
    print(f"✓ Todas las ventanas actualizadas en {result.execution_time:.2f}s")
else:
    print(f"⚠ {result.failed} ventanas fallaron")
```

---

### 6. Funciones Auxiliares

#### test_connection()
```python
success, error = backend.test_connection()
if not success:
    raise ConnectionError(f"Panel no disponible: {error}")
```

#### clear_window()
```python
result = backend.clear_window(window_number=0)
```

#### clear_all_windows()
```python
result = backend.clear_all_windows(windows=[0, 1, 2, 3, 4, 5, 6])
```

---

## Estructuras de Datos

### WindowMessage

```python
@dataclass
class WindowMessage:
    window_number: int
    text: str
    color: TextColor = TextColor.GREEN
    font_size: FontSize = FontSize.SIZE_16
    alignment: TextAlignment = TextAlignment.CENTER_CENTER
    effect: TextEffect = TextEffect.STATIC
    speed: int = 0x03
    wait_time: int = 0x0003
```

### SendResult

```python
@dataclass
class SendResult:
    window_number: int
    success: bool
    error_message: Optional[str] = None
    response: Optional[bytes] = None
```

### BatchResult

```python
@dataclass
class BatchResult:
    total: int
    successful: int
    failed: int
    results: List[SendResult]
    execution_time: float
    
    @property
    def success_rate(self) -> float
    
    @property
    def all_successful(self) -> bool
```

---

## Ejemplos de Integración

### Integración con Django

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from panel_backend import PanelBackend, WindowMessage
from panel_protocol import TextColor, TextEffect
import json

# Configurar backend (puede ser singleton)
panel_backend = PanelBackend("192.168.10.110")

@require_http_methods(["POST"])
def update_panel(request):
    """
    Endpoint para actualizar panel
    POST /api/panel/update
    Body: {
        "window": 0,
        "text": "LIBRE",
        "color": "green",
        "effect": "static"
    }
    """
    try:
        data = json.loads(request.body)
        
        # Validar conexión
        connected, error = panel_backend.test_connection()
        if not connected:
            return JsonResponse({
                "success": False,
                "error": f"Panel not available: {error}"
            }, status=503)
        
        # Mapeo de colores
        color_map = {
            "red": TextColor.RED,
            "green": TextColor.GREEN,
            "yellow": TextColor.YELLOW,
            "blue": TextColor.BLUE
        }
        
        effect_map = {
            "static": TextEffect.STATIC,
            "scroll_left": TextEffect.SCROLL_LEFT,
            "scroll_right": TextEffect.SCROLL_RIGHT
        }
        
        # Enviar a panel
        result = panel_backend.send_to_window(
            window_number=data.get("window", 0),
            text=data.get("text", ""),
            color=color_map.get(data.get("color", "green"), TextColor.GREEN),
            effect=effect_map.get(data.get("effect", "static"), TextEffect.STATIC),
            speed=data.get("speed", 5)
        )
        
        if result.success:
            return JsonResponse({
                "success": True,
                "window": result.window_number,
                "message": "Panel updated successfully"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": result.error_message
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@require_http_methods(["POST"])
def update_all_panels(request):
    """
    Actualizar todas las ventanas
    POST /api/panel/update-all
    Body: {
        "text": "LIBRE",
        "windows": [0,1,2,3,4,5,6],
        "color": "green"
    }
    """
    try:
        data = json.loads(request.body)
        
        color_map = {
            "red": TextColor.RED,
            "green": TextColor.GREEN,
            "yellow": TextColor.YELLOW
        }
        
        result = panel_backend.send_same_to_all_windows(
            text=data.get("text", ""),
            windows=data.get("windows", [0]),
            color=color_map.get(data.get("color", "green"), TextColor.GREEN)
        )
        
        return JsonResponse({
            "success": result.all_successful,
            "total": result.total,
            "successful": result.successful,
            "failed": result.failed,
            "execution_time": result.execution_time
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
```

### Integración con Flask

```python
# app.py
from flask import Flask, request, jsonify
from panel_backend import quick_send, quick_send_all

app = Flask(__name__)
PANEL_IP = "192.168.10.110"

@app.route('/api/panel/send', methods=['POST'])
def send_to_panel():
    """
    Enviar texto a una ventana
    POST /api/panel/send
    Body: {
        "window": 0,
        "text": "HOLA",
        "color": "green",
        "effect": "static",
        "speed": 5
    }
    """
    data = request.get_json()
    
    success = quick_send(
        ip=PANEL_IP,
        window=data.get('window', 0),
        text=data.get('text', ''),
        color=data.get('color', 'green'),
        effect=data.get('effect', 'static'),
        speed=data.get('speed', 5)
    )
    
    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": "Failed to send"}), 500


@app.route('/api/panel/send-all', methods=['POST'])
def send_to_all():
    """
    Enviar a todas las ventanas
    POST /api/panel/send-all
    Body: {
        "windows": [0,1,2,3,4,5,6],
        "text": "LIBRE",
        "color": "green"
    }
    """
    data = request.get_json()
    
    result = quick_send_all(
        ip=PANEL_IP,
        windows=data.get('windows', [0]),
        text=data.get('text', ''),
        color=data.get('color', 'green'),
        effect=data.get('effect', 'static'),
        speed=data.get('speed', 5)
    )
    
    return jsonify(result), 200 if result['success'] else 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Integración con FastAPI

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from panel_backend import PanelBackend
from panel_protocol import TextColor, TextEffect
import logging

app = FastAPI(title="Panel LED API")
logger = logging.getLogger(__name__)

# Singleton del backend
panel_backend = PanelBackend("192.168.10.110", retry_attempts=3)

class PanelMessage(BaseModel):
    window: int
    text: str
    color: Optional[str] = "green"
    effect: Optional[str] = "static"
    speed: Optional[int] = 5

class BulkPanelMessage(BaseModel):
    windows: List[int]
    text: str
    color: Optional[str] = "green"
    effect: Optional[str] = "static"
    speed: Optional[int] = 5

@app.on_event("startup")
async def startup_event():
    """Verificar conexión al iniciar"""
    success, error = panel_backend.test_connection()
    if not success:
        logger.warning(f"Panel not available on startup: {error}")
    else:
        logger.info("Panel connected successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    success, error = panel_backend.test_connection()
    if success:
        return {"status": "healthy", "panel": "connected"}
    else:
        return {"status": "degraded", "panel": "disconnected", "error": error}

@app.post("/api/v1/panel/send")
async def send_message(message: PanelMessage):
    """Enviar mensaje a una ventana"""
    color_map = {
        "red": TextColor.RED,
        "green": TextColor.GREEN,
        "yellow": TextColor.YELLOW,
        "blue": TextColor.BLUE,
        "purple": TextColor.PURPLE,
        "cyan": TextColor.CYAN,
        "white": TextColor.WHITE
    }
    
    effect_map = {
        "static": TextEffect.STATIC,
        "scroll_left": TextEffect.SCROLL_LEFT,
        "scroll_right": TextEffect.SCROLL_RIGHT,
        "scroll_up": TextEffect.SCROLL_UP,
        "flicker": TextEffect.FLICKER
    }
    
    result = panel_backend.send_to_window(
        window_number=message.window,
        text=message.text,
        color=color_map.get(message.color.lower(), TextColor.GREEN),
        effect=effect_map.get(message.effect.lower(), TextEffect.STATIC),
        speed=message.speed
    )
    
    if result.success:
        return {
            "success": True,
            "window": result.window_number,
            "message": "Text sent successfully"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send: {result.error_message}"
        )

@app.post("/api/v1/panel/send-bulk")
async def send_bulk_message(message: BulkPanelMessage):
    """Enviar el mismo mensaje a múltiples ventanas"""
    color_map = {
        "red": TextColor.RED,
        "green": TextColor.GREEN,
        "yellow": TextColor.YELLOW,
        "blue": TextColor.BLUE
    }
    
    effect_map = {
        "static": TextEffect.STATIC,
        "scroll_left": TextEffect.SCROLL_LEFT,
        "scroll_right": TextEffect.SCROLL_RIGHT
    }
    
    result = panel_backend.send_same_to_all_windows(
        text=message.text,
        windows=message.windows,
        color=color_map.get(message.color.lower(), TextColor.GREEN),
        effect=effect_map.get(message.effect.lower(), TextEffect.STATIC),
        speed=message.speed
    )
    
    return {
        "success": result.all_successful,
        "total": result.total,
        "successful": result.successful,
        "failed": result.failed,
        "success_rate": result.success_rate,
        "execution_time": result.execution_time
    }

@app.post("/api/v1/panel/clear")
async def clear_panel(windows: List[int]):
    """Limpiar ventanas"""
    result = panel_backend.clear_all_windows(windows)
    return {
        "success": result.all_successful,
        "cleared": result.successful
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Manejo de Errores

### Tipos de Errores

```python
from panel_backend import PanelBackend

backend = PanelBackend("192.168.10.110")

# 1. Error de conexión
result = backend.send_to_window(0, "TEST")
if not result.success:
    if "Connection refused" in result.error_message:
        # Panel apagado o IP incorrecta
        pass
    elif "Timeout" in result.error_message:
        # Red lenta o panel no responde
        pass
    elif "Exception" in result.error_message:
        # Error inesperado
        pass

# 2. Validar conexión antes de enviar
success, error = backend.test_connection()
if not success:
    print(f"Panel no disponible: {error}")
    # Implementar fallback o notificación
```

### Estrategia de Reintentos

```python
# Configurar reintentos
backend = PanelBackend(
    ip_address="192.168.10.110",
    retry_attempts=5,      # 5 intentos
    retry_delay=1.0        # 1 segundo entre intentos
)

# Los reintentos son automáticos
result = backend.send_to_window(0, "TEST")
# Si falla, habrá intentado 5 veces antes de retornar
```

### Manejo Robusto

```python
def safe_send_to_panel(window, text, max_retries=3):
    """Función wrapper con manejo de errores completo"""
    backend = PanelBackend("192.168.10.110", retry_attempts=max_retries)
    
    try:
        # Validar conexión primero
        connected, error = backend.test_connection()
        if not connected:
            logger.error(f"Panel not available: {error}")
            return {"success": False, "error": "Panel not available"}
        
        # Enviar mensaje
        result = backend.send_to_window(window, text)
        
        if result.success:
            logger.info(f"Message sent to window {window}")
            return {"success": True, "window": window}
        else:
            logger.error(f"Failed to send: {result.error_message}")
            return {"success": False, "error": result.error_message}
            
    except Exception as e:
        logger.exception("Unexpected error")
        return {"success": False, "error": str(e)}
```

---

## Respuestas del Panel

### Formato de Respuesta

El panel responde con un paquete binario:

```
ff ff ff ff  0c 00 00 00  e8 32 01 7b  00 01 00 00  00 02 99 01
│            │            │            │             │
ID Code      Net Length   Packet Data  Return Val   Checksum
```

### Interpretación de Respuestas

```python
result = backend.send_to_window(0, "TEST")

if result.success and result.response:
    response = result.response
    
    # Bytes importantes
    packet_type = response[8]    # 0xE8 = respuesta
    return_value = response[12]  # 0x00 = éxito
    
    if packet_type == 0xE8 and return_value == 0x00:
        print("✓ Panel confirmó recepción exitosa")
    else:
        print(f"⚠ Panel retornó código: {return_value:02x}")
```

### Códigos de Retorno

| Código | Significado |
|--------|-------------|
| `0x00` | Éxito |
| `0x01-0xFF` | Códigos de error (ver documentación del fabricante) |

---

## Mejores Prácticas

### 1. Usar Singleton para el Backend

```python
# backend_manager.py
from panel_backend import PanelBackend

class PanelManager:
    _instance = None
    _backend = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._backend = PanelBackend(
                ip_address="192.168.10.110",
                retry_attempts=3,
                timeout=5
            )
        return cls._instance
    
    def send(self, window, text, **kwargs):
        return self._backend.send_to_window(window, text, **kwargs)
    
    def test_connection(self):
        return self._backend.test_connection()

# Uso
panel_manager = PanelManager()
result = panel_manager.send(0, "HOLA")
```

### 2. Implementar Circuit Breaker

```python
from datetime import datetime, timedelta

class PanelCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.backend = PanelBackend("192.168.10.110")
    
    def send(self, window, text):
        if self.state == "open":
            # Verificar si es tiempo de intentar de nuevo
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half-open"
            else:
                return {"success": False, "error": "Circuit breaker open"}
        
        result = self.backend.send_to_window(window, text)
        
        if result.success:
            # Reset en caso de éxito
            self.failures = 0
            if self.state == "half-open":
                self.state = "closed"
            return {"success": True}
        else:
            # Incrementar fallos
            self.failures += 1
            self.last_failure_time = datetime.now()
            
            if self.failures >= self.failure_threshold:
                self.state = "open"
            
            return {"success": False, "error": result.error_message}
```

### 3. Logging y Monitoreo

```python
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('panel_backend')

def monitored_send(backend, window, text):
    """Envío con logging y métricas"""
    start_time = datetime.now()
    
    logger.info(f"Sending to window {window}: {text}")
    
    result = backend.send_to_window(window, text)
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    if result.success:
        logger.info(f"✓ Success - Window {window} - {execution_time:.3f}s")
    else:
        logger.error(f"✗ Failed - Window {window} - {result.error_message}")
    
    # Enviar métricas (Prometheus, StatsD, etc.)
    # metrics.increment('panel.send.total')
    # metrics.timing('panel.send.duration', execution_time)
    # if result.success:
    #     metrics.increment('panel.send.success')
    # else:
    #     metrics.increment('panel.send.failure')
    
    return result
```

### 4. Caché de Estados

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedPanelBackend:
    def __init__(self, backend):
        self.backend = backend
        self.cache = {}
        self.cache_ttl = 60  # segundos
    
    def send_with_cache(self, window, text):
        """Solo enviar si el texto ha cambiado"""
        cache_key = f"window_{window}"
        now = datetime.now()
        
        if cache_key in self.cache:
            cached_text, cached_time = self.cache[cache_key]
            
            # Si el texto es el mismo y no ha expirado, skip
            if cached_text == text and (now - cached_time).seconds < self.cache_ttl:
                return {"success": True, "cached": True}
        
        # Enviar y actualizar caché
        result = self.backend.send_to_window(window, text)
        
        if result.success:
            self.cache[cache_key] = (text, now)
        
        return {"success": result.success, "cached": False}
```

### 5. Validación de Entrada

```python
def validate_and_send(backend, window, text, color="green", effect="static"):
    """Validar entrada antes de enviar"""
    # Validar ventana
    if not 0 <= window <= 7:
        return {"success": False, "error": "Invalid window number (0-7)"}
    
    # Validar texto
    if not text or len(text) > 100:
        return {"success": False, "error": "Text length invalid (1-100 chars)"}
    
    # Validar color
    valid_colors = ["red", "green", "yellow", "blue", "purple", "cyan", "white"]
    if color.lower() not in valid_colors:
        return {"success": False, "error": f"Invalid color. Use: {valid_colors}"}
    
    # Validar efecto
    valid_effects = ["static", "scroll_left", "scroll_right", "scroll_up", "flicker"]
    if effect.lower() not in valid_effects:
        return {"success": False, "error": f"Invalid effect. Use: {valid_effects}"}
    
    # Todo válido, enviar
    from panel_backend import quick_send
    success = quick_send(backend.ip_address, window, text, color, effect)
    
    return {"success": success}
```

---

## Integración con Frameworks

### Django + Celery (Async)

```python
# tasks.py
from celery import shared_task
from panel_backend import PanelBackend

@shared_task
def send_to_panel_async(window, text, color="green"):
    """Tarea asíncrona para enviar a panel"""
    backend = PanelBackend("192.168.10.110")
    result = backend.send_to_window(
        window_number=window,
        text=text,
        color=getattr(TextColor, color.upper())
    )
    return {
        "success": result.success,
        "window": window,
        "error": result.error_message
    }

# views.py
from .tasks import send_to_panel_async

def update_panel_view(request):
    # Enviar de forma asíncrona
    task = send_to_panel_async.delay(
        window=0,
        text="HOLA",
        color="green"
    )
    
    return JsonResponse({
        "task_id": task.id,
        "status": "processing"
    })
```

### FastAPI + Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/api/v1/panel/send-async")
async def send_message_async(
    message: PanelMessage,
    background_tasks: BackgroundTasks
):
    """Enviar mensaje en background"""
    def send_in_background():
        backend = PanelBackend("192.168.10.110")
        backend.send_to_window(
            window_number=message.window,
            text=message.text
        )
    
    background_tasks.add_task(send_in_background)
    
    return {"status": "queued", "message": "Will be sent in background"}
```

---

## Resumen de Decisiones

### ✅ Usar Funciones Python Directas Si:
- Tu backend está en Python
- Necesitas baja latencia
- Tienes una sola aplicación
- Quieres simplicidad

### ✅ Crear API REST Si:
- Tienes múltiples aplicaciones
- Usas diferentes lenguajes
- Necesitas escalabilidad horizontal
- Arquitectura de microservicios

### ✅ Recomendación Final:
**Empezar con funciones directas (`panel_backend.py`)** y migrar a API REST solo si se necesita.

---

## Checklist de Integración

- [ ] Importar `panel_backend` en tu proyecto
- [ ] Crear instancia de `PanelBackend` con configuración
- [ ] Implementar `test_connection()` en health checks
- [ ] Agregar manejo de errores robusto
- [ ] Implementar logging de operaciones
- [ ] Validar entrada de usuarios
- [ ] Configurar reintentos apropiados
- [ ] Documentar endpoints/funciones
- [ ] Agregar tests unitarios
- [ ] Monitorear rendimiento en producción

---

**Versión del documento**: 1.0  
**Última actualización**: 10 de Noviembre de 2025  
**Mantenido por**: Equipo ALTEA - PROTOCOLO_PANEL

