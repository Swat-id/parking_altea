#!/bin/bash

# Script de construcción y despliegue del servicio Java de paneles LED
# Parking Altea - Java Panel Service

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SERVICE_NAME="java-panel-service"
SERVICE_DIR="server/java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
TARGET_DIR="target"
LOG_DIR="logs"
SERVICE_PORT=5002

# Función de logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Función para verificar prerrequisitos
check_prerequisites() {
    log "Verificando prerrequisitos..."
    
    # Verificar Java
    if ! command -v java &> /dev/null; then
        error "Java no está instalado"
        exit 1
    fi
    
    java_version=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$java_version" -lt 11 ]; then
        error "Se requiere Java 11 o superior. Versión actual: $java_version"
        exit 1
    fi
    
    success "Java $java_version encontrado"
    
    # Verificar Maven
    if ! command -v mvn &> /dev/null; then
        error "Maven no está instalado"
        exit 1
    fi
    
    mvn_version=$(mvn -version 2>&1 | head -n 1 | cut -d' ' -f3)
    success "Maven $mvn_version encontrado"
    
    # Verificar directorio del servicio
    if [ ! -d "$SERVICE_DIR" ]; then
        error "Directorio del servicio no encontrado: $SERVICE_DIR"
        exit 1
    fi
    
    # Verificar librería Java del fabricante
    if [ ! -f "../panel_java/protocol-1.2.6.jar" ]; then
        warning "Librería Java del fabricante no encontrada: ../panel_java/protocol-1.2.6.jar"
        warning "El servicio funcionará en modo simulación"
    else
        success "Librería Java del fabricante encontrada"
    fi
}

# Función para limpiar
clean() {
    log "Limpiando proyecto..."
    cd "$SERVICE_DIR"
    mvn clean
    success "Proyecto limpiado"
}

# Función para compilar
compile() {
    log "Compilando proyecto..."
    cd "$SERVICE_DIR"
    
    # Compilar sin ejecutar tests
    mvn compile -DskipTests
    
    if [ $? -eq 0 ]; then
        success "Proyecto compilado exitosamente"
    else
        error "Error al compilar el proyecto"
        exit 1
    fi
}

# Función para ejecutar tests
test() {
    log "Ejecutando tests..."
    cd "$SERVICE_DIR"
    
    mvn test
    
    if [ $? -eq 0 ]; then
        success "Tests ejecutados exitosamente"
    else
        error "Algunos tests fallaron"
        exit 1
    fi
}

# Función para empaquetar
package() {
    log "Empaquetando aplicación..."
    cd "$SERVICE_DIR"
    
    # Crear JAR ejecutable
    mvn package -DskipTests
    
    if [ $? -eq 0 ]; then
        success "Aplicación empaquetada exitosamente"
        
        # Verificar que el JAR se creó
        if [ -f "$TARGET_DIR/$JAR_NAME" ]; then
            jar_size=$(du -h "$TARGET_DIR/$JAR_NAME" | cut -f1)
            success "JAR creado: $TARGET_DIR/$JAR_NAME ($jar_size)"
        else
            error "JAR no encontrado después de la compilación"
            exit 1
        fi
    else
        error "Error al empaquetar la aplicación"
        exit 1
    fi
}

# Función para crear directorios necesarios
create_directories() {
    log "Creando directorios necesarios..."
    
    # Crear directorio de logs
    mkdir -p "$LOG_DIR"
    success "Directorio de logs creado: $LOG_DIR"
    
    # Crear directorio de configuración
    mkdir -p "config"
    success "Directorio de configuración creado: config"
}

# Función para copiar archivos de configuración
copy_config() {
    log "Copiando archivos de configuración..."
    
    # Copiar JAR
    if [ -f "$SERVICE_DIR/$TARGET_DIR/$JAR_NAME" ]; then
        cp "$SERVICE_DIR/$TARGET_DIR/$JAR_NAME" .
        success "JAR copiado: $JAR_NAME"
    fi
    
    # Copiar librería del fabricante si existe
    if [ -f "../panel_java/protocol-1.2.6.jar" ]; then
        cp "../panel_java/protocol-1.2.6.jar" .
        success "Librería del fabricante copiada"
    fi
}

# Función para crear script de inicio
create_startup_script() {
    log "Creando script de inicio..."
    
    cat > "start_java_panel_service.sh" << 'EOF'
#!/bin/bash

# Script de inicio para el servicio Java de paneles LED
# Parking Altea

SERVICE_NAME="java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
LOG_FILE="logs/panel-service.log"
PID_FILE="java-panel-service.pid"

# Configuración JVM
JVM_OPTS="-Xms512m -Xmx1024m -XX:+UseG1GC"
JAVA_OPTS="-Dspring.profiles.active=production -Dserver.port=5002"

# Función de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Verificar si el servicio ya está ejecutándose
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "El servicio ya está ejecutándose con PID: $PID"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Iniciar servicio
log "Iniciando servicio Java de paneles..."
nohup java $JVM_OPTS $JAVA_OPTS -jar "$JAR_NAME" > "$LOG_FILE" 2>&1 &
PID=$!

# Guardar PID
echo $PID > "$PID_FILE"

log "Servicio iniciado con PID: $PID"
log "Logs disponibles en: $LOG_FILE"
log "Para detener el servicio: ./stop_java_panel_service.sh"

echo "Servicio Java de paneles iniciado exitosamente"
echo "PID: $PID"
echo "Logs: $LOG_FILE"
EOF

    chmod +x "start_java_panel_service.sh"
    success "Script de inicio creado: start_java_panel_service.sh"
}

