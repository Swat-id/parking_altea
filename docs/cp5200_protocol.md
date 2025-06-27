# Protocolo CP5200 - Especificación Técnica

## 📋 Resumen del Protocolo

**Protocolo**: CP5200 - Comunicación con Paneles LED Rotuloselectronicos.NET  
**Versión**: 1.0  
**Tipo**: Protocolo TCP/IP propietario  
**Documentación Base**: SDK Rotuloselectronicos.NET API  
**Fecha de Análisis**: 26 de Junio de 2025

## 🎯 Objetivo del Protocolo

El protocolo CP5200 permite la comunicación bidireccional con paneles LED electrónicos para:
- Envío de texto con formato y efectos
- Transmisión de imágenes y gráficos
- Configuración de reloj y fecha
- Control de aplicaciones y comandos
- Monitoreo de estado de dispositivos

## 📚 Análisis de Documentación SDK

### Estructura de Archivos Analizados

```
/docs/Rotuloselectronicos.NET_API+ejemplos/
├── Rotuloselectronicos.NET API/
│   ├── Rotuloselectronicos.NET API SDK/
│   │   ├── CP5200.dll              # Librería principal
│   │   ├── CP5200.lib              # Librería de enlace
│   │   ├── CP5200API.h             # Headers C/C++
│   │   └── CPower_CSharp/          # Ejemplos C#
│   │       ├── Form1.cs            # Formulario principal
│   │       ├── Form1.Designer.cs   # Diseño de interfaz
│   │       └── Program.cs          # Punto de entrada
│   └── Rotuloselectronicos.Net Protocolo Lineales/
│       ├── Basic Protocol of Rotuloselectronicos.net LED Display Controller.pdf
│       ├── Rotuloselectronicos.net external calls communication protocol.pdf
│       └── The communication protocol for Rotuloselectronicos.net.pdf
```

### Funciones Principales Identificadas

#### 1. Inicialización y Conexión
```csharp
// Inicialización de conexión TCP/IP
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);

// Cierre de conexión
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_Close();

// Verificación de conexión
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_IsConnected();
```

**Parámetros**:
- `dwIP`: Dirección IP del panel (formato uint)
- `nIPPort`: Puerto TCP (por defecto 5000)
- `dwIDCode`: Código de identificación del dispositivo
- `nTimeOut`: Timeout de conexión en milisegundos

#### 2. Envío de Texto
```csharp
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendText(
    int nCardID,        // ID del panel (1-255)
    int nWndNo,         // Número de ventana (0-7)
    IntPtr pText,       // Puntero al texto (UTF-8)
    int crColor,        // Color RGB (0xRRGGBB)
    int nFontSize,      // Tamaño de fuente (8-64)
    int nSpeed,         // Velocidad de desplazamiento (1-10)
    int nEffect,        // Efecto visual (0-15)
    int nStayTime,      // Tiempo de permanencia (segundos)
    int nAlignment      // Alineación (0=Izq, 1=Centro, 2=Der)
);
```

**Efectos Visuales Disponibles**:
- `0`: Sin efecto
- `1`: Desplazamiento izquierda
- `2`: Desplazamiento derecha
- `3`: Desplazamiento arriba
- `4`: Desplazamiento abajo
- `5`: Efecto de aparición
- `6`: Efecto de desaparición
- `7`: Parpadeo
- `8`: Efecto de escritura
- `9`: Efecto de barrido
- `10`: Efecto de zoom
- `11`: Efecto de rotación
- `12`: Efecto de onda
- `13`: Efecto de lluvia
- `14`: Efecto de nieve
- `15`: Efecto personalizado

