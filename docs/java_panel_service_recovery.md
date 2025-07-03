# Recuperación del Servicio Java de Paneles v2.5

## 📋 Resumen

Este documento describe la recuperación del servicio Java de paneles que estaba funcionando correctamente con la librería del fabricante (protocol-1.2.6.jar).

## 🎯 Objetivo

Recuperar la funcionalidad completa del servicio Java que:
- Usa la librería oficial del fabricante
- Implementa el flujo correcto de comunicación
- Funciona con todos los paneles de protocolo "old"
- Proporciona API REST completa

## 🔧 Problemas Identificados

### 1. Servicio Actual No Funcional
- El servicio actual en `server/panel-service-v2/` es un servicio Node.js, no Java
- No usa la librería del fabricante
- No implementa el protocolo correcto

### 2. Configuración Incorrecta
- Los paneles están configurados con protocolo "old" pero no hay servicio Java funcional
- El backend intenta enviar mensajes a un servicio que no existe o no funciona

### 3. Librería No Integrada
- La librería `protocol.jar` existe pero no está siendo usada correctamente
- No hay implementación Java que use la librería del fabricante

## 🚀 Solución Implementada

### 1. Recreación del Servicio Java

Se ha recreado el servicio Java completo en `server/java-panel-service/` con:

#### Estructura del Proyecto
```
server/java-panel-service/
├── pom.xml                              # Configuración Maven
├── src/main/java/com/parkingaltea/panelservice/
│   ├── PanelServiceApplication.java     # Clase principal Spring Boot
│   ├── controller/
│   │   └── PanelController.java         # Controlador REST
│   ├── service/
│   │   └── PanelCommunicationService.java # Servicio de comunicación
│   └── model/
│       ├── PanelMessage.java            # Modelo de mensaje
│       ├── PanelOccupancy.java          # Modelo de ocupación
│       └── PanelResponse.java           # Modelo de respuesta
├── src/main/resources/
│   └── application.yml                  # Configuración
└── lib/
    └── protocol-1.2.6.jar              # Librería del fabricante
```

#### Características del Servicio

1. **Spring Boot 2.7.0** con Java 11
2. **API REST completa** con endpoints:
   - `GET /api/health` - Health check
   - `GET /api/panels/status` - Estado de paneles
   - `GET /api/panels/list` - Lista de paneles
   - `POST /api/panels/test` - Test de conectividad
   - `POST /api/panels/send` - Envío individual
   - `POST /sendMulti` - Envío múltiple (compatibilidad)
   - `POST /api/panels/occupancy` - Mensaje de ocupación

3. **Integración con librería del fabricante**:
   - Usa `protocol-1.2.6.jar`
   - Implementa flujo: initNetwork → setListener → sendMulti
   - Manejo correcto de errores y reintentos

4. **Configuración flexible**:
   - Puerto 5656 (como estaba funcionando)
   - Timeout y reintentos configurables
   - Lista de paneles en `application.yml`

### 2. Scripts de Despliegue

#### Compilación
```bash
./deploy/build_java_panel_service.sh
```

#### Despliegue como Servicio
```bash
sudo ./deploy/deploy_java_panel_service.sh
```

#### Pruebas
```bash
python3 test/test_java_panel_service_v2.5.py
```

### 3. Configuración de Paneles

Todos los paneles están configurados con:
- **Protocolo**: "old"
- **Servicio**: Java (puerto 5656)
- **Librería**: protocol-1.2.6.jar
- **Configuración**: Según `application.yml`

## 🔄 Flujo de Comunicación

### 1. Inicialización
```
1. Cargar librería del fabricante
2. initNetwork() - Inicializar conexión de red
3. setListener() - Configurar listener
4. Servicio listo para recibir mensajes
```

### 2. Envío de Mensaje
```
1. Backend detecta cambio de ocupación
2. Envía mensaje a /sendMulti (puerto 5656)
3. Servicio Java recibe mensaje
4. Usa librería para enviar a panel
5. Retorna respuesta de éxito/error
```

### 3. Formato de Mensaje
```json
{
  "ip": "172.20.4.52",
  "itemNum": 1,
  "texts": ["4 - P. Poble antic/Belles Arts 2: 25 libres (LIBRE)"],
  "colors": [1],
  "fontSizes": [16],
  "showEffects": [0]
}
```

