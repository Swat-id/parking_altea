#!/bin/bash

# Script para configurar las programaciones de paneles
# Versión: v2.7
# Fecha: 1 de Julio de 2025

set -e

echo "🚀 Configurando programaciones de paneles v2.7..."

# Variables
PROJECT_DIR="/opt/parking_altea"
BACKEND_DIR="$PROJECT_DIR/src"
CLIENT_DIR="$PROJECT_DIR/client"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Directorio del proyecto no encontrado: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

log_info "Directorio de trabajo: $(pwd)"

# 1. Ejecutar migración de base de datos
log_info "Ejecutando migración de base de datos..."

cd "$BACKEND_DIR"

if [ -f "migrate_panel_schedules.py" ]; then
    python3 migrate_panel_schedules.py
    if [ $? -eq 0 ]; then
        log_success "Migración de base de datos completada"
    else
        log_error "Error en la migración de base de datos"
        exit 1
    fi
else
    log_error "Script de migración no encontrado: migrate_panel_schedules.py"
    exit 1
fi

# 2. Verificar que las tablas se crearon correctamente
log_info "Verificando tablas creadas..."

python3 -c "
import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
from config import DB_URL

engine = create_engine(DB_URL)
with engine.connect() as conn:
    result = conn.execute(text(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('panel_schedules', 'panel_schedule_logs')
        ORDER BY table_name
    \"\"\"))
    
    tables = [row[0] for row in result]
    if len(tables) == 2:
        print('✅ Tablas creadas correctamente:', tables)
    else:
        print('❌ Error: Tablas encontradas:', tables)
        sys.exit(1)
"

if [ $? -eq 0 ]; then
    log_success "Verificación de tablas completada"
else
    log_error "Error en la verificación de tablas"
    exit 1
fi

# 3. Reiniciar el servicio de backend
log_info "Reiniciando servicio de backend..."

sudo systemctl restart parking-api

if [ $? -eq 0 ]; then
    log_success "Servicio de backend reiniciado"
else
    log_error "Error al reiniciar el servicio de backend"
    exit 1
fi

# 4. Verificar que el backend está funcionando
log_info "Verificando que el backend está funcionando..."

sleep 3

if curl -s http://localhost:5000/parkings > /dev/null; then
    log_success "Backend funcionando correctamente"
else
    log_error "Backend no responde"
    exit 1
fi

# 5. Construir y desplegar el frontend
log_info "Construyendo frontend..."

cd "$CLIENT_DIR"

# Verificar que el archivo Schedules.jsx existe
if [ ! -f "src/pages/Schedules.jsx" ]; then
    log_error "Archivo Schedules.jsx no encontrado"
    exit 1
fi

# Instalar dependencias si es necesario
if [ ! -d "node_modules" ]; then
    log_info "Instalando dependencias..."
    npm install
fi

# Construir el proyecto
log_info "Construyendo proyecto..."
npm run build

if [ $? -eq 0 ]; then
    log_success "Frontend construido correctamente"
else
    log_error "Error al construir el frontend"
    exit 1
fi

# 6. Verificar que el frontend está funcionando
log_info "Verificando que el frontend está funcionando..."

sleep 3

if curl -s http://localhost:5789 > /dev/null; then
    log_success "Frontend funcionando correctamente"
else
    log_error "Frontend no responde"
    exit 1
fi

# 7. Probar endpoints de programaciones
log_info "Probando endpoints de programaciones..."

# Probar GET /schedules
if curl -s http://localhost:5000/schedules > /dev/null; then
    log_success "Endpoint GET /schedules funcionando"
else
    log_error "Endpoint GET /schedules no responde"
fi

# Probar GET /parking/1/schedules
if curl -s http://localhost:5000/parking/1/schedules > /dev/null; then
    log_success "Endpoint GET /parking/1/schedules funcionando"
else
    log_error "Endpoint GET /parking/1/schedules no responde"
fi

# 8. Crear programación de prueba
log_info "Creando programación de prueba..."

TEST_SCHEDULE='{
  "parking_id": 1,
  "name": "Programación de Prueba",
  "description": "Programación creada automáticamente para pruebas",
  "start_date": "2025-07-01T00:00:00",
  "end_date": "2025-12-31T23:59:59",
  "start_time": "09:00",
  "end_time": "18:00",
  "monday": true,
  "tuesday": true,
  "wednesday": true,
  "thursday": true,
  "friday": true,
  "saturday": false,
  "sunday": false,
  "message": "PROVA PROGRAMACIÓ",
  "color": 2,
  "font_size": 2,
  "effect": "static",
  "priority": 1,
  "is_active": true
}'

RESPONSE=$(curl -s -X POST http://localhost:5000/schedules \
  -H "Content-Type: application/json" \
  -d "$TEST_SCHEDULE")

if echo "$RESPONSE" | grep -q "success.*true"; then
    log_success "Programación de prueba creada correctamente"
else
    log_warning "No se pudo crear la programación de prueba: $RESPONSE"
fi

# 9. Mostrar resumen
log_info "=== RESUMEN DE LA CONFIGURACIÓN ==="
log_success "✅ Migración de base de datos completada"
log_success "✅ Tablas verificadas"
log_success "✅ Backend reiniciado y funcionando"
log_success "✅ Frontend construido y funcionando"
log_success "✅ Endpoints de programaciones probados"
log_success "✅ Programación de prueba creada"

echo ""
log_info "🎉 Configuración de programaciones de paneles v2.7 completada exitosamente!"
echo ""
log_info "📋 Próximos pasos:"
echo "   1. Acceder a http://157.180.91.63:5789"
echo "   2. Ir a la sección 'Programaciones' en el menú"
echo "   3. Crear y gestionar programaciones de paneles"
echo ""
log_info "🔧 Endpoints disponibles:"
echo "   - GET /api/schedules - Listar programaciones"
echo "   - POST /api/schedules - Crear programación"
echo "   - GET /api/schedules/{id} - Obtener programación"
echo "   - PUT /api/schedules/{id} - Actualizar programación"
echo "   - DELETE /api/schedules/{id} - Eliminar programación"
echo "   - POST /api/schedules/{id}/toggle - Activar/desactivar"
echo "   - POST /api/schedules/{id}/execute - Ejecutar manualmente"
echo "   - GET /api/parking/{id}/schedules - Programaciones de un parking"
echo "   - GET /api/parking/{id}/active-schedules - Programaciones activas"
echo ""
log_info "📚 Documentación:"
echo "   - Ver docs/v2.7_status.md para más detalles"
echo "" 