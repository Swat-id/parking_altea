# Guía de Despliegue - v3.2.0_alarms

## 📋 Información del Despliegue

- **Versión**: v3.2.0_alarms
- **Fecha**: 28/07/2025
- **Servidor**: 157.180.91.63
- **Usuario**: root
- **Directorio**: `/opt/parking_altea`

## 🚀 Pasos de Despliegue

### Paso 1: Detener Servicios Actuales

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Detener todos los servicios del sistema
systemctl stop parking-api.service
systemctl stop parking-camera.service
systemctl stop parking-schedule-monitor.service
systemctl stop parking-alarm-monitor.service

# Verificar que están detenidos
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service parking-alarm-monitor.service
```

### Paso 2: Actualizar Código y Cambiar a Nueva Rama

```bash
# Navegar al directorio del proyecto
cd /opt/parking_altea

# Verificar estado actual
git status
git branch

# Obtener todas las ramas remotas
git fetch --all

# Cambiar a la rama v3.2.0_alarms
git checkout v3.2.0_alarms

# Forzar actualización con el repositorio remoto
git reset --hard origin/v3.2.0_alarms

# Verificar que los cambios se han aplicado
git log --oneline -5
```

### Paso 3: Aplicar Migración de Base de Datos

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar migración del sistema de alarmas
python src/migrate_alarm_system.py

# Verificar que las tablas se han creado correctamente
python -c "
from src.models import db, AlarmConfiguration, Alarm, AlarmHistory
from src.config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print('Tablas de alarmas creadas correctamente')
    print('AlarmConfiguration:', AlarmConfiguration.query.count(), 'registros')
    print('Alarm:', Alarm.query.count(), 'registros')
    print('AlarmHistory:', AlarmHistory.query.count(), 'registros')
"
```

### Paso 4: Instalar Dependencias Backend

```bash
# Asegurar que el entorno virtual está activado
source venv/bin/activate

# Actualizar dependencias
pip install -r requirements.txt

# Verificar instalación de dependencias críticas
python -c "
import flask
import psycopg2
import schedule
import smtplib
print('Dependencias principales instaladas correctamente')
"
```

### Paso 5: Compilar y Actualizar Frontend

```bash
# Navegar al directorio del cliente
cd /opt/parking_altea/client

# Instalar dependencias de Node.js
npm install

# Compilar para producción
npm run build

# Verificar que la compilación fue exitosa
ls -la dist/

# Copiar archivos compilados al directorio estático
cp -r dist/* /opt/parking_altea/static/

# Verificar que los archivos se han copiado
ls -la /opt/parking_altea/static/
```

### Paso 6: Configurar Nuevo Servicio de Alarmas

```bash
# Volver al directorio raíz
cd /opt/parking_altea

# Copiar archivo de servicio de alarmas
cp deploy/parking-alarm-monitor.service /etc/systemd/system/

# Recargar configuración de systemd
systemctl daemon-reload

# Habilitar el servicio para que se inicie automáticamente
systemctl enable parking-alarm-monitor.service

# Verificar que el archivo de servicio se ha copiado correctamente
cat /etc/systemd/system/parking-alarm-monitor.service
```

### Paso 7: Levantar Todos los Servicios

```bash
# Iniciar servicios en orden
systemctl start parking-api.service
systemctl start parking-camera.service
systemctl start parking-schedule-monitor.service
systemctl start parking-alarm-monitor.service

# Verificar estado de todos los servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service parking-alarm-monitor.service
```

### Paso 8: Verificar Puertos y Conectividad

```bash
# Verificar que los puertos están en uso
netstat -tlnp | grep -E ':(6001|5789|5432)'

# Verificar que nginx está sirviendo el frontend
curl -I http://localhost:5789

# Verificar que la API está respondiendo
curl http://localhost:6001/api/panels

# Verificar endpoints de alarmas
curl http://localhost:6001/api/alarms/configurations
curl http://localhost:6001/api/alarms/active
```

