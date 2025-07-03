#!/bin/bash

# Script para compilar el servicio Java de paneles
# Autor: Parking Altea Team
# Versión: 2.5

set -e

echo "🔨 COMPILANDO SERVICIO JAVA DE PANELES v2.5"
echo "=============================================="

# Configuración
PROJECT_DIR="/opt/parking_altea/server/java-panel-service"
TARGET_DIR="$PROJECT_DIR/target"
JAR_NAME="java-panel-service-1.0.0.jar"
SERVICE_NAME="java-panel-service"

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_DIR/pom.xml" ]; then
    echo "❌ Error: No se encontró pom.xml en $PROJECT_DIR"
    echo "   Asegúrate de estar en el directorio correcto del proyecto"
    exit 1
fi

# Verificar que Java está instalado
if ! command -v java &> /dev/null; then
    echo "❌ Error: Java no está instalado"
    exit 1
fi

# Verificar que Maven está instalado
if ! command -v mvn &> /dev/null; then
    echo "❌ Error: Maven no está instalado"
    exit 1
fi

echo "✅ Java y Maven verificados"

# Verificar que la librería del fabricante existe
if [ ! -f "$PROJECT_DIR/lib/protocol-1.2.6.jar" ]; then
    echo "❌ Error: No se encontró la librería protocol-1.2.6.jar"
    echo "   Verifica que el archivo existe en $PROJECT_DIR/lib/"
    exit 1
fi

echo "✅ Librería del fabricante verificada"

# Limpiar compilación anterior
echo "🧹 Limpiando compilación anterior..."
cd "$PROJECT_DIR"
mvn clean

# Compilar el proyecto
echo "🔨 Compilando proyecto..."
mvn package -DskipTests

# Verificar que el JAR se creó correctamente
if [ ! -f "$TARGET_DIR/$JAR_NAME" ]; then
    echo "❌ Error: No se generó el archivo JAR"
    echo "   Verifica los errores de compilación"
    exit 1
fi

echo "✅ Compilación completada exitosamente"
echo "📦 JAR generado: $TARGET_DIR/$JAR_NAME"

# Mostrar información del JAR
echo ""
echo "📋 INFORMACIÓN DEL JAR:"
echo "======================="
ls -lh "$TARGET_DIR/$JAR_NAME"
echo ""

# Verificar dependencias incluidas
echo "🔍 Verificando dependencias..."
jar -tf "$TARGET_DIR/$JAR_NAME" | grep -E "(protocol|CP5200)" || echo "⚠️  No se encontraron clases de la librería del fabricante"

echo ""
echo "✅ COMPILACIÓN COMPLETADA"
echo "========================="
echo "📁 JAR: $TARGET_DIR/$JAR_NAME"
echo "🚀 Para ejecutar: java -jar $TARGET_DIR/$JAR_NAME"
echo "🔧 Para instalar como servicio: sudo ./deploy/deploy_java_panel_service.sh" 