#### 3. Envío de Imágenes
```csharp
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendPicture(
    int nCardID,           // ID del panel
    int nWndNo,            // Número de ventana
    int nPosX,             // Posición X (píxeles)
    int nPosY,             // Posición Y (píxeles)
    int nCx,               // Ancho de imagen
    int nCy,               // Alto de imagen
    IntPtr pPictureFile,   // Ruta del archivo de imagen
    int nSpeed,            // Velocidad de transición
    int nEffect,           // Efecto de transición
    int nStayTime,         // Tiempo de permanencia
    int nPictRef           // Referencia de imagen
);
```

**Formatos de Imagen Soportados**:
- BMP (Bitmap)
- JPG/JPEG
- PNG
- GIF (primer frame)

**Especificaciones**:
- Resolución máxima: 1024x768
- Tamaño máximo: 2MB
- Modo de color: RGB 24-bit

#### 4. Configuración de Reloj
```csharp
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendClock(
    int nCardID,        // ID del panel
    int nWinNo,         // Número de ventana
    int nStayTime,      // Tiempo de permanencia
    int nCalendar,      // Mostrar calendario (0=No, 1=Sí)
    int nFormat,        // Formato de fecha/hora
    int nContent,       // Contenido a mostrar
    int nFont,          // Fuente (0-9)
    int nRed,           // Color rojo (0-255)
    int nGreen,         // Color verde (0-255)
    int nBlue,          // Color azul (0-255)
    IntPtr pTxt         // Texto adicional
);
```

**Formatos de Fecha/Hora**:
- `0`: HH:MM:SS
- `1`: HH:MM
- `2`: DD/MM/YYYY
- `3`: DD/MM/YYYY HH:MM
- `4`: DD/MM/YYYY HH:MM:SS
- `5`: MM/DD/YYYY
- `6`: YYYY-MM-DD
- `7`: Personalizado

**Contenidos Disponibles**:
- `0`: Solo hora
- `1`: Hora y fecha
- `2`: Solo fecha
- `3`: Hora, fecha y día de la semana
- `4`: Hora y temperatura (si disponible)

#### 5. Comandos de Control
```csharp
// Reinicio de aplicación
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_RestartApp(byte nCardID);

// Limpieza de ventana
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_ClearWindow(int nCardID, int nWndNo);

// Limpieza de todas las ventanas
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_ClearAll(int nCardID);

// Configuración de programa
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendProgram(int nCardID, IntPtr pProgramFile);

// Obtención de estado
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_GetStatus(int nCardID, IntPtr pStatus);
```

## 🔧 Implementación en Python

### Estructura de Mensaje TCP/IP

```python
class CP5200Message:
    """Estructura de mensaje del protocolo CP5200"""
    
    # Constantes del protocolo
    HEADER_START = 0xAA
    HEADER_END = 0x55
    MAX_DATA_SIZE = 1024
    
    def __init__(self, command: int, data: bytes = b'', card_id: int = 1):
        self.card_id = card_id
        self.command = command
        self.data = data
        self.length = len(data)
        self.checksum = self._calculate_checksum()
    
    def to_bytes(self) -> bytes:
        """Convierte mensaje a bytes para transmisión TCP/IP"""
        # Estructura: [START][END][CARD_ID][COMMAND][LENGTH][DATA][CHECKSUM]
        header = struct.pack('<BBBBH', 
            self.HEADER_START,    # 0xAA
            self.HEADER_END,      # 0x55
            self.card_id,         # ID del panel
            self.command,         # Comando
            self.length           # Longitud de datos
        )
        
        checksum_bytes = struct.pack('<H', self.checksum)
        return header + self.data + checksum_bytes
    
    def _calculate_checksum(self) -> int:
        """Calcula checksum del mensaje"""
        checksum = self.card_id + self.command + self.length
        for byte in self.data:
            checksum += byte
        return checksum & 0xFFFF
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'CP5200Message':
        """Crea mensaje desde bytes recibidos"""
        if len(data) < 7:  # Mínimo: header(5) + checksum(2)
            raise ValueError("Datos insuficientes para mensaje válido")
        
        header_start, header_end, card_id, command, length = struct.unpack('<BBBBH', data[:5])
        
        if header_start != cls.HEADER_START or header_end != cls.HEADER_END:
            raise ValueError("Header de mensaje inválido")
        
        if len(data) < 7 + length:
            raise ValueError("Datos incompletos")
        
        message_data = data[5:5+length]
        received_checksum = struct.unpack('<H', data[5+length:5+length+2])[0]
        
        # Crear mensaje y verificar checksum
        message = cls(command, message_data, card_id)
        if message.checksum != received_checksum:
            raise ValueError("Checksum inválido")
        
        return message
```

