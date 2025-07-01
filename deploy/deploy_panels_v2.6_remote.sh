#!/bin/bash

# Script para desplegar la actualización de paneles v2.6 en el servidor remoto
# Autor: Parking Altea Team
# Fecha: $(date +%Y-%m-%d)

set -e

echo "🚀 DESPLIEGUE REMOTO - PANELES v2.6"
echo "===================================="
echo "📅 Fecha: $(date)"
echo "🌐 Servidor: 157.180.91.63"
echo ""

# Configuración
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
PROJECT_DIR="/root/parking_altea"
FRONTEND_DIR="/var/www/parking-altea-frontend"
BACKUP_DIR="/var/www/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para ejecutar comandos remotos
remote_exec() {
    local cmd="$1"
    log_info "Ejecutando: $cmd"
    ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "$cmd"
}

# Función para copiar archivos
remote_copy() {
    local src="$1"
    local dest="$2"
    log_info "Copiando: $src -> $dest"
    scp -o StrictHostKeyChecking=no -r "$src" "$REMOTE_USER@$REMOTE_HOST:$dest"
}

# 1. Verificar conectividad con el servidor
log_info "Verificando conectividad con el servidor..."
if ! ping -c 1 $REMOTE_HOST > /dev/null 2>&1; then
    log_error "No se puede conectar al servidor $REMOTE_HOST"
    exit 1
fi
log_success "Conectividad OK"

# 2. Crear backup del frontend actual
log_info "Creando backup del frontend actual..."
remote_exec "mkdir -p $BACKUP_DIR"
remote_exec "cd $FRONTEND_DIR && tar -czf $BACKUP_DIR/frontend_backup_$TIMESTAMP.tar.gz ."
log_success "Backup creado: frontend_backup_$TIMESTAMP.tar.gz"

# 3. Actualizar código del proyecto
log_info "Actualizando código del proyecto..."
remote_exec "cd $PROJECT_DIR && git fetch origin"
remote_exec "cd $PROJECT_DIR && git reset --hard origin/develop"
log_success "Código actualizado"

# 4. Verificar que los archivos nuevos existen
log_info "Verificando archivos de la actualización..."
remote_exec "cd $PROJECT_DIR && ls -la client/src/services/panelService.js"
remote_exec "cd $PROJECT_DIR && ls -la client/src/pages/Panels.jsx"
remote_exec "cd $PROJECT_DIR && ls -la deploy/update_frontend_panels_v2.6.sh"
remote_exec "cd $PROJECT_DIR && ls -la test/test_panel_service_v2.6.py"
log_success "Archivos verificados"

# 5. Actualizar frontend
log_info "Actualizando frontend..."
remote_exec "cd $FRONTEND_DIR && cp $PROJECT_DIR/client/src/services/panelService.js src/services/"
remote_exec "cd $FRONTEND_DIR && cp $PROJECT_DIR/client/src/pages/Panels.jsx src/pages/"
log_success "Archivos del frontend actualizados"

# 6. Instalar dependencias y construir
log_info "Instalando dependencias y construyendo frontend..."
remote_exec "cd $FRONTEND_DIR && npm install"
remote_exec "cd $FRONTEND_DIR && npm run build"
log_success "Frontend construido"

# 7. Verificar servicios del sistema
log_info "Verificando servicios del sistema..."

# Verificar parking-api
if remote_exec "systemctl is-active --quiet parking-api"; then
    log_success "Servicio parking-api está activo"
else
    log_warning "Servicio parking-api no está activo"
fi

# Verificar parking-camera
if remote_exec "systemctl is-active --quiet parking-camera"; then
    log_success "Servicio parking-camera está activo"
else
    log_warning "Servicio parking-camera no está activo"
fi

# 8. Verificar puertos
log_info "Verificando puertos..."

# Puerto 5789 (Frontend)
if remote_exec "netstat -tlnp | grep -q ':5789'"; then
    log_success "Puerto 5789 (Frontend) está activo"
else
    log_warning "Puerto 5789 (Frontend) no está activo"
fi

# Puerto 6001 (Backend API)
if remote_exec "netstat -tlnp | grep -q ':6001'"; then
    log_success "Puerto 6001 (Backend API) está activo"
else
    log_warning "Puerto 6001 (Backend API) no está activo"
fi

# Puerto 5656 (Servicio v2.6)
if remote_exec "netstat -tlnp | grep -q ':5656'"; then
    log_success "Puerto 5656 (Servicio v2.6) está activo"
else
    log_warning "Puerto 5656 (Servicio v2.6) no está activo"
fi

# 9. Ejecutar pruebas del servicio v2.6
log_info "Ejecutando pruebas del servicio v2.6..."
remote_exec "cd $PROJECT_DIR && python3 test/test_panel_service_v2.6.py"
if [ $? -eq 0 ]; then
    log_success "Pruebas del servicio v2.6 pasaron"
else
    log_warning "Algunas pruebas del servicio v2.6 fallaron"
fi

# 10. Reiniciar servicios si es necesario
log_info "Reiniciando servicios..."
remote_exec "systemctl restart parking-api"
remote_exec "systemctl restart parking-camera"
log_success "Servicios reiniciados"

# 11. Verificar estado final
log_info "Verificando estado final..."

# Verificar que los servicios están activos
sleep 5
if remote_exec "systemctl is-active --quiet parking-api"; then
    log_success "parking-api activo después del reinicio"
else
    log_error "parking-api no está activo después del reinicio"
fi

if remote_exec "systemctl is-active --quiet parking-camera"; then
    log_success "parking-camera activo después del reinicio"
else
    log_error "parking-camera no está activo después del reinicio"
fi

# 12. Información final
echo ""
echo "🎉 DESPLIEGUE COMPLETADO"
echo "========================"
echo ""
echo "📋 Resumen de cambios:"
echo "  • Frontend actualizado para usar servicio v2.6"
echo "  • Nuevo endpoint: http://157.180.91.63:5656/sendMulti"
echo "  • Soporte para 7 colores diferentes"
echo "  • Mensajes en valenciano por defecto"
echo "  • Tamaño de texto 2 por defecto"
echo ""
echo "🔗 URLs importantes:"
echo "  • Frontend: http://157.180.91.63:5789"
echo "  • Backend API: http://157.180.91.63:6001"
echo "  • Servicio v2.6: http://157.180.91.63:5656"
echo ""
echo "📁 Backup creado: $BACKUP_DIR/frontend_backup_$TIMESTAMP.tar.gz"
echo ""
echo "✅ El frontend ahora usa el nuevo servicio de paneles v2.6"
echo "🌐 Puedes acceder al menú de paneles para probar las nuevas funcionalidades"
echo ""

# 13. Mostrar comandos útiles
echo "🛠️  Comandos útiles para monitoreo:"
echo "  • Ver logs del servicio: ssh root@157.180.91.63 'journalctl -u parking-api -f'"
echo "  • Verificar estado: ssh root@157.180.91.63 'systemctl status parking-api parking-camera'"
echo "  • Probar servicio: ssh root@157.180.91.63 'cd /root/parking_altea && python3 test/test_panel_service_v2.6.py'"
echo "  • Verificar puertos: ssh root@157.180.91.63 'netstat -tlnp | grep -E \":(5789|6001|5656)\"'"
echo ""

log_success "Despliegue completado exitosamente" 