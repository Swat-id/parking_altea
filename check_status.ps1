# Script simple para verificar el estado del servidor
$ServerIP = "157.180.91.63"
$APIPort = 6001
$FrontendPort = 5789

Write-Host "=== VERIFICACION DEL SISTEMA DE PARKING ALTEA ===" -ForegroundColor Yellow
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White

# Verificar frontend
Write-Host "`nVerificando Frontend..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://$ServerIP`:$FrontendPort" -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Frontend: Funcionando (Status: $($response.StatusCode))" -ForegroundColor Green
}
catch {
    Write-Host "❌ Frontend: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Verificar API endpoints
$endpoints = @(
    "parkings",
    "statistics", 
    "cameras/status",
    "panels",
    "camera/logs"
)

Write-Host "`nVerificando API Endpoints..." -ForegroundColor Cyan
$successCount = 0
foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://$ServerIP`:$APIPort/$endpoint" -UseBasicParsing -TimeoutSec 10
        Write-Host "✅ $endpoint`: OK" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host "❌ $endpoint`: Error" -ForegroundColor Red
    }
}

# Resumen
Write-Host "`n=== RESUMEN ===" -ForegroundColor Yellow
Write-Host "API Endpoints: $successCount/$($endpoints.Count) funcionando" -ForegroundColor White

if ($successCount -eq $endpoints.Count) {
    Write-Host "🎯 SISTEMA FUNCIONANDO CORRECTAMENTE" -ForegroundColor Green
} else {
    Write-Host "⚠️  PROBLEMAS DETECTADOS" -ForegroundColor Red
}

Write-Host "`nComandos de gestion:" -ForegroundColor Yellow
Write-Host "Reiniciar servicios: ssh root@$ServerIP 'systemctl restart parking-api parking-camera'" -ForegroundColor Gray
Write-Host "Ver logs API: ssh root@$ServerIP 'journalctl -u parking-api --no-pager -n 20'" -ForegroundColor Gray
Write-Host "Ver logs Camaras: ssh root@$ServerIP 'journalctl -u parking-camera --no-pager -n 20'" -ForegroundColor Gray 