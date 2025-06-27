#!/bin/bash

echo "🚀 DESPLEGANDO SERVICIO DE PANELES COMPLETO"
echo "==========================================="
echo "Este script despliega el servicio C# y lo integra con Python"
echo "==========================================="

# Verificar que estamos en el directorio correcto
if [ ! -d "src" ]; then
    echo "❌ Error: No se encontró el directorio 'src'"
    echo "   Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Paso 1: Construir el servicio C#
echo ""
echo "🔨 PASO 1: CONSTRUYENDO SERVICIO C#"
echo "==================================="

if [ -d "PanelService" ]; then
    cd PanelService
    
    # Verificar .NET
    if ! command -v dotnet &> /dev/null; then
        echo "❌ .NET 6 no está instalado. Instalando..."
        wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
        sudo dpkg -i packages-microsoft-prod.deb
        sudo apt-get update
        sudo apt-get install -y apt-transport-https
        sudo apt-get install -y dotnet-sdk-6.0
    else
        echo "✅ .NET encontrado: $(dotnet --version)"
    fi
    
    # Restaurar y construir
    echo "📦 Restaurando dependencias..."
    dotnet restore
    
    echo "🔨 Construyendo proyecto..."
    dotnet build --configuration Release
    
    echo "📤 Publicando proyecto..."
    dotnet publish --configuration Release --output ./publish
    
    # Copiar DLL
    echo "📋 Copiando CP5200.dll..."
    cp ../docs/Rotuloselectronicos.NET_API+ejemplos/Rotuloselectronicos.NET\ API/Rotuloselectronicos.NET\ API\ SDK/CP5200.dll ./publish/
    
    # Crear script de inicio
    cat > ./publish/start_service.sh << 'EOF'
#!/bin/bash
echo "🚦 INICIANDO SERVICIO DE PANELES"
echo "================================"
echo "Puerto: 5001"
echo "URL: http://localhost:5001"
echo "Swagger: http://localhost:5001/swagger"
echo ""

# Verificar que CP5200.dll esté presente
if [ ! -f "CP5200.dll" ]; then
    echo "❌ ERROR: CP5200.dll no encontrado"
    exit 1
fi

echo "✅ CP5200.dll encontrado"
echo ""

# Ejecutar el servicio
dotnet ParkingAltea.PanelService.dll --urls "http://0.0.0.0:5001"
EOF

    chmod +x ./publish/start_service.sh
    
    cd ..
    echo "✅ Servicio C# construido exitosamente"
else
    echo "❌ Error: Directorio PanelService no encontrado"
    exit 1
fi

# Paso 2: Integrar con Python
echo ""
echo "🔧 PASO 2: INTEGRANDO CON PYTHON"
echo "================================="

echo "📦 Haciendo backup de archivos originales..."
python3 integrate_panel_service.py

if [ $? -eq 0 ]; then
    echo "✅ Integración completada"
else
    echo "❌ Error en la integración"
    exit 1
fi

# Paso 3: Crear servicio systemd
echo ""
echo "🔧 PASO 3: CREANDO SERVICIO SYSTEMD"
echo "==================================="

SERVICE_FILE="/etc/systemd/system/parking-panel-service.service"
SERVICE_DIR="/opt/parking-panel-service"

# Crear directorio del servicio
sudo mkdir -p $SERVICE_DIR

