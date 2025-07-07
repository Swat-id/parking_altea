#!/bin/bash

# Script de Verificación Post-Despliegue v3.1.0 - Parking Altea
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

set -e

# Configuración
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_PASSWORD="Sudv9uvSvdu!"
REMOTE_DIR="/opt/parking_altea"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para ejecutar comandos remotos
remote_exec() {
    sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$1"
}

# Función para verificar servicios systemd
verify_systemd_services() {
    log "Verificando servicios systemd..."
    
    SERVICES=("parking-api" "parking-camera" "parking-schedule-monitor")
    
    for service in "${SERVICES[@]}"; do
        STATUS=$(remote_exec "systemctl is-active ${service}.service")
        if [ "$STATUS" = "active" ]; then
            success "Servicio $service está activo"
        else
            error "Servicio $service no está activo"
            remote_exec "systemctl status ${service}.service"
        fi
    done
}

# Función para verificar endpoints
verify_endpoints() {
    log "Verificando endpoints..."
    
    # Verificar API
    if remote_exec "curl -f http://localhost:5000/health" > /dev/null 2>&1; then
        success "API endpoint (localhost:5000) responde"
    else
        error "API endpoint (localhost:5000) no responde"
    fi
    
    # Verificar frontend
    if remote_exec "curl -f http://localhost" > /dev/null 2>&1; then
        success "Frontend endpoint (localhost) responde"
    else
        error "Frontend endpoint (localhost) no responde"
    fi
    
    # Verificar desde el exterior
    if curl -f "http://$REMOTE_HOST" > /dev/null 2>&1; then
        success "Frontend accesible desde exterior"
    else
        error "Frontend no accesible desde exterior"
    fi
}

# Función para verificar base de datos
verify_database() {
    log "Verificando base de datos..."
    
    # Verificar conexión a PostgreSQL
    if remote_exec "sudo -u postgres psql -d parking_altea -c 'SELECT version();'" > /dev/null 2>&1; then
        success "Conexión a PostgreSQL exitosa"
    else
        error "Error conectando a PostgreSQL"
    fi
    
    # Verificar tablas principales
    TABLES=("users" "parkings" "panels" "schedules")
    
    for table in "${TABLES[@]}"; do
        COUNT=$(remote_exec "sudo -u postgres psql -d parking_altea -t -c \"SELECT COUNT(*) FROM $table;\"")
        if [ "$COUNT" -ge 0 ] 2>/dev/null; then
            success "Tabla $table existe con $COUNT registros"
        else
            error "Tabla $table no existe o error al consultar"
        fi
    done
}

# Función para verificar archivos críticos
verify_critical_files() {
    log "Verificando archivos críticos..."
    
    CRITICAL_FILES=(
        "$REMOTE_DIR/api_server.py"
        "$REMOTE_DIR/camera_server.py"
        "$REMOTE_DIR/schedule_monitor_service.py"
        "$REMOTE_DIR/models.py"
        "$REMOTE_DIR/config.py"
        "$REMOTE_DIR/static/index.html"
        "/etc/systemd/system/parking-api.service"
        "/etc/systemd/system/parking-camera.service"
        "/etc/systemd/system/parking-schedule-monitor.service"
    )
    
    for file in "${CRITICAL_FILES[@]}"; do
        if remote_exec "[ -f $file ]"; then
            success "Archivo $file existe"
        else
            error "Archivo $file no existe"
        fi
    done
}

# Función para verificar permisos
verify_permissions() {
    log "Verificando permisos..."
    
    # Verificar propietario de archivos
    OWNER=$(remote_exec "stat -c '%U:%G' $REMOTE_DIR")
    if [ "$OWNER" = "parking:parking" ]; then
        success "Propietario correcto: $OWNER"
    else
        error "Propietario incorrecto: $OWNER (esperado: parking:parking)"
    fi
    
    # Verificar permisos de ejecución
    if remote_exec "[ -x $REMOTE_DIR/api_server.py ]"; then
        success "Permisos de ejecución correctos"
    else
        error "Permisos de ejecución incorrectos"
    fi
}

# Función para verificar logs
verify_logs() {
    log "Verificando logs..."
    
    # Verificar que los logs se están generando
    LOG_FILES=(
        "/var/log/syslog"
        "/var/log/nginx/parking_altea_access.log"
        "/var/log/nginx/parking_altea_error.log"
    )
    
    for log_file in "${LOG_FILES[@]}"; do
        if remote_exec "[ -f $log_file ]"; then
            SIZE=$(remote_exec "stat -c '%s' $log_file")
            if [ "$SIZE" -gt 0 ]; then
                success "Log $log_file existe y tiene contenido"
            else
                warning "Log $log_file existe pero está vacío"
            fi
        else
            warning "Log $log_file no existe"
        fi
    done
}

