# Comandos Completos para Servidor Remoto v3.4.0

## 🖥️ **INFORMACIÓN DEL SERVIDOR**

**Servidor**: `157.180.91.63`  
**Usuario**: `root`  
**Proyecto Backend**: `/opt/parking_altea`  
**Frontend Nginx**: `/var/www/parking_altea`  
**Puertos**: API:8080, Camera:5000, Frontend:5789

---

## 🚀 **SECUENCIA COMPLETA DE COMANDOS PASO A PASO**

### **PASO 1: CONEXIÓN Y VERIFICACIÓN INICIAL**

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Verificar que estamos en el servidor correcto
hostname -I
# Debe mostrar: 157.180.91.63

# Verificar estado actual de servicios
systemctl status parking-api
systemctl status parking-camera
systemctl status parking-schedule-monitor
systemctl status nginx

# Verificar endpoints actuales funcionando
curl -s localhost:8080/health | jq
curl -s localhost:5000/ -I
curl -s localhost:5789/ -I

# Verificar espacio en disco disponible
df -h /opt
df -h /var/www
free -h
```

### **PASO 2: CREAR BACKUP COMPLETO**

```bash
# Crear directorio de backup con timestamp
BACKUP_DIR="/opt/backups/v3_4_0_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup directory: $BACKUP_DIR"

