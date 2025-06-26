# Mantenimiento y Monitoreo - Parking Altea

## Información General

Este documento describe las tareas de mantenimiento rutinario, monitoreo del sistema y procedimientos de troubleshooting para el sistema Parking Altea.

## Monitoreo Diario

### 1. Verificación de Servicios

```bash
# Script de verificación rápida
#!/bin/bash
echo "=== Verificación Diaria - $(date) ==="

# Verificar servicios
echo "1. Estado de servicios:"
systemctl is-active parking-api.service && echo "✓ API Service: ACTIVO" || echo "✗ API Service: INACTIVO"
systemctl is-active parking-camera.service && echo "✓ Camera Service: ACTIVO" || echo "✗ Camera Service: INACTIVO"
systemctl is-active postgresql && echo "✓ PostgreSQL: ACTIVO" || echo "✗ PostgreSQL: INACTIVO"

# Verificar puertos
echo -e "\n2. Puertos en uso:"
netstat -tlnp | grep -E ':(6001|6400|5432)' | while read line; do
    echo "✓ $line"
done

# Verificar API
echo -e "\n3. Test API:"
if curl -s http://localhost:6001/parkings > /dev/null; then
    echo "✓ API responde correctamente"
else
    echo "✗ API no responde"
fi

# Verificar base de datos
echo -e "\n4. Test Base de Datos:"
if sudo -u postgres psql -d parking_db -c "SELECT COUNT(*) FROM parkings;" > /dev/null 2>&1; then
    echo "✓ Base de datos accesible"
else
    echo "✗ Error de conexión a BD"
fi
```

### 2. Monitoreo de Recursos

```bash
# Verificar uso de recursos
echo "=== Uso de Recursos ==="

# Memoria
echo "Memoria:"
free -h | grep -E "Mem|Swap"

# Disco
echo -e "\nDisco:"
df -h / | tail -1

# CPU
echo -e "\nCPU (últimos 5 minutos):"
uptime

# Conexiones activas
echo -e "\nConexiones activas:"
netstat -an | grep -E ':(6001|6400)' | wc -l
```

### 3. Logs de Errores

```bash
# Verificar errores recientes
echo "=== Errores Recientes ==="

echo "Errores API (últimas 24h):"
journalctl -u parking-api.service -p err --since "24 hours ago" --no-pager

echo -e "\nErrores Camera (últimas 24h):"
journalctl -u parking-camera.service -p err --since "24 hours ago" --no-pager

echo -e "\nErrores PostgreSQL (últimas 24h):"
journalctl -u postgresql -p err --since "24 hours ago" --no-pager
```

## Mantenimiento Semanal

### 1. Limpieza de Logs

```bash
# Limpiar logs antiguos
echo "Limpiando logs antiguos..."

# Limpiar logs de systemd (mantener últimos 30 días)
journalctl --vacuum-time=30d

# Limpiar logs de PostgreSQL
sudo -u postgres psql -c "SELECT pg_rotate_logfile();"

# Verificar espacio liberado
df -h /
```

### 2. Verificación de Base de Datos

```bash
# Análisis de tablas
echo "Analizando tablas de la base de datos..."

sudo -u postgres psql -d parking_db <<EOF
-- Analizar todas las tablas
ANALYZE;

-- Verificar tamaño de tablas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Verificar registros por tabla
SELECT 'parkings' as table_name, COUNT(*) as count FROM parkings
UNION ALL
SELECT 'accesses', COUNT(*) FROM accesses
UNION ALL
SELECT 'panels', COUNT(*) FROM panels
UNION ALL
SELECT 'occupancy_history', COUNT(*) FROM occupancy_history
UNION ALL
SELECT 'scheduled_messages', COUNT(*) FROM scheduled_messages;
EOF
```

### 3. Limpieza de Histórico

```bash
# Limpiar histórico de ocupación (mantener 15 días)
echo "Limpiando histórico de ocupación..."

sudo -u postgres psql -d parking_db <<EOF
-- Eliminar registros antiguos
DELETE FROM occupancy_history 
WHERE timestamp < NOW() - INTERVAL '15 days';

-- Verificar registros restantes
SELECT COUNT(*) as registros_restantes FROM occupancy_history;
EOF
```

### 4. Verificación de Conectividad

