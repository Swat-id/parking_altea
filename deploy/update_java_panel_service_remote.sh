#!/bin/bash

# Script para actualizar y recompilar el Java Panel Service en el servidor remoto
# Uso: ./update_java_panel_service_remote.sh

set -e

echo "=== Actualizando Java Panel Service en servidor remoto ==="

# Variables
PROJECT_DIR="/opt/parking_altea"
JAVA_SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="java-panel-service"
JAR_NAME="panel-service-1.0.0.jar"

echo "1. Navegando al directorio del proyecto..."
cd $PROJECT_DIR

echo "2. Actualizando código desde Git..."
git fetch origin
git checkout java-panel-service
git pull origin java-panel-service

echo "3. Navegando al directorio del servicio Java..."
cd $JAVA_SERVICE_DIR

echo "4. Limpiando compilación anterior..."
mvn clean

echo "5. Compilando el proyecto..."
mvn compile

echo "6. Creando JAR ejecutable..."
mvn package -DskipTests

echo "7. Verificando que el JAR se creó correctamente..."
if [ ! -f "target/$JAR_NAME" ]; then
    echo "ERROR: No se pudo crear el JAR ejecutable"
    exit 1
fi

echo "8. Deteniendo el servicio si está ejecutándose..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Deteniendo servicio $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
    sleep 2
fi

echo "9. Copiando el nuevo JAR..."
cp target/$JAR_NAME /opt/$JAR_NAME

echo "10. Reiniciando el servicio..."
systemctl start $SERVICE_NAME

echo "11. Verificando estado del servicio..."
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Servicio $SERVICE_NAME iniciado correctamente"
else
    echo "❌ ERROR: El servicio no se pudo iniciar"
    systemctl status $SERVICE_NAME
    exit 1
fi

echo "12. Verificando logs del servicio..."
echo "Últimas líneas del log:"
journalctl -u $SERVICE_NAME --no-pager -n 10

echo "13. Probando endpoints..."
echo "Health check:"
curl -s http://localhost:5002/api/panel/health | jq .

echo "Status de paneles:"
curl -s http://localhost:5002/api/panel/status | jq .

echo "Colores disponibles:"
curl -s http://localhost:5002/api/panel/colors | jq .

echo ""
echo "=== Actualización completada ==="
echo "✅ Java Panel Service actualizado y funcionando"
echo "📍 Puerto: 5002"
echo "🔗 Health: http://localhost:5002/api/panel/health"
echo "📊 Status: http://localhost:5002/api/panel/status" 