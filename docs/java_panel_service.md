# Servicio Java de Comunicación con Paneles LED

## 📋 Resumen Ejecutivo

Este documento describe la implementación del servicio Java de comunicación con paneles LED para el sistema de Parking Altea. El servicio utiliza la librería Java del fabricante Rotuloselectronicos.net (`protocol-1.2.6.jar`) para comunicarse con los paneles electrónicos LED.

## 🏗️ Arquitectura

### Componentes del Sistema

```
Frontend React (5789) → Backend Python (6001) → Servicio Java (5002) → Librería Java → Panel LED (5200)
```

### Tecnologías Utilizadas

- **Spring Boot 2.7.18**: Framework de aplicación Java
- **Java 11**: Lenguaje de programación
- **Maven**: Gestión de dependencias
- **Librería Java del fabricante**: `protocol-1.2.6.jar`
- **Lombok**: Reducción de boilerplate
- **JUnit 5**: Pruebas unitarias

### Estructura del Proyecto

```
server/java-panel-service/
├── src/
│   ├── main/
│   │   ├── java/com/parkingaltea/panelservice/
│   │   │   ├── PanelServiceApplication.java          # Clase principal
│   │   │   ├── config/
│   │   │   │   └── PanelServiceConfig.java          # Configuración
│   │   │   ├── controller/
│   │   │   │   └── PanelController.java             # Controlador REST
│   │   │   ├── model/
│   │   │   │   ├── PanelMessage.java                # Modelo de mensaje
│   │   │   │   ├── PanelOccupancy.java              # Modelo de ocupación
│   │   │   │   └── PanelResponse.java               # Modelo de respuesta
│   │   │   └── service/
│   │   │       └── PanelCommunicationService.java   # Servicio principal
│   │   └── resources/
│   │       └── application.yml                      # Configuración
│   └── test/
│       └── java/com/parkingaltea/panelservice/
│           ├── PanelServiceApplicationTests.java
│           └── service/
│               └── PanelCommunicationServiceTest.java
├── pom.xml                                          # Configuración Maven
└── README.md                                        # Documentación
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Java 11** o superior
- **Maven 3.6** o superior
- **Librería Java del fabricante**: `panel_java/protocol-1.2.6.jar`

### Compilación y Despliegue

```bash
# Navegar al directorio del proyecto
cd server/java-panel-service

# Compilar proyecto
mvn clean compile

# Ejecutar tests
mvn test

# Empaquetar aplicación
mvn package

# Ejecutar en desarrollo
mvn spring-boot:run

# Ejecutar JAR compilado
java -jar target/java-panel-service-1.0.0.jar
```

### Script de Despliegue Automatizado

```bash
# Usar script de despliegue
./deploy/build_java_panel_service.sh deploy

