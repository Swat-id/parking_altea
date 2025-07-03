# Script de Prueba de Preparación para Deployment v3.0.0
# ======================================================
# Este script verifica que todo esté listo para el deployment

param(
    [string]$RemoteHost = "parking-altea.com",
    [string]$RemoteUser = "parking"
)

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

# Función para verificar archivos locales
function Test-LocalFiles {
    Write-Log "Verificando archivos locales..." $Green
    
    $requiredFiles = @(
        "deploy/deploy_v3.0.0_complete.sh",
        "deploy/deploy_v3.0.0.ps1",
        "deploy/verify_v3.0.0_deployment.sh",
        "deploy/verify_v3.0.0.ps1",
        "deploy/rollback_v3.0.0.sh",
        "src/migrate_panel_types.py",
        "src/models.py",
        "server/panel-service-v2/server.js",
        "server/panel-service-v2/protocol.jar",
        "server/panel-service-v2/config/panels.json"
    )
    
    $missingFiles = @()
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Error "Archivos faltantes:"
        foreach ($file in $missingFiles) {
            Write-Error "  - $file"
        }
        return $false
    }
    
    Write-Log "✅ Todos los archivos locales están presentes" $Green
    return $true
}

# Función para verificar conectividad
function Test-Connectivity {
    Write-Log "Verificando conectividad con servidor remoto..." $Green
    
    try {
        $ping = Test-Connection -ComputerName $RemoteHost -Count 3 -Quiet
        if ($ping) {
            Write-Log "✅ Conectividad verificada" $Green
            return $true
        } else {
            Write-Error "❌ No se puede conectar al servidor remoto: $RemoteHost"
            return $false
        }
    } catch {
        Write-Error "❌ Error verificando conectividad: $($_.Exception.Message)"
        return $false
    }
}

# Función para verificar estado actual del servidor
function Test-ServerStatus {
    Write-Log "Verificando estado actual del servidor..." $Green
    
    try {
        # Verificar servicios actuales
        $services = @("parking-api", "parking-camera", "parking-panel")
        $activeServices = 0
        
        foreach ($service in $services) {
            $status = ssh "${RemoteUser}@${RemoteHost}" "systemctl is-active $service 2>/dev/null || echo 'inactive'"
            if ($status -eq "active") {
                Write-Log "✅ $service está ejecutándose" $Green
                $activeServices++
            } else {
                Write-Warning "⚠️ $service no está ejecutándose (estado: $status)" $Yellow
            }
        }
        
        # Verificar Panel Service v2 (no debería existir)
        $panelV2Status = ssh "${RemoteUser}@${RemoteHost}" "systemctl is-active panel-service-v2 2>/dev/null || echo 'not-found'"
        if ($panelV2Status -eq "not-found") {
            Write-Log "✅ Panel Service v2 no existe (correcto)" $Green
        } else {
            Write-Warning "⚠️ Panel Service v2 ya existe (estado: $panelV2Status)" $Yellow
        }
        
        # Verificar base de datos
        $dbTest = ssh "${RemoteUser}@${RemoteHost}" "cd /opt/parking_altea && python -c 'from src.models import engine; print(\"OK\")' 2>/dev/null || echo 'ERROR'"
        if ($dbTest -eq "OK") {
            Write-Log "✅ Conexión a base de datos establecida" $Green
        } else {
            Write-Error "❌ Error conectando a base de datos" $Red
        }
        
        # Verificar espacio en disco
        $diskInfo = ssh "${RemoteUser}@${RemoteHost}" "df / | tail -1"
        $diskValues = $diskInfo -split '\s+'
        $diskUsage = $diskValues[4] -replace '%', ''
        
        if ([int]$diskUsage -lt 90) {
            Write-Log "✅ Espacio en disco: $($diskValues[4]) disponible" $Green
        } else {
            Write-Warning "⚠️ Espacio en disco bajo: $($diskValues[4]) usado" $Yellow
        }
        
        return $true
        
    } catch {
        Write-Error "❌ Error verificando estado del servidor: $($_.Exception.Message)"
        return $false
    }
}

