# Script para actualizar el frontend en el servidor remoto
# Uso: .\update_frontend.ps1

param(
    [string]$ServerIP = "157.180.91.63",
    [string]$ServerUser = "root"
)

Write-Host "🚀 Iniciando actualización del frontend..." -ForegroundColor Green

try {
    Write-Host "📦 Compilando frontend en el servidor remoto..." -ForegroundColor Yellow
    
    # Compilar el frontend en el servidor
    $compileCommand = @"
cd /opt/parking_altea/client
echo "Instalando dependencias..."
npm install --silent
echo "Compilando frontend..."
npm run build
echo "✅ Frontend compilado correctamente"
"@
    
    ssh ${ServerUser}@${ServerIP} $compileCommand
    
    Write-Host "🔄 Recargando nginx..." -ForegroundColor Yellow
    ssh ${ServerUser}@${ServerIP} "systemctl reload nginx"
    
    Write-Host "🧪 Verificando que la API funciona..." -ForegroundColor Yellow
    ssh ${ServerUser}@${ServerIP} "curl -s http://localhost:5789/api/panels | jq '.[0:1]' | head -10"
    
    Write-Host "✅ Frontend actualizado correctamente!" -ForegroundColor Green
    Write-Host "🌐 Accede a: http://${ServerIP}:5789" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error durante la actualización: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 