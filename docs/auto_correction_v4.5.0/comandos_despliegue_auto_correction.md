# Comandos de Despliegue - Sistema de Corrección Automática v4.5.0

## Descripción
Este documento contiene los comandos para desplegar el sistema de corrección automática de ocupación basado en patrones históricos de ajustes manuales.

## Requisitos Previos
- Servidor de producción: 157.180.91.63 (ubuntu-16gb-hel1-1)
- Usuario: root
- Repositorio actualizado con la rama v4.5.0

---

## FASE 1: Actualizar Código

```bash
# 1. Conectar al servidor
ssh root@157.180.91.63

# 2. Ir al directorio del proyecto
cd /opt/parking_altea

# 3. Verificar estado actual
git status

# 4. Descartar cambios locales (si los hay)
git checkout -- .
git clean -fd

# 5. Actualizar código
git fetch origin
git checkout v4.5.0
git pull origin v4.5.0

# 6. Verificar que los nuevos archivos existen
ls -la src/auto_correction_*.py
ls -la src/migrations/auto_correction_v4.5.0.sql
```

---

## FASE 2: Ejecutar Migración de Base de Datos

```bash
# 1. Ejecutar migración SQL
sudo -u postgres psql -d parking_db -f /opt/parking_altea/src/migrations/auto_correction_v4.5.0.sql

# 2. Verificar nuevas tablas
sudo -u postgres psql -d parking_db -c "\dt *correction*"

# 3. Verificar estructura de las tablas
sudo -u postgres psql -d parking_db -c "\d parking_correction_config"
sudo -u postgres psql -d parking_db -c "\d correction_calculations"
sudo -u postgres psql -d parking_db -c "\d auto_correction_history"
```

---

## FASE 3: Verificar Datos Existentes de Ajustes Manuales

```bash
# 1. Contar ajustes manuales existentes
sudo -u postgres psql -d parking_db -c "
SELECT 
    p.name as parking,
    COUNT(*) as total_manual_adjustments,
    MIN(oh.timestamp) as oldest,
    MAX(oh.timestamp) as newest
FROM occupancy_history oh
JOIN parkings p ON oh.parking_id = p.id
WHERE oh.source = 'manual'
GROUP BY p.id, p.name
ORDER BY total_manual_adjustments DESC;
"

# 2. Ver ejemplo de datos disponibles
sudo -u postgres psql -d parking_db -c "
SELECT 
    id,
    parking_id,
    timestamp,
    previous_occupancy,
    occupancy as new_occupancy,
    change_amount,
    source
FROM occupancy_history 
WHERE source = 'manual' 
ORDER BY timestamp DESC 
LIMIT 10;
"
```

---

## FASE 4: Ejecutar Bootstrap (Análisis de 12 meses)

```bash
# 1. Activar entorno virtual
source /opt/parking_altea/venv/bin/activate
cd /opt/parking_altea/src

# 2. Ejecutar bootstrap para todos los parkings (últimos 365 días)
python auto_correction_bootstrap.py --days 365

# 3. Verificar resultados del bootstrap
sudo -u postgres psql -d parking_db -c "
SELECT 
    pcc.parking_id,
    p.name,
    pcc.auto_correction_enabled,
    pcc.correction_hour || ':' || LPAD(pcc.correction_minute::text, 2, '0') as correction_time,
    ROUND(pcc.avg_hourly_drift::numeric, 3) as drift_per_hour,
    ROUND(pcc.avg_daily_drift::numeric, 1) as drift_per_day,
    ROUND(pcc.confidence_level::numeric * 100) || '%' as confidence,
    pcc.sample_count,
    pcc.suggested_correction
FROM parking_correction_config pcc
JOIN parkings p ON pcc.parking_id = p.id
ORDER BY pcc.confidence_level DESC;
"

# 4. Verificar cálculos guardados
sudo -u postgres psql -d parking_db -c "
SELECT 
    COUNT(*) as total_calculations,
    COUNT(DISTINCT parking_id) as parkings_with_data,
    MIN(adjustment_timestamp) as oldest_calc,
    MAX(adjustment_timestamp) as newest_calc
FROM correction_calculations;
"
```

---

## FASE 5: Instalar Servicio de Worker

```bash
# 1. Copiar archivo de servicio
cp /opt/parking_altea/deploy/parking-auto-correction.service /etc/systemd/system/

# 2. Recargar systemd
systemctl daemon-reload

# 3. Habilitar e iniciar servicio
systemctl enable parking-auto-correction.service
systemctl start parking-auto-correction.service

# 4. Verificar estado
systemctl status parking-auto-correction.service

# 5. Ver logs del worker
journalctl -u parking-auto-correction.service -f --no-pager | head -50
```

