# Deployment v3.0.0 - Parking Altea

## Resumen

Este documento describe el proceso completo de deployment de la versión 3.0.0 del sistema Parking Altea, que incluye:

- **Panel Service v2** con nueva librería Java `protocol.jar`
- **Migración de tipos de paneles** (3 tipos soportados)
- **Actualización de frontend** con gestión de tipos de paneles
- **Mejoras en la API** para soporte de múltiples protocolos

## Cambios Principales

### 1. Panel Service v2
- Nueva implementación en Node.js con librería Java `protocol.jar`
- Soporte para múltiples protocolos de comunicación
- API REST en puerto 5657
- Configuración centralizada de paneles

### 2. Tipos de Paneles
- **Tipo 1**: Protocolo antiguo, 1 ventana 64x16
- **Tipo 2**: Protocolo nuevo, 1 ventana 64x16  
- **Tipo 3**: Protocolo nuevo, 2 ventanas 32x16 cada una

### 3. Migración de Base de Datos
- Nuevas tablas: `manufacturers`, `panel_types`
- Actualización de tabla `panels` con campos de tipo
- Migración automática de paneles existentes

## Requisitos Previos

### Servidor Remoto
- Ubuntu 20.04 LTS o superior
- PostgreSQL 12 o superior
- Node.js 16 o superior
- Python 3.8 o superior
- Nginx configurado
- Java 8 o superior (para protocol.jar)

### Local (Windows)
- PowerShell 5.1 o superior
- SSH configurado
- Acceso al servidor remoto

## Archivos de Deployment

### Scripts Principales
- `deploy/deploy_v3.0.0_complete.sh` - Script principal de deployment (Linux)
- `deploy/deploy_v3.0.0.ps1` - Script de deployment desde Windows
- `deploy/verify_v3.0.0_deployment.sh` - Verificación post-deployment (Linux)
- `deploy/verify_v3.0.0.ps1` - Verificación desde Windows
- `deploy/rollback_v3.0.0.sh` - Rollback en caso de problemas

### Archivos de Migración
- `src/migrate_panel_types.py` - Script de migración de tipos de paneles
- `src/models.py` - Modelos actualizados de base de datos

### Panel Service v2
- `server/panel-service-v2/` - Directorio completo del servicio
- `server/panel-service-v2/server.js` - Servidor Node.js
- `server/panel-service-v2/protocol.jar` - Librería Java
- `server/panel-service-v2/config/` - Configuración

## Proceso de Deployment

### 1. Preparación

#### Verificar Estado Actual
```bash
# Verificar servicios activos
systemctl status parking-api parking-camera parking-panel

# Verificar base de datos
psql -d parking_altea -c "SELECT COUNT(*) FROM panels;"

# Verificar espacio en disco
df -h
```

#### Crear Backup
```bash
# El script crea automáticamente backups:
# - Base de datos: parking_altea_backup_v3.0.0_TIMESTAMP.sql
# - Archivos: parking_altea_backup_v3.0.0_TIMESTAMP.tar.gz
# - Configuración: parking_altea_backup_v3.0.0_TIMESTAMP.config.tar.gz
```

### 2. Deployment desde Windows

#### Opción 1: Deployment Completo
```powershell
# Deployment con verificación automática
.\deploy\deploy_v3.0.0.ps1

# Deployment sin backup (solo si es necesario)
.\deploy\deploy_v3.0.0.ps1 -SkipBackup

# Deployment sin verificación
.\deploy\deploy_v3.0.0.ps1 -SkipVerification

# Deployment forzado (sin confirmación)
.\deploy\deploy_v3.0.0.ps1 -Force
```

#### Opción 2: Deployment Manual
```powershell
# 1. Copiar archivos
scp deploy\deploy_v3.0.0_complete.sh parking@parking-altea.com:/tmp/

# 2. Ejecutar deployment
ssh parking@parking-altea.com "chmod +x /tmp/deploy_v3.0.0_complete.sh && /tmp/deploy_v3.0.0_complete.sh"

# 3. Verificar
.\deploy\verify_v3.0.0.ps1
```

### 3. Deployment desde Linux

```bash
# 1. Copiar script
scp deploy/deploy_v3.0.0_complete.sh parking@parking-altea.com:/tmp/

# 2. Ejecutar deployment
ssh parking@parking-altea.com "chmod +x /tmp/deploy_v3.0.0_complete.sh && /tmp/deploy_v3.0.0_complete.sh"

# 3. Verificar
scp deploy/verify_v3.0.0_deployment.sh parking@parking-altea.com:/tmp/
ssh parking@parking-altea.com "chmod +x /tmp/verify_v3.0.0_deployment.sh && /tmp/verify_v3.0.0_deployment.sh"
```

## Verificación Post-Deployment

### 1. Verificación Automática

#### Desde Windows
```powershell
.\deploy\verify_v3.0.0.ps1
```

#### Desde Linux
```bash
ssh parking@parking-altea.com "cd /tmp && ./verify_v3.0.0_deployment.sh"
```

### 2. Verificación Manual

#### Servicios
```bash
# Verificar servicios activos
systemctl status parking-api parking-camera parking-panel panel-service-v2

# Verificar puertos
netstat -tuln | grep -E ':(5000|5001|3000|5657|80|443)'
```

#### Base de Datos
```bash
# Verificar migración
psql -d parking_altea -c "SELECT COUNT(*) FROM manufacturers;"
psql -d parking_altea -c "SELECT COUNT(*) FROM panel_types;"
psql -d parking_altea -c "SELECT COUNT(*) FROM panels WHERE panel_type_id IS NOT NULL;"
```

