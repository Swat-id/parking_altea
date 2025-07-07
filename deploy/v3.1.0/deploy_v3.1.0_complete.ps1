# Script de Despliegue Completo v3.1.0 - Parking Altea (PowerShell)
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

param(
    [switch]$SkipBackup,
    [switch]$SkipTests,
    [switch]$Force
)

# Configuración del servidor
$RemoteHost = "157.180.91.63"
$RemoteUser = "root"
$RemotePassword = "Sudv9uvSvdu!"
$RemoteDir = "/opt/parking_altea"
$BackupDir = "/opt/backups/parking_altea"

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

# Función para copiar archivos
function Copy-RemoteFile {
    param([string]$Source, [string]$Destination)
    $scpCommand = "sshpass -p '$RemotePassword' scp -o StrictHostKeyChecking=no -r '$Source' ${RemoteUser}@${RemoteHost}:$Destination"
    Invoke-Expression $scpCommand
}

# Función para crear backup
function New-Backup {
    if ($SkipBackup) {
        Write-Log "Saltando creación de backup (SkipBackup especificado)" "WARNING"
        return
    }
    
    Write-Log "Creando backup del sistema actual..."
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "parking_altea_backup_v3.1.0_$timestamp"
    
    Invoke-RemoteCommand "mkdir -p $BackupDir"
    $result = Invoke-RemoteCommand "cd $RemoteDir && tar -czf $BackupDir/$backupName.tar.gz ."
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Backup creado: $backupName.tar.gz" "SUCCESS"
    } else {
        Write-Log "Error creando backup" "ERROR"
        exit 1
    }
}

# Función para verificar requisitos
function Test-Requirements {
    Write-Log "Verificando requisitos del sistema..."
    
    # Verificar conexión al servidor
    $testConnection = Invoke-RemoteCommand "echo 'Conexión exitosa'"
    if ($LASTEXITCODE -ne 0) {
        Write-Log "No se puede conectar al servidor remoto" "ERROR"
        exit 1
    }
    
    # Verificar archivos necesarios
    if (-not (Test-Path "src/api_server.py")) {
        Write-Log "No se encuentra api_server.py" "ERROR"
        exit 1
    }
    
    if (-not (Test-Path "client")) {
        Write-Log "No se encuentra el directorio client" "ERROR"
        exit 1
    }
    
    Write-Log "Requisitos verificados correctamente" "SUCCESS"
}

# Función para detener servicios
function Stop-Services {
    Write-Log "Deteniendo servicios actuales..."
    
    Invoke-RemoteCommand "systemctl stop parking-api.service 2>/dev/null || true"
    Invoke-RemoteCommand "systemctl stop parking-camera.service 2>/dev/null || true"
    Invoke-RemoteCommand "systemctl stop parking-schedule-monitor.service 2>/dev/null || true"
    
    Write-Log "Servicios detenidos" "SUCCESS"
}

# Función para actualizar backend
function Update-Backend {
    Write-Log "Actualizando backend..."
    
    # Crear directorio temporal
    Invoke-RemoteCommand "mkdir -p /tmp/parking_backend_update"
    
    # Copiar archivos del backend
    Copy-RemoteFile "src/" "/tmp/parking_backend_update/"
    Copy-RemoteFile "requirements.txt" "/tmp/parking_backend_update/"
    
    # Actualizar archivos en el servidor
    Invoke-RemoteCommand "cp -r /tmp/parking_backend_update/* $RemoteDir/"
    Invoke-RemoteCommand "rm -rf /tmp/parking_backend_update"
    
    # Instalar dependencias
    Invoke-RemoteCommand "cd $RemoteDir && pip3 install -r requirements.txt --upgrade"
    
    # Actualizar permisos
    Invoke-RemoteCommand "chmod +x $RemoteDir/api_server.py"
    Invoke-RemoteCommand "chmod +x $RemoteDir/camera_server.py"
    Invoke-RemoteCommand "chmod +x $RemoteDir/schedule_monitor_service.py"
    
    Write-Log "Backend actualizado" "SUCCESS"
}

# Función para actualizar base de datos
function Update-Database {
    Write-Log "Actualizando base de datos..."
    
    # Copiar scripts de migración
    Copy-RemoteFile "src/migrate_to_v3_1_0.py" "$RemoteDir/"
    Copy-RemoteFile "src/verify_migration_v3_1_0.py" "$RemoteDir/"
    Copy-RemoteFile "src/assign_parkings_to_users.py" "$RemoteDir/"
    
    # Ejecutar migración
    Invoke-RemoteCommand "cd $RemoteDir && python3 migrate_to_v3_1_0.py"
    
    # Verificar migración
    Invoke-RemoteCommand "cd $RemoteDir && python3 verify_migration_v3_1_0.py"
    
    # Asignar parkings a usuarios existentes
    Invoke-RemoteCommand "cd $RemoteDir && python3 assign_parkings_to_users.py"
    
    Write-Log "Base de datos actualizada" "SUCCESS"
}

# Función para actualizar frontend
function Update-Frontend {
    Write-Log "Actualizando frontend..."
    
    # Crear directorio temporal para build
    $buildDir = "/tmp/parking_frontend_build"
    Invoke-RemoteCommand "mkdir -p $buildDir"
    
    # Copiar código del frontend
    Copy-RemoteFile "client/" "$buildDir/"
    
    # Instalar dependencias y hacer build
    Invoke-RemoteCommand "cd $buildDir && npm install"
    Invoke-RemoteCommand "cd $buildDir && npm run build"
    
    # Copiar build al directorio de producción
    Invoke-RemoteCommand "rm -rf $RemoteDir/static"
    Invoke-RemoteCommand "cp -r $buildDir/dist/* $RemoteDir/static/"
    
    # Limpiar directorio temporal
    Invoke-RemoteCommand "rm -rf $buildDir"
    
    Write-Log "Frontend actualizado" "SUCCESS"
}

