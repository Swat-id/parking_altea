# Contexto y Despliegue - v3.1.0 Login System

## 📋 Información del Servidor Remoto

### **Configuración del Servidor**
- **IP**: 157.180.91.63
- **Usuario**: root
- **Contraseña**: Sudv9uvSvdu!
- **Sistema**: Linux (Ubuntu/Debian)
- **Directorio del proyecto**: `/root/parking_altea`

### **Servicios Activos**
- **API Server**: `parking-api.service` (Puerto 8000)
- **Camera Service**: `parking-camera.service` (Puerto 8001)
- **Schedule Monitor**: `parking-schedule-monitor.service`
- **Nginx**: Proxy reverso y servidor web
- **PostgreSQL**: Base de datos

### **Estructura de Directorios**
```
/root/parking_altea/
├── backend/           # Código Python del backend
├── client/           # Frontend React/Vite
├── server/           # Servicios Java y otros
├── deploy/           # Scripts de despliegue
├── docs/             # Documentación
└── test/             # Scripts de prueba
```

## 🔄 Proceso de Despliegue

### **1. Preparación Local**
```bash
# Asegurar que estamos en la rama correcta
git checkout v3.1.0_login
git pull origin v3.1.0_login

# Verificar estado del repositorio
git status
```

### **2. Despliegue al Servidor Remoto**
```bash
# Conectar al servidor
ssh root@157.180.91.63

# Navegar al directorio del proyecto
cd /root/parking_altea

# Actualizar repositorio
git fetch origin
git checkout v3.1.0_login
git pull origin v3.1.0_login
```

### **3. Migración de Base de Datos**
```bash
# Ejecutar migración v3.1.0
cd /root/parking_altea/src
python3 migrate_to_v3_1_0.py

# Verificar migración
python3 verify_migration_v3_1_0.py
```

### **4. Actualización de Backend**
```bash
# Reiniciar servicio de API
sudo systemctl restart parking-api.service

# Verificar estado
sudo systemctl status parking-api.service
```

### **5. Actualización de Frontend**
```bash
# Navegar al directorio del frontend
cd /root/parking_altea/client

# Instalar dependencias (si es necesario)
npm install

# Construir frontend
npm run build

# Verificar que se construyó correctamente
ls -la dist/
```

### **6. Reinicio de Servicios**
```bash
# Reiniciar todos los servicios
sudo systemctl restart parking-api.service
sudo systemctl restart parking-camera.service
sudo systemctl restart parking-schedule-monitor.service
sudo systemctl restart nginx

# Verificar estado de todos los servicios
sudo systemctl status parking-api.service
sudo systemctl status parking-camera.service
sudo systemctl status parking-schedule-monitor.service
sudo systemctl status nginx
```

## 🧪 Verificación Post-Despliegue

### **1. Verificar API**
```bash
# Probar endpoint de login
curl -X POST http://157.180.91.63:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@parking-altea.es", "password": "admin123!"}'

# Probar endpoint de usuarios (requiere autenticación)
curl -X GET http://157.180.91.63:8000/admin/users \
  -H "Authorization: Bearer <token>"
```

### **2. Verificar Frontend**
```bash
# Verificar que el frontend responde
curl -I http://157.180.91.63

# Verificar archivos estáticos
curl -I http://157.180.91.63/assets/
```

### **3. Verificar Base de Datos**
```bash
# Conectar a PostgreSQL
sudo -u postgres psql parking_altea

# Verificar tabla users
SELECT id, name, email, role, is_active FROM users;

# Verificar asignaciones
SELECT u.name, u.role, COUNT(up.parking_id) as parkings
FROM users u
LEFT JOIN user_parkings up ON u.id = up.user_id
GROUP BY u.id, u.name, u.role;
```

## 🚨 Rollback en Caso de Problemas

### **1. Rollback de Base de Datos**
```bash
cd /root/parking_altea/src
python3 rollback_migration_v3_1_0.py
```

### **2. Rollback de Código**
```bash
# Volver a la rama anterior
git checkout main
git pull origin main

# Reiniciar servicios
sudo systemctl restart parking-api.service
sudo systemctl restart parking-camera.service
sudo systemctl restart nginx
```

## 📝 Logs y Monitoreo

### **Logs de Servicios**
```bash
# Logs de API
sudo journalctl -u parking-api.service -f

# Logs de Camera Service
sudo journalctl -u parking-camera.service -f

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Logs de Aplicación**
```bash
# Logs de la API
tail -f /root/parking_altea/backend/api.log

# Logs de migración
tail -f /root/parking_altea/src/migration.log
```

## 🔧 Comandos Útiles

### **Gestión de Servicios**
```bash
# Ver estado de todos los servicios
sudo systemctl status parking-*

# Reiniciar todos los servicios
sudo systemctl restart parking-*

# Habilitar servicios al inicio
sudo systemctl enable parking-api.service
sudo systemctl enable parking-camera.service
sudo systemctl enable parking-schedule-monitor.service
```

### **Gestión de Base de Datos**
```bash
# Backup de base de datos
sudo -u postgres pg_dump parking_altea > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
sudo -u postgres psql parking_altea < backup_file.sql
```

### **Gestión de Archivos**
```bash
# Verificar espacio en disco
df -h

# Verificar permisos
ls -la /root/parking_altea/

# Limpiar logs antiguos
sudo journalctl --vacuum-time=7d
```

## 📊 Estado Actual del Despliegue

### **Última Actualización**
- **Fecha**: 7 de enero de 2025
- **Versión**: v3.1.0_login
- **Estado**: Sprint 1 COMPLETADO (100%) - Listo para despliegue

### **Tareas Completadas**
- [x] T1.1 - Script de migración de base de datos ✅ COMPLETADO
- [x] T1.2 - Actualización de modelos SQLAlchemy ✅ COMPLETADO
- [x] T1.3 - Crear datos iniciales ✅ COMPLETADO (Saltado - datos ya existen)
- [x] T1.4 - Script de verificación ✅ COMPLETADO
- [x] T1.5 - Tests de migración ✅ COMPLETADO
- [x] T1.6 - Script de asignación de parkings ✅ COMPLETADO

### **Archivos Listos para Despliegue**
- `src/migrate_to_v3_1_0.py` - Migración principal
- `src/rollback_migration_v3_1_0.py` - Rollback
- `src/verify_migration_v3_1_0.py` - Verificación mejorada
- `src/assign_parkings_to_users.py` - Asignación de parkings
- `src/models.py` - Modelos actualizados
- `test/v3.1.0/` - Tests completos

### **Próximas Tareas**
- [ ] Sprint 2: Backend - Sistema de Autenticación
- [ ] Sprint 3: Frontend - Sistema de Autenticación
- [ ] Sprint 4: Administración y Gestión

## 🔗 Enlaces Útiles

- **API Documentation**: http://157.180.91.63:8000/docs
- **Frontend**: http://157.180.91.63
- **GitHub Repository**: [URL del repositorio]
- **Documentación v3.1.0**: `/docs/v3.1.0/`

## 📞 Contacto y Soporte

- **Desarrollador**: [Nombre del desarrollador]
- **Email**: [Email de contacto]
- **Servidor**: root@157.180.91.63

---

**Nota**: Este documento se actualiza automáticamente con cada desarrollo. Mantener sincronizado con el estado real del servidor. 