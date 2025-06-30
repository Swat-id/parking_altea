# Despliegue del Servicio Java de Paneles

## Descripción

El servicio Java de paneles es una aplicación Spring Boot que proporciona una API REST para comunicarse con los paneles LED de los aparcamientos de Altea. Utiliza la librería Java del fabricante para enviar mensajes y información de ocupación a los paneles.

## Requisitos Previos

- Ubuntu 20.04 o superior
- Java 11 o superior
- Maven 3.6 o superior
- Git
- Acceso root al servidor

## Instalación Inicial

### 1. Clonar el repositorio

```bash
cd /opt
git clone https://github.com/Swat-id/parking_altea.git
cd parking_altea
git checkout java-panel-service
```

### 2. Verificar archivos necesarios

```bash
# Verificar que existe el archivo JAR del fabricante
ls -la panel_java/protocol-1.2.6.jar

# Verificar que existe el directorio del servicio Java
ls -la server/java-panel-service/
```

### 3. Ejecutar script de instalación

```bash
# Hacer el script ejecutable
chmod +x deploy/setup_java_panel_service.sh

# Ejecutar instalación
./deploy/setup_java_panel_service.sh
```

El script realizará automáticamente:
- Crear directorio de instalación `/opt/java-panel-service`
- Instalar archivo de servicio systemd
- Compilar el proyecto Java
- Copiar el JAR generado
- Configurar permisos
- Iniciar y habilitar el servicio

## Actualización del Servicio

### Actualización Automática

Para actualizar el servicio con los últimos cambios:

```bash
# Hacer el script ejecutable
chmod +x deploy/update_java_panel_service.sh

# Ejecutar actualización
./deploy/update_java_panel_service.sh
```

El script realizará automáticamente:
- Actualizar código desde GitHub
- Verificar archivo JAR del fabricante
- Compilar el proyecto
- Ejecutar tests
- Crear nuevo package
- Detener servicio actual
- Copiar nuevo JAR
- Reiniciar servicio
- Verificar estado

### Actualización Manual

Si prefieres actualizar manualmente:

```bash
# 1. Actualizar código
cd /opt/parking_altea
git pull origin java-panel-service

# 2. Compilar
cd server/java-panel-service
mvn clean package -DskipTests

# 3. Detener servicio
systemctl stop java-panel-service

# 4. Copiar nuevo JAR
cp target/java-panel-service-1.0.0.jar /opt/java-panel-service/

# 5. Reiniciar servicio
systemctl start java-panel-service

# 6. Verificar estado
systemctl status java-panel-service
```

## Configuración

### Archivo de Configuración

El servicio utiliza `application.yml` para su configuración:

```yaml
server:
  port: 5002
  servlet:
    context-path: /api

panel:
  service:
    library:
      jar-path: "/opt/parking_altea/panel_java/protocol-1.2.6.jar"
      timeout: 3000
      retry-attempts: 3
      retry-delay: 1000
    default:
      port: 5200
      card-id: 1
      window-no: 0
```

### Paneles Configurados

El servicio incluye la configuración de todos los paneles de Altea:

| IP | Nombre | Parking |
|----|--------|---------|
| 172.20.17.50 | PANEL C. ESPORTIVA | P. Ciutat Esportiva |
| 172.20.5.50 | PANEL BASSETA 1 | P. Basseta Centre |
| 172.20.5.51 | PANEL BASSETA 2 | P. Basseta Centre |
| 172.20.8.50 | PANEL PITERES | P. Poble antic/Conservatori |
| 172.20.4.50 | PANEL PALAU | P. Poble antic/Palau Altea |
| 172.20.4.51 | PANEL COCOLISO | P. Poble antic/Palau Altea |
| 172.20.4.52 | BELLES ARTS 2 | P. Poble antic/Belles Arts 2 |
| 172.20.4.53 | BELLES ARTS | P. Poble antic/Belles Arts 1 |
| 172.20.2.50 | PANEL RENFE | P. Estació Altea |
| 172.20.1.50 | PANEL ALTEA VELLA | P. Altea la Vella |

## Gestión del Servicio

### Comandos Básicos

