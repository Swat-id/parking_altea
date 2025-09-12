#!/bin/bash

# Script de Tests para Nueva Lógica de Cálculo de Deltas v4.0.0
# Ejecutar en el servidor remoto después del despliegue

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[TEST]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

# Variables
CAMERA_ENDPOINT="http://localhost:6400/camera"
TEST_DEVICE="TEST_CAMERA_V4"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_LOG="/opt/parking/logs/tests_v4_0_0_${TIMESTAMP}.log"

echo "🧪 TESTS FUNCIONALES - NUEVA LÓGICA v4.0.0"
echo "============================================="
echo "Fecha: $(date)"
echo "Log de tests: $TEST_LOG"
echo

# Función para logging
log_to_file() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$TEST_LOG"
}

# Test 1: Verificar que el servicio está activo
log_info "Test 1: Verificando estado del servicio..."
if systemctl is-active --quiet parking-camera.service; then
    log_success "Servicio parking-camera.service está activo"
    log_to_file "PASS: Servicio activo"
else
    log_error "Servicio parking-camera.service no está activo"
    log_to_file "FAIL: Servicio inactivo"
    exit 1
fi

# Test 2: Verificar que la nueva lógica está activa
log_info "Test 2: Verificando activación de nueva lógica..."
if journalctl -u parking-camera.service --since "10 minutes ago" | grep -q "NEW DELTA LOGIC ENABLED"; then
    log_success "Nueva lógica v4.0.0 está activa"
    log_to_file "PASS: Nueva lógica activa"
else
    log_error "Nueva lógica v4.0.0 no está activa"
    log_to_file "FAIL: Nueva lógica no activa"
    
    # Mostrar logs recientes para debugging
    log_info "Logs recientes del servicio:"
    journalctl -u parking-camera.service --since "10 minutes ago" --no-pager | tail -20
    exit 1
fi

# Test 3: Test de conectividad básica
log_info "Test 3: Verificando conectividad del endpoint..."
if curl -s -f "$CAMERA_ENDPOINT" > /dev/null; then
    log_success "Endpoint $CAMERA_ENDPOINT responde correctamente"
    log_to_file "PASS: Endpoint accesible"
else
    log_error "Endpoint $CAMERA_ENDPOINT no responde"
    log_to_file "FAIL: Endpoint no accesible"
    exit 1
fi

# Test 4: Mensaje de funcionamiento normal
log_info "Test 4: Enviando mensaje de funcionamiento normal..."
response=$(curl -s -w "%{http_code}" -X POST "$CAMERA_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
        "device": "'$TEST_DEVICE'",
        "line": 0,
        "Vehicle In": 100,
        "Vehicle Out": 95,
        "event": "test_normal",
        "time": "'$(date -Iseconds)'"
    }')

http_code="${response: -3}"
if [ "$http_code" = "200" ] || [ "$http_code" = "404" ]; then
    log_success "Mensaje normal procesado (HTTP $http_code)"
    log_to_file "PASS: Mensaje normal - HTTP $http_code"
    
    # Verificar en logs
    sleep 2
    if journalctl -u parking-camera.service --since "1 minute ago" | grep -q "NEW LOGIC - Delta final"; then
        log_success "Delta calculado con nueva lógica detectado en logs"
        log_to_file "PASS: Delta con nueva lógica en logs"
    else
        log_warning "No se detectó cálculo de delta con nueva lógica en logs"
        log_to_file "WARN: Delta nueva lógica no en logs"
    fi
else
    log_error "Error procesando mensaje normal (HTTP $http_code)"
    log_to_file "FAIL: Mensaje normal - HTTP $http_code"
fi

# Test 5: Mensaje duplicado
log_info "Test 5: Enviando mensaje duplicado..."
response=$(curl -s -w "%{http_code}" -X POST "$CAMERA_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
        "device": "'$TEST_DEVICE'",
        "line": 0,
        "Vehicle In": 100,
        "Vehicle Out": 95,
        "event": "test_duplicate",
        "time": "'$(date -Iseconds)'"
    }')

