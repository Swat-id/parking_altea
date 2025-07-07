#!/bin/bash

# Script de Mantenimiento v3.1.0 - Parking Altea
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

# Función para mostrar menú
show_menu() {
    echo ""
    echo "🔧 Mantenimiento v3.1.0 - Parking Altea"
    echo "======================================="
    echo "1.  Verificar estado del sistema"
    echo "2.  Reiniciar servicios"
    echo "3.  Ver logs en tiempo real"
    echo "4.  Crear backup manual"
    echo "5.  Limpiar logs antiguos"
    echo "6.  Verificar espacio en disco"
    echo "7.  Actualizar dependencias"
    echo "8.  Verificar conectividad de cámaras"
    echo "9.  Verificar base de datos"
    echo "10. Reiniciar sistema completo"
    echo "0.  Salir"
    echo ""
}

# Función para verificar estado del sistema
check_system_status() {
    log "Verificando estado del sistema..."
    
    echo "=== SERVICIOS ==="
    remote_exec "systemctl status parking-api.service --no-pager"
    echo ""
    remote_exec "systemctl status parking-camera.service --no-pager"
    echo ""
    remote_exec "systemctl status parking-schedule-monitor.service --no-pager"
    
    echo "=== ENDPOINTS ==="
    if remote_exec "curl -f http://localhost:5000/health" > /dev/null 2>&1; then
        success "API: OK"
    else
        error "API: ERROR"
    fi
    
    if remote_exec "curl -f http://localhost" > /dev/null 2>&1; then
        success "Frontend: OK"
    else
        error "Frontend: ERROR"
    fi
    
    echo "=== RECURSOS ==="
    remote_exec "df -h"
    echo ""
    remote_exec "free -h"
    echo ""
    remote_exec "uptime"
    
    success "Verificación completada"
}

# Función para reiniciar servicios
restart_services() {
    log "Reiniciando servicios..."
    
    remote_exec "systemctl restart parking-api.service"
    remote_exec "systemctl restart parking-camera.service"
    remote_exec "systemctl restart parking-schedule-monitor.service"
    
    # Esperar a que los servicios se inicien
    sleep 10
    
    # Verificar estado
    SERVICES=("parking-api" "parking-camera" "parking-schedule-monitor")
    
    for service in "${SERVICES[@]}"; do
        STATUS=$(remote_exec "systemctl is-active ${service}.service")
        if [ "$STATUS" = "active" ]; then
            success "Servicio $service reiniciado correctamente"
        else
            error "Servicio $service no se pudo reiniciar"
        fi
    done
}

# Función para ver logs en tiempo real
show_logs() {
    log "Mostrando logs en tiempo real..."
    
    echo "Selecciona el servicio para ver logs:"
    echo "1. API Server"
    echo "2. Camera Server"
    echo "3. Schedule Monitor"
    echo "4. Nginx"
    echo "5. Sistema"
    
    read -p "Selección: " LOG_CHOICE
    
    case $LOG_CHOICE in
        1)
            remote_exec "journalctl -u parking-api.service -f"
            ;;
        2)
            remote_exec "journalctl -u parking-camera.service -f"
            ;;
        3)
            remote_exec "journalctl -u parking-schedule-monitor.service -f"
            ;;
        4)
            remote_exec "tail -f /var/log/nginx/parking_altea_*.log"
            ;;
        5)
            remote_exec "tail -f /var/log/syslog | grep parking"
            ;;
        *)
            error "Opción inválida"
            ;;
    esac
}

# Función para crear backup manual
create_manual_backup() {
    log "Creando backup manual..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="parking_altea_manual_backup_$TIMESTAMP"
    
    remote_exec "mkdir -p $BACKUP_DIR"
    remote_exec "cd $REMOTE_DIR && tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz ."
    
    # Backup de base de datos
    remote_exec "sudo -u postgres pg_dump parking_altea > $BACKUP_DIR/${BACKUP_NAME}_database.sql"
    
    if [ $? -eq 0 ]; then
        success "Backup creado: $BACKUP_NAME"
        remote_exec "ls -la $BACKUP_DIR/$BACKUP_NAME*"
    else
        error "Error creando backup"
    fi
}

# Función para limpiar logs antiguos
cleanup_old_logs() {
    log "Limpiando logs antiguos..."
    
    # Limpiar logs del sistema (más de 30 días)
    remote_exec "find /var/log -name '*.log' -mtime +30 -delete"
    remote_exec "find /var/log -name '*.gz' -mtime +30 -delete"
    
    # Limpiar logs de la aplicación (más de 7 días)
    remote_exec "find $REMOTE_DIR/logs -name '*.log' -mtime +7 -delete"
    
    # Limpiar backups antiguos (más de 30 días)
    remote_exec "find $BACKUP_DIR -name '*.tar.gz' -mtime +30 -delete"
    remote_exec "find $BACKUP_DIR -name '*.sql' -mtime +30 -delete"
    
    success "Logs antiguos limpiados"
}

