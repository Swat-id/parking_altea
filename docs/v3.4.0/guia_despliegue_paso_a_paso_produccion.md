# Guía de Despliegue Paso a Paso - Producción v3.4.0

## 📋 Información del Servidor

**Servidor de Producción**: `157.180.91.63`  
**Usuario**: `root`  
**Directorio del Proyecto**: `/opt/parking_altea`  
**Directorio Frontend**: `/var/www/parking_altea`  
**Puerto API**: `8080`  
**Puerto Camera**: `5000`  
**Puerto Frontend**: `5789`  
**Base de Datos**: `parking_db` (PostgreSQL)

---

## 🚀 **FASE 1: PREPARACIÓN Y VALIDACIÓN**

### **1.1 Conexión al Servidor**
```bash
# Conectar al servidor de producción
ssh root@157.180.91.63

# Verificar que estamos en el servidor correcto
hostname -I
# Debe mostrar: 157.180.91.63
```

### **1.2 Verificar Estado Actual del Sistema**
```bash
# Verificar servicios actuales
systemctl status parking-api
systemctl status parking-camera
systemctl status parking-schedule-monitor
systemctl status nginx

# Verificar endpoints actuales
curl -s localhost:8080/health | jq
curl -s localhost:5000/ -I
curl -s localhost:5789/ -I

# Verificar base de datos
psql parking_db -c "SELECT COUNT(*) FROM parkings;"
psql parking_db -c "SELECT COUNT(*) FROM users;"
```

### **1.3 Verificar Recursos del Sistema**
```bash
# Verificar espacio en disco
df -h /opt
df -h /var/www

# Verificar memoria disponible
free -h

# Verificar CPU
top -bn1 | head -5
```

---

## 💾 **FASE 2: BACKUP COMPLETO**

### **2.1 Crear Directorio de Backup**
```bash
# Crear directorio de backup con timestamp
BACKUP_DIR="/opt/backups/v3_4_0_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup directory: $BACKUP_DIR"
```

### **2.2 Backup del Código Backend**
```bash
# Ir al directorio del proyecto
cd /opt/parking_altea

# Crear backup del código completo
tar -czf "$BACKUP_DIR/parking_altea_code_backup.tar.gz" \
  --exclude=.git/objects \
  --exclude=logs/* \
  --exclude=__pycache__/* \
  --exclude=venv/lib \
  .

# Verificar backup
ls -lh "$BACKUP_DIR/parking_altea_code_backup.tar.gz"
```

### **2.3 Backup del Frontend**
```bash
# Backup del frontend actual
tar -czf "$BACKUP_DIR/frontend_backup.tar.gz" /var/www/parking_altea/

# Verificar backup frontend
ls -lh "$BACKUP_DIR/frontend_backup.tar.gz"
```

### **2.4 Backup de Configuraciones**
```bash
# Backup servicios systemd
cp -r /etc/systemd/system/parking-* "$BACKUP_DIR/systemd_services/"

# Backup configuración Nginx
cp /etc/nginx/sites-available/default "$BACKUP_DIR/nginx_default.conf"

# Backup base de datos (opcional)
pg_dump parking_db > "$BACKUP_DIR/parking_db_backup.sql"

echo "✅ Backup completo en: $BACKUP_DIR"
```

---

## 📦 **FASE 3: ACTUALIZACIÓN DEL CÓDIGO BACKEND**

### **3.1 Actualizar Repositorio Git**
```bash
# Ir al directorio del proyecto
cd /opt/parking_altea

# Verificar rama actual
git branch
git status

# Hacer fetch de todas las ramas
git fetch origin

# Cambiar a rama v3.4.0
git checkout v3.4.0
git pull origin v3.4.0

# Verificar que estamos en v3.4.0
git branch
git log --oneline -3
```

