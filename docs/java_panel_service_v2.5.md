# Java Panel Service v2.5

## Descripción

El Java Panel Service v2.5 es un servicio Spring Boot que proporciona una API REST para la comunicación con paneles LED. Este servicio reemplaza la implementación anterior y utiliza la librería Java oficial del fabricante para una integración más robusta y confiable.

## Características

- **API REST completa** para comunicación con paneles LED
- **Integración con librería oficial** del fabricante (protocol-1.2.6.jar)
- **Flujo de comunicación correcto** según el manual del fabricante
- **Envío individual y multi-panel** de mensajes
- **Pruebas de conectividad** automáticas
- **Logging detallado** para debugging
- **Configuración flexible** via application.yml
- **Servicio systemd** para gestión automática

## Arquitectura

### Estructura del Proyecto

```
server/java-panel-service/
├── src/main/java/com/parkingaltea/panelservice/
│   ├── PanelServiceApplication.java      # Clase principal Spring Boot
│   ├── controller/
│   │   └── PanelController.java         # Controlador REST
│   ├── service/
│   │   └── PanelService.java            # Lógica de negocio
│   └── model/
│       ├── PanelMessage.java            # Modelo de mensaje
│       └── PanelResponse.java           # Modelo de respuesta
├── src/main/resources/
│   └── application.yml                  # Configuración
├── pom.xml                              # Dependencias Maven
└── README.md                            # Documentación
```

### Componentes Principales

1. **PanelServiceApplication**: Punto de entrada de la aplicación Spring Boot
2. **PanelController**: Controlador REST que expone los endpoints de la API
3. **PanelService**: Servicio que maneja la lógica de comunicación con los paneles
4. **Modelos**: Clases para representar mensajes y respuestas

## API Endpoints

### Health Check
```
GET /api/health
```
Verifica el estado del servicio.

### Estado de Paneles
```
GET /api/panels/status
```
Obtiene el estado de todos los paneles configurados.

### Lista de Paneles
```
GET /api/panels/list
```
Obtiene la lista de paneles disponibles.

### Test de Conectividad
```
POST /api/panels/test
Content-Type: application/json

{
  "ip": "172.20.5.50"
}
```
Prueba la conectividad con un panel específico.

### Envío de Mensaje Individual
```
POST /api/panels/send
Content-Type: application/json

{
  "ip": "172.20.5.50",
  "message": "Mensaje de prueba",
  "color": 1,
  "fontSize": 2,
  "windowNo": 0
}
```
Envía un mensaje a un panel específico.

### Envío Multi-Panel
```
POST /api/panels/send-multi
Content-Type: application/json

{
  "ips": ["172.20.5.50", "172.20.5.51"],
  "message": "Mensaje multi-panel",
  "color": 2,
  "fontSize": 2,
  "windowNo": 0
}
```
Envía un mensaje a múltiples paneles simultáneamente.

## Configuración

### application.yml

```yaml
server:
  port: 5002
  servlet:
    context-path: /api

spring:
  application:
    name: java-panel-service

logging:
  level:
    com.parkingaltea.panelservice: DEBUG
    org.springframework.web: INFO

panel:
  service:
    library:
      jar-path: /opt/parking_altea/panel_java/protocol-1.2.6.jar
      timeout: 5000
      retry-attempts: 3
      retry-delay: 1000
    default:
      port: 5200
      card-id: 1
      window-no: 0
    panels:
      - ip: "172.20.5.50"
        name: "PANEL BASSETA 1"
        description: "P. Basseta Centre"
      # ... más paneles
```

### Parámetros de Configuración

- **server.port**: Puerto del servicio (5002)
- **panel.service.library.jar-path**: Ruta a la librería del fabricante
- **panel.service.library.timeout**: Timeout para operaciones (ms)
- **panel.service.library.retry-attempts**: Número de reintentos
- **panel.service.library.retry-delay**: Delay entre reintentos (ms)

## Instalación y Despliegue

### Requisitos Previos

- Java 11 o superior
- Maven 3.6 o superior
- Acceso root al servidor
- Librería del fabricante (protocol-1.2.6.jar)

### Instalación Local

1. **Compilar el proyecto**:
```bash
cd /opt/parking_altea/server/java-panel-service
mvn clean package -DskipTests
```

2. **Ejecutar el servicio**:
```bash
java -jar target/java-panel-service-1.0.0.jar
```

### Despliegue en Producción

