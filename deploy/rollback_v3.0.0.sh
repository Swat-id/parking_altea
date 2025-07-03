#!/bin/bash

# Script de Rollback v3.0.0 - Parking Altea
# =========================================
# Este script revierte el deployment v3.0.0 al estado anterior

# Configuración
REMOTE_HOST="parking-altea.com"
REMOTE_USER="parking"
REMOTE_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/parking_altea/rollback_v3.0.0.log"

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

# Función para listar backups disponibles
list_backups() {
    log "Backups disponibles:"
    ssh $REMOTE_USER@$REMOTE_HOST "ls -la $BACKUP_DIR/ | grep parking_altea_backup_v3.0.0"
}

# Función para seleccionar backup
select_backup() {
    log "Seleccionando backup para rollback..."
    
    # Buscar el backup más reciente
    LATEST_BACKUP=$(ssh $REMOTE_USER@$REMOTE_HOST "ls -t $BACKUP_DIR/parking_altea_backup_v3.0.0_* | head -1")
    
    if [ -z "$LATEST_BACKUP" ]; then
        error "No se encontraron backups de v3.0.0"
        exit 1
    fi
    
    BACKUP_NAME=$(basename "$LATEST_BACKUP")
    log "Backup seleccionado: $BACKUP_NAME"
    
    echo "$BACKUP_NAME"
}

# Función para detener servicios
stop_services() {
    log "Deteniendo servicios..."
    
    services=("parking-api" "parking-camera" "parking-panel" "panel-service-v2")
    
    for service in "${services[@]}"; do
        if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet $service"; then
            log "Deteniendo $service..."
            ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl stop $service"
        fi
    done
    
    sleep 5
}

# Función para restaurar base de datos
restore_database() {
    local backup_name=$1
    log "Restaurando base de datos desde $backup_name..."
    
    BACKUP_FILE="$BACKUP_DIR/${backup_name}.sql"
    
    if ssh $REMOTE_USER@$REMOTE_HOST "test -f $BACKUP_FILE"; then
        # Crear backup de la base actual antes de restaurar
        CURRENT_BACKUP="$BACKUP_DIR/pre_rollback_backup_$(date +%Y%m%d_%H%M%S).sql"
        ssh $REMOTE_USER@$REMOTE_HOST "pg_dump parking_altea > $CURRENT_BACKUP"
        log "Backup de seguridad creado: $CURRENT_BACKUP"
        
        # Restaurar base de datos
        ssh $REMOTE_USER@$REMOTE_HOST "psql -d parking_altea -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'"
        ssh $REMOTE_USER@$REMOTE_HOST "psql -d parking_altea < $BACKUP_FILE"
        
        log "Base de datos restaurada"
    else
        error "Archivo de backup no encontrado: $BACKUP_FILE"
        return 1
    fi
}

# Función para restaurar archivos
restore_files() {
    local backup_name=$1
    log "Restaurando archivos desde $backup_name..."
    
    BACKUP_FILE="$BACKUP_DIR/${backup_name}.tar.gz"
    
    if ssh $REMOTE_USER@$REMOTE_HOST "test -f $BACKUP_FILE"; then
        # Crear backup de archivos actuales
        CURRENT_BACKUP="$BACKUP_DIR/pre_rollback_files_$(date +%Y%m%d_%H%M%S).tar.gz"
        ssh $REMOTE_USER@$REMOTE_HOST "tar -czf $CURRENT_BACKUP -C /opt parking_altea"
        log "Backup de archivos creado: $CURRENT_BACKUP"
        
        # Restaurar archivos
        ssh $REMOTE_USER@$REMOTE_HOST "sudo rm -rf $REMOTE_DIR"
        ssh $REMOTE_USER@$REMOTE_HOST "sudo tar -xzf $BACKUP_FILE -C /opt"
        ssh $REMOTE_USER@$REMOTE_USER "sudo chown -R $REMOTE_USER:$REMOTE_USER $REMOTE_DIR"
        
        log "Archivos restaurados"
    else
        error "Archivo de backup no encontrado: $BACKUP_FILE"
        return 1
    fi
}

