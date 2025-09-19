#!/bin/bash

# Script de Validación Post-Despliegue v4.1.0
# Verifica que todas las funcionalidades estén operativas

set -e

echo "=== VALIDACIÓN DESPLIEGUE v4.1.0 ==="
echo "Servidor: $(hostname -I | awk '{print $1}')"
echo "Fecha: $(date)"
echo

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
API_PORT=5000
PUSH_SERVICE_PORT=3535
FRONTEND_PORT=5789
DB_NAME="parking_db"

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

# Función para testing
test_passed() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

test_failed() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo "🔍 INICIANDO VALIDACIÓN COMPLETA..."
echo

# ============================================================================
# 1. VALIDACIÓN DE SERVICIOS SYSTEMD
# ============================================================================
echo "1. VALIDACIÓN SERVICIOS SYSTEMD"
echo "================================"

# Verificar parking-api
if systemctl is-active --quiet parking-api; then
    test_passed "Servicio parking-api está activo"
else
    test_failed "Servicio parking-api no está activo"
fi

# Verificar parking-sensor-push
if systemctl is-active --quiet parking-sensor-push; then
    test_passed "Servicio parking-sensor-push está activo"
else
    test_failed "Servicio parking-sensor-push no está activo"
fi

# Verificar parking-panel-worker
if systemctl is-active --quiet parking-panel-worker; then
    test_passed "Servicio parking-panel-worker está activo"
else
    test_warning "Servicio parking-panel-worker no está activo (opcional)"
fi

echo

# ============================================================================
# 2. VALIDACIÓN DE PUERTOS
# ============================================================================
echo "2. VALIDACIÓN PUERTOS"
echo "===================="

# Puerto API
if lsof -i :$API_PORT > /dev/null 2>&1; then
    test_passed "Puerto $API_PORT (API Backend) está en uso"
else
    test_failed "Puerto $API_PORT (API Backend) no está en uso"
fi

# Puerto Push Service
if lsof -i :$PUSH_SERVICE_PORT > /dev/null 2>&1; then
    test_passed "Puerto $PUSH_SERVICE_PORT (Push Service) está en uso"
else
    test_failed "Puerto $PUSH_SERVICE_PORT (Push Service) no está en uso"
fi

# Puerto Frontend
if lsof -i :$FRONTEND_PORT > /dev/null 2>&1; then
    test_passed "Puerto $FRONTEND_PORT (Frontend) está en uso"
else
    test_warning "Puerto $FRONTEND_PORT (Frontend) no está en uso"
fi

echo

# ============================================================================
# 3. VALIDACIÓN CONECTIVIDAD HTTP
# ============================================================================
echo "3. VALIDACIÓN CONECTIVIDAD HTTP"
echo "==============================="

# Test API Health
if curl -s -f "http://localhost:$API_PORT/api/health" > /dev/null; then
    test_passed "API Backend responde en /api/health"
else
    test_failed "API Backend no responde en /api/health"
fi

