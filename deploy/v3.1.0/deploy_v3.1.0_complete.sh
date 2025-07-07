#!/bin/bash

# Script de Despliegue Completo v3.1.0 - Parking Altea
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

set -e  # Salir en caso de error

# Configuración del servidor
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
NC='\033[0m' # No Color

# Función para logging
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

# Función para copiar archivos
remote_copy() {
    sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$REMOTE_USER@$REMOTE_HOST:$2"
}

# Función para crear backup
create_backup() {
    log "Creando backup del sistema actual..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="parking_altea_backup_v3.1.0_$TIMESTAMP"
    
    remote_exec "mkdir -p $BACKUP_DIR"
    remote_exec "cd $REMOTE_DIR && tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz ."
    
    if [ $? -eq 0 ]; then
        success "Backup creado: $BACKUP_NAME.tar.gz"
    else
        error "Error creando backup"
        exit 1
    fi
}

# Función para verificar requisitos
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar conexión al servidor
    if ! remote_exec "echo 'Conexión exitosa'" > /dev/null 2>&1; then
        error "No se puede conectar al servidor remoto"
        exit 1
    fi
    
    # Verificar dependencias locales
    if ! command -v sshpass &> /dev/null; then
        error "sshpass no está instalado. Instalar con: sudo apt-get install sshpass"
        exit 1
    fi
    
    # Verificar archivos necesarios
    if [ ! -f "src/api_server.py" ]; then
        error "No se encuentra api_server.py"
        exit 1
    fi
    
    if [ ! -d "client" ]; then
        error "No se encuentra el directorio client"
        exit 1
    fi
    
    success "Requisitos verificados correctamente"
}

# Función para detener servicios
stop_services() {
    log "Deteniendo servicios actuales..."
    
    remote_exec "systemctl stop parking-api.service || true"
    remote_exec "systemctl stop parking-camera.service || true"
    remote_exec "systemctl stop parking-schedule-monitor.service || true"
    
    success "Servicios detenidos"
}

# Función para actualizar backend
update_backend() {
    log "Actualizando backend..."
    
    # Crear directorio temporal
    remote_exec "mkdir -p /tmp/parking_backend_update"
    
    # Copiar archivos del backend
    remote_copy "src/" "/tmp/parking_backend_update/"
    remote_copy "requirements.txt" "/tmp/parking_backend_update/"
    
    # Actualizar archivos en el servidor
    remote_exec "cp -r /tmp/parking_backend_update/* $REMOTE_DIR/"
    remote_exec "rm -rf /tmp/parking_backend_update"
    
    # Instalar dependencias
    remote_exec "cd $REMOTE_DIR && pip3 install -r requirements.txt --upgrade"
    
    # Actualizar permisos
    remote_exec "chmod +x $REMOTE_DIR/api_server.py"
    remote_exec "chmod +x $REMOTE_DIR/camera_server.py"
    remote_exec "chmod +x $REMOTE_DIR/schedule_monitor_service.py"
    
    success "Backend actualizado"
}

# Función para actualizar base de datos
update_database() {
    log "Actualizando base de datos..."
    
    # Copiar scripts de migración
    remote_copy "src/migrate_to_v3_1_0.py" "$REMOTE_DIR/"
    remote_copy "src/verify_migration_v3_1_0.py" "$REMOTE_DIR/"
    remote_copy "src/assign_parkings_to_users.py" "$REMOTE_DIR/"
    
    # Ejecutar migración
    remote_exec "cd $REMOTE_DIR && python3 migrate_to_v3_1_0.py"
    
    # Verificar migración
    remote_exec "cd $REMOTE_DIR && python3 verify_migration_v3_1_0.py"
    
    # Asignar parkings a usuarios existentes
    remote_exec "cd $REMOTE_DIR && python3 assign_parkings_to_users.py"
    
    success "Base de datos actualizada"
}