```bash
# Verificar conectividad con paneles
echo "Verificando conectividad con paneles..."

# Obtener lista de paneles
panels=$(sudo -u postgres psql -d parking_db -t -c "SELECT ip FROM panels;")

for panel_ip in $panels; do
    if curl -s --connect-timeout 5 http://$panel_ip/update > /dev/null; then
        echo "✓ Panel $panel_ip: RESPONDE"
    else
        echo "✗ Panel $panel_ip: NO RESPONDE"
    fi
done
```

## Mantenimiento Mensual

### 1. Backup Completo

```bash
# Backup completo del sistema
echo "Realizando backup completo..."

BACKUP_DIR="/backup/parking-altea/monthly"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup de base de datos
echo "Backup de base de datos..."
pg_dump parking_db > $BACKUP_DIR/parking_db_$DATE.sql

# Backup de configuración
echo "Backup de configuración..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/parking_altea/

# Backup de logs
echo "Backup de logs..."
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /var/log/

# Limpiar backups antiguos (mantener últimos 3 meses)
find $BACKUP_DIR -name "*.sql" -mtime +90 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +90 -delete

echo "Backup completado: $BACKUP_DIR"
```

### 2. Análisis de Rendimiento

```bash
# Análisis de rendimiento del sistema
echo "Analizando rendimiento..."

# Estadísticas de uso de API
echo "Estadísticas de uso de API (último mes):"
journalctl -u parking-api.service --since "1 month ago" | grep -c "GET\|POST"

# Estadísticas de mensajes de cámaras
echo "Mensajes de cámaras (último mes):"
journalctl -u parking-camera.service --since "1 month ago" | grep -c "POST"

# Análisis de ocupación
sudo -u postgres psql -d parking_db <<EOF
-- Estadísticas de ocupación por aparcamiento
SELECT 
    p.name,
    AVG(oh.occupancy) as avg_occupancy,
    MAX(oh.occupancy) as max_occupancy,
    MIN(oh.occupancy) as min_occupancy,
    COUNT(oh.id) as registros
FROM parkings p
LEFT JOIN occupancy_history oh ON p.id = oh.parking_id
WHERE oh.timestamp >= NOW() - INTERVAL '1 month'
GROUP BY p.id, p.name
ORDER BY avg_occupancy DESC;
EOF
```

### 3. Actualización de Sistema

```bash
# Actualizar sistema operativo
echo "Actualizando sistema operativo..."

# Actualizar paquetes
apt update
apt upgrade -y

# Verificar servicios después de actualización
systemctl restart parking-api.service
systemctl restart parking-camera.service

# Verificar funcionamiento
sleep 10
systemctl is-active parking-api.service && echo "✓ API Service OK" || echo "✗ API Service ERROR"
systemctl is-active parking-camera.service && echo "✓ Camera Service OK" || echo "✗ Camera Service ERROR"
```

## Monitoreo Automático

### 1. Script de Monitoreo Automático

```bash
# Crear script de monitoreo
cat > /opt/parking_altea/monitor.sh <<'EOF'
#!/bin/bash

LOG_FILE="/var/log/parking-altea/monitor.log"
ALERT_EMAIL="admin@swat-id.com"

# Función para logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Función para enviar alerta
send_alert() {
    echo "$1" | mail -s "ALERTA Parking Altea - $(date)" $ALERT_EMAIL
    log "ALERTA ENVIADA: $1"
}

# Verificar servicios
if ! systemctl is-active --quiet parking-api.service; then
    send_alert "API Service está inactivo"
    systemctl restart parking-api.service
    log "API Service reiniciado"
fi

if ! systemctl is-active --quiet parking-camera.service; then
    send_alert "Camera Service está inactivo"
    systemctl restart parking-camera.service
    log "Camera Service reiniciado"
fi

if ! systemctl is-active --quiet postgresql; then
    send_alert "PostgreSQL está inactivo"
    systemctl restart postgresql
    log "PostgreSQL reiniciado"
fi

# Verificar uso de disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    send_alert "Uso de disco crítico: ${DISK_USAGE}%"
fi

# Verificar uso de memoria
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEM_USAGE -gt 90 ]; then
    send_alert "Uso de memoria crítico: ${MEM_USAGE}%"
fi

# Verificar API
if ! curl -s --connect-timeout 10 http://localhost:6001/parkings > /dev/null; then
    send_alert "API no responde"
fi

log "Monitoreo completado"
EOF

chmod +x /opt/parking_altea/monitor.sh
```

### 2. Configurar Cron Jobs

