# Contexto de Despliegue v3.1.0 - Parking Altea

## 📋 Resumen Ejecutivo

Este documento describe el contexto completo del despliegue de la versión v3.1.0 del sistema Parking Altea, incluyendo la arquitectura, requisitos, procedimientos y mantenimiento.

## 🎯 Objetivos del Despliegue

### Versión v3.1.0
- **Sistema de autenticación completo** con roles superadmin y user
- **Gestión de usuarios** con asignación de parkings
- **Dashboard de administración** con estadísticas
- **Perfil de usuario** con historial de actividad
- **Cambio de contraseña** seguro
- **Tests automatizados** completos

### Metas de Despliegue
- **Disponibilidad**: 99.9%
- **Tiempo de respuesta**: < 500ms
- **Escalabilidad**: Soporte para múltiples parkings
- **Seguridad**: Autenticación JWT y control de acceso
- **Mantenibilidad**: Logs centralizados y monitoreo

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │   Database      │
│   (React)       │◄──►│   (Flask)       │◄──►│   (PostgreSQL)  │
│   Port 80       │    │   Port 5000     │    │   Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Camera Server │    │   Schedule      │
│   (Reverse      │    │   (Python)      │    │   Monitor       │
│    Proxy)       │    │   Port 5001     │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Servicios Systemd

| Servicio | Descripción | Puerto | Usuario | Estado |
|----------|-------------|--------|---------|--------|
| parking-api.service | API principal Flask | 5000 | parking | Activo |
| parking-camera.service | Servidor de cámaras | 5001 | parking | Activo |
| parking-schedule-monitor.service | Monitor de programaciones | - | parking | Activo |
| nginx | Servidor web | 80/443 | root | Activo |
| postgresql | Base de datos | 5432 | postgres | Activo |

## 🖥️ Especificaciones del Servidor

### Hardware
- **Servidor**: 157.180.91.63
- **CPU**: Mínimo 2 cores
- **RAM**: Mínimo 4GB
- **Almacenamiento**: Mínimo 20GB SSD
- **Red**: Conexión estable a internet

### Software
- **Sistema Operativo**: Ubuntu 20.04 LTS o superior
- **Python**: 3.8+
- **Node.js**: 18+
- **PostgreSQL**: 12+
- **Nginx**: 1.18+
- **Git**: Última versión

### Dependencias Python
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
psycopg2-binary==2.9.7
requests==2.31.0
python-dotenv==1.0.0
```

### Dependencias Node.js
```
React 18+
Vite 4+
Tailwind CSS 3+
React Router 6+
Axios
```

## 📁 Estructura de Directorios

```
/opt/parking_altea/
├── api_server.py                    # Servidor API principal
├── camera_server.py                 # Servidor de cámaras
├── schedule_monitor_service.py      # Monitor de programaciones
├── models.py                        # Modelos de base de datos
├── config.py                        # Configuración
├── requirements.txt                 # Dependencias Python
├── static/                          # Frontend compilado
│   ├── index.html
│   ├── assets/
│   └── ...
├── logs/                            # Logs de aplicación
│   ├── api.log
│   ├── camera.log
│   └── schedule.log
├── data/                            # Datos de aplicación
├── uploads/                         # Archivos subidos
├── venv/                            # Entorno virtual Python
└── tests/                           # Tests automatizados

/opt/backups/parking_altea/
├── parking_altea_backup_*.tar.gz    # Backups del sistema
└── parking_altea_*_database.sql     # Backups de base de datos

/etc/systemd/system/
├── parking-api.service              # Servicio API
├── parking-camera.service           # Servicio cámaras
└── parking-schedule-monitor.service # Servicio programaciones

/etc/nginx/sites-available/
└── parking_altea                    # Configuración Nginx
```

## 🔐 Configuración de Seguridad

### Usuarios y Permisos
```bash
# Usuario del sistema
Usuario: parking
Contraseña: parking123
Grupo: parking

# Base de datos
Usuario: parking
Contraseña: parking123
Base de datos: parking_altea
```

### Firewall
```bash
# Puertos abiertos
Puerto 22: SSH
Puerto 80: HTTP
Puerto 443: HTTPS (futuro)
```

### Variables de Entorno Críticas
```bash
SECRET_KEY=parking-altea-prod-secret-key-v3.1.0
JWT_SECRET_KEY=parking-altea-jwt-secret-v3.1.0
DATABASE_URL=postgresql://parking:parking123@localhost/parking_altea
FLASK_ENV=production
```

## 🚀 Procedimiento de Despliegue

### Fase 1: Preparación
1. **Verificar requisitos del servidor**
2. **Crear backup del sistema actual** (si existe)
3. **Preparar scripts de despliegue**
4. **Verificar conectividad**

### Fase 2: Configuración Inicial
1. **Ejecutar setup_server_v3.1.0.sh**
2. **Instalar dependencias del sistema**
3. **Configurar PostgreSQL**
4. **Configurar Nginx**
5. **Crear usuario del sistema**

### Fase 3: Despliegue de Aplicación
1. **Ejecutar deploy_v3.1.0_complete.sh**
2. **Actualizar backend**
3. **Migrar base de datos**
4. **Compilar y desplegar frontend**
5. **Configurar servicios systemd**

### Fase 4: Verificación
1. **Ejecutar verify_deployment_v3.1.0.sh**
2. **Verificar servicios**
3. **Verificar endpoints**
4. **Ejecutar tests automatizados**
5. **Verificar funcionalidades críticas**

## 📊 Monitoreo y Logs

### Logs del Sistema
```bash
# Logs de servicios
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u parking-schedule-monitor.service -f

