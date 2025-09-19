# Comandos de Despliegue v4.1.0

## Resumen de Comandos

Esta guía contiene todos los comandos necesarios para desplegar la versión 4.1.0 del sistema de gestión de parking, incluyendo las nuevas funcionalidades de selección de ventanas, gestión de plazas individuales PMR y servicio de push de sensores.

## Pre-requisitos

### Verificación del Sistema
```bash
# Verificar versión actual
git branch
git status

# Verificar servicios activos
sudo systemctl status parking-api
sudo systemctl status parking-panel-worker
sudo systemctl status parking-camera

# Verificar base de datos
psql -U parking_user -d parking_db -c "SELECT version();"
```

### Backup del Sistema
```bash
# Crear directorio de backup
sudo mkdir -p /opt/parking_backups/v4.1.0/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/parking_backups/v4.1.0/$(date +%Y%m%d_%H%M%S)"

# Backup de base de datos
sudo -u postgres pg_dump parking_db > "$BACKUP_DIR/parking_db_backup.sql"

# Backup de código
sudo cp -r /opt/parking_altea "$BACKUP_DIR/code_backup"

# Verificar backup
ls -la "$BACKUP_DIR"
```

## FASE 1: Migración de Base de Datos

### Crear Tablas de Sensores Individuales

```sql
-- Conectar a la base de datos
psql -U parking_user -d parking_db

-- Crear tabla de sensores individuales
CREATE TABLE IF NOT EXISTS individual_sensors (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL, -- Nombre descriptivo de la plaza
    sensor_type VARCHAR(20) DEFAULT 'PMR' NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    parking_id INTEGER REFERENCES parkings(id) ON DELETE SET NULL,
    description TEXT,
    location_coordinates VARCHAR(100), -- "lat,lng" format
    manufacturer VARCHAR(50) DEFAULT 'Fleximodo' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear tabla de historial de estados
CREATE TABLE IF NOT EXISTS sensor_status_history (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES individual_sensors(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('free', 'busy', 'error', 'unknown', 'notcalib')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER CHECK (battery_capacity >= 0 AND battery_capacity <= 100),
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    radar_only BOOLEAN DEFAULT FALSE,
    raw_data JSONB
);

-- Crear tabla de estado actual
CREATE TABLE IF NOT EXISTS sensor_current_status (
    sensor_id INTEGER PRIMARY KEY REFERENCES individual_sensors(id) ON DELETE CASCADE,
    current_status VARCHAR(20) NOT NULL CHECK (current_status IN ('free', 'busy', 'error', 'unknown', 'notcalib')),
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    battery_voltage DECIMAL(4,2),
    battery_capacity INTEGER CHECK (battery_capacity >= 0 AND battery_capacity <= 100),
    temperature DECIMAL(5,2),
    network_signal_strength INTEGER,
    consecutive_errors INTEGER DEFAULT 0,
    last_successful_ping TIMESTAMP WITH TIME ZONE
);

-- Crear tabla de resumen por parking
CREATE TABLE IF NOT EXISTS parking_sensor_summary (
    id SERIAL PRIMARY KEY,
    parking_id INTEGER REFERENCES parkings(id) ON DELETE CASCADE,
    sensor_type VARCHAR(20) NOT NULL CHECK (
        sensor_type IN ('PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros')
    ),
    total_sensors INTEGER DEFAULT 0,
    free_sensors INTEGER DEFAULT 0,
    busy_sensors INTEGER DEFAULT 0,
    error_sensors INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parking_id, sensor_type)
);

-- Crear índices para optimización
CREATE INDEX IF NOT EXISTS idx_individual_sensors_parking_id ON individual_sensors(parking_id);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_type ON individual_sensors(sensor_type);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_active ON individual_sensors(is_active);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_serial ON individual_sensors(serial_number);
CREATE INDEX IF NOT EXISTS idx_individual_sensors_name ON individual_sensors(name);

CREATE INDEX IF NOT EXISTS idx_sensor_status_sensor_id ON sensor_status_history(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensor_status_timestamp ON sensor_status_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_status_current ON sensor_status_history(sensor_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_parking_sensor_summary_parking ON parking_sensor_summary(parking_id);

-- Insertar datos de ejemplo (opcional)
INSERT INTO individual_sensors (serial_number, name, sensor_type, description) VALUES
('FLX001001', 'Plaza PMR-01', 'PMR', 'Sensor PMR entrada principal - EJEMPLO'),
('FLX001002', 'Plaza ELE-01', 'Electrico', 'Plaza eléctrica zona A - EJEMPLO'),
('FLX001003', 'Plaza PMR-02', 'PMR', 'Sensor PMR zona B - EJEMPLO')
ON CONFLICT (serial_number) DO NOTHING;

-- Confirmar cambios
COMMIT;

-- Verificar creación de tablas
\dt individual_sensors
\dt sensor_status_history
\dt sensor_current_status
\dt parking_sensor_summary

-- Salir de psql
\q
```