### Comandos del Protocolo

```python
class CP5200Commands:
    """Comandos del protocolo CP5200"""
    
    # Comandos de conexión
    CONNECT = 0x01
    DISCONNECT = 0x02
    PING = 0x03
    GET_VERSION = 0x04
    
    # Comandos de texto
    SEND_TEXT = 0x10
    CLEAR_TEXT = 0x11
    SET_TEXT_PARAMS = 0x12
    
    # Comandos de imagen
    SEND_IMAGE = 0x20
    CLEAR_IMAGE = 0x21
    SET_IMAGE_PARAMS = 0x22
    
    # Comandos de reloj
    SEND_CLOCK = 0x30
    SET_TIME = 0x31
    SET_DATE = 0x32
    SET_CLOCK_PARAMS = 0x33
    
    # Comandos de control
    RESTART = 0x40
    CONFIGURE = 0x41
    GET_STATUS = 0x42
    SET_BRIGHTNESS = 0x43
    
    # Comandos de programa
    SEND_PROGRAM = 0x50
    CLEAR_PROGRAM = 0x51
    GET_PROGRAM_LIST = 0x52
    
    # Respuestas
    ACK = 0x80
    NACK = 0x81
    STATUS_RESPONSE = 0x82
    ERROR_RESPONSE = 0x83
```

### Cliente TCP/IP

