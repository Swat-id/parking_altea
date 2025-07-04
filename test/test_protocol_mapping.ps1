# Script de prueba para verificar el mapeo correcto de fontSize y colors
# según el protocolo del fabricante

Write-Host "🔍 PRUEBA DE MAPEO DE PROTOCOLO" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuración
$panelIp = "172.20.4.52"  # BELLES ARTS 2
$javaApiUrl = "http://127.0.0.1:5656/api/v1/panels/sendMulti"

# Test 1: Verificar que el servicio Java está respondiendo
Write-Host "`n1️⃣ Verificando servicio Java en puerto 5656..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:5656/api/v1/panels/health" -Method GET -TimeoutSec 5
    Write-Host "   ✅ Servicio respondiendo: $response" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error conectando al servicio: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Probar mapeo de fontSize 16 -> valor 2
Write-Host "`n2️⃣ Probando mapeo fontSize 16 -> valor 2..." -ForegroundColor Yellow

$payloadFont16 = @{
    ip = $panelIp
    itemNum = 1
    texts = @("FONT 16 TEST")
    colors = @(1)  # Rojo
    fontSizes = @(16)  # Debe mapearse a valor 2
    showEffects = @(1)
} | ConvertTo-Json

Write-Host "   📤 Payload: $payloadFont16" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $javaApiUrl -Method POST -Body $payloadFont16 -ContentType "application/json" -TimeoutSec 10
    Write-Host "   📥 Respuesta: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error enviando mensaje: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Probar mapeo de color rojo (valor 1)
Write-Host "`n3️⃣ Probando mapeo color rojo (valor 1)..." -ForegroundColor Yellow

$payloadRed = @{
    ip = $panelIp
    itemNum = 1
    texts = @("COLOR ROJO TEST")
    colors = @(1)  # Rojo según protocolo
    fontSizes = @(16)  # 16px = valor 2
    showEffects = @(1)
} | ConvertTo-Json

Write-Host "   📤 Payload: $payloadRed" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $javaApiUrl -Method POST -Body $payloadRed -ContentType "application/json" -TimeoutSec 10
    Write-Host "   📥 Respuesta: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error enviando mensaje: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Probar diferentes tamaños de fuente
Write-Host "`n4️⃣ Probando diferentes tamaños de fuente..." -ForegroundColor Yellow

$fontSizes = @(8, 12, 16, 24, 32, 40, 48, 56)
$protocolValues = @(0, 1, 2, 3, 4, 5, 6, 7)

for ($i = 0; $i -lt $fontSizes.Length; $i++) {
    $fontSize = $fontSizes[$i]
    $protocolValue = $protocolValues[$i]
    Write-Host "   📝 Probando fontSize ${fontSize}px -> valor $protocolValue" -ForegroundColor White
    
    $payload = @{
        ip = $panelIp
        itemNum = 1
        texts = @("FONT $fontSize TEST")
        colors = @(1)  # Rojo
        fontSizes = @($fontSize)
        showEffects = @(1)
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $javaApiUrl -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 10
        Write-Host "      ✅ Enviado correctamente" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1  # Pausa entre envíos
}

# Test 5: Probar diferentes colores
Write-Host "`n5️⃣ Probando diferentes colores..." -ForegroundColor Yellow

$colors = @(
    @{Value = 1; Name = "ROJO"},
    @{Value = 2; Name = "VERDE"},
    @{Value = 3; Name = "AMARILLO"},
    @{Value = 4; Name = "AZUL"},
    @{Value = 5; Name = "PURPURA"},
    @{Value = 6; Name = "AZUL2"},
    @{Value = 7; Name = "BLANCO"}
)

foreach ($color in $colors) {
    Write-Host "   📝 Probando color $($color.Name) (valor $($color.Value))" -ForegroundColor White
    
    $payload = @{
        ip = $panelIp
        itemNum = 1
        texts = @("COLOR $($color.Name) TEST")
        colors = @($color.Value)
        fontSizes = @(16)  # 16px = valor 2
        showEffects = @(1)
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $javaApiUrl -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 10
        Write-Host "      ✅ Enviado correctamente" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1  # Pausa entre envíos
}

# Test 6: Verificar logs del servicio Java
Write-Host "`n6️⃣ Verificando logs del servicio Java..." -ForegroundColor Yellow
Write-Host "   🔍 Comando para ver logs:" -ForegroundColor Gray
Write-Host "   📝 journalctl -u parking-panel-service.service -n 50" -ForegroundColor Cyan
Write-Host "   📝 Buscar en logs:" -ForegroundColor Gray
Write-Host "   📝 - 'Parámetros mapeados - fontSize: 16->2'" -ForegroundColor Cyan
Write-Host "   📝 - 'Simulando envío de mensaje con fontSize=2 y color=1'" -ForegroundColor Cyan

# Test 7: Resumen del mapeo
Write-Host "`n7️⃣ RESUMEN DEL MAPEO" -ForegroundColor Yellow
Write-Host "   📋 Mapeo de fontSize:" -ForegroundColor White
Write-Host "     8px -> valor 0" -ForegroundColor Gray
Write-Host "     12px -> valor 1" -ForegroundColor Gray
Write-Host "     16px -> valor 2 (por defecto)" -ForegroundColor Green
Write-Host "     24px -> valor 3" -ForegroundColor Gray
Write-Host "     32px -> valor 4" -ForegroundColor Gray
Write-Host "     40px -> valor 5" -ForegroundColor Gray
Write-Host "     48px -> valor 6" -ForegroundColor Gray
Write-Host "     56px -> valor 7" -ForegroundColor Gray

Write-Host "   📋 Mapeo de colores:" -ForegroundColor White
Write-Host "     1 -> Rojo" -ForegroundColor Gray
Write-Host "     2 -> Verde" -ForegroundColor Gray
Write-Host "     3 -> Amarillo" -ForegroundColor Gray
Write-Host "     4 -> Azul" -ForegroundColor Gray
Write-Host "     5 -> Púrpura" -ForegroundColor Gray
Write-Host "     6 -> Azul (otro tono)" -ForegroundColor Gray
Write-Host "     7 -> Blanco" -ForegroundColor Gray

Write-Host "`n✅ Prueba completada" -ForegroundColor Green 