# Resumen de Despliegue - Parking Altea v3.4.0

## 📋 Información General

**Servidor:** 157.180.91.63  
**Usuario:** root  
**Directorio del proyecto:** `/opt/parking_altea`  
**Rama de trabajo:** `v3.4.0`  

---

## 🌐 Arquitectura del Sistema

### **Frontend**
- **Puerto:** 5789
- **Servidor:** Nginx
- **Directorio web:** `/var/www/parking_altea/`
- **Configuración:** `/etc/nginx/sites-available/parking_altea`

### **Backend (API)**
- **Puerto:** 6001
- **Servicio:** `parking-api.service`
- **Directorio:** `/opt/parking_altea/src/`

### **Servicios Adicionales**
- **Panel Worker:** `parking-panel-worker.service`
- **Schedule Monitor:** `parking-schedule-monitor.service`
- **Camera Service:** `parking-camera.service` 
- **Alarm Monitor:** `parking-alarm-monitor.service`

---

## 🔄 Proceso de Despliegue Completo

### **1. Preparación Local**

```bash
# Verificar rama actual
git branch

# Asegurar que todos los cambios están commiteados
git status
git add .
git commit -m "Descripción de cambios"

# Subir cambios al repositorio
git push origin v3.4.0
```

### **2. Actualización del Código en el Servidor**

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Navegar al directorio del proyecto
cd /opt/parking_altea

# Verificar rama actual
git branch

# Obtener últimos cambios
git fetch origin v3.4.0

# Actualizar código local
git pull origin v3.4.0

# Verificar que se actualizó correctamente
git log --oneline -5
```

### **3. Despliegue del Backend**

#### **a) Parar servicios**
```bash
systemctl stop parking-api
systemctl stop parking-panel-worker
systemctl stop parking-schedule-monitor
systemctl stop parking-camera
systemctl stop parking-alarm-monitor
```

#### **b) Instalar dependencias (si es necesario)**
```bash
cd /opt/parking_altea
pip3 install -r requirements.txt
```

#### **c) Reiniciar servicios**
```bash
systemctl start parking-api
systemctl start parking-panel-worker
systemctl start parking-schedule-monitor
systemctl start parking-camera
systemctl start parking-alarm-monitor
```

#### **d) Verificar estado de servicios**
```bash
systemctl status parking-api
systemctl status parking-panel-worker
systemctl status parking-schedule-monitor
systemctl status parking-camera
systemctl status parking-alarm-monitor
```

### **4. Despliegue del Frontend**

#### **a) Compilar frontend**
```bash
cd /opt/parking_altea/client

# Instalar dependencias (si es necesario)
npm install

# Compilar para producción
npm run build
```

#### **b) Desplegar archivos compilados**
```bash
# ⚠️ CRÍTICO: Nginx está configurado para servir desde /var/www/parking_altea/
# NO copiar a /var/www/html/

# Limpiar directorio web actual
rm -rf /var/www/parking_altea/*

# Copiar archivos compilados al directorio correcto
cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/

# Verificar que se copiaron correctamente
ls -la /var/www/parking_altea/
ls -la /var/www/parking_altea/assets/
```

#### **c) Reiniciar Nginx**
```bash
# Reiniciar Nginx para limpiar cualquier caché
systemctl restart nginx

# Verificar estado
systemctl status nginx
```

---

## ✅ Validación del Despliegue

### **1. Verificar Puertos**

```bash
# Verificar que todos los puertos están activos
netstat -tlnp | grep -E "(5789|6001|8888)"

# O usar lsof
lsof -i :5789  # Frontend (Nginx)
lsof -i :6001  # Backend API
lsof -i :8888  # Panel Sender (si está activo)
```

### **2. Verificar Servicios Backend**

```bash
# Verificar logs de servicios
journalctl -u parking-api -f --lines=20
journalctl -u parking-panel-worker -f --lines=20
journalctl -u parking-schedule-monitor -f --lines=20
```

### **3. Verificar Frontend**

```bash
# Verificar que se sirve el archivo correcto
curl -s http://localhost:5789/ | grep 'index-.*\.js'

# Verificar que la API responde
curl -s http://localhost:6001/api/health || echo "API no responde"
```

### **4. Pruebas Funcionales**

1. **Acceder al frontend:** http://157.180.91.63:5789
2. **Login con usuario superadmin:** info@swat-id.com
3. **Verificar secciones principales:**
   - Dashboard
   - Parkings (crear, editar, borrar)
   - Paneles (crear, editar, borrar, enviar mensajes)
   - Programaciones
   - Estadísticas

---

## 🐛 Solución de Problemas Comunes

### **1. Frontend no se actualiza**

**Problema:** Los cambios de frontend no aparecen en el navegador.

**Solución:**
```bash
# Verificar directorio correcto
ls -la /var/www/parking_altea/

# Si está vacío o con archivos antiguos, recompilar y copiar
cd /opt/parking_altea/client
npm run build
rm -rf /var/www/parking_altea/*
cp -r dist/* /var/www/parking_altea/
systemctl restart nginx
```

### **2. API no responde**

**Problema:** Error 502 o 500 en llamadas a la API.

**Solución:**
```bash
# Verificar estado del servicio
systemctl status parking-api

# Ver logs de errores
journalctl -u parking-api --lines=50

# Reiniciar servicio
systemctl restart parking-api
```

### **3. Paneles no reciben mensajes**

**Problema:** Los paneles no muestran los mensajes enviados.

**Solución:**
```bash
# Verificar worker de paneles
systemctl status parking-panel-worker
journalctl -u parking-panel-worker --lines=30

# Verificar panelsender (puerto 8888)
lsof -i :8888
```

### **4. Base de datos no conecta**

**Problema:** Error de conexión a PostgreSQL.

**Solución:**
```bash
# Verificar PostgreSQL
systemctl status postgresql

# Verificar configuración de conexión
cat /opt/parking_altea/.env

# Probar conexión manual
psql -h localhost -U parking_user -d parking_db
```

---

## 📁 Directorios y Archivos Importantes

### **Configuraciones**
- **Nginx:** `/etc/nginx/sites-available/parking_altea`
- **Servicios:** `/etc/systemd/system/parking-*.service`
- **Variables de entorno:** `/opt/parking_altea/.env`

### **Logs**
- **Servicios:** `journalctl -u [nombre-servicio]`
- **Nginx:** `/var/log/nginx/access.log` y `/var/log/nginx/error.log`

### **Código**
- **Backend:** `/opt/parking_altea/src/`
- **Frontend compilado:** `/var/www/parking_altea/`
- **Frontend fuente:** `/opt/parking_altea/client/`

---

## 🔒 Comandos de Emergencia

### **Rollback rápido**
```bash
# Volver a commit anterior
cd /opt/parking_altea
git reset --hard HEAD~1

# Recompilar y redesplegar
cd client && npm run build
rm -rf /var/www/parking_altea/*
cp -r dist/* /var/www/parking_altea/
systemctl restart nginx
systemctl restart parking-api
```

### **Reinicio completo del sistema**
```bash
systemctl restart postgresql
systemctl restart nginx
systemctl restart parking-api
systemctl restart parking-panel-worker
systemctl restart parking-schedule-monitor
systemctl restart parking-camera
systemctl restart parking-alarm-monitor
```

---

## 📞 Contacto y Soporte

**Desarrollador:** SWAT-ID  
**Email:** info@swat-id.com  
**Documentación:** `/opt/parking_altea/docs/`

---

*Última actualización: Septiembre 2024*
*Versión del documento: 1.0*
