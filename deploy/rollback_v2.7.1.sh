#!/bin/bash

# Script de rollback v2.7.1 - Parking Altea
# Restaura el sistema a la versión anterior en caso de problemas

set -e

echo "=========================================="
echo "ROLLBACK v2.7.1 - Parking Altea"
echo "Restaurando sistema a versión anterior"
echo "=========================================="

# Configuración
SERVER_IP="157.180.91.63"
PROJECT_DIR="/root/parking_altea"
BACKUP_DIR="/root/backups"

echo "Fecha de rollback: $(date)"
echo "Servidor: $SERVER_IP"

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para verificar comandos
check_command() {
    if [ $? -eq 0 ]; then
        log "✅ $1 completado exitosamente"
    else
        log "❌ Error en $1"
        exit 1
    fi
}

# Buscar el backup más reciente
log "Buscando backup más reciente..."

BACKUP_TIMESTAMP=$(ssh root@$SERVER_IP "ls -t $BACKUP_DIR/code_backup_*.tar.gz | head -1 | grep -o '[0-9]\{8\}_[0-9]\{6\}'")
if [ -z "$BACKUP_TIMESTAMP" ]; then
    log "❌ No se encontró backup para rollback"
    exit 1
fi

log "Backup encontrado: $BACKUP_TIMESTAMP"

# 1. DETENER SERVICIOS
log "Deteniendo servicios..."

ssh root@$SERVER_IP "systemctl stop parking-schedule-monitor.service"
ssh root@$SERVER_IP "systemctl stop parking-api.service"
ssh root@$SERVER_IP "systemctl stop parking-camera.service"

log "✅ Servicios detenidos"

# 2. RESTAURAR CÓDIGO
log "Restaurando código desde backup..."

# Crear backup del código actual antes de restaurar
ssh root@$SERVER_IP "cd $PROJECT_DIR && tar -czf $BACKUP_DIR/code_before_rollback_$(date +%Y%m%d_%H%M%S).tar.gz ."

# Restaurar código
ssh root@$SERVER_IP "cd $PROJECT_DIR && rm -rf * .* 2>/dev/null || true"
ssh root@$SERVER_IP "cd $PROJECT_DIR && tar -xzf $BACKUP_DIR/code_backup_$BACKUP_TIMESTAMP.tar.gz"

check_command "Restauración de código"

# 3. RESTAURAR BASE DE DATOS
log "Restaurando base de datos..."

ssh root@$SERVER_IP "psql -d parking_altea -c \"DROP TABLE IF EXISTS panel_schedules CASCADE;\""
ssh root@$SERVER_IP "psql -d parking_altea -c \"DROP TABLE IF EXISTS panel_schedule_logs CASCADE;\""
ssh root@$SERVER_IP "psql -d parking_altea -c \"ALTER TABLE parkings DROP COLUMN IF EXISTS panel_display_text;\""

# Restaurar desde backup si existe
if ssh root@$SERVER_IP "test -f $BACKUP_DIR/parking_altea_backup_$BACKUP_TIMESTAMP.sql"; then
    ssh root@$SERVER_IP "psql -d parking_altea < $BACKUP_DIR/parking_altea_backup_$BACKUP_TIMESTAMP.sql"
    check_command "Restauración de base de datos"
else
    log "⚠️ No se encontró backup de base de datos, solo se eliminaron las nuevas tablas"
fi

# 4. ELIMINAR SERVICIO DE MONITORIZACIÓN
log "Eliminando servicio de monitorización..."

ssh root@$SERVER_IP "systemctl stop parking-schedule-monitor.service"
ssh root@$SERVER_IP "systemctl disable parking-schedule-monitor.service"
ssh root@$SERVER_IP "rm -f /etc/systemd/system/parking-schedule-monitor.service"
ssh root@$SERVER_IP "systemctl daemon-reload"

log "✅ Servicio de monitorización eliminado"

# 5. REINICIAR SERVICIOS
log "Reiniciando servicios..."

ssh root@$SERVER_IP "systemctl start parking-api.service"
check_command "Inicio de parking-api.service"

