# Servicio de Paneles - Parking Altea

## 📋 Descripción

Este servicio proporciona comunicación con los paneles electrónicos del sistema de parking usando el protocolo CP5200 nativo a través de un servicio .NET que se integra con el backend Python existente.

## 🏗️ Arquitectura

```
┌─────────────────┐    HTTP REST    ┌─────────────────┐    CP5200 DLL    ┌─────────────────┐
│   Backend       │ ──────────────► │   Panel Service │ ──────────────► │   Paneles       │
│   Python        │                 │   C# (.NET)     │                 │   (Hardware)    │
│                 │                 │                 │                 │                 │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
```

## 📁 Estructura del Proyecto

```
parking_altea/
├── PanelService/                    # Servicio C# (.NET)
│   ├── Controllers/                 # Controladores REST
│   ├── Models/                      # Modelos de datos
│   ├── Services/                    # Servicios de comunicación
│   ├── Program.cs                   # Punto de entrada
│   └── PanelService.csproj          # Archivo de proyecto
├── src/
│   ├── panel_service_client.py      # Cliente Python para el servicio
│   ├── panel_service_wrapper.py     # Wrapper de integración
│   └── api_server.py                # Backend Python (modificado)
├── test_panel_service.py            # Test del servicio
├── test_integration.py              # Test de integración
├── integrate_panel_service.py       # Script de integración
├── deploy_panel_service.sh          # Script de despliegue
├── manage_panel_service.sh          # Script de gestión
└── monitor_panel_service.py         # Monitor del servicio
```

## 🚀 Instalación y Despliegue

### 1. Despliegue Automático

```bash
# Ejecutar el script de despliegue completo
./deploy_panel_service.sh
```

Este script:
- Construye el servicio C#
- Integra con el backend Python
- Crea el servicio systemd
- Inicia el servicio
- Ejecuta tests iniciales

### 2. Despliegue Manual

#### Construir el Servicio C#

```bash
cd PanelService
dotnet restore
dotnet build --configuration Release
dotnet publish --configuration Release --output ./publish
```

#### Integrar con Python

```bash
python3 integrate_panel_service.py
```

#### Crear Servicio Systemd

```bash
sudo cp -r PanelService/publish/* /opt/parking-panel-service/
sudo systemctl enable parking-panel-service
sudo systemctl start parking-panel-service
```

## 🔧 Gestión del Servicio

### Comandos de Gestión

```bash
# Iniciar servicio
./manage_panel_service.sh start

# Detener servicio
./manage_panel_service.sh stop

# Reiniciar servicio
./manage_panel_service.sh restart

# Ver estado
./manage_panel_service.sh status

# Ver logs en tiempo real
./manage_panel_service.sh logs

# Testear servicio
./manage_panel_service.sh test

# Testear integración
./manage_panel_service.sh integration
```

### Monitor Continuo

```bash
# Ejecutar monitor continuo
./monitor_panel_service.py
```

## 🌐 API REST

### Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado de salud del servicio |
| GET | `/api/panel/status` | Estado de todos los paneles |
| GET | `/api/panel/status/{ip}` | Estado de un panel específico |
| POST | `/api/panel/send` | Enviar mensaje a un panel |
| POST | `/api/panel/occupancy` | Enviar ocupación a un panel |
| POST | `/api/panel/broadcast` | Broadcast a todos los paneles |
| POST | `/api/panel/test/{ip}` | Testear un panel |
| POST | `/api/panel/static` | Enviar texto estático |

### Ejemplos de Uso

#### Enviar Mensaje

```bash
curl -X POST http://localhost:5001/api/panel/send \
  -H "Content-Type: application/json" \
  -d '{
    "panelIP": "172.20.17.50",
    "message": "Parking LLIURE"
  }'
```

#### Enviar Ocupación

```bash
curl -X POST http://localhost:5001/api/panel/occupancy \
  -H "Content-Type: application/json" \
  -d '{
    "panelIP": "172.20.17.50",
    "current": 150,
    "total": 250,
    "status": "LLIURE"
  }'
```

#### Broadcast

```bash
curl -X POST http://localhost:5001/api/panel/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mantenimiento programado",
    "sendToAll": true
  }'
```

## 🧪 Testing

### Test del Servicio

```bash
python3 test_panel_service.py
```

Este test verifica:
- Conectividad con el servicio
- Estado de paneles
- Envío de mensajes
- Envío de ocupación
- Broadcast
- Texto estático

### Test de Integración

```bash
python3 test_integration.py
```

Este test verifica:
- Integración entre C# y Python
- Funcionamiento del wrapper
- Comunicación end-to-end

## 🔍 Monitoreo

### Logs del Servicio

```bash
# Ver logs en tiempo real
sudo journalctl -u parking-panel-service -f

# Ver logs de las últimas 100 líneas
sudo journalctl -u parking-panel-service -n 100
```

### Estado del Servicio

