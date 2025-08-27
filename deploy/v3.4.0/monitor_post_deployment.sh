#!/bin/bash
"""
Script de monitoreo post-despliegue para Sistema v3.4.0
Valida el funcionamiento del sistema después del despliegue
"""

set -euo pipefail

# Configuración
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

MONITOR_DURATION=${1:-300}  # 5 minutos por defecto
CHECK_INTERVAL=30           # Cada 30 segundos
LOG_FILE="/var/log/parking_post_deployment_monitor.log"

# Contadores
TOTAL_CHECKS=0
SUCCESSFUL_CHECKS=0
FAILED_CHECKS=0

# Función de logging
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
    SUCCESSFUL_CHECKS=$((SUCCESSFUL_CHECKS + 1))
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️ $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')] ℹ️ $1${NC}" | tee -a "$LOG_FILE"
}

# Función para verificar servicios
check_services() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando estado de servicios..."
    
    # Verificar servicios críticos
    local services=("parking-api" "parking-camera" "parking-panel-worker")
    local all_ok=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service está activo"
        else
            log_error "$service NO está activo"
            all_ok=false
        fi
    done
    
    if $all_ok; then
        log_success "Todos los servicios críticos están activos"
    else
        log_error "Algunos servicios críticos están fallando"
    fi
}

# Función para verificar endpoints
check_endpoints() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando endpoints del sistema..."
    
    # Camera Server v3.4.0
    if curl -s localhost:5000/camera/version | jq -e '.version == "v3.4.0"' >/dev/null 2>&1; then
        log_success "Camera Server v3.4.0 respondiendo correctamente"
    else
        log_error "Camera Server v3.4.0 no responde o versión incorrecta"
    fi
    
    # Health endpoints
    if curl -s localhost:5000/camera/health | jq -e '.status' >/dev/null 2>&1; then
        log_success "Camera health endpoint OK"
    else
        log_error "Camera health endpoint falló"
    fi
    
    if curl -s localhost:8080/health | jq -e '.status' >/dev/null 2>&1; then
        log_success "API health endpoint OK"
    else
        log_error "API health endpoint falló"
    fi
    
    # Stats endpoint
    if curl -s localhost:5000/camera/stats | jq -e '.version' >/dev/null 2>&1; then
        log_success "Camera stats endpoint OK"
    else
        log_warning "Camera stats endpoint no responde (puede ser normal)"
    fi
}

# Función para verificar rendimiento
check_performance() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando métricas de rendimiento..."
    
    # Test de latencia
    local start_time=$(date +%s%3N)
    if curl -s localhost:5000/camera/health >/dev/null 2>&1; then
        local end_time=$(date +%s%3N)
        local latency=$((end_time - start_time))
        
        if [ "$latency" -lt 200 ]; then
            log_success "Latencia OK: ${latency}ms (<200ms objetivo)"
        elif [ "$latency" -lt 500 ]; then
            log_warning "Latencia alta: ${latency}ms (objetivo <200ms)"
        else
            log_error "Latencia crítica: ${latency}ms (muy por encima del objetivo)"
        fi
    else
        log_error "No se pudo medir latencia - endpoint no responde"
    fi
    
    # Test de throughput básico
    log_info "Ejecutando test de throughput básico..."
    local throughput_start=$(date +%s)
    local requests=10
    
    for i in $(seq 1 $requests); do
        curl -s localhost:5000/camera/health >/dev/null &
    done
    wait
    
    local throughput_end=$(date +%s)
    local duration=$((throughput_end - throughput_start))
    local throughput=$((requests / duration))
    
    if [ "$throughput" -ge 20 ]; then
        log_success "Throughput OK: ${throughput} req/s (>=20 objetivo)"
    elif [ "$throughput" -ge 10 ]; then
        log_warning "Throughput bajo: ${throughput} req/s (objetivo >=20)"
    else
        log_error "Throughput crítico: ${throughput} req/s (muy por debajo del objetivo)"
    fi
}

# Función para verificar procesamiento de mensajes
check_message_processing() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando procesamiento de mensajes..."
    
    # Enviar mensaje de prueba
    local response=$(curl -s -X POST localhost:5000/camera \
        -H "Content-Type: application/json" \
        -d '{"device":"MONITOR_TEST","line":1,"Vehicle In":100,"Vehicle Out":50}' 2>/dev/null)
    
    if echo "$response" | jq -e '.status' >/dev/null 2>&1; then
        local status=$(echo "$response" | jq -r '.status')
        local processing_time=$(echo "$response" | jq -r '.processing_time_ms // 0')
        
        if [ "$status" = "ok" ] || [ "$status" = "success" ]; then
            log_success "Procesamiento de mensajes OK (${processing_time}ms)"
        elif [ "$status" = "duplicate" ]; then
            log_success "Mensaje duplicado detectado correctamente"
        elif [ "$status" = "camera_not_found" ]; then
            log_success "Validación de cámara funcionando (cámara test no encontrada - normal)"
        else
            log_warning "Mensaje procesado con status: $status"
        fi
    else
        log_error "Error en procesamiento de mensajes"
    fi
}

