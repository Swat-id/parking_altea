#!/bin/bash

# Script de Rollback v4.1.0
# Revierte los cambios en caso de problemas

set -e

echo "=== ROLLBACK v4.1.0 ==="
echo "Servidor: 157.180.91.63"
echo "Fecha: $(date)"
echo

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Variables
PROJECT_DIR="/opt/parking_altea"
BACKUP_DIR=""
PUSH_SERVICE_PORT=3535

# Verificar permisos de root
if [ "$EUID" -ne 0 ]; then
    log_error "Este script debe ejecutarse como root"
    exit 1
fi

cd "$PROJECT_DIR"

# Buscar el backup más reciente
BACKUP_DIR=$(find /opt/parking_altea/backups -type d -name "20*" | sort -r | head -1)

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    log_error "No se encontró directorio de backup reciente"
    log_info "Directorios disponibles:"
    ls -la /opt/parking_altea/backups/ 2>/dev/null || echo "No hay backups"
    exit 1
fi

log_info "Usando backup: $BACKUP_DIR"

echo
read -p "¿Estás seguro de que quieres hacer rollback? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Rollback cancelado"
    exit 0
fi

log_step "1. Deteniendo nuevos servicios..."

# Detener servicio push
if systemctl is-active --quiet parking-sensor-push; then
    log_info "Deteniendo parking-sensor-push..."
    systemctl stop parking-sensor-push
    systemctl disable parking-sensor-push
fi

# Remover archivo de servicio
if [ -f "/etc/systemd/system/parking-sensor-push.service" ]; then
    rm /etc/systemd/system/parking-sensor-push.service
    systemctl daemon-reload
fi

log_step "2. Liberando puerto $PUSH_SERVICE_PORT..."

if lsof -i :$PUSH_SERVICE_PORT > /dev/null 2>&1; then
    PID=$(lsof -t -i :$PUSH_SERVICE_PORT)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        log_info "Proceso $PID terminado en puerto $PUSH_SERVICE_PORT"
    fi
fi

log_step "3. Restaurando código fuente..."

# Hacer backup del estado actual por si acaso
ROLLBACK_BACKUP="/opt/parking_altea/backups/rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ROLLBACK_BACKUP"
tar -czf "$ROLLBACK_BACKUP/pre_rollback.tar.gz" --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='__pycache__' --exclude='logs' .

# Restaurar código
if [ -f "$BACKUP_DIR/source_code.tar.gz" ]; then
    log_info "Restaurando código fuente desde backup..."
    tar -xzf "$BACKUP_DIR/source_code.tar.gz" -C "$PROJECT_DIR" --overwrite
    log_info "✅ Código fuente restaurado"
else
    log_error "Backup de código fuente no encontrado"
    exit 1
fi

log_step "4. Evaluando rollback de base de datos..."

log_warning "ATENCIÓN: El rollback de base de datos puede causar pérdida de datos"
echo
read -p "¿Quieres restaurar también la base de datos? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "$BACKUP_DIR/database_backup.sql" ]; then
        log_info "Creando backup de seguridad de BD actual..."
        sudo -u postgres pg_dump parking_db > "$ROLLBACK_BACKUP/current_database.sql"
        
        log_warning "Restaurando base de datos desde backup..."
        sudo -u postgres dropdb parking_db
        sudo -u postgres createdb parking_db
        sudo -u postgres psql parking_db < "$BACKUP_DIR/database_backup.sql"
        log_info "✅ Base de datos restaurada"
    else
        log_error "Backup de base de datos no encontrado"
    fi
else
    log_info "Manteniendo base de datos actual (recomendado)"
fi

log_step "5. Restaurando servicios systemd..."

if [ -d "$BACKUP_DIR/systemd" ]; then
    log_info "Restaurando archivos de servicios..."
    cp "$BACKUP_DIR/systemd"/*.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload
    log_info "✅ Servicios restaurados"
fi

log_step "6. Reiniciando servicios existentes..."

# Reiniciar API
if systemctl is-enabled --quiet parking-api; then
    log_info "Reiniciando parking-api..."
    systemctl restart parking-api
    sleep 2
    if systemctl is-active --quiet parking-api; then
        log_info "✅ parking-api reiniciado"
    else
        log_error "❌ Error reiniciando parking-api"
    fi
fi

# Reiniciar panel worker si existe
if systemctl is-enabled --quiet parking-panel-worker; then
    log_info "Reiniciando parking-panel-worker..."
    systemctl restart parking-panel-worker
    sleep 2
    if systemctl is-active --quiet parking-panel-worker; then
        log_info "✅ parking-panel-worker reiniciado"
    else
        log_warning "⚠️  parking-panel-worker con problemas"
    fi
fi

log_step "7. Limpiando configuración de firewall..."

# Remover regla del puerto 3535 si existe
if command -v ufw &> /dev/null && ufw status | grep -q "$PUSH_SERVICE_PORT"; then
    log_info "Removiendo regla de firewall para puerto $PUSH_SERVICE_PORT..."
    ufw delete allow $PUSH_SERVICE_PORT/tcp
fi

log_step "8. Validando rollback..."

# Verificar servicios
log_info "Estado de servicios después del rollback:"
systemctl is-active parking-api && log_info "✅ parking-api: ACTIVO" || log_warning "⚠️  parking-api: INACTIVO"
systemctl is-active parking-sensor-push && log_warning "⚠️  parking-sensor-push: AÚN ACTIVO" || log_info "✅ parking-sensor-push: DETENIDO"

# Verificar puertos
if lsof -i :5000 > /dev/null 2>&1; then
    log_info "✅ Puerto 5000 (API): ACTIVO"
else
    log_warning "⚠️  Puerto 5000 (API): INACTIVO"
fi

if lsof -i :$PUSH_SERVICE_PORT > /dev/null 2>&1; then
    log_warning "⚠️  Puerto $PUSH_SERVICE_PORT aún en uso"
else
    log_info "✅ Puerto $PUSH_SERVICE_PORT: LIBERADO"
fi

echo
log_info "=== RESUMEN ROLLBACK ==="
echo
echo "🔄 Rollback completado"
echo "📅 Fecha: $(date)"
echo "💾 Backup usado: $BACKUP_DIR"
echo "💾 Backup pre-rollback: $ROLLBACK_BACKUP"
echo
echo "📊 CAMBIOS REVERTIDOS:"
echo "  • ❌ Servicio push puerto $PUSH_SERVICE_PORT deshabilitado"
echo "  • ❌ Nuevas funcionalidades de sensores revertidas"
echo "  • ❌ Dashboard avanzado revertido"
echo "  • ✅ Sistema vuelto al estado anterior"
echo
echo "🔧 VERIFICACIONES RECOMENDADAS:"
echo "  • Verificar funcionamiento de API existente"
echo "  • Comprobar acceso al frontend"
echo "  • Validar que no hay errores en logs"
echo
echo "✅ ROLLBACK COMPLETADO"
