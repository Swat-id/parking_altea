#!/bin/bash

# Script de actualización para Java Panel Service v2.5 en servidor remoto
# Este script actualiza el servicio en el servidor de producción

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración del servidor
REMOTE_HOST="parking.altea.es"
REMOTE_USER="root"
REMOTE_DIR="/opt/parking_altea"
SERVICE_NAME="java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Actualización Java Panel Service v2.5${NC}"
echo -e "${BLUE}==========================================${NC}"
echo "Servidor: $REMOTE_HOST"
echo "Usuario: $REMOTE_USER"
echo "Directorio: $REMOTE_DIR"
echo "Fecha: $(date)"
echo ""

# Verificar conectividad con el servidor
echo -e "${YELLOW}🔍 Verificando conectividad con el servidor...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" "echo 'Conexión exitosa'" 2>/dev/null; then
    echo -e "${RED}❌ Error: No se puede conectar al servidor $REMOTE_HOST${NC}"
    echo "Verifica la conectividad y las credenciales SSH"
    exit 1
fi

echo -e "${GREEN}✅ Conectividad verificada${NC}"

# Verificar que el directorio del proyecto existe
echo -e "${YELLOW}📁 Verificando directorio del proyecto...${NC}"
if ! ssh "$REMOTE_USER@$REMOTE_HOST" "[ -d '$REMOTE_DIR' ]"; then
    echo -e "${RED}❌ Error: El directorio $REMOTE_DIR no existe en el servidor${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Directorio del proyecto encontrado${NC}"

# Hacer backup del JAR actual
echo -e "${YELLOW}💾 Creando backup del JAR actual...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR/server/java-panel-service/target && \
    if [ -f '$JAR_NAME' ]; then \
        cp '$JAR_NAME' '${JAR_NAME}.backup.$(date +%Y%m%d_%H%M%S)'; \
        echo 'Backup creado'; \
    else \
        echo 'No hay JAR para hacer backup'; \
    fi"

# Detener el servicio si está ejecutándose
echo -e "${YELLOW}🛑 Deteniendo el servicio actual...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl stop $SERVICE_NAME 2>/dev/null || echo 'Servicio no estaba ejecutándose'"

# Actualizar el código desde git
echo -e "${YELLOW}📥 Actualizando código desde git...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && \
    git fetch origin && \
    git checkout v2.5_no_login_paneles && \
    git pull origin v2.5_no_login_paneles"

# Verificar que la librería del fabricante esté disponible
echo -e "${YELLOW}📋 Verificando librería del fabricante...${NC}"
if ! ssh "$REMOTE_USER@$REMOTE_HOST" "[ -f '$REMOTE_DIR/panel_java/protocol-1.2.6.jar' ]"; then
    echo -e "${RED}❌ Error: No se encontró la librería del fabricante${NC}"
    echo "Ruta esperada: $REMOTE_DIR/panel_java/protocol-1.2.6.jar"
    exit 1
fi

echo -e "${GREEN}✅ Librería del fabricante encontrada${NC}"

# Compilar el proyecto
echo -e "${YELLOW}🔨 Compilando el proyecto...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR/server/java-panel-service && \
    mvn clean package -DskipTests"

# Verificar que el JAR se generó correctamente
echo -e "${YELLOW}🔍 Verificando JAR generado...${NC}"
if ! ssh "$REMOTE_USER@$REMOTE_HOST" "[ -f '$REMOTE_DIR/server/java-panel-service/target/$JAR_NAME' ]"; then
    echo -e "${RED}❌ Error: No se generó el JAR después de la compilación${NC}"
    exit 1
fi

echo -e "${GREEN}✅ JAR generado correctamente${NC}"

# Crear script de inicio si no existe
echo -e "${YELLOW}📝 Creando script de inicio...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/server/java-panel-service/target/start-service.sh << 'EOF'
#!/bin/bash

# Script de inicio para Java Panel Service v2.5
JAR_FILE=\"\$(dirname \"\$0\")/$JAR_NAME\"
JAVA_OPTS=\"-Xms512m -Xmx1024m -Dserver.port=5002\"

echo \"Iniciando Java Panel Service v2.5...\"
echo \"JAR: \$JAR_FILE\"
echo \"Puerto: 5002\"
echo \"\"

java \$JAVA_OPTS -jar \"\$JAR_FILE\"
EOF"

ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_DIR/server/java-panel-service/target/start-service.sh"

# Actualizar el servicio systemd
echo -e "${YELLOW}⚙️  Actualizando servicio systemd...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
[Unit]
Description=Java Panel Service v2.5
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REMOTE_DIR/server/java-panel-service/target
ExecStart=$REMOTE_DIR/server/java-panel-service/target/start-service.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

# Recargar systemd y habilitar el servicio
echo -e "${YELLOW}🔄 Recargando systemd...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl daemon-reload && \
    systemctl enable $SERVICE_NAME"

# Iniciar el servicio
echo -e "${YELLOW}🚀 Iniciando el servicio...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl start $SERVICE_NAME"

# Esperar un momento para que el servicio se inicie
echo -e "${YELLOW}⏳ Esperando que el servicio se inicie...${NC}"
sleep 5

# Verificar el estado del servicio
echo -e "${YELLOW}🔍 Verificando estado del servicio...${NC}"
if ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl is-active --quiet $SERVICE_NAME"; then
    echo -e "${GREEN}✅ Servicio iniciado correctamente${NC}"
else
    echo -e "${RED}❌ Error: El servicio no se inició correctamente${NC}"
    echo "Verificando logs..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "journalctl -u $SERVICE_NAME -n 20 --no-pager"
    exit 1
fi

# Probar el servicio
echo -e "${YELLOW}🧪 Probando el servicio...${NC}"
if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -s http://localhost:5002/api/panels/health | grep -q 'success'"; then
    echo -e "${GREEN}✅ Health check del servicio exitoso${NC}"
else
    echo -e "${YELLOW}⚠️  Health check falló, pero el servicio está ejecutándose${NC}"
fi

# Mostrar información del servicio
echo -e "${YELLOW}📊 Información del servicio:${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl status $SERVICE_NAME --no-pager -l"

# Resumen final
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}RESUMEN DE ACTUALIZACIÓN${NC}"
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}✅ Actualización completada exitosamente${NC}"
echo ""
echo -e "${YELLOW}📁 Archivos actualizados:${NC}"
echo "  - JAR: $REMOTE_DIR/server/java-panel-service/target/$JAR_NAME"
echo "  - Script de inicio: $REMOTE_DIR/server/java-panel-service/target/start-service.sh"
echo "  - Servicio systemd: /etc/systemd/system/$SERVICE_NAME.service"
echo ""
echo -e "${YELLOW}🔍 Comandos útiles:${NC}"
echo "  - Estado del servicio: systemctl status $SERVICE_NAME"
echo "  - Logs del servicio: journalctl -u $SERVICE_NAME -f"
echo "  - Reiniciar servicio: systemctl restart $SERVICE_NAME"
echo "  - Detener servicio: systemctl stop $SERVICE_NAME"
echo ""
echo -e "${YELLOW}🌐 URLs del servicio:${NC}"
echo "  - Health Check: http://$REMOTE_HOST:5002/api/panels/health"
echo "  - Lista de paneles: http://$REMOTE_HOST:5002/api/panels/list"
echo "  - Estado de paneles: http://$REMOTE_HOST:5002/api/panels/status"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo "Fecha: $(date)"
echo -e "${BLUE}==========================================${NC}" 