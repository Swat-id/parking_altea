# Despliegue v3.1.0 - Parking Altea

## 📋 Resumen

Este directorio contiene todos los archivos y scripts necesarios para el despliegue completo de la versión v3.1.0 del sistema Parking Altea en el servidor remoto.

## 🎯 Información del Despliegue

- **Versión**: v3.1.0
- **Servidor**: 157.180.91.63
- **Usuario**: root
- **Directorio**: /opt/parking_altea
- **Fecha**: 7 de enero de 2025

## 📁 Estructura de Archivos

```
deploy/v3.1.0/
├── README.md                           # Este archivo
├── deploy_v3.1.0_complete.sh           # Script principal de despliegue (Linux)
├── deploy_v3.1.0_complete.ps1          # Script principal de despliegue (PowerShell)
├── setup_server_v3.1.0.sh              # Configuración inicial del servidor
├── rollback_v3.1.0.sh                  # Script de rollback
├── verify_deployment_v3.1.0.sh         # Verificación post-despliegue (Linux)
├── verify_deployment_v3.1.0.ps1        # Verificación post-despliegue (PowerShell)
├── validate_deployment.sh              # Validación completa
├── maintenance_v3.1.0.sh               # Script de mantenimiento
├── parking-api.service                  # Servicio systemd para API
├── parking-camera.service               # Servicio systemd para cámaras
├── parking-schedule-monitor.service     # Servicio systemd para programaciones
├── nginx_parking_altea.conf            # Configuración de Nginx
└── env_production.py                   # Configuración de entorno
```

## 🚀 Proceso de Despliegue

### Opción 1: Desde Linux/macOS

```bash
# Ejecutar configuración inicial (solo la primera vez)
chmod +x deploy/v3.1.0/setup_server_v3.1.0.sh
./deploy/v3.1.0/setup_server_v3.1.0.sh

# Ejecutar despliegue completo
chmod +x deploy/v3.1.0/deploy_v3.1.0_complete.sh
./deploy/v3.1.0/deploy_v3.1.0_complete.sh

# Verificar el despliegue
chmod +x deploy/v3.1.0/verify_deployment_v3.1.0.sh
./deploy/v3.1.0/verify_deployment_v3.1.0.sh
```

### Opción 2: Desde Windows (PowerShell)

```powershell
# Ejecutar despliegue completo
.\deploy\v3.1.0\deploy_v3.1.0_complete.ps1

# Verificar el despliegue
.\deploy\v3.1.0\verify_deployment_v3.1.0.ps1

# Opciones adicionales
.\deploy\v3.1.0\deploy_v3.1.0_complete.ps1 -SkipBackup -SkipTests
.\deploy\v3.1.0\deploy_v3.1.0_complete.ps1 -Force
```

### Parámetros PowerShell

- `-SkipBackup`: Saltar la creación de backup
- `-SkipTests`: Saltar los tests post-despliegue
- `-Force`: No pedir confirmación

## 🔧 Servicios del Sistema

### Servicios Systemd

| Servicio | Descripción | Puerto | Estado |
|----------|-------------|--------|--------|
| parking-api.service | API principal | 5000 | Activo |
| parking-camera.service | Servidor de cámaras | 5001 | Activo |
| parking-schedule-monitor.service | Monitor de programaciones | - | Activo |

### Comandos de Gestión

```bash
# Verificar estado de servicios
systemctl status parking-api.service
systemctl status parking-camera.service
systemctl status parking-schedule-monitor.service

# Reiniciar servicios
systemctl restart parking-api.service
systemctl restart parking-camera.service
systemctl restart parking-schedule-monitor.service

# Ver logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u parking-schedule-monitor.service -f
```

## 🌐 Endpoints

### Frontend
- **URL**: http://157.180.91.63
- **Puerto**: 80 (Nginx)

### API
- **URL**: http://157.180.91.63/api/
- **Puerto**: 5000 (proxied por Nginx)
- **Health Check**: http://157.180.91.63/health

## 🗄️ Base de Datos

### PostgreSQL
- **Host**: localhost
- **Puerto**: 5432
- **Base de datos**: parking_altea
- **Usuario**: parking
- **Contraseña**: parking123

### Comandos Útiles

```bash
# Conectar a la base de datos
sudo -u postgres psql -d parking_altea

# Verificar tablas
\dt

# Verificar usuarios
SELECT * FROM users;

# Verificar parkings
SELECT * FROM parkings;
```

## 🔒 Seguridad

### Usuarios del Sistema
- **Usuario**: parking
- **Contraseña**: parking123
- **Grupo**: parking

### Firewall
- **Puerto 22**: SSH
- **Puerto 80**: HTTP
- **Puerto 443**: HTTPS (cuando se configure)

### Permisos
- Archivos de aplicación: parking:parking
- Logs: parking:parking
- Backups: parking:parking

## 📊 Monitoreo

### Script de Monitoreo
```bash
# Ejecutar monitoreo
/usr/local/bin/monitor_parking.sh
```

### Logs Importantes
- **API**: /var/log/syslog (journalctl -u parking-api.service)
- **Nginx**: /var/log/nginx/parking_altea_*.log
- **Aplicación**: /opt/parking_altea/logs/

### Métricas del Sistema
```bash
# Uso de disco
df -h /opt/parking_altea

# Uso de memoria
free -h

# Procesos
ps aux | grep parking
```