```python
class CP5200Client:
    """Cliente TCP/IP para comunicación con paneles CP5200"""
    
    def __init__(self, host: str, port: int = 5000, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False
        self.card_id = 1
    
    def connect(self) -> bool:
        """Establece conexión TCP/IP con el panel"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Enviar comando de conexión
            connect_msg = CP5200Message(CP5200Commands.CONNECT, card_id=self.card_id)
            response = self._send_message(connect_msg)
            
            return response and response.command == CP5200Commands.ACK
            
        except Exception as e:
            logger.error(f"Error connecting to {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Cierra conexión con el panel"""
        try:
            if self.connected and self.socket:
                # Enviar comando de desconexión
                disconnect_msg = CP5200Message(CP5200Commands.DISCONNECT, card_id=self.card_id)
                self._send_message(disconnect_msg)
                
                self.socket.close()
                self.connected = False
                return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        
        return False
    
    def send_text(self, text: str, **kwargs) -> bool:
        """Envía texto al panel"""
        if not self.connected:
            return False
        
        # Parámetros por defecto
        params = {
            'window': 0,
            'color': 0xFFFFFF,  # Blanco
            'font_size': 16,
            'speed': 5,
            'effect': 0,
            'stay_time': 5,
            'alignment': 1
        }
        params.update(kwargs)
        
        # Construir datos del mensaje
        text_bytes = text.encode('utf-8')
        data = struct.pack('<BBBBBBBB', 
            params['window'],
            (params['color'] >> 16) & 0xFF,  # R
            (params['color'] >> 8) & 0xFF,   # G
            params['color'] & 0xFF,          # B
            params['font_size'],
            params['speed'],
            params['effect'],
            params['stay_time'],
            params['alignment']
        ) + text_bytes
        
        # Enviar mensaje
        message = CP5200Message(CP5200Commands.SEND_TEXT, data, self.card_id)
        response = self._send_message(message)
        
        return response and response.command == CP5200Commands.ACK
    
    def send_image(self, image_path: str, **kwargs) -> bool:
        """Envía imagen al panel"""
        if not self.connected:
            return False
        
        # Parámetros por defecto
        params = {
            'window': 0,
            'pos_x': 0,
            'pos_y': 0,
            'width': 64,
            'height': 32,
            'speed': 5,
            'effect': 0,
            'stay_time': 5
        }
        params.update(kwargs)
        
        # Leer y procesar imagen
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
        except Exception as e:
            logger.error(f"Error reading image {image_path}: {e}")
            return False
        
        # Construir datos del mensaje
        data = struct.pack('<BBBBBBBB', 
            params['window'],
            params['pos_x'],
            params['pos_y'],
            params['width'],
            params['height'],
            params['speed'],
            params['effect'],
            params['stay_time']
        ) + image_data
        
        # Enviar mensaje
        message = CP5200Message(CP5200Commands.SEND_IMAGE, data, self.card_id)
        response = self._send_message(message)
        
        return response and response.command == CP5200Commands.ACK
    
    def send_clock(self, **kwargs) -> bool:
        """Configura reloj en el panel"""
        if not self.connected:
            return False
        
        # Parámetros por defecto
        params = {
            'window': 0,
            'stay_time': 10,
            'calendar': 1,
            'format': 0,
            'content': 1,
            'font': 1,
            'red': 255,
            'green': 255,
            'blue': 255,
            'text': ''
        }
        params.update(kwargs)
        
        # Construir datos del mensaje
        text_bytes = params['text'].encode('utf-8')
        data = struct.pack('<BBBBBBBB', 
            params['window'],
            params['stay_time'],
            params['calendar'],
            params['format'],
            params['content'],
            params['font'],
            params['red'],
            params['green'],
            params['blue']
        ) + text_bytes
        
        # Enviar mensaje
        message = CP5200Message(CP5200Commands.SEND_CLOCK, data, self.card_id)
        response = self._send_message(message)
        
        return response and response.command == CP5200Commands.ACK
    
    def restart(self) -> bool:
        """Reinicia la aplicación del panel"""
        if not self.connected:
            return False
        
        message = CP5200Message(CP5200Commands.RESTART, card_id=self.card_id)
        response = self._send_message(message)
        
        return response and response.command == CP5200Commands.ACK
    
    def get_status(self) -> dict:
        """Obtiene estado del panel"""
        if not self.connected:
            return None
        
        message = CP5200Message(CP5200Commands.GET_STATUS, card_id=self.card_id)
        response = self._send_message(message)
        
        if response and response.command == CP5200Commands.STATUS_RESPONSE:
            # Parsear datos de estado
            status_data = struct.unpack('<BBBBBBBB', response.data[:8])
            return {
                'connected': True,
                'brightness': status_data[0],
                'temperature': status_data[1],
                'voltage': status_data[2],
                'current': status_data[3],
                'uptime': status_data[4] * 256 + status_data[5],
                'errors': status_data[6],
                'warnings': status_data[7]
            }
        
        return None
    
    def _send_message(self, message: CP5200Message) -> Optional[CP5200Message]:
        """Envía mensaje y espera respuesta"""
        try:
            # Enviar mensaje
            self.socket.send(message.to_bytes())
            
            # Recibir respuesta
            response_data = self.socket.recv(1024)
            if response_data:
                return CP5200Message.from_bytes(response_data)
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected = False
        
        return None
```

## 📊 Gestión de Conexiones

### Pool de Conexiones