```bash
# Ver estado detallado
sudo systemctl status parking-panel-service

# Verificar puerto
netstat -tlnp | grep 5001
```

### Monitor Automático

El script `monitor_panel_service.py` verifica continuamente:
- Estado del servicio
- Estado de los paneles
- Reinicia automáticamente si es necesario

## 🛠️ Configuración

### Configuración del Servicio

Archivo: `/opt/parking-panel-service/appsettings.json`

```json
{
  "PanelService": {
    "Port": 5001,
    "Timeout": 600,
    "RetryAttempts": 3,
    "RetryDelay": 1000
  },
  "Panels": {
    "DefaultPort": 5200,
    "DefaultCardId": 1,
    "DefaultTimeout": 600,
    "DefaultIDCode": "255.255.255.255"
  }
}
```

### Configuración de Paneles

Los paneles están configurados en el código:

| Panel | IP | Nombre | Parking |
|-------|----|--------|---------|
| 1 | 172.20.17.50 | PANEL C. ESPORTIVA | 1 - P. Ciutat Esportiva |
| 2 | 172.20.5.50 | PANEL BASSETA 1 | 2 - P. Basseta Centre |
| 3 | 172.20.5.51 | PANEL BASSETA 2 | 2 - P. Basseta Centre |
| 4 | 172.20.8.50 | PANEL PITERES | 6 - P. Poble antic/Conservatori |
| 5 | 172.20.4.50 | PANEL PALAU | 5 - P. Poble antic/Palau Altea |
| 6 | 172.20.4.51 | PANEL COCOLISO | 5 - P. Poble antic/Palau Altea |
| 7 | 172.20.4.52 | BELLES ARTS 2 | 4 - P. Poble antic/Belles Arts 2 |
| 8 | 172.20.4.53 | BELLES ARTS | 3 - P. Poble antic/Belles Arts 1 |
| 9 | 172.20.2.50 | PANEL RENFE | 8 - P. Estació Altea |
| 10 | 172.20.1.50 | PANEL ALTEA VELLA | 9 - P. Altea la Vella |

## 🔧 Solución de Problemas

### Servicio No Inicia

```bash
# Verificar logs
sudo journalctl -u parking-panel-service -n 50

# Verificar dependencias
ls -la /opt/parking-panel-service/CP5200.dll

# Verificar puerto
sudo netstat -tlnp | grep 5001
```

### Paneles No Responden

```bash
# Testear conectividad
ping 172.20.17.50

# Testear servicio
python3 test_panel_service.py

# Verificar estado de paneles
curl http://localhost:5001/api/panel/status
```

### Integración Fallida

```bash
# Verificar que el servicio esté ejecutándose
./manage_panel_service.sh status

# Testear integración
python3 test_integration.py

# Verificar logs del backend Python
tail -f /var/log/parking-api.log
```

## 📊 Métricas y Monitoreo

### Métricas Disponibles

- Estado del servicio (online/offline)
- Estado de cada panel
- Tiempo de respuesta
- Número de mensajes enviados
- Errores de comunicación

### Dashboard Swagger

Acceder a: http://localhost:5001/swagger

Proporciona:
- Documentación interactiva de la API
- Pruebas de endpoints
- Esquemas de datos

## 🔄 Actualizaciones

### Actualizar el Servicio

```bash
# Detener servicio
./manage_panel_service.sh stop

# Reconstruir
cd PanelService
dotnet publish --configuration Release --output ./publish

# Copiar archivos
sudo cp -r publish/* /opt/parking-panel-service/

# Reiniciar servicio
./manage_panel_service.sh start
```

### Actualizar Integración

```bash
# Ejecutar script de integración
python3 integrate_panel_service.py

# Reiniciar backend Python
sudo systemctl restart parking-api
```

## 📞 Soporte

### Logs Importantes

- Servicio C#: `sudo journalctl -u parking-panel-service`
- Backend Python: `/var/log/parking-api.log`
- Monitor: Salida de `monitor_panel_service.py`

### Comandos de Diagnóstico

```bash
# Estado completo del sistema
./manage_panel_service.sh status
python3 test_panel_service.py
python3 test_integration.py

# Verificar conectividad de red
for ip in 172.20.17.50 172.20.5.50 172.20.5.51; do
    ping -c 1 $ip
done
```

## 📝 Notas de Desarrollo

### Protocolo CP5200

El servicio usa la DLL CP5200 original para comunicación con los paneles:
- Inicialización de red antes de enviar mensajes
- Protocolo nativo del fabricante
- Soporte para texto dinámico y estático

### Fallback a HTTP

Si el servicio C# no está disponible, el sistema fallback al método HTTP original:
- Mantiene compatibilidad
- No interrumpe el funcionamiento
- Logs de errores para diagnóstico

### Seguridad

- El servicio se ejecuta como root (necesario para CP5200)
- Solo acepta conexiones locales
- Logs detallados para auditoría
- Timeouts configurados para evitar bloqueos 