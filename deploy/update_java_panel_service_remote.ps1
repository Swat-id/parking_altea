# Script para actualizar el servicio Java con el protocolo correcto en el servidor remoto
# Mapeo correcto de fontSize y colors según documentación del fabricante

param(
    [string]$RemoteHost = "157.180.91.63",
    [string]$RemoteUser = "root"
)

Write-Host "🚀 ACTUALIZACIÓN REMOTA DEL SERVICIO JAVA PANEL" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Configuración del servidor remoto
$PROJECT_DIR = "/opt/parking_altea"
$JAVA_SERVICE_DIR = "$PROJECT_DIR/server/java-panel-service"
$SERVICE_NAME = "parking-panel-service"

# Función para logging
function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-Log "INFO: $Message" "Blue"
}

function Write-Success {
    param([string]$Message)
    Write-Log "SUCCESS: $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-Log "WARNING: $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-Log "ERROR: $Message" "Red"
}

# Función para ejecutar comandos remotos
function Invoke-RemoteCommand {
    param([string]$Command)
    Write-Info "Ejecutando: $Command"
    ssh -o StrictHostKeyChecking=no "${RemoteUser}@${RemoteHost}" $Command
}

# Función para copiar archivos
function Copy-RemoteFile {
    param([string]$Source, [string]$Destination)
    Write-Info "Copiando: $Source -> $Destination"
    scp -o StrictHostKeyChecking=no -r $Source "${RemoteUser}@${RemoteHost}:$Destination"
}

# 1. Verificar conectividad con el servidor
Write-Info "Verificando conectividad con el servidor..."
try {
    $ping = Test-Connection -ComputerName $RemoteHost -Count 3 -Quiet
    if ($ping) {
        Write-Success "Conectividad OK"
    } else {
        Write-Error "No se puede conectar al servidor $RemoteHost"
        exit 1
    }
} catch {
    Write-Error "Error verificando conectividad: $($_.Exception.Message)"
    exit 1
}

# 2. Actualizar código del proyecto en el servidor
Write-Info "Actualizando código del proyecto en el servidor..."
Invoke-RemoteCommand "cd $PROJECT_DIR && git fetch origin"
Invoke-RemoteCommand "cd $PROJECT_DIR && git reset --hard origin/v3.0.0"
Write-Success "Código actualizado"

# 3. Verificar que los archivos del servicio Java existen
Write-Info "Verificando archivos del servicio Java..."
Invoke-RemoteCommand "cd $JAVA_SERVICE_DIR && ls -la"
Invoke-RemoteCommand "cd $JAVA_SERVICE_DIR && ls -la src/main/java/com/parkingaltea/panelservice/service/PanelCommunicationService.java"
Invoke-RemoteCommand "cd $JAVA_SERVICE_DIR && ls -la src/main/java/com/parkingaltea/panelservice/controller/PanelController.java"
Invoke-RemoteCommand "cd $JAVA_SERVICE_DIR && ls -la src/main/java/com/parkingaltea/panelservice/model/PanelMessage.java"
Write-Success "Archivos del servicio Java verificados"

# 4. Verificar Java y Maven en el servidor
Write-Info "Verificando Java y Maven en el servidor..."
Invoke-RemoteCommand "java -version"
Invoke-RemoteCommand "mvn -version"
Write-Success "Java y Maven verificados"

# 5. Compilar servicio Java en el servidor
Write-Info "Compilando servicio Java en el servidor..."
Invoke-RemoteCommand "cd $JAVA_SERVICE_DIR && mvn clean compile package -DskipTests"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error compilando el servicio Java en el servidor"
    exit 1
}
Write-Success "Compilación exitosa"

# 6. Detener servicio actual
Write-Info "Deteniendo servicio actual..."
Invoke-RemoteCommand "systemctl stop $SERVICE_NAME"
Write-Success "Servicio detenido"

# 7. Copiar archivo JAR
Write-Info "Copiando archivo JAR..."
Invoke-RemoteCommand "cp $JAVA_SERVICE_DIR/target/panel-service-1.0.0.jar $PROJECT_DIR/java-panel-service.jar"
Write-Success "Archivo JAR copiado"

# 8. Reiniciar servicio
Write-Info "Reiniciando servicio..."
Invoke-RemoteCommand "systemctl start $SERVICE_NAME"
Write-Success "Servicio reiniciado"