---

## FASE 6: Reiniciar Servicios Backend

```bash
# 1. Reiniciar API para cargar nuevos endpoints
systemctl restart parking-api.service

# 2. Verificar estado de servicios
systemctl status parking-api.service
systemctl status parking-auto-correction.service

# 3. Probar endpoint de configuraciones
curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "Swat2025!"}' | jq -r '.token' > /tmp/token.txt

TOKEN=$(cat /tmp/token.txt)
curl -s -X GET "http://localhost:6001/api/correction-configs" \
  -H "Authorization: Bearer $TOKEN" | jq '.total'
```

---

## FASE 7: Compilar y Desplegar Frontend

```bash
# 1. Ir al directorio del cliente
cd /opt/parking_altea/client

# 2. Instalar dependencias si es necesario
npm install

# 3. Compilar frontend
npm run build

# 4. Matar proceso anterior en puerto 5789
kill $(lsof -t -i:5789) 2>/dev/null || true

# 5. Iniciar frontend en background
nohup npx serve -s dist -l 5789 > /opt/parking_altea/logs/frontend.log 2>&1 &

# 6. Verificar que está corriendo
sleep 2
curl -s -o /dev/null -w "%{http_code}" http://localhost:5789/
```

---

## FASE 8: Verificación Final

```bash
# 1. Verificar todos los servicios
systemctl status parking-api.service | grep "Active:"
systemctl status parking-auto-correction.service | grep "Active:"
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:5789/

# 2. Verificar nuevo endpoint en API
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "Swat2025!"}' | jq -r '.token')

echo "=== Configuraciones de corrección ==="
curl -s -X GET "http://localhost:6001/api/correction-configs" \
  -H "Authorization: Bearer $TOKEN" | jq '.configs | length'

# 3. Verificar acceso a nueva página
echo "=== Verificar acceso desde navegador ==="
echo "URL: https://parking.swat-id.com/admin/auto-correction"
echo "(Requiere login como superadmin)"
```

---

## Comandos Útiles de Mantenimiento

### Ver estado del worker
```bash
journalctl -u parking-auto-correction.service --since "1 hour ago" | tail -30
```

### Ejecutar corrección manual para un parking específico
```bash
source /opt/parking_altea/venv/bin/activate
cd /opt/parking_altea/src
python auto_correction_worker.py --manual --parking-id 1
```

### Ejecutar bootstrap para un parking específico
```bash
python auto_correction_bootstrap.py --days 365 --parking-id 1
```

### Ver estadísticas de corrección de un parking
```bash
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "Swat2025!"}' | jq -r '.token')

curl -s -X GET "http://localhost:6001/api/parkings/1/correction-config?days=30" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Ver historial de correcciones automáticas
```bash
curl -s -X GET "http://localhost:6001/api/auto-corrections/history?days=7" \
  -H "Authorization: Bearer $TOKEN" | jq '.history | length'
```

---

## Notas Importantes

1. **Hora por defecto**: Las correcciones se ejecutan a las **06:00** de cada día
2. **Habilitado por defecto**: Todos los parkings tienen la corrección automática **habilitada** inicialmente
3. **Bootstrap recomendado**: Se recomienda ejecutar el bootstrap con **365 días** para obtener patrones significativos
4. **Confianza mínima**: Solo se aplican correcciones si la confianza es **≥30%**
5. **Límites de seguridad**:
   - Ocupación nunca será negativa (límite inferior: 0)
   - Ocupación máxima: 110% de la capacidad
   - Corrección máxima: 50% de la capacidad

## Solución de Problemas

### El worker no arranca
```bash
# Ver logs detallados
journalctl -u parking-auto-correction.service -xe

# Verificar sintaxis del servicio
systemctl cat parking-auto-correction.service

# Verificar que el script es ejecutable
chmod +x /opt/parking_altea/src/auto_correction_worker.py
```

### No hay datos en la configuración
```bash
# Verificar que existen ajustes manuales
sudo -u postgres psql -d parking_db -c "SELECT COUNT(*) FROM occupancy_history WHERE source = 'manual';"

# Si hay datos, ejecutar bootstrap
python auto_correction_bootstrap.py --days 365
```

### Error de conexión a BD
```bash
# Verificar que la variable DATABASE_URL está correcta
echo $DATABASE_URL

# Probar conexión
sudo -u postgres psql -d parking_db -c "SELECT 1;"
```
