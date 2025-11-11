# Guía de Integración Backend - Paneles LED

Instrucciones completas para integrar el sistema de paneles LED en tu backend existente.

## 📦 Archivos a Copiar al Backend

### Archivos Esenciales (Obligatorios)

Copia estos 3 archivos Python a tu proyecto backend:

```
panel_protocol.py      ⭐ OBLIGATORIO - Funcionalidades básicas
panel_backend.py       ⭐ OBLIGATORIO - Optimizado para backend
panel_advanced.py      ⭐ OPCIONAL - Solo si necesitas imágenes, ventanas, etc.
```

### Ubicación en tu Backend

```
tu_proyecto_backend/
├── app/
│   └── services/
│       ├── panel_protocol.py      ← Copiar aquí
│       ├── panel_backend.py       ← Copiar aquí
│       └── panel_advanced.py      ← Copiar aquí (opcional)
```

O si prefieres como paquete:

```
tu_proyecto_backend/
├── app/
│   └── panel_led/
│       ├── __init__.py            ← Crear vacío
│       ├── protocol.py            ← panel_protocol.py renombrado
│       ├── backend.py             ← panel_backend.py renombrado
│       └── advanced.py            ← panel_advanced.py renombrado
```

---

## 📋 Comandos de Copia

### Opción 1: Copia Directa

```bash
# Ir a tu proyecto backend
cd /ruta/a/tu/backend

# Crear directorio para paneles (si no existe)
mkdir -p app/services

# Copiar archivos esenciales
cp /Volumes/SWAT_WORK/00\ -\ PROYECTOS/04\ -\ ALTEA/04\ -\ PROTOCOLO_PANEL/panel_protocol.py app/services/
cp /Volumes/SWAT_WORK/00\ -\ PROYECTOS/04\ -\ ALTEA/04\ -\ PROTOCOLO_PANEL/panel_backend.py app/services/

# Copiar avanzado (opcional)
cp /Volumes/SWAT_WORK/00\ -\ PROYECTOS/04\ -\ ALTEA/04\ -\ PROTOCOLO_PANEL/panel_advanced.py app/services/
```

### Opción 2: Como Módulo Python

```bash
# Crear estructura de paquete
mkdir -p app/panel_led
touch app/panel_led/__init__.py

# Copiar archivos
cp panel_protocol.py app/panel_led/protocol.py
cp panel_backend.py app/panel_led/backend.py
cp panel_advanced.py app/panel_led/advanced.py  # opcional
```

---

## 📚 Documentación a Enviar

### Para Desarrolladores Backend

**Documentos esenciales:**

1. **`backend-integration.md`** ⭐ PRINCIPAL
   - Guía completa de integración
   - Ejemplos con Django, Flask, FastAPI
   - Todas las funciones explicadas
   - Mejores prácticas

2. **`INTEGRACION_BACKEND.md`** (este documento)
   - Instrucciones rápidas de setup
   - Qué archivos copiar
   - Comandos específicos

3. **`README.md`**
   - Documentación general del sistema
   - Tablas de referencia (colores, tamaños, etc.)

### Opcional (según necesidades)

4. **`advanced-features.md`**
   - Solo si necesitan imágenes, ventanas dinámicas, etc.

5. **`EJEMPLOS_HEXADECIMALES.md`**
   - Solo si necesitan debugging bajo nivel

---

## 🚀 Setup Rápido (5 minutos)

### Paso 1: Copiar Archivos

```bash
# Copiar los 2 archivos esenciales
cp panel_protocol.py tu_backend/app/services/
cp panel_backend.py tu_backend/app/services/
```

### Paso 2: Verificar Importación

```python
# En tu backend, probar importación
from app.services.panel_backend import quick_send, quick_send_all

# Test rápido
result = quick_send(
    ip="192.168.10.110",
    window=0,
    text="TEST",
    color="green"
)
print(f"✓ Integración OK" if result else "✗ Error")
```

### Paso 3: Integrar en tu API

**Ejemplo Django:**
```python
# views.py
from app.services.panel_backend import quick_send_all
from django.http import JsonResponse

def update_panels(request):
    result = quick_send_all(
        ip="192.168.10.110",
        windows=[0, 1, 2, 3, 4, 5, 6],
        text=request.POST.get('text', 'LIBRE'),
        color=request.POST.get('color', 'green')
    )
    return JsonResponse(result)
```

