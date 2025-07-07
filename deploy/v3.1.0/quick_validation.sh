#!/bin/bash

# Script de Validación Rápida v3.1.0 - Parking Altea
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

# Configuración
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_PASSWORD="Sudv9uvSvdu!"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
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

# Función para validación rápida
quick_validation() {
    echo "🔍 Validación Rápida v3.1.0 - Parking Altea"
    echo "=========================================="
    
    # Verificar servicios
    log "Verificando servicios..."
    SERVICES=("parking-api" "parking-camera" "parking-schedule-monitor")
    
    for service in "${SERVICES[@]}"; do
        STATUS=$(remote_exec "systemctl is-active ${service}.service")
        if [ "$STATUS" = "active" ]; then
            success "Servicio $service: ACTIVO"
        else
            error "Servicio $service: INACTIVO"
        fi
    done
    
    # Verificar endpoints
    log "Verificando endpoints..."
    
    if remote_exec "curl -f -s http://localhost:5000/health" > /dev/null 2>&1; then
        success "API: RESPONDE"
    else
        error "API: NO RESPONDE"
    fi
    
    if remote_exec "curl -f -s http://localhost" > /dev/null 2>&1; then
        success "Frontend: RESPONDE"
    else
        error "Frontend: NO RESPONDE"
    fi
    
    # Verificar desde exterior
    if curl -f -s "http://$REMOTE_HOST" > /dev/null 2>&1; then
        success "Exterior: ACCESIBLE"
    else
        error "Exterior: NO ACCESIBLE"
    fi
    
    # Verificar base de datos
    log "Verificando base de datos..."
    if remote_exec "sudo -u postgres psql -d parking_altea -c 'SELECT 1;'" > /dev/null 2>&1; then
        success "Base de datos: CONECTADA"
    else
        error "Base de datos: ERROR"
    fi
    
    # Verificar recursos
    log "Verificando recursos..."
    
    DISK_USAGE=$(remote_exec "df -h /opt/parking_altea | tail -1 | awk '{print \$5}' | sed 's/%//'")
    if [ "$DISK_USAGE" -lt 80 ]; then
        success "Disco: ${DISK_USAGE}%"
    else
        warning "Disco: ${DISK_USAGE}% (ALTO)"
    fi
    
    MEMORY_USAGE=$(remote_exec "free | grep Mem | awk '{printf \"%.0f\", \$3/\$2 * 100.0}'")
    if [ "$MEMORY_USAGE" -lt 80 ]; then
        success "Memoria: ${MEMORY_USAGE}%"
    else
        warning "Memoria: ${MEMORY_USAGE}% (ALTO)"
    fi
    
    # Verificar logs recientes
    log "Verificando logs recientes..."
    ERROR_COUNT=$(remote_exec "journalctl -u parking-api.service --since '1 hour ago' | grep -i error | wc -l")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        success "Logs: SIN ERRORES"
    else
        warning "Logs: $ERROR_COUNT errores en la última hora"
    fi
    
    echo ""
    echo "=========================================="
    success "Validación rápida completada"
}

# Función para mostrar estado detallado
detailed_status() {
    echo ""
    log "Estado detallado del sistema:"
    echo "----------------------------"
    
    # Estado de servicios
    remote_exec "systemctl status parking-api.service --no-pager"
    echo ""
    remote_exec "systemctl status parking-camera.service --no-pager"
    echo ""
    remote_exec "systemctl status parking-schedule-monitor.service --no-pager"
    
    # Recursos del sistema
    echo ""
    log "Recursos del sistema:"
    remote_exec "df -h"
    echo ""
    remote_exec "free -h"
    echo ""
    remote_exec "uptime"
    
    # Logs recientes
    echo ""
    log "Logs recientes (últimas 10 líneas):"
    remote_exec "journalctl -u parking-api.service --no-pager | tail -10"
}

# Función principal
main() {
    case "${1:-quick}" in
        "quick")
            quick_validation
            ;;
        "detailed")
            quick_validation
            detailed_status
            ;;
        "help"|"-h"|"--help")
            echo "Uso: $0 [quick|detailed|help]"
            echo "  quick     - Validación rápida (por defecto)"
            echo "  detailed  - Validación rápida + estado detallado"
            echo "  help      - Mostrar esta ayuda"
            ;;
        *)
            echo "Opción desconocida: $1"
            echo "Usar '$0 help' para ver las opciones disponibles"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@" 