# Función para verificar espacio en disco
check_disk_space() {
    log "Verificando espacio en disco..."
    
    echo "=== USO DE DISCO ==="
    remote_exec "df -h"
    
    echo ""
    echo "=== DIRECTORIOS MÁS GRANDES ==="
    remote_exec "du -h --max-depth=1 $REMOTE_DIR | sort -hr"
    
    echo ""
    echo "=== BACKUPS ==="
    remote_exec "du -h --max-depth=1 $BACKUP_DIR | sort -hr"
    
    echo ""
    echo "=== LOGS ==="
    remote_exec "du -h --max-depth=1 /var/log | sort -hr | head -10"
}

# Función para actualizar dependencias
update_dependencies() {
    log "Actualizando dependencias..."
    
    # Actualizar sistema
    remote_exec "apt-get update && apt-get upgrade -y"
    
    # Actualizar dependencias Python
    remote_exec "cd $REMOTE_DIR && source venv/bin/activate && pip install --upgrade pip"
    remote_exec "cd $REMOTE_DIR && source venv/bin/activate && pip install -r requirements.txt --upgrade"
    
    # Actualizar dependencias Node.js
    remote_exec "npm update -g"
    
    success "Dependencias actualizadas"
}

# Función para verificar conectividad de cámaras
check_camera_connectivity() {
    log "Verificando conectividad de cámaras..."
    
    # Obtener IPs de cámaras desde la base de datos
    CAMERA_IPS=$(remote_exec "sudo -u postgres psql -d parking_altea -t -c \"SELECT DISTINCT ip_address FROM cameras WHERE is_active = true;\"")
    
    if [ -n "$CAMERA_IPS" ]; then
        echo "Verificando conectividad con cámaras:"
        for ip in $CAMERA_IPS; do
            if remote_exec "ping -c 1 $ip" > /dev/null 2>&1; then
                success "Cámara $ip: CONECTADA"
            else
                error "Cámara $ip: SIN CONEXIÓN"
            fi
        done
    else
        warning "No se encontraron cámaras activas en la base de datos"
    fi
}

# Función para verificar base de datos
check_database() {
    log "Verificando base de datos..."
    
    echo "=== CONEXIÓN ==="
    if remote_exec "sudo -u postgres psql -d parking_altea -c 'SELECT version();'" > /dev/null 2>&1; then
        success "Conexión a PostgreSQL: OK"
    else
        error "Conexión a PostgreSQL: ERROR"
    fi
    
    echo ""
    echo "=== TABLAS ==="
    remote_exec "sudo -u postgres psql -d parking_altea -c \"SELECT table_name, COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' GROUP BY table_name ORDER BY table_name;\""
    
    echo ""
    echo "=== TAMAÑO DE BASE DE DATOS ==="
    remote_exec "sudo -u postgres psql -d parking_altea -c \"SELECT pg_size_pretty(pg_database_size('parking_altea'));\""
    
    echo ""
    echo "=== CONEXIONES ACTIVAS ==="
    remote_exec "sudo -u postgres psql -d parking_altea -c \"SELECT count(*) FROM pg_stat_activity WHERE datname = 'parking_altea';\""
}

# Función para reiniciar sistema completo
restart_system() {
    warning "⚠️  ¿Estás seguro de que quieres reiniciar el sistema completo?"
    read -p "Esto detendrá todos los servicios. Continuar? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Reiniciando sistema..."
        remote_exec "reboot"
        echo "Sistema reiniciándose. Espera unos minutos antes de verificar el estado."
    else
        log "Reinicio cancelado"
    fi
}

# Función principal
main() {
    while true; do
        show_menu
        read -p "Selecciona una opción: " choice
        
        case $choice in
            1)
                check_system_status
                ;;
            2)
                restart_services
                ;;
            3)
                show_logs
                ;;
            4)
                create_manual_backup
                ;;
            5)
                cleanup_old_logs
                ;;
            6)
                check_disk_space
                ;;
            7)
                update_dependencies
                ;;
            8)
                check_camera_connectivity
                ;;
            9)
                check_database
                ;;
            10)
                restart_system
                ;;
            0)
                log "Saliendo..."
                exit 0
                ;;
            *)
                error "Opción inválida"
                ;;
        esac
        
        echo ""
        read -p "Presiona Enter para continuar..."
    done
}

# Ejecutar función principal
main "$@" 