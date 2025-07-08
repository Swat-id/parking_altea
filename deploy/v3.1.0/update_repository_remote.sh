#!/bin/bash

# Script para Actualizar Repositorio en Servidor Remoto v3.1.0
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

set -e

# Configuración
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_PASSWORD="Sudv9uvSvdu!"
REMOTE_DIR="/opt/parking_altea"
BRANCH="v3.1.0_login"

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

# Función para verificar si el repositorio existe
check_repository() {
    log "Verificando si el repositorio existe..."
    
    if remote_exec "[ -d $REMOTE_DIR/.git ]"; then
        success "Repositorio Git encontrado en $REMOTE_DIR"
        return 0
    else
        warning "No se encontró repositorio Git en $REMOTE_DIR"
        return 1
    fi
}

# Función para clonar el repositorio
clone_repository() {
    log "Clonando repositorio desde GitHub..."
    
    # Crear directorio si no existe
    remote_exec "mkdir -p $REMOTE_DIR"
    
    # Clonar repositorio
    remote_exec "cd $REMOTE_DIR && git clone https://github.com/Swat-id/parking_altea.git ."
    
    if [ $? -eq 0 ]; then
        success "Repositorio clonado exitosamente"
    else
        error "Error clonando el repositorio"
        exit 1
    fi
}

# Función para actualizar el repositorio
update_repository() {
    log "Actualizando repositorio existente..."
    
    # Guardar cambios locales si existen
    remote_exec "cd $REMOTE_DIR && git stash"
    
    # Obtener cambios remotos
    remote_exec "cd $REMOTE_DIR && git fetch origin"
    
    # Verificar si la rama existe
    BRANCH_EXISTS=$(remote_exec "cd $REMOTE_DIR && git branch -r | grep origin/$BRANCH")
    
    if [ -n "$BRANCH_EXISTS" ]; then
        success "Rama $BRANCH encontrada en el repositorio remoto"
        
        # Cambiar a la rama
        remote_exec "cd $REMOTE_DIR && git checkout $BRANCH"
        
        # Actualizar con los cambios remotos
        remote_exec "cd $REMOTE_DIR && git pull origin $BRANCH"
        
        success "Repositorio actualizado a la rama $BRANCH"
    else
        error "Rama $BRANCH no encontrada en el repositorio remoto"
        exit 1
    fi
}

# Función para verificar el estado del repositorio
verify_repository() {
    log "Verificando estado del repositorio..."
    
    # Verificar rama actual
    CURRENT_BRANCH=$(remote_exec "cd $REMOTE_DIR && git branch --show-current")
    log "Rama actual: $CURRENT_BRANCH"
    
    # Verificar último commit
    LAST_COMMIT=$(remote_exec "cd $REMOTE_DIR && git log --oneline -1")
    log "Último commit: $LAST_COMMIT"
    
    # Verificar archivos nuevos
    NEW_FILES=$(remote_exec "cd $REMOTE_DIR && git status --porcelain")
    if [ -n "$NEW_FILES" ]; then
        warning "Hay archivos modificados o sin commitear:"
        echo "$NEW_FILES"
    else
        success "Repositorio limpio"
    fi
    
    # Verificar que el script existe
    if remote_exec "[ -f $REMOTE_DIR/test/send_en_proves_message.py ]"; then
        success "Script send_en_proves_message.py encontrado"
    else
        error "Script send_en_proves_message.py no encontrado"
        exit 1
    fi
}

# Función para instalar dependencias
install_dependencies() {
    log "Instalando dependencias Python..."
    
    # Verificar si requirements.txt existe
    if remote_exec "[ -f $REMOTE_DIR/requirements.txt ]"; then
        remote_exec "cd $REMOTE_DIR && pip3 install -r requirements.txt"
        success "Dependencias instaladas"
    else
        warning "No se encontró requirements.txt"
    fi
    
    # Instalar requests específicamente si no está
    remote_exec "pip3 install requests"
    success "Módulo requests instalado"
}

# Función para verificar servicios
check_services() {
    log "Verificando servicios del sistema..."
    
    SERVICES=("parking-api" "parking-camera" "parking-schedule-monitor")
    
    for service in "${SERVICES[@]}"; do
        STATUS=$(remote_exec "systemctl is-active ${service}.service")
        if [ "$STATUS" = "active" ]; then
            success "Servicio $service: ACTIVO"
        else
            warning "Servicio $service: INACTIVO"
        fi
    done
}

# Función principal
main() {
    echo "🔄 Actualización de Repositorio en Servidor Remoto v3.1.0"
    echo "========================================================"
    
    # Verificar si el repositorio existe
    if check_repository; then
        # Actualizar repositorio existente
        update_repository
    else
        # Clonar repositorio nuevo
        clone_repository
    fi
    
    # Verificar estado
    verify_repository
    
    # Instalar dependencias
    install_dependencies
    
    # Verificar servicios
    check_services
    
    echo ""
    success "🎉 Repositorio actualizado exitosamente!"
    echo ""
    log "Próximos pasos:"
    echo "1. Ejecutar script de envío: python3 $REMOTE_DIR/test/send_en_proves_message.py"
    echo "2. Verificar conectividad: python3 $REMOTE_DIR/test/send_en_proves_message.py --test"
    echo "3. Revisar logs: journalctl -u parking-api.service -f"
}

# Ejecutar función principal
main "$@" 