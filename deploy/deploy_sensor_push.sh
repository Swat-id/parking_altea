#!/bin/bash
# Script de despliegue del servicio push de sensores v4.1.0
# Autor: Sistema SWATID
# Fecha: 2025-09-24

set -e

echo "=== Desplegando Servicio Push de Sensores v4.1.0 ==="

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "src/sensor_push_service.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# 2. Detener procesos manuales del servicio push
echo "📝 Deteniendo procesos manuales..."
pkill -f sensor_push_service || true

# 3. Copiar archivo de servicio systemd
echo "📝 Instalando servicio systemd..."
cp deploy/parking-sensor-push.service /etc/systemd/system/
systemctl daemon-reload

# 4. Habilitar y iniciar servicio
echo "📝 Habilitando servicio para auto-inicio..."
systemctl enable parking-sensor-push.service

echo "📝 Iniciando servicio..."
systemctl start parking-sensor-push.service

# 5. Verificar estado
echo "📝 Verificando estado del servicio..."
sleep 3
systemctl status parking-sensor-push.service --no-pager

# 6. Verificar conectividad
echo "📝 Probando conectividad..."
if curl -s http://localhost:3535/health > /dev/null; then
    echo "✅ Servicio push operativo en puerto 3535"
else
    echo "❌ Error: Servicio no responde en puerto 3535"
    exit 1
fi

# 7. Mostrar estadísticas
echo "📊 Estadísticas del servicio:"
curl -s http://localhost:3535/stats | jq '.' || echo "Stats no disponibles"

echo ""
echo "🎉 ¡Despliegue completado exitosamente!"
echo "📡 Servicio push v4.1.0 operativo en puerto 3535"
echo "🔄 Auto-reinicio habilitado con systemd"
echo "📝 Logs: journalctl -u parking-sensor-push.service -f"