# Logs de Nginx
tail -f /var/log/nginx/parking_altea_access.log
tail -f /var/log/nginx/parking_altea_error.log

# Logs de aplicación
tail -f /opt/parking_altea/logs/api.log
tail -f /opt/parking_altea/logs/camera.log
```

### Métricas de Monitoreo
- **Uptime de servicios**: systemctl is-active
- **Uso de recursos**: htop, df, free
- **Conectividad**: curl health endpoints
- **Base de datos**: pg_stat_activity
- **Logs de error**: grep ERROR en logs

### Alertas
- **Servicios caídos**: systemd notifications
- **Espacio en disco**: < 20% libre
- **Memoria**: > 80% uso
- **CPU**: > 80% uso por más de 5 minutos

## 🔄 Mantenimiento

### Tareas Diarias
- **Verificar estado de servicios**
- **Revisar logs de error**
- **Verificar espacio en disco**
- **Crear backup automático**

### Tareas Semanales
- **Limpiar logs antiguos**
- **Verificar conectividad de cámaras**
- **Actualizar dependencias de seguridad**
- **Revisar métricas de rendimiento**

### Tareas Mensuales
- **Revisar backups**
- **Actualizar sistema operativo**
- **Verificar configuración de seguridad**
- **Revisar logs de auditoría**

## 🔙 Procedimiento de Rollback

### Criterios de Rollback
- **Errores críticos en producción**
- **Problemas de rendimiento severos**
- **Vulnerabilidades de seguridad**
- **Pérdida de datos**

### Proceso de Rollback
1. **Detener servicios**
2. **Seleccionar backup estable**
3. **Restaurar sistema**
4. **Restaurar base de datos**
5. **Iniciar servicios**
6. **Verificar funcionamiento**

### Backups Disponibles
- **Automáticos**: Diarios, retención 30 días
- **Manuales**: Antes de cada despliegue
- **Base de datos**: Separados del sistema

## 🧪 Testing y Validación

### Tests Automatizados
```bash
# Tests completos
python3 test/v3.1.0/test_admin_complete.py

# Tests específicos
python3 test/v3.1.0/test_admin_pages.py
python3 test/v3.1.0/test_frontend_protection_and_nav.py
```

### Validación Manual
- **Login de usuarios**
- **Gestión de usuarios (superadmin)**
- **Asignación de parkings**
- **Cambio de contraseña**
- **Dashboard de administración**
- **Perfil de usuario**

### Criterios de Aceptación
- **Todos los tests pasan**
- **Endpoints responden correctamente**
- **Interfaz de usuario funcional**
- **Base de datos accesible**
- **Logs sin errores críticos**

## 📈 Escalabilidad

### Escalado Vertical
- **Aumentar RAM**: Hasta 16GB
- **Aumentar CPU**: Hasta 8 cores
- **Aumentar almacenamiento**: Hasta 100GB

### Escalado Horizontal
- **Load balancer**: Nginx upstream
- **Múltiples instancias API**: Docker containers
- **Base de datos replicada**: PostgreSQL streaming
- **CDN**: Para archivos estáticos

### Límites Actuales
- **Usuarios concurrentes**: 100
- **Parkings**: 50
- **Cámaras por parking**: 10
- **Consultas por minuto**: 1000

## 🔧 Troubleshooting

### Problemas Comunes

#### Servicio no inicia
```bash
# Verificar logs
journalctl -u parking-api.service --no-pager

# Verificar dependencias
systemctl list-dependencies parking-api.service

# Verificar configuración
systemctl cat parking-api.service
```

#### Base de datos no conecta
```bash
# Verificar PostgreSQL
systemctl status postgresql

# Verificar conexión
sudo -u postgres psql -d parking_altea

# Verificar logs
tail -f /var/log/postgresql/postgresql-*.log
```

#### Frontend no carga
```bash
# Verificar Nginx
systemctl status nginx
nginx -t

# Verificar archivos estáticos
ls -la /opt/parking_altea/static/

# Verificar logs
tail -f /var/log/nginx/parking_altea_error.log
```

#### API no responde
```bash
# Verificar puerto
netstat -tlnp | grep 5000

# Verificar proceso
ps aux | grep api_server

# Verificar logs
tail -f /opt/parking_altea/logs/api.log
```

## 📞 Soporte y Contacto

### Información de Contacto
- **Servidor**: 157.180.91.63
- **Usuario SSH**: root
- **Documentación**: /docs/v3.1.0/
- **Logs**: /opt/parking_altea/logs/

### Comandos de Emergencia
```bash
# Detener todo
systemctl stop parking-api.service parking-camera.service parking-schedule-monitor.service

# Reiniciar todo
systemctl restart parking-api.service parking-camera.service parking-schedule-monitor.service

# Verificar estado crítico
/usr/local/bin/monitor_parking.sh
```

### Escalación
1. **Verificar logs y estado**
2. **Intentar reinicio de servicios**
3. **Verificar recursos del sistema**
4. **Contactar administrador**
5. **Considerar rollback si es necesario**

## 📝 Documentación Relacionada

- **Implementation Roadmap**: docs/v3.1.0/implementation_roadmap.md
- **API Documentation**: docs/api.md
- **Database Schema**: docs/database.md
- **Frontend Guide**: client/README.md
- **Testing Guide**: test/README.md

---

**Versión**: v3.1.0  
**Fecha**: 7 de enero de 2025  
**Estado**: Listo para despliegue  
**Última actualización**: 7 de enero de 2025 