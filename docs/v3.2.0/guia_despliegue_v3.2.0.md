# Guía de Despliegue - v3.2.0_alarms

## 📋 Información del Despliegue

- **Versión**: v3.2.0_alarms
- **Fecha**: 28/07/2025
- **Servidor**: 157.180.91.63
- **Usuario**: root
- **Directorio**: `/opt/parking_altea`
- **Estado**: ✅ **DESPLIEGUE COMPLETADO EXITOSAMENTE**

## 🎯 Estado Actual del Sistema

### Servicios Activos
- ✅ **parking-api.service**: Activo (puerto 6001)
- ✅ **parking-camera.service**: Activo (puerto 6400)
- ✅ **parking-schedule-monitor.service**: Activo
- ✅ **parking-alarm-monitor.service**: Activo

### Puertos Verificados
- ✅ **Puerto 6001**: API Server (gunicorn - 4 procesos)
- ✅ **Puerto 6400**: Camera Server (gunicorn - 3 procesos)
- ✅ **Puerto 5789**: Frontend (nginx)

### Funcionalidades Verificadas
- ✅ **API**: Endpoint `/api/parkings` responde correctamente
- ✅ **Frontend**: Servidor web funcionando en puerto 5789
- ✅ **Base de Datos**: Migración de alarmas aplicada correctamente
- ✅ **Monitores**: Servicios de programación y alarmas ejecutándose

## 🚀 Pasos de Despliegue

### ✅ Paso 1: Detener Servicios Actuales

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

### ✅ Paso 2: Actualizar Código y Cambiar a Nueva Rama

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

### ✅ Paso 3: Aplicar Migración de Base de Datos

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

### ✅ Paso 4: Instalar Dependencias Backend

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

### ✅ Paso 5: Compilar y Actualizar Frontend

```bash
# Navegar al directorio del frontend
cd /opt/parking_altea/client

# Instalar dependencias de Node.js
npm install

# Instalar dependencias adicionales necesarias
npm install react-bootstrap bootstrap react-bootstrap-icons

# Compilar para producción
npm run build

# Verificar que la compilación fue exitosa
ls -la dist/
```

### ✅ Paso 6: Configurar Nuevo Servicio de Alarmas

```bash
# Copiar archivo de servicio
cp /opt/parking_altea/deploy/parking-alarm-monitor.service /etc/systemd/system/

# Recargar configuración de systemd
systemctl daemon-reload

# Habilitar el servicio
systemctl enable parking-alarm-monitor.service

# Verificar que el servicio se ha configurado correctamente
systemctl status parking-alarm-monitor.service
```

### ✅ Paso 7: Levantar Todos los Servicios

```bash
# Iniciar API Server
systemctl start parking-api.service

# Iniciar Camera Server
systemctl start parking-camera.service

# Iniciar Schedule Monitor
systemctl start parking-schedule-monitor.service

# Iniciar Alarm Monitor
systemctl start parking-alarm-monitor.service

# Verificar estado de todos los servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service parking-alarm-monitor.service
```

### ✅ Paso 8: Verificar Puertos y Conectividad

```bash
# Verificar que los puertos están escuchando
netstat -tlnp | grep -E ':(6001|6400|5789)'

# Verificar conectividad de la API
curl -s http://localhost:6001/api/parkings | head -20

# Verificar conectividad del frontend
curl -s http://localhost:5789 | head -20
```

### ✅ Paso 9: Verificar Funcionalidad del Sistema

```bash
# Verificar que todos los servicios están activos
systemctl is-active parking-api.service parking-camera.service parking-schedule-monitor.service parking-alarm-monitor.service

# Verificar procesos en ejecución
ps aux | grep -E '(gunicorn|python.*monitor)' | grep -v grep

# Verificar logs de los servicios
journalctl -u parking-api.service --no-pager -n 10
journalctl -u parking-camera.service --no-pager -n 10
journalctl -u parking-schedule-monitor.service --no-pager -n 10
journalctl -u parking-alarm-monitor.service --no-pager -n 10
```

### ✅ Paso 10: Verificación Final

```bash
# Verificar estado final de todos los servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service parking-alarm-monitor.service

# Verificar puertos finales
netstat -tlnp | grep -E ':(6001|6400|5789)'

# Verificar procesos finales
ps aux | grep -E '(gunicorn|python.*monitor)' | grep -v grep

# Verificar funcionalidad de la API
curl -s http://localhost:6001/api/parkings | jq '.[0]' 2>/dev/null || curl -s http://localhost:6001/api/parkings | head -5
```

## 🔧 Problemas Resueltos Durante el Despliegue

### 1. Problemas de Import/Export en Frontend
- **Problema**: Errores de compilación por inconsistencias en import/export de servicios
- **Solución**: Convertir todos los servicios a default exports y actualizar imports correspondientes
- **Archivos afectados**: 
  - `client/src/services/panelService.js`
  - `client/src/services/cameraService.js`
  - `client/src/services/parkingService.js`
  - `client/src/pages/ParkingDetail.jsx`
  - `client/src/pages/Panels.jsx`
  - `client/src/pages/CameraLogs.jsx`

### 2. Dependencias Faltantes en Frontend
- **Problema**: Errores de compilación por dependencias faltantes
- **Solución**: Instalar `react-bootstrap`, `bootstrap`, `react-bootstrap-icons`
- **Comando**: `npm install react-bootstrap bootstrap react-bootstrap-icons`

### 3. Problemas de Sincronización Git
- **Problema**: Cambios locales no reflejados en servidor remoto
- **Solución**: Commit y push de cambios locales, seguido de `git fetch --all` y `git reset --hard origin/v3.2.0_alarms` en remoto

## 📊 Métricas del Despliegue

- **Tiempo total**: ~45 minutos
- **Servicios desplegados**: 4
- **Puertos configurados**: 3
- **Procesos activos**: 10
- **Errores resueltos**: 3 tipos principales
- **Estado final**: ✅ **FUNCIONANDO CORRECTAMENTE**

## 🎉 Conclusión

El despliegue de la versión v3.2.0_alarms se ha completado exitosamente. Todos los servicios están funcionando correctamente y el sistema de alarmas está operativo. El sistema está listo para uso en producción.

### URLs de Acceso
- **Frontend**: http://157.180.91.63:5789
- **API**: http://157.180.91.63:6001/api/
- **Camera Server**: http://157.180.91.63:6400/

### Próximos Pasos Recomendados
1. Realizar pruebas de funcionalidad del sistema de alarmas
2. Configurar alarmas específicas según necesidades
3. Monitorear logs de los servicios durante las primeras horas
4. Verificar integración con sistemas externos (email, SMS, etc.) 