# Comandos disponibles
./deploy/build_java_panel_service.sh clean      # Limpiar
./deploy/build_java_panel_service.sh compile    # Compilar
./deploy/build_java_panel_service.sh test       # Ejecutar tests
./deploy/build_java_panel_service.sh package    # Empaquetar
./deploy/build_java_panel_service.sh deploy     # Desplegar completo
./deploy/build_java_panel_service.sh info       # Mostrar información
```

## 📡 API Endpoints

### Base URL
```
http://localhost:5002/api
```

### Endpoints Disponibles

#### 1. Health Check
```http
GET /panel/health
```

**Respuesta:**
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

#### 2. Enviar Mensaje a Panel
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

**Respuesta:**
```json
{
  "success": true,
  "message": "Mensaje enviado correctamente al panel 172.20.5.50",
  "responseTime": 75.45,
  "timestamp": "2025-01-27T10:12:58.674"
}
```

#### 3. Enviar Información de Ocupación
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

#### 4. Broadcast a Todos los Paneles
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

**Respuesta:**
```json
{
  "success": true,
  "message": "Broadcast completado: 8/10 paneles actualizados",
  "data": {
    "responseTime": 1250.75,
    "successCount": 8,
    "totalCount": 10,
    "successRate": 80.0
  }
}
```

#### 5. Probar Conectividad de Panel
```http
POST /panel/test/{panelIP}
```

#### 6. Obtener Estado de Paneles
```http
GET /panel/status
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Estado de paneles obtenido correctamente",
  "data": {
    "initializedPanels": {
      "172.20.5.50": true,
      "172.20.5.51": true,
      "172.20.8.50": false
    },
    "totalPanels": 3,
    "onlinePanels": 2
  }
}
```

#### 7. Obtener Colores Disponibles
```http
GET /panel/colors
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Colores disponibles obtenidos correctamente",
  "data": {
    "red": 255,
    "green": 65280,
    "blue": 16711680,
    "yellow": 65535,
    "orange": 33023,
    "white": 16777215,
    "default": 3000
  }
}
```

#### 8. Limpiar Cache de Paneles
```http
POST /panel/clear-cache
```

## 🎨 Configuración de Colores

### Colores Disponibles
| Color | Valor Hex | Valor Decimal | Descripción |
|-------|-----------|---------------|-------------|
| Rojo | `0x0000FF` | 255 | Estado COMPLET |
| Verde | `0x00FF00` | 65280 | Estado LLIURE |
| Azul | `0xFF0000` | 16711680 | Color azul |
| Amarillo | `0x00FFFF` | 65535 | Mensajes de advertencia |
| Naranja | `0x0080FF` | 33023 | Estado DENS |
| Blanco | `0xFFFFFF` | 16777215 | Color blanco |
| Por defecto | - | 3000 | Color del fabricante |

### Estados de Ocupación por Color
- **LLIURE**: Verde (`0x00FF00`)
- **DENS**: Naranja (`0x0080FF`)
- **COMPLET**: Rojo (`0x0000FF`)

## 🔧 Configuración de Paneles

### Paneles Configurados
| IP | Nombre | Parking | Estado |
|----|--------|---------|--------|
| 172.20.17.50 | Panel 1 | P. Ciutat Esportiva | ONLINE |
| 172.20.5.50 | Panel 2 | P. Poble antic 1 | ONLINE |
| 172.20.5.51 | Panel 3 | P. Poble antic 2 | ONLINE |
| 172.20.8.50 | Panel 4 | P. Piteres | ONLINE |
| 172.20.4.50 | Panel 5 | P. Palau | ONLINE |
| 172.20.4.51 | Panel 6 | P. Cocoliso | ONLINE |
| 172.20.4.52 | Panel 7 | Belles Arts 2 | ONLINE |
| 172.20.4.53 | Panel 8 | Belles Arts | ONLINE |
| 172.20.2.50 | Panel 9 | P. Renfe | ONLINE |
| 172.20.1.50 | Panel 10 | P. Altea Vella | ONLINE |

### Configuración por Defecto
```yaml
panel:
  service:
    default:
      port: 5200
      card-id: 1
      window-no: 0
      font-size: 16
      speed: 3
      effect: 0
      stay-time: 5
      alignment: 5
      screen-width: 64
      screen-height: 32
```

## 🔄 Flujo de Comunicación

### 1. Inicialización del Servicio
```
1. Cargar librería Java del fabricante
2. Verificar existencia del archivo JAR
3. Configurar pool de conexiones
4. Inicializar cache de paneles
```

### 2. Envío de Mensaje
```
1. Validar parámetros de entrada
2. Verificar conectividad con panel
3. Inicializar panel si es necesario
4. Enviar mensaje con reintentos
5. Registrar resultado y tiempo de respuesta
```

### 3. Gestión de Errores
```
1. Timeout de conexión (configurable)
2. Reintentos automáticos (3 intentos por defecto)
3. Logging detallado de errores
4. Respuestas estructuradas con códigos de error
```

## 📊 Monitoreo y Logs

### Configuración de Logging
```yaml
logging:
  level:
    com.parkingaltea.panelservice: DEBUG
    org.springframework.web: INFO
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
    file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: logs/panel-service.log
    max-size: 10MB
    max-history: 30
```

### Métricas Disponibles
- **Tiempo de respuesta**: Por operación y promedio
- **Tasa de éxito**: Porcentaje de envíos exitosos
- **Paneles online**: Número de paneles conectados
- **Errores por tipo**: Clasificación de errores

### Health Check
```bash
# Verificar estado del servicio
curl http://localhost:5002/api/panel/health