```bash
# Configurar tareas automáticas
cat > /tmp/parking_cron <<EOF
# Monitoreo cada 5 minutos
*/5 * * * * /opt/parking_altea/monitor.sh

# Limpieza diaria a las 2:00 AM
0 2 * * * /opt/parking_altea/backup.sh

# Análisis semanal los domingos a las 3:00 AM
0 3 * * 0 /opt/parking_altea/weekly_maintenance.sh

# Backup mensual el primer día del mes a las 4:00 AM
0 4 1 * * /opt/parking_altea/monthly_maintenance.sh
EOF

crontab /tmp/parking_cron
rm /tmp/parking_cron
```

## Troubleshooting Avanzado

### 1. Problemas de Rendimiento

```bash
# Análisis de rendimiento
echo "=== Análisis de Rendimiento ==="

# Procesos que consumen más CPU
echo "Top procesos por CPU:"
ps aux --sort=-%cpu | head -10

# Procesos que consumen más memoria
echo -e "\nTop procesos por memoria:"
ps aux --sort=-%mem | head -10

# Conexiones de red
echo -e "\nConexiones de red activas:"
netstat -tuln | grep -E ':(6001|6400|5432)'

# Análisis de logs lentos
echo -e "\nConsultas lentas de PostgreSQL:"
sudo -u postgres psql -d parking_db -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

### 2. Problemas de Base de Datos

```bash
# Diagnóstico de base de datos
echo "=== Diagnóstico de Base de Datos ==="

# Verificar locks
sudo -u postgres psql -d parking_db -c "
SELECT pid, usename, application_name, client_addr, state, query 
FROM pg_stat_activity 
WHERE state != 'idle';
"

# Verificar tamaño de tablas
sudo -u postgres psql -d parking_db -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::text)) as size,
    pg_total_relation_size(tablename::text) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::text) DESC;
"

# Verificar índices
sudo -u postgres psql -d parking_db -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
"
```

### 3. Problemas de Red

```bash
# Diagnóstico de red
echo "=== Diagnóstico de Red ==="

# Verificar conectividad con paneles
echo "Test de conectividad con paneles:"
panels=$(sudo -u postgres psql -d parking_db -t -c "SELECT ip FROM panels;")

for panel_ip in $panels; do
    echo -n "Panel $panel_ip: "
    if ping -c 1 -W 5 $panel_ip > /dev/null 2>&1; then
        echo "PING OK"
        if curl -s --connect-timeout 5 http://$panel_ip/update > /dev/null; then
            echo "  HTTP OK"
        else
            echo "  HTTP FAIL"
        fi
    else
        echo "PING FAIL"
    fi
done

# Verificar puertos
echo -e "\nVerificación de puertos:"
for port in 6001 6400 5432; do
    if netstat -tlnp | grep ":$port " > /dev/null; then
        echo "Puerto $port: ABIERTO"
    else
        echo "Puerto $port: CERRADO"
    fi
done
```

## Alertas y Notificaciones

### 1. Configuración de Alertas por Email

```bash
# Instalar y configurar mail
apt install -y mailutils

# Configurar postfix
echo "postfix postfix/mailname string parking-altea.local" | debconf-set-selections
echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
apt install -y postfix

# Configurar alias para root
echo "root: admin@swat-id.com" >> /etc/aliases
newaliases
```

### 2. Alertas por Telegram (Opcional)

```bash
# Script para alertas por Telegram
cat > /opt/parking_altea/telegram_alert.sh <<'EOF'
#!/bin/bash

BOT_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"
MESSAGE="$1"

curl -s -X POST \
    https://api.telegram.org/bot$BOT_TOKEN/sendMessage \
    -d chat_id=$CHAT_ID \
    -d text="$MESSAGE" \
    -d parse_mode=HTML
EOF

chmod +x /opt/parking_altea/telegram_alert.sh
```

## Reportes Automáticos

### 1. Reporte Diario

```bash
# Script de reporte diario
cat > /opt/parking_altea/daily_report.sh <<'EOF'
#!/bin/bash

REPORT_FILE="/var/log/parking-altea/daily_report_$(date +%Y%m%d).txt"

echo "=== Reporte Diario Parking Altea - $(date) ===" > $REPORT_FILE

# Estado de servicios
echo -e "\n1. Estado de Servicios:" >> $REPORT_FILE
systemctl is-active parking-api.service >> $REPORT_FILE
systemctl is-active parking-camera.service >> $REPORT_FILE
systemctl is-active postgresql >> $REPORT_FILE