**Ejemplo FastAPI:**
```python
# main.py
from app.services.panel_backend import PanelBackend
from fastapi import FastAPI

app = FastAPI()
panel = PanelBackend("192.168.10.110")

@app.post("/panel/update")
async def update_panel(text: str, color: str = "green"):
    result = panel.send_to_window(0, text)
    return {"success": result.success}
```

---

## ✅ Checklist de Integración

### Pre-integración

- [ ] Verificar que el panel es accesible desde el backend
- [ ] Confirmar IP y puerto (por defecto: 5200)
- [ ] Probar conectividad: `ping 192.168.10.110`

### Durante la integración

- [ ] Copiar `panel_protocol.py` al backend
- [ ] Copiar `panel_backend.py` al backend
- [ ] Copiar `panel_advanced.py` si se necesita (opcional)
- [ ] Verificar que se importan correctamente
- [ ] Ejecutar test de conexión

### Post-integración

- [ ] Crear endpoint/función de actualización de panel
- [ ] Implementar manejo de errores
- [ ] Agregar logging de operaciones
- [ ] Documentar uso interno para el equipo
- [ ] Hacer pruebas con el panel real

---

## 🔧 Configuración Recomendada

### Variables de Entorno

```bash
# .env
PANEL_LED_IP=192.168.10.110
PANEL_LED_PORT=5200
PANEL_LED_TIMEOUT=5
PANEL_LED_RETRY_ATTEMPTS=3
```

### Configuración en Backend

```python
# config.py
import os

PANEL_CONFIG = {
    'ip': os.getenv('PANEL_LED_IP', '192.168.10.110'),
    'port': int(os.getenv('PANEL_LED_PORT', 5200)),
    'timeout': int(os.getenv('PANEL_LED_TIMEOUT', 5)),
    'retry_attempts': int(os.getenv('PANEL_LED_RETRY_ATTEMPTS', 3))
}
```

### Singleton para el Backend

```python
# panel_manager.py
from app.services.panel_backend import PanelBackend
from .config import PANEL_CONFIG

class PanelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._backend = PanelBackend(
                ip_address=PANEL_CONFIG['ip'],
                port=PANEL_CONFIG['port'],
                timeout=PANEL_CONFIG['timeout'],
                retry_attempts=PANEL_CONFIG['retry_attempts']
            )
        return cls._instance
    
    def send_to_all(self, text, color="green"):
        """Envía a todas las ventanas"""
        return self._backend.send_same_to_all_windows(
            text=text,
            windows=[0, 1, 2, 3, 4, 5, 6],
            color=getattr(TextColor, color.upper())
        )

# Uso en tu backend
panel_manager = PanelManager()
panel_manager.send_to_all("LIBRE", "green")
```

---

## 📖 Ejemplos de Uso por Framework

### Django

```python
# services/panel_service.py
from app.services.panel_backend import PanelBackend, WindowMessage
from panel_protocol import TextColor
import logging

logger = logging.getLogger(__name__)

class PanelService:
    def __init__(self):
        self.panel = PanelBackend("192.168.10.110")
    
    def update_status(self, status: str):
        """Actualiza estado en el panel"""
        color_map = {
            'libre': TextColor.GREEN,
            'ocupado': TextColor.RED,
            'cerrado': TextColor.YELLOW
        }
        
        try:
            result = self.panel.send_to_window(
                window_number=0,
                text=status.upper(),
                color=color_map.get(status.lower(), TextColor.GREEN)
            )
            
            if result.success:
                logger.info(f"Panel updated: {status}")
            else:
                logger.error(f"Failed to update panel: {result.error_message}")
            
            return result.success
            
        except Exception as e:
            logger.exception("Error updating panel")
            return False

# views.py
from .services.panel_service import PanelService

panel_service = PanelService()

def cambiar_estado(request, estado):
    if panel_service.update_status(estado):
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False}, status=500)
```

### Flask

