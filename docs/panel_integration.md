# Integración Avanzada con Paneles Electrónicos - Parking Altea v2.4

## 📋 Resumen Ejecutivo

**Versión**: v2.4 - Integración Avanzada con Paneles Electrónicos  
**Fecha**: 26 de Junio de 2025  
**Objetivo**: Implementar comunicación nativa con paneles Rotuloselectronicos.NET usando el protocolo CP5200  
**Estado**: 🟡 **EN DESARROLLO - Fase 1**

## 🎯 Objetivos de la Integración

### Objetivos Principales
1. **Comunicación nativa** con paneles usando protocolo CP5200
2. **Eliminación de dependencias** externas para comunicación
3. **Optimización de rendimiento** en envío de mensajes
4. **Soporte completo** para todas las funcionalidades de paneles
5. **Monitoreo avanzado** del estado de comunicación

### Objetivos Técnicos
- Implementar protocolo TCP/IP directo con paneles
- Soporte para texto, imágenes, reloj y comandos
- Gestión de conexiones persistentes
- Manejo robusto de errores y reconexión
- Logging detallado de comunicación

## 📚 Análisis de Documentación Técnica

### Recursos Disponibles

#### SDK Rotuloselectronicos.NET
**Ubicación**: `/docs/Rotuloselectronicos.NET_API+ejemplos/`  
**Contenido**:
- Librería CP5200.dll (API nativa)
- Documentación PDF de protocolos
- Ejemplos en C#, VB.NET, VC++
- Aplicaciones de prueba ejecutables

#### Documentación PDF Identificada
1. **Basic Protocol of Rotuloselectronicos.net LED Display Controller.pdf**
2. **Rotuloselectronicos.net external calls communication protocol.pdf**
3. **The communication protocol for Rotuloselectronicos.net.pdf**
4. **Protocolo cambio de programa.pdf**
5. **Ejemplo protocolos texto network.pdf**
6. **Ejemplo texto estatico protocolos network.pdf**

#### Código Fuente de Ejemplo
**Ubicación**: `/docs/Rotuloselectronicos.NET_API+ejemplos/Rotuloselectronicos.NET API/Rotuloselectronicos.NET API SDK/CPower_CSharp/`

### Funciones Clave del SDK CP5200

#### Inicialización y Conexión
```csharp
// Inicialización de conexión TCP/IP
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);

// Cierre de conexión
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_Close();
```

#### Envío de Texto
```csharp
// Envío de texto con parámetros completos
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendText(
    int nCardID,        // ID del panel
    int nWndNo,         // Número de ventana (0-7)
    IntPtr pText,       // Puntero al texto
    int crColor,        // Color (RGB)
    int nFontSize,      // Tamaño de fuente
    int nSpeed,         // Velocidad de desplazamiento
    int nEffect,        // Efecto visual
    int nStayTime,      // Tiempo de permanencia
    int nAlignment      // Alineación del texto
);
```

#### Envío de Imágenes
```csharp
// Envío de imágenes con posicionamiento
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendPicture(
    int nCardID,           // ID del panel
    int nWndNo,            // Número de ventana
    int nPosX,             // Posición X
    int nPosY,             // Posición Y
    int nCx,               // Ancho
    int nCy,               // Alto
    IntPtr pPictureFile,   // Archivo de imagen
    int nSpeed,            // Velocidad
    int nEffect,           // Efecto
    int nStayTime,         // Tiempo de permanencia
    int nPictRef           // Referencia de imagen
);
```

#### Configuración de Reloj
```csharp
// Configuración de reloj y fecha
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendClock(
    int nCardID,        // ID del panel
    int nWinNo,         // Número de ventana
    int nStayTime,      // Tiempo de permanencia
    int nCalendar,      // Mostrar calendario (0/1)
    int nFormat,        // Formato de fecha/hora
    int nContent,       // Contenido a mostrar
    int nFont,          // Fuente
    int nRed,           // Color rojo
    int nGreen,         // Color verde
    int nBlue,          // Color azul
    IntPtr pTxt         // Texto adicional
);
```