# Función para restaurar configuración
restore_config() {
    local backup_name=$1
    log "Restaurando configuración desde $backup_name..."
    
    BACKUP_FILE="$BACKUP_DIR/${backup_name}.config.tar.gz"
    
    if ssh $REMOTE_USER@$REMOTE_HOST "test -f $BACKUP_FILE"; then
        # Crear backup de configuración actual
        CURRENT_BACKUP="$BACKUP_DIR/pre_rollback_config_$(date +%Y%m%d_%H%M%S).tar.gz"
        ssh $REMOTE_USER@$REMOTE_HOST "sudo tar -czf $CURRENT_BACKUP /etc/parking_altea /etc/systemd/system/parking-*.service"
        log "Backup de configuración creado: $CURRENT_BACKUP"
        
        # Restaurar configuración
        ssh $REMOTE_USER@$REMOTE_HOST "sudo tar -xzf $BACKUP_FILE -C /"
        
        log "Configuración restaurada"
    else
        error "Archivo de configuración no encontrado: $BACKUP_FILE"
        return 1
    fi
}

# Función para eliminar Panel Service v2
remove_panel_service_v2() {
    log "Eliminando Panel Service v2..."
    
    # Detener y deshabilitar servicio
    ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl stop panel-service-v2 2>/dev/null || true"
    ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl disable panel-service-v2 2>/dev/null || true"
    
    # Eliminar archivo de servicio
    ssh $REMOTE_USER@$REMOTE_HOST "sudo rm -f /etc/systemd/system/panel-service-v2.service"
    
    # Eliminar directorio
    ssh $REMOTE_USER@$REMOTE_HOST "sudo rm -rf /opt/panelsender"
    
    # Recargar systemd
    ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl daemon-reload"
    
    log "Panel Service v2 eliminado"
}

# Función para restaurar configuración de nginx
restore_nginx_config() {
    log "Restaurando configuración de nginx..."
    
    # Eliminar configuración de Panel Service v2
    ssh $REMOTE_USER@$REMOTE_HOST "sudo rm -f /etc/nginx/sites-enabled/panel-service-v2.conf"
    ssh $REMOTE_USER@$REMOTE_HOST "sudo rm -f /etc/nginx/sites-available/panel-service-v2.conf"
    
    # Verificar configuración
    ssh $REMOTE_USER@$REMOTE_HOST "sudo nginx -t"
    
    # Recargar nginx
    ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl reload nginx"
    
    log "Configuración de nginx restaurada"
}

# Función para volver a la rama anterior
restore_git_branch() {
    log "Restaurando rama Git anterior..."
    
    # Cambiar a la rama principal
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && git checkout main"
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && git pull origin main"
    
    log "Rama Git restaurada a main"
}

# Función para reinstalar dependencias
reinstall_dependencies() {
    log "Reinstalando dependencias..."
    
    # Dependencias Python
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && pip install -r requirements.txt"
    
    # Dependencias Frontend
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR/client && npm install"
    
    log "Dependencias reinstaladas"
}

# Función para reconstruir frontend
rebuild_frontend() {
    log "Reconstruyendo frontend..."
    
    # Construir frontend
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR/client && npm run build"
    
    # Copiar archivos construidos
    ssh $REMOTE_USER@$REMOTE_HOST "sudo cp -r $REMOTE_DIR/client/dist/* /var/www/parking_altea/"
    
    # Ajustar permisos
    ssh $REMOTE_USER@$REMOTE_HOST "sudo chown -R www-data:www-data /var/www/parking_altea/"
    
    log "Frontend reconstruido"
}

# Función para iniciar servicios
start_services() {
    log "Iniciando servicios..."
    
    services=("parking-api" "parking-camera" "parking-panel")
    
    for service in "${services[@]}"; do
        log "Iniciando $service..."
        ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl start $service"
        
        # Verificar que el servicio se inició correctamente
        sleep 3
        if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet $service"; then
            log "$service iniciado correctamente"
        else
            error "$service no se pudo iniciar"
            ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl status $service"
        fi
    done
}