# Función para verificar panel worker
check_panel_worker() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando Panel Worker..."
    
    # Verificar actividad en logs recientes
    local worker_activity=$(journalctl -u parking-panel-worker --since "5 minutes ago" | grep -c "Parking" || echo "0")
    
    if [ "$worker_activity" -gt 0 ]; then
        log_success "Panel Worker activo: $worker_activity actualizaciones de parking en últimos 5min"
    else
        # Verificar si el servicio lleva poco tiempo corriendo
        local service_uptime=$(systemctl show parking-panel-worker --property=ActiveEnterTimestamp --value)
        if [ -n "$service_uptime" ]; then
            log_info "Panel Worker sin actividad visible (puede ser normal si recién inició)"
        else
            log_warning "Panel Worker sin actividad detectada"
        fi
    fi
    
    # Verificar que el servicio está corriendo
    if systemctl is-active --quiet parking-panel-worker; then
        log_success "Panel Worker service está activo"
    else
        log_error "Panel Worker service NO está activo"
    fi
}

# Función para verificar recursos del sistema
check_system_resources() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando recursos del sistema..."
    
    # CPU
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    if (( $(echo "$cpu_usage < 50" | bc -l) )); then
        log_success "CPU OK: ${cpu_usage}% (<50% objetivo)"
    elif (( $(echo "$cpu_usage < 80" | bc -l) )); then
        log_warning "CPU alta: ${cpu_usage}% (objetivo <50%)"
    else
        log_error "CPU crítica: ${cpu_usage}% (muy alta)"
    fi
    
    # Memoria
    local memory_info=$(free -m | grep Mem)
    local memory_used=$(echo $memory_info | awk '{print $3}')
    local memory_total=$(echo $memory_info | awk '{print $2}')
    local memory_percent=$((memory_used * 100 / memory_total))
    
    if [ "$memory_percent" -lt 70 ]; then
        log_success "Memoria OK: ${memory_percent}% usado (<70% objetivo)"
    elif [ "$memory_percent" -lt 85 ]; then
        log_warning "Memoria alta: ${memory_percent}% usado (objetivo <70%)"
    else
        log_error "Memoria crítica: ${memory_percent}% usado (muy alta)"
    fi
    
    # Disco
    local disk_usage=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        log_success "Disco OK: ${disk_usage}% usado (<80% objetivo)"
    elif [ "$disk_usage" -lt 90 ]; then
        log_warning "Disco alto: ${disk_usage}% usado (objetivo <80%)"
    else
        log_error "Disco crítico: ${disk_usage}% usado (muy alto)"
    fi
}

# Función para verificar logs de errores
check_error_logs() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log "Verificando logs de errores..."
    
    local error_count=$(journalctl -u parking-* --since "10 minutes ago" | grep -ci error || echo "0")
    
    if [ "$error_count" -eq 0 ]; then
        log_success "Sin errores en logs recientes"
    elif [ "$error_count" -lt 5 ]; then
        log_warning "$error_count errores en logs recientes (revisar si persisten)"
    else
        log_error "$error_count errores en logs recientes (revisar inmediatamente)"
    fi
    
    # Mostrar últimos errores si los hay
    if [ "$error_count" -gt 0 ]; then
        log_info "Últimos errores detectados:"
        journalctl -u parking-* --since "10 minutes ago" | grep -i error | tail -3 | while read line; do
            echo "  $line" | tee -a "$LOG_FILE"
        done
    fi
}