#### Comandos de Control
```csharp
// Reinicio de aplicación
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_RestartApp(byte nCardID);

// Limpieza de ventana
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_ClearWindow(int nCardID, int nWndNo);

// Configuración de programa
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendProgram(int nCardID, IntPtr pProgramFile);
```

## 🏗️ Arquitectura de Integración

### Módulo de Comunicación con Paneles

```
src/
├── panel_communication/
│   ├── __init__.py
│   ├── cp5200_protocol.py      # Implementación del protocolo CP5200
│   ├── panel_client.py         # Cliente mejorado para paneles
│   ├── message_builder.py      # Constructor de mensajes
│   ├── connection_manager.py   # Gestión de conexiones
│   ├── panel_monitor.py        # Monitoreo de estado de paneles
│   └── utils/
│       ├── __init__.py
│       ├── color_utils.py      # Utilidades de color
│       ├── image_utils.py      # Procesamiento de imágenes
│       └── text_utils.py       # Procesamiento de texto
```

### Clases Principales

#### CP5200Protocol
```python
class CP5200Protocol:
    """Implementación del protocolo CP5200 para comunicación con paneles"""
    
    def __init__(self):
        self.connections = {}  # Cache de conexiones
        self.timeout = 5000    # Timeout por defecto
    
    def connect(self, ip: str, port: int = 5000, card_id: int = 1) -> bool:
        """Establece conexión con un panel"""
        
    def disconnect(self, card_id: int) -> bool:
        """Cierra conexión con un panel"""
        
    def send_text(self, card_id: int, text: str, **kwargs) -> bool:
        """Envía texto a un panel"""
        
    def send_image(self, card_id: int, image_path: str, **kwargs) -> bool:
        """Envía imagen a un panel"""
        
    def send_clock(self, card_id: int, **kwargs) -> bool:
        """Configura reloj en un panel"""
        
    def restart_app(self, card_id: int) -> bool:
        """Reinicia aplicación en un panel"""
```

#### ConnectionManager
```python
class ConnectionManager:
    """Gestión de conexiones TCP/IP con paneles"""
    
    def __init__(self):
        self.active_connections = {}
        self.connection_pool = {}
    
    def get_connection(self, ip: str, port: int) -> Connection:
        """Obtiene o crea conexión TCP/IP"""
        
    def close_connection(self, ip: str, port: int) -> bool:
        """Cierra conexión específica"""
        
    def close_all(self) -> bool:
        """Cierra todas las conexiones"""
        
    def is_connected(self, ip: str, port: int) -> bool:
        """Verifica si hay conexión activa"""
```

#### MessageBuilder
```python
class MessageBuilder:
    """Constructor de mensajes para paneles"""
    
    def __init__(self):
        self.default_params = {
            'font_size': 16,
            'color': 0xFFFFFF,  # Blanco
            'speed': 5,
            'effect': 0,        # Sin efecto
            'stay_time': 5,
            'alignment': 1      # Centrado
        }
    
    def build_text_message(self, text: str, **kwargs) -> dict:
        """Construye mensaje de texto"""
        
    def build_image_message(self, image_path: str, **kwargs) -> dict:
        """Construye mensaje de imagen"""
        
    def build_clock_message(self, **kwargs) -> dict:
        """Construye mensaje de reloj"""
        
    def build_command_message(self, command: str, **kwargs) -> dict:
        """Construye mensaje de comando"""
```

## 🔧 Implementación Técnica

### Protocolo TCP/IP Directo

#### Estructura de Mensaje
```python
class CP5200Message:
    """Estructura de mensaje CP5200"""
    
    def __init__(self, command: int, data: bytes = b''):
        self.command = command
        self.data = data
        self.length = len(data)
        self.checksum = self._calculate_checksum()
    
    def to_bytes(self) -> bytes:
        """Convierte mensaje a bytes para envío"""
        header = struct.pack('<BBHH', 0xAA, 0x55, self.command, self.length)
        return header + self.data + struct.pack('<H', self.checksum)
    
    def _calculate_checksum(self) -> int:
        """Calcula checksum del mensaje"""
        checksum = self.command + self.length
        for byte in self.data:
            checksum += byte
        return checksum & 0xFFFF
```