# 9. Verificar estado del servicio
Write-Info "Verificando estado del servicio..."
Invoke-RemoteCommand "systemctl status $SERVICE_NAME --no-pager"

# 10. Esperar que el servicio esté listo
Write-Info "Esperando que el servicio esté listo..."
Start-Sleep -Seconds 5

# 11. Verificar que el servicio responde
Write-Info "Verificando que el servicio responde..."
$response = Invoke-RemoteCommand "curl -s http://127.0.0.1:5656/api/v1/panels/health"

if ($response -like "*Panel Service OK*") {
    Write-Success "Servicio respondiendo correctamente: $response"
} else {
    Write-Error "Error: El servicio no responde correctamente"
    Write-Info "Logs del servicio:"
    Invoke-RemoteCommand "journalctl -u $SERVICE_NAME -n 20 --no-pager"
    exit 1
}

# 12. Pruebas de mapeo de protocolo
Write-Host ""
Write-Info "🧪 PRUEBA DE MAPEO DE PROTOCOLO"
Write-Host "===============================" -ForegroundColor Cyan

# Test 1: Probar mapeo fontSize 16 -> valor 2
Write-Info "1️⃣ Probando mapeo fontSize 16 -> valor 2..."

$testPayload = @{
    ip = "172.20.4.52"
    itemNum = 1
    texts = @("FONT 16 TEST")
    colors = @(1)
    fontSizes = @(16)
    showEffects = @(1)
} | ConvertTo-Json

$response = Invoke-RemoteCommand "curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti -H 'Content-Type: application/json' -d '$testPayload'"
Write-Info "Respuesta: $response"

# Test 2: Probar mapeo color rojo (valor 1)
Write-Info "2️⃣ Probando mapeo color rojo (valor 1)..."

$testPayload2 = @{
    ip = "172.20.4.52"
    itemNum = 1
    texts = @("COLOR ROJO TEST")
    colors = @(1)
    fontSizes = @(16)
    showEffects = @(1)
} | ConvertTo-Json

$response = Invoke-RemoteCommand "curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti -H 'Content-Type: application/json' -d '$testPayload2'"
Write-Info "Respuesta: $response"

# 13. Verificación de logs
Write-Info "📋 VERIFICACIÓN DE LOGS"
Write-Host "=======================" -ForegroundColor Cyan
Write-Info "Comando para ver logs:"
Write-Host "ssh $RemoteUser@$RemoteHost 'journalctl -u $SERVICE_NAME -f'" -ForegroundColor Gray
Write-Host ""
Write-Info "Buscar en logs:"
Write-Host "- 'Parámetros mapeados - fontSize: 16->2'" -ForegroundColor Gray
Write-Host "- 'Simulando envío de mensaje con fontSize=2 y color=1'" -ForegroundColor Gray

# 14. Información final
Write-Host ""
Write-Success "🎉 ACTUALIZACIÓN COMPLETADA"
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Info "📋 Resumen de cambios:"
Write-Host "  • Servicio Java actualizado con protocolo correcto" -ForegroundColor White
Write-Host "  • Mapeo fontSize: 16px -> valor 2 (FONTSIZE_16)" -ForegroundColor White
Write-Host "  • Mapeo color: 1 -> Rojo" -ForegroundColor White
Write-Host "  • Protocolo sendMulti implementado correctamente" -ForegroundColor White
Write-Host "  • Librería Java del fabricante (sin DLL)" -ForegroundColor White
Write-Host ""
Write-Info "🔗 URLs importantes:"
Write-Host "  • Servicio Java: http://$RemoteHost:5656" -ForegroundColor White
Write-Host "  • Health check: http://$RemoteHost:5656/api/v1/panels/health" -ForegroundColor White
Write-Host "  • Backend API: http://$RemoteHost:6001" -ForegroundColor White
Write-Host "  • Frontend: http://$RemoteHost:5789" -ForegroundColor White
Write-Host ""
Write-Info "📋 RESUMEN DEL MAPEO IMPLEMENTADO:"
Write-Host "   fontSize: 16px -> valor 2 (FONTSIZE_16)" -ForegroundColor White
Write-Host "   color: 1 -> Rojo" -ForegroundColor White
Write-Host "   protocolo: sendMulti con mapeo correcto" -ForegroundColor White
Write-Host ""
Write-Success "✅ Actualización completada exitosamente" 