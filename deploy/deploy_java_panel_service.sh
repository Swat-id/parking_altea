#!/bin/bash

# Script para desplegar el servicio Java de paneles como servicio systemd
# Autor: Parking Altea Team
# Versión: 2.5

set -e

echo "🚀 DESPLEGANDO SERVICIO JAVA DE PANELES v2.5"
echo "============================================="

# Configuración
PROJECT_DIR="/opt/parking_altea"
SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
TARGET_DIR="$SERVICE_DIR/target"
JAR_NAME="java-panel-service-1.0.0.jar"
SERVICE_NAME="java-panel-service"
SERVICE_USER="parking"
SERVICE_GROUP="parking"
INSTALL_DIR="/opt/parking_altea/java-panel-service"
LOG_DIR="/var/log/parking_altea"

# Verificar que somos root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Este script debe ejecutarse como root"
    echo "   Usa: sudo $0"
    exit 1
fi

# Verificar que el JAR existe
if [ ! -f "$TARGET_DIR/$JAR_NAME" ]; then
    echo "❌ Error: No se encontró el JAR compilado"
    echo "   Ejecuta primero: ./deploy/build_java_panel_service.sh"
    exit 1
fi

echo "✅ JAR verificado: $TARGET_DIR/$JAR_NAME"

# Crear directorio de instalación
echo "📁 Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"

# Crear usuario del servicio si no existe
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "👤 Creando usuario $SERVICE_USER..."
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
fi

# Copiar archivos
echo "📋 Copiando archivos..."
cp "$TARGET_DIR/$JAR_NAME" "$INSTALL_DIR/"
cp "$SERVICE_DIR/src/main/resources/application.yml" "$INSTALL_DIR/"
cp -r "$SERVICE_DIR/lib" "$INSTALL_DIR/"

# Crear directorio de logs
mkdir -p "$LOG_DIR"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"

# Configurar permisos
echo "🔐 Configurando permisos..."
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR/$JAR_NAME"
chmod 644 "$INSTALL_DIR/application.yml"
chmod -R 644 "$INSTALL_DIR/lib/"

# Crear archivo de servicio systemd
echo "⚙️  Creando servicio systemd..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Java Panel Service v2.5
Documentation=https://github.com/parking-altea/java-panel-service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/java -jar $INSTALL_DIR/$JAR_NAME
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Configuración de seguridad
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR

# Configuración de recursos
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
echo "🔄 Recargando systemd..."
systemctl daemon-reload

# Habilitar y iniciar el servicio
echo "🚀 Habilitando e iniciando servicio..."
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# Verificar estado
echo "🔍 Verificando estado del servicio..."
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Servicio iniciado correctamente"
else
    echo "❌ Error: El servicio no se inició correctamente"
    echo "📋 Logs del servicio:"
    journalctl -u "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi

# Mostrar información del servicio
echo ""
echo "📋 INFORMACIÓN DEL SERVICIO:"
echo "============================"
echo "🔧 Servicio: $SERVICE_NAME"
echo "📁 Directorio: $INSTALL_DIR"
echo "📦 JAR: $INSTALL_DIR/$JAR_NAME"
echo "📝 Logs: $LOG_DIR"
echo "👤 Usuario: $SERVICE_USER"
echo "🌐 Puerto: 5656"
echo ""

echo "🔧 COMANDOS ÚTILES:"
echo "==================="
echo "📊 Estado: systemctl status $SERVICE_NAME"
echo "📋 Logs: journalctl -u $SERVICE_NAME -f"
echo "🔄 Reiniciar: systemctl restart $SERVICE_NAME"
echo "⏹️  Detener: systemctl stop $SERVICE_NAME"
echo "🧪 Health Check: curl http://localhost:5656/api/health"
echo ""

echo "✅ DESPLIEGUE COMPLETADO EXITOSAMENTE"
echo "=====================================" 