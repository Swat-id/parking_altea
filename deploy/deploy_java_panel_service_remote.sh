#!/bin/bash

# Script de despliegue del servicio Java de paneles LED en servidor remoto
# Parking Altea - Java Panel Service

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración del servidor remoto
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_DIR="/opt/parking_altea"
SERVICE_NAME="java-panel-service"
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

# Función para verificar conectividad con servidor remoto
check_remote_connectivity() {
    log "Verificando conectividad con servidor remoto..."
    
    if ! ping -c 1 "$REMOTE_HOST" > /dev/null 2>&1; then
        error "No se puede conectar al servidor remoto: $REMOTE_HOST"
        return 1
    fi
    
    success "Conectividad con servidor remoto verificada"
    return 0
}

# Función para verificar prerrequisitos en servidor remoto
check_remote_prerequisites() {
    log "Verificando prerrequisitos en servidor remoto..."
    
    # Verificar Java
    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "java -version" > /dev/null 2>&1; then
        error "Java no está instalado en el servidor remoto"
        return 1
    fi
    
    # Verificar Maven
    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "mvn -version" > /dev/null 2>&1; then
        error "Maven no está instalado en el servidor remoto"
        return 1
    fi
    
    # Verificar directorio de destino
    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "test -d $REMOTE_DIR"; then
        log "Creando directorio de destino en servidor remoto..."
        ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"
    fi
    
    success "Prerrequisitos en servidor remoto verificados"
    return 0
}

# Función para subir código al servidor remoto
upload_code_to_remote() {
    log "Subiendo código al servidor remoto..."
    
    # Crear archivo tar con el código
    tar_file="java_panel_service_deploy.tar.gz"
    
    log "Creando archivo de despliegue..."
    tar -czf "$tar_file" \
        --exclude='*.git*' \
        --exclude='target' \
        --exclude='*.log' \
        --exclude='*.pid' \
        server/java-panel-service/ \
        panel_java/ \
        deploy/ \
        test/ \
        docs/
    
    # Subir archivo al servidor remoto
    log "Subiendo archivo al servidor remoto..."
    scp "$tar_file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
    
    # Extraer archivo en servidor remoto
    log "Extrayendo archivo en servidor remoto..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && tar -xzf $tar_file"
    
    # Limpiar archivo temporal
    rm -f "$tar_file"
    
    success "Código subido al servidor remoto exitosamente"
    return 0
}

# Función para compilar en servidor remoto
compile_on_remote() {
    log "Compilando servicio en servidor remoto..."
    
    ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR/server/java-panel-service && mvn clean package -DskipTests"
    
    if [ $? -eq 0 ]; then
        success "Servicio compilado exitosamente en servidor remoto"
    else
        error "Error al compilar el servicio en servidor remoto"
        return 1
    fi
    
    return 0
}

# Función para crear scripts de gestión en servidor remoto
create_management_scripts_on_remote() {
    log "Creando scripts de gestión en servidor remoto..."
    
    # Script de inicio
    ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/start_java_panel_service.sh" << 'EOF'
#!/bin/bash

# Script de inicio para el servicio Java de paneles LED
# Parking Altea - Servidor Remoto

SERVICE_NAME="java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
LOG_FILE="logs/panel-service.log"
PID_FILE="java-panel-service.pid"
REMOTE_DIR="/opt/parking_altea"

# Configuración JVM para servidor remoto
JVM_OPTS="-Xms1g -Xmx2g -XX:+UseG1GC -XX:+UseStringDeduplication"
JAVA_OPTS="-Dspring.profiles.active=production -Dserver.port=5002"

# Función de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Cambiar al directorio del servicio
cd "$REMOTE_DIR"

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
log "Iniciando servicio Java de paneles en servidor remoto..."
nohup java $JVM_OPTS $JAVA_OPTS -jar "server/java-panel-service/target/$JAR_NAME" > "$LOG_FILE" 2>&1 &
PID=$!

# Guardar PID
echo $PID > "$PID_FILE"

log "Servicio iniciado con PID: $PID"
log "Logs disponibles en: $LOG_FILE"
log "Para detener el servicio: ./stop_java_panel_service.sh"

echo "Servicio Java de paneles iniciado exitosamente en servidor remoto"
echo "PID: $PID"
echo "Logs: $LOG_FILE"
EOF

    # Script de parada
    ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/stop_java_panel_service.sh" << 'EOF'
#!/bin/bash

# Script de parada para el servicio Java de paneles LED
# Parking Altea - Servidor Remoto

SERVICE_NAME="java-panel-service"
PID_FILE="java-panel-service.pid"
LOG_FILE="logs/panel-service.log"
REMOTE_DIR="/opt/parking_altea"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$REMOTE_DIR"

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

    # Script de estado
    ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/status_java_panel_service.sh" << 'EOF'
#!/bin/bash

# Script de estado para el servicio Java de paneles LED
# Parking Altea - Servidor Remoto

SERVICE_NAME="java-panel-service"
PID_FILE="java-panel-service.pid"
LOG_FILE="logs/panel-service.log"
REMOTE_DIR="/opt/parking_altea"

cd "$REMOTE_DIR"

echo "=========================================="
echo "  Estado del Servicio Java de Paneles"
echo "=========================================="
echo ""

# Verificar proceso
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Servicio ejecutándose (PID: $PID)"
        echo "   Memoria: $(ps -o rss= -p $PID | awk '{print $1/1024 " MB"}')"
        echo "   CPU: $(ps -o %cpu= -p $PID)%"
    else
        echo "❌ Servicio no ejecutándose (PID obsoleto: $PID)"
    fi
else
    echo "❌ Servicio no ejecutándose (archivo PID no encontrado)"
fi

echo ""

# Verificar puerto
if netstat -tuln 2>/dev/null | grep -q ":5002 "; then
    echo "✅ Puerto 5002 en uso"
else
    echo "❌ Puerto 5002 no en uso"
fi

echo ""

# Verificar logs
if [ -f "$LOG_FILE" ]; then
    echo "📋 Logs disponibles: $LOG_FILE"
    echo "   Tamaño: $(du -h "$LOG_FILE" | cut -f1)"
    echo "   Última modificación: $(stat -c %y "$LOG_FILE")"
else
    echo "❌ Archivo de logs no encontrado"
fi

echo ""

# Verificar health check
if command -v curl > /dev/null 2>&1; then
    if curl -s "http://localhost:5002/api/panel/health" > /dev/null 2>&1; then
        echo "✅ Health check exitoso"
    else
        echo "❌ Health check falló"
    fi
else
    echo "⚠️  curl no disponible para health check"
fi

echo ""
echo "=========================================="
EOF

    # Dar permisos de ejecución
    ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_DIR/start_java_panel_service.sh"
    ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_DIR/stop_java_panel_service.sh"
    ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_DIR/status_java_panel_service.sh"
    
    success "Scripts de gestión creados en servidor remoto"
    return 0
}

