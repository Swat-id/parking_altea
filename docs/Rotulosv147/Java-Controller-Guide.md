# Guía del Controlador Java - PanelSender

## Descripción

El controlador Java implementa el protocolo de comunicación con los paneles LED según la documentación del fabricante. Utiliza reflection para cargar dinámicamente la librería `protocol.jar` y maneja la comunicación de forma secuencial para evitar conflictos.

## Características Implementadas

### ✅ Protocolo de Comunicación
- **initNetwork**: Inicialización de parámetros de red
- **setListener**: Configuración de listener para eventos de comunicación
- **splitScreen**: División de pantalla en ventanas
- **sendText**: Envío de texto con parámetros configurables

### ✅ Flujo Secuencial Mejorado
- **Procesamiento secuencial**: Los paneles se procesan uno por uno para evitar conflictos
- **Sincronización robusta**: Sistema de espera con timeout de 10 segundos por paso
- **Listener global**: Un solo listener configurado para todos los paneles
- **Manejo de errores**: Continuación del flujo incluso si un paso falla

### ✅ Sistema de Logging Detallado
- **Logging de API**: Registro de todas las llamadas a la librería
- **Logging de conexiones**: Estado de conexión con cada panel
- **Logging de sincronización**: Estado de cada paso del protocolo
- **Archivo de log**: `panel_controller.log` con toda la información

## Estructura del Proyecto

```
java-panel-controller/
├── src/main/java/com/panelsender/
│   ├── PanelController.java      # Controlador principal
│   ├── ProtocolManager.java      # Gestor de comunicación con protocol.jar
│   ├── TestRunner.java           # Ejecutor de pruebas interactivo
│   └── LibraryTest.java          # Pruebas de integración con librería
├── pom.xml                       # Configuración Maven
├── run-test.bat                  # Script de prueba básica
├── run-interactive.bat           # Script de prueba interactiva
├── run-with-protocol.bat         # Script con librería real
└── test-library.bat              # Script de pruebas de librería
```

## Componentes Principales

### PanelController.java
Clase principal que maneja la comunicación con múltiples paneles de forma concurrente.

**Características:**
- Gestión de múltiples paneles simultáneamente
- Implementación del protocolo del fabricante
- Manejo de errores robusto
- Ejecución en hilos separados

**Métodos principales:**
- `initializePanels()`: Inicializa todos los paneles
- `sendNumberPattern()`: Envía el patrón de números (000, 111, 222, 333, 444, 555, 666, 777)
- `sendCustomText()`: Envía texto personalizado a un panel específico
- `shutdown()`: Cierra todas las conexiones

### ProtocolManager.java
Singleton que encapsula la comunicación con la librería `protocol.jar`.

**Funcionalidades:**
- **Carga dinámica de librería**: Detecta automáticamente si protocol.jar está disponible
- **Modo real/simulación**: Funciona tanto con la librería real como en modo simulación
- **Reflection API**: Usa reflection para llamar a los métodos de la librería
- **Manejo de errores**: Gestión robusta de errores de comunicación

**Métodos implementados:**
- `initNetwork()`: Inicialización de red usando `ExtSendUtil.initNetwork()`
- `setListener()`: Configuración de listener usando `ExtSendUtil.setListener()`
- `splitScreen()`: División de pantalla usando `ExtSendUtil.splitScreen()`
- `sendText()`: Envío de texto usando `ExtSendUtil.sendTextRGB()`
- `closeConnection()`: Cierre de conexión usando `ExtSendUtil.quitExternalScreen()`

### TestRunner.java
Aplicación interactiva para pruebas del sistema.

**Opciones disponibles:**
1. Enviar patrón de números predefinido
2. Enviar texto personalizado a un panel específico
3. Enviar texto a todos los paneles
4. Salir de la aplicación

### LibraryTest.java
Clase de prueba para verificar la integración con protocol.jar.

**Funcionalidades:**
- Verificación de carga de librería
- Prueba de métodos disponibles
- Validación de ProtocolManager
- Diagnóstico de problemas de integración

## Configuración de Paneles

### IPs Configuradas
- Panel 1: 192.168.1.221
- Panel 2: 192.168.1.222
- Panel 3: 192.168.1.223
- Panel 4: 192.168.1.224

