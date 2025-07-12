# Configuración del Sistema Parking Altea v3.1.0

## 📋 Resumen Ejecutivo

Este documento describe la configuración completa del sistema Parking Altea v3.1.0, incluyendo puertos fijos, integración con paneles y procedimientos de despliegue.

## 🏗️ Arquitectura del Sistema

### Componentes Principales
- **Frontend React**: Puerto 5789 (fijo)
- **API REST**: Puerto 6001
- **Servicio de Cámaras**: Puerto 6400
- **Monitor de Programaciones**: Proceso independiente
- **Base de Datos**: PostgreSQL (puerto 5432)

## 🔌 Configuración de Puertos

### Puerto 5789 - Frontend (FIJO)
- **Propósito**: Interfaz web de usuario
- **Tecnología**: React + Vite
- **Proxy**: Nginx
- **Configuración**: 
  - Desarrollo: `vite.config.js` - puerto 5789
  - Producción: Nginx sirve archivos estáticos
  - Proxy reverso para API en `/api/*`

### Puerto 6001 - API REST
- **Propósito**: API principal del sistema
- **Tecnología**: Flask + Gunicorn
- **Workers**: 3 procesos
- **Autenticación**: JWT

### Puerto 6400 - Servicio de Cámaras
- **Propósito**: Procesamiento de datos de cámaras
- **Tecnología**: Flask + Gunicorn
- **Workers**: 2 procesos
- **Integración**: Actualización automática de paneles

## 🌐 Configuración de Nginx

### Archivo de Configuración
```nginx
server {
    listen 5789;
    server_name localhost;
    
    root /var/www/parking_altea;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:6001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /socket.io/ {
        proxy_pass http://localhost:6001/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 🎯 Integración con Paneles

### Servicio de Comunicación
- **Archivo**: `src/panel_communication_service.py`
- **Clase**: `PanelCommunicationService`
- **Protocolo**: CP5200 (Java service)
- **Puerto**: 8888 (servicio interno)

### Funcionalidades
1. **Envío de mensajes directos**
2. **Actualización automática por ocupación**
3. **Programaciones temporales**
4. **Verificación de conectividad**

### Configuración de Paneles
```python
PANEL_API_URL = "http://127.0.0.1:8888/api/v1/panels/send"
```

## 🗄️ Base de Datos

### Configuración
- **Sistema**: PostgreSQL
- **Base de datos**: `parking_altea`
- **Usuario**: `parking`
- **Contraseña**: `parking123`
- **Puerto**: 5432

### Tablas Principales
- `users` - Usuarios del sistema
- `parkings` - Información de parkings
- `panels` - Configuración de paneles
- `accesses` - Configuración de cámaras
- `scheduled_messages` - Programaciones de mensajes

## 🚀 Procedimiento de Despliegue

### 1. Preparación del Servidor
```bash
# Verificar puertos en uso
netstat -tlnp | grep -E ':(5789|6001|6400)'

# Detener procesos conflictivos
sudo pkill -f "8000"  # Si hay frontend en puerto 8000
```

### 2. Actualización del Código
```bash
cd /opt/parking_altea
git fetch origin
git checkout v3.1.0_login
git pull origin v3.1.0_login
```

### 3. Instalación de Dependencias
```bash
# Backend
pip3 install -r requirements.txt

# Frontend
cd client
npm install
npm run build
```

### 4. Despliegue del Frontend
```bash
# Copiar archivos
cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/

# Configurar permisos
chown -R www-data:www-data /var/www/parking_altea
chmod -R 755 /var/www/parking_altea
```

### 5. Configuración de Nginx
```bash
# Copiar configuración
cp /opt/parking_altea/deploy/v3.1.0/nginx_parking_altea.conf /etc/nginx/sites-available/parking_altea

# Activar configuración
ln -sf /etc/nginx/sites-available/parking_altea /etc/nginx/sites-enabled/

# Verificar y reiniciar
nginx -t
systemctl restart nginx
```

### 6. Reinicio de Servicios
```bash
systemctl restart parking-api
systemctl restart parking-camera
systemctl restart parking-schedule-monitor
```

## 🔧 Verificación del Despliegue

### 1. Verificar Servicios
```bash
systemctl status parking-api
systemctl status parking-camera
systemctl status parking-schedule-monitor
systemctl status nginx
```

### 2. Verificar Puertos
```bash
netstat -tlnp | grep -E ':(5789|6001|6400)'
```

### 3. Probar API
```bash
curl -I http://localhost:6001/
curl -I http://localhost:5789/
curl -I http://localhost:5789/api/parkings/status
```

### 4. Verificar Paneles
```bash
# Probar conectividad
ping -c 3 172.20.5.50

# Verificar estado en base de datos
psql -h localhost -U parking -d parking_altea -c "SELECT id, name, ip, status FROM panels;"
```

## 🐛 Troubleshooting

### Problema: Puerto 5789 ocupado
```bash
# Identificar proceso
lsof -i :5789

# Detener proceso
sudo pkill -f "proceso_identificado"

# Verificar que está libre
netstat -tlnp | grep :5789
```

### Problema: API no responde
```bash
# Verificar logs
journalctl -u parking-api -f

# Verificar base de datos
psql -h localhost -U parking -d parking_altea -c "SELECT 1;"

# Reiniciar servicio
systemctl restart parking-api
```

### Problema: Paneles no responden
```bash
# Verificar conectividad
ping -c 3 IP_PANEL

# Verificar servicio Java
ps aux | grep java

# Verificar logs
tail -f /opt/parking_altea/logs/java-panel-service.log
```

## 📊 Monitoreo

### Logs Importantes
- **API**: `journalctl -u parking-api -f`
- **Cámaras**: `journalctl -u parking-camera -f`
- **Nginx**: `tail -f /var/log/nginx/access.log`
- **Paneles**: `/opt/parking_altea/logs/java-panel-service.log`

### Métricas Clave
- **Uptime de servicios**
- **Tiempo de respuesta de API**
- **Conectividad de paneles**
- **Uso de memoria y CPU**

## 🔒 Seguridad

### Configuraciones de Seguridad
- **Autenticación JWT** para API
- **CORS configurado** para dominio específico
- **Contraseñas seguras** en base de datos
- **Logs de auditoría** para acciones críticas

### Recomendaciones
- **Cambiar contraseñas por defecto**
- **Configurar firewall** para puertos específicos
- **Mantener actualizaciones** de seguridad
- **Backup regular** de base de datos

## 📝 Notas de Versión v3.1.0

### Nuevas Funcionalidades
- ✅ Gestión mejorada de usuarios (desactivar vs eliminar)
- ✅ Asignación de parkings con selección previa
- ✅ Edición de cámaras en parkings existentes
- ✅ Protección de API con autenticación
- ✅ Visibilidad de barra lateral solo en páginas autenticadas
- ✅ Resultados detallados de ping en paneles
- ✅ Información completa del último mensaje en paneles

### Correcciones
- 🔧 Puerto 5789 fijo para frontend
- 🔧 Eliminación de duplicación de frontends
- 🔧 Corrección de importaciones en panel_client.py
- 🔧 Configuración correcta de base de datos

### Configuración Final
- **Frontend**: Puerto 5789 (fijo)
- **API**: Puerto 6001
- **Cámaras**: Puerto 6400
- **Base de datos**: PostgreSQL (puerto 5432)
- **Paneles**: Protocolo CP5200 (puerto 8888 interno) 