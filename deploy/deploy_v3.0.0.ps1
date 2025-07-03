# Script de Deployment v3.0.0 - Parking Altea (PowerShell)
# =======================================================
# Este script ejecuta el deployment v3.0.0 desde Windows

param(
    [string]$RemoteHost = "parking-altea.com",
    [string]$RemoteUser = "parking",
    [switch]$SkipBackup,
    [switch]$SkipVerification,
    [switch]$Force
)

# Configuración
$RemoteDir = "/opt/parking_altea"
$DeployScript = "deploy_v3.0.0_complete.sh"
$VerifyScript = "verify_v3.0.0_deployment.sh"
$RollbackScript = "rollback_v3.0.0.sh"

# Colores para output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$White = "White"

# Función para logging
function Write-Log {
    param([string]$Message, [string]$Color = $White)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Error {
    param([string]$Message)
    Write-Log "ERROR: $Message" $Red
}

function Write-Warning {
    param([string]$Message)
    Write-Log "WARNING: $Message" $Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Log "INFO: $Message" $Blue
}

# Función para verificar conectividad
function Test-Connectivity {
    Write-Log "Verificando conectividad con servidor remoto..." $Green
    
    try {
        $ping = Test-Connection -ComputerName $RemoteHost -Count 3 -Quiet
        if ($ping) {
            Write-Log "Conectividad verificada" $Green
            return $true
        } else {
            Write-Error "No se puede conectar al servidor remoto: $RemoteHost"
            return $false
        }
    } catch {
        Write-Error "Error verificando conectividad: $($_.Exception.Message)"
        return $false
    }
}

# Función para verificar archivos de deployment
function Test-DeploymentFiles {
    Write-Log "Verificando archivos de deployment..." $Green
    
    $files = @($DeployScript, $VerifyScript, $RollbackScript)
    $missingFiles = @()
    
    foreach ($file in $files) {
        $filePath = Join-Path "deploy" $file
        if (-not (Test-Path $filePath)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Error "Archivos de deployment faltantes: $($missingFiles -join ', ')"
        return $false
    }
    
    Write-Log "Todos los archivos de deployment encontrados" $Green
    return $true
}

# Función para copiar archivos al servidor
function Copy-DeploymentFiles {
    Write-Log "Copiando archivos de deployment al servidor..." $Green
    
    try {
        # Crear directorio temporal en el servidor
        ssh "${RemoteUser}@${RemoteHost}" "mkdir -p /tmp/parking_deployment"
        
        # Copiar scripts de deployment
        scp "deploy/$DeployScript" "${RemoteUser}@${RemoteHost}:/tmp/parking_deployment/"
        scp "deploy/$VerifyScript" "${RemoteUser}@${RemoteHost}:/tmp/parking_deployment/"
        scp "deploy/$RollbackScript" "${RemoteUser}@${RemoteHost}:/tmp/parking_deployment/"
        
        # Dar permisos de ejecución
        ssh "${RemoteUser}@${RemoteHost}" "chmod +x /tmp/parking_deployment/*.sh"
        
        Write-Log "Archivos copiados correctamente" $Green
        return $true
    } catch {
        Write-Error "Error copiando archivos: $($_.Exception.Message)"
        return $false
    }
}

# Función para ejecutar deployment
function Start-Deployment {
    Write-Log "Iniciando deployment v3.0.0..." $Green
    
    $deployParams = ""
    if ($SkipBackup) {
        $deployParams += " --skip-backup"
    }
    
    try {
        # Ejecutar script de deployment
        ssh "${RemoteUser}@${RemoteHost}" "cd /tmp/parking_deployment && ./$DeployScript$deployParams"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Deployment completado exitosamente" $Green
            return $true
        } else {
            Write-Error "Deployment falló con código de salida: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Error "Error ejecutando deployment: $($_.Exception.Message)"
        return $false
    }
}

# Función para ejecutar verificación
function Start-Verification {
    if ($SkipVerification) {
        Write-Warning "Verificación omitida por parámetro"
        return $true
    }
    
    Write-Log "Ejecutando verificación post-deployment..." $Green
    
    try {
        # Ejecutar script de verificación
        ssh "${RemoteUser}@${RemoteHost}" "cd /tmp/parking_deployment && ./$VerifyScript"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Verificación completada exitosamente" $Green
            return $true
        } else {
            Write-Error "Verificación falló con código de salida: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Error "Error ejecutando verificación: $($_.Exception.Message)"
        return $false
    }
}

# Función para limpiar archivos temporales
function Remove-TempFiles {
    Write-Log "Limpiando archivos temporales..." $Green
    
    try {
        ssh "${RemoteUser}@${RemoteHost}" "rm -rf /tmp/parking_deployment"
        Write-Log "Archivos temporales eliminados" $Green
    } catch {
        Write-Warning "Error limpiando archivos temporales: $($_.Exception.Message)"
    }
}

# Función para mostrar ayuda
function Show-Help {
    Write-Host @"
Script de Deployment v3.0.0 - Parking Altea

Uso: .\deploy_v3.0.0.ps1 [parámetros]

Parámetros:
    -RemoteHost <string>    Host remoto (default: parking-altea.com)
    -RemoteUser <string>    Usuario remoto (default: parking)
    -SkipBackup            Omitir creación de backup
    -SkipVerification      Omitir verificación post-deployment
    -Force                 Forzar deployment sin confirmación

Ejemplos:
    .\deploy_v3.0.0.ps1
    .\deploy_v3.0.0.ps1 -RemoteHost "mi-servidor.com" -RemoteUser "admin"
    .\deploy_v3.0.0.ps1 -SkipBackup -SkipVerification

"@ -ForegroundColor $Blue
}

# Función principal
function Main {
    Write-Log "🚀 Iniciando deployment v3.0.0 desde PowerShell" $Green
    Write-Log "=" * 60 $Green
    
    # Mostrar configuración
    Write-Info "Configuración:"
    Write-Info "  Host remoto: $RemoteHost"
    Write-Info "  Usuario: $RemoteUser"
    Write-Info "  Directorio: $RemoteDir"
    Write-Info "  Omitir backup: $SkipBackup"
    Write-Info "  Omitir verificación: $SkipVerification"
    Write-Info ""
    
    # Verificar conectividad
    if (-not (Test-Connectivity)) {
        exit 1
    }
    
    # Verificar archivos de deployment
    if (-not (Test-DeploymentFiles)) {
        exit 1
    }
    
    # Confirmar deployment (a menos que se use -Force)
    if (-not $Force) {
        Write-Warning "¿Está seguro de que desea ejecutar el deployment v3.0.0? (y/N)"
        $response = Read-Host
        if ($response -notmatch "^[Yy]$") {
            Write-Log "Deployment cancelado por el usuario" $Yellow
            exit 0
        }
    }
    
    # Copiar archivos al servidor
    if (-not (Copy-DeploymentFiles)) {
        exit 1
    }
    
    # Ejecutar deployment
    if (-not (Start-Deployment)) {
        Write-Error "Deployment falló. Considere ejecutar el rollback manualmente."
        Write-Info "Comando de rollback: ssh ${RemoteUser}@${RemoteHost} 'cd /tmp/parking_deployment && ./$RollbackScript'"
        exit 1
    }
    
    # Ejecutar verificación
    if (-not (Start-Verification)) {
        Write-Warning "Verificación falló. Revise el estado del sistema manualmente."
    }
    
    # Limpiar archivos temporales
    Remove-TempFiles
    
    # Mostrar resumen
    Write-Log "🎉 Deployment v3.0.0 completado" $Green
    Write-Log "=" * 50 $Green
    Write-Log "El sistema ha sido actualizado exitosamente a v3.0.0"
    Write-Log ""
    Write-Log "Próximos pasos:"
    Write-Log "1. Acceder al panel de administración"
    Write-Log "2. Verificar que todos los paneles están funcionando"
    Write-Log "3. Actualizar tipos de panel según corresponda"
    Write-Log "4. Probar envío de mensajes a paneles"
    Write-Log ""
    Write-Log "En caso de problemas, ejecute el rollback:"
    Write-Log "  ssh ${RemoteUser}@${RemoteHost} 'cd /tmp/parking_deployment && ./$RollbackScript'"
}

# Manejo de parámetros
if ($args -contains "-h" -or $args -contains "--help") {
    Show-Help
    exit 0
}

# Ejecutar función principal
try {
    Main
} catch {
    Write-Error "Error inesperado: $($_.Exception.Message)"
    exit 1
} 