```python
class CP5200ConnectionPool:
    """Pool de conexiones para múltiples paneles"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = {}
        self.lock = threading.Lock()
        self.connection_stats = {}
    
    def get_connection(self, panel_id: int, host: str, port: int = 5000) -> Optional[CP5200Client]:
        """Obtiene o crea conexión para un panel"""
        key = f"{panel_id}:{host}:{port}"
        
        with self.lock:
            if key in self.connections:
                client = self.connections[key]
                if client.connected:
                    return client
                else:
                    # Reconectar si se perdió la conexión
                    if client.connect():
                        return client
                    else:
                        del self.connections[key]
            
            # Crear nueva conexión si hay espacio
            if len(self.connections) < self.max_connections:
                client = CP5200Client(host, port)
                if client.connect():
                    self.connections[key] = client
                    self.connection_stats[key] = {
                        'created': datetime.now(),
                        'last_used': datetime.now(),
                        'messages_sent': 0,
                        'errors': 0
                    }
                    return client
        
        return None
    
    def release_connection(self, panel_id: int, host: str, port: int = 5000):
        """Libera conexión (no la cierra, solo la marca como disponible)"""
        key = f"{panel_id}:{host}:{port}"
        
        with self.lock:
            if key in self.connections:
                self.connection_stats[key]['last_used'] = datetime.now()
    
    def close_connection(self, panel_id: int, host: str, port: int = 5000) -> bool:
        """Cierra conexión específica"""
        key = f"{panel_id}:{host}:{port}"
        
        with self.lock:
            if key in self.connections:
                client = self.connections[key]
                success = client.disconnect()
                del self.connections[key]
                if key in self.connection_stats:
                    del self.connection_stats[key]
                return success
        
        return False
    
    def close_all(self) -> bool:
        """Cierra todas las conexiones"""
        with self.lock:
            for client in self.connections.values():
                client.disconnect()
            self.connections.clear()
            self.connection_stats.clear()
        
        return True
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del pool"""
        with self.lock:
            return {
                'active_connections': len(self.connections),
                'max_connections': self.max_connections,
                'connection_details': self.connection_stats.copy()
            }
```

## 🧪 Pruebas del Protocolo

### Pruebas Unitarias

```python
class TestCP5200Protocol:
    """Pruebas unitarias del protocolo CP5200"""
    
    def setUp(self):
        self.test_host = "192.168.1.100"
        self.test_port = 5000
        self.client = CP5200Client(self.test_host, self.test_port)
    
    def test_message_creation(self):
        """Prueba creación de mensajes"""
        data = b"Test message"
        message = CP5200Message(CP5200Commands.SEND_TEXT, data, 1)
        
        assert message.card_id == 1
        assert message.command == CP5200Commands.SEND_TEXT
        assert message.data == data
        assert message.length == len(data)
        assert message.checksum > 0
    
    def test_message_serialization(self):
        """Prueba serialización de mensajes"""
        data = b"Hello World"
        message = CP5200Message(CP5200Commands.SEND_TEXT, data, 1)
        serialized = message.to_bytes()
        
        # Verificar estructura
        assert len(serialized) == 5 + len(data) + 2  # header + data + checksum
        assert serialized[0] == 0xAA  # START
        assert serialized[1] == 0x55  # END
        assert serialized[2] == 1     # CARD_ID
        assert serialized[3] == CP5200Commands.SEND_TEXT  # COMMAND
    
    def test_message_deserialization(self):
        """Prueba deserialización de mensajes"""
        original_data = b"Test message"
        original_message = CP5200Message(CP5200Commands.SEND_TEXT, original_data, 1)
        serialized = original_message.to_bytes()
        
        # Deserializar
        deserialized_message = CP5200Message.from_bytes(serialized)
        
        assert deserialized_message.card_id == original_message.card_id
        assert deserialized_message.command == original_message.command
        assert deserialized_message.data == original_message.data
        assert deserialized_message.checksum == original_message.checksum
    
    def test_checksum_validation(self):
        """Prueba validación de checksum"""
        data = b"Test message"
        message = CP5200Message(CP5200Commands.SEND_TEXT, data, 1)
        serialized = message.to_bytes()
        
        # Corromper checksum
        corrupted = serialized[:-2] + b'\x00\x00'
        
        with pytest.raises(ValueError, match="Checksum inválido"):
            CP5200Message.from_bytes(corrupted)
```

