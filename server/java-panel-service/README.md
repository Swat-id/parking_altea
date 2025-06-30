# Java Panel Service v2.5

Servicio Java para comunicación con paneles LED basado en la librería del fabricante.

## Características

- ✅ Comunicación con paneles LED usando la librería oficial
- ✅ API REST para envío de mensajes
- ✅ Cache de conexiones por panel
- ✅ Configuración flexible
- ✅ Logging detallado
- ✅ Health checks
- ✅ Validación de datos

## Tecnologías

- **Java 11**
- **Spring Boot 2.7.18**
- **Maven**
- **Lombok**
- **Librería del fabricante**: `protocol-1.2.6.jar`

## Estructura del Proyecto

```
src/main/java/com/parkingaltea/panelservice/
├── PanelServiceApplication.java    # Clase principal
├── controller/
│   └── PanelController.java        # Controlador REST
├── model/
│   ├── PanelMessage.java           # Modelo de mensaje
│   └── PanelResponse.java          # Modelo de respuesta
└── service/
    └── PanelService.java           # Servicio principal
```

## Configuración

El servicio se configura mediante `application.yml`:

```yaml
server:
  port: 5002
  servlet:
    context-path: /api

panel:
  service:
    default:
      port: 5200
      card-id: 1
      window-no: 0
    panels:
      - ip: "172.20.5.50"
        name: "PANEL BASSETA 1"
      # ... más paneles
```

## API Endpoints

### Health Check
```
GET /api/panel/health
```

### Enviar Mensaje
```
POST /api/panel/send
Content-Type: application/json

{
  "panelIP": "172.20.4.52",
  "message": "PANEL 3",
  "color": 1,
  "fontSize": 2,
  "effect": 0,
  "itemNum": 1
}
```

### Estado de Cache
```
GET /api/panel/status
```

### Limpiar Cache
```
POST /api/panel/clear-cache
```

### Colores Disponibles
```
GET /api/panel/colors
```

## Parámetros de Mensaje

| Parámetro | Tipo | Descripción | Valores |
|-----------|------|-------------|---------|
| `panelIP` | String | IP del panel | Obligatorio |
| `message` | String | Texto a mostrar | Obligatorio |
| `color` | Integer | Color del texto | 1-7 (1=Rojo, 2=Verde, etc.) |
| `fontSize` | Integer | Tamaño de fuente | 1-7 |
| `effect` | Integer | Efecto de visualización | 0-3 |
| `itemNum` | Integer | Número de item | 1-10 |

## Colores Disponibles

1. **Rojo** (1)
2. **Verde** (2)
3. **Amarillo** (3)
4. **Azul** (4)
5. **Púrpura** (5)
6. **Azul oscuro** (6)
7. **Blanco** (7)

## Compilación y Ejecución

### Prerrequisitos
- Java 11 o superior
- Maven 3.6 o superior
- Librería `protocol-1.2.6.jar` en `../../panel_java/`

### Compilar
```bash
mvn clean compile
```

### Ejecutar
```bash
mvn spring-boot:run
```

### Crear JAR
```bash
mvn clean package
```

### Ejecutar JAR
```bash
java -jar target/java-panel-service-1.0.0.jar
```

## Logging

El servicio incluye logging detallado con diferentes niveles:

- **INFO**: Operaciones principales
- **DEBUG**: Detalles de comunicación
- **ERROR**: Errores y excepciones

## Ejemplo de Uso

```java
// Crear mensaje
PanelMessage message = PanelMessage.builder()
    .panelIP("172.20.4.52")
    .message("PANEL 3")
    .color(1)        // Rojo
    .fontSize(2)     // Tamaño 2
    .effect(0)       // Sin efecto
    .itemNum(1)      // Item 1
    .build();

// Enviar mensaje
boolean success = panelService.sendMessage(message);
```

## Notas de Implementación

- El servicio mantiene una cache de instancias `ExtSendUtil` por panel
- Cada panel se inicializa automáticamente en la primera comunicación
- Los listeners se configuran automáticamente para cada panel
- El servicio es thread-safe usando `ConcurrentHashMap`

## Troubleshooting

### Error de librería no encontrada
Verificar que `protocol-1.2.6.jar` esté en la ruta correcta:
```
../../panel_java/protocol-1.2.6.jar
```

### Error de conexión
- Verificar que el panel esté encendido y en red
- Verificar la IP y puerto configurados
- Revisar logs para detalles del error

### Error de compilación
- Verificar versión de Java (requiere Java 11+)
- Verificar que Maven esté instalado correctamente
- Limpiar y recompilar: `mvn clean compile` 