### Comando de Migración Automatizada
```bash
# Crear script de migración
cat > /tmp/migrate_v4.1.0.sql << 'EOF'
-- Script de migración v4.1.0
-- [Incluir todo el contenido SQL de arriba]
EOF

# Ejecutar migración
psql -U parking_user -d parking_db -f /tmp/migrate_v4.1.0.sql

# Verificar migración
psql -U parking_user -d parking_db -c "SELECT count(*) FROM individual_sensors;"
```

## FASE 2: Actualización del Backend

### Detener Servicios
```bash
# Detener servicios principales
sudo systemctl stop parking-api
sudo systemctl stop parking-panel-worker
sudo systemctl stop parking-camera

# Verificar que se detuvieron
sudo systemctl status parking-api
sudo systemctl status parking-panel-worker
sudo systemctl status parking-camera
```

### Actualizar Código Backend
```bash
# Cambiar a directorio del proyecto
cd /opt/parking_altea

# Actualizar desde git
git fetch origin
git checkout v4.1.0
git pull origin v4.1.0

# Verificar cambios
git log --oneline -10

# Instalar nuevas dependencias si las hay
source venv/bin/activate
pip install -r requirements.txt
```

### Verificar Nuevos Modelos
```bash
# Verificar que los nuevos modelos se importan correctamente
cd /opt/parking_altea/src
python3 -c "
from models import IndividualSensor, SensorStatusHistory, SensorCurrentStatus, ParkingSensorSummary
print('✅ Nuevos modelos importados correctamente')
"
```

### Reiniciar Servicios Backend
```bash
# Reiniciar servicios principales
sudo systemctl start parking-api
sudo systemctl start parking-panel-worker
sudo systemctl start parking-camera

# Verificar que iniciaron correctamente
sleep 5
sudo systemctl status parking-api
sudo systemctl status parking-panel-worker
sudo systemctl status parking-camera

# Verificar logs por errores
sudo journalctl -u parking-api -n 20 --no-pager
```

## FASE 3: Despliegue del Servicio Push (Puerto 3535)

### Crear Archivos del Servicio
```bash
# Crear directorio para el servicio push
sudo mkdir -p /opt/parking_altea/src/push_service
cd /opt/parking_altea/src/push_service

# Los archivos del servicio ya deberían estar en el repositorio
# Verificar que existen
ls -la /opt/parking_altea/src/sensor_push_service.py
ls -la /opt/parking_altea/src/start_sensor_push_service.py
```

### Crear Servicio Systemd
```bash
# Crear archivo de servicio
sudo tee /etc/systemd/system/sensor-push-service.service > /dev/null << 'EOF'
[Unit]
Description=Sensor Push Service v4.1.0
After=network.target postgresql.service

[Service]
Type=simple
User=parking
Group=parking
WorkingDirectory=/opt/parking_altea/src
Environment=PYTHONPATH=/opt/parking_altea
Environment=FLASK_ENV=production
Environment=LOG_LEVEL=INFO
ExecStart=/opt/parking_altea/venv/bin/python start_sensor_push_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Configuración de recursos
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
sudo systemctl daemon-reload
```

### Configurar Firewall
```bash
# Permitir tráfico en puerto 3535
sudo ufw allow 3535/tcp comment "Sensor Push Service v4.1.0"

# Verificar reglas de firewall
sudo ufw status numbered
```