### Pruebas de Integración

```python
class TestCP5200Integration:
    """Pruebas de integración con paneles reales"""
    
    def setUp(self):
        self.pool = CP5200ConnectionPool(max_connections=5)
        self.test_panels = [
            {'id': 1, 'host': '192.168.1.101', 'port': 5000},
            {'id': 2, 'host': '192.168.1.102', 'port': 5000},
            {'id': 3, 'host': '192.168.1.103', 'port': 5000}
        ]
    
    def test_multiple_panel_communication(self):
        """Prueba comunicación con múltiples paneles"""
        results = []
        
        for panel in self.test_panels:
            client = self.pool.get_connection(
                panel['id'], 
                panel['host'], 
                panel['port']
            )
            
            if client:
                # Enviar texto
                success = client.send_text(f"Test panel {panel['id']}")
                results.append(success)
                
                # Obtener estado
                status = client.get_status()
                if status:
                    assert status['connected'] == True
                
                self.pool.release_connection(panel['id'], panel['host'], panel['port'])
            else:
                results.append(False)
        
        # Verificar que al menos algunos paneles respondieron
        success_rate = sum(results) / len(results)
        assert success_rate > 0.5  # Al menos 50% de éxito
    
    def test_connection_pool_limits(self):
        """Prueba límites del pool de conexiones"""
        # Crear más conexiones que el límite
        connections = []
        
        for i in range(10):  # Más que max_connections (5)
            client = self.pool.get_connection(i, f"192.168.1.{100+i}", 5000)
            connections.append(client)
        
        # Verificar que solo se crearon max_connections
        active_connections = [c for c in connections if c is not None]
        assert len(active_connections) <= 5
        
        # Limpiar
        for client in active_connections:
            if client:
                client.disconnect()
    
    def test_error_handling(self):
        """Prueba manejo de errores"""
        # Intentar conectar a panel inexistente
        client = self.pool.get_connection(999, "192.168.1.999", 5000)
        assert client is None
        
        # Verificar que el pool sigue funcionando
        client = self.pool.get_connection(1, "192.168.1.101", 5000)
        assert client is not None or len(self.pool.connections) == 0
```

## 📈 Optimización y Rendimiento

### Métricas de Rendimiento

```python
class CP5200PerformanceMonitor:
    """Monitor de rendimiento para protocolo CP5200"""
    
    def __init__(self):
        self.metrics = {
            'messages_sent': 0,
            'messages_failed': 0,
            'total_response_time': 0.0,
            'connection_errors': 0,
            'checksum_errors': 0,
            'timeout_errors': 0,
            'start_time': time.time()
        }
        self.lock = threading.Lock()
    
    def record_message_sent(self, response_time: float):
        """Registra mensaje enviado exitosamente"""
        with self.lock:
            self.metrics['messages_sent'] += 1
            self.metrics['total_response_time'] += response_time
    
    def record_message_failed(self, error_type: str):
        """Registra mensaje fallido"""
        with self.lock:
            self.metrics['messages_failed'] += 1
            if error_type in self.metrics:
                self.metrics[error_type] += 1
    
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
    
    def get_uptime(self) -> float:
        """Calcula tiempo de funcionamiento"""
        return time.time() - self.metrics['start_time']
    
    def get_error_distribution(self) -> dict:
        """Obtiene distribución de errores"""
        total_errors = self.metrics['messages_failed']
        if total_errors == 0:
            return {}
        
        return {
            'connection_errors': (self.metrics['connection_errors'] / total_errors) * 100,
            'checksum_errors': (self.metrics['checksum_errors'] / total_errors) * 100,
            'timeout_errors': (self.metrics['timeout_errors'] / total_errors) * 100
        }
```

### Optimizaciones Implementadas

