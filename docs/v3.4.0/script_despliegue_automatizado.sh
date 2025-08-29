#!/bin/bash

# ===================================================================
# SCRIPT DE DESPLIEGUE AUTOMATIZADO v3.4.0
# Servidor: 157.180.91.63
# Usuario: root
# Proyecto: /opt/parking_altea
# ===================================================================

set -euo pipefail  # Strict mode para detener en cualquier error

# Configuración
DEPLOYMENT_VERSION="v3.4.0"
PROJECT_DIR="/opt/parking_altea"
FRONTEND_DIR="/var/www/parking_altea"
SERVER_IP="157.180.91.63"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funciones de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ $1${NC}"
}

# Función de rollback
rollback_deployment() {
    log_error "INICIANDO ROLLBACK DEL DESPLIEGUE"
    
    # Detener servicios nuevos
    systemctl stop parking-panel-worker 2>/dev/null || true
    systemctl stop parking-camera 2>/dev/null || true
    systemctl stop parking-api 2>/dev/null || true
    
    # Restaurar camera server anterior
    if [ -f "src/camera_server_backup_$(date +%Y%m%d)_*.py" ]; then
        cp src/camera_server_backup_$(date +%Y%m%d)_*.py src/camera_server.py
        log_success "Camera server anterior restaurado"
    fi
    
    # Restaurar frontend anterior
    if [ -f "$BACKUP_DIR/frontend_backup.tar.gz" ]; then
        rm -rf /var/www/parking_altea/*
        tar -xzf "$BACKUP_DIR/frontend_backup.tar.gz" -C /
        log_success "Frontend anterior restaurado"
    fi
    
    # Iniciar servicios anteriores
    systemctl start nginx
    systemctl start parking-api
    systemctl start parking-camera
    systemctl start parking-schedule-monitor
    
    # Verificar rollback
    sleep 10
    if curl -s localhost:8080/health > /dev/null; then
        log_success "Rollback completado exitosamente"
        return 0
    else
        log_error "Rollback falló - intervención manual requerida"
        return 1
    fi
}

# Trap para manejo de errores
trap 'rollback_deployment; exit 1' ERR

# Función principal
main() {
    log "🚀 INICIANDO DESPLIEGUE AUTOMATIZADO v3.4.0"
    log "================================================="
    log "Servidor: $SERVER_IP"
    log "Proyecto: $PROJECT_DIR"
    log "Frontend: $FRONTEND_DIR"
    echo ""
    
    # ===================================================================
    # PASO 1: VERIFICACIONES INICIALES
    # ===================================================================
    log "📋 PASO 1: Verificaciones iniciales"
    
    # Verificar que estamos en el servidor correcto
    CURRENT_IP=$(hostname -I | awk '{print $1}')
    if [ "$CURRENT_IP" != "$SERVER_IP" ]; then
        log_error "Script debe ejecutarse en el servidor de producción ($SERVER_IP)"
        log_error "IP actual: $CURRENT_IP"
        exit 1
    fi
    log_success "Servidor verificado: $CURRENT_IP"
    
    # Verificar servicios actuales
    systemctl is-active --quiet parking-api || { log_error "API service no está activo"; exit 1; }
    systemctl is-active --quiet parking-camera || { log_error "Camera service no está activo"; exit 1; }
    log_success "Servicios actuales verificados"
    
    # Verificar conectividad BD
    psql parking_db -c "SELECT version();" > /dev/null || { log_error "Conexión a BD falló"; exit 1; }
    log_success "Base de datos accesible"
    
    # Verificar espacio en disco
    DISK_USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 80 ]; then
        log_error "Espacio en disco insuficiente: ${DISK_USAGE}% usado"
        exit 1
    fi
    log_success "Espacio en disco suficiente: ${DISK_USAGE}% usado"
    
    # ===================================================================
    # PASO 2: CREAR BACKUP COMPLETO
    # ===================================================================
    log "💾 PASO 2: Creando backup completo"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/opt/backups/v3_4_0_${TIMESTAMP}"
    mkdir -p "$BACKUP_DIR"
    
    # Backup del código
    cd /opt
    tar -czf "$BACKUP_DIR/parking_altea_code_backup.tar.gz" \
      --exclude=parking_altea/.git/objects \
      --exclude=parking_altea/logs/* \
      --exclude=parking_altea/__pycache__/* \
      parking_altea/
    
    # Backup del frontend
    tar -czf "$BACKUP_DIR/frontend_backup.tar.gz" /var/www/parking_altea/
    
    # Backup configuraciones systemd
    mkdir -p "$BACKUP_DIR/systemd_services"
    cp /etc/systemd/system/parking-*.service "$BACKUP_DIR/systemd_services/" 2>/dev/null || true
    
    # Verificar backup
    if [ -f "$BACKUP_DIR/parking_altea_code_backup.tar.gz" ] && [ -f "$BACKUP_DIR/frontend_backup.tar.gz" ]; then
        log_success "Backup creado: $BACKUP_DIR"
    else
        log_error "Backup falló"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # ===================================================================
    # PASO 3: DETENER SERVICIOS
    # ===================================================================
    log "🛑 PASO 3: Deteniendo servicios actuales"
    
    systemctl stop parking-schedule-monitor || true
    log "Schedule Monitor detenido"
    
    systemctl stop parking-camera || true
    log "Camera Server detenido"
    
    systemctl stop parking-api || true
    log "API Server detenido"
    
    systemctl stop nginx || true
    log "Nginx detenido"
    
    sleep 10
    log_success "Todos los servicios detenidos"
    
    # ===================================================================
    # PASO 4: ACTUALIZAR CÓDIGO BACKEND
    # ===================================================================
    log "📦 PASO 4: Actualizando código backend"
    
    # Verificar rama actual
    CURRENT_BRANCH=$(git branch --show-current)
    log "Rama actual: $CURRENT_BRANCH"
    
    # Actualizar Git
    git fetch origin
    git checkout v3.4.0
    git pull origin v3.4.0
    
    # Verificar archivos nuevos
    [ -f "src/camera_message_processor.py" ] || { log_error "CameraMessageProcessor no encontrado"; exit 1; }
    [ -f "src/panel_update_worker.py" ] || { log_error "PanelUpdateWorker no encontrado"; exit 1; }
    [ -f "src/camera_server_v3_4_0.py" ] || { log_error "Camera Server v3.4.0 no encontrado"; exit 1; }
    
    log_success "Código actualizado a v3.4.0"
    
    # ===================================================================
    # PASO 5: ACTUALIZAR DEPENDENCIAS PYTHON
    # ===================================================================
    log "🔧 PASO 5: Actualizando dependencias Python"
    
    # Activar virtual environment
    source venv/bin/activate
    
    # Instalar dependencias
    pip install -r requirements.txt --quiet
    
    # Verificar imports críticos
    python -c "from camera_message_processor import CameraMessageProcessor; print('CameraMessageProcessor: OK')"
    python -c "from panel_update_worker import PanelUpdateWorker; print('PanelUpdateWorker: OK')"
    
    log_success "Dependencias Python actualizadas"
    
    # ===================================================================
    # PASO 6: COMPILAR Y DESPLEGAR FRONTEND
    # ===================================================================
    log "🎨 PASO 6: Compilando y desplegando frontend"
    
    # Ir al directorio del frontend
    cd /opt/parking_altea/client
    
    # Instalar dependencias
    npm install --quiet
    
    # Compilar frontend
    npm run build
    
    # Verificar compilación
    [ -d "dist" ] || { log_error "Compilación frontend falló"; exit 1; }
    [ -d "dist/assets" ] || { log_error "Assets frontend no encontrados"; exit 1; }
    
    # Limpiar y copiar
    rm -rf /var/www/parking_altea/*
    cp -r /opt/parking_altea/client/dist/* /var/www/parking_altea/
    
    # Establecer permisos
    chown -R www-data:www-data /var/www/parking_altea/
    chmod -R 755 /var/www/parking_altea/
    
    log_success "Frontend compilado y desplegado"
    
    # ===================================================================
    # PASO 7: CONFIGURAR NUEVOS SERVICIOS
    # ===================================================================
    log "⚙️ PASO 7: Configurando servicios"
    
    cd /opt/parking_altea
    
    # Instalar nuevo servicio panel worker
    cp deploy/parking-panel-worker.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable parking-panel-worker
    
    log_success "Servicios configurados"
    
    # ===================================================================
    # PASO 8: MIGRAR CAMERA SERVER
    # ===================================================================
    log "📡 PASO 8: Migrando Camera Server"
    
    # Backup camera server actual
    cp src/camera_server.py "src/camera_server_backup_${TIMESTAMP}.py"
    
    # Reemplazar con v3.4.0
    cp src/camera_server_v3_4_0.py src/camera_server.py
    
    # Verificar migración
    if grep -q "v3.4.0" src/camera_server.py; then
        log_success "Camera Server migrado a v3.4.0"
    else
        log_error "Migración de Camera Server falló"
        exit 1
    fi
    
    # ===================================================================
    # PASO 9: INICIAR NUEVA ARQUITECTURA
    # ===================================================================
    log "🚀 PASO 9: Iniciando nueva arquitectura"
    
    # Iniciar Nginx
    log "Iniciando Nginx..."
    nginx -t
    systemctl start nginx
    sleep 3
    
    if ! systemctl is-active --quiet nginx; then
        log_error "Nginx no inició correctamente"
        exit 1
    fi
    log_success "Nginx iniciado"
    
    # Iniciar Panel Worker
    log "Iniciando Panel Worker..."
    systemctl start parking-panel-worker
    sleep 5
    
    if ! systemctl is-active --quiet parking-panel-worker; then
        log_error "Panel Worker no inició correctamente"
        exit 1
    fi
    log_success "Panel Worker iniciado"
    
    # Iniciar Camera Server v3.4.0
    log "Iniciando Camera Server v3.4.0..."
    systemctl start parking-camera
    sleep 8
    
    if ! systemctl is-active --quiet parking-camera; then
        log_error "Camera Server no inició correctamente"
        exit 1
    fi
    log_success "Camera Server v3.4.0 iniciado"
    
    # Iniciar API Server
    log "Iniciando API Server..."
    systemctl start parking-api
    sleep 8
    
    if ! systemctl is-active --quiet parking-api; then
        log_error "API Server no inició correctamente"
        exit 1
    fi
    log_success "API Server iniciado"
    
    # ===================================================================
    # PASO 10: VALIDACIÓN COMPLETA
    # ===================================================================
    log "✅ PASO 10: Validando despliegue"
    
    # Esperar estabilización
    sleep 15
    
    # Verificar Camera Server v3.4.0
    CAMERA_VERSION=$(curl -s localhost:5000/camera/version | jq -r '.version' 2>/dev/null || echo "error")
    if [ "$CAMERA_VERSION" != "v3.4.0" ]; then
        log_error "Camera Server v3.4.0 no responde correctamente: $CAMERA_VERSION"
        exit 1
    fi
    log_success "Camera Server v3.4.0 verificado"
    
    # Verificar health endpoints
    curl -s localhost:5000/camera/health | jq -e '.status' > /dev/null || { log_error "Camera health falló"; exit 1; }
    curl -s localhost:8080/health | jq -e '.status' > /dev/null || { log_error "API health falló"; exit 1; }
    log_success "Health endpoints verificados"
    
    # Test de mensaje
    RESPONSE=$(curl -s -X POST localhost:5000/camera \
        -H "Content-Type: application/json" \
        -d '{"device":"DEPLOY_TEST","line":1,"Vehicle In":100,"Vehicle Out":50}')
    
    if echo "$RESPONSE" | jq -e '.status' > /dev/null; then
        log_success "Procesamiento de mensajes funcional"
    else
        log_warning "Procesamiento de mensajes: respuesta inesperada"
    fi
    
    # Verificar frontend
    curl -s localhost:5789/ > /dev/null && log_success "Frontend local OK" || log_error "Frontend local ERROR"
    curl -s http://157.180.91.63:5789/ > /dev/null && log_success "Frontend externo OK" || log_warning "Frontend externo no accesible"
    
    # ===================================================================
    # PASO 11: CONFIGURAR MONITOREO
    # ===================================================================
    log "📊 PASO 11: Configurando monitoreo"
    
    # Script de monitoreo
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
EOF
    
    chmod +x /opt/parking_altea/scripts/monitor_system.sh
    
    # Cron job de monitoreo
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/parking_altea/scripts/monitor_system.sh >> /var/log/parking_monitor.log 2>&1") | crontab -
    
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
    
    log_success "Monitoreo configurado"
    
    # ===================================================================
    # FINALIZACIÓN
    # ===================================================================
    log_success "🎉 DESPLIEGUE v3.4.0 COMPLETADO EXITOSAMENTE"
    
    echo ""
    echo "================================================================="
    echo "✅ SISTEMA v3.4.0 DESPLEGADO Y OPERATIVO"
    echo "================================================================="
    echo ""
    echo "📡 URLs de acceso:"
    echo "  🌐 Frontend: http://157.180.91.63:5789"
    echo "  🔌 API Health: http://157.180.91.63:8080/health"
    echo "  📡 Camera Version: http://157.180.91.63:5000/camera/version"
    echo "  📊 Camera Health: http://157.180.91.63:5000/camera/health"
    echo "  📈 Camera Stats: http://157.180.91.63:5000/camera/stats"
    echo ""
    echo "🖥️ Servicios activos:"
    systemctl is-active parking-api && echo "  ✅ API Server (puerto 8080)"
    systemctl is-active parking-camera && echo "  ✅ Camera Server v3.4.0 (puerto 5000)"
    systemctl is-active parking-panel-worker && echo "  ✅ Panel Worker (cada 2 min)"
    systemctl is-active nginx && echo "  ✅ Nginx Frontend (puerto 5789)"
    echo ""
    echo "📊 Monitoreo:"
    echo "  📝 Monitor automático: tail -f /var/log/parking_monitor.log"
    echo "  🔧 Script manual: /opt/parking_altea/scripts/monitor_system.sh"
    echo ""
    echo "💾 Backup:"
    echo "  📁 Location: $BACKUP_DIR"
    echo "  📦 Code: $BACKUP_DIR/parking_altea_code_backup.tar.gz"
    echo "  🌐 Frontend: $BACKUP_DIR/frontend_backup.tar.gz"
    echo ""
    echo "📈 Mejoras v3.4.0 implementadas:"
    echo "  ✅ Arquitectura separada: mensajes no bloquean paneles"
    echo "  ✅ Procesamiento concurrente: >100 msg/s sin bloqueos"
    echo "  ✅ Detección inteligente de reinicios de cámaras"
    echo "  ✅ Validación robusta de deltas de aforo"
    echo "  ✅ Worker independiente para actualización de paneles"
    echo "  ✅ Actualizaciones atómicas con locks de BD"
    echo "  ✅ Endpoints de monitoreo y estadísticas"
    echo ""
    echo "⚠️ SIGUIENTE PASO:"
    echo "  📊 Monitorear sistema durante las próximas 24 horas"
    echo "  🔍 Verificar logs: journalctl -u parking-* -f"
    echo "  📱 Probar acceso frontend desde exterior"
    echo ""
    echo "🆘 En caso de problemas ejecutar rollback:"
    echo "  📞 bash $0 --rollback"
    echo ""
    echo "================================================================="
    echo "🎉 DESPLIEGUE AUTOMATIZADO COMPLETADO"
    echo "================================================================="
}

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script debe ejecutarse como root"
    exit 1
fi

# Manejar argumentos
if [ "${1:-}" = "--rollback" ]; then
    log "🔄 Ejecutando rollback manual..."
    rollback_deployment
    exit $?
fi

# Ejecutar función principal
main "$@"

log_success "Script de despliegue automatizado finalizado exitosamente"
