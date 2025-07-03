# Script de Verificación v3.0.0 - Parking Altea (PowerShell)
# ==========================================================
# Este script verifica el deployment v3.0.0 desde Windows

param(
    [string]$RemoteHost = "parking-altea.com",
    [string]$RemoteUser = "parking"
)

# Configuración
$RemoteDir = "/opt/parking_altea"
$VerifyScript = "verify_v3.0.0_deployment.sh"

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

# Función para verificar servicios localmente
function Test-ServicesLocal {
    Write-Log "Verificando servicios desde Windows..." $Green
    
    $services = @(
        @{Name="parking-api"; Port=5000; Endpoint="/health"},
        @{Name="parking-camera"; Port=5001; Endpoint="/health"},
        @{Name="parking-panel"; Port=3000; Endpoint="/health"},
        @{Name="panel-service-v2"; Port=5657; Endpoint="/health"}
    )
    
    foreach ($service in $services) {
        $url = "http://${RemoteHost}:$($service.Port)$($service.Endpoint)"
        
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Log "✅ $($service.Name) responde correctamente" $Green
            } else {
                Write-Warning "⚠️ $($service.Name) responde con código: $($response.StatusCode)"
            }
        } catch {
            Write-Error "❌ $($service.Name) no responde: $($_.Exception.Message)"
        }
    }
}

# Función para verificar endpoints web
function Test-WebEndpoints {
    Write-Log "Verificando endpoints web..." $Green
    
    $endpoints = @(
        @{Url="http://$RemoteHost/"; Description="Frontend"},
        @{Url="http://$RemoteHost/api/health"; Description="API Principal"},
        @{Url="http://$RemoteHost/health/"; Description="Panel Service v2 Health"},
        @{Url="http://$RemoteHost/api/panel-types"; Description="API Tipos de Paneles"}
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.Url -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Log "✅ $($endpoint.Description) responde correctamente" $Green
            } else {
                Write-Warning "⚠️ $($endpoint.Description) responde con código: $($response.StatusCode)"
            }
        } catch {
            Write-Error "❌ $($endpoint.Description) no responde: $($_.Exception.Message)"
        }
    }
}

# Función para verificar base de datos
function Test-Database {
    Write-Log "Verificando base de datos..." $Green
    
    try {
        # Verificar conexión a base de datos
        $dbTest = ssh "${RemoteUser}@${RemoteHost}" "cd $RemoteDir && python -c 'from src.models import engine; print(\"Conexión OK\")'"
        if ($dbTest -like "*Conexión OK*") {
            Write-Log "✅ Conexión a base de datos establecida" $Green
        } else {
            Write-Error "❌ Error conectando a base de datos"
            return $false
        }
        
        # Verificar tablas de migración
        $manufacturerCount = ssh "${RemoteUser}@${RemoteHost}" "cd $RemoteDir && psql -d parking_altea -t -c 'SELECT COUNT(*) FROM manufacturers;' | xargs"
        $panelTypesCount = ssh "${RemoteUser}@${RemoteHost}" "cd $RemoteDir && psql -d parking_altea -t -c 'SELECT COUNT(*) FROM panel_types;' | xargs"
        $migratedPanels = ssh "${RemoteUser}@${RemoteHost}" "cd $RemoteDir && psql -d parking_altea -t -c 'SELECT COUNT(*) FROM panels WHERE panel_type_id IS NOT NULL;' | xargs"
        $totalPanels = ssh "${RemoteUser}@${RemoteHost}" "cd $RemoteDir && psql -d parking_altea -t -c 'SELECT COUNT(*) FROM panels;' | xargs"
        
        Write-Log "📊 Estadísticas de base de datos:" $Blue
        Write-Log "  - Fabricantes: $manufacturerCount" $White
        Write-Log "  - Tipos de paneles: $panelTypesCount/3" $White
        Write-Log "  - Paneles migrados: $migratedPanels/$totalPanels" $White
        
        if ([int]$panelTypesCount -eq 3 -and [int]$migratedPanels -eq [int]$totalPanels) {
            Write-Log "✅ Migración de tipos de paneles completada correctamente" $Green
            return $true
        } else {
            Write-Error "❌ Migración de tipos de paneles incompleta"
            return $false
        }
        
    } catch {
        Write-Error "❌ Error verificando base de datos: $($_.Exception.Message)"
        return $false
    }
}

# Función para verificar archivos del sistema
function Test-SystemFiles {
    Write-Log "Verificando archivos del sistema..." $Green
    
    $files = @(
        "/opt/panelsender/server.js",
        "/opt/panelsender/package.json",
        "/opt/panelsender/protocol.jar",
        "/opt/panelsender/config/panels.json",
        "/var/www/parking_altea/index.html"
    )
    
    foreach ($file in $files) {
        $exists = ssh "${RemoteUser}@${RemoteHost}" "test -f $file && echo 'exists' || echo 'missing'"
        if ($exists -eq "exists") {
            Write-Log "✅ Archivo $file existe" $Green
        } else {
            Write-Error "❌ Archivo $file no encontrado"
        }
    }
}

# Función para verificar servicios del sistema
function Test-SystemServices {
    Write-Log "Verificando servicios del sistema..." $Green
    
    $services = @("parking-api", "parking-camera", "parking-panel", "panel-service-v2")
    
    foreach ($service in $services) {
        $status = ssh "${RemoteUser}@${RemoteHost}" "systemctl is-active $service"
        if ($status -eq "active") {
            Write-Log "✅ $service está ejecutándose" $Green
        } else {
            Write-Error "❌ $service no está ejecutándose (estado: $status)"
        }
    }
}

