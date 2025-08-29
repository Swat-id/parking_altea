# Comandos Copy-Paste para Despliegue v3.4.0

## 🖥️ **INFORMACIÓN SERVIDOR**
- **IP**: `157.180.91.63`
- **Usuario**: `root`
- **Backend**: `/opt/parking_altea`
- **Frontend**: `/var/www/parking_altea`

---

## 📋 **COMANDOS PARA COPIAR Y PEGAR**

### **1. CONECTAR AL SERVIDOR**
```bash
# Conectar por SSH
ssh root@157.180.91.63
```
**Qué hace**: Conecta al servidor de producción

---

### **2. VERIFICAR ESTADO INICIAL**
```bash
# Verificar servicios actuales
systemctl status parking-api parking-camera parking-schedule-monitor nginx

# Verificar endpoints funcionando
curl -s localhost:8080/health | jq
curl -s localhost:5000/ -I
curl -s localhost:5789/ -I

# Verificar espacio en disco
df -h /opt /var/www
```
**Qué hace**: Comprueba que todo funciona antes de empezar

---

### **3. CREAR BACKUP**
```bash
# Crear directorio backup
BACKUP_DIR="/opt/backups/v3_4_0_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup en: $BACKUP_DIR"

# Backup código backend
cd /opt
tar -czf "$BACKUP_DIR/code_backup.tar.gz" parking_altea/ --exclude=parking_altea/.git/objects --exclude=parking_altea/logs/*

# Backup frontend
tar -czf "$BACKUP_DIR/frontend_backup.tar.gz" /var/www/parking_altea/

# Backup configuraciones
cp /etc/systemd/system/parking-*.service "$BACKUP_DIR/" 2>/dev/null || mkdir -p "$BACKUP_DIR" && cp /etc/systemd/system/parking-*.service "$BACKUP_DIR/"

# Verificar backup
ls -lh "$BACKUP_DIR/"
```
**Qué hace**: Crea backup completo del sistema actual para poder volver atrás si hay problemas

---

### **4. DETENER SERVICIOS**
```bash
# Detener en orden específico
systemctl stop parking-schedule-monitor
systemctl stop parking-camera
systemctl stop parking-api
systemctl stop nginx

# Verificar que están detenidos
systemctl is-active parking-schedule-monitor parking-camera parking-api nginx || echo "Servicios detenidos"

# Esperar que terminen completamente
sleep 10
```
**Qué hace**: Para todos los servicios de forma segura para poder actualizar

---

### **5. ACTUALIZAR CÓDIGO**
```bash
# Ir al directorio del proyecto
cd /opt/parking_altea

# Actualizar Git
git fetch origin
git checkout v3.4.0
git pull origin v3.4.0

# Verificar rama actual
git branch
git log --oneline -3

# Verificar archivos nuevos v3.4.0
ls -la src/camera_message_processor.py src/panel_update_worker.py src/camera_server_v3_4_0.py
```
**Qué hace**: Descarga el código nuevo v3.4.0 con todas las mejoras

---

### **6. ACTUALIZAR DEPENDENCIAS PYTHON**
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar módulos nuevos
python -c "from camera_message_processor import CameraMessageProcessor; print('✅ CameraMessageProcessor OK')"
python -c "from panel_update_worker import PanelUpdateWorker; print('✅ PanelUpdateWorker OK')"
```
**Qué hace**: Instala las librerías Python necesarias para el nuevo código

---

### **7. COMPILAR FRONTEND**
```bash
# Ir al directorio frontend
cd /opt/parking_altea/client

# Instalar dependencias Node
npm install

# Compilar para producción
npm run build

