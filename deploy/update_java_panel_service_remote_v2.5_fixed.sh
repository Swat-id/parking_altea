#!/bin/bash

# Script de actualización remota para Java Panel Service v2.5
# Este script actualiza el servicio en el servidor remoto

set -e

echo "=========================================="
echo "Actualizando Java Panel Service v2.5 en servidor remoto"
echo "=========================================="

# Variables
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_PROJECT_DIR="/opt/parking_altea"
REMOTE_SERVICE_DIR="$REMOTE_PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
REMOTE_INSTALL_DIR="/opt/java-panel-service"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar conectividad con el servidor remoto
print_status "Verificando conectividad con $REMOTE_HOST..."
if ! ping -c 1 "$REMOTE_HOST" &> /dev/null; then
    print_error "No se puede conectar con $REMOTE_HOST"
    exit 1
fi

# Verificar que SSH funciona
print_status "Verificando acceso SSH..."
if ! ssh -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH OK'" &> /dev/null; then
    print_error "No se puede acceder por SSH a $REMOTE_HOST"
    exit 1
fi

# Crear script de actualización remoto
print_status "Creando script de actualización remoto..."
cat > /tmp/update_java_panel_service_remote.sh << 'EOF'
#!/bin/bash

# Script de actualización para Java Panel Service v2.5 (ejecutar en servidor remoto)
set -e

echo "=========================================="
echo "Actualizando Java Panel Service v2.5"
echo "=========================================="

# Variables
PROJECT_DIR="/opt/parking_altea"
SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
TARGET_DIR="$SERVICE_DIR/target"
INSTALL_DIR="/opt/java-panel-service"
LIBRARY_JAR="$PROJECT_DIR/panel_java/protocol-1.2.6.jar"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que el directorio del proyecto existe
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "No se encontró el directorio del proyecto: $PROJECT_DIR"
    exit 1
fi

# Verificar que existe la librería del fabricante
if [ ! -f "$LIBRARY_JAR" ]; then
    print_error "No se encontró la librería del fabricante: $LIBRARY_JAR"
    exit 1
fi

# Detener el servicio
print_status "Deteniendo el servicio..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Hacer backup del JAR actual
if [ -f "$INSTALL_DIR/$JAR_NAME" ]; then
    print_status "Creando backup del JAR actual..."
    cp "$INSTALL_DIR/$JAR_NAME" "$INSTALL_DIR/${JAR_NAME}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Compilar el proyecto
print_status "Compilando el proyecto Java..."
cd "$SERVICE_DIR"

# Limpiar compilaciones anteriores
mvn clean

# Compilar y crear JAR
mvn package -DskipTests

# Verificar que el JAR se creó correctamente
if [ ! -f "$TARGET_DIR/$JAR_NAME" ]; then
    print_error "No se pudo crear el JAR"
    exit 1
fi

print_status "JAR creado exitosamente: $TARGET_DIR/$JAR_NAME"

# Copiar archivos actualizados
print_status "Copiando archivos actualizados..."
cp "$TARGET_DIR/$JAR_NAME" "$INSTALL_DIR/"
cp "$SERVICE_DIR/src/main/resources/application.yml" "$INSTALL_DIR/"

# Asignar permisos
print_status "Asignando permisos..."
chown parking:parking "$INSTALL_DIR"/*.jar 2>/dev/null || chown root:root "$INSTALL_DIR"/*.jar
chown parking:parking "$INSTALL_DIR"/*.yml 2>/dev/null || chown root:root "$INSTALL_DIR"/*.yml
chmod 644 "$INSTALL_DIR"/*.jar
chmod 644 "$INSTALL_DIR"/*.yml

# Recargar systemd
print_status "Recargando configuración de systemd..."
systemctl daemon-reload

# Iniciar el servicio
print_status "Iniciando el servicio..."
systemctl start "$SERVICE_NAME"

# Verificar que el servicio está ejecutándose
sleep 5
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_status "Servicio iniciado correctamente"
else
    print_error "Error al iniciar el servicio"
    systemctl status "$SERVICE_NAME"
    exit 1
fi

# Verificar que el puerto está abierto
print_status "Verificando que el puerto 5002 está abierto..."
if netstat -tlnp | grep :5002; then
    print_status "Puerto 5002 abierto correctamente"
else
    print_warning "Puerto 5002 no está abierto. Verificando logs..."
    journalctl -u "$SERVICE_NAME" --no-pager -n 20
fi

# Mostrar información del servicio
print_status "Información del servicio:"
echo "Estado: $(systemctl is-active $SERVICE_NAME)"
echo "Habilitado: $(systemctl is-enabled $SERVICE_NAME)"
echo "Puerto: 5002"
echo "API Base: http://localhost:5002/api"

# Mostrar logs recientes
print_status "Logs recientes del servicio:"
journalctl -u "$SERVICE_NAME" --no-pager -n 10

echo "=========================================="
print_status "Actualización completada exitosamente"
echo "=========================================="
EOF

# Copiar script al servidor remoto
print_status "Copiando script de actualización al servidor remoto..."
scp /tmp/update_java_panel_service_remote.sh "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Ejecutar script en el servidor remoto
print_status "Ejecutando actualización en el servidor remoto..."
ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x /tmp/update_java_panel_service_remote.sh && /tmp/update_java_panel_service_remote.sh"

# Limpiar archivo temporal
rm -f /tmp/update_java_panel_service_remote.sh

# Verificar estado final
print_status "Verificando estado final del servicio..."
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl status $SERVICE_NAME --no-pager"

echo "=========================================="
print_status "Actualización remota completada exitosamente"
echo "=========================================="
echo "Servidor: $REMOTE_HOST"
echo "Servicio: $SERVICE_NAME"
echo "API Base: http://$REMOTE_HOST:5002/api"
echo "Health Check: http://$REMOTE_HOST:5002/api/health"
EOF 