#### Comandos del Protocolo
```python
class CP5200Commands:
    """Comandos del protocolo CP5200"""
    
    # Comandos básicos
    CONNECT = 0x01
    DISCONNECT = 0x02
    PING = 0x03
    
    # Comandos de texto
    SEND_TEXT = 0x10
    CLEAR_TEXT = 0x11
    
    # Comandos de imagen
    SEND_IMAGE = 0x20
    CLEAR_IMAGE = 0x21
    
    # Comandos de reloj
    SEND_CLOCK = 0x30
    SET_TIME = 0x31
    
    # Comandos de control
    RESTART = 0x40
    CONFIGURE = 0x41
    GET_STATUS = 0x42
```

### Gestión de Conexiones

#### Pool de Conexiones
```python
class ConnectionPool:
    """Pool de conexiones TCP/IP"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = {}
        self.lock = threading.Lock()
    
    def get_connection(self, key: str) -> Optional[socket.socket]:
        """Obtiene conexión del pool"""
        with self.lock:
            if key in self.connections:
                conn = self.connections[key]
                if self._is_connection_alive(conn):
                    return conn
                else:
                    del self.connections[key]
            
            if len(self.connections) < self.max_connections:
                return self._create_connection(key)
            return None
    
    def _create_connection(self, key: str) -> Optional[socket.socket]:
        """Crea nueva conexión TCP/IP"""
        try:
            ip, port = key.split(':')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((ip, int(port)))
            self.connections[key] = sock
            return sock
        except Exception as e:
            logger.error(f"Error creating connection to {key}: {e}")
            return None
```

### Procesamiento de Mensajes

#### Constructor de Mensajes de Texto
```python
def build_text_message(self, text: str, **kwargs) -> dict:
    """Construye mensaje de texto optimizado"""
    
    # Parámetros por defecto
    params = self.default_params.copy()
    params.update(kwargs)
    
    # Validación de texto
    if not text or len(text) > 1024:
        raise ValueError("Texto inválido o demasiado largo")
    
    # Codificación UTF-8
    text_bytes = text.encode('utf-8')
    
    # Estructura del mensaje
    message = {
        'command': CP5200Commands.SEND_TEXT,
        'data': {
            'text': text_bytes,
            'font_size': params['font_size'],
            'color': params['color'],
            'speed': params['speed'],
            'effect': params['effect'],
            'stay_time': params['stay_time'],
            'alignment': params['alignment']
        }
    }
    
    return message
```

#### Constructor de Mensajes de Imagen
```python
def build_image_message(self, image_path: str, **kwargs) -> dict:
    """Construye mensaje de imagen"""
    
    # Validación de archivo
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
    
    # Procesamiento de imagen
    image_data = self._process_image(image_path, kwargs.get('width'), kwargs.get('height'))
    
    # Estructura del mensaje
    message = {
        'command': CP5200Commands.SEND_IMAGE,
        'data': {
            'image_data': image_data,
            'pos_x': kwargs.get('pos_x', 0),
            'pos_y': kwargs.get('pos_y', 0),
            'width': kwargs.get('width', 64),
            'height': kwargs.get('height', 32),
            'speed': kwargs.get('speed', 5),
            'effect': kwargs.get('effect', 0),
            'stay_time': kwargs.get('stay_time', 5)
        }
    }
    
    return message
```

## 📊 Monitoreo y Logging

### Sistema de Monitoreo
```python
class PanelMonitor:
    """Monitoreo avanzado de paneles"""
    
    def __init__(self):
        self.panel_status = {}
        self.communication_log = []
        self.error_count = {}
        self.last_communication = {}
    
    def monitor_panel(self, panel_id: int, ip: str) -> dict:
        """Monitorea estado de un panel específico"""
        
        status = {
            'panel_id': panel_id,
            'ip': ip,
            'timestamp': datetime.now(),
            'ping_status': self._ping_panel(ip),
            'connection_status': self._check_connection(ip),
            'last_message': self.last_communication.get(panel_id),
            'error_count': self.error_count.get(panel_id, 0)
        }
        
        self.panel_status[panel_id] = status
        return status
    
    def log_communication(self, panel_id: int, message: str, success: bool):
        """Registra comunicación con panel"""
        
        log_entry = {
            'timestamp': datetime.now(),
            'panel_id': panel_id,
            'message': message,
            'success': success,
            'response_time': self._get_response_time()
        }
        
        self.communication_log.append(log_entry)
        self.last_communication[panel_id] = log_entry
        
        if not success:
            self.error_count[panel_id] = self.error_count.get(panel_id, 0) + 1
```