### **3.2 Verificar Archivos Nuevos**
```bash
# Verificar que los archivos nuevos están presentes
ls -la src/camera_message_processor.py
ls -la src/panel_update_worker.py
ls -la src/camera_server_v3_4_0.py
ls -la src/panel_worker_service.py
ls -la deploy/parking-panel-worker.service

# Verificar scripts de despliegue
ls -la deploy/v3.4.0/
```

### **3.3 Actualizar Dependencias Python**
```bash
# Activar virtual environment
cd /opt/parking_altea
source venv/bin/activate

# Verificar Python version
python --version

# Actualizar pip
pip install --upgrade pip

# Instalar/actualizar dependencias
pip install -r requirements.txt

# Verificar dependencias críticas
python -c "import flask, psycopg2, sqlalchemy, concurrent.futures; print('Dependencies OK')"

# Verificar nuevos módulos
python -c "from camera_message_processor import CameraMessageProcessor; print('CameraMessageProcessor OK')"
python -c "from panel_update_worker import PanelUpdateWorker; print('PanelUpdateWorker OK')"
```

---

## 🔧 **FASE 4: CONFIGURACIÓN DE SERVICIOS**

### **4.1 Instalar Nuevo Servicio Panel Worker**
```bash
# Copiar archivo de servicio
cp deploy/parking-panel-worker.service /etc/systemd/system/

# Verificar archivo copiado
cat /etc/systemd/system/parking-panel-worker.service

# Recargar systemd
systemctl daemon-reload

# Habilitar servicio (no iniciar aún)
systemctl enable parking-panel-worker

# Verificar configuración
systemctl status parking-panel-worker
```

### **4.2 Migrar Camera Server**
```bash
# Crear backup del camera server actual
cp src/camera_server.py src/camera_server_backup_$(date +%Y%m%d_%H%M%S).py

# Reemplazar con nueva versión
cp src/camera_server_v3_4_0.py src/camera_server.py

# Verificar reemplazo
head -10 src/camera_server.py | grep "v3.4.0"
```

---

## 🎨 **FASE 5: COMPILACIÓN Y DESPLIEGUE DEL FRONTEND**

### **5.1 Compilar Frontend**
```bash
# Ir al directorio del frontend
cd /opt/parking_altea/client

# Verificar Node.js y npm
node --version
npm --version

# Instalar dependencias (si es necesario)
npm install

# Compilar para producción
npm run build

# Verificar compilación
ls -la dist/
ls -la dist/assets/
```

### **5.2 Desplegar Frontend en Nginx**
```bash
# Detener nginx temporalmente
systemctl stop nginx

# Limpiar directorio anterior
rm -rf /var/www/parking_altea/*

# Copiar nueva build al directorio de nginx
cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/

# Verificar archivos copiados
ls -la /var/www/parking_altea/
ls -la /var/www/parking_altea/assets/

# Establecer permisos correctos
chown -R www-data:www-data /var/www/parking_altea/
chmod -R 755 /var/www/parking_altea/

# Verificar configuración Nginx
nginx -t

# Iniciar nginx
systemctl start nginx
systemctl status nginx
```

### **5.3 Verificar Frontend**
```bash
# Verificar que el frontend sirve correctamente
curl -I localhost:5789/

# Verificar archivos estáticos
curl -I localhost:5789/assets/

# Verificar desde exterior (opcional)
curl -I http://157.180.91.63:5789/
```

---

## 🚀 **FASE 6: ACTIVACIÓN DE LA NUEVA ARQUITECTURA**

### **6.1 Detener Servicios Actuales**
```bash
# Detener servicios en orden
systemctl stop parking-schedule-monitor
systemctl stop parking-camera
systemctl stop parking-api

# Verificar que están detenidos
systemctl is-active parking-schedule-monitor || echo "Detenido"
systemctl is-active parking-camera || echo "Detenido"
systemctl is-active parking-api || echo "Detenido"

# Esperar un momento
sleep 5
```