# Función para actualizar servicios systemd
function Update-Services {
    Write-Log "Actualizando servicios systemd..."
    
    # Copiar archivos de servicio
    Copy-RemoteFile "deploy/v3.1.0/parking-api.service" "/etc/systemd/system/"
    Copy-RemoteFile "deploy/v3.1.0/parking-camera.service" "/etc/systemd/system/"
    Copy-RemoteFile "deploy/v3.1.0/parking-schedule-monitor.service" "/etc/systemd/system/"
    
    # Recargar systemd
    Invoke-RemoteCommand "systemctl daemon-reload"
    
    # Habilitar servicios
    Invoke-RemoteCommand "systemctl enable parking-api.service"
    Invoke-RemoteCommand "systemctl enable parking-camera.service"
    Invoke-RemoteCommand "systemctl enable parking-schedule-monitor.service"
    
    Write-Log "Servicios systemd actualizados" "SUCCESS"
}

# Función para iniciar servicios
function Start-Services {
    Write-Log "Iniciando servicios..."
    
    Invoke-RemoteCommand "systemctl start parking-api.service"
    Invoke-RemoteCommand "systemctl start parking-camera.service"
    Invoke-RemoteCommand "systemctl start parking-schedule-monitor.service"
    
    # Esperar un momento para que los servicios se inicien
    Start-Sleep -Seconds 5
    
    Write-Log "Servicios iniciados" "SUCCESS"
}

# Función para verificar servicios
function Test-Services {
    Write-Log "Verificando servicios..."
    
    # Verificar estado de los servicios
    $apiStatus = Invoke-RemoteCommand "systemctl is-active parking-api.service"
    $cameraStatus = Invoke-RemoteCommand "systemctl is-active parking-camera.service"
    $scheduleStatus = Invoke-RemoteCommand "systemctl is-active parking-schedule-monitor.service"
    
    if ($apiStatus -eq "active" -and $cameraStatus -eq "active" -and $scheduleStatus -eq "active") {
        Write-Log "Todos los servicios están activos" "SUCCESS"
    } else {
        Write-Log "Algunos servicios no están activos" "ERROR"
        Invoke-RemoteCommand "systemctl status parking-api.service"
        Invoke-RemoteCommand "systemctl status parking-camera.service"
        Invoke-RemoteCommand "systemctl status parking-schedule-monitor.service"
        exit 1
    }
    
    # Verificar endpoints
    Write-Log "Verificando endpoints..."
    Start-Sleep -Seconds 10  # Esperar a que los servicios estén completamente iniciados
    
    $healthCheck = Invoke-RemoteCommand "curl -f http://localhost:5000/health"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "API endpoint verificado" "SUCCESS"
    } else {
        Write-Log "API endpoint no responde" "ERROR"
        exit 1
    }
}

# Función para ejecutar tests post-despliegue
function Invoke-PostDeploymentTests {
    if ($SkipTests) {
        Write-Log "Saltando tests post-despliegue (SkipTests especificado)" "WARNING"
        return
    }
    
    Write-Log "Ejecutando tests post-despliegue..."
    
    # Copiar scripts de test
    Copy-RemoteFile "test/v3.1.0/" "$RemoteDir/tests/"
    
    # Ejecutar tests
    Invoke-RemoteCommand "cd $RemoteDir && python3 tests/test_admin_complete.py"
    
    Write-Log "Tests post-despliegue completados" "SUCCESS"
}

# Función para mostrar información del despliegue
function Show-DeploymentInfo {
    Write-Log "Información del despliegue v3.1.0:"
    Write-Host "=================================="
    Write-Host "Servidor: $RemoteHost"
    Write-Host "Directorio: $RemoteDir"
    Write-Host "Backup: $BackupDir"
    Write-Host "Servicios:"
    Write-Host "  - parking-api.service"
    Write-Host "  - parking-camera.service"
    Write-Host "  - parking-schedule-monitor.service"
    Write-Host ""
    Write-Host "Endpoints:"
    Write-Host "  - API: http://$RemoteHost:5000"
    Write-Host "  - Frontend: http://$RemoteHost"
    Write-Host ""
    Write-Host "Logs:"
    Write-Host "  - API: journalctl -u parking-api.service -f"
    Write-Host "  - Camera: journalctl -u parking-camera.service -f"
    Write-Host "  - Schedule: journalctl -u parking-schedule-monitor.service -f"
}

# Función principal
function Start-Deployment {
    Write-Host "🚀 Despliegue Completo v3.1.0 - Parking Altea" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    
    Show-DeploymentInfo
    
    if (-not $Force) {
        $confirmation = Read-Host "¿Continuar con el despliegue? (y/N)"
        if ($confirmation -ne "y" -and $confirmation -ne "Y") {
            Write-Log "Despliegue cancelado"
            exit 0
        }
    }
    
    # Ejecutar pasos del despliegue
    Test-Requirements
    New-Backup
    Stop-Services
    Update-Backend
    Update-Database
    Update-Frontend
    Update-Services
    Start-Services
    Test-Services
    Invoke-PostDeploymentTests
    
    Write-Host ""
    Write-Log "🎉 Despliegue v3.1.0 completado exitosamente!" "SUCCESS"
    Write-Host ""
    Write-Log "El sistema está disponible en: http://$RemoteHost"
    Write-Log "Para ver logs: journalctl -u parking-api.service -f"
}

# Ejecutar función principal
Start-Deployment 