### Logging Detallado
```python
class CommunicationLogger:
    """Logger especializado para comunicación con paneles"""
    
    def __init__(self, log_file: str = "panel_communication.log"):
        self.logger = logging.getLogger('panel_communication')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_message_sent(self, panel_id: int, message: str, response_time: float):
        """Registra mensaje enviado exitosamente"""
        self.logger.info(
            f"Message sent to panel {panel_id}: {message} "
            f"(Response time: {response_time:.2f}ms)"
        )
    
    def log_message_error(self, panel_id: int, message: str, error: str):
        """Registra error en envío de mensaje"""
        self.logger.error(
            f"Error sending message to panel {panel_id}: {message} - {error}"
        )
    
    def log_connection_status(self, panel_id: int, ip: str, status: bool):
        """Registra estado de conexión"""
        status_str = "CONNECTED" if status else "DISCONNECTED"
        self.logger.info(f"Panel {panel_id} ({ip}): {status_str}")
```

## 🧪 Pruebas y Validación

### Pruebas Unitarias
```python
class TestCP5200Protocol:
    """Pruebas unitarias del protocolo CP5200"""
    
    def setUp(self):
        self.protocol = CP5200Protocol()
        self.test_panel_ip = "192.168.1.100"
        self.test_panel_port = 5000
    
    def test_connection_establishment(self):
        """Prueba establecimiento de conexión"""
        result = self.protocol.connect(self.test_panel_ip, self.test_panel_port)
        assert result == True
        assert self.protocol.is_connected(self.test_panel_ip)
    
    def test_text_message_sending(self):
        """Prueba envío de mensaje de texto"""
        self.protocol.connect(self.test_panel_ip, self.test_panel_port)
        result = self.protocol.send_text(1, "Test Message")
        assert result == True
    
    def test_image_message_sending(self):
        """Prueba envío de mensaje de imagen"""
        self.protocol.connect(self.test_panel_ip, self.test_panel_port)
        result = self.protocol.send_image(1, "test_image.png")
        assert result == True
    
    def test_connection_timeout(self):
        """Prueba timeout de conexión"""
        result = self.protocol.connect("192.168.1.999", self.test_panel_port)
        assert result == False
```

### Pruebas de Integración
```python
class TestPanelIntegration:
    """Pruebas de integración con paneles reales"""
    
    def setUp(self):
        self.panel_client = PanelClient()
        self.test_panels = [
            {'id': 1, 'ip': '192.168.1.101'},
            {'id': 2, 'ip': '192.168.1.102'},
            {'id': 3, 'ip': '192.168.1.103'}
        ]
    
    def test_multiple_panel_communication(self):
        """Prueba comunicación con múltiples paneles"""
        for panel in self.test_panels:
            result = self.panel_client.send_message(
                panel['id'], 
                f"Test message for panel {panel['id']}"
            )
            assert result['success'] == True
    
    def test_concurrent_messages(self):
        """Prueba envío concurrente de mensajes"""
        import threading
        
        def send_message(panel_id):
            return self.panel_client.send_message(panel_id, f"Concurrent test {panel_id}")
        
        threads = []
        for panel in self.test_panels:
            thread = threading.Thread(target=send_message, args=(panel['id'],))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
```

## 📈 Métricas y Rendimiento

### Métricas Objetivo
- **Tiempo de envío**: < 100ms por mensaje
- **Tasa de éxito**: > 99.5% de mensajes entregados
- **Reconexión**: < 2 segundos tras pérdida de conexión
- **Concurrencia**: Soporte para 10+ paneles simultáneos
- **Memoria**: < 50MB de uso por módulo