## 📊 Paneles Soportados

| Panel | IP | Nombre | Parking | Protocolo |
|-------|----|--------|---------|-----------|
| PANEL BASSETA 1 | 172.20.5.50 | P. Basseta Centre | 2 | old |
| PANEL BASSETA 2 | 172.20.5.51 | P. Basseta Centre | 2 | old |
| PANEL PALAU | 172.20.4.50 | P. Poble antic/Palau Altea | 5 | old |
| PANEL COCOLISO | 172.20.4.51 | P. Poble antic/Palau Altea | 5 | old |
| BELLES ARTS 2 | 172.20.4.52 | P. Poble antic/Belles Arts 2 | 4 | old |
| BELLES ARTS | 172.20.4.53 | P. Poble antic/Belles Arts 1 | 3 | old |
| PANEL C. ESPORTIVA | 172.20.17.50 | P. Ciutat Esportiva | 1 | old |
| PANEL PITERES | 172.20.8.50 | P. Poble antic/Conservatori | 6 | old |
| PANEL RENFE | 172.20.2.50 | P. Estació Altea | 8 | old |
| PANEL ALTEA VELLA | 172.20.1.50 | P. Altea la Vella | 9 | old |

## 🧪 Pruebas

### Pruebas Automáticas
```bash
python3 test/test_java_panel_service_v2.5.py
```

### Pruebas Manuales
```bash
# Health check
curl http://localhost:5656/api/health

# Estado de paneles
curl http://localhost:5656/api/panels/status

# Envío de mensaje
curl -X POST http://localhost:5656/sendMulti \
  -H "Content-Type: application/json" \
  -d '{"ip":"172.20.4.52","itemNum":1,"texts":["TEST"],"colors":[1],"fontSizes":[16],"showEffects":[0]}'
```

## 🔧 Gestión del Servicio

### Comandos Systemd
```bash
# Estado
systemctl status java-panel-service

# Logs
journalctl -u java-panel-service -f

# Reiniciar
systemctl restart java-panel-service

# Detener
systemctl stop java-panel-service
```

### Logs
- **Ubicación**: `/var/log/parking_altea/`
- **Journal**: `journalctl -u java-panel-service`
- **Nivel**: INFO (configurable en `application.yml`)

## 🚨 Troubleshooting

### Problemas Comunes

1. **Servicio no inicia**:
   - Verificar Java 11+ instalado
   - Verificar librería en `/lib/protocol-1.2.6.jar`
   - Revisar logs: `journalctl -u java-panel-service -n 50`

2. **Error de conectividad**:
   - Verificar IPs de paneles
   - Verificar conectividad de red
   - Revisar configuración de firewall

3. **Error de librería**:
   - Verificar que `protocol-1.2.6.jar` existe
   - Verificar permisos del archivo
   - Recompilar proyecto

### Logs de Debug
```yaml
logging:
  level:
    com.parkingaltea.panelservice: DEBUG
    org.springframework.web: DEBUG
```

## ✅ Verificación de Funcionamiento

### 1. Servicio Activo
```bash
systemctl is-active java-panel-service
# Debe retornar: active
```

### 2. API Respondiendo
```bash
curl http://localhost:5656/api/health
# Debe retornar JSON con status: "UP"
```

### 3. Panel Responde
```bash
curl -X POST http://localhost:5656/sendMulti \
  -H "Content-Type: application/json" \
  -d '{"ip":"172.20.4.52","itemNum":1,"texts":["TEST"],"colors":[1],"fontSizes":[16],"showEffects":[0]}'
# Debe retornar: {"success": true, ...}
```

### 4. Panel Visual Actualiza
- El panel 172.20.4.52 debe mostrar el mensaje "TEST" en rojo
- El mensaje debe permanecer visible por 5 segundos

## 📈 Próximos Pasos

1. **Desplegar el servicio** en el servidor de producción
2. **Verificar funcionamiento** con todos los paneles
3. **Monitorear logs** para detectar problemas
4. **Actualizar documentación** con experiencias reales
5. **Optimizar configuración** según necesidades

## 🔗 Referencias

- [Documentación original v2.5](docs/java_panel_service_v2.5.md)
- [Protocolo CP5200](docs/cp5200_protocol.md)
- [Configuración de paneles](docs/panels.md)
- [API Endpoints](docs/api_endpoints.md) 