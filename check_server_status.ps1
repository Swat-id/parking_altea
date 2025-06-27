# Script para verificar el estado del servidor y gestionar las respuestas
param(
    [string]$ServerIP = "157.180.91.63",
    [int]$APIPort = 6001,
    [int]$FrontendPort = 5789
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "🔍 VERIFICACIÓN COMPLETA DEL SISTEMA DE PARKING ALTEA" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White

# Función para verificar endpoints
function Test-Endpoint {
    param([string]$Url, [string]$Description)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        Write-Host "✅ $Description`: $($response.StatusCode)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ $Description`: Error - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Verificar endpoints del API
Write-Host "`n=== VERIFICACIÓN DE ENDPOINTS DEL API ===" -ForegroundColor Yellow

$endpoints = @(
    @{Url = "http://$ServerIP`:$APIPort/parkings"; Description = "Lista de parkings"},
    @{Url = "http://$ServerIP`:$APIPort/statistics"; Description = "Estadísticas generales"},
    @{Url = "http://$ServerIP`:$APIPort/cameras/status"; Description = "Estado de cámaras"},
    @{Url = "http://$ServerIP`:$APIPort/panels"; Description = "Lista de paneles"},
    @{Url = "http://$ServerIP`:$APIPort/camera/logs"; Description = "Logs de cámaras"}
)

$apiResults = @()
foreach ($endpoint in $endpoints) {
    $success = Test-Endpoint -Url $endpoint.Url -Description $endpoint.Description
    $apiResults += @{Description = $endpoint.Description; Success = $success}
}

# Verificar frontend
Write-Host "`n=== VERIFICACIÓN DEL FRONTEND ===" -ForegroundColor Yellow
$frontendOk = Test-Endpoint -Url "http://$ServerIP`:$FrontendPort" -Description "Frontend React"

# Obtener detalles de parkings
Write-Host "`n=== ESTADO DE PARKINGS ===" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$ServerIP`:$APIPort/parkings" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        $parkings = $response.Content | ConvertFrom-Json
        Write-Host "Total de parkings: $($parkings.Count)" -ForegroundColor Green
        
        foreach ($parking in $parkings) {
            $statusColor = switch ($parking.estado) {
                "LIBRE" { "Green" }
                "DENSO" { "Yellow" }
                "COMPLETO" { "Red" }
                default { "White" }
            }
            
            Write-Host "🅿️  $($parking.name)" -ForegroundColor $statusColor
            Write-Host "   Estado: $($parking.estado)" -ForegroundColor $statusColor
            Write-Host "   Ocupadas: $($parking.plazas_ocupadas)/$($parking.total_plazas)" -ForegroundColor $statusColor
            Write-Host "   Libres: $($parking.plazas_libres)" -ForegroundColor $statusColor
            Write-Host ""
        }
    }
}
catch {
    Write-Host "❌ Error obteniendo detalles de parkings: $($_.Exception.Message)" -ForegroundColor Red
}

# Obtener estado de cámaras
Write-Host "=== ESTADO DE CÁMARAS ===" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$ServerIP`:$APIPort/cameras/status" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        $cameras = $data.cameras
        Write-Host "Total de cámaras: $($cameras.Count)" -ForegroundColor Green
        
        foreach ($camera in $cameras) {
            $status = if ($camera.is_active) { "🟢 Activa" } else { "🔴 Inactiva" }
            $statusColor = if ($camera.is_active) { "Green" } else { "Red" }
            
            Write-Host "📷 $($camera.name) ($($camera.ip)) - $status" -ForegroundColor $statusColor
            if ($camera.last_message_received) {
                Write-Host "   Último mensaje: $($camera.last_message_received)" -ForegroundColor Gray
            }
            Write-Host ""
        }
    }
}
catch {
    Write-Host "❌ Error obteniendo estado de cámaras: $($_.Exception.Message)" -ForegroundColor Red
}

# Obtener logs recientes
Write-Host "=== LOGS RECIENTES DE CÁMARAS ===" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$ServerIP`:$APIPort/camera/logs?limit=5" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        $logs = $data.logs
        Write-Host "Logs recientes: $($logs.Count) entradas" -ForegroundColor Green
        
        foreach ($log in $logs) {
            Write-Host "📝 $($log.timestamp) - $($log.camera_name)" -ForegroundColor Cyan
            Write-Host "   Entrada: +$($log.delta_in), Salida: -$($log.delta_out), Ocupación: $($log.new_occupancy)" -ForegroundColor White
            if ($log.error_message) {
                Write-Host "   ⚠️  Error: $($log.error_message)" -ForegroundColor Red
            }
            Write-Host ""
        }
    }
}
catch {
    Write-Host "❌ Error obteniendo logs de cámaras: $($_.Exception.Message)" -ForegroundColor Red
}

# Resumen final
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "📊 RESUMEN DEL ESTADO DEL SISTEMA" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

$apiSuccess = ($apiResults | Where-Object { $_.Success }).Count
Write-Host "✅ API Endpoints: $apiSuccess/$($apiResults.Count) funcionando" -ForegroundColor Green
Write-Host "✅ Frontend: $(if ($frontendOk) { 'Funcionando' } else { 'Error' })" -ForegroundColor $(if ($frontendOk) { 'Green' } else { 'Red' })

# Verificar problemas
$problems = @()
if ($apiSuccess -lt $apiResults.Count) {
    foreach ($result in $apiResults) {
        if (-not $result.Success) {
            $problems += "   - $($result.Description): No responde"
        }
    }
}

if (-not $frontendOk) {
    $problems += "   - Frontend: No accesible"
}

if ($problems.Count -gt 0) {
    Write-Host "`n⚠️  PROBLEMAS DETECTADOS:" -ForegroundColor Red
    foreach ($problem in $problems) {
        Write-Host $problem -ForegroundColor Red
    }
    Write-Host "`n🔧 SE REQUIEREN CORRECCIONES" -ForegroundColor Red
}
else {
    Write-Host "`n🎯 SISTEMA LISTO PARA PRODUCCIÓN" -ForegroundColor Green
}

Write-Host "`n=== COMANDOS DE GESTIÓN ===" -ForegroundColor Yellow
Write-Host "Para reiniciar servicios en el servidor:" -ForegroundColor White
Write-Host "  ssh root@$ServerIP 'systemctl restart parking-api parking-camera'" -ForegroundColor Gray
Write-Host "Para ver logs de servicios:" -ForegroundColor White
Write-Host "  ssh root@$ServerIP 'journalctl -u parking-api --no-pager -n 20'" -ForegroundColor Gray
Write-Host "  ssh root@$ServerIP 'journalctl -u parking-camera --no-pager -n 20'" -ForegroundColor Gray 