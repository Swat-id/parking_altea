#!/bin/bash

# Script de actualización para Parking Altea
# Servidor: 157.180.91.63

set -e

echo "=== Iniciando actualización de Parking Altea ==="

# 1. Navegar al directorio del proyecto
echo "Navegando al directorio del proyecto..."
cd /opt/parking_altea

# 2. Actualizar código desde git
echo "Actualizando código desde git..."
git fetch origin
git checkout v1.1
git pull origin v1.1

# 3. Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# 4. Actualizar dependencias si es necesario
echo "Verificando dependencias..."
pip install -r requirements.txt

# 5. Reiniciar servicios
echo "Reiniciando servicios..."
systemctl restart parking-api.service
systemctl restart parking-camera.service

# 6. Verificar estado de servicios
echo "Verificando estado de servicios..."
echo "=== Estado del API Server ==="
systemctl status parking-api.service --no-pager
echo ""
echo "=== Estado del Camera Server ==="
systemctl status parking-camera.service --no-pager

# 7. Verificar conectividad
echo "Verificando conectividad..."
echo "=== Test API ==="
curl -s http://localhost:6001/parkings | head -c 200
echo ""
echo "=== Test Camera Server ==="
curl -s http://localhost:6400/camera

echo ""
echo "=== Actualización completada ==="
echo "API disponible en: http://157.180.91.63:6001"
echo "Servidor de cámaras en puerto: 6400"
echo ""
echo "Para ver logs en tiempo real:"
echo "journalctl -u parking-api.service -f"
echo "journalctl -u parking-camera.service -f" 