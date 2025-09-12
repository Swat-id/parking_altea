#!/bin/bash

# Script de Despliegue - Nueva Lógica de Cálculo de Deltas v4.0.0
# Autor: Sistema de Parking Altea
# Fecha: 12 de septiembre de 2025

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
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

# Variables
SERVICE_NAME="parking-camera.service"
BACKUP_DIR="/opt/parking_altea/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_LOG="/opt/parking_altea/logs/deployment_v4_0_0_${TIMESTAMP}.log"

# Crear directorio de logs si no existe
mkdir -p /opt/parking_altea/logs

# Función para logging a archivo
log_to_file() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEPLOYMENT_LOG"
}

echo "🚀 DESPLIEGUE NUEVA LÓGICA DE CÁLCULO DE DELTAS v4.0.0"
echo "============================================================"
echo "Fecha: $(date)"
echo "Log de despliegue: $DEPLOYMENT_LOG"
echo

# Verificar que estamos en el directorio correcto
if [ ! -f "src/camera_server.py" ]; then
    log_error "No se encuentra src/camera_server.py. Ejecutar desde el directorio raíz del proyecto."
    exit 1
fi

log_info "Iniciando despliegue de nueva lógica de deltas v4.0.0..."
log_to_file "Inicio de despliegue v4.0.0"

# PASO 1: Backup del estado actual
log_info "PASO 1: Creando backup del estado actual..."
mkdir -p "$BACKUP_DIR"

# Backup del archivo principal
cp src/camera_server.py "$BACKUP_DIR/camera_server.py.backup.$TIMESTAMP"
log_success "Backup creado: $BACKUP_DIR/camera_server.py.backup.$TIMESTAMP"
log_to_file "Backup creado exitosamente"

# PASO 2: Verificar estado del servicio antes del despliegue
log_info "PASO 2: Verificando estado actual del servicio..."
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Servicio $SERVICE_NAME está activo"
    SERVICE_WAS_RUNNING=true
else
    log_warning "Servicio $SERVICE_NAME no está activo"
    SERVICE_WAS_RUNNING=false
fi

# PASO 3: Verificar feature flag
log_info "PASO 3: Verificando configuración del feature flag..."
if grep -q "USE_NEW_DELTA_LOGIC = True" src/camera_server.py; then
    log_success "Feature flag USE_NEW_DELTA_LOGIC está configurado como True"
    log_to_file "Feature flag configurado correctamente"
else
    log_error "Feature flag USE_NEW_DELTA_LOGIC no está configurado como True"
    log_to_file "ERROR: Feature flag mal configurado"
    exit 1
fi

# PASO 4: Verificar que las nuevas funciones están presentes
log_info "PASO 4: Verificando implementación de nuevas funciones..."
functions_to_check=(
    "detect_camera_reset_new_logic"
    "calculate_deltas_new_logic" 
    "validate_delta_thresholds"
)

for func in "${functions_to_check[@]}"; do
    if grep -q "def $func" src/camera_server.py; then
        log_success "Función $func encontrada"
    else
        log_error "Función $func no encontrada"
        log_to_file "ERROR: Función $func faltante"
        exit 1
    fi
done

# PASO 5: Reiniciar servicio
log_info "PASO 5: Reiniciando servicio de cámaras..."
if [ "$SERVICE_WAS_RUNNING" = true ]; then
    systemctl restart $SERVICE_NAME
    log_success "Servicio $SERVICE_NAME reiniciado"
    log_to_file "Servicio reiniciado exitosamente"
else
    systemctl start $SERVICE_NAME
    log_success "Servicio $SERVICE_NAME iniciado"
    log_to_file "Servicio iniciado exitosamente"
fi

# PASO 6: Verificar que el servicio inició correctamente
log_info "PASO 6: Verificando estado del servicio después del reinicio..."
sleep 5

if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Servicio $SERVICE_NAME está activo después del reinicio"
    log_to_file "Servicio activo post-reinicio"
else
    log_error "Servicio $SERVICE_NAME falló al iniciar"
    log_to_file "ERROR: Servicio falló al iniciar"
    
    # Mostrar logs de error
    log_error "Logs de error del servicio:"
    journalctl -u $SERVICE_NAME --since "5 minutes ago" --no-pager
    
    # Rollback automático
    log_warning "Iniciando rollback automático..."
    cp "$BACKUP_DIR/camera_server.py.backup.$TIMESTAMP" src/camera_server.py
    systemctl restart $SERVICE_NAME
    log_error "Rollback completado. Revise los logs para diagnosticar el problema."
    log_to_file "Rollback ejecutado debido a fallo en inicio"
    exit 1
fi

# PASO 7: Verificar logs de nueva lógica
log_info "PASO 7: Verificando activación de nueva lógica en logs..."
sleep 10

if journalctl -u $SERVICE_NAME --since "2 minutes ago" | grep -q "NEW DELTA LOGIC ENABLED"; then
    log_success "Nueva lógica v4.0.0 activada correctamente"
    log_to_file "Nueva lógica activada exitosamente"
else
    log_warning "No se detectó mensaje de activación de nueva lógica en logs"
    log_to_file "WARNING: Mensaje de activación no detectado"
    
    log_info "Logs recientes del servicio:"
    journalctl -u $SERVICE_NAME --since "2 minutes ago" --no-pager
