# Servicio Java de Comunicación con Paneles LED

## 📋 Descripción

Este servicio proporciona una API REST para comunicarse con los paneles electrónicos LED del sistema de parking de Altea, utilizando la librería Java del fabricante Rotuloselectronicos.net.

## 🏗️ Arquitectura

### Componentes

- **Spring Boot 2.7.18**: Framework de aplicación
- **Java 11**: Lenguaje de programación
- **Maven**: Gestión de dependencias
- **Librería Java del fabricante**: `protocol-1.2.6.jar`

### Estructura del Proyecto

```
server/java-panel-service/
├── src/
│   ├── main/
│   │   ├── java/com/parkingaltea/panelservice/
│   │   │   ├── PanelServiceApplication.java
│   │   │   ├── config/
│   │   │   │   └── PanelServiceConfig.java
│   │   │   ├── controller/
│   │   │   │   └── PanelController.java
│   │   │   ├── model/
│   │   │   │   ├── PanelMessage.java
│   │   │   │   ├── PanelOccupancy.java
│   │   │   │   └── PanelResponse.java
│   │   │   └── service/
│   │   │       └── PanelCommunicationService.java
│   │   └── resources/
│   │       └── application.yml
│   └── test/
│       └── java/com/parkingaltea/panelservice/
│           ├── PanelServiceApplicationTests.java
│           └── service/
│               └── PanelCommunicationServiceTest.java
├── pom.xml
└── README.md
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Java 11 o superior
- Maven 3.6 o superior
- Librería Java del fabricante: `panel_java/protocol-1.2.6.jar`

### Compilación

```bash
cd server/java-panel-service
mvn clean compile
```

### Ejecución

```bash
# Ejecutar en modo desarrollo
mvn spring-boot:run

# Ejecutar JAR compilado
mvn clean package
java -jar target/java-panel-service-1.0.0.jar
```

### Configuración

El servicio se configura a través del archivo `application.yml`:

```yaml
server:
  port: 5002
  servlet:
    context-path: /api

panel:
  service:
    library:
      jar-path: "../panel_java/protocol-1.2.6.jar"
      timeout: 3000
      retry-attempts: 3
      retry-delay: 1000
```

## 📡 API Endpoints

### Base URL
```
http://localhost:5002/api
```

### Endpoints Disponibles

#### 1. Enviar Mensaje a Panel
```http
POST /panel/send
Content-Type: application/json

{
  "panelIP": "172.20.5.50",
  "message": "PARKING LLIURE",
  "color": 0x00FF00,
  "fontSize": 16,
  "speed": 3,
  "effect": 0,
  "stayTime": 5,
  "alignment": 5
}
```

#### 2. Enviar Información de Ocupación
```http
POST /panel/occupancy
Content-Type: application/json

{
  "panelIP": "172.20.5.50",
  "current": 45,
  "total": 500,
  "status": "LLIURE",
  "parkingName": "P. Ciutat Esportiva",
  "color": 0x00FF00,
  "fontSize": 16,
  "speed": 2,
  "alignment": 5
}
```

#### 3. Broadcast a Todos los Paneles
```http
POST /panel/broadcast
Content-Type: application/json

{
  "message": "MANTENIMENT EN CURS",
  "color": 0xFFFF00,
  "fontSize": 16,
  "speed": 3,
  "alignment": 5
}
```

#### 4. Probar Conectividad de Panel
```http
POST /panel/test/{panelIP}
```

#### 5. Obtener Estado de Paneles
```http
GET /panel/status
```

#### 6. Obtener Colores Disponibles
```http
GET /panel/colors
```

#### 7. Limpiar Cache de Paneles
```http
POST /panel/clear-cache
```

#### 8. Health Check
```http
GET /panel/health
```

## 🎨 Configuración de Colores

### Colores Disponibles
- **Rojo**: `0x0000FF`
- **Verde**: `0x00FF00`
- **Azul**: `0xFF0000`
- **Amarillo**: `0x00FFFF`
- **Naranja**: `0x0080FF`
- **Blanco**: `0xFFFFFF`
- **Por defecto**: `3000`

### Estados de Ocupación por Color
- **LLIURE**: Verde (`0x00FF00`)
- **DENS**: Naranja (`0x0080FF`)
- **COMPLET**: Rojo (`0x0000FF`)

## 🔧 Configuración de Paneles

### Paneles Configurados
| IP | Nombre | Parking |
|----|--------|---------|
| 172.20.17.50 | Panel 1 | P. Ciutat Esportiva |
| 172.20.5.50 | Panel 2 | P. Poble antic 1 |
| 172.20.5.51 | Panel 3 | P. Poble antic 2 |
| 172.20.8.50 | Panel 4 | P. Piteres |
| 172.20.4.50 | Panel 5 | P. Palau |
| 172.20.4.51 | Panel 6 | P. Cocoliso |
| 172.20.4.52 | Panel 7 | Belles Arts 2 |
| 172.20.4.53 | Panel 8 | Belles Arts |
| 172.20.2.50 | Panel 9 | P. Renfe |
| 172.20.1.50 | Panel 10 | P. Altea Vella |

### Configuración por Defecto
- **Puerto**: 5200
- **Card ID**: 1
- **Window No**: 0
- **Font Size**: 16
- **Speed**: 3
- **Effect**: 0
- **Stay Time**: 5
- **Alignment**: 5 (Centro)

## 🔄 Flujo de Comunicación

### 1. Inicialización
```
1. Cargar librería Java del fabricante
2. Verificar conectividad con panel
3. Inicializar panel (una vez por panel)
4. Configurar pantalla dividida
```

### 2. Envío de Mensaje
```
1. Validar parámetros de entrada
2. Verificar conectividad
3. Inicializar panel si es necesario
4. Enviar mensaje con reintentos
5. Registrar resultado
```

### 3. Gestión de Errores
```
1. Timeout de conexión
2. Reintentos automáticos
3. Logging detallado
4. Respuestas estructuradas
```

## 📊 Monitoreo y Logs

### Logs del Servicio
```bash
# Ver logs en tiempo real
tail -f logs/panel-service.log