```python
# app.py
from flask import Flask, request, jsonify
from services.panel_backend import quick_send_all
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PANEL_IP = "192.168.10.110"

@app.route('/api/panel/update', methods=['POST'])
def update_panel():
    """Actualiza el panel con el texto recibido"""
    data = request.get_json()
    
    text = data.get('text', 'LIBRE')
    color = data.get('color', 'green')
    windows = data.get('windows', [0, 1, 2, 3, 4, 5, 6])
    
    logger.info(f"Updating panel: text={text}, color={color}")
    
    result = quick_send_all(
        ip=PANEL_IP,
        windows=windows,
        text=text,
        color=color
    )
    
    if result['success']:
        logger.info(f"Panel updated successfully: {result['successful']}/{result['total']}")
        return jsonify(result), 200
    else:
        logger.error(f"Failed to update panel: {result['failed']} failures")
        return jsonify(result), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### FastAPI

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from services.panel_backend import PanelBackend
from panel_protocol import TextColor
import logging

app = FastAPI(title="Panel LED API")
logger = logging.getLogger(__name__)

# Singleton del backend
panel_backend = PanelBackend("192.168.10.110", retry_attempts=3)

class PanelUpdate(BaseModel):
    text: str
    color: str = "green"
    windows: List[int] = [0, 1, 2, 3, 4, 5, 6]

@app.on_event("startup")
async def startup_event():
    """Verificar conexión al iniciar"""
    success, error = panel_backend.test_connection()
    if success:
        logger.info("Panel connected successfully")
    else:
        logger.warning(f"Panel not available: {error}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    success, error = panel_backend.test_connection()
    return {
        "status": "healthy" if success else "degraded",
        "panel": "connected" if success else "disconnected"
    }

@app.post("/api/v1/panel/update")
async def update_panel(update: PanelUpdate):
    """Actualizar panel"""
    color_map = {
        "red": TextColor.RED,
        "green": TextColor.GREEN,
        "yellow": TextColor.YELLOW,
        "blue": TextColor.BLUE
    }
    
    result = panel_backend.send_same_to_all_windows(
        text=update.text,
        windows=update.windows,
        color=color_map.get(update.color.lower(), TextColor.GREEN)
    )
    
    if result.all_successful:
        return {
            "success": True,
            "windows_updated": result.successful,
            "execution_time": result.execution_time
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"{result.failed} windows failed to update"
        )
```

---

## 🔍 Testing en el Backend

### Test de Integración

Crear archivo `tests/test_panel_integration.py`:

```python
import pytest
from app.services.panel_backend import PanelBackend

@pytest.fixture
def panel():
    return PanelBackend("192.168.10.110")

def test_connection(panel):
    """Test que el panel es accesible"""
    success, error = panel.test_connection()
    assert success, f"Panel not accessible: {error}"

def test_send_text(panel):
    """Test envío de texto básico"""
    result = panel.send_to_window(0, "TEST")
    assert result.success, f"Failed to send: {result.error_message}"

def test_send_to_all_windows(panel):
    """Test envío a múltiples ventanas"""
    result = panel.send_same_to_all_windows(
        text="TEST",
        windows=[0, 1, 2]
    )
    assert result.all_successful
    assert result.successful == 3
```

---

## 📞 Soporte y Contacto

### Para el Equipo de Desarrollo

**Documentos de referencia:**
1. `backend-integration.md` - Guía completa
2. Este documento - Setup rápido
3. `README.md` - Referencia general

**En caso de problemas:**
1. Verificar conectividad de red al panel
2. Revisar logs con `verbose=True`
3. Verificar IP y puerto correctos
4. Comprobar que el panel responde a ping

### Información del Panel

```
IP Panel:        192.168.10.110
Puerto:          5200
Protocolo:       TCP
Ventanas:        0-6 (7 ventanas)
Timeout:         5 segundos (configurable)
Reintentos:      3 (configurable)
```

---

## 📦 Resumen Ejecutivo

### ¿Qué copiar?

```
✅ panel_protocol.py  (obligatorio)
✅ panel_backend.py   (obligatorio)
⭐ panel_advanced.py  (opcional)
```

### ¿Qué documentación enviar?

```
📄 backend-integration.md    (principal - 150+ ejemplos)
📄 INTEGRACION_BACKEND.md    (este - setup rápido)
📄 README.md                 (referencia general)
```

### ¿Cuánto tarda la integración?

```
⏱️ Setup básico:           5 minutos
⏱️ Integración completa:   30 minutos
⏱️ Testing:                15 minutos
────────────────────────────────────
   TOTAL:                  ~1 hora
```

### Líneas de código necesarias

```python
# Caso más simple (3 líneas)
from panel_backend import quick_send_all
result = quick_send_all("192.168.10.110", [0,1,2,3,4,5,6], "LIBRE", "green")
print(f"Exitoso: {result['success']}")
```

---

**Versión**: 1.0  
**Fecha**: 10 de Noviembre de 2025  
**Proyecto**: ALTEA - PROTOCOLO_PANEL