### Iniciar Servicio Push
```bash
# Verificar que el puerto esté libre
sudo netstat -tuln | grep :3535 || echo "Puerto 3535 disponible"

# Si el puerto está ocupado, liberar
sudo fuser -k 3535/tcp 2>/dev/null || true
sleep 2

# Habilitar e iniciar servicio
sudo systemctl enable sensor-push-service
sudo systemctl start sensor-push-service

# Verificar estado
sleep 3
sudo systemctl status sensor-push-service

# Verificar que responde
curl -s http://localhost:3535/health | jq . || echo "Servicio respondiendo"
```

### Verificar Logs del Servicio Push
```bash
# Ver logs en tiempo real
sudo journalctl -u sensor-push-service -f

# Ver últimas 50 líneas de logs
sudo journalctl -u sensor-push-service -n 50 --no-pager
```

## FASE 4: Actualización del Frontend

### Construir Nuevo Frontend
```bash
# Cambiar al directorio del cliente
cd /opt/parking_altea/client

# Instalar dependencias (si hay cambios)
npm install

# Construir para producción
npm run build

# Verificar que la construcción fue exitosa
ls -la dist/
```

### Desplegar Frontend
```bash
# Detener frontend actual si está corriendo en puerto 5789
sudo fuser -k 5789/tcp 2>/dev/null || true
sleep 2

# Iniciar nuevo frontend
cd /opt/parking_altea/client
nohup npm run preview -- --port 5789 --host 0.0.0.0 > /var/log/parking/frontend.log 2>&1 &

# Verificar que está corriendo
sleep 5
curl -s http://localhost:5789 > /dev/null && echo "✅ Frontend corriendo en puerto 5789" || echo "❌ Error en frontend"

# Verificar proceso
ps aux | grep "npm run preview" | grep -v grep
```

### Alternativa: Servicio Systemd para Frontend
```bash
# Crear servicio systemd para frontend (recomendado)
sudo tee /etc/systemd/system/parking-frontend.service > /dev/null << 'EOF'
[Unit]
Description=Parking Frontend v4.1.0
After=network.target

[Service]
Type=simple
User=parking
Group=parking
WorkingDirectory=/opt/parking_altea/client
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm run preview -- --port 5789 --host 0.0.0.0
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Recargar, habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable parking-frontend
sudo systemctl stop parking-frontend 2>/dev/null || true
sudo systemctl start parking-frontend

# Verificar estado
sudo systemctl status parking-frontend
```

## FASE 5: Verificación Post-Despliegue

### Verificar Servicios
```bash
# Verificar todos los servicios
echo "=== SERVICIOS DEL SISTEMA ==="
sudo systemctl status parking-api --no-pager -l
echo ""
sudo systemctl status parking-panel-worker --no-pager -l
echo ""
sudo systemctl status parking-camera --no-pager -l
echo ""
sudo systemctl status sensor-push-service --no-pager -l
echo ""
sudo systemctl status parking-frontend --no-pager -l
```

### Verificar Conectividad
```bash
# Verificar endpoints principales
echo "=== VERIFICACIÓN DE ENDPOINTS ==="

# API principal
curl -s http://localhost:5000/api/health | jq . || echo "❌ API principal no responde"

# Servicio push
curl -s http://localhost:3535/health | jq . || echo "❌ Servicio push no responde"

# Frontend
curl -s http://localhost:5789 > /dev/null && echo "✅ Frontend accesible" || echo "❌ Frontend no accesible"

# Verificar desde exterior (cambiar IP si es necesario)
curl -s http://157.180.91.63:5000/api/health | jq . || echo "❌ API no accesible desde exterior"
curl -s http://157.180.91.63:3535/health | jq . || echo "❌ Servicio push no accesible desde exterior"
curl -s http://157.180.91.63:5789 > /dev/null && echo "✅ Frontend accesible desde exterior" || echo "❌ Frontend no accesible desde exterior"
```

### Verificar Base de Datos
```bash
# Verificar nuevas tablas
echo "=== VERIFICACIÓN DE BASE DE DATOS ==="
psql -U parking_user -d parking_db -c "
SELECT 
    schemaname, 
    tablename, 
    tableowner 
FROM pg_tables 
WHERE tablename LIKE '%sensor%' OR tablename LIKE 'individual%'
ORDER BY tablename;
"

# Verificar datos de ejemplo
psql -U parking_user -d parking_db -c "SELECT count(*) as total_sensores FROM individual_sensors;"
```