# Función para crear script de parada
create_stop_script() {
    log "Creando script de parada..."
    
    cat > "stop_java_panel_service.sh" << 'EOF'
#!/bin/bash

# Script de parada para el servicio Java de paneles LED
# Parking Altea

SERVICE_NAME="java-panel-service"
PID_FILE="java-panel-service.pid"
LOG_FILE="logs/panel-service.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

if [ ! -f "$PID_FILE" ]; then
    echo "Archivo PID no encontrado. El servicio no parece estar ejecutándose."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Proceso con PID $PID no encontrado. Limpiando archivo PID."
    rm -f "$PID_FILE"
    exit 1
fi

log "Deteniendo servicio Java de paneles (PID: $PID)..."
kill "$PID"

# Esperar a que el proceso termine
for i in {1..30}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Verificar si el proceso terminó
if ps -p "$PID" > /dev/null 2>&1; then
    log "El proceso no terminó. Forzando terminación..."
    kill -9 "$PID"
fi

rm -f "$PID_FILE"
log "Servicio Java de paneles detenido"

echo "Servicio Java de paneles detenido exitosamente"
EOF

    chmod +x "stop_java_panel_service.sh"
    success "Script de parada creado: stop_java_panel_service.sh"
}

# Función para crear archivo de configuración de producción
create_production_config() {
    log "Creando configuración de producción..."
    
    cat > "application-production.yml" << 'EOF'
server:
  port: 5002
  servlet:
    context-path: /api

spring:
  application:
    name: java-panel-service
  
  jackson:
    default-property-inclusion: non_null
    serialization:
      write-dates-as-timestamps: false
    deserialization:
      fail-on-unknown-properties: false

# Configuración del servicio de paneles para producción
panel:
  service:
    library:
      jar-path: "./protocol-1.2.6.jar"
      timeout: 5000
      retry-attempts: 3
      retry-delay: 2000
    
    default:
      port: 5200
      card-id: 1
      window-no: 0
      font-size: 16
      speed: 3
      effect: 0
      stay-time: 5
      alignment: 5
      screen-width: 64
      screen-height: 32
    
    colors:
      red: 0x0000FF
      green: 0x00FF00
      blue: 0xFF0000
      yellow: 0x00FFFF
      orange: 0x0080FF
      white: 0xFFFFFF
      default: 3000

# Configuración de logging para producción
logging:
  level:
    com.parkingaltea.panelservice: INFO
    org.springframework.web: WARN
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
    file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: logs/panel-service.log
    max-size: 50MB
    max-history: 30

# Configuración de actuator para producción
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: when-authorized
  metrics:
    export:
      prometheus:
        enabled: true
EOF

    success "Configuración de producción creada: application-production.yml"
}

# Función para verificar el servicio
check_service() {
    log "Verificando servicio..."
    
    # Esperar un momento para que el servicio se inicie
    sleep 5
    
    # Verificar si el puerto está en uso
    if netstat -tuln 2>/dev/null | grep -q ":$SERVICE_PORT "; then
        success "Servicio escuchando en puerto $SERVICE_PORT"
    else
        warning "Servicio no parece estar escuchando en puerto $SERVICE_PORT"
    fi
    
    # Verificar health check
    if command -v curl &> /dev/null; then
        if curl -s "http://localhost:$SERVICE_PORT/api/panel/health" > /dev/null; then
            success "Health check exitoso"
        else
            warning "Health check falló"
        fi
    fi
}

# Función para mostrar información del servicio
show_info() {
    log "Información del servicio Java de paneles:"
    echo "  - Nombre: $SERVICE_NAME"
    echo "  - Puerto: $SERVICE_PORT"
    echo "  - JAR: $JAR_NAME"
    echo "  - Logs: $LOG_DIR/panel-service.log"
    echo ""
    echo "Comandos disponibles:"
    echo "  ./start_java_panel_service.sh  - Iniciar servicio"
    echo "  ./stop_java_panel_service.sh   - Detener servicio"
    echo "  tail -f $LOG_DIR/panel-service.log  - Ver logs en tiempo real"
    echo ""
    echo "Endpoints disponibles:"
    echo "  http://localhost:$SERVICE_PORT/api/panel/health"
    echo "  http://localhost:$SERVICE_PORT/api/panel/status"
    echo "  http://localhost:$SERVICE_PORT/api/panel/colors"
}

# Función principal
main() {
    echo "=========================================="
    echo "  Parking Altea - Java Panel Service"
    echo "  Script de construcción y despliegue"
    echo "=========================================="
    echo ""
    
    # Verificar argumentos
    if [ "$1" = "clean" ]; then
        clean
        exit 0
    elif [ "$1" = "compile" ]; then
        check_prerequisites
        clean
        compile
        exit 0
    elif [ "$1" = "test" ]; then
        check_prerequisites
        test
        exit 0
    elif [ "$1" = "package" ]; then
        check_prerequisites
        clean
        compile
        package
        exit 0
    elif [ "$1" = "deploy" ]; then
        check_prerequisites
        clean
        compile
        package
        create_directories
        copy_config
        create_startup_script
        create_stop_script
        create_production_config
        show_info
        success "Despliegue completado exitosamente"
        exit 0
    elif [ "$1" = "info" ]; then
        show_info
        exit 0
    else
        echo "Uso: $0 {clean|compile|test|package|deploy|info}"
        echo ""
        echo "Comandos:"
        echo "  clean    - Limpiar proyecto"
        echo "  compile  - Compilar proyecto"
        echo "  test     - Ejecutar tests"
        echo "  package  - Empaquetar aplicación"
        echo "  deploy   - Desplegar servicio completo"
        echo "  info     - Mostrar información del servicio"
        echo ""
        echo "Ejemplo: $0 deploy"
        exit 1
    fi
}

# Ejecutar función principal
main "$@" 