# Función para crear configuración de producción en servidor remoto
create_production_config_on_remote() {
    log "Creando configuración de producción en servidor remoto..."
    
    ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/application-production.yml" << 'EOF'
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
      jar-path: "./panel_java/protocol-1.2.6.jar"
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

    success "Configuración de producción creada en servidor remoto"
    return 0
}

# Función para verificar despliegue
verify_deployment() {
    log "Verificando despliegue en servidor remoto..."
    
    # Esperar un momento para que el servicio se inicie
    sleep 10
    
    # Verificar si el proceso está ejecutándose
    if ssh "$REMOTE_USER@$REMOTE_HOST" "test -f $REMOTE_DIR/java-panel-service.pid"; then
        PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cat $REMOTE_DIR/java-panel-service.pid")
        if ssh "$REMOTE_USER@$REMOTE_HOST" "ps -p $PID > /dev/null 2>&1"; then
            success "Servicio ejecutándose en servidor remoto (PID: $PID)"
        else
            error "Servicio no está ejecutándose en servidor remoto"
            return 1
        fi
    else
        error "Archivo PID no encontrado en servidor remoto"
        return 1
    fi
    
    # Verificar puerto
    if ssh "$REMOTE_USER@$REMOTE_HOST" "netstat -tuln 2>/dev/null | grep -q ':5002 '"; then
        success "Puerto 5002 en uso en servidor remoto"
    else
        warning "Puerto 5002 no parece estar en uso en servidor remoto"
    fi
    
    # Verificar health check
    if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -s http://localhost:5002/api/panel/health > /dev/null 2>&1"; then
        success "Health check exitoso en servidor remoto"
    else
        warning "Health check falló en servidor remoto"
    fi
    
    return 0
}

# Función para mostrar información del despliegue
show_deployment_info() {
    log "Información del despliegue en servidor remoto:"
    echo "  - Servidor: $REMOTE_HOST"
    echo "  - Usuario: $REMOTE_USER"
    echo "  - Directorio: $REMOTE_DIR"
    echo "  - Puerto: $SERVICE_PORT"
    echo "  - Servicio: $SERVICE_NAME"
    echo ""
    echo "Comandos disponibles en servidor remoto:"
    echo "  ./start_java_panel_service.sh  - Iniciar servicio"
    echo "  ./stop_java_panel_service.sh   - Detener servicio"
    echo "  ./status_java_panel_service.sh - Ver estado"
    echo ""
    echo "Endpoints disponibles:"
    echo "  http://$REMOTE_HOST:$SERVICE_PORT/api/panel/health"
    echo "  http://$REMOTE_HOST:$SERVICE_PORT/api/panel/status"
    echo "  http://$REMOTE_HOST:$SERVICE_PORT/api/panel/colors"
    echo ""
    echo "Logs del servicio:"
    echo "  tail -f $REMOTE_DIR/logs/panel-service.log"
}

# Función principal de despliegue
main() {
    echo "=========================================="
    echo "  Parking Altea - Java Panel Service"
    echo "  Despliegue en Servidor Remoto"
    echo "=========================================="
    echo ""
    
    # Verificar argumentos
    if [ "$1" = "verify" ]; then
        check_remote_connectivity
        check_remote_prerequisites
        show_deployment_info
        exit 0
    elif [ "$1" = "deploy" ]; then
        # Ejecutar despliegue completo
        check_remote_connectivity || exit 1
        check_remote_prerequisites || exit 1
        upload_code_to_remote || exit 1
        compile_on_remote || exit 1
        create_management_scripts_on_remote || exit 1
        create_production_config_on_remote || exit 1
        
        echo ""
        success "Despliegue completado exitosamente"
        echo ""
        echo "Para iniciar el servicio en el servidor remoto:"
        echo "ssh $REMOTE_USER@$REMOTE_HOST"
        echo "cd $REMOTE_DIR"
        echo "./start_java_panel_service.sh"
        echo ""
        echo "Para verificar el estado:"
        echo "./status_java_panel_service.sh"
        echo ""
        echo "Para ver logs:"
        echo "tail -f logs/panel-service.log"
        
        exit 0
    else
        echo "Uso: $0 {verify|deploy}"
        echo ""
        echo "Comandos:"
        echo "  verify  - Verificar conectividad y prerrequisitos"
        echo "  deploy  - Desplegar servicio completo"
        echo ""
        echo "Ejemplo: $0 deploy"
        exit 1
    fi
}

# Ejecutar función principal
main "$@" 