### **6.2 Iniciar Servicios Nueva Arquitectura**
```bash
# Ir al directorio del proyecto
cd /opt/parking_altea

# Iniciar Panel Worker primero
systemctl start parking-panel-worker
sleep 3

# Verificar Panel Worker
systemctl status parking-panel-worker
journalctl -u parking-panel-worker --lines=10

# Iniciar Camera Server v3.4.0
systemctl start parking-camera
sleep 5

# Verificar Camera Server
systemctl status parking-camera
journalctl -u parking-camera --lines=10

# Iniciar API Server
systemctl start parking-api
sleep 5

# Verificar API Server
systemctl status parking-api
journalctl -u parking-api --lines=10
```

### **6.3 Verificar Todos los Servicios**
```bash
# Estado de todos los servicios
systemctl status parking-*

# Verificar logs recientes sin errores
journalctl -u parking-* --since "5 minutes ago" | grep -i error | wc -l
```

---

## ✅ **FASE 7: VALIDACIÓN COMPLETA DEL DESPLIEGUE**

### **7.1 Verificar Endpoints v3.4.0**
```bash
# Verificar versión del Camera Server
curl -s localhost:5000/camera/version | jq
# Debe mostrar: {"version": "v3.4.0"}

# Verificar health del Camera Server
curl -s localhost:5000/camera/health | jq

# Verificar estadísticas del Camera Server
curl -s localhost:5000/camera/stats | jq

# Verificar API Server
curl -s localhost:8080/health | jq

# Verificar endpoints API críticos
curl -s localhost:8080/api/parkings | jq '.[0]'
```

### **7.2 Test de Procesamiento de Mensajes**
```bash
# Test de mensaje de cámara
curl -X POST localhost:5000/camera \
  -H "Content-Type: application/json" \
  -d '{
    "device": "DEPLOY_TEST_CAM",
    "line": 1,
    "Vehicle In": 100,
    "Vehicle Out": 50
  }' | jq

# Verificar respuesta rápida y formato v3.4.0
```

### **7.3 Verificar Panel Worker**
```bash
# Verificar logs del Panel Worker (debe mostrar actividad cada 2 min)
journalctl -u parking-panel-worker --since "5 minutes ago" | grep "Parking"

# Verificar estado del worker
systemctl is-active parking-panel-worker && echo "Panel Worker ACTIVO"
```

### **7.4 Test de Rendimiento**
```bash
# Test de latencia
time curl -s localhost:5000/camera/health > /dev/null
# Debe ser < 0.2 segundos

# Test de throughput básico
echo "Testing throughput..."
start_time=$(date +%s)
for i in {1..10}; do
  curl -s localhost:5000/camera/health > /dev/null &
done
wait
end_time=$(date +%s)
duration=$((end_time - start_time))
throughput=$((10 / duration))
echo "Throughput: $throughput req/s (objetivo: >20 req/s)"
```

### **7.5 Verificar Frontend Completo**
```bash
# Verificar frontend principal
curl -s localhost:5789/ | grep -i "parking" && echo "Frontend OK"

# Verificar acceso externo
curl -s http://157.180.91.63:5789/ | grep -i "parking" && echo "Frontend externo OK"

# Verificar assets
curl -I localhost:5789/assets/ 
```

---

## 📊 **FASE 8: CONFIGURACIÓN DE MONITOREO**

### **8.1 Configurar Logs Automáticos**
```bash
# Configurar rotación de logs
cat > /etc/logrotate.d/parking-system << 'EOF'
/opt/parking_altea/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

# Verificar configuración
logrotate -d /etc/logrotate.d/parking-system
```

