#!/bin/bash

# Script completo de despliegue Parking Altea v2.2
# Backend: Puerto 6001
# Frontend: Puerto 5789

echo "🚀 Desplegando Parking Altea v2.2..."
echo "===================================="

# Configuración
SERVER_IP="157.180.91.63"
REMOTE_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups"

# 1. Crear backup de la base de datos
echo "📦 Creando backup de la base de datos..."
ssh root@$SERVER_IP "mkdir -p $BACKUP_DIR"
ssh root@$SERVER_IP "sudo -u postgres pg_dump parking_db > $BACKUP_DIR/parking_db_backup_$(date +%Y%m%d_%H%M%S).sql"

# 2. Detener servicios
echo "⏹️  Deteniendo servicios..."
ssh root@$SERVER_IP "systemctl stop parking-api.service"
ssh root@$SERVER_IP "systemctl stop parking-camera.service"

# 3. Actualizar código desde Git
echo "📥 Actualizando código desde Git..."
ssh root@$SERVER_IP "cd $REMOTE_DIR && git fetch origin"
ssh root@$SERVER_IP "cd $REMOTE_DIR && git reset --hard origin/v2.2"

# 4. Instalar dependencias del backend
echo "📦 Instalando dependencias del backend..."
ssh root@$SERVER_IP "cd $REMOTE_DIR && pip3 install -r requirements.txt"

# 5. Actualizar base de datos
echo "🗄️  Actualizando estructura de base de datos..."
ssh root@$SERVER_IP "cd $REMOTE_DIR/src && python3 update_database.py"

# 6. Instalar dependencias del frontend
echo "📦 Instalando dependencias del frontend..."
ssh root@$SERVER_IP "cd $REMOTE_DIR/client && npm install"

# 7. Construir frontend
echo "🔨 Construyendo frontend..."
ssh root@$SERVER_IP "cd $REMOTE_DIR/client && npm run build"

# 8. Configurar Nginx para frontend
echo "⚙️  Configurando Nginx..."
ssh root@$SERVER_IP "cat > /etc/nginx/sites-available/parking-frontend << 'EOF'
server {
    listen 5789;
    server_name 157.180.91.63;
    
    root /opt/parking_altea/client/dist;
    index index.html;
    
    # Configuración para SPA
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Configuración para archivos estáticos
    location /assets/ {
        expires 1y;
        add_header Cache-Control \"public, immutable\";
    }
    
    # Proxy para API
    location /api/ {
        proxy_pass http://localhost:6001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Configuración de seguridad
    add_header X-Frame-Options \"SAMEORIGIN\" always;
    add_header X-Content-Type-Options \"nosniff\" always;
    add_header X-XSS-Protection \"1; mode=block\" always;
}
EOF"

# 9. Habilitar sitio y reiniciar Nginx
echo "🔄 Reiniciando Nginx..."
ssh root@$SERVER_IP "
    ln -sf /etc/nginx/sites-available/parking-frontend /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
"

# 10. Reiniciar servicios del backend
echo "▶️  Reiniciando servicios del backend..."
ssh root@$SERVER_IP "systemctl start parking-api.service"
ssh root@$SERVER_IP "systemctl start parking-camera.service"

# 11. Configurar firewall
echo "🔥 Configurando firewall..."
ssh root@$SERVER_IP "ufw allow 5789/tcp"

# 12. Verificar estado de servicios
echo "🔍 Verificando estado de servicios..."
ssh root@$SERVER_IP "systemctl status parking-api.service --no-pager"
ssh root@$SERVER_IP "systemctl status parking-camera.service --no-pager"
ssh root@$SERVER_IP "systemctl status nginx --no-pager"

# 13. Verificar puertos
echo "🔍 Verificando puertos..."
ssh root@$SERVER_IP "
    echo 'Puerto 6001 (API):'
    netstat -tlnp | grep :6001
    echo ''
    echo 'Puerto 5789 (Frontend):'
    netstat -tlnp | grep :5789
"

echo ""
echo "🎉 Despliegue completado exitosamente!"
echo "======================================"
echo "🌐 Frontend: http://$SERVER_IP:5789"
echo "📊 API: http://$SERVER_IP:6001"
echo ""
echo "📋 Funcionalidades disponibles:"
echo "  ✅ Sistema de autenticación JWT"
echo "  ✅ Gestión de usuarios y permisos"
echo "  ✅ Estadísticas en tiempo real"
echo "  ✅ Gestión de paneles electrónicos"
echo "  ✅ Logs de actividad y auditoría"
echo "  ✅ Frontend responsive con React"
echo ""
echo "🔑 Usuarios disponibles:"
echo "  Email: atea.dti@altea.es"
echo "  Email: gerenciapstd@altea.es"
echo ""
echo "📝 Próximos pasos:"
echo "  1. Acceder a http://$SERVER_IP:5789"
echo "  2. Iniciar sesión con las credenciales"
echo "  3. Verificar que las estadísticas funcionan"
echo "  4. Probar la gestión de paneles"
echo "  5. Ejecutar pruebas con: python3 test_statistics.py" 