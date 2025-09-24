# Despliegue del Servicio Push de Sensores v4.1.0

## Descripción

El servicio push de sensores v4.1.0 incluye correcciones críticas para compatibilidad total con sensores reales Fleximodo.

## Características v4.1.0

- ✅ **Compatibilidad total** con formato real de sensores Fleximodo
- ✅ **Auto-conversión** de estados: `FREE` → `free`, `BUSY` → `busy`
- ✅ **Soporte timestamps** con milisegundos: `2025-09-24 09:25:04.987`
- ✅ **Auto-creación** de sensores no registrados
- ✅ **Servicio systemd** con auto-reinicio
- ✅ **Monitoreo** y logs estructurados

## Despliegue Automático

### Método 1: Script Automático

```bash
cd /opt/parking_altea
chmod +x deploy/deploy_sensor_push.sh
./deploy/deploy_sensor_push.sh
```

### Método 2: Manual

```bash
# 1. Detener procesos manuales
pkill -f sensor_push_service

# 2. Instalar servicio systemd
cp deploy/parking-sensor-push.service /etc/systemd/system/
systemctl daemon-reload

# 3. Habilitar y iniciar
systemctl enable parking-sensor-push.service
systemctl start parking-sensor-push.service

# 4. Verificar
systemctl status parking-sensor-push.service
curl http://localhost:3535/health
```

## Configuración del Servicio

**Archivo:** `/etc/systemd/system/parking-sensor-push.service`

```ini
[Unit]
Description=Parking Sensor Push Service v4.1.0
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea
Environment=PATH=/opt/parking_altea/venv/bin
ExecStart=/opt/parking_altea/venv/bin/python /opt/parking_altea/src/sensor_push_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Monitoreo y Logs

### Ver Estado del Servicio

```bash
systemctl status parking-sensor-push.service
```

### Ver Logs en Tiempo Real

```bash
journalctl -u parking-sensor-push.service -f
```

### Verificar Conectividad

```bash
curl http://localhost:3535/health
curl http://localhost:3535/stats
```

### Ver Actividad de Sensores

```bash
# Logs del archivo específico
tail -f /opt/parking_altea/src/logs/sensor_push_service.log

# Buscar mensajes de sensores específicos
grep "FC0723" /opt/parking_altea/src/logs/sensor_push_service.log
```

## Comandos de Gestión

### Reiniciar Servicio

```bash
systemctl restart parking-sensor-push.service
```

### Detener Servicio

```bash
systemctl stop parking-sensor-push.service
```

### Deshabilitar Auto-inicio

```bash
systemctl disable parking-sensor-push.service
```

### Ver Logs de Errores

```bash
journalctl -u parking-sensor-push.service --since="1 hour ago" -p err
```

## Verificación de Funcionamiento

### 1. Test de Salud

```bash
curl http://localhost:3535/health
# Esperado: {"status":"healthy","service":"sensor-push-service","version":"4.1.0",...}
```

### 2. Test de Formato Real

```bash
curl -X POST http://localhost:3535/ \
  -H "Content-Type: application/json" \
  -d '{
    "carpark_id": "905",
    "status": "FREE",
    "timestamp": "2025-09-24 09:25:04.987",
    "sensor_info": {
      "serial_number": "TEST123",
      "battery_capacity": 98.5,
      "battery_voltage": "3570",
      "temperature": "22"
    }
  }'
# Esperado: {"success":true,"sensor_id":X,"new_status":"free",...}
```

### 3. Verificar Base de Datos

```bash
psql -h localhost -U postgres -d parking_db -c "
SELECT COUNT(*) as registros_recientes
FROM sensor_status_history 
WHERE timestamp > NOW() - INTERVAL '1 hour';
"
```

## Sensores Reales Soportados

El servicio v4.1.0 es compatible con todos los sensores Fleximodo que envían datos al sistema:

- FC072308, FC07230C, FC07230A, FC07230E
- FC072310, FC07230D, FC072311, FC07230F
- FC07230B, FC072309

## Troubleshooting

### Servicio no arranca

```bash
# Ver logs de error
journalctl -u parking-sensor-push.service --since="10 minutes ago"

# Verificar permisos
ls -la /opt/parking_altea/src/sensor_push_service.py

# Verificar entorno virtual
/opt/parking_altea/venv/bin/python --version
```

### Puerto 3535 ocupado

```bash
# Ver qué proceso usa el puerto
netstat -tlnp | grep :3535

# Matar proceso manual si existe
pkill -f sensor_push_service
```

### Base de datos no conecta

```bash
# Verificar PostgreSQL
systemctl status postgresql

# Probar conexión manual
psql -h localhost -U postgres -d parking_db -c "SELECT 1;"
```

## Actualización

Para actualizar el servicio:

```bash
cd /opt/parking_altea
git pull origin v4.1.0
systemctl restart parking-sensor-push.service
```