### Paso 9: Verificar Funcionalidad del Sistema

```bash
# Verificar logs de servicios
journalctl -u parking-api.service --no-pager -n 20
journalctl -u parking-camera.service --no-pager -n 20
journalctl -u parking-schedule-monitor.service --no-pager -n 20
journalctl -u parking-alarm-monitor.service --no-pager -n 20

# Verificar que el sistema de alarmas está funcionando
curl http://localhost:6001/api/alarms/equipment-status

# Verificar configuración de email
python src/test_gmail_config.py
```

### Paso 10: Verificación Final

```bash
# Verificar acceso desde el exterior
curl -I http://157.180.91.63:5789

# Verificar API desde el exterior
curl http://157.180.91.63:6001/api/panels

# Verificar que todos los paneles están online
curl http://157.180.91.63:6001/api/panels | jq '.[] | {name: .name, status: .status}'
```

## 🔍 Comandos de Verificación Rápida

### Estado de Servicios
```bash
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service parking-alarm-monitor.service
```

### Puertos Activos
```bash
netstat -tlnp | grep -E ':(6001|5789|5432)'
```

### Logs en Tiempo Real
```bash
# API Server
journalctl -u parking-api.service -f

# Camera Server
journalctl -u parking-camera.service -f

# Schedule Monitor
journalctl -u parking-schedule-monitor.service -f

# Alarm Monitor
journalctl -u parking-alarm-monitor.service -f
```

### Verificación de Endpoints
```bash
# Paneles
curl http://localhost:6001/api/panels

# Configuraciones de alarmas
curl http://localhost:6001/api/alarms/configurations

# Alarmas activas
curl http://localhost:6001/api/alarms/active

# Estado de equipos
curl http://localhost:6001/api/alarms/equipment-status

# Estadísticas
curl http://localhost:6001/api/alarms/statistics
```

## 🚨 Solución de Problemas

### Si un servicio no inicia
```bash
# Verificar logs específicos
journalctl -u [nombre-servicio] --no-pager -n 50

# Verificar archivo de configuración
systemctl cat [nombre-servicio]

# Reiniciar servicio
systemctl restart [nombre-servicio]
```

### Si la migración falla
```bash
# Verificar conexión a base de datos
python -c "
from src.config import Config
import psycopg2
try:
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    print('Conexión a BD exitosa')
    conn.close()
except Exception as e:
    print('Error de conexión:', e)
"
```

### Si el frontend no se carga
```bash
# Verificar nginx
systemctl status nginx

# Verificar archivos estáticos
ls -la /opt/parking_altea/static/

# Reiniciar nginx
systemctl restart nginx
```

### Si las alarmas no funcionan
```bash
# Verificar configuración de email
python src/test_gmail_config.py

# Verificar logs del monitor de alarmas
journalctl -u parking-alarm-monitor.service --no-pager -n 50

# Verificar estado de equipos
curl http://localhost:6001/api/alarms/equipment-status
```

## ✅ Checklist de Verificación

- [ ] Todos los servicios están ejecutándose
- [ ] Puerto 6001 (API) está activo
- [ ] Puerto 5789 (Frontend) está activo
- [ ] Base de datos migrada correctamente
- [ ] Frontend compilado y copiado
- [ ] Servicio de alarmas configurado
- [ ] API responde correctamente
- [ ] Frontend accesible desde exterior
- [ ] Sistema de alarmas funcionando
- [ ] Configuración de email válida
- [ ] Todos los paneles online
- [ ] Logs sin errores críticos

## 📞 Información de Contacto

- **Servidor**: 157.180.91.63
- **Frontend**: http://157.180.91.63:5789
- **API**: http://157.180.91.63:6001
- **Documentación**: `/opt/parking_altea/docs/v3.2.0/`

---

**Nota**: Ejecutar los comandos en el orden especificado para asegurar un despliegue correcto. 