# Estadísticas de uso
echo -e "\n2. Estadísticas de Uso:" >> $REPORT_FILE
echo "Mensajes de cámaras (hoy): $(journalctl -u parking-camera.service --since "today" | grep -c POST)" >> $REPORT_FILE
echo "Consultas API (hoy): $(journalctl -u parking-api.service --since "today" | grep -c "GET\|POST")" >> $REPORT_FILE

# Uso de recursos
echo -e "\n3. Uso de Recursos:" >> $REPORT_FILE
free -h >> $REPORT_FILE
df -h / >> $REPORT_FILE

# Enviar reporte por email
cat $REPORT_FILE | mail -s "Reporte Diario Parking Altea - $(date +%Y-%m-%d)" admin@swat-id.com
EOF

chmod +x /opt/parking_altea/daily_report.sh
```

### 2. Reporte Semanal

```bash
# Script de reporte semanal
cat > /opt/parking_altea/weekly_report.sh <<'EOF'
#!/bin/bash

REPORT_FILE="/var/log/parking-altea/weekly_report_$(date +%Y%m%d).txt"

echo "=== Reporte Semanal Parking Altea - $(date) ===" > $REPORT_FILE

# Estadísticas de ocupación
echo -e "\n1. Estadísticas de Ocupación:" >> $REPORT_FILE
sudo -u postgres psql -d parking_db -c "
SELECT 
    p.name,
    AVG(oh.occupancy) as avg_occupancy,
    MAX(oh.occupancy) as max_occupancy,
    COUNT(oh.id) as registros
FROM parkings p
LEFT JOIN occupancy_history oh ON p.id = oh.parking_id
WHERE oh.timestamp >= NOW() - INTERVAL '7 days'
GROUP BY p.id, p.name
ORDER BY avg_occupancy DESC;
" >> $REPORT_FILE

# Errores de la semana
echo -e "\n2. Errores de la Semana:" >> $REPORT_FILE
journalctl -u parking-api.service -p err --since "7 days ago" --no-pager >> $REPORT_FILE
journalctl -u parking-camera.service -p err --since "7 days ago" --no-pager >> $REPORT_FILE

# Enviar reporte
cat $REPORT_FILE | mail -s "Reporte Semanal Parking Altea - $(date +%Y-%m-%d)" admin@swat-id.com
EOF

chmod +x /opt/parking_altea/weekly_report.sh
```

## Documentación de Incidentes

### Plantilla de Incidente

```bash
# Crear plantilla para documentar incidentes
cat > /opt/parking_altea/incident_template.md <<'EOF'
# Incidente Parking Altea

## Información Básica
- **Fecha y Hora**: 
- **Reportado por**: 
- **Prioridad**: [BAJA/MEDIA/ALTA/CRÍTICA]
- **Estado**: [ABIERTO/EN_PROGRESO/RESUELTO/CERRADO]

## Descripción del Problema
[Descripción detallada del incidente]

## Impacto
[Descripción del impacto en el servicio]

## Acciones Tomadas
1. [Acción 1]
2. [Acción 2]
3. [Acción 3]

## Causa Raíz
[Análisis de la causa del problema]

## Solución Implementada
[Descripción de la solución]

## Prevención
[Medidas para prevenir futuros incidentes similares]

## Lecciones Aprendidas
[Lecciones aprendidas del incidente]

## Cierre
- **Fecha de Cierre**: 
- **Cerrado por**: 
- **Verificación**: 
EOF
```

## Gestión de Descuadres y Correcciones

### Tipos de Descuadres

El sistema permite y registra automáticamente los siguientes descuadres:

1. **Exceso de Ocupación**: Cuando hay más vehículos que plazas disponibles
   - Estado: `COMPLETO_EXCESO`
   - Causas: Exceso real de vehículos, capacidad subestimada

2. **Plazas Libres Negativas**: Cuando el conteo indica más vehículos que capacidad
   - Estado: `DESCUADRE_NEGATIVO`
   - Causas: Errores de conteo, problemas en cámaras, overflow

### Análisis de Descuadres

El sistema incluye un script de análisis que genera estadísticas y sugerencias:

```bash
# Analizar descuadres de los últimos 7 días
python src/analyze_discrepancies.py analyze 7

# Generar sugerencias de corrección
python src/analyze_discrepancies.py suggestions