# Función para verificar rama Git
function Test-GitBranch {
    Write-Log "Verificando rama Git..." $Green
    
    try {
        $currentBranch = git branch --show-current
        if ($currentBranch -eq "v3.0.0") {
            Write-Log "✅ Rama actual: v3.0.0" $Green
        } else {
            Write-Warning "⚠️ Rama actual: $currentBranch (esperado: v3.0.0)" $Yellow
        }
        
        $status = git status --porcelain
        if ($status) {
            Write-Warning "⚠️ Hay cambios sin commitear:" $Yellow
            $status | ForEach-Object { Write-Warning "  $_" $Yellow }
        } else {
            Write-Log "✅ Repositorio limpio" $Green
        }
        
        return $true
        
    } catch {
        Write-Error "❌ Error verificando Git: $($_.Exception.Message)"
        return $false
    }
}

# Función para verificar dependencias
function Test-Dependencies {
    Write-Log "Verificando dependencias..." $Green
    
    $dependencies = @("ssh", "scp", "git")
    $missingDeps = @()
    
    foreach ($dep in $dependencies) {
        if (-not (Get-Command $dep -ErrorAction SilentlyContinue)) {
            $missingDeps += $dep
        }
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Error "Dependencias faltantes: $($missingDeps -join ', ')"
        return $false
    }
    
    Write-Log "✅ Todas las dependencias están disponibles" $Green
    return $true
}

# Función para mostrar resumen
function Show-Summary {
    Write-Log "📋 Resumen de Preparación para Deployment v3.0.0" $Green
    Write-Log "=" * 60 $Green
    
    Write-Log "Verificaciones realizadas:" $Blue
    Write-Log "✅ Archivos locales" $Green
    Write-Log "✅ Conectividad con servidor" $Green
    Write-Log "✅ Estado del servidor" $Green
    Write-Log "✅ Rama Git" $Green
    Write-Log "✅ Dependencias" $Green
    
    Write-Log ""
    Write-Log "El sistema está listo para el deployment v3.0.0" $Green
    Write-Log ""
    Write-Log "Próximos pasos:" $Blue
    Write-Log "1. Ejecutar: .\deploy\deploy_v3.0.0.ps1"
    Write-Log "2. Monitorear el proceso de deployment"
    Write-Log "3. Ejecutar verificación: .\deploy\verify_v3.0.0.ps1"
    Write-Log ""
    Write-Log "En caso de problemas:" $Yellow
    Write-Log "1. Revisar logs del deployment"
    Write-Log "2. Ejecutar rollback si es necesario"
    Write-Log "3. Contactar al equipo de desarrollo"
}

# Función principal
function Main {
    Write-Log "🔍 Iniciando verificación de preparación para deployment v3.0.0" $Green
    Write-Log "=" * 70 $Green
    
    # Mostrar configuración
    Write-Info "Configuración:"
    Write-Info "  Host remoto: $RemoteHost"
    Write-Info "  Usuario: $RemoteUser"
    Write-Info ""
    
    $allChecksPassed = $true
    
    # Verificar archivos locales
    if (-not (Test-LocalFiles)) {
        $allChecksPassed = $false
    }
    
    # Verificar dependencias
    if (-not (Test-Dependencies)) {
        $allChecksPassed = $false
    }
    
    # Verificar conectividad
    if (-not (Test-Connectivity)) {
        $allChecksPassed = $false
    }
    
    # Verificar estado del servidor
    if (-not (Test-ServerStatus)) {
        $allChecksPassed = $false
    }
    
    # Verificar rama Git
    if (-not (Test-GitBranch)) {
        $allChecksPassed = $false
    }
    
    # Mostrar resumen
    if ($allChecksPassed) {
        Show-Summary
        exit 0
    } else {
        Write-Error "❌ Verificación de preparación falló"
        Write-Log "Corrija los errores antes de proceder con el deployment" $Red
        exit 1
    }
}

# Ejecutar función principal
try {
    Main
} catch {
    Write-Error "Error inesperado: $($_.Exception.Message)"
    exit 1
} 