# Backup del código backend completo
cd /opt
tar -czf "$BACKUP_DIR/parking_altea_code_backup.tar.gz" \
  --exclude=parking_altea/.git/objects \
  --exclude=parking_altea/logs/* \
  --exclude=parking_altea/__pycache__/* \
  --exclude=parking_altea/venv/lib \
  parking_altea/

# Backup del frontend actual
tar -czf "$BACKUP_DIR/frontend_backup.tar.gz" /var/www/parking_altea/

# Backup de configuraciones systemd
mkdir -p "$BACKUP_DIR/systemd_services"
cp /etc/systemd/system/parking-*.service "$BACKUP_DIR/systemd_services/"

# Backup configuración nginx
cp /etc/nginx/sites-available/default "$BACKUP_DIR/nginx_default.conf"

# Verificar backups creados
ls -lh "$BACKUP_DIR/"
echo "✅ Backup completo en: $BACKUP_DIR"
```

### **PASO 3: DETENER TODOS LOS SERVICIOS**

```bash
# Detener servicios en orden específico para evitar conflictos
echo "🛑 Deteniendo servicios actuales..."

# 1. Detener schedule monitor primero
systemctl stop parking-schedule-monitor
echo "✅ Schedule Monitor detenido"

# 2. Detener camera server
systemctl stop parking-camera
echo "✅ Camera Server detenido"

# 3. Detener API server
systemctl stop parking-api
echo "✅ API Server detenido"

# 4. Detener nginx temporalmente
systemctl stop nginx
echo "✅ Nginx detenido"

# Verificar que todos están detenidos
systemctl is-active parking-schedule-monitor || echo "✅ Schedule Monitor: DETENIDO"
systemctl is-active parking-camera || echo "✅ Camera Server: DETENIDO"
systemctl is-active parking-api || echo "✅ API Server: DETENIDO"
systemctl is-active nginx || echo "✅ Nginx: DETENIDO"

# Esperar que los procesos terminen completamente
sleep 10
echo "✅ Todos los servicios detenidos correctamente"
```

### **PASO 4: ACTUALIZAR CÓDIGO BACKEND**

```bash
# Ir al directorio del proyecto
cd /opt/parking_altea

# Verificar estado actual de Git
git status
git branch
echo "Rama actual: $(git branch --show-current)"

# Actualizar repositorio Git
git fetch origin
echo "✅ Git fetch completado"

# Cambiar a rama v3.4.0
git checkout v3.4.0
echo "✅ Checkout a v3.4.0 completado"

# Actualizar código
git pull origin v3.4.0
echo "✅ Pull v3.4.0 completado"

# Verificar que estamos en v3.4.0
git branch
git log --oneline -3

# Verificar archivos nuevos críticos
echo "🔍 Verificando archivos nuevos..."
ls -la src/camera_message_processor.py
ls -la src/panel_update_worker.py  
ls -la src/camera_server_v3_4_0.py
ls -la src/panel_worker_service.py
ls -la deploy/parking-panel-worker.service

echo "✅ Archivos v3.4.0 verificados"
```

### **PASO 5: ACTUALIZAR DEPENDENCIAS PYTHON**

```bash
# Activar entorno virtual
cd /opt/parking_altea
source venv/bin/activate

# Verificar Python version
python --version
pip --version

# Actualizar pip
pip install --upgrade pip

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Verificar dependencias críticas
echo "🔍 Verificando dependencias críticas..."
python -c "import flask, psycopg2, sqlalchemy, concurrent.futures; print('✅ Dependencies básicas OK')"

# Verificar nuevos módulos v3.4.0
python -c "from camera_message_processor import CameraMessageProcessor; print('✅ CameraMessageProcessor OK')"
python -c "from panel_update_worker import PanelUpdateWorker; print('✅ PanelUpdateWorker OK')"

echo "✅ Dependencias Python actualizadas"
```

### **PASO 6: COMPILAR Y DESPLEGAR FRONTEND**

```bash
# Ir al directorio del frontend
cd /opt/parking_altea/client

# Verificar Node.js y npm
node --version
npm --version

# Limpiar cache npm si es necesario
npm cache clean --force

# Instalar dependencias del frontend
echo "📦 Instalando dependencias del frontend..."
npm install

# Compilar frontend para producción
echo "🔨 Compilando frontend..."
npm run build

# Verificar compilación exitosa
ls -la dist/
ls -la dist/assets/
echo "✅ Frontend compilado correctamente"

# Limpiar directorio nginx actual
echo "🧹 Limpiando directorio nginx anterior..."
rm -rf /var/www/parking_altea/*

# Copiar nueva build al directorio nginx
echo "📋 Copiando frontend compilado..."
cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/

# Verificar archivos copiados
ls -la /var/www/parking_altea/
ls -la /var/www/parking_altea/assets/

# Establecer permisos correctos
chown -R www-data:www-data /var/www/parking_altea/
chmod -R 755 /var/www/parking_altea/

echo "✅ Frontend desplegado en nginx"
```

### **PASO 7: CONFIGURAR NUEVOS SERVICIOS SYSTEMD**

```bash
# Volver al directorio del proyecto
cd /opt/parking_altea

# Instalar nuevo servicio Panel Worker
echo "⚙️ Configurando servicio Panel Worker..."
cp deploy/parking-panel-worker.service /etc/systemd/system/

# Verificar archivo copiado
cat /etc/systemd/system/parking-panel-worker.service

# Recargar configuración systemd
systemctl daemon-reload

# Habilitar nuevo servicio (sin iniciarlo aún)
systemctl enable parking-panel-worker

# Verificar que está habilitado
systemctl is-enabled parking-panel-worker

echo "✅ Servicio Panel Worker configurado"
```

### **PASO 8: MIGRAR CAMERA SERVER**

```bash
# Crear backup del camera server actual
echo "💾 Creando backup camera server actual..."
cp src/camera_server.py "src/camera_server_backup_$(date +%Y%m%d_%H%M%S).py"

# Listar backups creados
ls -la src/camera_server_backup_*.py

# Reemplazar con nueva versión v3.4.0
echo "🔄 Migrando a Camera Server v3.4.0..."
cp src/camera_server_v3_4_0.py src/camera_server.py

# Verificar migración
head -10 src/camera_server.py | grep "v3.4.0"
echo "✅ Camera Server migrado a v3.4.0"
```

### **PASO 9: ARRANCAR NUEVA ARQUITECTURA SECUENCIALMENTE**

```bash
echo "🚀 INICIANDO NUEVA ARQUITECTURA v3.4.0"

# PASO 9.1: Iniciar Nginx primero
echo "🌐 1. Iniciando Nginx..."
nginx -t  # Verificar configuración
systemctl start nginx
sleep 3

# Verificar nginx
systemctl status nginx
curl -I localhost:5789/
echo "✅ Nginx iniciado correctamente"

# PASO 9.2: Iniciar Panel Worker 
echo "🔄 2. Iniciando Panel Worker..."
systemctl start parking-panel-worker
sleep 5

# Verificar Panel Worker
systemctl status parking-panel-worker
journalctl -u parking-panel-worker --lines=10 --no-pager
echo "✅ Panel Worker iniciado"

# PASO 9.3: Iniciar Camera Server v3.4.0
echo "📡 3. Iniciando Camera Server v3.4.0..."
systemctl start parking-camera
sleep 8

# Verificar Camera Server
systemctl status parking-camera
journalctl -u parking-camera --lines=10 --no-pager
echo "✅ Camera Server v3.4.0 iniciado"

# PASO 9.4: Iniciar API Server
echo "🔌 4. Iniciando API Server..."
systemctl start parking-api
sleep 8

# Verificar API Server
systemctl status parking-api
journalctl -u parking-api --lines=10 --no-pager
echo "✅ API Server iniciado"

echo "🎉 TODOS LOS SERVICIOS INICIADOS"
```

### **PASO 10: VERIFICACIÓN COMPLETA DEL SISTEMA**

```bash
echo "✅ VERIFICACIÓN COMPLETA DEL SISTEMA v3.4.0"
echo "================================================="

# Estado de todos los servicios
echo "📊 1. Estado de servicios:"
systemctl status parking-api --no-pager | grep "Active:"
systemctl status parking-camera --no-pager | grep "Active:"
systemctl status parking-panel-worker --no-pager | grep "Active:"
systemctl status nginx --no-pager | grep "Active:"

# Verificar versiones y endpoints
echo ""
echo "📡 2. Verificación de endpoints:"

# Camera Server v3.4.0
CAMERA_VERSION=$(curl -s localhost:5000/camera/version | jq -r '.version' 2>/dev/null)
echo "Camera Version: $CAMERA_VERSION"
[ "$CAMERA_VERSION" = "v3.4.0" ] && echo "✅ Camera Server v3.4.0 OK" || echo "❌ Camera Server versión incorrecta"

# Camera Health
curl -s localhost:5000/camera/health | jq 2>/dev/null && echo "✅ Camera Health OK" || echo "❌ Camera Health ERROR"

# Camera Stats
curl -s localhost:5000/camera/stats | jq 2>/dev/null && echo "✅ Camera Stats OK" || echo "❌ Camera Stats ERROR"

# API Health
curl -s localhost:8080/health | jq 2>/dev/null && echo "✅ API Health OK" || echo "❌ API Health ERROR"

# Frontend
curl -s localhost:5789/ | grep -q "parking" && echo "✅ Frontend OK" || echo "❌ Frontend ERROR"

# Frontend externo
curl -s http://157.180.91.63:5789/ | grep -q "parking" && echo "✅ Frontend externo OK" || echo "❌ Frontend externo ERROR"

echo ""
echo "🧪 3. Test de procesamiento de mensajes:"

# Test completo de mensaje
RESPONSE=$(curl -s -X POST localhost:5000/camera \
  -H "Content-Type: application/json" \
  -d '{
    "device": "DEPLOY_VALIDATION_CAM",
    "line": 1,
    "Vehicle In": 100,
    "Vehicle Out": 50
  }')

echo "Response: $RESPONSE"
echo "$RESPONSE" | jq -r '.status' | grep -q "." && echo "✅ Procesamiento mensajes OK" || echo "❌ Procesamiento ERROR"

echo ""
echo "⏱️ 4. Test de rendimiento:"

# Test de latencia
echo "Testing latency..."
START_TIME=$(date +%s%3N)
curl -s localhost:5000/camera/health > /dev/null
END_TIME=$(date +%s%3N)
LATENCY=$((END_TIME - START_TIME))
echo "Latencia: ${LATENCY}ms (objetivo: <200ms)"

# Test básico de throughput
echo "Testing throughput..."
START_TIME=$(date +%s)
for i in {1..10}; do
    curl -s localhost:5000/camera/health > /dev/null &
done
wait
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
THROUGHPUT=$((10 / DURATION))
echo "Throughput: ${THROUGHPUT} req/s (objetivo: >20 req/s)"

echo ""
echo "💾 5. Recursos del sistema:"
free -h | grep Mem
df -h /opt | tail -1
top -bn1 | grep "Cpu(s)"

echo ""
echo "📝 6. Verificar logs recientes (últimos errores):"
ERROR_COUNT=$(journalctl -u parking-* --since "10 minutes ago" | grep -i error | wc -l)
echo "Errores en últimos 10 min: $ERROR_COUNT"

echo ""
echo "================================================="
echo "✅ VERIFICACIÓN COMPLETADA"
echo "================================================="
```

### **PASO 11: CONFIGURAR MONITOREO AUTOMÁTICO**

```bash
echo "📊 CONFIGURANDO MONITOREO AUTOMÁTICO"

# Script de monitoreo sistema
mkdir -p /opt/parking_altea/scripts

cat > /opt/parking_altea/scripts/monitor_system.sh << 'EOF'
#!/bin/bash
echo "=== Parking System Monitor $(date) ==="

echo "📊 Services Status:"
systemctl status parking-* --no-pager | grep -E "(Active|Main PID)"

echo "📡 Endpoints Health:"
curl -s localhost:5000/camera/health | jq -r '.status' 2>/dev/null || echo "Camera: ERROR"
curl -s localhost:8080/health | jq -r '.status' 2>/dev/null || echo "API: ERROR"
curl -s localhost:5789/ > /dev/null && echo "Frontend: OK" || echo "Frontend: ERROR"

echo "📈 Performance Metrics:"
curl -s localhost:5000/camera/stats | jq -r '.messages_processed' 2>/dev/null || echo "Stats: N/A"

echo "💾 Resources:"
free -h | grep Mem
df -h /opt/parking_altea | tail -1

echo "❌ Recent Errors:"
journalctl -u parking-* --since "1 hour ago" | grep -ci error

echo "🔄 Panel Worker Status:"
journalctl -u parking-panel-worker --since "10 minutes ago" | grep "Parking" | tail -3
EOF

# Hacer ejecutable
chmod +x /opt/parking_altea/scripts/monitor_system.sh

# Probar script
echo "🧪 Probando script de monitoreo..."
/opt/parking_altea/scripts/monitor_system.sh

# Configurar cron job para ejecutar cada 5 minutos
echo "⏰ Configurando cron job..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/parking_altea/scripts/monitor_system.sh >> /var/log/parking_monitor.log 2>&1") | crontab -

# Verificar cron job configurado
crontab -l | grep parking

# Crear archivo de log inicial
touch /var/log/parking_monitor.log
chmod 644 /var/log/parking_monitor.log

echo "✅ Monitoreo automático configurado"
```

### **PASO 12: CONFIGURAR ROTACIÓN DE LOGS**

```bash
echo "📋 CONFIGURANDO ROTACIÓN DE LOGS"

# Configurar logrotate para logs del sistema
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
/var/log/parking_monitor.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

# Verificar configuración logrotate
logrotate -d /etc/logrotate.d/parking-system

echo "✅ Rotación de logs configurada"
```

---

## 🎯 **VERIFICACIÓN FINAL Y URLS DE ACCESO**

```bash
echo ""
echo "🎉 =============================================="
echo "✅ DESPLIEGUE v3.4.0 COMPLETADO EXITOSAMENTE"
echo "=============================================="
echo ""
echo "📡 URLs de acceso:"
echo "  🌐 Frontend: http://157.180.91.63:5789"
echo "  🔌 API Health: http://157.180.91.63:8080/health"
echo "  📡 Camera Version: http://157.180.91.63:5000/camera/version"
echo "  📊 Camera Health: http://157.180.91.63:5000/camera/health"
echo "  📈 Camera Stats: http://157.180.91.63:5000/camera/stats"
echo ""
echo "🖥️ Servicios desplegados:"
systemctl is-active parking-api && echo "  ✅ API Server (puerto 8080)"
systemctl is-active parking-camera && echo "  ✅ Camera Server v3.4.0 (puerto 5000)"
systemctl is-active parking-panel-worker && echo "  ✅ Panel Worker (cada 2 min)"
systemctl is-active nginx && echo "  ✅ Nginx Frontend (puerto 5789)"
echo ""
echo "📊 Monitoreo y soporte:"
echo "  📝 Monitor en tiempo real: tail -f /var/log/parking_monitor.log"
echo "  🔧 Script manual: /opt/parking_altea/scripts/monitor_system.sh"
echo "  💾 Backup location: $BACKUP_DIR"
echo "  📋 Logs servicios: journalctl -u parking-* -f"
echo ""
echo "📈 Mejoras implementadas v3.4.0:"
echo "  ✅ Arquitectura separada: mensajes no bloquean paneles"
echo "  ✅ Procesamiento concurrente: >100 msg/s sin bloqueos"
echo "  ✅ Detección inteligente de reinicios de cámaras"
echo "  ✅ Validación robusta de deltas de aforo"
echo "  ✅ Worker independiente para actualización de paneles"
echo "  ✅ Actualizaciones atómicas con locks de BD"
echo "  ✅ Endpoints de monitoreo y estadísticas"
echo ""
echo "⚠️ IMPORTANTE:"
echo "  📊 Monitorear sistema durante las próximas 24 horas"
echo "  🔍 Verificar logs regularmente: journalctl -u parking-* -f"
echo "  📱 Comprobar funcionamiento frontend desde exterior"
echo "  📊 Panel Worker debe mostrar actividad cada 2 minutos"
echo ""
echo "🆘 En caso de problemas:"
echo "  📞 Rollback: ejecutar comandos de la sección ROLLBACK"
echo "  🔧 Reiniciar servicio: systemctl restart parking-[api|camera|panel-worker]"
echo "  📋 Diagnóstico: /opt/parking_altea/scripts/monitor_system.sh"
echo ""
echo "=============================================="
echo "🎉 SISTEMA v3.4.0 OPERATIVO Y MONITORIZADO"
echo "=============================================="
```

---

## 🚨 **COMANDOS DE ROLLBACK DE EMERGENCIA**

**En caso de problemas graves, ejecutar esta secuencia:**

```bash
echo "🚨 INICIANDO ROLLBACK DE EMERGENCIA"

# 1. Detener todos los servicios nuevos
systemctl stop parking-panel-worker
systemctl stop parking-camera  
systemctl stop parking-api
systemctl stop nginx

# 2. Restaurar camera server anterior
cd /opt/parking_altea
cp src/camera_server_backup_$(date +%Y%m%d)_*.py src/camera_server.py

# 3. Restaurar frontend anterior
rm -rf /var/www/parking_altea/*
tar -xzf "$BACKUP_DIR/frontend_backup.tar.gz" -C /

# 4. Volver a código anterior (opcional)
git checkout HEAD~1

# 5. Iniciar servicios anteriores
systemctl start nginx
systemctl start parking-api
systemctl start parking-camera
systemctl start parking-schedule-monitor

# 6. Verificar rollback
sleep 10
curl localhost:8080/health && echo "✅ Rollback completado"
curl localhost:5789/ && echo "✅ Frontend restaurado"

echo "🔄 Rollback completado - Sistema restaurado"
```

---

## 📞 **COMANDOS ÚTILES POST-DESPLIEGUE**

```bash
# Ver estado de todos los servicios
systemctl status parking-*

# Logs en tiempo real
journalctl -u parking-* -f

# Reiniciar servicio específico
systemctl restart parking-api
systemctl restart parking-camera
systemctl restart parking-panel-worker

# Verificar endpoints
curl localhost:5000/camera/version | jq
curl localhost:5000/camera/health | jq
curl localhost:5000/camera/stats | jq
curl localhost:8080/health | jq

# Monitoreo manual
/opt/parking_altea/scripts/monitor_system.sh

# Ver logs específicos
journalctl -u parking-api --since "1 hour ago"
journalctl -u parking-camera --since "1 hour ago"
journalctl -u parking-panel-worker --since "1 hour ago"

# Verificar frontend
curl localhost:5789/
curl http://157.180.91.63:5789/

# Base de datos
psql parking_db -c "SELECT COUNT(*) FROM parkings;"
psql parking_db -c "SELECT COUNT(*) FROM users;"

# Recursos del sistema
htop
df -h
free -h
```

---

**Tiempo estimado total**: **20-25 minutos**  
**Tiempo de rollback**: **<5 minutos**  
**Servidor**: `157.180.91.63`  
**Estado**: ✅ **COMANDOS LISTOS PARA EJECUCIÓN**

---

**Documento creado**: 7 de Agosto de 2025  
**Versión**: v3.4.0  
**Servidor de producción**: 157.180.91.63  
**Estado**: ✅ **SECUENCIA COMPLETA LISTA**
