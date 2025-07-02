#!/bin/bash

# Script de despliegue completo v2.7.1 - Parking Altea
# Incluye: Sistema de programaciones + Corrección de cálculo de deltas + Servicio de monitorización

set -e

echo "=========================================="
echo "DESPLIEGUE COMPLETO v2.7.1"
echo "Parking Altea - Sistema de Programaciones"
echo "=========================================="

# Configuración
SERVER_IP="157.180.91.63"
PROJECT_DIR="/root/parking_altea"
BACKUP_DIR="/root/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Fecha de despliegue: $(date)"
echo "Servidor: $SERVER_IP"
echo "Directorio del proyecto: $PROJECT_DIR"

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

# 1. CREAR BACKUP COMPLETO
log "Iniciando backup completo del sistema..."

# Crear directorio de backup si no existe
ssh root@$SERVER_IP "mkdir -p $BACKUP_DIR"

# Backup de la base de datos
log "Creando backup de la base de datos..."
ssh root@$SERVER_IP "pg_dump parking_altea > $BACKUP_DIR/parking_altea_backup_$TIMESTAMP.sql"
check_command "Backup de base de datos"

# Backup del código actual
log "Creando backup del código actual..."
ssh root@$SERVER_IP "cd $PROJECT_DIR && tar -czf $BACKUP_DIR/code_backup_$TIMESTAMP.tar.gz ."
check_command "Backup del código"

# Backup de logs
log "Creando backup de logs..."
ssh root@$SERVER_IP "tar -czf $BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz /var/log/parking* 2>/dev/null || true"
check_command "Backup de logs"

log "✅ Backup completo creado en $BACKUP_DIR"

# 2. ACTUALIZAR CÓDIGO DESDE GIT
log "Actualizando código desde Git..."

ssh root@$SERVER_IP "cd $PROJECT_DIR && git fetch origin"
check_command "Git fetch"

ssh root@$SERVER_IP "cd $PROJECT_DIR && git checkout v2.7_no_login_Panel_prog"
check_command "Git checkout"

ssh root@$SERVER_IP "cd $PROJECT_DIR && git pull origin v2.7_no_login_Panel_prog"
check_command "Git pull"

log "✅ Código actualizado a v2.7.1"

# 3. EJECUTAR MIGRACIÓN DE BASE DE DATOS
log "Ejecutando migración de base de datos..."

ssh root@$SERVER_IP "cd $PROJECT_DIR/src && python3 migrate_panel_schedules.py"
check_command "Migración de base de datos"

log "✅ Migración completada"

# 4. REINICIAR SERVICIOS BACKEND
log "Reiniciando servicios backend..."

# Detener servicios
ssh root@$SERVER_IP "systemctl stop parking-api.service"
ssh root@$SERVER_IP "systemctl stop parking-camera.service"

# Verificar que se detuvieron
sleep 2
ssh root@$SERVER_IP "systemctl is-active parking-api.service || echo 'API service stopped'"
ssh root@$SERVER_IP "systemctl is-active parking-camera.service || echo 'Camera service stopped'"

# Iniciar servicios
ssh root@$SERVER_IP "systemctl start parking-api.service"
check_command "Inicio de parking-api.service"

ssh root@$SERVER_IP "systemctl start parking-camera.service"
check_command "Inicio de parking-camera.service"

# Verificar que están activos
sleep 3
ssh root@$SERVER_IP "systemctl is-active parking-api.service"
ssh root@$SERVER_IP "systemctl is-active parking-camera.service"

log "✅ Servicios backend reiniciados"

# 5. CONFIGURAR SERVICIO DE MONITORIZACIÓN
log "Configurando servicio de monitorización..."

# Copiar archivo de servicio
ssh root@$SERVER_IP "cp $PROJECT_DIR/deploy/parking-schedule-monitor.service /etc/systemd/system/"

# Recargar systemd
ssh root@$SERVER_IP "systemctl daemon-reload"

# Habilitar servicio
ssh root@$SERVER_IP "systemctl enable parking-schedule-monitor.service"

# Hacer ejecutable el script
ssh root@$SERVER_IP "chmod +x $PROJECT_DIR/src/schedule_monitor_service.py"

log "✅ Servicio de monitorización configurado"

# 6. CONSTRUIR Y DESPLEGAR FRONTEND
log "Construyendo frontend..."

ssh root@$SERVER_IP "cd $PROJECT_DIR/client && npm install"
check_command "Instalación de dependencias frontend"

ssh root@$SERVER_IP "cd $PROJECT_DIR/client && npm run build"
check_command "Construcción del frontend"

# Copiar build a nginx
ssh root@$SERVER_IP "cp -r $PROJECT_DIR/client/dist/* /var/www/html/"
check_command "Copia de archivos frontend"

log "✅ Frontend construido y desplegado"

# 7. VERIFICAR SERVICIOS
log "Verificando servicios..."

# Verificar API
log "Verificando API backend..."
ssh root@$SERVER_IP "curl -s http://localhost:6001/api/parkings | head -c 100"

