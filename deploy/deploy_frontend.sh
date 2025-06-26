#!/bin/bash

# Script para desplegar el frontend de Parking Altea
# Puerto: 5789

echo "🚀 Desplegando Frontend Parking Altea..."
echo "========================================"

# Configuración
SERVER_IP="157.180.91.63"
REMOTE_DIR="/opt/parking_altea"
FRONTEND_DIR="$REMOTE_DIR/client"
NGINX_CONFIG="/etc/nginx/sites-available/parking-frontend"

# 1. Construir el frontend localmente
echo "📦 Construyendo frontend..."
cd client
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Error construyendo el frontend"
    exit 1
fi

echo "✅ Frontend construido correctamente"

# 2. Subir archivos al servidor
echo "📤 Subiendo archivos al servidor..."
scp -r dist/* root@$SERVER_IP:$FRONTEND_DIR/dist/

if [ $? -ne 0 ]; then
    echo "❌ Error subiendo archivos"
    exit 1
fi

echo "✅ Archivos subidos correctamente"

# 3. Configurar Nginx en el servidor
echo "⚙️  Configurando Nginx..."
ssh root@$SERVER_IP "cat > $NGINX_CONFIG << 'EOF'
server {
    listen 5789;
    server_name $SERVER_IP;
    
    root $FRONTEND_DIR/dist;
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
        proxy_pass http://localhost:5000/;
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

# 4. Habilitar el sitio y reiniciar Nginx
echo "🔄 Reiniciando servicios..."
ssh root@$SERVER_IP "
    ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    echo '✅ Nginx configurado y reiniciado'
"

# 5. Verificar que el puerto esté abierto
echo "🔍 Verificando puerto 5789..."
ssh root@$SERVER_IP "
    if netstat -tlnp | grep :5789; then
        echo '✅ Puerto 5789 está abierto y funcionando'
    else
        echo '❌ Puerto 5789 no está abierto'
        exit 1
    fi
"

# 6. Verificar firewall
echo "🔥 Configurando firewall..."
ssh root@$SERVER_IP "
    ufw allow 5789/tcp
    echo '✅ Puerto 5789 abierto en firewall'
"

echo ""
echo "🎉 Frontend desplegado exitosamente!"
echo "🌐 URL: http://$SERVER_IP:5789"
echo "📊 API: http://$SERVER_IP:5000"
echo ""
echo "📋 Próximos pasos:"
echo "  1. Verificar que el frontend carga correctamente"
echo "  2. Probar la autenticación"
echo "  3. Verificar que las estadísticas funcionan"
echo "  4. Probar la gestión de paneles" 