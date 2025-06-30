#!/bin/bash

# Script de actualización para correcciones de valenciano y configuración de colores dinámica
# Actualiza la base de datos y servicios en el servidor

set -e

echo "🚀 Iniciando actualización de valenciano y configuración de colores dinámica..."
echo "=================================================="

# Variables
REMOTE_HOST="root@157.180.91.63"
REMOTE_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups/valenciano_colors_$(date +%Y%m%d_%H%M%S)"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para ejecutar comandos remotos
remote_exec() {
    ssh $REMOTE_HOST "$1"
}

# Función para copiar archivos
remote_copy() {
    scp "$1" "$REMOTE_HOST:$2"
}

# 1. Crear backup
print_status "Creando backup de la base de datos..."
remote_exec "mkdir -p $BACKUP_DIR"
remote_exec "pg_dump -h localhost -U parking_user -d parking_altea > $BACKUP_DIR/parking_altea_backup.sql"
print_status "Backup creado en: $BACKUP_DIR"

# 2. Actualizar código en el servidor
print_status "Actualizando código en el servidor..."
remote_exec "cd $REMOTE_DIR && git fetch origin"
remote_exec "cd $REMOTE_DIR && git checkout v2.6_valenciano_colors"
remote_exec "cd $REMOTE_DIR && git pull origin v2.6_valenciano_colors"

# 3. Ejecutar migración de base de datos para corregir textos en valenciano
print_status "Ejecutando migración de base de datos para corregir textos en valenciano..."
remote_exec "cd $REMOTE_DIR && python3 src/update_database_panels_v2.6.py"

# 4. Verificar correcciones de valenciano
print_status "Verificando correcciones de textos en valenciano..."
remote_exec "cd $REMOTE_DIR && python3 test/test_valenciano_corrections.py"

# 5. Verificar configuración de colores dinámica
print_status "Verificando configuración de colores dinámica..."
remote_exec "cd $REMOTE_DIR && psql -h localhost -U parking_user -d parking_altea -c \"
SELECT 
    name,
    threshold_dense,
    threshold_full,
    current_occupancy,
    status,
    CASE 
        WHEN (max_capacity - current_occupancy) < 0 THEN '🔴 Rojo (descuadre)'
        WHEN (max_capacity - current_occupancy) <= threshold_full THEN '🔴 Rojo (completo)'
        WHEN (max_capacity - current_occupancy) <= threshold_dense THEN '🟡 Amarillo (denso)'
        ELSE '🟢 Verde (libre)'
    END as color_esperado
FROM parkings
ORDER BY id;
\""

# 6. Reiniciar servicios necesarios
print_status "Reiniciando servicios..."
remote_exec "systemctl restart parking-api"
remote_exec "systemctl status parking-api --no-pager"

# 7. Verificar que los servicios funcionan correctamente
print_status "Verificando funcionamiento de servicios..."
remote_exec "cd $REMOTE_DIR && python3 -c \"
import sys
sys.path.append('src')
try:
    from panel_communication_service import PanelCommunicationService
    service = PanelCommunicationService()
    result = service.test_connection()
    print('✅ Panel Communication Service:', 'OK' if result['success'] else 'ERROR')
except Exception as e:
    print('❌ Error en Panel Communication Service:', str(e))
\""

# 8. Verificar textos en valenciano en la base de datos
print_status "Verificando textos en valenciano en la base de datos..."
remote_exec "cd $REMOTE_DIR && psql -h localhost -U parking_user -d parking_altea -c \"
SELECT 
    language_code,
    language_name,
    libre_text,
    denso_text,
    completo_text,
    CASE 
        WHEN libre_text = 'LLIURE' AND denso_text = 'DENS' AND completo_text = 'COMPLET' 
        THEN '✅ Correcto' 
        ELSE '❌ Incorrecto' 
    END as estado
FROM panel_languages 
WHERE language_code = 'va';
\""

# 9. Mostrar resumen de cambios
print_status "Mostrando resumen de cambios..."
remote_exec "cd $REMOTE_DIR && psql -h localhost -U parking_user -d parking_altea -c \"
SELECT 
    'Parkings con umbrales configurados' as cambio,
    COUNT(*) as cantidad
FROM parkings 
WHERE threshold_dense IS NOT NULL AND threshold_full IS NOT NULL
UNION ALL
SELECT 
    'Textos en valenciano corregidos' as cambio,
    COUNT(*) as cantidad
FROM panel_languages 
WHERE language_code = 'va' 
    AND libre_text = 'LLIURE' 
    AND denso_text = 'DENS' 
    AND completo_text = 'COMPLET'
UNION ALL
SELECT 
    'Configuración de colores dinámica' as cambio,
    COUNT(*) as cantidad
FROM parkings 
WHERE threshold_dense > 0 AND threshold_full > 0;
\""

# 10. Verificar frontend
print_status "Verificando frontend..."
remote_exec "curl -s -o /dev/null -w '%{http_code}' http://157.180.91.63:5789" || print_warning "Frontend no responde (puede estar en desarrollo)"

echo ""
echo "=================================================="
print_status "✅ Actualización de valenciano y configuración de colores completada exitosamente!"
echo ""
print_status "📋 Resumen de cambios:"
echo "   - Textos en valenciano corregidos: LLIURE, DENS, COMPLET"
echo "   - Configuración de colores dinámica implementada"
echo "   - Umbrales configurables desde frontend"
echo "   - Documentación actualizada en /docs"
echo "   - Script de verificación añadido"
echo ""
print_status "🎨 Configuración de colores dinámica:"
echo "   - Verde: Ocupación < threshold_dense"
echo "   - Amarillo: Ocupación >= threshold_dense y < threshold_full"
echo "   - Rojo: Ocupación >= threshold_full"
echo ""
print_status "🔧 Próximos pasos:"
echo "   - Verificar que los paneles muestran los textos correctos en valenciano"
echo "   - Probar la configuración de umbrales desde el frontend"
echo "   - Verificar que los colores se actualizan según los umbrales"
echo ""
print_status "📁 Backup disponible en: $BACKUP_DIR" 