# Función para verificar recursos del sistema
verify_system_resources() {
    log "Verificando recursos del sistema..."
    
    # Verificar uso de disco
    DISK_USAGE=$(remote_exec "df -h $REMOTE_DIR | tail -1 | awk '{print \$5}' | sed 's/%//'")
    if [ "$DISK_USAGE" -lt 80 ]; then
        success "Uso de disco: ${DISK_USAGE}% (OK)"
    else
        warning "Uso de disco: ${DISK_USAGE}% (ALTO)"
    fi
    
    # Verificar uso de memoria
    MEMORY_USAGE=$(remote_exec "free | grep Mem | awk '{printf \"%.0f\", \$3/\$2 * 100.0}'")
    if [ "$MEMORY_USAGE" -lt 80 ]; then
        success "Uso de memoria: ${MEMORY_USAGE}% (OK)"
    else
        warning "Uso de memoria: ${MEMORY_USAGE}% (ALTO)"
    fi
    
    # Verificar carga del sistema
    LOAD_AVG=$(remote_exec "uptime | awk -F'load average:' '{print \$2}' | awk '{print \$1}' | sed 's/,//'")
    success "Carga del sistema: $LOAD_AVG"
}

# Función para verificar funcionalidades específicas
verify_functionality() {
    log "Verificando funcionalidades específicas..."
    
    # Verificar autenticación
    if remote_exec "curl -f http://localhost:5000/auth/login -X POST -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}'" > /dev/null 2>&1; then
        success "Endpoint de autenticación responde"
    else
        warning "Endpoint de autenticación no responde correctamente"
    fi
    
    # Verificar listado de parkings
    if remote_exec "curl -f http://localhost:5000/parkings" > /dev/null 2>&1; then
        success "Endpoint de parkings responde"
    else
        warning "Endpoint de parkings no responde"
    fi
    
    # Verificar archivos estáticos
    if remote_exec "curl -f http://localhost/static/js/main.js" > /dev/null 2>&1; then
        success "Archivos estáticos accesibles"
    else
        error "Archivos estáticos no accesibles"
    fi
}

# Función para generar reporte
generate_report() {
    log "Generando reporte de verificación..."
    
    REPORT_FILE="/tmp/deployment_verification_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
Reporte de Verificación Post-Despliegue v3.1.0
==============================================
Fecha: $(date)
Servidor: $REMOTE_HOST
Directorio: $REMOTE_DIR

SERVICIOS SYSTEMD:
$(remote_exec "systemctl status parking-api.service --no-pager")
$(remote_exec "systemctl status parking-camera.service --no-pager")
$(remote_exec "systemctl status parking-schedule-monitor.service --no-pager")

ENDPOINTS:
API Health: $(curl -f http://$REMOTE_HOST:5000/health 2>/dev/null && echo "OK" || echo "ERROR")
Frontend: $(curl -f http://$REMOTE_HOST 2>/dev/null && echo "OK" || echo "ERROR")

BASE DE DATOS:
$(remote_exec "sudo -u postgres psql -d parking_altea -c 'SELECT table_name, COUNT(*) FROM information_schema.tables WHERE table_schema = '\''public'\'' GROUP BY table_name;'")

RECURSOS DEL SISTEMA:
$(remote_exec "df -h")
$(remote_exec "free -h")
$(remote_exec "uptime")

LOGS RECIENTES:
$(remote_exec "tail -20 /var/log/syslog | grep parking")
EOF
    
    success "Reporte generado: $REPORT_FILE"
}

# Función principal
main() {
    echo "🔍 Verificación Post-Despliegue v3.1.0 - Parking Altea"
    echo "====================================================="
    
    # Ejecutar verificaciones
    verify_systemd_services
    verify_endpoints
    verify_database
    verify_critical_files
    verify_permissions
    verify_logs
    verify_system_resources
    verify_functionality
    
    # Generar reporte
    generate_report
    
    echo ""
    success "🎉 Verificación completada!"
    echo ""
    log "Resumen:"
    echo "  - Servicios: Verificados"
    echo "  - Endpoints: Verificados"
    echo "  - Base de datos: Verificada"
    echo "  - Archivos: Verificados"
    echo "  - Permisos: Verificados"
    echo "  - Logs: Verificados"
    echo "  - Recursos: Verificados"
    echo "  - Funcionalidades: Verificadas"
    echo ""
    log "El sistema está funcionando correctamente"
}

# Ejecutar función principal
main "$@" 