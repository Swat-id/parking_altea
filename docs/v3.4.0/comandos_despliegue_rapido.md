# Comandos de Despliegue Rápido v3.4.0

## 🚀 Script de Ejecución Rápida

### **Información del Servidor:**
- **IP**: `157.180.91.63`
- **Usuario**: `root`
- **Proyecto**: `/opt/parking_altea`
- **Frontend**: `/var/www/parking_altea`

---

## 📋 **COMANDOS EJECUTABLES PASO A PASO**

### **1. Conexión y Preparación**
```bash
# Conectar al servidor
ssh root@157.180.91.63

# Crear backup
BACKUP_DIR="/opt/backups/v3_4_0_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cd /opt/parking_altea
tar -czf "$BACKUP_DIR/parking_altea_backup.tar.gz" --exclude=.git/objects --exclude=logs/* .
tar -czf "$BACKUP_DIR/frontend_backup.tar.gz" /var/www/parking_altea/
cp -r /etc/systemd/system/parking-* "$BACKUP_DIR/"
echo "✅ Backup en: $BACKUP_DIR"
```

### **2. Actualización del Código**
```bash
# Actualizar código backend
cd /opt/parking_altea
git fetch origin
git checkout v3.4.0
git pull origin v3.4.0

# Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Verificar nuevos módulos
python -c "from camera_message_processor import CameraMessageProcessor; print('✅ CameraMessageProcessor OK')"
python -c "from panel_update_worker import PanelUpdateWorker; print('✅ PanelUpdateWorker OK')"
```

### **3. Frontend**
```bash
# Compilar frontend
cd /opt/parking_altea/client
npm install
npm run build

# Desplegar en Nginx
systemctl stop nginx
rm -rf /var/www/parking_altea/*
cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/
chown -R www-data:www-data /var/www/parking_altea/
chmod -R 755 /var/www/parking_altea/
systemctl start nginx
```

### **4. Configurar Servicios**
```bash
# Instalar nuevo servicio
cd /opt/parking_altea
cp deploy/parking-panel-worker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable parking-panel-worker

# Migrar camera server
cp src/camera_server.py src/camera_server_backup_$(date +%Y%m%d_%H%M%S).py
cp src/camera_server_v3_4_0.py src/camera_server.py
```

### **5. Activar Nueva Arquitectura**
```bash
# Detener servicios actuales
systemctl stop parking-schedule-monitor
systemctl stop parking-camera  
systemctl stop parking-api
sleep 5

# Iniciar nuevos servicios
systemctl start parking-panel-worker
sleep 3
systemctl start parking-camera
sleep 5
systemctl start parking-api
sleep 5
```

### **6. Verificación Inmediata**
```bash
# Verificar servicios
systemctl status parking-*

# Verificar endpoints
curl -s localhost:5000/camera/version | jq
curl -s localhost:5000/camera/health | jq
curl -s localhost:8080/health | jq
curl -s localhost:5789/ | head -5

# Test de mensaje
curl -X POST localhost:5000/camera \
  -H "Content-Type: application/json" \
  -d '{"device":"DEPLOY_TEST","line":1,"Vehicle In":100,"Vehicle Out":50}' | jq
```

### **7. Configurar Monitoreo**
```bash
# Script de monitoreo
mkdir -p /opt/parking_altea/scripts
cat > /opt/parking_altea/scripts/monitor_system.sh << 'EOF'
#!/bin/bash
echo "=== $(date) ==="
systemctl status parking-* --no-pager | grep -E "(Active|Main PID)"
curl -s localhost:5000/camera/health | jq -r '.status' 2>/dev/null || echo "Camera: ERROR"
curl -s localhost:8080/health | jq -r '.status' 2>/dev/null || echo "API: ERROR"
curl -s localhost:5789/ > /dev/null && echo "Frontend: OK" || echo "Frontend: ERROR"
free -h | grep Mem
df -h /opt | tail -1
journalctl -u parking-* --since "1 hour ago" | grep -ci error
EOF

chmod +x /opt/parking_altea/scripts/monitor_system.sh

# Cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/parking_altea/scripts/monitor_system.sh >> /var/log/parking_monitor.log 2>&1") | crontab -
```

---

## ✅ **VERIFICACIÓN FINAL**

```bash
echo "🎯 VERIFICACIÓN FINAL v3.4.0"
echo "=========================="

# Servicios
systemctl is-active parking-api && echo "✅ API" || echo "❌ API"
systemctl is-active parking-camera && echo "✅ Camera" || echo "❌ Camera"  
systemctl is-active parking-panel-worker && echo "✅ Panel Worker" || echo "❌ Panel Worker"
systemctl is-active nginx && echo "✅ Nginx" || echo "❌ Nginx"

# Versión
curl -s localhost:5000/camera/version | jq -r '.version' | grep "v3.4.0" && echo "✅ v3.4.0" || echo "❌ Versión incorrecta"

# URLs de acceso
echo ""
echo "📡 URLs:"
echo "  Frontend: http://157.180.91.63:5789"
echo "  API: http://157.180.91.63:8080/health"
echo "  Camera: http://157.180.91.63:5000/camera/version"
echo ""
echo "📋 Monitoreo: tail -f /var/log/parking_monitor.log"
echo "🔧 Scripts: /opt/parking_altea/scripts/"
echo "💾 Backup: $BACKUP_DIR"
echo ""
echo "🎉 DESPLIEGUE v3.4.0 COMPLETADO"
```

---

## 🚨 **ROLLBACK RÁPIDO (Si hay problemas)**

```bash
# Rollback de emergencia
systemctl stop parking-panel-worker parking-camera parking-api
cp src/camera_server_backup_*.py src/camera_server.py
rm -rf /var/www/parking_altea/*
tar -xzf "$BACKUP_DIR/frontend_backup.tar.gz" -C /
systemctl start parking-api parking-camera parking-schedule-monitor
curl localhost:8080/health && echo "✅ Rollback OK"
```

---

## 📞 **Comandos de Diagnóstico**

```bash
# Logs en tiempo real
journalctl -u parking-* -f

# Estado detallado
/opt/parking_altea/scripts/monitor_system.sh

# Reiniciar servicio específico
systemctl restart parking-api
systemctl restart parking-camera
systemctl restart parking-panel-worker

# Verificar configuración
nginx -t
systemctl daemon-reload
```

---

**Ejecución estimada**: 15-20 minutos  
**Rollback time**: <5 minutos  
**Servidor**: 157.180.91.63  
**Estado**: ✅ Listo para ejecutar