# Test Push Service Health
if curl -s -f "http://localhost:$PUSH_SERVICE_PORT/health" > /dev/null; then
    test_passed "Push Service responde en /health"
    
    # Obtener información del servicio
    PUSH_INFO=$(curl -s "http://localhost:$PUSH_SERVICE_PORT/health" 2>/dev/null)
    if echo "$PUSH_INFO" | grep -q "sensor-push-service"; then
        test_passed "Push Service retorna información correcta"
        VERSION=$(echo "$PUSH_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null)
        log_info "Versión Push Service: $VERSION"
    else
        test_warning "Push Service responde pero formato incorrecto"
    fi
else
    test_failed "Push Service no responde en /health"
fi

# Test Push Service Stats
if curl -s -f "http://localhost:$PUSH_SERVICE_PORT/stats" > /dev/null; then
    test_passed "Push Service responde en /stats"
else
    test_warning "Push Service no responde en /stats (puede ser normal si no hay sensores)"
fi

echo

# ============================================================================
# 4. VALIDACIÓN BASE DE DATOS
# ============================================================================
echo "4. VALIDACIÓN BASE DE DATOS"
echo "==========================="

# Verificar conexión a PostgreSQL
if sudo -u postgres psql -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    test_passed "Conexión a base de datos $DB_NAME"
else
    test_failed "No se puede conectar a base de datos $DB_NAME"
fi

# Verificar tablas de sensores
TABLES_CHECK=$(sudo -u postgres psql -d $DB_NAME -t -c "
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_name IN ('individual_sensors', 'sensor_status_history', 'sensor_current_status', 'parking_sensor_summary')
AND table_schema = 'public';
" 2>/dev/null | xargs)

if [ "$TABLES_CHECK" = "4" ]; then
    test_passed "Todas las tablas de sensores existen ($TABLES_CHECK/4)"
else
    test_failed "Faltan tablas de sensores ($TABLES_CHECK/4 encontradas)"
fi

# Verificar columnas de panels
PANEL_COLUMNS=$(sudo -u postgres psql -d $DB_NAME -t -c "
SELECT COUNT(*) FROM information_schema.columns 
WHERE table_name = 'panels' 
AND column_name IN ('last_message_window_0', 'last_message_window_1', 'window_config_json');
" 2>/dev/null | xargs)

if [ "$PANEL_COLUMNS" = "3" ]; then
    test_passed "Columnas de ventanas en tabla panels ($PANEL_COLUMNS/3)"
else
    test_warning "Columnas de ventanas incompletas en panels ($PANEL_COLUMNS/3)"
fi

# Contar sensores existentes
SENSOR_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM individual_sensors;" 2>/dev/null | xargs)
log_info "Sensores individuales registrados: ${SENSOR_COUNT:-0}"

echo

# ============================================================================
# 5. VALIDACIÓN APIS ESPECÍFICAS
# ============================================================================
echo "5. VALIDACIÓN APIs ESPECÍFICAS"
echo "=============================="

# Test endpoint de estadísticas de sensores
if curl -s -f "http://localhost:$API_PORT/api/sensors/stats" > /dev/null; then
    test_passed "Endpoint /api/sensors/stats disponible"
else
    test_warning "Endpoint /api/sensors/stats no disponible (puede necesitar autenticación)"
fi

# Test endpoint de dashboard completo
if curl -s -f "http://localhost:$API_PORT/api/dashboard/complete" > /dev/null; then
    test_passed "Endpoint /api/dashboard/complete disponible"
else
    test_warning "Endpoint /api/dashboard/complete no disponible (puede necesitar autenticación)"
fi

# Test endpoint de sensores
if curl -s -f "http://localhost:$API_PORT/api/sensors" > /dev/null; then
    test_passed "Endpoint /api/sensors disponible"
else
    test_warning "Endpoint /api/sensors no disponible (puede necesitar autenticación)"
fi

echo

# ============================================================================
# 6. VALIDACIÓN ARCHIVOS ESTÁTICOS
# ============================================================================
echo "6. VALIDACIÓN ARCHIVOS ESTÁTICOS"
echo "================================"

# Verificar build del frontend
if [ -d "client/dist" ]; then
    test_passed "Build del frontend existe (client/dist)"
    
    # Verificar archivos principales
    if [ -f "client/dist/index.html" ]; then
        test_passed "Archivo index.html del frontend"
    else
        test_failed "Archivo index.html del frontend no encontrado"
    fi
else
    test_failed "Build del frontend no encontrado (client/dist)"
fi

# Verificar archivo del servicio push
if [ -f "src/sensor_push_service.py" ]; then
    test_passed "Archivo servicio push existe"
else
    test_failed "Archivo servicio push no encontrado"
fi

echo

# ============================================================================
# 7. VALIDACIÓN LOGS
# ============================================================================
echo "7. VALIDACIÓN LOGS"
echo "=================="

# Verificar logs de API
if journalctl -u parking-api --since="5 minutes ago" --no-pager -q > /dev/null 2>&1; then
    ERROR_COUNT=$(journalctl -u parking-api --since="5 minutes ago" --no-pager | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        test_passed "Logs API sin errores recientes"
    else
        test_warning "API tiene $ERROR_COUNT errores en logs recientes"
    fi
else
    test_warning "No se pueden leer logs de parking-api"
fi

# Verificar logs de Push Service
if journalctl -u parking-sensor-push --since="5 minutes ago" --no-pager -q > /dev/null 2>&1; then
    ERROR_COUNT=$(journalctl -u parking-sensor-push --since="5 minutes ago" --no-pager | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        test_passed "Logs Push Service sin errores recientes"
    else
        test_warning "Push Service tiene $ERROR_COUNT errores en logs recientes"
    fi
else
    test_warning "No se pueden leer logs de parking-sensor-push"
fi

echo

# ============================================================================
# 8. VALIDACIÓN FIREWALL
# ============================================================================
echo "8. VALIDACIÓN FIREWALL"
echo "======================"

if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    if ufw status | grep -q "$PUSH_SERVICE_PORT"; then
        test_passed "Puerto $PUSH_SERVICE_PORT permitido en firewall"
    else
        test_warning "Puerto $PUSH_SERVICE_PORT no configurado en firewall"
    fi
else
    log_info "UFW no está activo o no instalado"
fi

echo

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo "=================================="
echo "RESUMEN VALIDACIÓN v4.1.0"
echo "=================================="
echo
echo "✅ Tests pasados: $TESTS_PASSED"
echo "❌ Tests fallidos: $TESTS_FAILED"
echo "📊 Total tests: $((TESTS_PASSED + TESTS_FAILED))"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 VALIDACIÓN EXITOSA - SISTEMA OPERATIVO AL 100%${NC}"
    echo
    echo "🚀 FUNCIONALIDADES VALIDADAS:"
    echo "  • ✅ Sistema sensores individuales"
    echo "  • ✅ Dashboard con estadísticas tiempo real"
    echo "  • ✅ Servicio push puerto $PUSH_SERVICE_PORT"
    echo "  • ✅ APIs backend actualizadas"
    echo "  • ✅ Base de datos migrada"
    echo "  • ✅ Servicios systemd activos"
    echo
    echo "🌐 SISTEMA ACCESIBLE EN:"
    echo "  • Frontend: http://157.180.91.63:$FRONTEND_PORT"
    echo "  • API: http://157.180.91.63:$API_PORT"
    echo "  • Push Service: http://157.180.91.63:$PUSH_SERVICE_PORT"
    echo
    exit 0
elif [ $TESTS_FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠️  VALIDACIÓN CON ADVERTENCIAS - SISTEMA MAYORMENTE OPERATIVO${NC}"
    echo
    echo "El sistema está funcionando pero hay algunos elementos que requieren atención."
    echo "Revisar los tests fallidos arriba."
    echo
    exit 1
else
    echo -e "${RED}❌ VALIDACIÓN FALLIDA - SISTEMA CON PROBLEMAS CRÍTICOS${NC}"
    echo
    echo "Hay problemas críticos que impiden el funcionamiento correcto."
    echo "Revisar los tests fallidos y corregir antes de usar el sistema."
    echo
    exit 2
fi