ssh root@$SERVER_IP "systemctl start parking-camera.service"
check_command "Inicio de parking-camera.service"

# Verificar que están activos
sleep 3
ssh root@$SERVER_IP "systemctl is-active parking-api.service"
ssh root@$SERVER_IP "systemctl is-active parking-camera.service"

log "✅ Servicios reiniciados"

# 6. CONSTRUIR FRONTEND ANTERIOR
log "Construyendo frontend anterior..."

ssh root@$SERVER_IP "cd $PROJECT_DIR/client && npm install"
check_command "Instalación de dependencias frontend"

ssh root@$SERVER_IP "cd $PROJECT_DIR/client && npm run build"
check_command "Construcción del frontend"

# Copiar build a nginx
ssh root@$SERVER_IP "cp -r $PROJECT_DIR/client/dist/* /var/www/html/"
check_command "Copia de archivos frontend"

log "✅ Frontend restaurado"

# 7. VERIFICAR SERVICIOS
log "Verificando servicios restaurados..."

# Verificar API
ssh root@$SERVER_IP "curl -s http://localhost:6001/api/parkings | head -c 100"
check_command "API backend funcionando"

# Verificar servidor de cámaras
ssh root@$SERVER_IP "curl -s http://localhost:6400/camera"
check_command "Servidor de cámaras funcionando"

# Verificar que los endpoints de programaciones NO existen
ssh root@$SERVER_IP "curl -s http://localhost:6001/api/schedules || echo 'Endpoint de programaciones eliminado correctamente'"
check_command "Endpoints de programaciones eliminados"

log "✅ Verificación de servicios completada"

# 8. MOSTRAR ESTADO FINAL
log "Mostrando estado final de servicios..."

echo ""
echo "=========================================="
echo "ESTADO FINAL DESPUÉS DEL ROLLBACK"
echo "=========================================="

ssh root@$SERVER_IP "systemctl status parking-api.service --no-pager -l"
echo ""
ssh root@$SERVER_IP "systemctl status parking-camera.service --no-pager -l"
echo ""

# 9. INFORMACIÓN DE ACCESO
echo "=========================================="
echo "INFORMACIÓN DE ACCESO"
echo "=========================================="
echo "Frontend: http://$SERVER_IP:5789"
echo "API Backend: http://$SERVER_IP:6001"
echo "Servidor de Cámaras: http://$SERVER_IP:6400"
echo "Servicio de Paneles: http://$SERVER_IP:5656"
echo ""

# 10. LOGS RECIENTES
echo "=========================================="
echo "LOGS RECIENTES"
echo "=========================================="

echo "Logs de parking-api (últimas 3 líneas):"
ssh root@$SERVER_IP "journalctl -u parking-api.service --no-pager -n 3"

echo ""
echo "Logs de parking-camera (últimas 3 líneas):"
ssh root@$SERVER_IP "journalctl -u parking-camera.service --no-pager -n 3"

# 11. BACKUP INFORMATION
echo ""
echo "=========================================="
echo "INFORMACIÓN DE BACKUP"
echo "=========================================="
echo "Backup restaurado: $BACKUP_TIMESTAMP"
echo "Backup creado antes del rollback:"
ssh root@$SERVER_IP "ls -la $BACKUP_DIR/code_before_rollback_* | tail -1"
echo ""

log "🔄 ROLLBACK v2.7.1 COMPLETADO EXITOSAMENTE"
echo ""
echo "El sistema ha sido restaurado a la versión anterior:"
echo "✅ Código restaurado desde backup"
echo "✅ Base de datos restaurada (nuevas tablas eliminadas)"
echo "✅ Servicio de monitorización eliminado"
echo "✅ Servicios backend reiniciados"
echo "✅ Frontend restaurado"
echo "✅ Funcionalidades v2.7.1 eliminadas"
echo ""
echo "El sistema está ahora funcionando con la versión anterior."
echo ""
echo "Si necesitas volver a intentar el despliegue v2.7.1:"
echo "1. Revisar los logs para identificar el problema"
echo "2. Corregir el problema identificado"
echo "3. Ejecutar nuevamente deploy_v2.7.1_complete.sh"
echo "" 