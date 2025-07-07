#!/bin/bash

# Script de Validación de Despliegue v3.1.0 - Parking Altea
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

# Función para validar servicios systemd
validate_systemd_services() {
    log "Validando servicios systemd..."
    
    SERVICES=("parking-api" "parking-camera" "parking-schedule-monitor")
    ALL_ACTIVE=true
    
    for service in "${SERVICES[@]}"; do
        STATUS=$(remote_exec "systemctl is-active ${service}.service")
        if [ "$STATUS" = "active" ]; then
            success "Servicio $service: ACTIVO"
        else
            error "Servicio $service: INACTIVO"
            ALL_ACTIVE=false
        fi
        
        # Verificar que el servicio está habilitado
        ENABLED=$(remote_exec "systemctl is-enabled ${service}.service")
        if [ "$ENABLED" = "enabled" ]; then
            success "Servicio $service: HABILITADO"
        else
            warning "Servicio $service: NO HABILITADO"
        fi
    done
    
    if [ "$ALL_ACTIVE" = true ]; then
        success "Todos los servicios están activos"
        return 0
    else
        error "Algunos servicios no están activos"
        return 1
    fi
}

# Función para validar endpoints
validate_endpoints() {
    log "Validando endpoints..."
    
    ENDPOINTS=(
        "http://localhost:5000/health"
        "http://localhost:5000/api/parkings"
        "http://localhost:5000/api/auth/login"
        "http://localhost"
    )
    
    ALL_RESPONDING=true
    
    for endpoint in "${ENDPOINTS[@]}"; do
        if remote_exec "curl -f -s $endpoint" > /dev/null 2>&1; then
            success "Endpoint $endpoint: RESPONDE"
        else
            error "Endpoint $endpoint: NO RESPONDE"
            ALL_RESPONDING=false
        fi
    done
    
    # Verificar desde el exterior
    if curl -f -s "http://$REMOTE_HOST" > /dev/null 2>&1; then
        success "Frontend accesible desde exterior"
    else
        error "Frontend no accesible desde exterior"
        ALL_RESPONDING=false
    fi
    
    if [ "$ALL_RESPONDING" = true ]; then
        success "Todos los endpoints responden"
        return 0
    else
        error "Algunos endpoints no responden"
        return 1
    fi
}

# Función para validar base de datos
validate_database() {
    log "Validando base de datos..."
    
    # Verificar conexión
    if remote_exec "sudo -u postgres psql -d parking_altea -c 'SELECT version();'" > /dev/null 2>&1; then
        success "Conexión a PostgreSQL: OK"
    else
        error "Conexión a PostgreSQL: ERROR"
        return 1
    fi
    
    # Verificar tablas principales
    TABLES=("users" "parkings" "panels" "schedules" "camera_logs")
    ALL_TABLES_EXIST=true
    
    for table in "${TABLES[@]}"; do
        COUNT=$(remote_exec "sudo -u postgres psql -d parking_altea -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '$table';\"")
        if [ "$COUNT" -eq 1 ] 2>/dev/null; then
            success "Tabla $table: EXISTE"
        else
            error "Tabla $table: NO EXISTE"
            ALL_TABLES_EXIST=false
        fi
    done
    
    # Verificar datos mínimos
    USER_COUNT=$(remote_exec "sudo -u postgres psql -d parking_altea -t -c \"SELECT COUNT(*) FROM users;\"")
    if [ "$USER_COUNT" -gt 0 ] 2>/dev/null; then
        success "Usuarios en base de datos: $USER_COUNT"
    else
        warning "No hay usuarios en la base de datos"
    fi
    
    if [ "$ALL_TABLES_EXIST" = true ]; then
        success "Base de datos validada correctamente"
        return 0
    else
        error "Problemas con la base de datos"
        return 1
    fi
}

# Función para validar archivos críticos
validate_critical_files() {
    log "Validando archivos críticos..."
    
    CRITICAL_FILES=(
        "$REMOTE_DIR/api_server.py"
        "$REMOTE_DIR/camera_server.py"
        "$REMOTE_DIR/schedule_monitor_service.py"
        "$REMOTE_DIR/models.py"
        "$REMOTE_DIR/config.py"
        "$REMOTE_DIR/requirements.txt"
        "$REMOTE_DIR/static/index.html"
        "$REMOTE_DIR/static/assets/main.js"
        "/etc/systemd/system/parking-api.service"
        "/etc/systemd/system/parking-camera.service"
        "/etc/systemd/system/parking-schedule-monitor.service"
        "/etc/nginx/sites-available/parking_altea"
    )
    
    ALL_FILES_EXIST=true
    
    for file in "${CRITICAL_FILES[@]}"; do
        if remote_exec "[ -f $file ]"; then
            success "Archivo $file: EXISTE"
        else
            error "Archivo $file: NO EXISTE"
            ALL_FILES_EXIST=false
        fi
    done
    
    if [ "$ALL_FILES_EXIST" = true ]; then
        success "Todos los archivos críticos existen"
        return 0
    else
        error "Faltan archivos críticos"
        return 1
    fi
}

# Función para validar permisos
validate_permissions() {
    log "Validando permisos..."
    
    # Verificar propietario de archivos
    OWNER=$(remote_exec "stat -c '%U:%G' $REMOTE_DIR")
    if [ "$OWNER" = "parking:parking" ]; then
        success "Propietario correcto: $OWNER"
    else
        error "Propietario incorrecto: $OWNER (esperado: parking:parking)"
        return 1
    fi
    
    # Verificar permisos de ejecución
    if remote_exec "[ -x $REMOTE_DIR/api_server.py ]"; then
        success "Permisos de ejecución correctos"
    else
        error "Permisos de ejecución incorrectos"
        return 1
    fi
    
    # Verificar permisos de directorios
    DIRS=("$REMOTE_DIR/logs" "$REMOTE_DIR/data" "$REMOTE_DIR/uploads")
    for dir in "${DIRS[@]}"; do
        if remote_exec "[ -d $dir ] && [ -w $dir ]"; then
            success "Directorio $dir: ACCESIBLE"
        else
            error "Directorio $dir: NO ACCESIBLE"
            return 1
        fi
    done
    
    success "Permisos validados correctamente"
    return 0
}