# Verificar compilación
ls -la dist/ dist/assets/
```
**Qué hace**: Compila la interfaz web para producción

---

### **8. DESPLEGAR FRONTEND EN NGINX**
```bash
# Limpiar directorio nginx
rm -rf /var/www/parking_altea/*

# Copiar nueva versión
cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/

# Establecer permisos
chown -R www-data:www-data /var/www/parking_altea/
chmod -R 755 /var/www/parking_altea/

# Verificar archivos copiados
ls -la /var/www/parking_altea/
```
**Qué hace**: Instala la nueva interfaz web en el servidor nginx

---

### **9. CONFIGURAR NUEVO SERVICIO**
```bash
# Volver al directorio del proyecto
cd /opt/parking_altea

# Instalar servicio Panel Worker
cp deploy/parking-panel-worker.service /etc/systemd/system/

# Recargar configuración
systemctl daemon-reload

# Habilitar servicio
systemctl enable parking-panel-worker

# Verificar configuración
systemctl is-enabled parking-panel-worker
```
**Qué hace**: Configura el nuevo servicio que actualiza los paneles cada 2 minutos

---

### **10. MIGRAR CAMERA SERVER**
```bash
# Backup del camera server actual
cp src/camera_server.py "src/camera_server_backup_$(date +%Y%m%d_%H%M%S).py"

# Instalar nueva versión
cp src/camera_server_v3_4_0.py src/camera_server.py

# Verificar migración
head -10 src/camera_server.py | grep "v3.4.0"
```
**Qué hace**: Reemplaza el servidor de cámaras con la nueva versión mejorada

---

### **11. ARRANCAR SERVICIOS NUEVA ARQUITECTURA**
```bash
# 1. Iniciar Nginx
nginx -t
systemctl start nginx
sleep 3
systemctl status nginx

# 2. Iniciar Panel Worker
systemctl start parking-panel-worker
sleep 5
systemctl status parking-panel-worker

# 3. Iniciar Camera Server v3.4.0
systemctl start parking-camera
sleep 8
systemctl status parking-camera

# 4. Iniciar API Server
systemctl start parking-api
sleep 8
systemctl status parking-api
```
**Qué hace**: Arranca todos los servicios en el orden correcto

---

### **12. VERIFICAR QUE TODO FUNCIONA**
```bash
# Verificar servicios activos
systemctl is-active parking-api parking-camera parking-panel-worker nginx

# Verificar versión Camera Server
curl -s localhost:5000/camera/version | jq

# Verificar health endpoints
curl -s localhost:5000/camera/health | jq
curl -s localhost:8080/health | jq

# Verificar frontend
curl -s localhost:5789/ | head -5

# Test de mensaje cámara
curl -X POST localhost:5000/camera \
  -H "Content-Type: application/json" \
  -d '{"device":"TEST_DEPLOY","line":1,"Vehicle In":100,"Vehicle Out":50}' | jq
```
**Qué hace**: Comprueba que todo funciona correctamente

---

### **13. CONFIGURAR MONITOREO**
```bash
# Crear script de monitoreo
mkdir -p /opt/parking_altea/scripts
cat > /opt/parking_altea/scripts/monitor.sh << 'EOF'
#!/bin/bash
echo "=== Monitor $(date) ==="
systemctl status parking-* --no-pager | grep Active
curl -s localhost:5000/camera/health | jq -r '.status' 2>/dev/null || echo "Camera: ERROR"
curl -s localhost:8080/health | jq -r '.status' 2>/dev/null || echo "API: ERROR"
curl -s localhost:5789/ > /dev/null && echo "Frontend: OK" || echo "Frontend: ERROR"
free -h | grep Mem
journalctl -u parking-* --since "1 hour ago" | grep -ci error
EOF

# Hacer ejecutable
chmod +x /opt/parking_altea/scripts/monitor.sh

# Configurar cron (cada 5 minutos)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/parking_altea/scripts/monitor.sh >> /var/log/parking_monitor.log 2>&1") | crontab -

# Probar script
/opt/parking_altea/scripts/monitor.sh
```
**Qué hace**: Configura monitoreo automático cada 5 minutos

---

## ✅ **VERIFICACIÓN FINAL**

### **URLs para comprobar desde fuera:**
- **Frontend**: http://157.180.91.63:5789
- **API**: http://157.180.91.63:8080/health

### **Comandos finales de verificación:**
```bash
# Ver estado completo
echo "=== ESTADO FINAL ==="
systemctl status parking-* --no-pager | grep -E "(Active|Main PID)"

# Verificar versión desplegada
curl -s localhost:5000/camera/version | jq -r '.version'

# Ver logs recientes (no debe haber errores)
journalctl -u parking-* --since "10 minutes ago" | grep -i error | wc -l

# Verificar monitoreo funcionando
tail -f /var/log/parking_monitor.log
```

---

## 🚨 **ROLLBACK EN CASO DE PROBLEMAS**

### **Si algo falla, ejecutar estos comandos:**
```bash
# Detener servicios nuevos
systemctl stop parking-panel-worker parking-camera parking-api nginx

# Restaurar camera server anterior
cp src/camera_server_backup_*.py src/camera_server.py

# Restaurar frontend anterior
rm -rf /var/www/parking_altea/*
tar -xzf "$BACKUP_DIR/frontend_backup.tar.gz" -C /

# Arrancar servicios anteriores
systemctl start nginx parking-api parking-camera parking-schedule-monitor

# Verificar rollback
curl localhost:8080/health && echo "✅ Rollback OK"
```

---

## 📊 **COMANDOS ÚTILES POST-DESPLIEGUE**

### **Ver logs en tiempo real:**
```bash
journalctl -u parking-* -f
```

### **Reiniciar servicio específico:**
```bash
systemctl restart parking-api
systemctl restart parking-camera
systemctl restart parking-panel-worker
```

### **Monitor manual:**
```bash
/opt/parking_altea/scripts/monitor.sh
```

### **Ver estadísticas cámara:**
```bash
curl localhost:5000/camera/stats | jq
```

---

## ⏱️ **TIEMPO ESTIMADO**

- **Backup**: 2 minutos
- **Parada servicios**: 2 minutos  
- **Actualización código**: 3 minutos
- **Compilación frontend**: 5 minutos
- **Despliegue**: 3 minutos
- **Configuración**: 3 minutos
- **Arranque**: 5 minutos
- **Verificación**: 2 minutos

**TOTAL**: **~25 minutos**  
**Rollback**: **<5 minutos**

---

## 🎯 **RESULTADO ESPERADO**

Al finalizar tendrás:
- ✅ **Camera Server v3.4.0** con arquitectura separada
- ✅ **Panel Worker** actualizando paneles cada 2 minutos
- ✅ **Frontend actualizado** con nuevas funcionalidades
- ✅ **Monitoreo automático** cada 5 minutos
- ✅ **Backup completo** para rollback si necesario
- ✅ **URLs funcionando**: Frontend, API, Camera endpoints

**Estado**: ✅ **COMANDOS LISTOS PARA COPY-PASTE**