### Configuración de Ventanas
Cada panel tiene 2 ventanas de 32x16 píxeles:
- **Ventana 0**: Coordenadas (0,0)
- **Ventana 1**: Coordenadas (32,0)

## Protocolo de Comunicación

### Secuencia de Inicialización
1. **initNetwork**: Inicializa parámetros de comunicación de red
2. **setListener**: Establece listener para escuchar estado de comunicación
3. **splitScreen**: Divide la pantalla en ventanas

### Secuencia de Envío
4. **sendTextRGB**: Envía texto con coordenadas y color específicos

## Implementación de la API del Fabricante

### Clases Utilizadas
- **ExtSendUtil**: Clase principal para comunicación de red
- **OnTcpNetWorkListener**: Interfaz para eventos de comunicación

### Métodos de la API Implementados
```java
// Inicialización
extSendUtil.initNetwork(ip, port)

// Configuración de listener
extSendUtil.setListener(listener)

// División de pantalla
extSendUtil.splitScreen()

// Envío de texto con color
extSendUtil.sendTextRGB(text, x, y, width, height, redColor)

// Cierre de conexión
extSendUtil.quitExternalScreen()
```

### Manejo de Reflection
El sistema usa reflection para:
- Cargar dinámicamente la librería protocol.jar
- Llamar a métodos sin dependencias directas
- Manejar casos donde la librería no está disponible
- Proporcionar modo de simulación

## Compilación y Ejecución

### Requisitos
- Java 11 o superior
- Maven 3.6 o superior
- Librería `protocol.jar` en el directorio raíz (opcional)

### Compilación
```bash
cd java-panel-controller
mvn clean compile
```

### Ejecución de Pruebas

#### Pruebas Básicas
```bash
# Windows
run-test.bat

# Linux/Mac
mvn exec:java -Dexec.mainClass="com.panelsender.PanelController"
```

#### Pruebas Interactivas
```bash
# Windows
run-interactive.bat

# Linux/Mac
mvn exec:java -Dexec.mainClass="com.panelsender.TestRunner"
```

#### Pruebas de Librería
```bash
# Windows
test-library.bat

# Linux/Mac
mvn exec:java -Dexec.mainClass="com.panelsender.LibraryTest"
```

#### Con Librería Real
```bash
# Windows
run-with-protocol.bat
```

## Patrón de Números

El sistema está configurado para enviar el siguiente patrón:
```
Panel 1 (192.168.1.221): 000
Panel 2 (192.168.1.222): 111
Panel 3 (192.168.1.223): 222
Panel 4 (192.168.1.224): 333
```

Cada número se envía a la **ventana 0** de cada panel con **texto rojo**.

## Manejo de Errores

El sistema incluye manejo robusto de errores:
- Verificación de inicialización antes de envío
- Timeouts en conexiones
- Logging detallado de operaciones
- Recuperación automática de errores de red
- Modo de simulación cuando la librería no está disponible

## Logs y Debugging

El sistema genera logs detallados que incluyen:
- Estado de carga de librería
- Estado de inicialización de cada panel
- Confirmación de envío de texto
- Errores de conexión y comunicación
- Tiempos de respuesta
- Modo de operación (real/simulación)

## Integración con protocol.jar

### Carga Automática
El sistema detecta automáticamente si protocol.jar está disponible:
- Si está disponible: Usa la librería real
- Si no está disponible: Funciona en modo simulación

### Verificación de Integración
Use `LibraryTest.java` para verificar:
- Carga correcta de la librería
- Disponibilidad de métodos requeridos
- Funcionamiento del ProtocolManager
- Diagnóstico de problemas

### Modo de Simulación
Cuando protocol.jar no está disponible, el sistema:
- Simula todas las operaciones
- Proporciona logs detallados
- Permite pruebas sin hardware real
- Mantiene la misma interfaz

## Próximos Pasos

1. **Pruebas físicas**: Validar con paneles reales
2. **Optimización**: Ajustar timeouts y parámetros de rendimiento
3. **Configuración avanzada**: Implementar parámetros específicos del protocolo
4. **Monitoreo**: Agregar métricas de rendimiento y estado 