### Tests de Funcionalidad

#### Test 1: Selección de Ventanas (Manual)
```bash
echo "=== TEST 1: SELECCIÓN DE VENTANAS ==="
echo "1. Acceder a http://157.180.91.63:5789"
echo "2. Ir a página de Paneles"
echo "3. Seleccionar un panel Tipo 3 (si existe)"
echo "4. Verificar que aparece selector de ventana"
echo "5. Enviar mensaje a ventana específica"
echo "✅ Completar verificación manual"
```

#### Test 2: API de Sensores Individuales
```bash
echo "=== TEST 2: API DE SENSORES INDIVIDUALES ==="

# Test crear sensor (requiere autenticación)
echo "Testing API endpoints..."

# Obtener token de autenticación (ajustar credenciales)
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin_password"}' | jq -r '.token' 2>/dev/null)

if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
    echo "✅ Autenticación exitosa"
    
    # Test listar sensores
    curl -s -H "Authorization: Bearer $TOKEN" \
      http://localhost:5000/api/individual-sensors | jq . || echo "❌ Error listando sensores"
    
    echo "✅ API de sensores responde correctamente"
else
    echo "⚠️  No se pudo obtener token de autenticación - verificar credenciales"
fi
```

#### Test 3: Servicio Push
```bash
echo "=== TEST 3: SERVICIO PUSH ==="

# Test mensaje push válido
curl -X POST http://localhost:3535/push \
  -H "Content-Type: application/json" \
  -d '{
    "carpark_id": 1,
    "carpark_code": "TEST",
    "floor": "0",
    "id": 1,
    "number": "A01",
    "status": "busy",
    "idle": false,
    "timestamp": "'$(date '+%Y-%m-%d %H:%M:%S')'",
    "parking_cards": ["1A2B3C4D"],
    "floor_stats": {
      "slot_count": 10,
      "free_count": 5,
      "busy_count": 4,
      "notcalib_count": 1
    },
    "sensor_info": {
      "serial_number": "FLX001001",
      "temperature": 23.5,
      "battery_voltage": 3.2,
      "battery_capacity": 85,
      "radar_only": false
    }
  }' | jq .

echo "✅ Test de push completado - verificar respuesta"
```

## Comandos de Monitorización

### Monitorización Continua
```bash
# Script de monitorización (ejecutar en otra terminal)
cat > /tmp/monitor_v4.1.0.sh << 'EOF'
#!/bin/bash
echo "🔍 Monitorizando sistema v4.1.0..."
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Verificando servicios..."
    
    # Verificar servicios críticos
    for service in parking-api parking-panel-worker parking-camera sensor-push-service parking-frontend; do
        if systemctl is-active --quiet $service; then
            echo "✅ $service: ACTIVO"
        else
            echo "❌ $service: INACTIVO"
        fi
    done
    
    # Verificar conectividad
    if curl -s http://localhost:3535/health > /dev/null; then
        echo "✅ Push service: RESPONDIENDO"
    else
        echo "❌ Push service: NO RESPONDE"
    fi
    
    echo "---"
    sleep 30
done
EOF

chmod +x /tmp/monitor_v4.1.0.sh
# Ejecutar: /tmp/monitor_v4.1.0.sh
```

### Ver Logs en Tiempo Real
```bash
# Logs de todos los servicios
sudo journalctl -f -u parking-api -u parking-panel-worker -u parking-camera -u sensor-push-service -u parking-frontend
```

### Estadísticas del Sistema
```bash
# Uso de recursos
echo "=== ESTADÍSTICAS DEL SISTEMA ==="
echo "CPU y Memoria:"
top -bn1 | head -20

echo -e "\nEspacio en disco:"
df -h

echo -e "\nConexiones de red:"
netstat -tuln | grep -E "(5000|3535|5789)"

echo -e "\nProcesos de parking:"
ps aux | grep -E "(parking|sensor|npm)" | grep -v grep
```

## Comandos de Rollback (En caso de problemas)