1. **Usar el script de despliegue**:
```bash
sudo ./deploy/deploy_java_panel_service_v2.5.sh
```

2. **Verificar el servicio**:
```bash
systemctl status java-panel-service
journalctl -u java-panel-service -f
```

### Actualización

1. **Actualización local**:
```bash
sudo ./deploy/update_java_panel_service_v2.5.sh
```

2. **Actualización remota**:
```bash
./deploy/update_java_panel_service_remote_v2.5.sh
```

## Gestión del Servicio

### Comandos Útiles

```bash
# Ver estado del servicio
systemctl status java-panel-service

# Ver logs en tiempo real
journalctl -u java-panel-service -f

# Reiniciar el servicio
systemctl restart java-panel-service

# Detener el servicio
systemctl stop java-panel-service

# Habilitar inicio automático
systemctl enable java-panel-service
```

### Logs

Los logs se almacenan en el journal de systemd:
```bash
# Ver logs recientes
journalctl -u java-panel-service --no-pager -n 50

# Ver logs de hoy
journalctl -u java-panel-service --since today

# Ver logs con timestamps
journalctl -u java-panel-service -o short-iso
```

## Pruebas

### Script de Pruebas Automáticas

```bash
# Ejecutar pruebas comprehensivas
python3 test/test_java_panel_service_v2.5.py
```

### Pruebas Manuales

1. **Health Check**:
```bash
curl http://localhost:5002/api/health
```

2. **Estado de Paneles**:
```bash
curl http://localhost:5002/api/panels/status
```

3. **Envío de Mensaje**:
```bash
curl -X POST http://localhost:5002/api/panels/send \
  -H "Content-Type: application/json" \
  -d '{"ip":"172.20.5.50","message":"TEST","color":1,"fontSize":2,"windowNo":0}'
```

## Troubleshooting

### Problemas Comunes

1. **Servicio no inicia**:
   - Verificar que Java 11+ está instalado
   - Verificar que la librería del fabricante existe
   - Revisar logs: `journalctl -u java-panel-service -n 50`

2. **Error de conectividad con paneles**:
   - Verificar que las IPs están correctas
   - Verificar conectividad de red
   - Revisar configuración de firewall

3. **Error de compilación**:
   - Verificar que Maven está instalado
   - Verificar que la librería del fabricante está en la ruta correcta
   - Limpiar y recompilar: `mvn clean package`

### Logs de Debug

Para habilitar logs detallados, modificar `application.yml`:
```yaml
logging:
  level:
    com.parkingaltea.panelservice: DEBUG
    org.springframework.web: DEBUG
```

## Diferencias con Versiones Anteriores

### v2.5 vs v2.4

- **Librería oficial**: Uso de la librería Java del fabricante en lugar de implementación propia
- **Flujo correcto**: Implementación del flujo initNetwork -> setListener -> sendMulti
- **Mejor manejo de errores**: Respuestas más detalladas y logging mejorado
- **Configuración simplificada**: Menos archivos de configuración
- **Servicio systemd**: Gestión automática del servicio

### Mejoras de Rendimiento

- **Comunicación más eficiente** con los paneles
- **Reintentos automáticos** en caso de fallo
- **Timeouts configurables** para diferentes operaciones
- **Logging optimizado** para producción

## Seguridad

### Configuraciones de Seguridad

- **Usuario dedicado**: El servicio se ejecuta con usuario `parking`
- **Permisos restringidos**: Acceso limitado al sistema
- **Protección de archivos**: Archivos de configuración con permisos 644
- **Logs seguros**: Sin información sensible en logs

### Recomendaciones

- Mantener el servicio actualizado
- Revisar logs regularmente
- Monitorear el uso de recursos
- Hacer backups de la configuración

## Monitoreo

### Métricas Disponibles

- Estado del servicio (activo/inactivo)
- Número de paneles conectados
- Tiempo de respuesta de operaciones
- Número de errores por operación

### Health Checks

El servicio expone endpoints de health check:
- `/api/health`: Estado general del servicio
- `/api/panels/status`: Estado de los paneles

## Soporte

### Contacto

Para soporte técnico o reportar problemas:
- Revisar logs del servicio
- Ejecutar script de pruebas
- Contactar al equipo de desarrollo

### Documentación Adicional

- [Manual del fabricante](panel_java/API%20Interface%20Manual%20for%20Control%20Card%20Development%201.2.6.pdf)
- [Protocolo de comunicación](docs/cp5200_protocol.md)
- [Guía de despliegue](docs/deployment.md) 