# Verificar servidor de cámaras
log "Verificando servidor de cámaras..."
ssh root@$SERVER_IP "curl -s http://localhost:6400/camera"

# Verificar servicio de paneles
log "Verificando servicio de paneles..."
ssh root@$SERVER_IP "curl -s http://localhost:5656/status || echo 'Panel service not responding'"

log "✅ Verificación de servicios completada"

# 8. PROBAR NUEVOS ENDPOINTS
log "Probando nuevos endpoints de programaciones..."

# Probar endpoint de programaciones
ssh root@$SERVER_IP "curl -s http://localhost:6001/api/schedules | head -c 100"

# Probar endpoint de logs
ssh root@$SERVER_IP "curl -s http://localhost:6001/api/schedules/logs | head -c 100"

log "✅ Endpoints de programaciones verificados"

# 9. INICIAR SERVICIO DE MONITORIZACIÓN
log "Iniciando servicio de monitorización..."

ssh root@$SERVER_IP "systemctl start parking-schedule-monitor.service"
check_command "Inicio de servicio de monitorización"

# Verificar que está activo
sleep 2
ssh root@$SERVER_IP "systemctl is-active parking-schedule-monitor.service"

log "✅ Servicio de monitorización iniciado"

# 10. VERIFICAR LOGS
log "Verificando logs de servicios..."

# Mostrar logs recientes
ssh root@$SERVER_IP "journalctl -u parking-api.service --no-pager -n 5"
ssh root@$SERVER_IP "journalctl -u parking-camera.service --no-pager -n 5"
ssh root@$SERVER_IP "journalctl -u parking-schedule-monitor.service --no-pager -n 5"

log "✅ Verificación de logs completada"

# 11. VERIFICAR CORRECCIÓN DE DELTAS
log "Verificando corrección de cálculo de deltas..."

# Verificar que el archivo corregido está en su lugar
ssh root@$SERVER_IP "grep -n 'adjusted_previous_in = 0' $PROJECT_DIR/src/camera_server.py"

log "✅ Corrección de deltas verificada"

# 12. MOSTRAR ESTADO FINAL
log "Mostrando estado final de servicios..."

echo ""
echo "=========================================="
echo "ESTADO FINAL DE SERVICIOS"
echo "=========================================="

ssh root@$SERVER_IP "systemctl status parking-api.service --no-pager -l"
echo ""
ssh root@$SERVER_IP "systemctl status parking-camera.service --no-pager -l"
echo ""
ssh root@$SERVER_IP "systemctl status parking-schedule-monitor.service --no-pager -l"
echo ""

# 13. INFORMACIÓN DE ACCESO
echo "=========================================="
echo "INFORMACIÓN DE ACCESO"
echo "=========================================="
echo "Frontend: http://$SERVER_IP:5789"
echo "API Backend: http://$SERVER_IP:6001"
echo "Servidor de Cámaras: http://$SERVER_IP:6400"
echo "Servicio de Paneles: http://$SERVER_IP:5656"
echo ""
echo "Nuevas funcionalidades disponibles:"
echo "- Gestión de programaciones: http://$SERVER_IP:5789/schedules"
echo "- API de programaciones: http://$SERVER_IP:6001/api/schedules"
echo ""

# 14. COMANDOS ÚTILES
echo "=========================================="
echo "COMANDOS ÚTILES PARA MONITOREO"
echo "=========================================="
echo "Ver logs en tiempo real:"
echo "  journalctl -u parking-api.service -f"
echo "  journalctl -u parking-camera.service -f"
echo "  journalctl -u parking-schedule-monitor.service -f"
echo ""
echo "Verificar estado de servicios:"
echo "  systemctl status parking-api.service"
echo "  systemctl status parking-camera.service"
echo "  systemctl status parking-schedule-monitor.service"
echo ""
echo "Probar endpoints:"
echo "  curl http://localhost:6001/api/schedules"
echo "  curl http://localhost:6001/api/parkings"
echo ""

# 15. BACKUP INFORMATION
echo "=========================================="
echo "INFORMACIÓN DE BACKUP"
echo "=========================================="
echo "Backup creado en: $BACKUP_DIR"
echo "Archivos de backup:"
ssh root@$SERVER_IP "ls -la $BACKUP_DIR/*$TIMESTAMP*"
echo ""

log "🎉 DESPLIEGUE COMPLETO v2.7.1 FINALIZADO EXITOSAMENTE"
echo ""
echo "El sistema está ahora actualizado con:"
echo "✅ Sistema de programaciones de paneles"
echo "✅ Corrección del cálculo de deltas"
echo "✅ Servicio de monitorización automática"
echo "✅ Frontend actualizado con nuevas funcionalidades"
echo "✅ API completa para gestión de programaciones"
echo ""
echo "Próximos pasos:"
echo "1. Probar creación de programaciones desde la interfaz web"
echo "2. Verificar que el cálculo de deltas funciona correctamente"
echo "3. Monitorear logs para detectar posibles problemas"
echo "4. Entrenar usuarios en las nuevas funcionalidades"
echo "" 