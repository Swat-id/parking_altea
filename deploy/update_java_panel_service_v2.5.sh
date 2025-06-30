#!/bin/bash

# Script de actualización para el servicio Java Panel Service v2.5
# Parking Altea - Actualización desde Git

set -e

# Configuración
SERVICE_NAME="java-panel-service"
SERVICE_DIR="/opt/java-panel-service"
PROJECT_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups/java-panel-service"
LOG_FILE="/var/log/java-panel-service-update.log"
JAR_NAME="java-panel-service-1.0.0.jar"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de logging
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}[$timestamp] INFO: $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] SUCCESS: $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] WARNING: $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR: $message${NC}"
            ;;
    esac
    
    echo "[$timestamp] $level: $message" >> "$LOG_FILE"
}

# Función para crear backup
create_backup() {
    log "INFO" "Creando backup del servicio actual..."
    
    if [ -d "$SERVICE_DIR" ]; then
        local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
        local backup_path="$BACKUP_DIR/$backup_name"
        
        mkdir -p "$BACKUP_DIR"
        cp -r "$SERVICE_DIR" "$backup_path"
        log "SUCCESS" "Backup creado en: $backup_path"
    else
        log "WARNING" "No se encontró directorio de servicio para backup"
    fi
}

# Función para actualizar desde Git
update_from_git() {
    log "INFO" "Actualizando código desde Git..."
    
    cd "$PROJECT_DIR"
    
    # Verificar que estamos en la rama correcta
    local current_branch=$(git branch --show-current)
    log "INFO" "Rama actual: $current_branch"
    
    # Pull de los últimos cambios
    git pull origin "$current_branch"
    log "SUCCESS" "Código actualizado desde Git"
}

# Función para compilar el proyecto
compile_project() {
    log "INFO" "Compilando proyecto Java Panel Service..."
    
    cd "$PROJECT_DIR/server/java-panel-service"
    
    # Limpiar y compilar
    mvn clean compile
    log "SUCCESS" "Proyecto compilado correctamente"
    
    # Crear JAR
    mvn clean package -DskipTests
    log "SUCCESS" "JAR generado correctamente"
}

# Función para parar el servicio
stop_service() {
    log "INFO" "Parando servicio $SERVICE_NAME..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        sleep 5
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log "WARNING" "Servicio no se paró correctamente, forzando..."
            systemctl kill "$SERVICE_NAME"
            sleep 3
        fi
        
        log "SUCCESS" "Servicio parado correctamente"
    else
        log "INFO" "Servicio ya estaba parado"
    fi
}

# Función para actualizar archivos
update_files() {
    log "INFO" "Actualizando archivos del servicio..."
    
    # Crear directorio si no existe
    mkdir -p "$SERVICE_DIR"
    
    # Copiar JAR
    cp "$PROJECT_DIR/server/java-panel-service/target/$JAR_NAME" "$SERVICE_DIR/"
    log "SUCCESS" "JAR actualizado"
    
    # Copiar librería del fabricante
    if [ -f "$PROJECT_DIR/panel_java/protocol-1.2.6.jar" ]; then
        cp "$PROJECT_DIR/panel_java/protocol-1.2.6.jar" "$SERVICE_DIR/"
        log "SUCCESS" "Librería del fabricante copiada"
    else
        log "WARNING" "Librería del fabricante no encontrada: $PROJECT_DIR/panel_java/protocol-1.2.6.jar"
    fi
    
    # Copiar configuración si existe
    if [ -f "$PROJECT_DIR/server/java-panel-service/src/main/resources/application.yml" ]; then
        cp "$PROJECT_DIR/server/java-panel-service/src/main/resources/application.yml" "$SERVICE_DIR/"
        log "SUCCESS" "Configuración actualizada"
    fi
    
    # Crear directorio de logs
    mkdir -p "$SERVICE_DIR/logs"
    
    # Asegurar permisos
    chown -R root:root "$SERVICE_DIR"
    chmod -R 755 "$SERVICE_DIR"
    chmod 644 "$SERVICE_DIR/$JAR_NAME"
    chmod 644 "$SERVICE_DIR/protocol-1.2.6.jar"
    
    log "SUCCESS" "Archivos actualizados correctamente"
}

# Función para arrancar el servicio
start_service() {
    log "INFO" "Arrancando servicio $SERVICE_NAME..."
    
    # Recargar configuración de systemd
    systemctl daemon-reload
    
    # Arrancar servicio
    systemctl start "$SERVICE_NAME"
    sleep 5
    
    # Verificar estado
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "SUCCESS" "Servicio arrancado correctamente"
    else
        log "ERROR" "Error al arrancar el servicio"
        systemctl status "$SERVICE_NAME"
        return 1
    fi
}

# Función para verificar el servicio
verify_service() {
    log "INFO" "Verificando servicio..."
    
    # Verificar estado del servicio
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "SUCCESS" "Servicio está activo"
    else
        log "ERROR" "Servicio no está activo"
        return 1
    fi
    
    # Verificar puerto
    if netstat -tlnp | grep -q ":5002 "; then
        log "SUCCESS" "Puerto 5002 está escuchando"
    else
        log "WARNING" "Puerto 5002 no está escuchando"
    fi
    
    # Verificar logs
    if journalctl -u "$SERVICE_NAME" --since "5 minutes ago" | grep -q "Started"; then
        log "SUCCESS" "Servicio iniciado correctamente según logs"
    else
        log "WARNING" "No se encontraron logs de inicio recientes"
    fi
}

# Función para mostrar logs recientes
show_logs() {
    log "INFO" "Mostrando logs recientes del servicio..."
    echo "=== Logs del servicio (últimos 20 líneas) ==="
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    echo "============================================="
}

# Función principal
main() {
    log "INFO" "Iniciando actualización del Java Panel Service v2.5"
    log "INFO" "Directorio del proyecto: $PROJECT_DIR"
    log "INFO" "Directorio del servicio: $SERVICE_DIR"
    
    # Verificar que estamos como root
    if [ "$EUID" -ne 0 ]; then
        log "ERROR" "Este script debe ejecutarse como root"
        exit 1
    fi
    
    # Verificar que existe el directorio del proyecto
    if [ ! -d "$PROJECT_DIR" ]; then
        log "ERROR" "Directorio del proyecto no encontrado: $PROJECT_DIR"
        exit 1
    fi
    
    # Ejecutar pasos de actualización
    create_backup
    update_from_git
    compile_project
    stop_service
    update_files
    start_service
    verify_service
    
    log "SUCCESS" "Actualización completada correctamente"
    show_logs
    
    log "INFO" "Logs de la actualización guardados en: $LOG_FILE"
}

# Ejecutar función principal
main "$@" 