#### Endpoints
```bash
# Verificar endpoints
curl http://parking-altea.com/api/health
curl http://parking-altea.com/health/
curl http://parking-altea.com/api/panel-types
```

#### Panel Service v2
```bash
# Verificar archivos
ls -la /opt/panelsender/
ls -la /opt/panelsender/config/

# Verificar logs
journalctl -u panel-service-v2 --since "1 hour ago"
```

## Rollback

### 1. Rollback Automático

#### Desde Windows
```powershell
# El rollback se ejecuta automáticamente si el deployment falla
# Para rollback manual:
ssh parking@parking-altea.com "cd /tmp && ./rollback_v3.0.0.sh"
```

#### Desde Linux
```bash
scp deploy/rollback_v3.0.0.sh parking@parking-altea.com:/tmp/
ssh parking@parking-altea.com "chmod +x /tmp/rollback_v3.0.0.sh && /tmp/rollback_v3.0.0.sh"
```

### 2. Rollback Manual

```bash
# 1. Detener servicios
systemctl stop parking-api parking-camera parking-panel panel-service-v2

# 2. Restaurar base de datos
psql -d parking_altea < /opt/backups/parking_altea_backup_v3.0.0_TIMESTAMP.sql

# 3. Restaurar archivos
tar -xzf /opt/backups/parking_altea_backup_v3.0.0_TIMESTAMP.tar.gz -C /opt

# 4. Restaurar configuración
tar -xzf /opt/backups/parking_altea_backup_v3.0.0_TIMESTAMP.config.tar.gz -C /

# 5. Eliminar Panel Service v2
systemctl disable panel-service-v2
rm -f /etc/systemd/system/panel-service-v2.service
rm -rf /opt/panelsender

# 6. Restaurar rama Git
cd /opt/parking_altea
git checkout main
git pull origin main

# 7. Reinstalar dependencias
pip install -r requirements.txt
cd client && npm install && npm run build

# 8. Iniciar servicios
systemctl start parking-api parking-camera parking-panel
```

## Configuración Post-Deployment

### 1. Configurar Tipos de Paneles

Acceder al panel de administración y configurar los tipos de panel según corresponda:

1. **Panel Tipo 1**: Protocolo antiguo, 1 ventana 64x16
2. **Panel Tipo 2**: Protocolo nuevo, 1 ventana 64x16
3. **Panel Tipo 3**: Protocolo nuevo, 2 ventanas 32x16

### 2. Actualizar Configuración de Paneles

```bash
# Editar configuración de paneles
nano /opt/panelsender/config/panels.json

# Reiniciar Panel Service v2
systemctl restart panel-service-v2
```

### 3. Verificar Comunicación con Paneles

```bash
# Test de comunicación
curl -X POST http://localhost:5657/api/v1/panels/test \
  -H "Content-Type: application/json" \
  -d '{"panel_id": 1, "message": "TEST"}'
```

## Monitoreo

### 1. Logs de Servicios

```bash
# Ver logs en tiempo real
journalctl -u parking-api -f
journalctl -u parking-camera -f
journalctl -u parking-panel -f
journalctl -u panel-service-v2 -f
```

### 2. Monitoreo de Recursos

```bash
# Uso de memoria
free -h

# Uso de disco
df -h

# Carga del sistema
uptime

# Procesos activos
ps aux | grep -E "(parking|panel)"
```

### 3. Verificación de Conectividad

```bash
# Verificar puertos abiertos
netstat -tuln | grep -E ':(5000|5001|3000|5657|80|443)'

# Test de conectividad
curl -I http://parking-altea.com/api/health
curl -I http://parking-altea.com/health/
```

## Troubleshooting

### Problemas Comunes

#### 1. Panel Service v2 no inicia
```bash
# Verificar logs
journalctl -u panel-service-v2 -n 50

# Verificar archivos
ls -la /opt/panelsender/
ls -la /opt/panelsender/config/

# Verificar permisos
chown -R parking:parking /opt/panelsender/
chmod +x /opt/panelsender/scripts/*.sh
```

#### 2. Migración de base de datos falla
```bash
# Verificar espacio en disco
df -h

# Verificar permisos de base de datos
sudo -u postgres psql -c "\du"

# Ejecutar migración manualmente
cd /opt/parking_altea
python src/migrate_panel_types.py
```

#### 3. Frontend no carga
```bash
# Verificar archivos construidos
ls -la /var/www/parking_altea/

# Reconstruir frontend
cd /opt/parking_altea/client
npm install
npm run build
sudo cp -r dist/* /var/www/parking_altea/
```

#### 4. Nginx no funciona
```bash
# Verificar configuración
nginx -t

# Verificar logs
tail -f /var/log/nginx/error.log

# Reiniciar nginx
systemctl restart nginx
```

### Comandos de Emergencia

```bash
# Detener todos los servicios
systemctl stop parking-api parking-camera parking-panel panel-service-v2

# Reiniciar todos los servicios
systemctl restart parking-api parking-camera parking-panel panel-service-v2

# Verificar estado de todos los servicios
systemctl status parking-api parking-camera parking-panel panel-service-v2

# Limpiar logs
journalctl --vacuum-time=1d
```

## Documentación Relacionada

- [Panel Service v2](../docs/panel_service_v2.md)
- [Migración de Tipos de Paneles](../docs/panel_types_migration.md)
- [API Endpoints](../docs/api_endpoints.md)
- [Base de Datos](../docs/database.md)

## Contacto

En caso de problemas durante el deployment, contactar al equipo de desarrollo con:

- Logs de error completos
- Estado de los servicios (`systemctl status`)
- Información del servidor (`uname -a`, `df -h`, `free -h`)
- Timestamp del error 