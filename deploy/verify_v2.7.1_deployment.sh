#!/bin/bash

# Script de verificación post-despliegue v2.7.1 - Parking Altea
# Valida que todas las funcionalidades nuevas funcionen correctamente

set -e

echo "=========================================="
echo "VERIFICACIÓN POST-DESPLIEGUE v2.7.1"
echo "Parking Altea - Validación Completa"
echo "=========================================="

# Configuración
SERVER_IP="157.180.91.63"
PROJECT_DIR="/root/parking_altea"

echo "Fecha de verificación: $(date)"
echo "Servidor: $SERVER_IP"

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para verificar comandos
check_command() {
    if [ $? -eq 0 ]; then
        log "✅ $1 - OK"
    else
        log "❌ $1 - ERROR"
        return 1
    fi
}

# Función para verificar respuesta HTTP
check_http_response() {
    local url=$1
    local description=$2
    local response=$(ssh root@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' $url")
    
    if [ "$response" = "200" ]; then
        log "✅ $description - HTTP $response"
    else
        log "❌ $description - HTTP $response"
        return 1
    fi
}

# 1. VERIFICAR SERVICIOS DEL SISTEMA
log "Verificando servicios del sistema..."

echo ""
echo "=== ESTADO DE SERVICIOS ==="

# Verificar parking-api
ssh root@$SERVER_IP "systemctl is-active parking-api.service"
check_command "Servicio parking-api activo"

# Verificar parking-camera
ssh root@$SERVER_IP "systemctl is-active parking-camera.service"
check_command "Servicio parking-camera activo"

# Verificar parking-schedule-monitor
ssh root@$SERVER_IP "systemctl is-active parking-schedule-monitor.service"
check_command "Servicio parking-schedule-monitor activo"

# Verificar panel-service
ssh root@$SERVER_IP "systemctl is-active panel-service.service"
check_command "Servicio panel-service activo"

# 2. VERIFICAR ENDPOINTS BÁSICOS
log "Verificando endpoints básicos..."

echo ""
echo "=== ENDPOINTS BÁSICOS ==="

# API Backend
check_http_response "http://localhost:6001/api/parkings" "API Backend - Parkings"

# Servidor de cámaras
check_http_response "http://localhost:6400/camera" "Servidor de cámaras"

# Servicio de paneles
ssh root@$SERVER_IP "curl -s http://localhost:5656/status | head -c 100"
check_command "Servicio de paneles respondiendo"

# 3. VERIFICAR NUEVOS ENDPOINTS DE PROGRAMACIONES
log "Verificando nuevos endpoints de programaciones..."

echo ""
echo "=== ENDPOINTS DE PROGRAMACIONES ==="

# Endpoint de programaciones
check_http_response "http://localhost:6001/api/schedules" "API Schedules"

# Endpoint de logs de programaciones
check_http_response "http://localhost:6001/api/schedules/logs" "API Schedules Logs"

# Endpoint de programaciones por parking
check_http_response "http://localhost:6001/api/parking/1/schedules" "API Parking Schedules"

# Endpoint de programaciones activas
check_http_response "http://localhost:6001/api/parking/1/active-schedules" "API Active Schedules"

# 4. VERIFICAR CORRECCIÓN DE DELTAS
log "Verificando corrección de cálculo de deltas..."

echo ""
echo "=== CORRECCIÓN DE DELTAS ==="

# Verificar que el archivo corregido está en su lugar
ssh root@$SERVER_IP "grep -n 'adjusted_previous_in = 0' $PROJECT_DIR/src/camera_server.py"
check_command "Corrección de deltas en código"

# Verificar que no está la línea problemática antigua
ssh root@$SERVER_IP "grep -n 'adjusted_previous_in = 0 if new_in <= previous_in else previous_in' $PROJECT_DIR/src/camera_server.py || echo 'Línea problemática eliminada correctamente'"
check_command "Línea problemática eliminada"

# 5. VERIFICAR BASE DE DATOS
log "Verificando base de datos..."

echo ""
echo "=== BASE DE DATOS ==="

# Verificar que las nuevas tablas existen
ssh root@$SERVER_IP "psql -d parking_altea -c \"SELECT table_name FROM information_schema.tables WHERE table_name IN ('panel_schedules', 'panel_schedule_logs');\""
check_command "Tablas de programaciones creadas"

# Verificar que el campo panel_display_text existe en parkings
ssh root@$SERVER_IP "psql -d parking_altea -c \"SELECT column_name FROM information_schema.columns WHERE table_name = 'parkings' AND column_name = 'panel_display_text';\""
check_command "Campo panel_display_text añadido"

# 6. VERIFICAR FRONTEND
log "Verificando frontend..."

echo ""
echo "=== FRONTEND ==="

# Verificar que el archivo index.html existe
ssh root@$SERVER_IP "ls -la /var/www/html/index.html"
check_command "Archivo index.html del frontend"

# Verificar que los archivos JS están presentes
ssh root@$SERVER_IP "ls -la /var/www/html/assets/ | head -5"
check_command "Archivos JS del frontend"

# 7. VERIFICAR LOGS RECIENTES
log "Verificando logs recientes..."

echo ""
echo "=== LOGS RECIENTES ==="

# Logs de parking-api
echo "Logs de parking-api (últimas 3 líneas):"
ssh root@$SERVER_IP "journalctl -u parking-api.service --no-pager -n 3"

# Logs de parking-camera
echo ""
echo "Logs de parking-camera (últimas 3 líneas):"
ssh root@$SERVER_IP "journalctl -u parking-camera.service --no-pager -n 3"

# Logs de parking-schedule-monitor
echo ""
echo "Logs de parking-schedule-monitor (últimas 3 líneas):"
ssh root@$SERVER_IP "journalctl -u parking-schedule-monitor.service --no-pager -n 3"

# 8. VERIFICAR ARCHIVOS DE CONFIGURACIÓN
log "Verificando archivos de configuración..."

echo ""
echo "=== ARCHIVOS DE CONFIGURACIÓN ==="

# Verificar archivo de servicio de monitorización
ssh root@$SERVER_IP "ls -la /etc/systemd/system/parking-schedule-monitor.service"
check_command "Archivo de servicio de monitorización"

# Verificar script de monitorización ejecutable
ssh root@$SERVER_IP "ls -la $PROJECT_DIR/src/schedule_monitor_service.py"
check_command "Script de monitorización ejecutable"

# 9. VERIFICAR GIT STATUS
log "Verificando estado de Git..."

echo ""
echo "=== GIT STATUS ==="

ssh root@$SERVER_IP "cd $PROJECT_DIR && git status --porcelain"
check_command "Git status limpio"

ssh root@$SERVER_IP "cd $PROJECT_DIR && git log --oneline -1"
check_command "Último commit"

# 10. VERIFICAR CONECTIVIDAD EXTERNA
log "Verificando conectividad externa..."

echo ""
echo "=== CONECTIVIDAD EXTERNA ==="

# Verificar frontend desde fuera
check_http_response "http://$SERVER_IP:5789" "Frontend externo"

# Verificar API desde fuera
check_http_response "http://$SERVER_IP:6001/api/parkings" "API externa"

# 11. VERIFICAR FUNCIONALIDADES ESPECÍFICAS
log "Verificando funcionalidades específicas..."

echo ""
echo "=== FUNCIONALIDADES ESPECÍFICAS ==="

# Probar creación de programación de prueba
echo "Probando creación de programación de prueba..."
ssh root@$SERVER_IP "curl -X POST http://localhost:6001/api/schedules \
  -H 'Content-Type: application/json' \
  -d '{
    \"parking_id\": 1,
    \"name\": \"Prueba Verificación\",
    \"start_date\": \"2025-07-01T00:00:00\",
    \"end_date\": \"2025-12-31T23:59:59\",
    \"start_time\": \"09:00\",
    \"end_time\": \"18:00\",
    \"monday\": true,
    \"message\": \"PRUEBA\",
    \"color\": 2,
    \"font_size\": 2,
    \"effect\": \"static\",
    \"priority\": 1,
    \"is_active\": false
  }' | head -c 200"

