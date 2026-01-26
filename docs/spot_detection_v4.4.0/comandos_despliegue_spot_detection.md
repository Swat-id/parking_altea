# Comandos de Despliegue - Sistema de Detección de Plazas v4.4.0

## Resumen de Cambios

- **Puerto 6401**: Nuevo servidor para cámaras de detección por plaza
- **Nuevas tablas**: `monitored_spots`, `spot_status_history`, `spot_occupancy_corrections`, `spot_detection_logs`
- **Modificaciones**: Campos nuevos en `accesses` y `parkings`
- **Límites**: Ocupación mínima 0, máxima 110% de capacidad

## Compatibilidad Hacia Atrás

✅ **Cámaras de conteo existentes**: Siguen funcionando exactamente igual
- La migración actualiza `camera_type='counting'` a todas las cámaras existentes
- El servidor del puerto 6400 solo procesa cámaras de tipo 'counting'
- No se requiere ningún cambio en la configuración de cámaras existentes

✅ **Parkings existentes**: Siguen funcionando sin cambios
- Los nuevos campos tienen valores por defecto seguros:
  - `spot_monitoring_enabled = FALSE`
  - `total_monitored_spots = 0`
  - `total_spot_occupied = 0`
- Los endpoints de API devuelven los nuevos campos (compatibles con frontend actual)

---

## FASE 1: Actualizar Código

### 1.1 Pull del código

```bash
cd /opt/parking_altea
git fetch origin v4.4.0
git checkout v4.4.0
git pull origin v4.4.0
```

---

## FASE 2: Migración de Base de Datos

### 2.1 Ejecutar migración

```bash
sudo -u postgres psql -d parking_db -f /opt/parking_altea/src/migrations/spot_detection_v4.4.0.sql
```

### 2.2 Verificar tablas creadas

```bash
sudo -u postgres psql -d parking_db -c "\dt *spot*"
```

**Resultado esperado:**
```
               List of relations
 Schema |           Name            | Type  |  Owner
--------+---------------------------+-------+----------
 public | monitored_spots           | table | postgres
 public | spot_detection_logs       | table | postgres
 public | spot_occupancy_corrections| table | postgres
 public | spot_status_history       | table | postgres
```

### 2.3 Verificar columnas en accesses

```bash
sudo -u postgres psql -d parking_db -c "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name = 'accesses' AND column_name IN ('camera_type', 'monitored_spots_count')"
```

### 2.4 Verificar columnas en parkings

```bash
sudo -u postgres psql -d parking_db -c "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name = 'parkings' AND column_name LIKE 'spot%' OR column_name LIKE 'total_spot%' OR column_name = 'last_spot_sync'"
```

---

## FASE 3: Configurar Servicio Systemd

### 3.1 Copiar fichero de servicio

```bash
sudo cp /opt/parking_altea/deploy/parking-spot-detection.service /etc/systemd/system/
```

### 3.2 Recargar systemd

```bash
sudo systemctl daemon-reload
```

### 3.3 Habilitar servicio

```bash
sudo systemctl enable parking-spot-detection.service
```

### 3.4 Iniciar servicio

```bash
sudo systemctl start parking-spot-detection.service
```

### 3.5 Verificar estado

```bash
sudo systemctl status parking-spot-detection.service
```

---

## FASE 4: Verificar Funcionamiento

### 4.1 Verificar puerto 6401

```bash
ss -tlnp | grep 6401
```

### 4.2 Health check

```bash
curl http://localhost:6401/detection/health
```

**Resultado esperado:**
```json
{
  "status": "ok",
  "service": "spot_detection_server",
  "version": "4.4.0",
  "database": "ok",
  "port": 6401,
  "limits": {
    "max_occupancy_percent": 110,
    "min_occupancy": 0
  }
}
```

### 4.3 Verificar estadísticas

```bash
curl http://localhost:6401/detection/stats
```

---

## FASE 5: Configurar Firewall (si es necesario)

### 5.1 Abrir puerto 6401

```bash
sudo ufw allow 6401/tcp
```

---

## FASE 6: Configurar Cámaras de Detección

### 6.1 Crear cámara de detección

Para añadir una cámara de tipo "spot_detection":

```bash
sudo -u postgres psql -d parking_db -c "
INSERT INTO accesses (ip, line, name, camera_type, status)
VALUES ('10.8.40.100', 1, 'CamDeteccion_ZonaA', 'spot_detection', 'OFFLINE');
"
```

### 6.2 Asignar cámara a parking

```bash
sudo -u postgres psql -d parking_db -c "
INSERT INTO camera_parkings (camera_id, parking_id)
SELECT a.id, p.id
FROM accesses a, parkings p
WHERE a.name = 'CamDeteccion_ZonaA' AND p.name = 'Nombre del Parking';
"
```

### 6.3 Habilitar monitorización en parking

```bash
sudo -u postgres psql -d parking_db -c "
UPDATE parkings SET spot_monitoring_enabled = TRUE WHERE name = 'Nombre del Parking';
"
```

---

## FASE 7: Reiniciar API (para cargar nuevos modelos)

```bash
sudo systemctl restart parking-api.service
```

---

## Verificación Final

### Listar cámaras por tipo

```bash
sudo -u postgres psql -d parking_db -c "
SELECT id, name, camera_type, monitored_spots_count, status
FROM accesses
ORDER BY camera_type, name;
"
```

### Listar parkings con monitorización

```bash
sudo -u postgres psql -d parking_db -c "
SELECT id, name, spot_monitoring_enabled, total_monitored_spots, total_spot_occupied
FROM parkings
WHERE spot_monitoring_enabled = TRUE;
"
```

---

## Logs y Troubleshooting

### Ver logs del servicio

```bash
journalctl -u parking-spot-detection.service -f
```

### Ver últimos mensajes recibidos

```bash
sudo -u postgres psql -d parking_db -c "
SELECT id, device_name, report_type, status, spots_processed, received_at
FROM spot_detection_logs
ORDER BY received_at DESC
LIMIT 20;
"
```

### Ver plazas monitorizadas

```bash
sudo -u postgres psql -d parking_db -c "
SELECT ms.id, p.name as parking, a.name as camera, ms.area_name, ms.spot_number, ms.current_status
FROM monitored_spots ms
JOIN parkings p ON ms.parking_id = p.id
JOIN accesses a ON ms.camera_id = a.id
ORDER BY p.name, a.name, ms.area_name, ms.spot_number;
"
```

---

## Rollback (si es necesario)

### Detener servicio

```bash
sudo systemctl stop parking-spot-detection.service
sudo systemctl disable parking-spot-detection.service
```

### Eliminar tablas (CUIDADO: pérdida de datos)

```bash
sudo -u postgres psql -d parking_db -c "
DROP TABLE IF EXISTS spot_detection_logs CASCADE;
DROP TABLE IF EXISTS spot_occupancy_corrections CASCADE;
DROP TABLE IF EXISTS spot_status_history CASCADE;
DROP TABLE IF EXISTS monitored_spots CASCADE;
"
```

### Eliminar columnas

```bash
sudo -u postgres psql -d parking_db -c "
ALTER TABLE accesses DROP COLUMN IF EXISTS camera_type;
ALTER TABLE accesses DROP COLUMN IF EXISTS monitored_spots_count;
ALTER TABLE parkings DROP COLUMN IF EXISTS spot_monitoring_enabled;
ALTER TABLE parkings DROP COLUMN IF EXISTS total_monitored_spots;
ALTER TABLE parkings DROP COLUMN IF EXISTS total_spot_occupied;
ALTER TABLE parkings DROP COLUMN IF EXISTS last_spot_sync;
"
```