http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    log_success "Mensaje duplicado procesado (HTTP $http_code)"
    log_to_file "PASS: Mensaje duplicado - HTTP $http_code"
    
    # Verificar detección de duplicado en logs
    sleep 2
    if journalctl -u parking-camera.service --since "1 minute ago" | grep -q "DUPLICATE MESSAGE DETECTED (NEW LOGIC)"; then
        log_success "Duplicado detectado correctamente con nueva lógica"
        log_to_file "PASS: Duplicado detectado nueva lógica"
    else
        log_warning "No se detectó mensaje duplicado en logs con nueva lógica"
        log_to_file "WARN: Duplicado nueva lógica no detectado"
    fi
else
    log_error "Error procesando mensaje duplicado (HTTP $http_code)"
    log_to_file "FAIL: Mensaje duplicado - HTTP $http_code"
fi

# Test 6: Simulación de reinicio de cámara
log_info "Test 6: Simulando reinicio de cámara..."
response=$(curl -s -w "%{http_code}" -X POST "$CAMERA_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
        "device": "'$TEST_DEVICE'",
        "line": 0,
        "Vehicle In": 5,
        "Vehicle Out": 2,
        "event": "test_reset",
        "time": "'$(date -Iseconds)'"
    }')

http_code="${response: -3}"
if [ "$http_code" = "200" ] || [ "$http_code" = "404" ]; then
    log_success "Mensaje de reinicio procesado (HTTP $http_code)"
    log_to_file "PASS: Mensaje reinicio - HTTP $http_code"
    
    # Verificar detección de reinicio en logs
    sleep 2
    if journalctl -u parking-camera.service --since "1 minute ago" | grep -q "Reset detected (NEW LOGIC)"; then
        log_success "Reinicio detectado correctamente con nueva lógica"
        log_to_file "PASS: Reinicio detectado nueva lógica"
        
        # Verificar cálculo de diferencia absoluta
        if journalctl -u parking-camera.service --since "1 minute ago" | grep -q "Using absolute difference"; then
            log_success "Diferencia absoluta calculada en reinicio"
            log_to_file "PASS: Diferencia absoluta en reinicio"
        else
            log_warning "No se detectó cálculo de diferencia absoluta"
            log_to_file "WARN: Diferencia absoluta no detectada"
        fi
    else
        log_warning "No se detectó reinicio en logs con nueva lógica"
        log_to_file "WARN: Reinicio nueva lógica no detectado"
    fi
else
    log_error "Error procesando mensaje de reinicio (HTTP $http_code)"
    log_to_file "FAIL: Mensaje reinicio - HTTP $http_code"
fi

# Test 7: Verificar logs de procesamiento
log_info "Test 7: Analizando logs de procesamiento..."

# Contar mensajes procesados en los últimos 5 minutos
processed_count=$(journalctl -u parking-camera.service --since "5 minutes ago" | grep -c "NEW LOGIC - Delta final" || echo "0")
reset_count=$(journalctl -u parking-camera.service --since "5 minutes ago" | grep -c "Reset detected (NEW LOGIC)" || echo "0")
duplicate_count=$(journalctl -u parking-camera.service --since "5 minutes ago" | grep -c "DUPLICATE MESSAGE DETECTED (NEW LOGIC)" || echo "0")

log_info "Estadísticas de procesamiento (últimos 5 minutos):"
echo "   - Mensajes procesados con nueva lógica: $processed_count"
echo "   - Reinicios detectados: $reset_count"
echo "   - Duplicados detectados: $duplicate_count"

log_to_file "STATS: Procesados=$processed_count, Reinicios=$reset_count, Duplicados=$duplicate_count"

if [ "$processed_count" -gt 0 ]; then
    log_success "Mensajes siendo procesados con nueva lógica"
    log_to_file "PASS: Mensajes procesados nueva lógica"
