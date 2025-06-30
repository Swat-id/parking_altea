#!/bin/bash

# Script de actualización para paneles v2.6
# Actualiza la base de datos y servicios en el servidor

set -e

echo "🚀 Iniciando actualización de paneles v2.6..."
echo "=================================================="

# Variables
REMOTE_HOST="root@157.180.91.63"
REMOTE_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups/panels_v2.6_$(date +%Y%m%d_%H%M%S)"

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
remote_exec "cd $REMOTE_DIR && git checkout v2.5_no_login_paneles"
remote_exec "cd $REMOTE_DIR && git pull origin v2.5_no_login_paneles"

# 3. Ejecutar migración de base de datos
print_status "Ejecutando migración de base de datos..."
remote_exec "cd $REMOTE_DIR && python3 src/update_database_panels_v2.6.py"

# 4. Verificar migración
print_status "Verificando migración..."
remote_exec "cd $REMOTE_DIR && python3 test/test_panel_v2.6.py"

# 5. Actualizar configuración de servicios
print_status "Actualizando configuración de servicios..."

# Crear archivo de configuración para el servicio de paneles
cat > panel_service_config.json << 'EOF'
{
    "api_url": "http://127.0.0.1:5656/sendMulti",
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "enabled": true
}
EOF

remote_copy "panel_service_config.json" "$REMOTE_DIR/config/"

# 6. Reiniciar servicios necesarios
print_status "Reiniciando servicios..."
remote_exec "systemctl restart parking-api"
remote_exec "systemctl status parking-api --no-pager"

# 7. Verificar que todo funciona
print_status "Verificando funcionamiento..."
remote_exec "cd $REMOTE_DIR && python3 -c \"
import sys
sys.path.append('src')
from panel_communication_service import PanelCommunicationService
service = PanelCommunicationService()
result = service.test_connection()
print('API Panel Service:', 'OK' if result['success'] else 'ERROR')
\""

# 8. Mostrar resumen de cambios
print_status "Mostrando resumen de cambios..."
remote_exec "cd $REMOTE_DIR && psql -h localhost -U parking_user -d parking_altea -c \"
SELECT 
    'Paneles actualizados' as cambio,
    COUNT(*) as cantidad
FROM panels 
WHERE fabricante IS NOT NULL
UNION ALL
SELECT 
    'Idiomas cargados' as cambio,
    COUNT(*) as cantidad
FROM panel_languages
UNION ALL
SELECT 
    'Configuración API' as cambio,
    COUNT(*) as cantidad
FROM panel_api_config;
\""

# 9. Limpiar archivos temporales
rm -f panel_service_config.json

echo ""
echo "=================================================="
print_status "✅ Actualización de paneles v2.6 completada exitosamente!"
echo ""
print_status "📋 Resumen de cambios:"
echo "   - Nuevas columnas en tabla panels"
echo "   - Tabla de idiomas creada y poblada"
echo "   - Configuración de API de paneles"
echo "   - Servicio de comunicación actualizado"
echo ""
print_status "🔧 Próximos pasos:"
echo "   - Verificar que la API REST en puerto 5656 esté funcionando"
echo "   - Probar envío de mensajes a paneles"
echo "   - Configurar idiomas específicos por panel si es necesario"
echo ""
print_status "📁 Backup disponible en: $BACKUP_DIR" 