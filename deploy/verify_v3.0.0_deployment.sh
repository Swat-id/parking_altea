#!/bin/bash

# Script de Verificación v3.0.0 - Parking Altea
# =============================================
# Este script verifica que el deployment v3.0.0 se realizó correctamente

# Configuración
REMOTE_HOST="parking-altea.com"
REMOTE_USER="parking"
REMOTE_DIR="/opt/parking_altea"
LOG_FILE="/var/log/parking_altea/verification_v3.0.0.log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a $LOG_FILE
}

# Función para verificar servicio
check_service() {
    local service_name=$1
    local service_description=$2
    
    log "Verificando $service_description..."
    
    if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet $service_name"; then
        log "✅ $service_description está ejecutándose"
        
        # Verificar puerto si es necesario
        case $service_name in
            "parking-api")
                if curl -s http://$REMOTE_HOST:5000/health | grep -q "ok"; then
                    log "✅ API responde correctamente en puerto 5000"
                else
                    error "❌ API no responde en puerto 5000"
                fi
                ;;
            "parking-camera")
                if curl -s http://$REMOTE_HOST:5001/health | grep -q "ok"; then
                    log "✅ Camera Service responde correctamente en puerto 5001"
                else
                    error "❌ Camera Service no responde en puerto 5001"
                fi
                ;;
            "parking-panel")
                if curl -s http://$REMOTE_HOST:3000/health | grep -q "ok"; then
                    log "✅ Panel Service v1 responde correctamente en puerto 3000"
                else
                    error "❌ Panel Service v1 no responde en puerto 3000"
                fi
                ;;
            "panel-service-v2")
                if curl -s http://$REMOTE_HOST:5657/health | grep -q "healthy"; then
                    log "✅ Panel Service v2 responde correctamente en puerto 5657"
                else
                    error "❌ Panel Service v2 no responde en puerto 5657"
                fi
                ;;
        esac
    else
        error "❌ $service_description no está ejecutándose"
        ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl status $service_name"
    fi
}

# Función para verificar base de datos
check_database() {
    log "Verificando base de datos..."
    
    # Verificar conexión
    if ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && python -c 'from src.models import engine; print(\"Conexión OK\")'"; then
        log "✅ Conexión a base de datos establecida"
    else
        error "❌ Error conectando a base de datos"
        return 1
    fi
    
    # Verificar tablas de migración
    log "Verificando tablas de migración..."
    
    # Verificar tabla manufacturers
    manufacturer_count=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM manufacturers;\" | xargs")
    if [ "$manufacturer_count" -gt 0 ]; then
        log "✅ Tabla manufacturers: $manufacturer_count registros"
    else
        error "❌ Tabla manufacturers vacía o no existe"
    fi
    
    # Verificar tabla panel_types
    panel_types_count=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM panel_types;\" | xargs")
    if [ "$panel_types_count" -eq 3 ]; then
        log "✅ Tabla panel_types: $panel_types_count tipos (correcto)"
    else
        error "❌ Tabla panel_types: $panel_types_count tipos (esperado: 3)"
    fi
    
    # Verificar paneles migrados
    migrated_panels=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM panels WHERE panel_type_id IS NOT NULL;\" | xargs")
    total_panels=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM panels;\" | xargs")
    
    if [ "$migrated_panels" -eq "$total_panels" ] && [ "$total_panels" -gt 0 ]; then
        log "✅ Paneles migrados: $migrated_panels/$total_panels"
    else
        error "❌ Paneles migrados: $migrated_panels/$total_panels"
    fi
}

# Función para verificar archivos
check_files() {
    log "Verificando archivos del sistema..."
    
    # Verificar Panel Service v2
    if ssh $REMOTE_USER@$REMOTE_HOST "test -d /opt/panelsender"; then
        log "✅ Directorio Panel Service v2 existe"
        
        # Verificar archivos principales
        files=("server.js" "package.json" "protocol.jar" "config/panels.json")
        for file in "${files[@]}"; do
            if ssh $REMOTE_USER@$REMOTE_HOST "test -f /opt/panelsender/$file"; then
                log "✅ Archivo $file existe"
            else
                error "❌ Archivo $file no encontrado"
            fi
        done
    else
        error "❌ Directorio Panel Service v2 no existe"
    fi
    
    # Verificar frontend
    if ssh $REMOTE_USER@$REMOTE_HOST "test -f /var/www/parking_altea/index.html"; then
        log "✅ Frontend desplegado correctamente"
    else
        error "❌ Frontend no encontrado"
    fi
}

