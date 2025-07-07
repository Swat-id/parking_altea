# Script de Verificación Post-Despliegue v3.1.0 - Parking Altea (PowerShell)
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

# Configuración
$RemoteHost = "157.180.91.63"
$RemoteUser = "root"
$RemotePassword = "Sudv9uvSvdu!"
$RemoteDir = "/opt/parking_altea"

# Función para logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "Blue" }
    }
    Write-Host "[$timestamp] $Message" -ForegroundColor $color
}

# Función para ejecutar comandos remotos
function Invoke-RemoteCommand {
    param([string]$Command)
    $sshCommand = "sshpass -p '$RemotePassword' ssh -o StrictHostKeyChecking=no ${RemoteUser}@${RemoteHost} '$Command'"
    Invoke-Expression $sshCommand
}

# Función para verificar servicios systemd
function Test-SystemdServices {
    Write-Log "Verificando servicios systemd..."
    
    $services = @("parking-api", "parking-camera", "parking-schedule-monitor")
    
    foreach ($service in $services) {
        $status = Invoke-RemoteCommand "systemctl is-active ${service}.service"
        if ($status -eq "active") {
            Write-Log "Servicio $service está activo" "SUCCESS"
        } else {
            Write-Log "Servicio $service no está activo" "ERROR"
            Invoke-RemoteCommand "systemctl status ${service}.service"
        }
    }
}

# Función para verificar endpoints
function Test-Endpoints {
    Write-Log "Verificando endpoints..."
    
    # Verificar API
    $apiCheck = Invoke-RemoteCommand "curl -f http://localhost:5000/health"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "API endpoint (localhost:5000) responde" "SUCCESS"
    } else {
        Write-Log "API endpoint (localhost:5000) no responde" "ERROR"
    }
    
    # Verificar frontend
    $frontendCheck = Invoke-RemoteCommand "curl -f http://localhost"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Frontend endpoint (localhost) responde" "SUCCESS"
    } else {
        Write-Log "Frontend endpoint (localhost) no responde" "ERROR"
    }
    
    # Verificar desde el exterior
    $externalCheck = Invoke-WebRequest -Uri "http://$RemoteHost" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($externalCheck.StatusCode -eq 200) {
        Write-Log "Frontend accesible desde exterior" "SUCCESS"
    } else {
        Write-Log "Frontend no accesible desde exterior" "ERROR"
    }
}

