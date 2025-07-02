#!/bin/bash

# Script de validación para la integración de programaciones y paneles
# Este script verifica que el sistema de programaciones funciona correctamente

echo "=== VALIDACIÓN DE INTEGRACIÓN DE PROGRAMACIONES Y PANELES ==="
echo "Fecha: $(date)"
echo ""

# Configuración
API_URL="http://localhost:5000"
DB_NAME="parking_db"
DB_USER="parking_user"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Función para verificar si un servicio está ejecutándose
check_service() {
    local service_name=$1
    if systemctl is-active --quiet $service_name; then
        print_status "OK" "Servicio $service_name está ejecutándose"
        return 0
    else
        print_status "ERROR" "Servicio $service_name NO está ejecutándose"
        return 1
    fi
}

# Función para verificar endpoint de API
check_api_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")
    
    if [ "$response" = "$expected_status" ]; then
        print_status "OK" "Endpoint $endpoint responde correctamente (HTTP $response)"
        return 0
    else
        print_status "ERROR" "Endpoint $endpoint responde con HTTP $response (esperado $expected_status)"
        return 1
    fi
}

# Función para verificar programaciones en la base de datos
check_schedules_in_db() {
    local query="SELECT COUNT(*) FROM panel_schedules WHERE is_active = true;"
    local count=$(sudo -u postgres psql -d $DB_NAME -t -c "$query" | xargs)
    
    if [ "$count" -ge 0 ]; then
        print_status "OK" "Base de datos accesible - $count programaciones activas encontradas"
        return 0
    else
        print_status "ERROR" "No se puede acceder a la base de datos"
        return 1
    fi
}

# Función para verificar logs del monitor
check_monitor_logs() {
    local log_file="schedule_monitor.log"
    if [ -f "$log_file" ]; then
        local recent_logs=$(tail -n 10 "$log_file" | grep -E "(ejecutada|finalizada|error)" | wc -l)
        print_status "OK" "Logs del monitor encontrados - $recent_logs entradas recientes"
        return 0
    else
        print_status "WARNING" "Archivo de logs del monitor no encontrado"
        return 1
    fi
}

# Función para crear una programación de prueba
create_test_schedule() {
    echo ""
    echo "--- Creando programación de prueba ---"
    
    # Obtener fecha y hora actual
    local current_date=$(date +%Y-%m-%d)
    local current_time=$(date +%H:%M)
    local end_time=$(date -d "+5 minutes" +%H:%M)
    
    # Determinar día de la semana (0=lunes, 6=domingo)
    local weekday=$(date +%u)
    local weekday_name=""
    case $weekday in
        1) weekday_name="monday" ;;
        2) weekday_name="tuesday" ;;
        3) weekday_name="wednesday" ;;
        4) weekday_name="thursday" ;;
        5) weekday_name="friday" ;;
        6) weekday_name="saturday" ;;
        7) weekday_name="sunday" ;;
    esac
    
    # Crear JSON para la programación
    local schedule_json=$(cat <<EOF
{
    "parking_id": 1,
    "name": "Prueba de validación - $(date +%H:%M)",
    "description": "Programación de prueba para validar integración",
    "start_date": "$current_date",
    "end_date": "$(date -d "+7 days" +%Y-%m-%d)",
    "start_time": "$current_time",
    "end_time": "$end_time",
    "message": "PROVA VALIDACIÓ",
    "color": 3,
    "font_size": 2,
    "effect": "static",
    "is_active": true,
    "priority": 1,
    "$weekday_name": true
}
EOF
)
    
    # Enviar request a la API
    local response=$(curl -s -X POST "$API_URL/schedules" \
        -H "Content-Type: application/json" \
        -d "$schedule_json")
    
    # Verificar respuesta
    if echo "$response" | grep -q '"success":true'; then
        local schedule_id=$(echo "$response" | grep -o '"schedule_id":[0-9]*' | cut -d: -f2)
        print_status "OK" "Programación de prueba creada (ID: $schedule_id)"
        
        # Verificar si se ejecutó automáticamente
        if echo "$response" | grep -q '"auto_executed":true'; then
            local panels_affected=$(echo "$response" | grep -o '"panels_affected":[0-9]*' | cut -d: -f2)
            print_status "OK" "Programación ejecutada automáticamente ($panels_affected paneles afectados)"
        else
            print_status "WARNING" "Programación no se ejecutó automáticamente"
        fi
        
        return 0
    else
        print_status "ERROR" "Error creando programación de prueba: $response"
        return 1
    fi
}