# Función para generar reporte de estado
generate_status_report() {
    log "Generando reporte de estado del sistema..."
    
    echo "" | tee -a "$LOG_FILE"
    echo "===============================================" | tee -a "$LOG_FILE"
    echo "📊 REPORTE DE ESTADO SISTEMA v3.4.0" | tee -a "$LOG_FILE"
    echo "===============================================" | tee -a "$LOG_FILE"
    echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Servicios
    echo "🔧 SERVICIOS:" | tee -a "$LOG_FILE"
    systemctl status parking-* --no-pager | grep -E "(Active|Main PID)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Endpoints
    echo "📡 ENDPOINTS:" | tee -a "$LOG_FILE"
    local camera_version=$(curl -s localhost:5000/camera/version | jq -r '.version' 2>/dev/null || echo "N/A")
    local camera_health=$(curl -s localhost:5000/camera/health | jq -r '.status' 2>/dev/null || echo "ERROR")
    local api_health=$(curl -s localhost:8080/health | jq -r '.status' 2>/dev/null || echo "ERROR")
    
    echo "  Camera Server: v$camera_version ($camera_health)" | tee -a "$LOG_FILE"
    echo "  API Server: $api_health" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Estadísticas
    echo "📈 ESTADÍSTICAS:" | tee -a "$LOG_FILE"
    local camera_stats=$(curl -s localhost:5000/camera/stats 2>/dev/null || echo "{}")
    local messages_processed=$(echo "$camera_stats" | jq -r '.messages_processed // "N/A"')
    local concurrent_messages=$(echo "$camera_stats" | jq -r '.concurrent_messages // "N/A"')
    
    echo "  Mensajes procesados: $messages_processed" | tee -a "$LOG_FILE"
    echo "  Mensajes concurrentes: $concurrent_messages" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Recursos
    echo "💾 RECURSOS:" | tee -a "$LOG_FILE"
    free -h | grep Mem | tee -a "$LOG_FILE"
    df -h /opt/parking_altea | tail -1 | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Resumen de checks
    echo "✅ CHECKS REALIZADOS:" | tee -a "$LOG_FILE"
    echo "  Total: $TOTAL_CHECKS" | tee -a "$LOG_FILE"
    echo "  Exitosos: $SUCCESSFUL_CHECKS" | tee -a "$LOG_FILE"
    echo "  Fallidos: $FAILED_CHECKS" | tee -a "$LOG_FILE"
    
    local success_rate=$((SUCCESSFUL_CHECKS * 100 / TOTAL_CHECKS))
    echo "  Tasa de éxito: ${success_rate}%" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Recomendación
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        echo -e "${GREEN}🎉 SISTEMA FUNCIONANDO CORRECTAMENTE${NC}" | tee -a "$LOG_FILE"
    elif [ "$FAILED_CHECKS" -lt 3 ]; then
        echo -e "${YELLOW}⚠️ SISTEMA FUNCIONANDO CON ADVERTENCIAS${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${RED}❌ SISTEMA CON PROBLEMAS CRÍTICOS${NC}" | tee -a "$LOG_FILE"
    fi
    
    echo "===============================================" | tee -a "$LOG_FILE"
}

# Función principal de monitoreo
main() {
    echo "🔍 MONITOREO POST-DESPLIEGUE SISTEMA v3.4.0"
    echo "=============================================="
    echo "Duración: ${MONITOR_DURATION}s"
    echo "Intervalo: ${CHECK_INTERVAL}s"
    echo "Log: $LOG_FILE"
    echo ""
    
    local end_time=$(($(date +%s) + MONITOR_DURATION))
    local check_count=0
    
    while [ $(date +%s) -lt $end_time ]; do
        check_count=$((check_count + 1))
        log "=== CHECK $check_count ==="
        
        # Ejecutar todas las verificaciones
        check_services
        check_endpoints
        check_performance
        check_message_processing
        check_panel_worker
        check_system_resources
        check_error_logs
        
        # Mostrar progreso
        local remaining=$((end_time - $(date +%s)))
        log_info "Tiempo restante: ${remaining}s"
        
        # Esperar siguiente iteración (solo si no es la última)
        if [ $remaining -gt $CHECK_INTERVAL ]; then
            sleep $CHECK_INTERVAL
        else
            break
        fi
    done
    
    # Generar reporte final
    generate_status_report
    
    # Determinar resultado final
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ MONITOREO COMPLETADO - SISTEMA ESTABLE${NC}"
        exit 0
    elif [ "$FAILED_CHECKS" -lt 5 ]; then
        echo ""
        echo -e "${YELLOW}⚠️ MONITOREO COMPLETADO - REVISAR ADVERTENCIAS${NC}"
        exit 1
    else
        echo ""
        echo -e "${RED}❌ MONITOREO COMPLETADO - PROBLEMAS CRÍTICOS DETECTADOS${NC}"
        exit 2
    fi
}

# Verificar argumentos
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Script de monitoreo post-despliegue v3.4.0"
    echo ""
    echo "Uso: $0 [duración_en_segundos]"
    echo ""
    echo "Argumentos:"
    echo "  duración_en_segundos  Duración del monitoreo (default: 300s = 5min)"
    echo ""
    echo "Ejemplos:"
    echo "  $0           # Monitorear por 5 minutos"
    echo "  $0 600       # Monitorear por 10 minutos"
    echo "  $0 1800      # Monitorear por 30 minutos"
    echo ""
    echo "El script verifica servicios, endpoints, rendimiento y recursos"
    echo "de forma continua durante el período especificado."
    exit 0
fi

# Verificar que estamos en el servidor correcto
if [ ! -d "/opt/parking_altea" ]; then
    echo "❌ Este script debe ejecutarse en el servidor de producción"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p "$(dirname "$LOG_FILE")"

# Ejecutar monitoreo
main