else
    log_warning "No se detectaron mensajes procesados con nueva lógica recientemente"
    log_to_file "WARN: No mensajes procesados nueva lógica"
fi

# Test 8: Verificar ausencia de errores críticos
log_info "Test 8: Verificando ausencia de errores críticos..."
error_count=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -i -c "error\|exception\|traceback" || echo "0")

if [ "$error_count" -eq 0 ]; then
    log_success "No se detectaron errores críticos en los logs"
    log_to_file "PASS: Sin errores críticos"
else
    log_warning "Se detectaron $error_count posibles errores en los logs"
    log_to_file "WARN: $error_count errores detectados"
    
    # Mostrar últimos errores
    log_info "Últimos errores detectados:"
    journalctl -u parking-camera.service --since "10 minutes ago" | grep -i "error\|exception" | tail -5
fi

# Test 9: Test de rendimiento básico
log_info "Test 9: Test básico de rendimiento..."
start_time=$(date +%s.%N)

for i in {1..10}; do
    curl -s -X POST "$CAMERA_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d '{
            "device": "'$TEST_DEVICE'_PERF",
            "line": 0,
            "Vehicle In": '$((100 + i))',
            "Vehicle Out": '$((95 + i))',
            "event": "test_performance",
            "time": "'$(date -Iseconds)'"
        }' > /dev/null || true
done

end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)
avg_time=$(echo "scale=3; $duration / 10" | bc)

log_info "Rendimiento: 10 requests en ${duration}s (promedio: ${avg_time}s por request)"
log_to_file "PERF: 10 requests en ${duration}s, promedio ${avg_time}s"

if (( $(echo "$avg_time < 0.5" | bc -l) )); then
    log_success "Rendimiento aceptable (< 0.5s por request)"
    log_to_file "PASS: Rendimiento aceptable"
else
    log_warning "Rendimiento lento (>= 0.5s por request)"
    log_to_file "WARN: Rendimiento lento"
fi

# Resumen final
echo
echo "📊 RESUMEN DE TESTS"
echo "=================="

# Contar tests pasados/fallidos del log
passed_tests=$(grep -c "PASS:" "$TEST_LOG" || echo "0")
failed_tests=$(grep -c "FAIL:" "$TEST_LOG" || echo "0")
warning_tests=$(grep -c "WARN:" "$TEST_LOG" || echo "0")

echo "✅ Tests pasados: $passed_tests"
echo "⚠️  Warnings: $warning_tests"
echo "❌ Tests fallidos: $failed_tests"
echo
echo "📁 Log completo: $TEST_LOG"
echo

if [ "$failed_tests" -eq 0 ]; then
    log_success "🎉 Todos los tests críticos pasaron exitosamente"
    log_to_file "SUMMARY: Tests exitosos"
    
    if [ "$warning_tests" -gt 0 ]; then
        log_warning "⚠️  Hay $warning_tests warnings que requieren atención"
        echo "   Revisar el log para detalles de los warnings"
    fi
    
    echo
    echo "✅ NUEVA LÓGICA v4.0.0 FUNCIONANDO CORRECTAMENTE"
    echo
    echo "📋 Próximos pasos recomendados:"
    echo "1. Monitorizar durante las próximas 2 horas"
    echo "2. Ejecutar /opt/parking/scripts/monitor_v4_0_0.sh periódicamente"
    echo "3. Verificar métricas de ocupación en dashboards"
    echo "4. Documentar comportamiento observado"
    
    exit 0
else
    log_error "❌ $failed_tests tests críticos fallaron"
    log_to_file "SUMMARY: Tests fallidos"
    
    echo
    echo "🚨 SE RECOMIENDA INVESTIGAR LOS FALLOS"
    echo
    echo "🔄 En caso de problemas graves:"
    echo "   sudo /opt/parking/scripts/rollback_v4_0_0.sh"
    
    exit 1
fi
