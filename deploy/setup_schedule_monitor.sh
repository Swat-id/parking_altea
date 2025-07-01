#!/bin/bash

# Script para instalar y configurar el servicio de monitorización de programaciones
# Parking Altea v2.7

set -e

echo "=========================================="
echo "Configurando Servicio de Monitorización"
echo "Parking Altea v2.7"
echo "=========================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "src/schedule_monitor_service.py" ]; then
    echo "Error: No se encuentra schedule_monitor_service.py"
    echo "Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# Hacer el script ejecutable
chmod +x src/schedule_monitor_service.py

# Copiar el archivo de servicio systemd
echo "Copiando archivo de servicio systemd..."
cp deploy/parking-schedule-monitor.service /etc/systemd/system/

# Recargar systemd
echo "Recargando systemd..."
systemctl daemon-reload

# Habilitar el servicio
echo "Habilitando servicio..."
systemctl enable parking-schedule-monitor.service

# Verificar que el archivo de servicio se copió correctamente
if [ ! -f "/etc/systemd/system/parking-schedule-monitor.service" ]; then
    echo "Error: No se pudo copiar el archivo de servicio"
    exit 1
fi

echo "=========================================="
echo "Servicio de monitorización configurado"
echo "=========================================="
echo ""
echo "Comandos útiles:"
echo "  Iniciar servicio: systemctl start parking-schedule-monitor"
echo "  Detener servicio: systemctl stop parking-schedule-monitor"
echo "  Ver estado: systemctl status parking-schedule-monitor"
echo "  Ver logs: journalctl -u parking-schedule-monitor -f"
echo ""
echo "¿Desea iniciar el servicio ahora? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Iniciando servicio..."
    systemctl start parking-schedule-monitor.service
    
    # Verificar que se inició correctamente
    sleep 2
    if systemctl is-active --quiet parking-schedule-monitor.service; then
        echo "✅ Servicio iniciado correctamente"
        echo ""
        echo "Estado del servicio:"
        systemctl status parking-schedule-monitor.service --no-pager -l
    else
        echo "❌ Error al iniciar el servicio"
        echo "Logs del servicio:"
        journalctl -u parking-schedule-monitor.service --no-pager -l -n 20
        exit 1
    fi
else
    echo "Servicio configurado pero no iniciado"
    echo "Para iniciarlo manualmente: systemctl start parking-schedule-monitor"
fi

echo ""
echo "=========================================="
echo "Configuración completada"
echo "==========================================" 