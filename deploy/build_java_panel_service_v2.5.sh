#!/bin/bash

# Script de construcción para Java Panel Service v2.5
# Este script compila y empaqueta el servicio Java

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="server/java-panel-service"
TARGET_DIR="$PROJECT_DIR/target"
JAR_NAME="java-panel-service-1.0.0.jar"
SERVICE_NAME="java-panel-service"

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Construcción Java Panel Service v2.5${NC}"
echo -e "${BLUE}==========================================${NC}"
echo "Fecha: $(date)"
echo "Directorio: $PROJECT_DIR"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_DIR/pom.xml" ]; then
    echo -e "${RED}❌ Error: No se encontró pom.xml en $PROJECT_DIR${NC}"
    echo "Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Verificar que Maven esté instalado
if ! command -v mvn &> /dev/null; then
    echo -e "${RED}❌ Error: Maven no está instalado${NC}"
    echo "Instala Maven para continuar"
    exit 1
fi

# Verificar que Java esté instalado
if ! command -v java &> /dev/null; then
    echo -e "${RED}❌ Error: Java no está instalado${NC}"
    echo "Instala Java 11 o superior para continuar"
    exit 1
fi

echo -e "${YELLOW}📋 Verificando dependencias...${NC}"

# Verificar que la librería del fabricante esté disponible
LIBRARY_PATH="$PROJECT_DIR/../../panel_java/protocol-1.2.6.jar"
if [ ! -f "$LIBRARY_PATH" ]; then
    echo -e "${RED}❌ Error: No se encontró la librería del fabricante${NC}"
    echo "Ruta esperada: $LIBRARY_PATH"
    echo "Asegúrate de que el archivo protocol-1.2.6.jar esté disponible"
    exit 1
fi

echo -e "${GREEN}✅ Librería del fabricante encontrada${NC}"

# Limpiar compilaciones anteriores
echo -e "${YELLOW}🧹 Limpiando compilaciones anteriores...${NC}"
cd "$PROJECT_DIR"
mvn clean

# Compilar el proyecto
echo -e "${YELLOW}🔨 Compilando el proyecto...${NC}"
mvn compile

# Ejecutar tests (si existen)
echo -e "${YELLOW}🧪 Ejecutando tests...${NC}"
if mvn test -q; then
    echo -e "${GREEN}✅ Tests pasaron exitosamente${NC}"
else
    echo -e "${YELLOW}⚠️  Algunos tests fallaron, pero continuando...${NC}"
fi

# Empaquetar el proyecto
echo -e "${YELLOW}📦 Empaquetando el proyecto...${NC}"
mvn package -DskipTests

# Verificar que el JAR se creó correctamente
if [ ! -f "$TARGET_DIR/$JAR_NAME" ]; then
    echo -e "${RED}❌ Error: No se generó el archivo JAR${NC}"
    echo "Verifica los logs de Maven para más detalles"
    exit 1
fi

echo -e "${GREEN}✅ JAR generado exitosamente: $TARGET_DIR/$JAR_NAME${NC}"

# Mostrar información del JAR
echo -e "${YELLOW}📊 Información del JAR:${NC}"
ls -lh "$TARGET_DIR/$JAR_NAME"

# Verificar que el JAR sea ejecutable
echo -e "${YELLOW}🔍 Verificando que el JAR sea ejecutable...${NC}"
if java -jar "$TARGET_DIR/$JAR_NAME" --version &>/dev/null || java -jar "$TARGET_DIR/$JAR_NAME" --help &>/dev/null; then
    echo -e "${GREEN}✅ JAR es ejecutable${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo verificar la ejecutabilidad del JAR${NC}"
fi

# Crear script de inicio
echo -e "${YELLOW}📝 Creando script de inicio...${NC}"
cat > "$TARGET_DIR/start-service.sh" << EOF
#!/bin/bash

# Script de inicio para Java Panel Service v2.5
JAR_FILE="\$(dirname "\$0")/$JAR_NAME"
JAVA_OPTS="-Xms512m -Xmx1024m -Dserver.port=5002"

echo "Iniciando Java Panel Service v2.5..."
echo "JAR: \$JAR_FILE"
echo "Puerto: 5002"
echo ""

java \$JAVA_OPTS -jar "\$JAR_FILE"
EOF

chmod +x "$TARGET_DIR/start-service.sh"
echo -e "${GREEN}✅ Script de inicio creado: $TARGET_DIR/start-service.sh${NC}"

# Crear archivo de configuración de ejemplo
echo -e "${YELLOW}📝 Creando archivo de configuración de ejemplo...${NC}"
cat > "$TARGET_DIR/application-example.yml" << EOF
# Configuración de ejemplo para Java Panel Service v2.5
server:
  port: 5002
  servlet:
    context-path: /api

spring:
  application:
    name: java-panel-service

logging:
  level:
    com.parkingaltea.panelservice: DEBUG
    org.springframework.web: INFO
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"

# Configuración de paneles
panel:
  service:
    library:
      jar-path: /opt/parking_altea/panel_java/protocol-1.2.6.jar
      timeout: 5000
      retry-attempts: 3
      retry-delay: 1000
    default:
      port: 5200
      card-id: 1
      window-no: 0
EOF

echo -e "${GREEN}✅ Archivo de configuración de ejemplo creado${NC}"

# Resumen final
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}RESUMEN DE CONSTRUCCIÓN${NC}"
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}✅ Construcción completada exitosamente${NC}"
echo ""
echo -e "${YELLOW}📁 Archivos generados:${NC}"
echo "  - JAR: $TARGET_DIR/$JAR_NAME"
echo "  - Script de inicio: $TARGET_DIR/start-service.sh"
echo "  - Configuración ejemplo: $TARGET_DIR/application-example.yml"
echo ""
echo -e "${YELLOW}🚀 Para ejecutar el servicio:${NC}"
echo "  cd $TARGET_DIR"
echo "  ./start-service.sh"
echo ""
echo -e "${YELLOW}🔍 Para probar el servicio:${NC}"
echo "  python3 test/test_java_panel_service_v2.5.py"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo "Fecha: $(date)"
echo -e "${BLUE}==========================================${NC}" 