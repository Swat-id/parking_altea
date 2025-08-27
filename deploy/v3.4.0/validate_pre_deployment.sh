#!/bin/bash
"""
Script de validación pre-despliegue para Sistema v3.4.0
Verifica que el sistema esté listo para el despliegue
"""

set -euo pipefail

# Configuración
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
CHECKS_TOTAL=0
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Función de logging
check_start() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    echo -e "${BLUE}[CHECK $CHECKS_TOTAL] $1${NC}"
}

check_pass() {
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    echo -e "${GREEN}  ✅ $1${NC}"
}

check_fail() {
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    echo -e "${RED}  ❌ $1${NC}"
}

check_warning() {
    CHECKS_WARNING=$((CHECKS_WARNING + 1))
    echo -e "${YELLOW}  ⚠️ $1${NC}"
}

# Función principal
main() {
    echo "🔍 VALIDACIÓN PRE-DESPLIEGUE SISTEMA v3.4.0"
    echo "=============================================="
    echo ""
    
    # 1. Verificar conectividad SSH
    check_start "Conectividad SSH al servidor"
    if ssh -o ConnectTimeout=10 root@157.180.91.63 "echo 'SSH OK'" >/dev/null 2>&1; then
        check_pass "Conexión SSH exitosa"
    else
        check_fail "No se puede conectar por SSH"
    fi
    
    # 2. Verificar servicios actuales
    check_start "Estado de servicios actuales"
    if ssh root@157.180.91.63 "systemctl is-active --quiet parking-api" >/dev/null 2>&1; then
        check_pass "API service activo"
    else
        check_fail "API service no está activo"
    fi
    
    if ssh root@157.180.91.63 "systemctl is-active --quiet parking-camera" >/dev/null 2>&1; then
        check_pass "Camera service activo"
    else
        check_warning "Camera service no está activo"
    fi
    
    # 3. Verificar base de datos
    check_start "Conectividad a base de datos"
    if ssh root@157.180.91.63 "psql parking_db -c 'SELECT version();'" >/dev/null 2>&1; then
        check_pass "Conexión a PostgreSQL exitosa"
    else
        check_fail "No se puede conectar a PostgreSQL"
    fi
    
    # Verificar tablas críticas
    PARKING_COUNT=$(ssh root@157.180.91.63 "psql parking_db -t -c 'SELECT COUNT(*) FROM parkings;'" 2>/dev/null | tr -d ' ' || echo "0")
    if [ "$PARKING_COUNT" -gt 0 ]; then
        check_pass "Tabla parkings tiene $PARKING_COUNT registros"
    else
        check_fail "Tabla parkings vacía o no accesible"
    fi
    
    USER_COUNT=$(ssh root@157.180.91.63 "psql parking_db -t -c 'SELECT COUNT(*) FROM users;'" 2>/dev/null | tr -d ' ' || echo "0")
    if [ "$USER_COUNT" -gt 0 ]; then
        check_pass "Tabla users tiene $USER_COUNT registros"
    else
        check_warning "Tabla users vacía o no accesible"
    fi
    
    # 4. Verificar espacio en disco
    check_start "Espacio en disco"
    DISK_USAGE=$(ssh root@157.180.91.63 "df /opt | tail -1 | awk '{print \$5}' | sed 's/%//'" 2>/dev/null || echo "100")
    if [ "$DISK_USAGE" -lt 70 ]; then
        check_pass "Espacio en disco OK (${DISK_USAGE}% usado)"
    elif [ "$DISK_USAGE" -lt 85 ]; then
        check_warning "Espacio en disco alto (${DISK_USAGE}% usado)"
    else
        check_fail "Espacio en disco crítico (${DISK_USAGE}% usado)"
    fi
    
    # 5. Verificar memoria
    check_start "Memoria disponible"
    MEMORY_FREE=$(ssh root@157.180.91.63 "free -m | grep Mem | awk '{print \$7}'" 2>/dev/null || echo "0")
    if [ "$MEMORY_FREE" -gt 500 ]; then
        check_pass "Memoria disponible OK (${MEMORY_FREE}MB libres)"
    elif [ "$MEMORY_FREE" -gt 200 ]; then
        check_warning "Memoria disponible baja (${MEMORY_FREE}MB libres)"
    else
        check_fail "Memoria disponible crítica (${MEMORY_FREE}MB libres)"
    fi
    
    # 6. Verificar endpoints actuales
    check_start "Endpoints del sistema actual"
    if ssh root@157.180.91.63 "curl -s localhost:8080/health | jq -e '.status'" >/dev/null 2>&1; then
        check_pass "API endpoint respondiendo"
    else
        check_fail "API endpoint no responde"
    fi
    
    # Camera server (puede no tener endpoint health)
    if ssh root@157.180.91.63 "curl -s localhost:5000/ -o /dev/null -w '%{http_code}' | grep -q '200\|404'" >/dev/null 2>&1; then
        check_pass "Camera server respondiendo"
    else
        check_warning "Camera server no responde (puede ser normal)"
    fi
    
    # 7. Verificar Git y código
    check_start "Repositorio Git"
    if ssh root@157.180.91.63 "cd /opt/parking_altea && git status" >/dev/null 2>&1; then
        check_pass "Repositorio Git accesible"
        
        # Verificar que puede acceder a la rama v3.4.0
        if ssh root@157.180.91.63 "cd /opt/parking_altea && git ls-remote origin v3.4.0" >/dev/null 2>&1; then
            check_pass "Rama v3.4.0 accesible en origin"
        else
            check_fail "Rama v3.4.0 no encontrada en origin"
        fi
    else
        check_fail "Repositorio Git no accesible"
    fi
    
    # 8. Verificar Python y dependencias básicas
    check_start "Entorno Python"
    if ssh root@157.180.91.63 "cd /opt/parking_altea && source venv/bin/activate && python --version" >/dev/null 2>&1; then
        check_pass "Virtual environment Python accesible"
    else
        check_fail "Virtual environment Python no accesible"
    fi
    
    # Verificar dependencias críticas
    if ssh root@157.180.91.63 "cd /opt/parking_altea && source venv/bin/activate && python -c 'import flask, psycopg2, sqlalchemy'" >/dev/null 2>&1; then
        check_pass "Dependencias críticas disponibles"
    else
        check_warning "Algunas dependencias pueden faltar"
    fi
    
    # 9. Verificar permisos
    check_start "Permisos y accesos"
    if ssh root@157.180.91.63 "[ -w /opt/parking_altea ]" >/dev/null 2>&1; then
        check_pass "Permisos de escritura en proyecto OK"
    else
        check_fail "Sin permisos de escritura en proyecto"
    fi
    
    if ssh root@157.180.91.63 "[ -w /etc/systemd/system ]" >/dev/null 2>&1; then
        check_pass "Permisos para servicios systemd OK"
    else
        check_fail "Sin permisos para servicios systemd"
    fi
    
    # 10. Verificar logs recientes
    check_start "Logs y errores recientes"
    ERROR_COUNT=$(ssh root@157.180.91.63 "journalctl -u parking-* --since '1 hour ago' | grep -ci error" 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        check_pass "Sin errores en logs recientes"
    elif [ "$ERROR_COUNT" -lt 5 ]; then
        check_warning "$ERROR_COUNT errores en logs recientes"
    else
        check_fail "$ERROR_COUNT errores en logs recientes (revisar antes de desplegar)"
    fi
    
    # 11. Verificar procesos y puertos
    check_start "Puertos en uso"
    PORT_5000=$(ssh root@157.180.91.63 "netstat -tulpn | grep :5000 | wc -l" 2>/dev/null || echo "0")
    PORT_8080=$(ssh root@157.180.91.63 "netstat -tulpn | grep :8080 | wc -l" 2>/dev/null || echo "0")
    
    if [ "$PORT_5000" -gt 0 ]; then
        check_pass "Puerto 5000 en uso (Camera server)"
    else
        check_warning "Puerto 5000 no en uso"
    fi
    
    if [ "$PORT_8080" -gt 0 ]; then
        check_pass "Puerto 8080 en uso (API server)"
    else
        check_warning "Puerto 8080 no en uso"
    fi
    
    # 12. Verificar horario (ventana de mantenimiento)
    check_start "Horario de despliegue"
    CURRENT_HOUR=$(date +%H)
    if [ "$CURRENT_HOUR" -ge 2 ] && [ "$CURRENT_HOUR" -le 6 ]; then
        check_pass "Horario apropiado para mantenimiento (${CURRENT_HOUR}:xx)"
    else
        check_warning "Fuera de ventana de mantenimiento recomendada (${CURRENT_HOUR}:xx)"
    fi
    
    # RESUMEN FINAL
    echo ""
    echo "=============================================="
    echo "📊 RESUMEN DE VALIDACIÓN PRE-DESPLIEGUE"
    echo "=============================================="
    echo -e "Total checks: ${CHECKS_TOTAL}"
    echo -e "${GREEN}Passed: ${CHECKS_PASSED}${NC}"
    echo -e "${YELLOW}Warnings: ${CHECKS_WARNING}${NC}"
    echo -e "${RED}Failed: ${CHECKS_FAILED}${NC}"
    echo ""
    
    # Determinar recomendación
    if [ "$CHECKS_FAILED" -eq 0 ]; then
        if [ "$CHECKS_WARNING" -eq 0 ]; then
            echo -e "${GREEN}✅ SISTEMA LISTO PARA DESPLIEGUE${NC}"
            echo "Todos los checks pasaron exitosamente."
            echo ""
            echo "▶️ Comando para proceder:"
            echo "   bash deploy/v3.4.0/deploy_v3_4_0_complete.sh"
            exit 0
        else
            echo -e "${YELLOW}⚠️ SISTEMA MAYORMENTE LISTO CON ADVERTENCIAS${NC}"
            echo "Hay ${CHECKS_WARNING} advertencias que deberían revisarse."
            echo "El despliegue puede proceder pero con precaución."
            echo ""
            echo "▶️ Comando para proceder (con cuidado):"
            echo "   bash deploy/v3.4.0/deploy_v3_4_0_complete.sh"
            exit 1
        fi
    else
        echo -e "${RED}❌ SISTEMA NO LISTO PARA DESPLIEGUE${NC}"
        echo "Hay ${CHECKS_FAILED} checks críticos fallidos que deben resolverse."
        echo ""
        echo "🔧 Acciones requeridas:"
        echo "1. Resolver los errores marcados con ❌"
        echo "2. Re-ejecutar validación"
        echo "3. Proceder solo cuando todos los checks críticos pasen"
        exit 2
    fi
}

# Verificar argumentos
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Script de validación pre-despliegue v3.4.0"
    echo ""
    echo "Uso: $0"
    echo ""
    echo "Este script verifica que el sistema esté listo para el despliegue"
    echo "realizando checks de conectividad, servicios, BD, recursos, etc."
    echo ""
    echo "Códigos de salida:"
    echo "  0 - Sistema completamente listo"
    echo "  1 - Sistema mayormente listo (advertencias)"
    echo "  2 - Sistema no listo (errores críticos)"
    exit 0
fi

# Ejecutar validación
main