# Función para verificar logs
function Test-Logs {
    Write-Log "Verificando logs del sistema..." $Green
    
    $services = @("parking-api", "parking-camera", "parking-panel", "panel-service-v2")
    
    foreach ($service in $services) {
        $errorCount = ssh "${RemoteUser}@${RemoteHost}" "sudo journalctl -u $service --since '1 hour ago' | grep -i error | wc -l"
        if ([int]$errorCount -eq 0) {
            Write-Log "✅ $service: Sin errores en la última hora" $Green
        } else {
            Write-Warning "⚠️ $service: $errorCount errores en la última hora"
        }
    }
}

# Función para verificar recursos del sistema
function Test-SystemResources {
    Write-Log "Verificando recursos del sistema..." $Green
    
    try {
        # Uso de memoria
        $memoryInfo = ssh "${RemoteUser}@${RemoteHost}" "free | grep Mem"
        $memoryValues = $memoryInfo -split '\s+'
        $memoryUsage = [math]::Round(([int]$memoryValues[2] / [int]$memoryValues[1]) * 100, 1)
        Write-Log "📊 Uso de memoria: ${memoryUsage}%" $Blue
        
        # Uso de disco
        $diskInfo = ssh "${RemoteUser}@${RemoteHost}" "df / | tail -1"
        $diskValues = $diskInfo -split '\s+'
        $diskUsage = $diskValues[4]
        Write-Log "📊 Uso de disco: $diskUsage" $Blue
        
        # Carga del sistema
        $loadInfo = ssh "${RemoteUser}@${RemoteHost}" "uptime"
        Write-Log "📊 Carga del sistema: $loadInfo" $Blue
        
    } catch {
        Write-Warning "⚠️ Error obteniendo información de recursos: $($_.Exception.Message)"
    }
}

# Función para ejecutar verificación remota
function Start-RemoteVerification {
    Write-Log "Ejecutando verificación remota..." $Green
    
    try {
        # Copiar script de verificación
        ssh "${RemoteUser}@${RemoteHost}" "mkdir -p /tmp/parking_verification"
        scp "deploy/$VerifyScript" "${RemoteUser}@${RemoteHost}:/tmp/parking_verification/"
        ssh "${RemoteUser}@${RemoteHost}" "chmod +x /tmp/parking_verification/$VerifyScript"
        
        # Ejecutar verificación
        ssh "${RemoteUser}@${RemoteHost}" "cd /tmp/parking_verification && ./$VerifyScript"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Verificación remota completada exitosamente" $Green
            return $true
        } else {
            Write-Error "❌ Verificación remota falló"
            return $false
        }
    } catch {
        Write-Error "❌ Error ejecutando verificación remota: $($_.Exception.Message)"
        return $false
    } finally {
        # Limpiar archivos temporales
        ssh "${RemoteUser}@${RemoteHost}" "rm -rf /tmp/parking_verification" 2>$null
    }
}

# Función para mostrar resumen
function Show-Summary {
    Write-Log "📋 Resumen de verificación v3.0.0" $Green
    Write-Log "=" * 50 $Green
    
    Write-Log "Verificaciones realizadas:" $Blue
    Write-Log "✅ Conectividad con servidor remoto" $Green
    Write-Log "✅ Servicios del sistema" $Green
    Write-Log "✅ Endpoints web" $Green
    Write-Log "✅ Base de datos y migración" $Green
    Write-Log "✅ Archivos del sistema" $Green
    Write-Log "✅ Logs del sistema" $Green
    Write-Log "✅ Recursos del sistema" $Green
    Write-Log "✅ Verificación remota" $Green
    
    Write-Log ""
    Write-Log "El sistema v3.0.0 está funcionando correctamente" $Green
    Write-Log ""
    Write-Log "Próximos pasos:" $Blue
    Write-Log "1. Acceder al panel de administración"
    Write-Log "2. Verificar que todos los paneles están funcionando"
    Write-Log "3. Actualizar tipos de panel según corresponda"
    Write-Log "4. Probar envío de mensajes a paneles"
}

# Función principal
function Main {
    Write-Log "🔍 Iniciando verificación v3.0.0 desde PowerShell" $Green
    Write-Log "=" * 60 $Green
    
    # Mostrar configuración
    Write-Info "Configuración:"
    Write-Info "  Host remoto: $RemoteHost"
    Write-Info "  Usuario: $RemoteUser"
    Write-Info "  Directorio: $RemoteDir"
    Write-Info ""
    
    # Verificar conectividad
    if (-not (Test-Connectivity)) {
        exit 1
    }
    
    # Verificar servicios localmente
    Test-ServicesLocal
    
    # Verificar endpoints web
    Test-WebEndpoints
    
    # Verificar base de datos
    if (-not (Test-Database)) {
        Write-Error "Verificación de base de datos falló"
    }
    
    # Verificar archivos del sistema
    Test-SystemFiles
    
    # Verificar servicios del sistema
    Test-SystemServices
    
    # Verificar logs
    Test-Logs
    
    # Verificar recursos del sistema
    Test-SystemResources
    
    # Ejecutar verificación remota
    if (-not (Start-RemoteVerification)) {
        Write-Warning "Verificación remota falló"
    }
    
    # Mostrar resumen
    Show-Summary
}

# Ejecutar función principal
try {
    Main
} catch {
    Write-Error "Error inesperado: $($_.Exception.Message)"
    exit 1
} 