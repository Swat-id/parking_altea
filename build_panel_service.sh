#!/bin/bash

echo "🚦 CONSTRUYENDO SERVICIO DE PANELES C#"
echo "======================================"

# Verificar que .NET 6 esté instalado
if ! command -v dotnet &> /dev/null; then
    echo "❌ .NET 6 no está instalado. Instalando..."
    # Instalar .NET 6 en Ubuntu/Debian
    wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
    sudo dpkg -i packages-microsoft-prod.deb
    sudo apt-get update
    sudo apt-get install -y apt-transport-https
    sudo apt-get install -y dotnet-sdk-6.0
else
    echo "✅ .NET 6 encontrado: $(dotnet --version)"
fi

# Navegar al directorio del servicio
cd PanelService

# Restaurar dependencias
echo "📦 Restaurando dependencias..."
dotnet restore

# Construir el proyecto
echo "🔨 Construyendo proyecto..."
dotnet build --configuration Release

# Publicar el proyecto
echo "📤 Publicando proyecto..."
dotnet publish --configuration Release --output ./publish

# Copiar DLL CP5200 al directorio de publicación
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

echo ""
echo "✅ SERVICIO CONSTRUIDO EXITOSAMENTE"
echo "==================================="
echo "Directorio: ./PanelService/publish/"
echo "Para ejecutar: cd PanelService/publish && ./start_service.sh"
echo ""
echo "📋 ENDPOINTS DISPONIBLES:"
echo "  GET  /api/panel/status          - Estado de todos los paneles"
echo "  GET  /api/panel/status/{ip}     - Estado de un panel específico"
echo "  POST /api/panel/send            - Enviar mensaje a un panel"
echo "  POST /api/panel/occupancy       - Enviar ocupación a un panel"
echo "  POST /api/panel/broadcast       - Broadcast a todos los paneles"
echo "  POST /api/panel/test/{ip}       - Testear un panel"
echo "  POST /api/panel/static          - Enviar texto estático"
echo ""
echo "📖 DOCUMENTACIÓN: http://localhost:5001/swagger"