### Monitoreo de Rendimiento
```python
class PerformanceMonitor:
    """Monitoreo de rendimiento de comunicación"""
    
    def __init__(self):
        self.metrics = {
            'messages_sent': 0,
            'messages_failed': 0,
            'total_response_time': 0,
            'connection_errors': 0,
            'last_reset': datetime.now()
        }
        self.lock = threading.Lock()
    
    def record_message_sent(self, response_time: float):
        """Registra mensaje enviado exitosamente"""
        with self.lock:
            self.metrics['messages_sent'] += 1
            self.metrics['total_response_time'] += response_time
    
    def record_message_failed(self):
        """Registra mensaje fallido"""
        with self.lock:
            self.metrics['messages_failed'] += 1
    
    def get_success_rate(self) -> float:
        """Calcula tasa de éxito"""
        total = self.metrics['messages_sent'] + self.metrics['messages_failed']
        if total == 0:
            return 0.0
        return (self.metrics['messages_sent'] / total) * 100
    
    def get_average_response_time(self) -> float:
        """Calcula tiempo de respuesta promedio"""
        if self.metrics['messages_sent'] == 0:
            return 0.0
        return self.metrics['total_response_time'] / self.metrics['messages_sent']
```

## 🔄 Plan de Implementación

### Fase 1: Análisis y Diseño (EN PROGRESO)
- [x] Revisión de documentación técnica
- [x] Identificación de funciones clave
- [ ] Diseño de arquitectura del módulo
- [ ] Definición de protocolo de comunicación
- [ ] Planificación de pruebas

### Fase 2: Implementación Base (PENDIENTE)
- [ ] Desarrollo del protocolo CP5200
- [ ] Implementación de conexión TCP/IP
- [ ] Funciones básicas de envío de texto
- [ ] Sistema de gestión de conexiones
- [ ] Logging y manejo de errores

### Fase 3: Funcionalidades Avanzadas (PENDIENTE)
- [ ] Soporte para imágenes y multimedia
- [ ] Implementación de reloj y fecha
- [ ] Efectos visuales y animaciones
- [ ] Comandos de control avanzados
- [ ] Optimización de rendimiento

### Fase 4: Integración y Pruebas (PENDIENTE)
- [ ] Integración con sistema existente
- [ ] Pruebas con paneles reales
- [ ] Validación de funcionalidades
- [ ] Optimización y ajustes
- [ ] Documentación de uso

### Fase 5: Despliegue y Validación (PENDIENTE)
- [ ] Despliegue en servidor de producción
- [ ] Pruebas de integración completa
- [ ] Monitoreo de funcionamiento
- [ ] Documentación final
- [ ] Entrenamiento y transferencia

## 📝 Documentación Técnica

### Archivos a Crear
- [ ] **cp5200_protocol.md** - Especificación detallada del protocolo
- [ ] **panel_communication.md** - Guía de uso del módulo
- [ ] **integration_examples.md** - Ejemplos de código
- [ ] **troubleshooting_panels.md** - Resolución de problemas
- [ ] **performance_guide.md** - Guía de optimización

### Código de Ejemplo
```python
# Ejemplo de uso del módulo de comunicación
from src.panel_communication import CP5200Protocol, MessageBuilder

# Inicialización
protocol = CP5200Protocol()
builder = MessageBuilder()

# Conexión con panel
protocol.connect("192.168.1.100", 5000, card_id=1)

# Envío de texto
text_message = builder.build_text_message(
    "Parking Altea - Plazas disponibles: 45",
    font_size=20,
    color=0x00FF00,  # Verde
    speed=3,
    effect=1,        # Desplazamiento
    stay_time=10
)
protocol.send_text(1, text_message)

# Envío de reloj
clock_message = builder.build_clock_message(
    calendar=True,
    format=1,        # HH:MM:SS
    content=1,       # Hora y fecha
    font=1,
    red=255,
    green=255,
    blue=255
)
protocol.send_clock(1, **clock_message)
```

---

**Próxima actualización**: Al completar la Fase 2 (Implementación Base)  
**Responsable**: Equipo de desarrollo  
**Estado actual**: 🟡 **EN DESARROLLO - Fase 1** 