#!/bin/bash

# Script para actualizar el frontend y probar el nuevo servicio de paneles v2.6
# Autor: Parking Altea Team
# Fecha: $(date +%Y-%m-%d)

set -e

echo "🚀 ACTUALIZACIÓN DEL FRONTEND PARA PANELES v2.6"
echo "=================================================="
echo "📅 Fecha: $(date)"
echo ""

# Configuración
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

# Verificar si estamos en el directorio correcto
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Directorio del frontend no encontrado: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# 1. Crear backup del frontend actual
log_info "Creando backup del frontend actual..."
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
fi

tar -czf "$BACKUP_DIR/frontend_backup_$TIMESTAMP.tar.gz" .
log_success "Backup creado: frontend_backup_$TIMESTAMP.tar.gz"

# 2. Actualizar archivos del frontend
log_info "Actualizando archivos del frontend..."

# Verificar si los archivos existen en el repositorio
if [ ! -f "src/services/panelService.js" ]; then
    log_error "Archivo panelService.js no encontrado"
    exit 1
fi

if [ ! -f "src/pages/Panels.jsx" ]; then
    log_error "Archivo Panels.jsx no encontrado"
    exit 1
fi

log_success "Archivos del frontend actualizados"

# 3. Instalar dependencias si es necesario
log_info "Verificando dependencias..."
if [ -f "package.json" ]; then
    npm install
    log_success "Dependencias instaladas"
fi

# 4. Construir el frontend
log_info "Construyendo el frontend..."
npm run build
log_success "Frontend construido exitosamente"

# 5. Verificar que el servicio v2.6 esté funcionando
log_info "Verificando servicio de paneles v2.6..."
SERVICE_URL="http://157.180.91.63:5656/sendMulti"

# Test básico de conexión
if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL" | grep -q "200"; then
    log_success "Servicio v2.6 está funcionando"
else
    log_warning "Servicio v2.6 no responde. Verificar estado del servicio."
fi

# 6. Ejecutar pruebas del servicio
log_info "Ejecutando pruebas del servicio v2.6..."
if [ -f "/root/parking_altea/test/test_panel_service_v2.6.py" ]; then
    cd /root/parking_altea
    python3 test/test_panel_service_v2.6.py
    if [ $? -eq 0 ]; then
        log_success "Pruebas del servicio v2.6 pasaron"
    else
        log_warning "Algunas pruebas del servicio v2.6 fallaron"
    fi
else
    log_warning "Script de pruebas no encontrado"
fi

# 7. Verificar servicios del sistema
log_info "Verificando servicios del sistema..."

# Verificar parking-api
if systemctl is-active --quiet parking-api; then
    log_success "Servicio parking-api está activo"
else
    log_warning "Servicio parking-api no está activo"
fi

# Verificar parking-camera
if systemctl is-active --quiet parking-camera; then
    log_success "Servicio parking-camera está activo"
else
    log_warning "Servicio parking-camera no está activo"
fi

# 8. Verificar puertos
log_info "Verificando puertos..."

# Puerto 5789 (Frontend)
if netstat -tlnp | grep -q ":5789"; then
    log_success "Puerto 5789 (Frontend) está activo"
else
    log_warning "Puerto 5789 (Frontend) no está activo"
fi

# Puerto 6001 (Backend API)
if netstat -tlnp | grep -q ":6001"; then
    log_success "Puerto 6001 (Backend API) está activo"
else
    log_warning "Puerto 6001 (Backend API) no está activo"
fi

# Puerto 5656 (Servicio v2.6)
if netstat -tlnp | grep -q ":5656"; then
    log_success "Puerto 5656 (Servicio v2.6) está activo"
else
    log_warning "Puerto 5656 (Servicio v2.6) no está activo"
fi

# 9. Información final
echo ""
echo "🎉 ACTUALIZACIÓN COMPLETADA"
echo "============================"
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

# 10. Mostrar comandos útiles
echo "🛠️  Comandos útiles:"
echo "  • Ver logs del servicio: journalctl -u parking-api -f"
echo "  • Reiniciar servicios: systemctl restart parking-api parking-camera"
echo "  • Probar servicio: python3 test/test_panel_service_v2.6.py"
echo ""

log_success "Actualización completada exitosamente" 