# Función para verificar nginx
check_nginx() {
    log "Verificando configuración de nginx..."
    
    # Verificar configuración
    if ssh $REMOTE_USER@$REMOTE_HOST "sudo nginx -t"; then
        log "✅ Configuración de nginx válida"
    else
        error "❌ Error en configuración de nginx"
    fi
    
    # Verificar que nginx está ejecutándose
    if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet nginx"; then
        log "✅ Nginx está ejecutándose"
    else
        error "❌ Nginx no está ejecutándose"
    fi
    
    # Verificar endpoints
    endpoints=(
        "http://$REMOTE_HOST/"
        "http://$REMOTE_HOST/api/health"
        "http://$REMOTE_HOST/health/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "$endpoint" > /dev/null; then
            log "✅ Endpoint $endpoint responde"
        else
            error "❌ Endpoint $endpoint no responde"
        fi
    done
}

# Función para verificar logs
check_logs() {
    log "Verificando logs del sistema..."
    
    # Verificar logs de servicios
    services=("parking-api" "parking-camera" "parking-panel" "panel-service-v2")
    
    for service in "${services[@]}"; do
        if ssh $REMOTE_USER@$REMOTE_HOST "sudo journalctl -u $service --since '1 hour ago' | grep -i error | wc -l" | grep -q "0"; then
            log "✅ $service: Sin errores en la última hora"
        else
            warning "⚠️ $service: Errores encontrados en logs"
            ssh $REMOTE_USER@$REMOTE_HOST "sudo journalctl -u $service --since '1 hour ago' | grep -i error | tail -5"
        fi
    done
}

# Función para verificar recursos del sistema
check_system_resources() {
    log "Verificando recursos del sistema..."
    
    # Verificar uso de memoria
    memory_usage=$(ssh $REMOTE_USER@$REMOTE_HOST "free | grep Mem | awk '{printf \"%.1f\", \$3/\$2 * 100.0}'")
    log "📊 Uso de memoria: ${memory_usage}%"
    
    # Verificar uso de disco
    disk_usage=$(ssh $REMOTE_USER@$REMOTE_HOST "df / | tail -1 | awk '{print \$5}'")
    log "📊 Uso de disco: $disk_usage"
    
    # Verificar carga del sistema
    load_average=$(ssh $REMOTE_USER@$REMOTE_HOST "uptime | awk -F'load average:' '{print \$2}'")
    log "📊 Carga del sistema: $load_average"
}

# Función para verificar conectividad de red
check_network() {
    log "Verificando conectividad de red..."
    
    # Verificar puertos abiertos
    ports=(5000 5001 3000 5657 80 443)
    
    for port in "${ports[@]}"; do
        if ssh $REMOTE_USER@$REMOTE_HOST "netstat -tuln | grep :$port"; then
            log "✅ Puerto $port está abierto"
        else
            warning "⚠️ Puerto $port no está abierto"
        fi
    done
}

# Función para realizar pruebas funcionales
run_functional_tests() {
    log "Ejecutando pruebas funcionales..."
    
    # Test 1: Verificar API de tipos de paneles
    if curl -s http://$REMOTE_HOST/api/panel-types | grep -q "Panel Tipo"; then
        log "✅ API de tipos de paneles funciona"
    else
        error "❌ API de tipos de paneles no funciona"
    fi
    
    # Test 2: Verificar endpoint de Panel Service v2
    if curl -s http://$REMOTE_HOST/api/v1/panels/config | grep -q "panels"; then
        log "✅ Panel Service v2 API funciona"
    else
        error "❌ Panel Service v2 API no funciona"
    fi
    
    # Test 3: Verificar frontend
    if curl -s http://$REMOTE_HOST/ | grep -q "Parking Altea"; then
        log "✅ Frontend carga correctamente"
    else
        error "❌ Frontend no carga correctamente"
    fi
}

# Función para mostrar resumen
show_summary() {
    log "📋 Resumen de verificación v3.0.0"
    log "=" * 50
    
    # Contar servicios activos
    active_services=0
    total_services=4
    
    services=("parking-api" "parking-camera" "parking-panel" "panel-service-v2")
    for service in "${services[@]}"; do
        if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet $service"; then
            ((active_services++))
        fi
    done
    
    log "Servicios activos: $active_services/$total_services"
    
    # Verificar migración
    migrated_panels=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM panels WHERE panel_type_id IS NOT NULL;\" | xargs")
    total_panels=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM panels;\" | xargs")
    
    log "Paneles migrados: $migrated_panels/$total_panels"
    
    # Verificar tipos de paneles
    panel_types_count=$(ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && psql -d parking_altea -t -c \"SELECT COUNT(*) FROM panel_types;\" | xargs")
    log "Tipos de paneles: $panel_types_count/3"
    
    if [ "$active_services" -eq "$total_services" ] && [ "$migrated_panels" -eq "$total_panels" ] && [ "$panel_types_count" -eq 3 ]; then
        log "🎉 Verificación completada exitosamente"
        log "El sistema v3.0.0 está funcionando correctamente"
    else
        error "❌ Verificación falló - revisar errores anteriores"
        exit 1
    fi
}

# Función principal
main() {
    log "🔍 Iniciando verificación v3.0.0 - Parking Altea"
    log "=" * 60
    
    # Verificar servicios
    check_service "parking-api" "API Principal"
    check_service "parking-camera" "Camera Service"
    check_service "parking-panel" "Panel Service v1"
    check_service "panel-service-v2" "Panel Service v2"
    
    # Verificar base de datos
    check_database
    
    # Verificar archivos
    check_files
    
    # Verificar nginx
    check_nginx
    
    # Verificar logs
    check_logs
    
    # Verificar recursos del sistema
    check_system_resources
    
    # Verificar conectividad de red
    check_network
    
    # Ejecutar pruebas funcionales
    run_functional_tests
    
    # Mostrar resumen
    show_summary
}

# Manejo de errores
set -e

# Ejecutar función principal
main "$@" 