### **8.2 Script de Monitoreo Automático**
```bash
# Crear directorio de scripts
mkdir -p /opt/parking_altea/scripts

# Crear script de monitoreo
cat > /opt/parking_altea/scripts/monitor_system.sh << 'EOF'
#!/bin/bash
echo "=== Parking System Monitor $(date) ==="

echo "📊 Services Status:"
systemctl status parking-* --no-pager | grep -E "(Active|Main PID)"

echo "📡 Endpoints Health:"
curl -s localhost:5000/camera/health | jq -r '.status' 2>/dev/null || echo "Camera: ERROR"
curl -s localhost:8080/health | jq -r '.status' 2>/dev/null || echo "API: ERROR"

echo "📈 Performance Metrics:"
curl -s localhost:5000/camera/stats | jq -r '.messages_processed' 2>/dev/null || echo "Stats: N/A"

echo "💾 Resources:"
free -h | grep Mem
df -h /opt/parking_altea | tail -1

echo "❌ Recent Errors:"
journalctl -u parking-* --since "1 hour ago" | grep -ci error

echo "🌐 Frontend Status:"
curl -s localhost:5789/ > /dev/null && echo "Frontend: OK" || echo "Frontend: ERROR"
EOF

# Hacer ejecutable
chmod +x /opt/parking_altea/scripts/monitor_system.sh

# Probar script
/opt/parking_altea/scripts/monitor_system.sh
```

### **8.3 Configurar Cron Job de Monitoreo**
```bash
# Añadir cron job para monitoreo cada 5 minutos
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/parking_altea/scripts/monitor_system.sh >> /var/log/parking_monitor.log 2>&1") | crontab -

# Verificar cron job
crontab -l | grep parking

# Crear archivo de log inicial
touch /var/log/parking_monitor.log
chmod 644 /var/log/parking_monitor.log
```

---

## 🔍 **FASE 9: VERIFICACIÓN FINAL Y MÉTRICAS**

### **9.1 Test Completo del Sistema**
```bash
# Test integrado de todo el flujo
echo "=== TEST COMPLETO SISTEMA v3.4.0 ==="

# 1. Verificar servicios
echo "1. Servicios:"
systemctl is-active parking-api && echo "  ✅ API Server"
systemctl is-active parking-camera && echo "  ✅ Camera Server"
systemctl is-active parking-panel-worker && echo "  ✅ Panel Worker"
systemctl is-active nginx && echo "  ✅ Nginx"

# 2. Verificar endpoints
echo "2. Endpoints:"
curl -s localhost:5000/camera/version | jq -r '.version' | grep "v3.4.0" && echo "  ✅ Camera v3.4.0"
curl -s localhost:8080/health | jq -r '.status' | grep -q "." && echo "  ✅ API Health"
curl -s localhost:5789/ | grep -q "parking" && echo "  ✅ Frontend"

# 3. Test de mensaje
echo "3. Test Mensaje:"
response=$(curl -s -X POST localhost:5000/camera \
  -H "Content-Type: application/json" \
  -d '{"device":"FINAL_TEST","line":1,"Vehicle In":100,"Vehicle Out":50}')
echo "$response" | jq -r '.status' | grep -q "ok\|success\|duplicate\|camera_not_found" && echo "  ✅ Procesamiento OK"

# 4. Verificar base de datos
echo "4. Base de Datos:"
psql parking_db -c "SELECT COUNT(*) FROM parkings;" | grep -q "[0-9]" && echo "  ✅ BD Accesible"

echo "=== FIN TEST COMPLETO ==="
```

### **9.2 Métricas de Rendimiento Final**
```bash
# Script de métricas de rendimiento
cat > /opt/parking_altea/scripts/performance_metrics.sh << 'EOF'
#!/bin/bash
echo "🚀 MÉTRICAS DE RENDIMIENTO v3.4.0"
echo "================================="

# Response Time
echo "📡 Response Time Test:"
response_time=$(time (curl -s localhost:5000/camera/health > /dev/null) 2>&1 | grep real | awk '{print $2}')
echo "  Camera Server: $response_time"

# Throughput
echo "🚀 Throughput Test:"
start_time=$(date +%s%3N)
for i in {1..20}; do curl -s localhost:5000/camera/health > /dev/null; done
end_time=$(date +%s%3N)
duration=$(( (end_time - start_time) ))
throughput=$(( 20000 / duration ))
echo "  20 requests in ${duration}ms = ${throughput} req/s"

# System Resources
echo "💾 System Resources:"
memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
disk_usage=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "  Memory: ${memory_usage}%"
echo "  Disk: ${disk_usage}%"
echo "  CPU: ${cpu_usage}%"

# Service Uptime
echo "⏰ Service Uptime:"
systemctl show parking-panel-worker --property=ActiveEnterTimestamp --value
echo "================================="
EOF

chmod +x /opt/parking_altea/scripts/performance_metrics.sh

# Ejecutar métricas
/opt/parking_altea/scripts/performance_metrics.sh
```

