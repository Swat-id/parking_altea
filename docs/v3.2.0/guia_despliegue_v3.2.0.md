# Guía de Despliegue - v3.2.0_alarms

## 🚀 Información del Servidor

### Datos de Conexión
- **IP del Servidor**: 157.180.91.63
- **Usuario**: root
- **Directorio del Proyecto**: `/opt/parking_altea`
- **Entorno Virtual**: `/opt/parking_altea/venv`

### Acceso SSH
```bash
ssh root@157.180.91.63
```

## 📋 Pre-requisitos

### Software Requerido
- Python 3.8+
- Node.js 16+
- PostgreSQL
- nginx
- systemd

### Servicios del Sistema
```bash
# Verificar servicios instalados
systemctl list-units --type=service | grep parking

# Servicios principales
parking-api.service          # API Server (Puerto 6001)
parking-camera.service       # Camera Server
parking-schedule-monitor.service  # Schedule Monitor
```

## 🔄 Proceso de Despliegue Completo

### Paso 1: Preparación Local

```bash
# 1. Verificar que estamos en la rama correcta
git branch
# Debe mostrar: * v3.2.0_alarms

# 2. Verificar cambios pendientes
git status

# 3. Añadir todos los cambios
git add .

# 4. Hacer commit con descripción clara
git commit -m "v3.2.0_alarms: [Descripción de cambios]"

# 5. Subir cambios al repositorio
git push origin v3.2.0_alarms
```

### Paso 2: Conectar al Servidor Remoto

```bash
ssh root@157.180.91.63
```

### Paso 3: Parar Servicios

```bash
# Parar todos los servicios del sistema
systemctl stop parking-api.service
systemctl stop parking-camera.service
systemctl stop parking-schedule-monitor.service

# Verificar que están parados
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service
```

### Paso 4: Actualizar Código

```bash
# Navegar al directorio del proyecto
cd /opt/parking_altea

# Obtener cambios del repositorio
git fetch --all

# Cambiar a la nueva rama
git checkout v3.2.0_alarms

# O alternativamente, hacer reset hard
git reset --hard origin/v3.2.0_alarms

# Verificar que estamos en la rama correcta
git branch
```

### Paso 5: Instalar Dependencias Backend

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt

# Verificar instalación
python -c "import flask, sqlalchemy; print('Dependencias instaladas correctamente')"
```

### Paso 6: Instalar y Compilar Frontend

```bash
# Navegar al directorio del cliente
cd client

# Instalar dependencias Node.js
npm install

# Compilar para producción
npm run build

# Verificar que la compilación fue exitosa
ls -la dist/
```

### Paso 7: Copiar Archivos Compilados

```bash
# Copiar archivos compilados al directorio estático
cp -r dist/* /opt/parking_altea/static/

# Verificar que se copiaron correctamente
ls -la /opt/parking_altea/static/
```

### Paso 8: Reiniciar Servicios

```bash
# Reiniciar todos los servicios
systemctl start parking-api.service
systemctl start parking-camera.service
systemctl start parking-schedule-monitor.service

# Verificar estado de los servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service
```

### Paso 9: Verificar Funcionamiento

```bash
# Verificar que la API responde
curl http://localhost:6001/api/panels

# Verificar que el frontend es accesible
curl http://157.180.91.63

# Verificar logs de servicios
journalctl -u parking-api.service --no-pager -n 20
```

## 🔍 Verificación Post-Despliegue

### Verificación de Servicios

```bash
# Estado de todos los servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service

# Verificar puertos en uso
netstat -tlnp | grep :6001
netstat -tlnp | grep :80
```

### Verificación de API

```bash
# Endpoint principal de paneles
curl http://localhost:6001/api/panels

# Verificar respuesta JSON
curl http://localhost:6001/api/panels | jq '.[0]'

# Verificar programaciones activas
curl http://localhost:6001/api/panels | jq '.[] | select(.active_schedule) | .name'
```

### Verificación de Frontend

```bash
# Verificar que nginx sirve el frontend
curl -I http://157.180.91.63

# Verificar archivos estáticos
ls -la /opt/parking_altea/static/
```

### Verificación de Base de Datos

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Verificar tablas
\dt

# Verificar datos de paneles
SELECT name, status, last_message FROM panels;

# Salir de PostgreSQL
\q
```

## 🚨 Solución de Problemas Comunes

### Error: tsconfig.json corrupto
```bash
# Copiar archivo correcto desde local
scp tsconfig.json root@157.180.91.63:/opt/parking_altea/
```

### Error: Entorno virtual no encontrado
```bash
# Crear nuevo entorno virtual
cd /opt/parking_altea
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: Puerto 6001 ocupado
```bash
# Encontrar proceso que usa el puerto
lsof -i :6001

# Matar proceso si es necesario
kill -9 [PID]
```

### Error: Permisos de archivos
```bash
# Corregir permisos
chown -R root:root /opt/parking_altea
chmod -R 755 /opt/parking_altea
```

### Error: Servicio no inicia
```bash
# Verificar logs del servicio
journalctl -u parking-api.service -f

# Verificar configuración del servicio
systemctl cat parking-api.service
```

## 📊 Monitoreo Continuo

### Comandos de Monitoreo

```bash
# Ver logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u parking-schedule-monitor.service -f

# Ver uso de recursos
htop
df -h
free -h

# Ver estado de servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service
```

### Verificación Periódica

```bash
# Script de verificación rápida
#!/bin/bash
echo "=== Verificación del Sistema ==="
echo "1. Estado de servicios:"
systemctl is-active parking-api.service parking-camera.service parking-schedule-monitor.service
echo ""
echo "2. API funcionando:"
curl -s http://localhost:6001/api/panels | jq 'length' 2>/dev/null || echo "API no responde"
echo ""
echo "3. Frontend accesible:"
curl -s -I http://157.180.91.63 | head -1
```

## 📞 Contacto y Soporte

- **Servidor**: 157.180.91.63
- **Usuario**: root
- **Documentación**: `/opt/parking_altea/docs/v3.2.0/`
- **Logs**: `journalctl -u [servicio]`

---

**Nota**: Esta guía debe actualizarse con cada nueva versión del sistema. 