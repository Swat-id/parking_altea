# Script para Actualizar Repositorio en Servidor Remoto v3.1.0 (PowerShell)
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07
# Versión: v3.1.0

param(
    [switch]$Force
)

# Configuración
$RemoteHost = "157.180.91.63"
$RemoteUser = "root"
$RemotePassword = "Sudv9uvSvdu!"
$RemoteDir = "/opt/parking_altea"
$Branch = "v3.1.0_login"

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

# Función para verificar si el repositorio existe
function Test-Repository {
    Write-Log "Verificando si el repositorio existe..."
    
    $repoExists = Invoke-RemoteCommand "[ -d $RemoteDir/.git ]"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Repositorio Git encontrado en $RemoteDir" "SUCCESS"
        return $true
    } else {
        Write-Log "No se encontró repositorio Git en $RemoteDir" "WARNING"
        return $false
    }
}

# Función para clonar el repositorio
function New-Repository {
    Write-Log "Clonando repositorio desde GitHub..."
    
    # Crear directorio si no existe
    Invoke-RemoteCommand "mkdir -p $RemoteDir"
    
    # Clonar repositorio
    Invoke-RemoteCommand "cd $RemoteDir && git clone https://github.com/Swat-id/parking_altea.git ."
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Repositorio clonado exitosamente" "SUCCESS"
    } else {
        Write-Log "Error clonando el repositorio" "ERROR"
        exit 1
    }
}

# Función para actualizar el repositorio
function Update-Repository {
    Write-Log "Actualizando repositorio existente..."
    
    # Guardar cambios locales si existen
    Invoke-RemoteCommand "cd $RemoteDir && git stash"
    
    # Obtener cambios remotos
    Invoke-RemoteCommand "cd $RemoteDir && git fetch origin"
    
    # Verificar si la rama existe
    $branchExists = Invoke-RemoteCommand "cd $RemoteDir && git branch -r | grep origin/$Branch"
    
    if ($branchExists) {
        Write-Log "Rama $Branch encontrada en el repositorio remoto" "SUCCESS"
        
        # Cambiar a la rama
        Invoke-RemoteCommand "cd $RemoteDir && git checkout $Branch"
        
        # Actualizar con los cambios remotos
        Invoke-RemoteCommand "cd $RemoteDir && git pull origin $Branch"
        
        Write-Log "Repositorio actualizado a la rama $Branch" "SUCCESS"
    } else {
        Write-Log "Rama $Branch no encontrada en el repositorio remoto" "ERROR"
        exit 1
    }
}

# Función para verificar el estado del repositorio
function Test-RepositoryStatus {
    Write-Log "Verificando estado del repositorio..."
    
    # Verificar rama actual
    $currentBranch = Invoke-RemoteCommand "cd $RemoteDir && git branch --show-current"
    Write-Log "Rama actual: $currentBranch"
    
    # Verificar último commit
    $lastCommit = Invoke-RemoteCommand "cd $RemoteDir && git log --oneline -1"
    Write-Log "Último commit: $lastCommit"
    
    # Verificar archivos nuevos
    $newFiles = Invoke-RemoteCommand "cd $RemoteDir && git status --porcelain"
    if ($newFiles) {
        Write-Log "Hay archivos modificados o sin commitear:" "WARNING"
        Write-Host $newFiles
    } else {
        Write-Log "Repositorio limpio" "SUCCESS"
    }
    
    # Verificar que el script existe
    $scriptExists = Invoke-RemoteCommand "[ -f $RemoteDir/test/send_en_proves_message.py ]"
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Script send_en_proves_message.py encontrado" "SUCCESS"
    } else {
        Write-Log "Script send_en_proves_message.py no encontrado" "ERROR"
        exit 1
    }
}

# Función para instalar dependencias
function Install-Dependencies {
    Write-Log "Instalando dependencias Python..."
    
    # Verificar si requirements.txt existe
    $requirementsExists = Invoke-RemoteCommand "[ -f $RemoteDir/requirements.txt ]"
    if ($LASTEXITCODE -eq 0) {
        Invoke-RemoteCommand "cd $RemoteDir && pip3 install -r requirements.txt"
        Write-Log "Dependencias instaladas" "SUCCESS"
    } else {
        Write-Log "No se encontró requirements.txt" "WARNING"
    }
    
    # Instalar requests específicamente si no está
    Invoke-RemoteCommand "pip3 install requests"
    Write-Log "Módulo requests instalado" "SUCCESS"
}

# Función para verificar servicios
function Test-Services {
    Write-Log "Verificando servicios del sistema..."
    
    $services = @("parking-api", "parking-camera", "parking-schedule-monitor")
    
    foreach ($service in $services) {
        $status = Invoke-RemoteCommand "systemctl is-active ${service}.service"
        if ($status -eq "active") {
            Write-Log "Servicio $service: ACTIVO" "SUCCESS"
        } else {
            Write-Log "Servicio $service: INACTIVO" "WARNING"
        }
    }
}

# Función principal
function Start-RepositoryUpdate {
    Write-Host "🔄 Actualización de Repositorio en Servidor Remoto v3.1.0" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    
    if (-not $Force) {
        $confirmation = Read-Host "¿Continuar con la actualización del repositorio? (y/N)"
        if ($confirmation -ne "y" -and $confirmation -ne "Y") {
            Write-Log "Actualización cancelada"
            exit 0
        }
    }
    
    # Verificar si el repositorio existe
    if (Test-Repository) {
        # Actualizar repositorio existente
        Update-Repository
    } else {
        # Clonar repositorio nuevo
        New-Repository
    }
    
    # Verificar estado
    Test-RepositoryStatus
    
    # Instalar dependencias
    Install-Dependencies
    
    # Verificar servicios
    Test-Services
    
    Write-Host ""
    Write-Log "🎉 Repositorio actualizado exitosamente!" "SUCCESS"
    Write-Host ""
    Write-Log "Próximos pasos:"
    Write-Host "1. Ejecutar script de envío: python3 $RemoteDir/test/send_en_proves_message.py"
    Write-Host "2. Verificar conectividad: python3 $RemoteDir/test/send_en_proves_message.py --test"
    Write-Host "3. Revisar logs: journalctl -u parking-api.service -f"
}

# Ejecutar función principal
Start-RepositoryUpdate 