```bash
# Ver estado del servicio
systemctl status java-panel-service

# Iniciar servicio
systemctl start java-panel-service

# Detener servicio
systemctl stop java-panel-service

# Reiniciar servicio
systemctl restart java-panel-service

# Habilitar inicio automático
systemctl enable java-panel-service

# Deshabilitar inicio automático
systemctl disable java-panel-service
```

### Logs

```bash
# Ver logs en tiempo real
journalctl -u java-panel-service -f

# Ver logs recientes
journalctl -u java-panel-service --no-pager -n 50

# Ver logs de hoy
journalctl -u java-panel-service --since today

# Ver logs con errores
journalctl -u java-panel-service -p err
```

## API REST

El servicio expone una API REST en el puerto 5002:

### Endpoints Disponibles

- `GET /api/health` - Estado del servicio
- `POST /api/panel/send` - Enviar mensaje a panel
- `POST /api/panel/occupancy` - Enviar ocupación a panel
- `GET /api/panel/test/{ip}` - Probar conectividad con panel
- `GET /api/panel/status/{ip}` - Obtener estado de panel

### Ejemplo de Uso

```bash
# Enviar mensaje a panel
curl -X POST http://localhost:5002/api/panel/send \
  -H "Content-Type: application/json" \
  -d '{
    "panelIP": "172.20.17.50",
    "message": "Test Message",
    "color": 65280,
    "fontSize": 16,
    "speed": 3
  }'

# Enviar ocupación
curl -X POST http://localhost:5002/api/panel/occupancy \
  -H "Content-Type: application/json" \
  -d '{
    "panelIP": "172.20.17.50",
    "current": 45,
    "total": 500,
    "status": "LLIURE",
    "parkingName": "P. Ciutat Esportiva"
  }'

# Probar panel
curl http://localhost:5002/api/panel/test/172.20.17.50
```

## Monitoreo

### Health Check

```bash
# Verificar estado del servicio
curl http://localhost:5002/api/health

# Verificar métricas
curl http://localhost:5002/actuator/health
```

### Métricas

El servicio expone métricas en `/actuator/metrics` para monitoreo con Prometheus.

## Troubleshooting

### Problemas Comunes

1. **Servicio no inicia**
   ```bash
   # Verificar logs
   journalctl -u java-panel-service --no-pager -n 20
   
   # Verificar archivo JAR
   ls -la /opt/java-panel-service/
   
   # Verificar permisos
   ls -la /opt/parking_altea/panel_java/
   ```

2. **Error de conectividad con paneles**
   ```bash
   # Verificar conectividad de red
   ping 172.20.17.50
   
   # Verificar puerto
   telnet 172.20.17.50 5200
   ```

3. **Error de librería JAR**
   ```bash
   # Verificar que existe el archivo
   ls -la /opt/parking_altea/panel_java/protocol-1.2.6.jar
   
   # Verificar permisos
   chmod 644 /opt/parking_altea/panel_java/protocol-1.2.6.jar
   ```

### Logs de Debug

Para habilitar logs detallados, editar `application.yml`:

```yaml
logging:
  level:
    com.parkingaltea.panelservice: DEBUG
```

## Desarrollo

### Compilación Local

```bash
cd server/java-panel-service
mvn clean compile
mvn test
mvn package
```

### Ejecución Local

```bash
java -jar target/java-panel-service-1.0.0.jar
```

### Tests

```bash
# Ejecutar todos los tests
mvn test

# Ejecutar tests específicos
mvn test -Dtest=PanelCommunicationServiceTest

# Ejecutar tests sin compilar
mvn test -DskipTests=false
```

## Seguridad

- El servicio se ejecuta como root para acceder a la librería del fabricante
- Se recomienda configurar firewall para limitar acceso al puerto 5002
- Los logs contienen información sensible, proteger acceso a `/var/log/`

## Backup

### Archivos Importantes

```bash
# Configuración del servicio
/etc/systemd/system/java-panel-service.service

# JAR del servicio
/opt/java-panel-service/java-panel-service-1.0.0.jar

# JAR del fabricante
/opt/parking_altea/panel_java/protocol-1.2.6.jar

# Logs
/var/log/journal/
``` 