# Ver logs en tiempo real
tail -f logs/panel-service.log

# Ver últimas 100 líneas
tail -n 100 logs/panel-service.log
```

## 🧪 Pruebas

### Pruebas Unitarias
```bash
# Ejecutar todas las pruebas
mvn test

# Ejecutar pruebas específicas
mvn test -Dtest=PanelCommunicationServiceTest
```

### Pruebas de Integración
```bash
# Usar script de pruebas
python test/test_java_panel_service.py

# Comandos disponibles
python test/test_java_panel_service.py health     # Health check
python test/test_java_panel_service.py colors     # Obtener colores
python test/test_java_panel_service.py status     # Estado de paneles
python test/test_java_panel_service.py test 172.20.5.50  # Probar panel
python test/test_java_panel_service.py send 172.20.5.50  # Enviar mensaje
python test/test_java_panel_service.py occupancy 172.20.5.50  # Enviar ocupación
python test/test_java_panel_service.py broadcast  # Broadcast
python test/test_java_panel_service.py clear      # Limpiar cache
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
# Ejecutar en modo desarrollo
mvn spring-boot:run

# Con configuración específica
mvn spring-boot:run -Dspring.profiles.active=development
```

### Producción
```bash
# Compilar para producción
mvn clean package -DskipTests

# Ejecutar con configuración de producción
java -jar target/java-panel-service-1.0.0.jar \
  --spring.profiles.active=production

# Con configuración JVM optimizada
java -Xms512m -Xmx1024m -XX:+UseG1GC \
  -jar target/java-panel-service-1.0.0.jar \
  --spring.profiles.active=production
```

### Scripts de Gestión
```bash
# Iniciar servicio
./start_java_panel_service.sh

# Detener servicio
./stop_java_panel_service.sh

# Verificar estado
ps aux | grep java-panel-service
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

#### 4. Error de compilación
```
Error: Java version incompatible
Solución: Usar Java 11 o superior
```

### Logs de Debug
```yaml
logging:
  level:
    com.parkingaltea.panelservice: DEBUG
```

### Verificación de Conectividad
```bash
# Ping a paneles
ping 172.20.5.50

# Verificar puerto
nc -zv 172.20.5.50 5200

# Verificar logs del servicio
tail -f logs/panel-service.log
```

## 📝 Notas de Desarrollo

### Integración con Librería Java
- La librería se carga dinámicamente al inicio
- Se mantiene cache de paneles inicializados
- Reintentos automáticos en caso de fallo
- Gestión de memoria optimizada

### Optimizaciones Implementadas
- **Pool de conexiones**: Para operaciones asíncronas
- **Cache de inicialización**: Evita reinicializar paneles
- **Logging estructurado**: Para debugging eficiente
- **Validación de entrada**: En todos los endpoints

### Seguridad
- **Validación de entrada**: En todos los endpoints
- **Sanitización de parámetros**: Prevención de inyección
- **Logging de operaciones**: Auditoría de acciones
- **Timeouts configurables**: Prevención de DoS

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

### Mejoras de Protocolo
1. **Comandos Avanzados**: Configuración de colores RGB
2. **Control de Brillo**: Ajuste dinámico
3. **Configuración de Fuente**: Tipografías personalizadas
4. **Gestión de Programas**: Programación temporal

## 📞 Soporte Técnico

### Información de Contacto
- **Desarrollador**: Parking Altea Team
- **Servidor**: 157.180.91.63 (Helsinki, Finlandia)
- **Documentación**: `/docs/java_panel_service.md`

### Comandos de Gestión
```bash
# Reiniciar servicio
./stop_java_panel_service.sh && ./start_java_panel_service.sh

# Verificar estado
curl http://localhost:5002/api/panel/health

# Ver logs en tiempo real
tail -f logs/panel-service.log

# Recompilar servicio
./deploy/build_java_panel_service.sh deploy
```

---

**Versión**: 1.0.0  
**Autor**: Parking Altea Team  
**Fecha**: Enero 2025  
**Estado**: ✅ Activo - En desarrollo 