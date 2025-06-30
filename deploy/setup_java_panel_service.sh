#!/bin/bash

# Script de instalación inicial del servicio Java de paneles
# Uso: ./setup_java_panel_service.sh

set -e  # Salir si hay algún error

echo "🔧 INSTALANDO SERVICIO JAVA DE PANELES"
echo "======================================"

# Variables
SERVICE_NAME="java-panel-service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
INSTALL_DIR="/opt/java-panel-service"
PROJECT_DIR="/opt/parking_altea"

echo "📁 Directorio de instalación: $INSTALL_DIR"
echo "📁 Directorio del proyecto: $PROJECT_DIR"

# 1. Crear directorio de instalación
echo ""
echo "1️⃣ Creando directorio de instalación..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/logs

# 2. Copiar archivo de servicio systemd
echo ""
echo "2️⃣ Instalando archivo de servicio systemd..."
cp $PROJECT_DIR/deploy/java-panel-service.service $SERVICE_FILE

# 3. Recargar systemd
echo ""
echo "3️⃣ Recargando configuración de systemd..."
systemctl daemon-reload

# 4. Habilitar el servicio
echo ""
echo "4️⃣ Habilitando servicio..."
systemctl enable $SERVICE_NAME

# 5. Verificar que el archivo JAR existe
echo ""
echo "5️⃣ Verificando archivo JAR..."
JAR_PATH="$PROJECT_DIR/panel_java/protocol-1.2.6.jar"
if [ ! -f "$JAR_PATH" ]; then
    echo "❌ Error: No se encontró el archivo JAR en $JAR_PATH"
    exit 1
fi
echo "✅ Archivo JAR encontrado: $JAR_PATH"

# 6. Compilar el proyecto
echo ""
echo "6️⃣ Compilando proyecto..."
cd $PROJECT_DIR/server/java-panel-service
mvn clean package -DskipTests

if [ $? -ne 0 ]; then
    echo "❌ Error: La compilación falló"
    exit 1
fi

# 7. Copiar el JAR
echo ""
echo "7️⃣ Copiando archivo JAR..."
JAR_FILE="$PROJECT_DIR/server/java-panel-service/target/java-panel-service-1.0.0.jar"
cp $JAR_FILE $INSTALL_DIR/

# 8. Configurar permisos
echo ""
echo "8️⃣ Configurando permisos..."
chown -R root:root $INSTALL_DIR
chmod 755 $INSTALL_DIR
chmod 644 $INSTALL_DIR/*.jar

# 9. Iniciar el servicio
echo ""
echo "9️⃣ Iniciando servicio..."
systemctl start $SERVICE_NAME
sleep 5

# 10. Verificar estado
echo ""
echo "🔟 Verificando estado del servicio..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Servicio $SERVICE_NAME está corriendo correctamente"
else
    echo "❌ Error: El servicio $SERVICE_NAME no se pudo iniciar"
    systemctl status $SERVICE_NAME
    exit 1
fi

# 11. Mostrar información del servicio
echo ""
echo "1️⃣1️⃣ Información del servicio:"
echo "📊 Estado:"
systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo "📋 Comandos útiles:"
echo "  - Ver logs: journalctl -u $SERVICE_NAME -f"
echo "  - Reiniciar: systemctl restart $SERVICE_NAME"
echo "  - Detener: systemctl stop $SERVICE_NAME"
echo "  - Habilitar: systemctl enable $SERVICE_NAME"
echo "  - Deshabilitar: systemctl disable $SERVICE_NAME"

echo ""
echo "🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo "========================================"
echo "✅ Directorio creado: $INSTALL_DIR"
echo "✅ Servicio systemd instalado: $SERVICE_FILE"
echo "✅ Servicio habilitado y corriendo"
echo "✅ Archivo JAR copiado"
echo "✅ Permisos configurados" 