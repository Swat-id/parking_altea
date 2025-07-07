#!/bin/bash

# Script de Configuración del Servidor v3.1.0 - Parking Altea
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

set -e

# Configuración
REMOTE_HOST="157.180.91.63"
REMOTE_USER="root"
REMOTE_PASSWORD="Sudv9uvSvdu!"
REMOTE_DIR="/opt/parking_altea"
VENV_DIR="/opt/parking_altea/venv"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para ejecutar comandos remotos
remote_exec() {
    sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$1"
}

# Función para copiar archivos
remote_copy() {
    sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$REMOTE_USER@$REMOTE_HOST:$2"
}

# Actualizar sistema
update_system() {
    log "Actualizando sistema..."
    remote_exec "apt-get update && apt-get upgrade -y"
    success "Sistema actualizado"
}

# Instalar dependencias del sistema
install_system_dependencies() {
    log "Instalando dependencias del sistema..."
    
    remote_exec "apt-get install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib nodejs npm git curl wget unzip"
    
    # Instalar Node.js 18 si no está disponible
    remote_exec "curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs"
    
    success "Dependencias del sistema instaladas"
}

# Configurar PostgreSQL
setup_postgresql() {
    log "Configurando PostgreSQL..."
    
    # Crear usuario y base de datos
    remote_exec "sudo -u postgres psql -c \"CREATE USER parking WITH PASSWORD 'parking123';\" || true"
    remote_exec "sudo -u postgres psql -c \"CREATE DATABASE parking_altea OWNER parking;\" || true"
    remote_exec "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE parking_altea TO parking;\" || true"
    
    # Configurar autenticación
    remote_exec "echo 'local parking_altea parking md5' >> /etc/postgresql/*/main/pg_hba.conf"
    remote_exec "systemctl restart postgresql"
    
    success "PostgreSQL configurado"
}

# Crear usuario del sistema
create_system_user() {
    log "Creando usuario del sistema..."
    
    remote_exec "useradd -m -s /bin/bash parking || true"
    remote_exec "usermod -aG sudo parking"
    remote_exec "echo 'parking:parking123' | chpasswd"
    
    success "Usuario del sistema creado"
}

# Configurar directorios
setup_directories() {
    log "Configurando directorios..."
    
    remote_exec "mkdir -p $REMOTE_DIR"
    remote_exec "mkdir -p $REMOTE_DIR/logs"
    remote_exec "mkdir -p $REMOTE_DIR/data"
    remote_exec "mkdir -p $REMOTE_DIR/static"
    remote_exec "mkdir -p $REMOTE_DIR/backups"
    remote_exec "mkdir -p /opt/backups/parking_altea"
    
    # Cambiar propietario
    remote_exec "chown -R parking:parking $REMOTE_DIR"
    remote_exec "chown -R parking:parking /opt/backups/parking_altea"
    
    success "Directorios configurados"
}

# Configurar entorno virtual Python
setup_python_venv() {
    log "Configurando entorno virtual Python..."
    
    remote_exec "cd $REMOTE_DIR && python3 -m venv venv"
    remote_exec "chown -R parking:parking $VENV_DIR"
    
    success "Entorno virtual Python configurado"
}

# Configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    # Crear configuración de Nginx
    cat > /tmp/parking_altea_nginx.conf << 'EOF'
server {
    listen 80;
    server_name 157.180.91.63;
    
    # Frontend
    location / {
        root /opt/parking_altea/static;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
    }
    
    # Logs
    access_log /var/log/nginx/parking_altea_access.log;
    error_log /var/log/nginx/parking_altea_error.log;
}
EOF
    
    remote_copy "/tmp/parking_altea_nginx.conf" "/etc/nginx/sites-available/parking_altea"
    remote_exec "ln -sf /etc/nginx/sites-available/parking_altea /etc/nginx/sites-enabled/"
    remote_exec "rm -f /etc/nginx/sites-enabled/default"
    remote_exec "nginx -t && systemctl restart nginx"
    
    success "Nginx configurado"
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    remote_exec "ufw allow 22/tcp"
    remote_exec "ufw allow 80/tcp"
    remote_exec "ufw allow 443/tcp"
    remote_exec "ufw --force enable"
    
    success "Firewall configurado"
}

# Configurar logs
setup_logs() {
    log "Configurando sistema de logs..."
    
    # Crear configuración de logrotate
    cat > /tmp/parking_altea_logrotate << 'EOF'
/opt/parking_altea/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 parking parking
    postrotate
        systemctl reload parking-api.service
        systemctl reload parking-camera.service
        systemctl reload parking-schedule-monitor.service
    endscript
}
EOF
    
    remote_copy "/tmp/parking_altea_logrotate" "/etc/logrotate.d/parking_altea"
    
    success "Sistema de logs configurado"
}

# Configurar monitoreo
setup_monitoring() {
    log "Configurando monitoreo..."
    
    # Instalar herramientas de monitoreo básicas
    remote_exec "apt-get install -y htop iotop nethogs"
    
    # Crear script de monitoreo
    cat > /tmp/monitor_parking.sh << 'EOF'
#!/bin/bash
echo "=== Parking Altea System Status ==="
echo "Date: $(date)"
echo ""
echo "Services:"
systemctl is-active parking-api.service
systemctl is-active parking-camera.service
systemctl is-active parking-schedule-monitor.service
echo ""
echo "Disk Usage:"
df -h /opt/parking_altea
echo ""
echo "Memory Usage:"
free -h
echo ""
echo "Processes:"
ps aux | grep parking | grep -v grep
EOF
    
    remote_copy "/tmp/monitor_parking.sh" "/usr/local/bin/"
    remote_exec "chmod +x /usr/local/bin/monitor_parking.sh"
    
    success "Monitoreo configurado"
}

# Función principal
main() {
    echo "🔧 Configuración del Servidor v3.1.0 - Parking Altea"
    echo "=================================================="
    
    read -p "¿Continuar con la configuración del servidor? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Configuración cancelada"
        exit 0
    fi
    
    # Ejecutar pasos de configuración
    update_system
    install_system_dependencies
    setup_postgresql
    create_system_user
    setup_directories
    setup_python_venv
    setup_nginx
    setup_firewall
    setup_logs
    setup_monitoring
    
    echo ""
    success "🎉 Configuración del servidor completada!"
    echo ""
    log "Información de acceso:"
    echo "  - Usuario: parking"
    echo "  - Contraseña: parking123"
    echo "  - Base de datos: parking_altea"
    echo "  - Directorio: $REMOTE_DIR"
    echo ""
    log "Para monitorear: /usr/local/bin/monitor_parking.sh"
}

# Ejecutar función principal
main "$@" 