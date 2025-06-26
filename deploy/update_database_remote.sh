#!/bin/bash

# Script para actualizar la base de datos en el servidor remoto
# Parking Altea - Actualización de estadísticas

echo "🔄 Actualizando base de datos Parking Altea en servidor remoto..."
echo "================================================================"

# Configuración
SERVER_IP="157.180.91.63"
REMOTE_DIR="/opt/parking_altea"
BACKUP_DIR="/opt/backups"

# Crear backup antes de actualizar
echo "📦 Creando backup de la base de datos..."
ssh root@$SERVER_IP "mkdir -p $BACKUP_DIR"
ssh root@$SERVER_IP "sudo -u postgres pg_dump parking_db > $BACKUP_DIR/parking_db_backup_$(date +%Y%m%d_%H%M%S).sql"

# Detener servicios
echo "⏹️  Deteniendo servicios..."
ssh root@$SERVER_IP "systemctl stop parking-api.service"
ssh root@$SERVER_IP "systemctl stop parking-camera.service"

# Actualizar código
echo "📥 Actualizando código desde Git..."
ssh root@$SERVER_IP "cd $REMOTE_DIR && git fetch origin"
ssh root@$SERVER_IP "cd $REMOTE_DIR && git reset --hard origin/v2.2"

# Instalar dependencias si es necesario
echo "📦 Verificando dependencias..."
ssh root@$SERVER_IP "cd $REMOTE_DIR && pip3 install -r requirements.txt"

# Ejecutar script de actualización de base de datos
echo "🗄️  Actualizando estructura de base de datos..."
ssh root@$SERVER_IP "cd $REMOTE_DIR/src && python3 update_database.py"

# Reiniciar servicios
echo "▶️  Reiniciando servicios..."
ssh root@$SERVER_IP "systemctl start parking-api.service"
ssh root@$SERVER_IP "systemctl start parking-camera.service"

# Verificar estado de servicios
echo "🔍 Verificando estado de servicios..."
ssh root@$SERVER_IP "systemctl status parking-api.service --no-pager"
ssh root@$SERVER_IP "systemctl status parking-camera.service --no-pager"

echo "✅ Actualización completada"
echo "📊 Nuevas tablas disponibles:"
echo "  - parking_statistics"
echo "  - daily_statistics"
echo "  - activity_logs"
echo "  - panel_message_logs"
echo "  - vehicle_counts"

echo "🌐 API endpoints nuevos:"
echo "  - GET /panels"
echo "  - POST /panel/{id}/message"
echo "  - POST /panel/{id}/test"
echo "  - GET /parking/{id}/statistics"
echo "  - GET /statistics"
echo "  - GET /parking/{id}/history"
echo "  - GET /logs/activity"
echo "  - GET /logs/panels" 