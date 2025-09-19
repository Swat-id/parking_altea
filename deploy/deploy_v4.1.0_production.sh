#!/bin/bash

# Script de Despliegue Producción v4.1.0
# Servidor: 157.180.91.63
# Funcionalidades: Sensores Individuales + Dashboard + Servicio Push Puerto 3535

set -e

echo "=== DESPLIEGUE PRODUCCIÓN v4.1.0 ==="
echo "Servidor: 157.180.91.63"
echo "Fecha: $(date)"
echo "Usuario: $(whoami)"
echo

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
PROJECT_DIR="/opt/fleximodo"
BACKUP_DIR="/opt/fleximodo/backups/$(date +%Y%m%d_%H%M%S)"
BRANCH="v4.1.0"
FRONTEND_PORT=5789
API_PORT=5000
PUSH_SERVICE_PORT=3535
DB_NAME="parking_db"

# Función para logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Verificar que estamos en el servidor correcto
if [ "$(hostname -I | grep -o '157.180.91.63')" != "157.180.91.63" ]; then
    log_error "Este script debe ejecutarse en el servidor 157.180.91.63"
    exit 1
fi

# Verificar permisos de root
if [ "$EUID" -ne 0 ]; then
    log_error "Este script debe ejecutarse como root"
    exit 1
fi

log_step "1. Verificando estado actual del sistema..."

# Verificar directorio del proyecto
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Directorio del proyecto $PROJECT_DIR no encontrado"
    exit 1
fi

cd "$PROJECT_DIR"

# Verificar que estamos en un repositorio git
if [ ! -d ".git" ]; then
    log_error "No se encontró repositorio git en $PROJECT_DIR"
    exit 1
fi

# Verificar servicios actuales
log_info "Servicios actuales en ejecución:"
systemctl status parking-api 2>/dev/null && log_info "✅ parking-api activo" || log_warning "⚠️  parking-api inactivo"
systemctl status parking-panel-worker 2>/dev/null && log_info "✅ parking-panel-worker activo" || log_warning "⚠️  parking-panel-worker inactivo"

# Verificar puertos en uso
log_info "Puertos actuales en uso:"
if lsof -i :$FRONTEND_PORT > /dev/null 2>&1; then
    log_info "✅ Puerto $FRONTEND_PORT (frontend) en uso"
else
    log_warning "⚠️  Puerto $FRONTEND_PORT (frontend) libre"
fi

if lsof -i :$API_PORT > /dev/null 2>&1; then
    log_info "✅ Puerto $API_PORT (API) en uso"
else
    log_warning "⚠️  Puerto $API_PORT (API) libre"
fi

if lsof -i :$PUSH_SERVICE_PORT > /dev/null 2>&1; then
    log_warning "⚠️  Puerto $PUSH_SERVICE_PORT ya en uso - se liberará"
    PID=$(lsof -t -i :$PUSH_SERVICE_PORT)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        log_info "Proceso $PID terminado en puerto $PUSH_SERVICE_PORT"
    fi
else
    log_info "✅ Puerto $PUSH_SERVICE_PORT (push service) disponible"
fi

log_step "2. Creando backup del sistema actual..."

# Crear directorio de backup
mkdir -p "$BACKUP_DIR"

# Backup de código fuente
log_info "Creando backup del código fuente..."
tar -czf "$BACKUP_DIR/source_code.tar.gz" --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='__pycache__' --exclude='logs' .

# Backup de base de datos
log_info "Creando backup de la base de datos..."
sudo -u postgres pg_dump $DB_NAME > "$BACKUP_DIR/database_backup.sql"

# Backup de configuración de servicios
log_info "Creando backup de servicios systemd..."
mkdir -p "$BACKUP_DIR/systemd"
cp /etc/systemd/system/parking-*.service "$BACKUP_DIR/systemd/" 2>/dev/null || true

log_info "✅ Backup creado en: $BACKUP_DIR"

log_step "3. Descargando actualizaciones de la rama $BRANCH..."

# Verificar rama actual
CURRENT_BRANCH=$(git branch --show-current)
log_info "Rama actual: $CURRENT_BRANCH"