fi

# PASO 8: Ejecutar tests funcionales básicos
log_info "PASO 8: Ejecutando tests funcionales básicos..."

# Test de conectividad
if curl -s -f http://localhost:6400/camera > /dev/null; then
    log_success "Endpoint /camera responde correctamente"
    log_to_file "Test de conectividad exitoso"
else
    log_error "Endpoint /camera no responde"
    log_to_file "ERROR: Endpoint no responde"
fi

# PASO 9: Configurar monitorización
log_info "PASO 9: Configurando monitorización post-despliegue..."

# Crear script de monitorización
cat > /opt/parking_altea/scripts/monitor_v4_0_0.sh << 'EOF'
#!/bin/bash
echo "=== MONITORIZACIÓN NUEVA LÓGICA v4.0.0 ==="
echo "Fecha: $(date)"
echo

# Estadísticas de procesamiento
echo "📊 ESTADÍSTICAS (últimas 24h):"
journalctl -u parking-camera.service --since "24 hours ago" | \
  grep -c "NEW LOGIC - Delta final" | \
  xargs -I {} echo "Mensajes procesados con nueva lógica: {}"

journalctl -u parking-camera.service --since "24 hours ago" | \
  grep -c "Reset detected (NEW LOGIC)" | \
  xargs -I {} echo "Reinicios detectados: {}"

journalctl -u parking-camera.service --since "24 hours ago" | \
  grep -c "DUPLICATE MESSAGE DETECTED (NEW LOGIC)" | \
  xargs -I {} echo "Duplicados detectados: {}"

# Errores
echo
echo "⚠️  ERRORES:"
journalctl -u parking-camera.service --since "24 hours ago" | \
  grep -i "error.*new logic" | wc -l | \
  xargs -I {} echo "Errores con nueva lógica: {}"

echo
echo "🔄 Estado del servicio:"
systemctl status parking-camera.service --no-pager -l
EOF

chmod +x /opt/parking_altea/scripts/monitor_v4_0_0.sh
log_success "Script de monitorización creado: /opt/parking_altea/scripts/monitor_v4_0_0.sh"
log_to_file "Script de monitorización configurado"

# PASO 10: Crear script de rollback rápido
log_info "PASO 10: Creando script de rollback rápido..."

cat > /opt/parking_altea/scripts/rollback_v4_0_0.sh << EOF
#!/bin/bash
echo "🔄 ROLLBACK RÁPIDO v4.0.0"
echo "========================="

# Opción 1: Cambiar feature flag
echo "Opción 1: Desactivar nueva lógica (cambiar feature flag)"
read -p "¿Desactivar nueva lógica? (y/N): " response
if [[ "\$response" =~ ^[Yy]$ ]]; then
    sed -i 's/USE_NEW_DELTA_LOGIC = True/USE_NEW_DELTA_LOGIC = False/' src/camera_server.py
    systemctl restart parking-camera.service
    echo "✅ Nueva lógica desactivada. Usando lógica legacy."
    exit 0
fi

# Opción 2: Restaurar backup completo
echo "Opción 2: Restaurar backup completo"
read -p "¿Restaurar backup completo? (y/N): " response
if [[ "\$response" =~ ^[Yy]$ ]]; then
    cp "$BACKUP_DIR/camera_server.py.backup.$TIMESTAMP" src/camera_server.py
    systemctl restart parking-camera.service
    echo "✅ Backup restaurado completamente."
    exit 0
fi

echo "❌ Rollback cancelado."
EOF

chmod +x /opt/parking_altea/scripts/rollback_v4_0_0.sh
log_success "Script de rollback creado: /opt/parking_altea/scripts/rollback_v4_0_0.sh"
log_to_file "Script de rollback configurado"

# RESUMEN FINAL
echo
echo "✅ DESPLIEGUE COMPLETADO EXITOSAMENTE"
echo "===================================="
echo
log_success "Nueva lógica de cálculo de deltas v4.0.0 desplegada"
echo
echo "📁 Archivos importantes:"
echo "   - Backup: $BACKUP_DIR/camera_server.py.backup.$TIMESTAMP"
echo "   - Log de despliegue: $DEPLOYMENT_LOG"
echo "   - Monitor: /opt/parking_altea/scripts/monitor_v4_0_0.sh"
echo "   - Rollback: /opt/parking_altea/scripts/rollback_v4_0_0.sh"
echo
echo "📊 Comandos de monitorización:"
echo "   sudo /opt/parking_altea/scripts/monitor_v4_0_0.sh"
echo "   sudo journalctl -u parking-camera.service -f"
echo
echo "🔄 En caso de problemas:"
echo "   sudo /opt/parking_altea/scripts/rollback_v4_0_0.sh"
echo
echo "⏰ Próximos pasos:"
echo "   1. Monitorizar durante las próximas 2 horas"
echo "   2. Ejecutar tests funcionales detallados"
echo "   3. Verificar métricas durante 24 horas"
echo "   4. Documentar resultados y comportamiento"

log_to_file "Despliegue completado exitosamente"

echo
log_success "🎉 ¡Despliegue v4.0.0 completado con éxito!"