# Función para actualizar frontend
update_frontend() {
    log "Actualizando frontend..."
    
    # Crear directorio temporal para build
    BUILD_DIR="/tmp/parking_frontend_build"
    remote_exec "mkdir -p $BUILD_DIR"
    
    # Copiar código del frontend
    remote_copy "client/" "$BUILD_DIR/"
    
    # Instalar dependencias y hacer build
    remote_exec "cd $BUILD_DIR && npm install"
    remote_exec "cd $BUILD_DIR && npm run build"
    
    # Copiar build al directorio de producción
    remote_exec "rm -rf $REMOTE_DIR/static"
    remote_exec "cp -r $BUILD_DIR/dist/* $REMOTE_DIR/static/"
    
    # Limpiar directorio temporal
    remote_exec "rm -rf $BUILD_DIR"
    
    success "Frontend actualizado"
}

# Función para actualizar servicios systemd
update_services() {
    log "Actualizando servicios systemd..."
    
    # Copiar archivos de servicio
    remote_copy "deploy/v3.1.0/parking-api.service" "/etc/systemd/system/"
    remote_copy "deploy/v3.1.0/parking-camera.service" "/etc/systemd/system/"
    remote_copy "deploy/v3.1.0/parking-schedule-monitor.service" "/etc/systemd/system/"
    
    # Recargar systemd
    remote_exec "systemctl daemon-reload"
    
    # Habilitar servicios
    remote_exec "systemctl enable parking-api.service"
    remote_exec "systemctl enable parking-camera.service"
    remote_exec "systemctl enable parking-schedule-monitor.service"
    
    success "Servicios systemd actualizados"
}

# Función para iniciar servicios
start_services() {
    log "Iniciando servicios..."
    
    remote_exec "systemctl start parking-api.service"
    remote_exec "systemctl start parking-camera.service"
    remote_exec "systemctl start parking-schedule-monitor.service"
    
    # Esperar un momento para que los servicios se inicien
    sleep 5
    
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
    sleep 10  # Esperar a que los servicios estén completamente iniciados
    
    if remote_exec "curl -f http://localhost:5000/health" > /dev/null 2>&1; then
        success "API endpoint verificado"
    else
        error "API endpoint no responde"
        exit 1
    fi
}

# Función para ejecutar tests post-despliegue
run_post_deployment_tests() {
    log "Ejecutando tests post-despliegue..."
    
    # Copiar scripts de test
    remote_copy "test/v3.1.0/" "$REMOTE_DIR/tests/"
    
    # Ejecutar tests
    remote_exec "cd $REMOTE_DIR && python3 tests/test_admin_complete.py"
    
    success "Tests post-despliegue completados"
}

# Función para mostrar información del despliegue
show_deployment_info() {
    log "Información del despliegue v3.1.0:"
    echo "=================================="
    echo "Servidor: $REMOTE_HOST"
    echo "Directorio: $REMOTE_DIR"
    echo "Backup: $BACKUP_DIR"
    echo "Servicios:"
    echo "  - parking-api.service"
    echo "  - parking-camera.service"
    echo "  - parking-schedule-monitor.service"
    echo ""
    echo "Endpoints:"
    echo "  - API: http://$REMOTE_HOST:5000"
    echo "  - Frontend: http://$REMOTE_HOST"
    echo ""
    echo "Logs:"
    echo "  - API: journalctl -u parking-api.service -f"
    echo "  - Camera: journalctl -u parking-camera.service -f"
    echo "  - Schedule: journalctl -u parking-schedule-monitor.service -f"
}

# Función principal
main() {
    echo "🚀 Despliegue Completo v3.1.0 - Parking Altea"
    echo "=============================================="
    
    show_deployment_info
    
    read -p "¿Continuar con el despliegue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Despliegue cancelado"
        exit 0
    fi
    
    # Ejecutar pasos del despliegue
    check_requirements
    create_backup
    stop_services
    update_backend
    update_database
    update_frontend
    update_services
    start_services
    verify_services
    run_post_deployment_tests
    
    echo ""
    success "🎉 Despliegue v3.1.0 completado exitosamente!"
    echo ""
    log "El sistema está disponible en: http://$REMOTE_HOST"
    log "Para ver logs: journalctl -u parking-api.service -f"
}

# Ejecutar función principal
main "$@" 