# Ver últimas 100 líneas
tail -n 100 logs/panel-service.log
```

### Métricas Disponibles
- Tiempo de respuesta por operación
- Tasa de éxito de envío
- Número de paneles online
- Errores por tipo

### Health Check
```http
GET /panel/health
```

Respuesta:
```json
{
  "success": true,
  "message": "Servicio funcionando correctamente",
  "data": {
    "status": "UP",
    "service": "Java Panel Service",
    "version": "1.0.0",
    "timestamp": 1640995200000
  }
}
```

## 🧪 Pruebas

### Ejecutar Pruebas Unitarias
```bash
mvn test
```

### Ejecutar Pruebas de Integración
```bash
mvn verify
```

### Pruebas Manuales

#### 1. Probar Envío de Mensaje
```bash
curl -X POST http://localhost:5002/api/panel/send \
  -H "Content-Type: application/json" \
  -d '{
    "panelIP": "172.20.5.50",
    "message": "TEST MESSAGE",
    "color": 0x00FF00
  }'
```

#### 2. Probar Conectividad
```bash
curl -X POST http://localhost:5002/api/panel/test/172.20.5.50
```

#### 3. Verificar Estado
```bash
curl -X GET http://localhost:5002/api/panel/status
```

## 🚀 Despliegue

### Desarrollo
```bash
mvn spring-boot:run
```

### Producción
```bash
# Compilar
mvn clean package -DskipTests

# Ejecutar
java -jar target/java-panel-service-1.0.0.jar \
  --spring.profiles.active=production
```

### Docker (Opcional)
```dockerfile
FROM openjdk:11-jre-slim
COPY target/java-panel-service-1.0.0.jar app.jar
EXPOSE 5002
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Librería Java no encontrada
```
Error: Archivo JAR no encontrado
Solución: Verificar ruta en application.yml
```

#### 2. Panel no responde
```
Error: Panel no es alcanzable
Solución: Verificar conectividad de red y configuración IP
```

#### 3. Timeout de conexión
```
Error: Timeout al conectar con panel
Solución: Aumentar timeout en configuración
```

### Logs de Debug
```yaml
logging:
  level:
    com.parkingaltea.panelservice: DEBUG
```

## 📝 Notas de Desarrollo

### Integración con Librería Java
- La librería se carga dinámicamente al inicio
- Se mantiene cache de paneles inicializados
- Reintentos automáticos en caso de fallo

### Optimizaciones
- Pool de conexiones para operaciones asíncronas
- Cache de inicialización de paneles
- Logging estructurado para debugging

### Seguridad
- Validación de entrada en todos los endpoints
- Sanitización de parámetros
- Logging de operaciones sensibles

## 🔮 Próximas Mejoras

### Funcionalidades Planificadas
1. **Integración con Base de Datos**: Cargar configuración de paneles desde BD
2. **Métricas Avanzadas**: Prometheus/Grafana
3. **Autenticación**: JWT para endpoints sensibles
4. **WebSocket**: Comunicación en tiempo real
5. **Clustering**: Múltiples instancias del servicio

### Optimizaciones
1. **Pool de Conexiones**: Reutilizar conexiones TCP
2. **Batch Processing**: Enviar múltiples mensajes en una conexión
3. **Compresión**: Comprimir mensajes largos
4. **Queue**: Cola para mensajes pendientes

---

**Versión**: 1.0.0  
**Autor**: Parking Altea Team  
**Fecha**: Enero 2025 