# Función para verificar rollback
verify_rollback() {
    log "Verificando rollback..."
    
    # Verificar servicios
    services=("parking-api" "parking-camera" "parking-panel")
    active_services=0
    
    for service in "${services[@]}"; do
        if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet $service"; then
            ((active_services++))
        fi
    done
    
    if [ "$active_services" -eq 3 ]; then
        log "✅ Todos los servicios están ejecutándose"
    else
        error "❌ No todos los servicios están ejecutándose"
    fi
    
    # Verificar que Panel Service v2 no está ejecutándose
    if ssh $REMOTE_USER@$REMOTE_HOST "systemctl is-active --quiet panel-service-v2"; then
        error "❌ Panel Service v2 aún está ejecutándose"
    else
        log "✅ Panel Service v2 no está ejecutándose (correcto)"
    fi
    
    # Verificar frontend
    if curl -s http://$REMOTE_HOST/ | grep -q "Parking Altea"; then
        log "✅ Frontend funciona correctamente"
    else
        error "❌ Frontend no funciona"
    fi
    
    # Verificar API
    if curl -s http://$REMOTE_HOST/api/health | grep -q "ok"; then
        log "✅ API funciona correctamente"
    else
        error "❌ API no funciona"
    fi
}

# Función para mostrar resumen
show_summary() {
    log "🔄 Rollback v3.0.0 completado"
    log "=" * 50
    log "El sistema ha sido revertido al estado anterior a v3.0.0"
    log ""
    log "Cambios realizados:"
    log "✅ Base de datos restaurada"
    log "✅ Archivos del sistema restaurados"
    log "✅ Configuración restaurada"
    log "✅ Panel Service v2 eliminado"
    log "✅ Configuración de nginx restaurada"
    log "✅ Rama Git restaurada a main"
    log "✅ Servicios reiniciados"
    log ""
    log "Servicios activos:"
    log "  - parking-api (Puerto 5000)"
    log "  - parking-camera (Puerto 5001)"
    log "  - parking-panel (Puerto 3000)"
    log ""
    log "Panel Service v2: ELIMINADO"
    log ""
    log "Backups de seguridad creados durante rollback:"
    log "  - pre_rollback_backup_*.sql"
    log "  - pre_rollback_files_*.tar.gz"
    log "  - pre_rollback_config_*.tar.gz"
}

# Función principal
main() {
    log "🔄 Iniciando rollback v3.0.0 - Parking Altea"
    log "=" * 60
    
    # Listar backups disponibles
    list_backups
    
    # Seleccionar backup
    BACKUP_NAME=$(select_backup)
    
    # Confirmar rollback
    echo -e "${YELLOW}¿Está seguro de que desea realizar el rollback? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Rollback cancelado por el usuario"
        exit 0
    fi
    
    # Detener servicios
    stop_services
    
    # Restaurar base de datos
    if ! restore_database "$BACKUP_NAME"; then
        error "Error restaurando base de datos. Abortando rollback."
        exit 1
    fi
    
    # Restaurar archivos
    if ! restore_files "$BACKUP_NAME"; then
        error "Error restaurando archivos. Abortando rollback."
        exit 1
    fi
    
    # Restaurar configuración
    if ! restore_config "$BACKUP_NAME"; then
        error "Error restaurando configuración. Abortando rollback."
        exit 1
    fi
    
    # Eliminar Panel Service v2
    remove_panel_service_v2
    
    # Restaurar configuración de nginx
    restore_nginx_config
    
    # Restaurar rama Git
    restore_git_branch
    
    # Reinstalar dependencias
    reinstall_dependencies
    
    # Reconstruir frontend
    rebuild_frontend
    
    # Iniciar servicios
    start_services
    
    # Verificar rollback
    verify_rollback
    
    # Mostrar resumen
    show_summary
}

# Manejo de errores
set -e
trap 'error "Error en línea $LINENO. Rollback incompleto."' ERR

# Ejecutar función principal
main "$@" 