## 🔄 Mantenimiento

### Script de Mantenimiento
```bash
# Ejecutar mantenimiento
chmod +x deploy/v3.1.0/maintenance_v3.1.0.sh
./deploy/v3.1.0/maintenance_v3.1.0.sh
```

**Funcionalidades:**
- Verificar estado del sistema
- Reiniciar servicios
- Ver logs en tiempo real
- Crear backup manual
- Limpiar logs antiguos
- Verificar espacio en disco
- Actualizar dependencias
- Verificar conectividad de cámaras
- Verificar base de datos
- Reiniciar sistema completo

### Backup Automático
- **Frecuencia**: Diaria
- **Retención**: 30 días
- **Ubicación**: /opt/backups/parking_altea/
- **Rotación**: Automática

## 🔙 Rollback

### Script de Rollback
```bash
# Ejecutar rollback
chmod +x deploy/v3.1.0/rollback_v3.1.0.sh
./deploy/v3.1.0/rollback_v3.1.0.sh
```

**Proceso:**
1. Listar backups disponibles
2. Seleccionar backup a restaurar
3. Detener servicios
4. Restaurar backup
5. Restaurar base de datos (si existe)
6. Iniciar servicios
7. Verificar funcionamiento

## 🧪 Testing

### Tests Post-Despliegue
```bash
# Ejecutar tests completos
python3 test/v3.1.0/test_admin_complete.py
```

### Tests Específicos
- **Autenticación**: Login, registro, cambio de contraseña
- **Administración**: Gestión de usuarios, asignación de parkings
- **API**: Endpoints principales
- **Base de datos**: Migraciones y consultas
- **Frontend**: Interfaz de usuario

## 📝 Logs y Debugging

### Verificar Logs
```bash
# Logs de la API
journalctl -u parking-api.service -f

# Logs de Nginx
tail -f /var/log/nginx/parking_altea_access.log
tail -f /var/log/nginx/parking_altea_error.log

# Logs del sistema
tail -f /var/log/syslog | grep parking
```

### Debugging
```bash
# Verificar conectividad
curl -f http://localhost:5000/health

# Verificar base de datos
sudo -u postgres psql -d parking_altea -c "SELECT version();"

# Verificar servicios
systemctl is-active parking-api.service
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# Configurar variables de entorno
export SECRET_KEY="tu-secret-key"
export JWT_SECRET_KEY="tu-jwt-secret"
export DATABASE_URL="postgresql://parking:parking123@localhost/parking_altea"
```

### Configuración de Nginx
- **Archivo**: /etc/nginx/sites-available/parking_altea
- **Enlace**: /etc/nginx/sites-enabled/parking_altea
- **Test**: nginx -t
- **Reload**: systemctl reload nginx

### Configuración de PostgreSQL
- **Archivo**: /etc/postgresql/*/main/postgresql.conf
- **Autenticación**: /etc/postgresql/*/main/pg_hba.conf
- **Restart**: systemctl restart postgresql

## 🚨 Troubleshooting

### Problemas Comunes

#### Error de conexión SSH
```bash
# Verificar conectividad
ping 157.180.91.63

# Verificar credenciales
ssh root@157.180.91.63
```

#### Servicio no inicia
```bash
# Verificar logs
journalctl -u parking-api.service --no-pager

# Verificar dependencias
systemctl list-dependencies parking-api.service
```

#### Base de datos no conecta
```bash
# Verificar PostgreSQL
systemctl status postgresql

# Verificar conexión
sudo -u postgres psql -d parking_altea
```

#### Frontend no carga
```bash
# Verificar Nginx
systemctl status nginx
nginx -t

# Verificar archivos estáticos
ls -la /opt/parking_altea/static/
```

## 📞 Soporte

### Información de Contacto
- **Servidor**: 157.180.91.63
- **Usuario SSH**: root
- **Documentación**: /docs/v3.1.0/

### Comandos de Emergencia
```bash
# Detener todos los servicios
systemctl stop parking-api.service parking-camera.service parking-schedule-monitor.service

# Reiniciar sistema
reboot

# Verificar espacio crítico
df -h

# Verificar memoria crítica
free -h
```

## 📈 Métricas de Rendimiento

### Objetivos
- **Tiempo de respuesta API**: < 500ms
- **Disponibilidad**: > 99.9%
- **Uso de CPU**: < 80%
- **Uso de memoria**: < 80%
- **Uso de disco**: < 80%

### Monitoreo Continuo
- **Uptime**: Monitoreado por systemd
- **Logs**: Rotación automática
- **Backups**: Automáticos diarios
- **Alertas**: Configurables por email/webhook

## 🔄 Actualizaciones

### Proceso de Actualización
1. **Crear backup del sistema actual**
2. **Detener servicios**
3. **Actualizar código**
4. **Ejecutar migraciones de BD**
5. **Reiniciar servicios**
6. **Verificar funcionamiento**

### Rollback Rápido
```bash
# Rollback automático en caso de error
./deploy/v3.1.0/rollback_v3.1.0.sh
```

---

**Última actualización**: 7 de enero de 2025  
**Versión**: v3.1.0  
**Estado**: Listo para despliegue  
**Compatibilidad**: Linux, macOS, Windows (PowerShell) 