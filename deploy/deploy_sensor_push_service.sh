#!/bin/bash

# Script de Despliegue - Servicio Push Sensores v4.1.0
# Puerto 3535 - Recepción de notificaciones de sensores Fleximodo

set -e

echo "=== DESPLIEGUE SERVICIO PUSH SENSORES v4.1.0 ==="
echo "Puerto: 3535"
echo "Fecha: $(date)"
echo

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
SERVICE_NAME="parking-sensor-push"
SERVICE_FILE="parking-sensor-push.service"
PYTHON_FILE="src/sensor_push_service.py"
PORT=3535
LOG_DIR="/opt/fleximodo/logs"
VENV_PATH="/opt/fleximodo/venv"

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

# Verificar que estamos en el directorio correcto
if [ ! -f "$PYTHON_FILE" ]; then
    log_error "No se encuentra $PYTHON_FILE. Ejecutar desde directorio raíz del proyecto."
    exit 1
fi

# Verificar permisos de root
if [ "$EUID" -ne 0 ]; then
    log_error "Este script debe ejecutarse como root"
    exit 1
fi

log_step "1. Verificando dependencias del sistema..."

# Verificar Python y pip
if ! command -v python3 &> /dev/null; then
    log_error "Python3 no está instalado"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    log_error "pip3 no está instalado"
    exit 1
fi

log_info "Python3 y pip3 disponibles"

log_step "2. Configurando entorno virtual..."

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"
chown root:root "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Verificar/crear entorno virtual
if [ ! -d "$VENV_PATH" ]; then
    log_info "Creando entorno virtual en $VENV_PATH"
    python3 -m venv "$VENV_PATH"
fi

# Activar entorno virtual
source "$VENV_PATH/bin/activate"

log_step "3. Instalando dependencias Python..."

# Instalar dependencias específicas para el servicio push
pip install --upgrade pip
pip install flask==2.3.3
pip install sqlalchemy==2.0.21
pip install psycopg2-binary==2.9.7
pip install requests==2.31.0

log_info "Dependencias instaladas correctamente"

log_step "4. Verificando conectividad de base de datos..."

# Test de conexión a PostgreSQL
sudo -u postgres psql -d parking_db -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_info "Conexión a base de datos OK"
else
    log_error "Error conectando a la base de datos"
    exit 1
fi

log_step "5. Verificando puerto $PORT..."

# Verificar si el puerto está en uso
if lsof -i :$PORT > /dev/null 2>&1; then
    log_warning "Puerto $PORT está en uso. Intentando liberar..."
    
    # Encontrar y terminar procesos usando el puerto
    PID=$(lsof -t -i :$PORT)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        log_info "Proceso $PID terminado"
        sleep 2
    fi
fi

# Verificar que el puerto esté libre
if lsof -i :$PORT > /dev/null 2>&1; then
    log_error "No se pudo liberar el puerto $PORT"
    exit 1
else
    log_info "Puerto $PORT disponible"
fi

log_step "6. Configurando servicio systemd..."

# Detener servicio si está ejecutándose
if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "Deteniendo servicio existente..."
    systemctl stop $SERVICE_NAME
fi

# Copiar archivo de servicio
cp "deploy/$SERVICE_FILE" "/etc/systemd/system/"
chmod 644 "/etc/systemd/system/$SERVICE_FILE"

# Recargar systemd
systemctl daemon-reload

log_info "Servicio systemd configurado"

log_step "7. Verificando permisos de archivos..."

# Asegurar permisos correctos
chmod +x "$PYTHON_FILE"
chown -R root:root /opt/fleximodo/src/
chown -R root:root "$LOG_DIR"

log_info "Permisos configurados correctamente"

log_step "8. Iniciando servicio..."

# Habilitar e iniciar el servicio
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Esperar un momento para que el servicio inicie
sleep 3

# Verificar estado del servicio
if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "✅ Servicio iniciado correctamente"
else
    log_error "❌ Error iniciando el servicio"
    systemctl status $SERVICE_NAME
    exit 1
fi

log_step "9. Verificando funcionalidad..."

# Test de conectividad al servicio
sleep 2
if curl -s -f "http://localhost:$PORT/health" > /dev/null; then
    log_info "✅ Servicio responde correctamente en puerto $PORT"
    
    # Mostrar información del endpoint de salud
    echo
    log_info "Información del servicio:"
    curl -s "http://localhost:$PORT/health" | python3 -m json.tool
    
else
    log_warning "⚠️  Servicio no responde en puerto $PORT"
    log_info "Verificando logs..."
    journalctl -u $SERVICE_NAME --no-pager -n 10
fi

log_step "10. Configuración de firewall..."

# Abrir puerto en firewall si ufw está activo
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    log_info "Configurando reglas de firewall..."
    ufw allow $PORT/tcp comment "Parking Sensor Push Service"
    log_info "Puerto $PORT abierto en firewall"
else
    log_info "UFW no está activo o no está instalado"
fi

echo
log_info "=== DESPLIEGUE COMPLETADO ==="
echo
echo "📡 Servicio: $SERVICE_NAME"
echo "🔌 Puerto: $PORT"
echo "📁 Logs: $LOG_DIR/sensor_push_service.log"
echo "🔧 Estado: $(systemctl is-active $SERVICE_NAME)"
echo
echo "📋 COMANDOS ÚTILES:"
echo "  • Ver estado: systemctl status $SERVICE_NAME"
echo "  • Ver logs: journalctl -u $SERVICE_NAME -f"
echo "  • Reiniciar: systemctl restart $SERVICE_NAME"
echo "  • Detener: systemctl stop $SERVICE_NAME"
echo
echo "🌐 ENDPOINTS DISPONIBLES:"
echo "  • Health Check: http://localhost:$PORT/health"
echo "  • Push Sensor: http://localhost:$PORT/push"
echo "  • Manual Update: http://localhost:$PORT/manual-update"
echo "  • Estadísticas: http://localhost:$PORT/stats"
echo
echo "🔗 INTEGRACIÓN:"
echo "  • Configurar sensores Fleximodo para enviar push a:"
echo "    http://157.180.91.63:$PORT/push"
echo
echo "✅ DESPLIEGUE EXITOSO"