# Función para validar funcionalidades específicas
validate_functionality() {
    log "Validando funcionalidades específicas..."
    
    # Verificar autenticación
    if remote_exec "curl -f -s http://localhost:5000/auth/login -X POST -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}'" > /dev/null 2>&1; then
        success "Endpoint de autenticación: FUNCIONAL"
    else
        warning "Endpoint de autenticación: PROBLEMA"
    fi
    
    # Verificar listado de parkings
    if remote_exec "curl -f -s http://localhost:5000/parkings" > /dev/null 2>&1; then
        success "Endpoint de parkings: FUNCIONAL"
    else
        warning "Endpoint de parkings: PROBLEMA"
    fi
    
    # Verificar archivos estáticos
    if remote_exec "curl -f -s http://localhost/static/js/main.js" > /dev/null 2>&1; then
        success "Archivos estáticos: ACCESIBLES"
    else
        error "Archivos estáticos: NO ACCESIBLES"
        return 1
    fi
    
    # Verificar configuración de Nginx
    if remote_exec "nginx -t" > /dev/null 2>&1; then
        success "Configuración de Nginx: VÁLIDA"
    else
        error "Configuración de Nginx: INVÁLIDA"
        return 1
    fi
    
    success "Funcionalidades validadas"
    return 0
}

# Función para validar recursos del sistema
validate_system_resources() {
    log "Validando recursos del sistema..."
    
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
    
    # Verificar procesos
    PROCESS_COUNT=$(remote_exec "ps aux | grep parking | grep -v grep | wc -l")
    success "Procesos de parking activos: $PROCESS_COUNT"
    
    return 0
}

# Función para ejecutar tests automatizados
run_automated_tests() {
    log "Ejecutando tests automatizados..."
    
    # Copiar tests al servidor si no existen
    if ! remote_exec "[ -d $REMOTE_DIR/tests ]"; then
        remote_exec "mkdir -p $REMOTE_DIR/tests"
        # Aquí se copiarían los tests si fuera necesario
    fi
    
    # Ejecutar tests si están disponibles
    if remote_exec "[ -f $REMOTE_DIR/tests/test_admin_complete.py ]"; then
        TEST_RESULT=$(remote_exec "cd $REMOTE_DIR && python3 tests/test_admin_complete.py")
        if [ $? -eq 0 ]; then
            success "Tests automatizados: PASARON"
        else
            error "Tests automatizados: FALLARON"
            return 1
        fi
    else
        warning "Tests automatizados no disponibles"
    fi
    
    return 0
}

# Función para generar reporte de validación
generate_validation_report() {
    log "Generando reporte de validación..."
    
    REPORT_FILE="/tmp/validation_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
Reporte de Validación de Despliegue v3.1.0
==========================================
Fecha: $(date)
Servidor: $REMOTE_HOST
Directorio: $REMOTE_DIR

RESUMEN DE VALIDACIÓN:
- Servicios Systemd: $(validate_systemd_services > /dev/null && echo "OK" || echo "ERROR")
- Endpoints: $(validate_endpoints > /dev/null && echo "OK" || echo "ERROR")
- Base de datos: $(validate_database > /dev/null && echo "OK" || echo "ERROR")
- Archivos críticos: $(validate_critical_files > /dev/null && echo "OK" || echo "ERROR")
- Permisos: $(validate_permissions > /dev/null && echo "OK" || echo "ERROR")
- Funcionalidades: $(validate_functionality > /dev/null && echo "OK" || echo "ERROR")
- Recursos del sistema: $(validate_system_resources > /dev/null && echo "OK" || echo "ERROR")
- Tests automatizados: $(run_automated_tests > /dev/null && echo "OK" || echo "ERROR")

DETALLES DEL SISTEMA:
$(remote_exec "systemctl status parking-api.service --no-pager")
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
    echo "🔍 Validación de Despliegue v3.1.0 - Parking Altea"
    echo "================================================="
    
    # Contador de errores
    ERROR_COUNT=0
    
    # Ejecutar validaciones
    validate_systemd_services || ERROR_COUNT=$((ERROR_COUNT + 1))
    validate_endpoints || ERROR_COUNT=$((ERROR_COUNT + 1))
    validate_database || ERROR_COUNT=$((ERROR_COUNT + 1))
    validate_critical_files || ERROR_COUNT=$((ERROR_COUNT + 1))
    validate_permissions || ERROR_COUNT=$((ERROR_COUNT + 1))
    validate_functionality || ERROR_COUNT=$((ERROR_COUNT + 1))
    validate_system_resources || ERROR_COUNT=$((ERROR_COUNT + 1))
    run_automated_tests || ERROR_COUNT=$((ERROR_COUNT + 1))
    
    # Generar reporte
    generate_validation_report
    
    echo ""
    echo "================================================="
    if [ $ERROR_COUNT -eq 0 ]; then
        success "🎉 Validación completada exitosamente!"
        success "El despliegue v3.1.0 está funcionando correctamente"
        exit 0
    else
        error "💥 Validación completada con $ERROR_COUNT errores"
        error "Revisar el reporte para más detalles"
        exit 1
    fi
}

# Ejecutar función principal
main "$@" 