# Hacer stash de cambios locales si existen
if ! git diff-index --quiet HEAD --; then
    log_warning "Detectados cambios locales. Creando stash..."
    git stash push -m "Backup antes de despliegue v4.1.0 - $(date)"
fi

# Fetch y checkout a la rama v4.1.0
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH

log_info "✅ Código actualizado a la rama $BRANCH"
log_info "Último commit: $(git log --oneline -1)"

log_step "4. Verificando dependencias del sistema..."

# Verificar Python y pip
python3 --version || { log_error "Python3 no encontrado"; exit 1; }
pip3 --version || { log_error "pip3 no encontrado"; exit 1; }

# Verificar Node.js y npm
node --version || { log_error "Node.js no encontrado"; exit 1; }
npm --version || { log_error "npm no encontrado"; exit 1; }

# Verificar PostgreSQL
sudo -u postgres psql -c "SELECT version();" > /dev/null || { log_error "PostgreSQL no accesible"; exit 1; }

log_info "✅ Todas las dependencias verificadas"

log_step "5. Actualizando base de datos..."

# Ejecutar migraciones de base de datos
log_info "Ejecutando migraciones de base de datos..."

# Crear tablas de sensores individuales
log_info "Creando tablas de sensores individuales..."
sudo -u postgres psql $DB_NAME << 'EOF'
-- Crear tabla de sensores individuales
CREATE TABLE IF NOT EXISTS individual_sensors (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(20) DEFAULT 'PMR' NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    parking_id INTEGER REFERENCES parkings(id) ON DELETE SET NULL,
    description TEXT,
    location_coordinates VARCHAR(100),
    manufacturer VARCHAR(50) DEFAULT 'Fleximodo' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear tabla de historial de estados
CREATE TABLE IF NOT EXISTS sensor_status_history (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES individual_sensors(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('free', 'busy', 'error', 'unknown', 'notcalib')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER CHECK (battery_capacity >= 0 AND battery_capacity <= 100),
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    radar_only BOOLEAN DEFAULT FALSE,
    raw_data JSONB
);

-- Crear tabla de estado actual
CREATE TABLE IF NOT EXISTS sensor_current_status (
    sensor_id INTEGER PRIMARY KEY REFERENCES individual_sensors(id) ON DELETE CASCADE,
    current_status VARCHAR(20) NOT NULL CHECK (current_status IN ('free', 'busy', 'error', 'unknown', 'notcalib')),
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER CHECK (battery_capacity >= 0 AND battery_capacity <= 100),
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    consecutive_errors INTEGER DEFAULT 0,
    last_successful_ping TIMESTAMP WITH TIME ZONE
);

-- Crear tabla de resúmenes por parking
CREATE TABLE IF NOT EXISTS parking_sensor_summary (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
    sensor_type VARCHAR(20) NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    total_sensors INTEGER DEFAULT 0,
    free_sensors INTEGER DEFAULT 0,
    busy_sensors INTEGER DEFAULT 0,
    error_sensors INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(parking_id, sensor_type)
);

-- Actualizar tabla panels para ventanas
ALTER TABLE panels ADD COLUMN IF NOT EXISTS last_message_window_0 TEXT;
ALTER TABLE panels ADD COLUMN IF NOT EXISTS last_message_window_1 TEXT;
ALTER TABLE panels ADD COLUMN IF NOT EXISTS last_update_window_0 TIMESTAMP WITH TIME ZONE;
ALTER TABLE panels ADD COLUMN IF NOT EXISTS last_update_window_1 TIMESTAMP WITH TIME ZONE;
ALTER TABLE panels ADD COLUMN IF NOT EXISTS window_config_json JSONB DEFAULT '{"windows": [{"id": 0, "enabled": true}, {"id": 1, "enabled": false}]}'::jsonb;

-- Migrar datos existentes
UPDATE panels SET 
    last_message_window_0 = last_message,
    last_update_window_0 = last_update 
WHERE last_message IS NOT NULL AND last_message_window_0 IS NULL;

\echo 'Tablas creadas exitosamente'
EOF

# Crear índices
log_info "Creando índices optimizados..."
sudo -u postgres psql $DB_NAME << 'EOF'
-- Índices para sensores individuales
CREATE INDEX IF NOT EXISTS idx_individual_sensors_parking_id ON individual_sensors(parking_id);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_type ON individual_sensors(sensor_type);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_active ON individual_sensors(is_active);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_serial ON individual_sensors(serial_number);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_name ON individual_sensors(name);

-- Índices para historial de estados
CREATE INDEX IF NOT EXISTS idx_sensor_status_sensor_id ON sensor_status_history(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensor_status_timestamp ON sensor_status_history(timestamp DESC);

-- Índices para estado actual
CREATE INDEX IF NOT EXISTS idx_sensor_current_status_composite ON sensor_current_status(current_status, last_update DESC, battery_capacity);

-- Índices para resúmenes
CREATE INDEX IF NOT EXISTS idx_parking_sensor_summary_parking ON parking_sensor_summary(parking_id);

-- Índices para panels
CREATE INDEX IF NOT EXISTS idx_panels_window_0_update ON panels(last_update_window_0);
CREATE INDEX IF NOT EXISTS idx_panels_window_1_update ON panels(last_update_window_1);
CREATE INDEX IF NOT EXISTS idx_panels_window_config ON panels USING GIN(window_config_json);

\echo 'Índices creados exitosamente'
EOF

log_info "✅ Base de datos actualizada correctamente"

log_step "6. Actualizando dependencias Python..."

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    log_info "Entorno virtual activado"
else
    log_warning "Entorno virtual no encontrado. Creando..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Actualizar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Instalar dependencias específicas para el servicio push
pip install flask==2.3.3
pip install sqlalchemy==2.0.21
pip install psycopg2-binary==2.9.7
pip install requests==2.31.0

log_info "✅ Dependencias Python actualizadas"

log_step "7. Compilando y desplegando frontend..."

cd client

# Verificar si node_modules existe
if [ ! -d "node_modules" ]; then
    log_info "Instalando dependencias npm..."
    npm install
else
    log_info "Actualizando dependencias npm..."
    npm update
fi

# Compilar frontend
log_info "Compilando frontend para producción..."
npm run build

# Verificar que se generó el build
if [ ! -d "dist" ]; then
    log_error "Build del frontend falló"
    exit 1
fi

log_info "✅ Frontend compilado correctamente"

cd ..

log_step "8. Desplegando servicio push (Puerto $PUSH_SERVICE_PORT)..."

# Copiar archivo de servicio systemd
cp deploy/parking-sensor-push.service /etc/systemd/system/
chmod 644 /etc/systemd/system/parking-sensor-push.service

# Recargar systemd
systemctl daemon-reload

# Habilitar e iniciar el servicio
systemctl enable parking-sensor-push
systemctl start parking-sensor-push

# Verificar estado
sleep 3
if systemctl is-active --quiet parking-sensor-push; then
    log_info "✅ Servicio push iniciado correctamente"
else
    log_error "❌ Error iniciando servicio push"
    systemctl status parking-sensor-push
    exit 1
fi

log_step "9. Reiniciando servicios existentes..."

# Reiniciar API backend
if systemctl is-active --quiet parking-api; then
    log_info "Reiniciando parking-api..."
    systemctl restart parking-api
    sleep 2
    if systemctl is-active --quiet parking-api; then
        log_info "✅ parking-api reiniciado correctamente"
    else
        log_error "❌ Error reiniciando parking-api"
        systemctl status parking-api
    fi
else
    log_warning "parking-api no estaba activo"
fi

# Reiniciar panel worker si existe
if systemctl is-active --quiet parking-panel-worker; then
    log_info "Reiniciando parking-panel-worker..."
    systemctl restart parking-panel-worker
    sleep 2
    if systemctl is-active --quiet parking-panel-worker; then
        log_info "✅ parking-panel-worker reiniciado correctamente"
    else
        log_warning "⚠️  parking-panel-worker con problemas"
    fi
else
    log_warning "parking-panel-worker no estaba activo"
fi

log_step "10. Configurando firewall..."

# Abrir puerto 3535 en firewall
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    log_info "Configurando reglas de firewall..."
    ufw allow $PUSH_SERVICE_PORT/tcp comment "Parking Sensor Push Service v4.1.0"
    log_info "Puerto $PUSH_SERVICE_PORT abierto en firewall"
else
    log_info "UFW no está activo o no está instalado"
fi

log_step "11. Validando despliegue..."

# Verificar servicios
log_info "Estado de servicios:"
systemctl is-active parking-api && log_info "✅ parking-api: ACTIVO" || log_warning "⚠️  parking-api: INACTIVO"
systemctl is-active parking-sensor-push && log_info "✅ parking-sensor-push: ACTIVO" || log_error "❌ parking-sensor-push: INACTIVO"

# Verificar puertos
log_info "Verificando puertos:"
if lsof -i :$API_PORT > /dev/null 2>&1; then
    log_info "✅ Puerto $API_PORT (API): ACTIVO"
else
    log_warning "⚠️  Puerto $API_PORT (API): INACTIVO"
fi

if lsof -i :$PUSH_SERVICE_PORT > /dev/null 2>&1; then
    log_info "✅ Puerto $PUSH_SERVICE_PORT (Push Service): ACTIVO"
else
    log_error "❌ Puerto $PUSH_SERVICE_PORT (Push Service): INACTIVO"
fi

# Test de conectividad
log_info "Probando conectividad de servicios..."

# Test API principal
if curl -s -f "http://localhost:$API_PORT/api/health" > /dev/null; then
    log_info "✅ API principal responde correctamente"
else
    log_warning "⚠️  API principal no responde"
fi

# Test servicio push
if curl -s -f "http://localhost:$PUSH_SERVICE_PORT/health" > /dev/null; then
    log_info "✅ Servicio push responde correctamente"
    # Mostrar información del servicio
    echo
    log_info "Información del servicio push:"
    curl -s "http://localhost:$PUSH_SERVICE_PORT/health" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "Error parsing JSON"
else
    log_error "❌ Servicio push no responde"
fi

# Test base de datos
log_info "Verificando base de datos..."
SENSOR_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM individual_sensors;" 2>/dev/null | xargs)
log_info "Sensores individuales en BD: ${SENSOR_COUNT:-0}"

echo
log_info "=== RESUMEN DEL DESPLIEGUE ==="
echo
echo "🚀 Versión desplegada: v4.1.0"
echo "📅 Fecha: $(date)"
echo "🖥️  Servidor: 157.180.91.63"
echo "💾 Backup: $BACKUP_DIR"
echo
echo "🔌 SERVICIOS DESPLEGADOS:"
echo "  • API Backend: http://157.180.91.63:$API_PORT"
echo "  • Push Service: http://157.180.91.63:$PUSH_SERVICE_PORT"
echo "  • Frontend: http://157.180.91.63:$FRONTEND_PORT"
echo
echo "📊 NUEVAS FUNCIONALIDADES:"
echo "  • ✅ Sistema sensores individuales completo"
echo "  • ✅ Dashboard con estadísticas tiempo real"
echo "  • ✅ Servicio push puerto $PUSH_SERVICE_PORT"
echo "  • ✅ Gestión paneles con ventanas Tipo 3"
echo "  • ✅ Integración página parking con sensores"
echo
echo "🔧 COMANDOS ÚTILES:"
echo "  • Ver logs API: journalctl -u parking-api -f"
echo "  • Ver logs Push: journalctl -u parking-sensor-push -f"
echo "  • Estado servicios: systemctl status parking-*"
echo "  • Reiniciar servicio: systemctl restart parking-sensor-push"
echo
echo "🌐 ENDPOINTS NUEVOS:"
echo "  • Health Push: http://157.180.91.63:$PUSH_SERVICE_PORT/health"
echo "  • Push Sensores: http://157.180.91.63:$PUSH_SERVICE_PORT/push"
echo "  • Stats Dashboard: http://157.180.91.63:$API_PORT/api/sensors/stats"
echo
echo "✅ DESPLIEGUE COMPLETADO EXITOSAMENTE"