### Rollback Completo
```bash
echo "🔄 INICIANDO ROLLBACK A VERSIÓN ANTERIOR..."

# 1. Detener nuevos servicios
sudo systemctl stop sensor-push-service
sudo systemctl stop parking-frontend
sudo systemctl disable sensor-push-service
sudo systemctl disable parking-frontend

# 2. Restaurar servicios principales
sudo systemctl stop parking-api
sudo systemctl stop parking-panel-worker
sudo systemctl stop parking-camera

# 3. Restaurar código
cd /opt/parking_altea
git checkout v4.0.0
git pull origin v4.0.0

# 4. Restaurar base de datos (CUIDADO: esto elimina datos nuevos)
read -p "⚠️  ¿Restaurar base de datos? Esto eliminará datos de sensores individuales (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Encontrar el backup más reciente
    LATEST_BACKUP=$(ls -t /opt/parking_backups/v4.1.0/*/parking_db_backup.sql | head -1)
    if [ -f "$LATEST_BACKUP" ]; then
        echo "Restaurando desde: $LATEST_BACKUP"
        sudo -u postgres dropdb parking_db
        sudo -u postgres createdb parking_db
        sudo -u postgres psql parking_db < "$LATEST_BACKUP"
        echo "✅ Base de datos restaurada"
    else
        echo "❌ No se encontró backup de base de datos"
    fi
fi

# 5. Reiniciar servicios originales
sudo systemctl start parking-api
sudo systemctl start parking-panel-worker
sudo systemctl start parking-camera

# 6. Reiniciar frontend original
cd /opt/parking_altea/client
sudo fuser -k 5789/tcp 2>/dev/null || true
sleep 2
nohup npm run preview -- --port 5789 --host 0.0.0.0 > /var/log/parking/frontend.log 2>&1 &

echo "✅ Rollback completado"
```

### Rollback Parcial (Solo Servicio Push)
```bash
# Solo detener el servicio push si hay problemas
sudo systemctl stop sensor-push-service
sudo systemctl disable sensor-push-service

# Liberar puerto
sudo fuser -k 3535/tcp 2>/dev/null || true

# Cerrar puerto en firewall
sudo ufw delete allow 3535/tcp

echo "✅ Servicio push deshabilitado"
```

## Comandos de Limpieza Post-Despliegue

### Limpiar Archivos Temporales
```bash
# Limpiar archivos temporales
sudo rm -f /tmp/migrate_v4.1.0.sql
sudo rm -f /tmp/monitor_v4.1.0.sh

# Limpiar logs antiguos (opcional)
sudo find /var/log/parking -name "*.log" -mtime +30 -delete 2>/dev/null || true

# Limpiar cache de npm
cd /opt/parking_altea/client
npm cache clean --force
```

### Verificación Final
```bash
echo "🎉 VERIFICACIÓN FINAL DEL DESPLIEGUE v4.1.0"
echo "============================================="

# Resumen de servicios
echo "Servicios activos:"
systemctl is-active parking-api && echo "✅ API Principal"
systemctl is-active parking-panel-worker && echo "✅ Panel Worker"
systemctl is-active parking-camera && echo "✅ Camera Service"
systemctl is-active sensor-push-service && echo "✅ Sensor Push Service"
systemctl is-active parking-frontend && echo "✅ Frontend"

# Resumen de endpoints
echo -e "\nEndpoints disponibles:"
echo "📱 Frontend: http://157.180.91.63:5789"
echo "🔧 API: http://157.180.91.63:5000/api"
echo "📡 Push Service: http://157.180.91.63:3535"

# Estado de base de datos
echo -e "\nBase de datos:"
SENSOR_COUNT=$(psql -U parking_user -d parking_db -t -c "SELECT count(*) FROM individual_sensors;" 2>/dev/null | tr -d ' ')
echo "📊 Sensores individuales: $SENSOR_COUNT"

echo -e "\n✅ Despliegue v4.1.0 completado exitosamente"
echo "📝 Documentación: docs/v4.1.0/"
echo "🔍 Monitorización: /tmp/monitor_v4.1.0.sh"
```

---

*Comandos de despliegue v4.1.0 - Sistema de Gestión de Parking*  
*Última actualización: 19/09/2025*

**⚠️ IMPORTANTE**: Siempre realizar backup antes del despliegue y tener plan de rollback preparado.

**📞 SOPORTE**: En caso de problemas durante el despliegue, verificar logs con `sudo journalctl -u [nombre-servicio] -n 50` y contactar al equipo de desarrollo.