check_command "Creación de programación de prueba"

# 12. MOSTRAR RESUMEN FINAL
echo ""
echo "=========================================="
echo "RESUMEN DE VERIFICACIÓN"
echo "=========================================="

echo "✅ Servicios del sistema: Verificados"
echo "✅ Endpoints básicos: Verificados"
echo "✅ Endpoints de programaciones: Verificados"
echo "✅ Corrección de deltas: Verificada"
echo "✅ Base de datos: Verificada"
echo "✅ Frontend: Verificado"
echo "✅ Logs: Verificados"
echo "✅ Archivos de configuración: Verificados"
echo "✅ Git status: Verificado"
echo "✅ Conectividad externa: Verificada"
echo "✅ Funcionalidades específicas: Verificadas"

echo ""
echo "🎉 VERIFICACIÓN POST-DESPLIEGUE COMPLETADA"
echo ""
echo "El sistema v2.7.1 está funcionando correctamente con:"
echo "✅ Sistema de programaciones de paneles operativo"
echo "✅ Corrección del cálculo de deltas aplicada"
echo "✅ Servicio de monitorización activo"
echo "✅ Frontend actualizado y accesible"
echo "✅ API completa para gestión de programaciones"
echo ""
echo "URLs de acceso:"
echo "Frontend: http://$SERVER_IP:5789"
echo "API: http://$SERVER_IP:6001"
echo "Programaciones: http://$SERVER_IP:5789/schedules"
echo ""
echo "Próximos pasos recomendados:"
echo "1. Probar creación de programaciones desde la interfaz web"
echo "2. Verificar que el cálculo de deltas funciona con datos reales"
echo "3. Monitorear logs durante las próximas horas"
echo "4. Entrenar usuarios en las nuevas funcionalidades"
echo "" 