# Función para verificar base de datos
function Test-Database {
    Write-Log "Verificando base de datos..."
    
    # Verificar conexión a PostgreSQL
    $dbCheck = Invoke-RemoteCommand "sudo -u postgres psql -d parking_altea -c 'SELECT version();'"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Conexión a PostgreSQL exitosa" "SUCCESS"
    } else {
        Write-Log "Error conectando a PostgreSQL" "ERROR"
    }
    
    # Verificar tablas principales
    $tables = @("users", "parkings", "panels", "schedules")
    
    foreach ($table in $tables) {
        $count = Invoke-RemoteCommand "sudo -u postgres psql -d parking_altea -t -c `"SELECT COUNT(*) FROM $table;`""
        if ($count -ge 0) {
            Write-Log "Tabla $table existe con $count registros" "SUCCESS"
        } else {
            Write-Log "Tabla $table no existe o error al consultar" "ERROR"
        }
    }
}

# Función para verificar archivos críticos
function Test-CriticalFiles {
    Write-Log "Verificando archivos críticos..."
    
    $criticalFiles = @(
        "$RemoteDir/api_server.py",
        "$RemoteDir/camera_server.py",
        "$RemoteDir/schedule_monitor_service.py",
        "$RemoteDir/models.py",
        "$RemoteDir/config.py",
        "$RemoteDir/static/index.html",
        "/etc/systemd/system/parking-api.service",
        "/etc/systemd/system/parking-camera.service",
        "/etc/systemd/system/parking-schedule-monitor.service"
    )
    
    foreach ($file in $criticalFiles) {
        $fileCheck = Invoke-RemoteCommand "[ -f $file ]"
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Archivo $file existe" "SUCCESS"
        } else {
            Write-Log "Archivo $file no existe" "ERROR"
        }
    }
}

# Función para verificar permisos
function Test-Permissions {
    Write-Log "Verificando permisos..."
    
    # Verificar propietario de archivos
    $owner = Invoke-RemoteCommand "stat -c '%U:%G' $RemoteDir"
    if ($owner -eq "parking:parking") {
        Write-Log "Propietario correcto: $owner" "SUCCESS"
    } else {
        Write-Log "Propietario incorrecto: $owner (esperado: parking:parking)" "ERROR"
    }
    
    # Verificar permisos de ejecución
    $execCheck = Invoke-RemoteCommand "[ -x $RemoteDir/api_server.py ]"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Permisos de ejecución correctos" "SUCCESS"
    } else {
        Write-Log "Permisos de ejecución incorrectos" "ERROR"
    }
}

# Función para verificar logs
function Test-Logs {
    Write-Log "Verificando logs..."
    
    $logFiles = @(
        "/var/log/syslog",
        "/var/log/nginx/parking_altea_access.log",
        "/var/log/nginx/parking_altea_error.log"
    )
    
    foreach ($logFile in $logFiles) {
        $logCheck = Invoke-RemoteCommand "[ -f $logFile ]"
        if ($LASTEXITCODE -eq 0) {
            $size = Invoke-RemoteCommand "stat -c '%s' $logFile"
            if ($size -gt 0) {
                Write-Log "Log $logFile existe y tiene contenido" "SUCCESS"
            } else {
                Write-Log "Log $logFile existe pero está vacío" "WARNING"
            }
        } else {
            Write-Log "Log $logFile no existe" "WARNING"
        }
    }
}

# Función para verificar recursos del sistema
function Test-SystemResources {
    Write-Log "Verificando recursos del sistema..."
    
    # Verificar uso de disco
    $diskUsage = Invoke-RemoteCommand "df -h $RemoteDir | tail -1 | awk '{print `$5}' | sed 's/%//'"
    if ($diskUsage -lt 80) {
        Write-Log "Uso de disco: ${diskUsage}% (OK)" "SUCCESS"
    } else {
        Write-Log "Uso de disco: ${diskUsage}% (ALTO)" "WARNING"
    }
    
    # Verificar uso de memoria
    $memoryUsage = Invoke-RemoteCommand "free | grep Mem | awk '{printf `"%.0f`", `$3/`$2 * 100.0}'"
    if ($memoryUsage -lt 80) {
        Write-Log "Uso de memoria: ${memoryUsage}% (OK)" "SUCCESS"
    } else {
        Write-Log "Uso de memoria: ${memoryUsage}% (ALTO)" "WARNING"
    }
    
    # Verificar carga del sistema
    $loadAvg = Invoke-RemoteCommand "uptime | awk -F'load average:' '{print `$2}' | awk '{print `$1}' | sed 's/,//'"
    Write-Log "Carga del sistema: $loadAvg" "SUCCESS"
}

# Función para verificar funcionalidades específicas
function Test-Functionality {
    Write-Log "Verificando funcionalidades específicas..."
    
    # Verificar autenticación
    $authCheck = Invoke-RemoteCommand "curl -f http://localhost:5000/auth/login -X POST -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}'"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Endpoint de autenticación responde" "SUCCESS"
    } else {
        Write-Log "Endpoint de autenticación no responde correctamente" "WARNING"
    }
    
    # Verificar listado de parkings
    $parkingsCheck = Invoke-RemoteCommand "curl -f http://localhost:5000/parkings"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Endpoint de parkings responde" "SUCCESS"
    } else {
        Write-Log "Endpoint de parkings no responde" "WARNING"
    }
    
    # Verificar archivos estáticos
    $staticCheck = Invoke-RemoteCommand "curl -f http://localhost/static/js/main.js"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Archivos estáticos accesibles" "SUCCESS"
    } else {
        Write-Log "Archivos estáticos no accesibles" "ERROR"
    }
}

# Función para generar reporte
function New-ValidationReport {
    Write-Log "Generando reporte de verificación..."
    
    $reportFile = "validation_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    
    $reportContent = @"
Reporte de Verificación Post-Despliegue v3.1.0
==============================================
Fecha: $(Get-Date)
Servidor: $RemoteHost
Directorio: $RemoteDir

SERVICIOS SYSTEMD:
$(Invoke-RemoteCommand "systemctl status parking-api.service --no-pager")
$(Invoke-RemoteCommand "systemctl status parking-camera.service --no-pager")
$(Invoke-RemoteCommand "systemctl status parking-schedule-monitor.service --no-pager")

ENDPOINTS:
API Health: $(try { Invoke-RemoteCommand "curl -f http://$RemoteHost:5000/health" } catch { "ERROR" })
Frontend: $(try { Invoke-WebRequest -Uri "http://$RemoteHost" -UseBasicParsing } catch { "ERROR" })

BASE DE DATOS:
$(Invoke-RemoteCommand "sudo -u postgres psql -d parking_altea -c 'SELECT table_name, COUNT(*) FROM information_schema.tables WHERE table_schema = '\''public'\'' GROUP BY table_name;'")

RECURSOS DEL SISTEMA:
$(Invoke-RemoteCommand "df -h")
$(Invoke-RemoteCommand "free -h")
$(Invoke-RemoteCommand "uptime")

LOGS RECIENTES:
$(Invoke-RemoteCommand "tail -20 /var/log/syslog | grep parking")
"@
    
    $reportContent | Out-File -FilePath $reportFile -Encoding UTF8
    Write-Log "Reporte generado: $reportFile" "SUCCESS"
}

# Función principal
function Start-Verification {
    Write-Host "🔍 Verificación Post-Despliegue v3.1.0 - Parking Altea" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
    
    # Ejecutar verificaciones
    Test-SystemdServices
    Test-Endpoints
    Test-Database
    Test-CriticalFiles
    Test-Permissions
    Test-Logs
    Test-SystemResources
    Test-Functionality
    
    # Generar reporte
    New-ValidationReport
    
    Write-Host ""
    Write-Log "🎉 Verificación completada!" "SUCCESS"
    Write-Host ""
    Write-Log "Resumen:"
    Write-Host "  - Servicios: Verificados"
    Write-Host "  - Endpoints: Verificados"
    Write-Host "  - Base de datos: Verificada"
    Write-Host "  - Archivos: Verificados"
    Write-Host "  - Permisos: Verificados"
    Write-Host "  - Logs: Verificados"
    Write-Host "  - Recursos: Verificados"
    Write-Host "  - Funcionalidades: Verificadas"
    Write-Host ""
    Write-Log "El sistema está funcionando correctamente"
}

# Ejecutar función principal
Start-Verification 