#!/bin/bash

# Script de despliegue completo para Java Panel Service v2.5
# Este script compila, instala y configura el servicio

set -e

echo "=========================================="
echo "Desplegando Java Panel Service v2.5"
echo "=========================================="

# Variables
PROJECT_DIR="/opt/parking_altea"
SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="java-panel-service"
SERVICE_USER="parking"
SERVICE_GROUP="parking"
JAR_NAME="java-panel-service-1.0.0.jar"
TARGET_DIR="$SERVICE_DIR/target"
INSTALL_DIR="/opt/java-panel-service"
SERVICE_FILE="/etc/systemd/system/java-panel-service.service"
LIBRARY_JAR="$PROJECT_DIR/panel_java/protocol-1.2.6.jar"

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

# Verificar que estamos ejecutando como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root"
    exit 1
fi

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

# Verificar que Maven está instalado
if ! command -v mvn &> /dev/null; then
    print_error "Maven no está instalado. Instalando..."
    apt update
    apt install -y maven
fi

# Verificar que Java está instalado
if ! command -v java &> /dev/null; then
    print_error "Java no está instalado. Instalando..."
    apt update
    apt install -y openjdk-11-jdk
fi

print_status "Versiones de las herramientas:"
java -version
mvn -version

# Detener el servicio si está ejecutándose
print_status "Deteniendo el servicio si está ejecutándose..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

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

# Crear directorio de instalación
print_status "Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR"

# Copiar archivos necesarios
print_status "Copiando archivos..."
cp "$TARGET_DIR/$JAR_NAME" "$INSTALL_DIR/"
cp "$LIBRARY_JAR" "$INSTALL_DIR/"
cp "$SERVICE_DIR/src/main/resources/application.yml" "$INSTALL_DIR/"

# Crear usuario del servicio si no existe
if ! id "$SERVICE_USER" &>/dev/null; then
    print_status "Creando usuario del servicio: $SERVICE_USER"
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
fi

# Asignar permisos
print_status "Asignando permisos..."
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR"/*.jar
chmod 644 "$INSTALL_DIR"/*.yml

# Crear archivo de servicio systemd
print_status "Creando archivo de servicio systemd..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Java Panel Service v2.5
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/java -jar -Dspring.config.location=file:application.yml $JAR_NAME
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Configuración de memoria y rendimiento
Environment="JAVA_OPTS=-Xms256m -Xmx512m -XX:+UseG1GC"

# Configuración de seguridad
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
print_status "Recargando configuración de systemd..."
systemctl daemon-reload

# Habilitar el servicio
print_status "Habilitando el servicio..."
systemctl enable "$SERVICE_NAME"

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
echo "Health Check: http://localhost:5002/api/health"

# Mostrar logs recientes
print_status "Logs recientes del servicio:"
journalctl -u "$SERVICE_NAME" --no-pager -n 10

echo "=========================================="
print_status "Despliegue completado exitosamente"
echo "=========================================="
echo "Servicio: $SERVICE_NAME"
echo "Directorio: $INSTALL_DIR"
echo "JAR: $INSTALL_DIR/$JAR_NAME"
echo "Configuración: $INSTALL_DIR/application.yml"
echo ""
echo "Comandos útiles:"
echo "  Ver estado: systemctl status $SERVICE_NAME"
echo "  Ver logs: journalctl -u $SERVICE_NAME -f"
echo "  Reiniciar: systemctl restart $SERVICE_NAME"
echo "  Detener: systemctl stop $SERVICE_NAME" 