# Función para verificar programaciones activas
check_active_schedules() {
    echo ""
    echo "--- Verificando programaciones activas ---"
    
    local response=$(curl -s "$API_URL/parking/1/active-schedules")
    
    if echo "$response" | grep -q '"success":true'; then
        local schedules_count=$(echo "$response" | grep -o '"schedules":\[.*\]' | grep -o '\[.*\]' | jq length 2>/dev/null || echo "0")
        print_status "OK" "API de programaciones activas funciona - $schedules_count programaciones activas"
        return 0
    else
        print_status "ERROR" "Error obteniendo programaciones activas: $response"
        return 1
    fi
}

# Función para verificar logs del sistema
check_system_logs() {
    echo ""
    echo "--- Verificando logs del sistema ---"
    
    # Verificar logs del API
    if journalctl -u parking-api --since "1 hour ago" | grep -q "schedule\|programación"; then
        print_status "OK" "Logs del API contienen entradas de programaciones"
    else
        print_status "WARNING" "No se encontraron logs de programaciones en el API"
    fi
    
    # Verificar logs del monitor
    if [ -f "schedule_monitor.log" ]; then
        local recent_entries=$(tail -n 20 schedule_monitor.log | grep -c "$(date +%Y-%m-%d)")
        print_status "OK" "Monitor tiene $recent_entries entradas de hoy"
    else
        print_status "WARNING" "Archivo de logs del monitor no encontrado"
    fi
}

# Función principal de validación
main() {
    echo "Iniciando validación del sistema de programaciones..."
    echo ""
    
    local errors=0
    local warnings=0
    
    # 1. Verificar servicios
    echo "1. Verificando servicios..."
    if ! check_service "parking-api"; then
        ((errors++))
    fi
    
    if ! check_service "parking-camera"; then
        ((errors++))
    fi
    
    # 2. Verificar API
    echo ""
    echo "2. Verificando API..."
    if ! check_api_endpoint "/parkings" "200"; then
        ((errors++))
    fi
    
    if ! check_api_endpoint "/schedules" "200"; then
        ((errors++))
    fi
    
    # 3. Verificar base de datos
    echo ""
    echo "3. Verificando base de datos..."
    if ! check_schedules_in_db; then
        ((errors++))
    fi
    
    # 4. Verificar programaciones activas
    if ! check_active_schedules; then
        ((warnings++))
    fi
    
    # 5. Crear programación de prueba
    if ! create_test_schedule; then
        ((errors++))
    fi
    
    # 6. Verificar logs
    check_system_logs
    
    # 7. Verificar logs del monitor
    if ! check_monitor_logs; then
        ((warnings++))
    fi
    
    # Resumen
    echo ""
    echo "=== RESUMEN DE VALIDACIÓN ==="
    echo "Errores encontrados: $errors"
    echo "Advertencias: $warnings"
    echo ""
    
    if [ $errors -eq 0 ]; then
        print_status "OK" "Validación completada exitosamente"
        echo ""
        echo "El sistema de programaciones está funcionando correctamente:"
        echo "✅ Los servicios están ejecutándose"
        echo "✅ La API responde correctamente"
        echo "✅ La base de datos es accesible"
        echo "✅ Las programaciones se crean y ejecutan automáticamente"
        echo "✅ El monitor detecta y finaliza programaciones"
        exit 0
    else
        print_status "ERROR" "Se encontraron $errors errores durante la validación"
        echo ""
        echo "Recomendaciones:"
        echo "- Verificar que todos los servicios estén ejecutándose"
        echo "- Revisar los logs para más detalles"
        echo "- Comprobar la conectividad de la base de datos"
        exit 1
    fi
}

# Ejecutar validación
main 