# Copiar archivos del servicio
sudo cp -r PanelService/publish/* $SERVICE_DIR/

# Crear archivo de servicio
sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Parking Panel Communication Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SERVICE_DIR
ExecStart=$SERVICE_DIR/start_service.sh
Restart=always
RestartSec=10
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://0.0.0.0:5001

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable parking-panel-service

echo "✅ Servicio systemd creado: parking-panel-service"

# Paso 4: Crear script de gestión
echo ""
echo "🔧 PASO 4: CREANDO SCRIPTS DE GESTIÓN"
echo "====================================="

# Script de gestión del servicio
cat > manage_panel_service.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="parking-panel-service"

case "$1" in
    start)
        echo "🚀 Iniciando servicio de paneles..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME
        ;;
    stop)
        echo "🛑 Deteniendo servicio de paneles..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "🔄 Reiniciando servicio de paneles..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME
        ;;
    status)
        echo "📊 Estado del servicio de paneles..."
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "📋 Logs del servicio de paneles..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    test)
        echo "🧪 Testeando servicio de paneles..."
        python3 test_panel_service.py
        ;;
    integration)
        echo "🔗 Testeando integración..."
        python3 test_integration.py
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs|test|integration}"
        echo ""
        echo "Comandos disponibles:"
        echo "  start      - Iniciar el servicio"
        echo "  stop       - Detener el servicio"
        echo "  restart    - Reiniciar el servicio"
        echo "  status     - Ver estado del servicio"
        echo "  logs       - Ver logs en tiempo real"
        echo "  test       - Testear el servicio"
        echo "  integration- Testear integración completa"
        exit 1
        ;;
esac
EOF

chmod +x manage_panel_service.sh

# Script de monitoreo
cat > monitor_panel_service.py << 'EOF'
#!/usr/bin/env python3
"""
Monitor del Servicio de Paneles
Verifica el estado del servicio y los paneles
"""

import time
import requests
import subprocess
from datetime import datetime

def check_service_status():
    """Verificar estado del servicio"""
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_panels_status():
    """Verificar estado de los paneles"""
    try:
        response = requests.get("http://localhost:5001/api/panel/status", timeout=10)
        if response.status_code == 200:
            panels = response.json()
            online_count = sum(1 for panel in panels if panel.get('online', False))
            return len(panels), online_count
        return 0, 0
    except:
        return 0, 0

def main():
    print("📊 MONITOR DEL SERVICIO DE PANELES")
    print("=" * 50)
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Verificar servicio
        service_online = check_service_status()
        service_status = "✅ ONLINE" if service_online else "❌ OFFLINE"
        
        # Verificar paneles
        total_panels, online_panels = check_panels_status()
        panels_status = f"{online_panels}/{total_panels}" if total_panels > 0 else "N/A"
        
        print(f"[{timestamp}] Servicio: {service_status} | Paneles: {panels_status}")
        
        if not service_online:
            print("   ⚠️  Servicio offline - intentando reiniciar...")
            subprocess.run(["./manage_panel_service.sh", "restart"], capture_output=True)
        
        time.sleep(30)  # Verificar cada 30 segundos

if __name__ == "__main__":
    main()
EOF

chmod +x monitor_panel_service.py

echo "✅ Scripts de gestión creados:"
echo "   - manage_panel_service.sh"
echo "   - monitor_panel_service.py"

# Paso 5: Iniciar el servicio
echo ""
echo "🚀 PASO 5: INICIANDO EL SERVICIO"
echo "================================="

echo "🚀 Iniciando servicio de paneles..."
sudo systemctl start parking-panel-service

# Esperar un momento para que el servicio se inicie
sleep 5

# Verificar estado
echo "📊 Verificando estado del servicio..."
sudo systemctl status parking-panel-service --no-pager

# Paso 6: Test inicial
echo ""
echo "🧪 PASO 6: TEST INICIAL"
echo "======================="

echo "🧪 Ejecutando test del servicio..."
python3 test_panel_service.py

echo ""
echo "🔗 Ejecutando test de integración..."
python3 test_integration.py

# Resumen final
echo ""
echo "🎉 DESPLIEGUE COMPLETADO"
echo "======================="
echo "✅ Servicio C# construido y desplegado"
echo "✅ Integración con Python completada"
echo "✅ Servicio systemd configurado"
echo "✅ Scripts de gestión creados"
echo ""
echo "📋 COMANDOS ÚTILES:"
echo "   ./manage_panel_service.sh start     - Iniciar servicio"
echo "   ./manage_panel_service.sh stop      - Detener servicio"
echo "   ./manage_panel_service.sh status    - Ver estado"
echo "   ./manage_panel_service.sh logs      - Ver logs"
echo "   ./manage_panel_service.sh test      - Testear servicio"
echo "   ./manage_panel_service.sh integration - Testear integración"
echo "   ./monitor_panel_service.py          - Monitor continuo"
echo ""
echo "🌐 URLs DEL SERVICIO:"
echo "   Servicio: http://localhost:5001"
echo "   Swagger:  http://localhost:5001/swagger"
echo "   Health:   http://localhost:5001/health"
echo ""
echo "📖 PRÓXIMOS PASOS:"
echo "   1. Verificar que el servicio esté ejecutándose"
echo "   2. Ejecutar tests para confirmar funcionamiento"
echo "   3. Verificar físicamente que los paneles muestran mensajes"
echo "   4. Configurar monitoreo continuo si es necesario" 