---

## 📋 **FASE 10: DOCUMENTACIÓN DEL DESPLIEGUE**

### **10.1 Generar Reporte Final**
```bash
# Crear reporte de despliegue
cat > /opt/parking_altea/deployment_report_v3_4_0.txt << EOF
REPORTE DE DESPLIEGUE SISTEMA v3.4.0
====================================
Fecha: $(date)
Servidor: $(hostname -I)
Usuario: $(whoami)

SERVICIOS DESPLEGADOS:
$(systemctl status parking-* --no-pager | grep -E "(Loaded|Active)")

VERSIONES:
Camera Server: $(curl -s localhost:5000/camera/version | jq -r '.version' 2>/dev/null || echo "Error")
API Server: $(curl -s localhost:8080/health | jq -r '.status' 2>/dev/null || echo "Error")

FRONTEND:
Frontend URL: http://157.180.91.63:5789
Status: $(curl -s localhost:5789/ > /dev/null && echo "OK" || echo "ERROR")

BACKUP LOCATION:
$BACKUP_DIR

LOGS:
API: journalctl -u parking-api
Camera: journalctl -u parking-camera  
Panel Worker: journalctl -u parking-panel-worker

MONITORING:
Script: /opt/parking_altea/scripts/monitor_system.sh
Log: /var/log/parking_monitor.log
Cron: */5 * * * *

====================================
EOF

echo "📋 Reporte generado: /opt/parking_altea/deployment_report_v3_4_0.txt"
cat /opt/parking_altea/deployment_report_v3_4_0.txt
```

### **10.2 Comandos Útiles Post-Despliegue**
```bash
# Crear script de comandos útiles
cat > /opt/parking_altea/scripts/useful_commands.sh << 'EOF'
#!/bin/bash
echo "🔧 COMANDOS ÚTILES SISTEMA v3.4.0"
echo "================================="
echo ""
echo "📊 ESTADO DE SERVICIOS:"
echo "  systemctl status parking-*"
echo "  systemctl restart parking-api"
echo "  systemctl restart parking-camera"
echo "  systemctl restart parking-panel-worker"
echo ""
echo "📡 VERIFICAR ENDPOINTS:"
echo "  curl localhost:5000/camera/version | jq"
echo "  curl localhost:5000/camera/health | jq"
echo "  curl localhost:5000/camera/stats | jq"
echo "  curl localhost:8080/health | jq"
echo ""
echo "📋 LOGS:"
echo "  journalctl -u parking-api -f"
echo "  journalctl -u parking-camera -f"
echo "  journalctl -u parking-panel-worker -f"
echo "  tail -f /var/log/parking_monitor.log"
echo ""
echo "🧪 TESTS:"
echo "  /opt/parking_altea/scripts/monitor_system.sh"
echo "  /opt/parking_altea/scripts/performance_metrics.sh"
echo ""
echo "🌐 FRONTEND:"
echo "  systemctl status nginx"
echo "  curl localhost:5789/"
echo "  ls -la /var/www/parking_altea/"
echo ""
echo "🗄️ BASE DE DATOS:"
echo "  psql parking_db -c 'SELECT COUNT(*) FROM parkings;'"
echo "  psql parking_db -c 'SELECT COUNT(*) FROM users;'"
echo ""
EOF

chmod +x /opt/parking_altea/scripts/useful_commands.sh
echo "📋 Comandos útiles: /opt/parking_altea/scripts/useful_commands.sh"
```

---

