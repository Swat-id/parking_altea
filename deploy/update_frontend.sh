#!/bin/bash

# Script para actualizar el frontend en el servidor remoto
# Uso: ./update_frontend.sh

set -e

echo "🚀 Iniciando actualización del frontend..."

# Configuración
SERVER_IP="157.180.91.63"
SERVER_USER="root"
CLIENT_PATH="/opt/parking_altea/client"

echo "📦 Compilando frontend en el servidor remoto..."

# Compilar el frontend en el servidor
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /opt/parking_altea/client
echo "Instalando dependencias..."
npm install --silent
echo "Compilando frontend..."
npm run build
echo "✅ Frontend compilado correctamente"
EOF

echo "🔄 Recargando nginx..."
ssh ${SERVER_USER}@${SERVER_IP} "systemctl reload nginx"

echo "🧪 Verificando que la API funciona..."
ssh ${SERVER_USER}@${SERVER_IP} "curl -s http://localhost:5789/api/panels | jq '.[0:1]' | head -10"

echo "✅ Frontend actualizado correctamente!"
echo "🌐 Accede a: http://${SERVER_IP}:5789" 