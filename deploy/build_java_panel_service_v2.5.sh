#!/bin/bash

# Script de compilación para Java Panel Service v2.5
# Este script compila el proyecto Java y crea el JAR ejecutable

set -e

echo "=========================================="
echo "Compilando Java Panel Service v2.5"
echo "=========================================="

# Variables
PROJECT_DIR="/opt/parking_altea/server/java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
TARGET_DIR="$PROJECT_DIR/target"
LIBRARY_JAR="/opt/parking_altea/panel_java/protocol-1.2.6.jar"

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_DIR/pom.xml" ]; then
    echo "Error: No se encontró pom.xml en $PROJECT_DIR"
    exit 1
fi

# Verificar que existe la librería del fabricante
if [ ! -f "$LIBRARY_JAR" ]; then
    echo "Error: No se encontró la librería del fabricante en $LIBRARY_JAR"
    exit 1
fi

# Verificar que Maven está instalado
if ! command -v mvn &> /dev/null; then
    echo "Error: Maven no está instalado"
    exit 1
fi

# Verificar que Java está instalado
if ! command -v java &> /dev/null; then
    echo "Error: Java no está instalado"
    exit 1
fi

echo "Java version:"
java -version

echo "Maven version:"
mvn -version

# Limpiar compilaciones anteriores
echo "Limpiando compilaciones anteriores..."
cd "$PROJECT_DIR"
mvn clean

# Compilar el proyecto
echo "Compilando el proyecto..."
mvn compile

# Ejecutar tests (opcional)
echo "Ejecutando tests..."
mvn test

# Crear el JAR ejecutable
echo "Creando JAR ejecutable..."
mvn package -DskipTests

# Verificar que el JAR se creó correctamente
if [ ! -f "$TARGET_DIR/$JAR_NAME" ]; then
    echo "Error: No se pudo crear el JAR en $TARGET_DIR/$JAR_NAME"
    exit 1
fi

echo "JAR creado exitosamente: $TARGET_DIR/$JAR_NAME"
echo "Tamaño del JAR: $(du -h "$TARGET_DIR/$JAR_NAME" | cut -f1)"

# Verificar que el JAR es ejecutable
echo "Verificando que el JAR es ejecutable..."
java -jar "$TARGET_DIR/$JAR_NAME" --version 2>/dev/null || echo "JAR creado pero no ejecutable (normal para Spring Boot)"

echo "=========================================="
echo "Compilación completada exitosamente"
echo "=========================================="
echo "JAR ubicado en: $TARGET_DIR/$JAR_NAME"
echo "Para ejecutar: java -jar $TARGET_DIR/$JAR_NAME" 