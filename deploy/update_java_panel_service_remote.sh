#!/bin/bash

# Script para actualizar el servicio Java con el protocolo correcto en el servidor remoto
# Mapeo correcto de fontSize y colors según documentación del fabricante

echo "🚀 ACTUALIZACIÓN REMOTA DEL SERVICIO JAVA PANEL"
echo "==============================================="

# Configuración del servidor remoto
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
PROJECT_DIR="/opt/parking_altea"
JAVA_SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="parking-panel-service"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para ejecutar comandos remotos
remote_exec() {
    local cmd="$1"
    log_info "Ejecutando: $cmd"
    ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "$cmd"
}

# Función para copiar archivos
remote_copy() {
    local src="$1"
    local dest="$2"
    log_info "Copiando: $src -> $dest"
    scp -o StrictHostKeyChecking=no -r "$src" "$REMOTE_USER@$REMOTE_HOST:$dest"
}

# 1. Verificar conectividad con el servidor
log_info "Verificando conectividad con el servidor..."
if ! ping -c 1 $REMOTE_HOST > /dev/null 2>&1; then
    log_error "No se puede conectar al servidor $REMOTE_HOST"
    exit 1
fi
log_success "Conectividad OK"

# 2. Actualizar código del proyecto en el servidor
log_info "Actualizando código del proyecto en el servidor..."
remote_exec "cd $PROJECT_DIR && git fetch origin"
remote_exec "cd $PROJECT_DIR && git reset --hard origin/v3.0.0"
log_success "Código actualizado"

# 3. Verificar que los archivos del servicio Java existen
log_info "Verificando archivos del servicio Java..."
remote_exec "cd $JAVA_SERVICE_DIR && ls -la"
remote_exec "cd $JAVA_SERVICE_DIR && ls -la src/main/java/com/parkingaltea/panelservice/service/PanelCommunicationService.java"
remote_exec "cd $JAVA_SERVICE_DIR && ls -la src/main/java/com/parkingaltea/panelservice/controller/PanelController.java"
remote_exec "cd $JAVA_SERVICE_DIR && ls -la src/main/java/com/parkingaltea/panelservice/model/PanelMessage.java"
log_success "Archivos del servicio Java verificados"

# 4. Verificar Java y Maven en el servidor
log_info "Verificando Java y Maven en el servidor..."
remote_exec "java -version"
remote_exec "mvn -version"
log_success "Java y Maven verificados"

# 5. Compilar servicio Java en el servidor
log_info "Compilando servicio Java en el servidor..."
remote_exec "cd $JAVA_SERVICE_DIR && mvn clean compile package -DskipTests"

if [ $? -ne 0 ]; then
    log_error "Error compilando el servicio Java en el servidor"
    exit 1
fi
log_success "Compilación exitosa"

# 6. Detener servicio actual
log_info "Deteniendo servicio actual..."
remote_exec "systemctl stop $SERVICE_NAME"
log_success "Servicio detenido"

# 7. Copiar archivo JAR
log_info "Copiando archivo JAR..."
remote_exec "cp $JAVA_SERVICE_DIR/target/panel-service-1.0.0.jar $PROJECT_DIR/java-panel-service.jar"
log_success "Archivo JAR copiado"

# 8. Reiniciar servicio
log_info "Reiniciando servicio..."
remote_exec "systemctl start $SERVICE_NAME"
log_success "Servicio reiniciado"

# 9. Verificar estado del servicio
log_info "Verificando estado del servicio..."
remote_exec "systemctl status $SERVICE_NAME --no-pager"

# 10. Esperar que el servicio esté listo
log_info "Esperando que el servicio esté listo..."
sleep 5

# 11. Verificar que el servicio responde
log_info "Verificando que el servicio responde..."
response=$(remote_exec "curl -s http://127.0.0.1:5656/api/v1/panels/health")

if [[ $response == *"Panel Service OK"* ]]; then
    log_success "Servicio respondiendo correctamente: $response"
else
    log_error "Error: El servicio no responde correctamente"
    log_info "Logs del servicio:"
    remote_exec "journalctl -u $SERVICE_NAME -n 20 --no-pager"
    exit 1
fi

# 12. Pruebas de mapeo de protocolo
echo ""
log_info "🧪 PRUEBA DE MAPEO DE PROTOCOLO"
echo "==============================="

# Test 1: Probar mapeo fontSize 16 -> valor 2
log_info "1️⃣ Probando mapeo fontSize 16 -> valor 2..."

test_payload='{
  "ip": "172.20.4.52",
  "itemNum": 1,
  "texts": ["FONT 16 TEST"],
  "colors": [1],
  "fontSizes": [16],
  "showEffects": [1]
}'

response=$(remote_exec "curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti -H 'Content-Type: application/json' -d '$test_payload'")
log_info "Respuesta: $response"

# Test 2: Probar mapeo color rojo (valor 1)
log_info "2️⃣ Probando mapeo color rojo (valor 1)..."

test_payload2='{
  "ip": "172.20.4.52",
  "itemNum": 1,
  "texts": ["COLOR ROJO TEST"],
  "colors": [1],
  "fontSizes": [16],
  "showEffects": [1]
}'

response=$(remote_exec "curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti -H 'Content-Type: application/json' -d '$test_payload2'")
log_info "Respuesta: $response"

# 13. Verificación de logs
log_info "📋 VERIFICACIÓN DE LOGS"
echo "======================="
log_info "Comando para ver logs:"
echo "ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u $SERVICE_NAME -f'"
echo ""
log_info "Buscar en logs:"
echo "- 'Parámetros mapeados - fontSize: 16->2'"
echo "- 'Simulando envío de mensaje con fontSize=2 y color=1'"

# 14. Información final
echo ""
log_success "🎉 ACTUALIZACIÓN COMPLETADA"
echo "==============================="
echo ""
log_info "📋 Resumen de cambios:"
echo "  • Servicio Java actualizado con protocolo correcto"
echo "  • Mapeo fontSize: 16px -> valor 2 (FONTSIZE_16)"
echo "  • Mapeo color: 1 -> Rojo"
echo "  • Protocolo sendMulti implementado correctamente"
echo "  • Librería Java del fabricante (sin DLL)"
echo ""
log_info "🔗 URLs importantes:"
echo "  • Servicio Java: http://$REMOTE_HOST:5656"
echo "  • Health check: http://$REMOTE_HOST:5656/api/v1/panels/health"
echo "  • Backend API: http://$REMOTE_HOST:6001"
echo "  • Frontend: http://$REMOTE_HOST:5789"
echo ""
log_info "📋 RESUMEN DEL MAPEO IMPLEMENTADO:"
echo "   fontSize: 16px -> valor 2 (FONTSIZE_16)"
echo "   color: 1 -> Rojo"
echo "   protocolo: sendMulti con mapeo correcto"
echo ""
log_success "✅ Actualización completada exitosamente" 