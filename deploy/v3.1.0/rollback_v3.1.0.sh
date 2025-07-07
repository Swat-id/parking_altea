#!/bin/bash

# Script de Rollback v3.1.0 - Parking Altea
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

set -e

# Configuración
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_PASSWORD="Sudv9uvSvdu!"
REMOTE_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups/parking_altea"

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

# Función para listar backups disponibles
list_backups() {
    log "Backups disponibles:"
    remote_exec "ls -la $BACKUP_DIR/*.tar.gz 2>/dev/null || echo 'No hay backups disponibles'"
}

# Función para seleccionar backup
select_backup() {
    echo ""
    log "Selecciona el backup a restaurar:"
    
    # Obtener lista de backups
    BACKUPS=$(remote_exec "ls $BACKUP_DIR/*.tar.gz 2>/dev/null | sort -r")
    
    if [ -z "$BACKUPS" ]; then
        error "No hay backups disponibles"
        exit 1
    fi
    
    # Mostrar backups numerados
    I=1
    for backup in $BACKUPS; do
        echo "$I) $(basename $backup)"
        I=$((I+1))
    done
    
    echo ""
    read -p "Selecciona el número del backup: " BACKUP_NUM
    
    # Validar selección
    if ! [[ "$BACKUP_NUM" =~ ^[0-9]+$ ]]; then
        error "Número inválido"
        exit 1
    fi
    
    # Obtener backup seleccionado
    BACKUP_FILE=$(echo "$BACKUPS" | sed -n "${BACKUP_NUM}p")
    
    if [ -z "$BACKUP_FILE" ]; then
        error "Backup no encontrado"
        exit 1
    fi
    
    echo ""
    warning "Se va a restaurar: $(basename $BACKUP_FILE)"
    read -p "¿Estás seguro? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Rollback cancelado"
        exit 0
    fi
}

# Función para detener servicios
stop_services() {
    log "Deteniendo servicios..."
    
    remote_exec "systemctl stop parking-api.service || true"
    remote_exec "systemctl stop parking-camera.service || true"
    remote_exec "systemctl stop parking-schedule-monitor.service || true"
    
    success "Servicios detenidos"
}

# Función para restaurar backup
restore_backup() {
    log "Restaurando backup..."
    
    # Crear backup del estado actual antes de restaurar
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    remote_exec "cd $REMOTE_DIR && tar -czf $BACKUP_DIR/pre_rollback_$TIMESTAMP.tar.gz ."
    
    # Limpiar directorio actual
    remote_exec "rm -rf $REMOTE_DIR/*"
    
    # Restaurar backup
    remote_exec "cd $REMOTE_DIR && tar -xzf $BACKUP_FILE"
    
    # Restaurar permisos
    remote_exec "chown -R parking:parking $REMOTE_DIR"
    remote_exec "chmod +x $REMOTE_DIR/*.py"
    
    success "Backup restaurado"
}

# Función para restaurar base de datos
restore_database() {
    log "Restaurando base de datos..."
    
    # Buscar archivo de backup de base de datos
    DB_BACKUP=$(remote_exec "find $BACKUP_DIR -name '*database*' -o -name '*db*' | head -1")
    
    if [ -n "$DB_BACKUP" ]; then
        warning "Backup de base de datos encontrado: $(basename $DB_BACKUP)"
        read -p "¿Restaurar base de datos? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            remote_exec "sudo -u postgres pg_restore -d parking_altea $DB_BACKUP || echo 'Error restaurando base de datos'"
            success "Base de datos restaurada"
        fi
    else
        warning "No se encontró backup de base de datos"
    fi
}

# Función para iniciar servicios
start_services() {
    log "Iniciando servicios..."
    
    remote_exec "systemctl start parking-api.service"
    remote_exec "systemctl start parking-camera.service"
    remote_exec "systemctl start parking-schedule-monitor.service"
    
    # Esperar a que los servicios se inicien
    sleep 10
    
    success "Servicios iniciados"
}

# Función para verificar servicios
verify_services() {
    log "Verificando servicios..."
    
    # Verificar estado de los servicios
    API_STATUS=$(remote_exec "systemctl is-active parking-api.service")
    CAMERA_STATUS=$(remote_exec "systemctl is-active parking-camera.service")
    SCHEDULE_STATUS=$(remote_exec "systemctl is-active parking-schedule-monitor.service")
    
    if [ "$API_STATUS" = "active" ] && [ "$CAMERA_STATUS" = "active" ] && [ "$SCHEDULE_STATUS" = "active" ]; then
        success "Todos los servicios están activos"
    else
        error "Algunos servicios no están activos"
        remote_exec "systemctl status parking-api.service"
        remote_exec "systemctl status parking-camera.service"
        remote_exec "systemctl status parking-schedule-monitor.service"
        exit 1
    fi
    
    # Verificar endpoints
    log "Verificando endpoints..."
    sleep 5
    
    if remote_exec "curl -f http://localhost:5000/health" > /dev/null 2>&1; then
        success "API endpoint verificado"
    else
        error "API endpoint no responde"
        exit 1
    fi
}

# Función para mostrar información del rollback
show_rollback_info() {
    log "Información del rollback:"
    echo "========================"
    echo "Backup seleccionado: $(basename $BACKUP_FILE)"
    echo "Servidor: $REMOTE_HOST"
    echo "Directorio: $REMOTE_DIR"
    echo ""
    echo "Este proceso:"
    echo "1. Detendrá todos los servicios"
    echo "2. Restaurará el backup seleccionado"
    echo "3. Restaurará la base de datos (si existe backup)"
    echo "4. Iniciará los servicios"
    echo "5. Verificará el funcionamiento"
    echo ""
    warning "⚠️  Este proceso es irreversible"
}

# Función principal
main() {
    echo "🔄 Rollback v3.1.0 - Parking Altea"
    echo "=================================="
    
    # Listar backups disponibles
    list_backups
    
    # Seleccionar backup
    select_backup
    
    # Mostrar información
    show_rollback_info
    
    # Ejecutar rollback
    stop_services
    restore_backup
    restore_database
    start_services
    verify_services
    
    echo ""
    success "🎉 Rollback completado exitosamente!"
    echo ""
    log "El sistema ha sido restaurado a: $(basename $BACKUP_FILE)"
    log "Verificar funcionamiento en: http://$REMOTE_HOST"
}

# Ejecutar función principal
main "$@" 