# Exportar reporte CSV
python src/analyze_discrepancies.py export reporte.csv
```

### Correcciones Automáticas

#### 1. Corrección de Excesos Menores (≤5 vehículos)
```bash
curl -X POST http://157.180.91.63:6001/parking/{id}/occupancy \
  -H 'Content-Type: application/json' \
  -d '{"occupancy": CAPACIDAD_MAXIMA}'
```

#### 2. Ajuste de Capacidad para Excesos Mayores
```bash
curl -X POST http://157.180.91.63:6001/parking/{id}/config \
  -H 'Content-Type: application/json' \
  -d '{"max_capacity": NUEVA_CAPACIDAD}'
```

#### 3. Corrección de Descuadres Negativos
```bash
# Para descuadres menores (≤10 vehículos)
curl -X POST http://157.180.91.63:6001/parking/{id}/occupancy \
  -H 'Content-Type: application/json' \
  -d '{"occupancy": CAPACIDAD_MAXIMA}'
```

### Monitoreo Continuo

#### Logs de Descuadres
Los descuadres se registran automáticamente en los logs:

```bash
# Ver logs de descuadres en tiempo real
journalctl -u parking-camera.service -f | grep -E "(EXCESS|NEGATIVE|DESCUADRE)"

# Ver logs de la API
journalctl -u parking-api.service -f | grep -E "(EXCESS|NEGATIVE|DESCUADRE)"
```

#### Alertas Recomendadas
- **Excesos > 10% de registros**: Revisar capacidad del parking
- **Descuadres negativos > 5% de registros**: Revisar sistema de conteo
- **Tendencias significativas**: Analizar cambios en patrones de uso

### Mantenimiento Preventivo

#### Revisión Diaria
1. Ejecutar análisis de descuadres
2. Revisar parkings con estados especiales
3. Aplicar correcciones sugeridas

#### Revisión Semanal
1. Exportar reporte de descuadres
2. Analizar tendencias
3. Ajustar capacidades si es necesario

#### Revisión Mensual
1. Auditoría completa del sistema
2. Revisión de precisión de cámaras
3. Optimización de umbrales

## Mantenimiento del Sistema

### Servicios del Sistema

El sistema consta de dos servicios principales:

1. **parking-api.service**: API REST en puerto 6001
2. **parking-camera.service**: Servidor de cámaras en puerto 6400

### Comandos de Mantenimiento

#### Reiniciar Servicios
```bash
sudo systemctl restart parking-api.service
sudo systemctl restart parking-camera.service
```

#### Ver Estado de Servicios
```bash
sudo systemctl status parking-api.service
sudo systemctl status parking-camera.service
```

#### Ver Logs en Tiempo Real
```bash
# API Server
sudo journalctl -u parking-api.service -f

# Camera Server
sudo journalctl -u parking-camera.service -f
```

#### Ver Logs Históricos
```bash
# Últimas 100 líneas
sudo journalctl -u parking-api.service -n 100

# Desde hace 1 hora
sudo journalctl -u parking-api.service --since "1 hour ago"
```

### Base de Datos

#### Backup Automático
```bash
# Crear backup
pg_dump parking_altea > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
psql parking_altea < backup_YYYYMMDD_HHMMSS.sql
```

#### Limpieza de Histórico
```bash
# Eliminar registros antiguos (más de 90 días)
DELETE FROM occupancy_history 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

### Monitoreo de Recursos

#### Uso de CPU y Memoria
```bash
# Ver uso de recursos
htop

# Ver procesos específicos
ps aux | grep python
```

#### Uso de Disco
```bash
# Ver espacio en disco
df -h

# Ver logs más grandes
du -sh /var/log/*
```

### Actualizaciones

#### Actualizar Código
```bash
cd /opt/parking_altea
git pull origin main
sudo systemctl restart parking-api.service
sudo systemctl restart parking-camera.service
```

#### Verificar Funcionamiento
```bash
# Probar API
curl http://157.180.91.63:6001/parkings

# Probar servidor de cámaras
curl http://157.180.91.63:6400/camera
```

### Troubleshooting

#### Problemas Comunes

1. **Servicio no inicia**
   ```bash
   sudo systemctl status parking-api.service
   sudo journalctl -u parking-api.service -n 50
   ```

2. **Error de conexión a base de datos**
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -c "SELECT version();"
   ```

3. **Puertos ocupados**
   ```bash
   sudo netstat -tlnp | grep :6001
   sudo netstat -tlnp | grep :6400
   ```

#### Logs de Error
```bash
# Ver errores específicos
sudo journalctl -u parking-api.service -p err
sudo journalctl -u parking-camera.service -p err
``` 