## 🎉 **VERIFICACIÓN FINAL DE ÉXITO**

### **Checklist Final:**
```bash
echo "✅ CHECKLIST FINAL DE DESPLIEGUE v3.4.0"
echo "========================================"

# Servicios
systemctl is-active parking-api >/dev/null && echo "✅ API Server ACTIVO" || echo "❌ API Server INACTIVO"
systemctl is-active parking-camera >/dev/null && echo "✅ Camera Server ACTIVO" || echo "❌ Camera Server INACTIVO"
systemctl is-active parking-panel-worker >/dev/null && echo "✅ Panel Worker ACTIVO" || echo "❌ Panel Worker INACTIVO"
systemctl is-active nginx >/dev/null && echo "✅ Nginx ACTIVO" || echo "❌ Nginx INACTIVO"

# Endpoints
curl -s localhost:5000/camera/version | jq -r '.version' | grep -q "v3.4.0" && echo "✅ Camera Server v3.4.0" || echo "❌ Camera Server versión incorrecta"
curl -s localhost:8080/health >/dev/null && echo "✅ API Health OK" || echo "❌ API Health ERROR"
curl -s localhost:5789/ >/dev/null && echo "✅ Frontend OK" || echo "❌ Frontend ERROR"

# Base de datos
psql parking_db -c "SELECT 1;" >/dev/null 2>&1 && echo "✅ Base de Datos OK" || echo "❌ Base de Datos ERROR"

# Archivos críticos
[ -f "/opt/parking_altea/scripts/monitor_system.sh" ] && echo "✅ Scripts de monitoreo OK" || echo "❌ Scripts faltantes"
[ -d "$BACKUP_DIR" ] && echo "✅ Backup realizado OK" || echo "❌ Backup no encontrado"

echo "========================================"
echo "🎯 DESPLIEGUE v3.4.0 COMPLETADO"
echo ""
echo "📡 URLs de acceso:"
echo "  Frontend: http://157.180.91.63:5789"
echo "  API: http://157.180.91.63:8080/health"
echo "  Camera: http://157.180.91.63:5000/camera/version"
echo ""
echo "📋 Monitoreo:"
echo "  tail -f /var/log/parking_monitor.log"
echo "  /opt/parking_altea/scripts/monitor_system.sh"
echo ""
echo "🔧 Soporte:"
echo "  /opt/parking_altea/scripts/useful_commands.sh"
echo "========================================"
```

---

## 🚨 **PLAN DE ROLLBACK (En caso de problemas)**

### **Rollback Rápido:**
```bash
# 1. Detener nuevos servicios
systemctl stop parking-panel-worker
systemctl stop parking-camera
systemctl stop parking-api

# 2. Restaurar camera server anterior
cp src/camera_server_backup_*.py src/camera_server.py

# 3. Restaurar frontend anterior
rm -rf /var/www/parking_altea/*
tar -xzf "$BACKUP_DIR/frontend_backup.tar.gz" -C /

# 4. Iniciar servicios anteriores
systemctl start parking-api
systemctl start parking-camera
systemctl start parking-schedule-monitor

# 5. Verificar rollback
curl localhost:8080/health
curl localhost:5789/
```

---

## 📞 **INFORMACIÓN DE SOPORTE**

**Archivos importantes:**
- Backup: `$BACKUP_DIR`
- Logs: `/var/log/parking_monitor.log`
- Scripts: `/opt/parking_altea/scripts/`
- Configuración: `/etc/systemd/system/parking-*`

**Comandos de emergencia:**
- Ver logs: `journalctl -u parking-* -f`
- Reiniciar servicios: `systemctl restart parking-*`
- Monitoreo: `/opt/parking_altea/scripts/monitor_system.sh`

**Despliegue completado exitosamente** ✅

---

**Documento creado**: 7 de Agosto de 2025  
**Versión**: v3.4.0  
**Servidor**: 157.180.91.63  
**Estado**: ✅ **LISTO PARA EJECUCIÓN**