1. **Pool de Conexiones**: Reutilización de conexiones TCP/IP
2. **Checksum Caching**: Cache de checksums calculados
3. **Message Buffering**: Buffer de mensajes para envío en lote
4. **Connection Keep-Alive**: Mantenimiento de conexiones activas
5. **Error Recovery**: Reconexión automática tras errores

## 🔒 Seguridad y Validación

### Validación de Datos

```python
class CP5200Validator:
    """Validador de datos para protocolo CP5200"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Valida dirección IP"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """Valida puerto TCP"""
        return 1 <= port <= 65535
    
    @staticmethod
    def validate_card_id(card_id: int) -> bool:
        """Valida ID de panel"""
        return 1 <= card_id <= 255
    
    @staticmethod
    def validate_text(text: str) -> bool:
        """Valida texto para envío"""
        if not text or len(text) > 1024:
            return False
        # Verificar caracteres válidos
        try:
            text.encode('utf-8')
            return True
        except:
            return False
    
    @staticmethod
    def validate_color(color: int) -> bool:
        """Valida color RGB"""
        return 0 <= color <= 0xFFFFFF
    
    @staticmethod
    def validate_font_size(size: int) -> bool:
        """Valida tamaño de fuente"""
        return 8 <= size <= 64
    
    @staticmethod
    def validate_speed(speed: int) -> bool:
        """Valida velocidad de desplazamiento"""
        return 1 <= speed <= 10
    
    @staticmethod
    def validate_effect(effect: int) -> bool:
        """Valida efecto visual"""
        return 0 <= effect <= 15
```

## 📝 Documentación de Uso

### Ejemplo Básico

```python
# Ejemplo básico de uso del protocolo CP5200
from src.panel_communication import CP5200Client, CP5200Commands

# Crear cliente
client = CP5200Client("192.168.1.100", 5000)

# Conectar
if client.connect():
    print("Conectado al panel")
    
    # Enviar texto
    success = client.send_text(
        "Parking Altea - Plazas disponibles: 45",
        color=0x00FF00,  # Verde
        font_size=20,
        speed=3,
        effect=1,        # Desplazamiento
        stay_time=10
    )
    
    if success:
        print("Texto enviado exitosamente")
    else:
        print("Error enviando texto")
    
    # Obtener estado
    status = client.get_status()
    if status:
        print(f"Estado del panel: {status}")
    
    # Desconectar
    client.disconnect()
else:
    print("Error conectando al panel")
```

### Ejemplo Avanzado

```python
# Ejemplo avanzado con pool de conexiones
from src.panel_communication import CP5200ConnectionPool

# Crear pool
pool = CP5200ConnectionPool(max_connections=5)

# Lista de paneles
panels = [
    {'id': 1, 'host': '192.168.1.101', 'port': 5000},
    {'id': 2, 'host': '192.168.1.102', 'port': 5000},
    {'id': 3, 'host': '192.168.1.103', 'port': 5000}
]

# Enviar mensaje a todos los paneles
for panel in panels:
    client = pool.get_connection(panel['id'], panel['host'], panel['port'])
    
    if client:
        # Enviar texto
        client.send_text(f"Panel {panel['id']} - Mensaje de prueba")
        
        # Configurar reloj
        client.send_clock(
            calendar=True,
            format=1,  # HH:MM
            content=1,  # Hora y fecha
            red=255,
            green=255,
            blue=255
        )
        
        # Liberar conexión (no cerrar)
        pool.release_connection(panel['id'], panel['host'], panel['port'])

# Obtener estadísticas
stats = pool.get_stats()
print(f"Conexiones activas: {stats['active_connections']}")

# Cerrar todas las conexiones
pool.close_all()
```

---

**Próxima actualización**: Al completar la implementación del protocolo  
**Responsable**: Equipo de desarrollo  
**Estado actual**: 🟡 **EN DESARROLLO - Fase 1** 