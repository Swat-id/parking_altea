#!/bin/bash

# Script de actualización local para correcciones de valenciano y configuración de colores dinámica

set -e

echo "🚀 Iniciando actualización de valenciano y configuración de colores dinámica..."
echo "=================================================="

# Variables
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

# 1. Crear backup
print_status "Creando backup de la base de datos..."
mkdir -p $BACKUP_DIR
sudo -u postgres pg_dump parking_db > $BACKUP_DIR/parking_db_backup.sql
print_status "Backup creado en: $BACKUP_DIR"

# 2. Verificar que estamos en la rama correcta
print_status "Verificando rama actual..."
cd /opt/parking_altea
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "v2.6_valenciano_colors" ]; then
    print_status "Cambiando a rama v2.6_valenciano_colors..."
    git checkout v2.6_valenciano_colors
    git pull origin v2.6_valenciano_colors
else
    print_status "Ya estamos en la rama v2.6_valenciano_colors"
    git pull origin v2.6_valenciano_colors
fi

# 3. Ejecutar migración de base de datos
print_status "Ejecutando migración de base de datos..."
cd /opt/parking_altea
python3 src/update_database_panels_v2.6.py

# 4. Verificar correcciones de valenciano
print_status "Verificando correcciones de textos en valenciano..."
python3 test/test_valenciano_corrections.py

# 5. Verificar configuración de colores dinámica
print_status "Verificando configuración de colores dinámica..."
psql -h localhost -U parking_user -d parking_db -c "
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
"

# 6. Reiniciar servicios
print_status "Reiniciando servicios..."
systemctl restart parking-api
systemctl status parking-api --no-pager

# 7. Verificar textos en valenciano en la base de datos
print_status "Verificando textos en valenciano en la base de datos..."
psql -h localhost -U parking_user -d parking_db -c "
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
"

# 8. Mostrar resumen
print_status "Mostrando resumen de cambios..."
psql -h localhost -U parking_user -d parking_db -c "
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
"

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
print_status "📁 Backup disponible en: $BACKUP_DIR" 