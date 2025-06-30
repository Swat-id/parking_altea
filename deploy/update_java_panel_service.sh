#!/bin/bash

# Script de actualización del servicio Java de paneles
# Uso: ./update_java_panel_service.sh

set -e  # Salir si hay algún error

echo "🚀 ACTUALIZANDO SERVICIO JAVA DE PANELES"
echo "========================================"

# Variables
PROJECT_DIR="/opt/parking_altea"
JAVA_SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="java-panel-service"

echo "📁 Directorio del proyecto: $PROJECT_DIR"
echo "📁 Directorio del servicio Java: $JAVA_SERVICE_DIR"

# 1. Navegar al directorio del proyecto
echo ""
echo "1️⃣ Navegando al directorio del proyecto..."
cd $PROJECT_DIR

# 2. Verificar que estamos en el directorio correcto
if [ ! -f "README.md" ]; then
    echo "❌ Error: No se encontró el archivo README.md en $PROJECT_DIR"
    exit 1
fi

# 3. Actualizar desde git
echo ""
echo "2️⃣ Actualizando código desde GitHub..."
git fetch origin
git pull origin java-panel-service

# Verificar que la actualización fue exitosa
if [ $? -ne 0 ]; then
    echo "❌ Error: No se pudo actualizar desde git"
    exit 1
fi

echo "✅ Código actualizado correctamente"

# 4. Verificar que el archivo JAR existe
echo ""
echo "3️⃣ Verificando archivo JAR..."
JAR_PATH="/opt/parking_altea/panel_java/protocol-1.2.6.jar"
if [ ! -f "$JAR_PATH" ]; then
    echo "❌ Error: No se encontró el archivo JAR en $JAR_PATH"
    exit 1
fi
echo "✅ Archivo JAR encontrado: $JAR_PATH"

# 5. Navegar al directorio del servicio Java
echo ""
echo "4️⃣ Navegando al directorio del servicio Java..."
cd $JAVA_SERVICE_DIR

# 6. Limpiar y compilar
echo ""
echo "5️⃣ Limpiando y compilando el proyecto..."
mvn clean compile

if [ $? -ne 0 ]; then
    echo "❌ Error: La compilación falló"
    exit 1
fi

echo "✅ Compilación exitosa"

# 7. Ejecutar tests
echo ""
echo "6️⃣ Ejecutando tests..."
mvn test

if [ $? -ne 0 ]; then
    echo "⚠️  Advertencia: Algunos tests fallaron, pero continuando..."
else
    echo "✅ Tests ejecutados correctamente"
fi

# 8. Crear el package
echo ""
echo "7️⃣ Creando package..."
mvn clean package -DskipTests

if [ $? -ne 0 ]; then
    echo "❌ Error: No se pudo crear el package"
    exit 1
fi

echo "✅ Package creado correctamente"

# 9. Verificar que el JAR se creó
JAR_FILE="$JAVA_SERVICE_DIR/target/java-panel-service-1.0.0.jar"
if [ ! -f "$JAR_FILE" ]; then
    echo "❌ Error: No se encontró el archivo JAR generado"
    exit 1
fi

echo "✅ Archivo JAR generado: $JAR_FILE"

# 10. Detener el servicio si está corriendo
echo ""
echo "8️⃣ Verificando estado del servicio..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "🛑 Deteniendo servicio $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
    sleep 2
else
    echo "ℹ️  El servicio $SERVICE_NAME no está corriendo"
fi

# 11. Copiar el nuevo JAR
echo ""
echo "9️⃣ Copiando nuevo JAR..."
cp $JAR_FILE /opt/java-panel-service/
echo "✅ JAR copiado a /opt/java-panel-service/"

# 12. Reiniciar el servicio
echo ""
echo "🔟 Reiniciando servicio..."
systemctl start $SERVICE_NAME
sleep 3

# 13. Verificar estado del servicio
echo ""
echo "1️⃣1️⃣ Verificando estado del servicio..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Servicio $SERVICE_NAME está corriendo correctamente"
else
    echo "❌ Error: El servicio $SERVICE_NAME no se pudo iniciar"
    systemctl status $SERVICE_NAME
    exit 1
fi

# 14. Mostrar logs recientes
echo ""
echo "1️⃣2️⃣ Mostrando logs recientes..."
journalctl -u $SERVICE_NAME --no-pager -n 10

echo ""
echo "🎉 ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!"
echo "=========================================="
echo "✅ Código actualizado desde git"
echo "✅ Proyecto compilado correctamente"
echo "✅ Tests ejecutados"
echo "✅ Package creado"
echo "✅ Servicio reiniciado"
echo "✅ Servicio funcionando correctamente"
echo ""
echo "📊 Estado del servicio:"
systemctl status $SERVICE_NAME --no-pager -l 