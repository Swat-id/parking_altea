# Comandos Manuales Completos - Despliegue v4.0.0 Sin Scripts

## 🎯 Despliegue Manual Paso a Paso

**Todos los comandos necesarios para desplegar la nueva lógica v4.0.0 SIN usar scripts automatizados.**

---

## 📋 SECUENCIA COMPLETA DE COMANDOS

### 🔌 **PASO 1: Conexión y Navegación**

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Navegar al directorio del proyecto
cd /opt/parking

# Verificar ubicación actual
pwd

# Verificar contenido del directorio
ls -la

# Verificar rama actual de Git
git branch

# Verificar estado del repositorio
git status
```

### 💾 **PASO 2: Backup Manual del Estado Actual**

```bash
# Crear directorio de backup con fecha
mkdir -p /opt/parking/backups/$(date +%Y%m%d_%H%M%S)

# Definir variable para el directorio de backup
BACKUP_DIR="/opt/parking/backups/$(date +%Y%m%d_%H%M%S)"

# Backup del archivo principal
cp src/camera_server.py $BACKUP_DIR/camera_server.py.backup

# Backup de configuración si existe
cp config.py $BACKUP_DIR/config.py.backup 2>/dev/null || echo "config.py no encontrado"

# Backup de logs actuales del servicio
journalctl -u parking-camera.service --since "24 hours ago" > $BACKUP_DIR/camera_service_logs_pre_deployment.log

# Backup del estado del servicio
systemctl status parking-camera.service > $BACKUP_DIR/service_status_pre_deployment.txt

# Verificar backups creados
ls -la $BACKUP_DIR/

# Mostrar directorio de backup para referencia
echo "✅ Backup creado en: $BACKUP_DIR"
```

### 🔍 **PASO 3: Verificación del Estado Actual**

```bash
# Verificar estado del servicio
systemctl status parking-camera.service

# Verificar que el servicio está activo
systemctl is-active parking-camera.service

# Verificar puerto en uso
netstat -tlnp | grep 6400

# Verificar logs recientes
journalctl -u parking-camera.service --since "10 minutes ago" --no-pager

# Verificar conectividad del endpoint
curl -s -w "HTTP Status: %{http_code}\n" http://localhost:6400/camera

# Verificar procesos relacionados
ps aux | grep camera_server
```

### 🔄 **PASO 4: Actualización desde Git**

```bash
# Guardar cambios locales si los hay
git stash push -m "Backup antes de despliegue v4.0.0 - $(date)"

# Verificar que el stash se creó
git stash list

# Cambiar a la rama v4.0.0
git checkout v4.0.0

# Verificar que estamos en la rama correcta
git branch

# Actualizar desde el repositorio remoto
git fetch origin

# Hacer pull de los últimos cambios
git pull origin v4.0.0

# Verificar el último commit
git log --oneline -5

# Verificar que tenemos el commit de implementación v4.0.0
git log --grep="Implementar nueva lógica de cálculo de deltas v4.0.0" --oneline

# Verificar estado después del pull
git status
```

### ✅ **PASO 5: Verificación de Archivos Actualizados**

```bash
# Verificar archivo principal modificado
ls -la src/camera_server.py

# Verificar que contiene el feature flag
grep -n "USE_NEW_DELTA_LOGIC" src/camera_server.py

# Verificar que está configurado como True
grep -n "USE_NEW_DELTA_LOGIC = True" src/camera_server.py

# Verificar que las nuevas funciones están presentes
grep -n "def detect_camera_reset_new_logic" src/camera_server.py
grep -n "def calculate_deltas_new_logic" src/camera_server.py
grep -n "def validate_delta_thresholds" src/camera_server.py

# Verificar archivos de tests
ls -la test/test_delta_calculation_v4_0_0.py

# Verificar documentación
ls -la docs/v4.0.0/

# Verificar scripts de despliegue (aunque no los usemos)
ls -la deploy/deploy_v4_0_0_nueva_logica_deltas.sh
ls -la deploy/test_v4_0_0_camera_server.sh
```

### 🛑 **PASO 6: Parada del Servicio**

```bash
# Parar el servicio de cámaras
systemctl stop parking-camera.service

# Verificar que se detuvo correctamente
systemctl is-active parking-camera.service

# Verificar que no hay procesos residuales
ps aux | grep camera_server

# Si hay procesos residuales, terminarlos
pkill -f camera_server

# Verificar que el puerto se liberó
netstat -tlnp | grep 6400

# Esperar un momento para asegurar limpieza completa
sleep 3
```

### 🔧 **PASO 7: Verificación de Dependencias**

```bash
# Verificar Python y versión
python3 --version

# Verificar que los módulos necesarios están disponibles
python3 -c "import flask; print('Flask OK')"
python3 -c "import sqlalchemy; print('SQLAlchemy OK')"
python3 -c "import psycopg2; print('psycopg2 OK')"

# Verificar conexión a base de datos
python3 -c "
import sys
sys.path.append('/opt/parking/src')
try:
    import config
    from sqlalchemy import create_engine
    engine = create_engine(config.DB_URL)
    conn = engine.connect()
    conn.close()
    print('Database connection OK')
except Exception as e:
    print(f'Database connection ERROR: {e}')
"

# Verificar archivos de configuración
ls -la src/config.py
ls -la src/models.py
```

### 🚀 **PASO 8: Inicio del Servicio con Nueva Lógica**

```bash
# Iniciar el servicio
systemctl start parking-camera.service

# Verificar que inició correctamente
systemctl is-active parking-camera.service

# Verificar estado detallado
systemctl status parking-camera.service

# Esperar unos segundos para que se estabilice
sleep 10

# Verificar logs de inicio
journalctl -u parking-camera.service --since "2 minutes ago" --no-pager

# Verificar que la nueva lógica está activa
journalctl -u parking-camera.service --since "2 minutes ago" | grep "NEW DELTA LOGIC ENABLED"

# Verificar que no hay errores críticos
journalctl -u parking-camera.service --since "2 minutes ago" | grep -i error

# Verificar que el puerto está activo
netstat -tlnp | grep 6400

# Verificar proceso en ejecución
ps aux | grep camera_server
```

### 🧪 **PASO 9: Tests Manuales de Funcionalidad**

```bash
# Test 1: Verificar endpoint básico
echo "=== Test 1: Endpoint básico ==="
curl -s -w "HTTP Status: %{http_code}\n" http://localhost:6400/camera

# Test 2: Enviar mensaje de prueba normal
echo "=== Test 2: Mensaje normal ==="
curl -X POST http://localhost:6400/camera \
  -H "Content-Type: application/json" \
  -d '{
    "device": "TEST_CAMERA_MANUAL",
    "line": 0,
    "Vehicle In": 100,
    "Vehicle Out": 95,
    "event": "test_manual_normal",
    "time": "'$(date -Iseconds)'"
  }' \
  -w "HTTP Status: %{http_code}\n"

# Verificar procesamiento en logs
sleep 2
journalctl -u parking-camera.service --since "1 minute ago" | grep "NEW LOGIC - Delta final"

# Test 3: Enviar mensaje duplicado
echo "=== Test 3: Mensaje duplicado ==="
curl -X POST http://localhost:6400/camera \
  -H "Content-Type: application/json" \
  -d '{
    "device": "TEST_CAMERA_MANUAL",
    "line": 0,
    "Vehicle In": 100,
    "Vehicle Out": 95,
    "event": "test_manual_duplicate",
    "time": "'$(date -Iseconds)'"
  }' \
  -w "HTTP Status: %{http_code}\n"

# Verificar detección de duplicado
sleep 2
journalctl -u parking-camera.service --since "1 minute ago" | grep "DUPLICATE MESSAGE DETECTED (NEW LOGIC)"

# Test 4: Simular reinicio de cámara
echo "=== Test 4: Reinicio de cámara ==="
curl -X POST http://localhost:6400/camera \
  -H "Content-Type: application/json" \
  -d '{
    "device": "TEST_CAMERA_MANUAL",
    "line": 0,
    "Vehicle In": 5,
    "Vehicle Out": 2,
    "event": "test_manual_reset",
    "time": "'$(date -Iseconds)'"
  }' \
  -w "HTTP Status: %{http_code}\n"

# Verificar detección de reinicio
sleep 2
journalctl -u parking-camera.service --since "1 minute ago" | grep "Reset detected (NEW LOGIC)"
journalctl -u parking-camera.service --since "1 minute ago" | grep "Using absolute difference"
```

### 📊 **PASO 10: Verificación de Métricas y Estadísticas**

```bash
# Contar mensajes procesados con nueva lógica
echo "=== Estadísticas de Procesamiento ==="
PROCESSED_COUNT=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -c "NEW LOGIC - Delta final" || echo "0")
echo "Mensajes procesados con nueva lógica: $PROCESSED_COUNT"

# Contar reinicios detectados
RESET_COUNT=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -c "Reset detected (NEW LOGIC)" || echo "0")
echo "Reinicios detectados: $RESET_COUNT"

# Contar duplicados detectados
DUPLICATE_COUNT=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -c "DUPLICATE MESSAGE DETECTED (NEW LOGIC)" || echo "0")
echo "Duplicados detectados: $DUPLICATE_COUNT"

# Contar errores
ERROR_COUNT=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -i -c "error\|exception" || echo "0")
echo "Errores detectados: $ERROR_COUNT"

# Verificar tiempo de respuesta
echo "=== Test de Rendimiento ==="
time curl -s http://localhost:6400/camera > /dev/null

# Verificar uso de memoria del proceso
echo "=== Uso de Recursos ==="
ps aux | grep camera_server | grep -v grep
```

### 🔍 **PASO 11: Verificación de Base de Datos**

```bash
# Conectar a PostgreSQL y verificar datos
echo "=== Verificación de Base de Datos ==="

# Verificar conexión a la base de datos
sudo -u postgres psql -c "SELECT version();"

# Verificar ocupaciones actuales de parkings
sudo -u postgres psql parking_db -c "
SELECT 
    name, 
    current_occupancy, 
    max_capacity,
    status,
    ROUND((current_occupancy::float / max_capacity * 100), 2) as ocupacion_porcentaje
FROM parkings 
ORDER BY name;
"

# Verificar últimos registros de cámaras
sudo -u postgres psql parking_db -c "
SELECT 
    camera_name,
    vehicle_in,
    vehicle_out,
    status,
    processed_at
FROM camera_logs 
WHERE processed_at > NOW() - INTERVAL '1 hour'
ORDER BY processed_at DESC 
LIMIT 10;
"

# Verificar histórico de ocupación reciente
sudo -u postgres psql parking_db -c "
SELECT 
    p.name,
    oh.occupancy,
    oh.timestamp,
    oh.source
FROM occupancy_history oh
JOIN parkings p ON oh.parking_id = p.id
WHERE oh.timestamp > NOW() - INTERVAL '1 hour'
ORDER BY oh.timestamp DESC 
LIMIT 10;
"
```

### 📈 **PASO 12: Monitorización Continua**

```bash
# Crear script de monitorización manual
cat > /tmp/monitor_v4_0_0_manual.sh << 'EOF'
#!/bin/bash
echo "=== MONITORIZACIÓN NUEVA LÓGICA v4.0.0 - $(date) ==="
echo

# Estado del servicio
echo "🔧 Estado del servicio:"
systemctl is-active parking-camera.service
echo

# Estadísticas de procesamiento
echo "📊 Estadísticas (últimas 24h):"
PROCESSED=$(journalctl -u parking-camera.service --since "24 hours ago" | grep -c "NEW LOGIC - Delta final" || echo "0")
RESETS=$(journalctl -u parking-camera.service --since "24 hours ago" | grep -c "Reset detected (NEW LOGIC)" || echo "0")
DUPLICATES=$(journalctl -u parking-camera.service --since "24 hours ago" | grep -c "DUPLICATE MESSAGE DETECTED (NEW LOGIC)" || echo "0")
ERRORS=$(journalctl -u parking-camera.service --since "24 hours ago" | grep -i -c "error.*new logic" || echo "0")

echo "- Mensajes procesados: $PROCESSED"
echo "- Reinicios detectados: $RESETS"
echo "- Duplicados detectados: $DUPLICATES"
echo "- Errores: $ERRORS"
echo

# Uso de recursos
echo "💾 Uso de recursos:"
ps aux | grep camera_server | grep -v grep | awk '{print "CPU: "$3"%, MEM: "$4"%, PID: "$2}'
echo

# Conectividad
echo "🌐 Conectividad:"
curl -s -w "Endpoint status: %{http_code}\n" http://localhost:6400/camera -o /dev/null
echo

echo "=== FIN MONITORIZACIÓN ==="
EOF

# Hacer ejecutable el script
chmod +x /tmp/monitor_v4_0_0_manual.sh

# Ejecutar monitorización
/tmp/monitor_v4_0_0_manual.sh

# Programar monitorización cada 15 minutos (opcional)
echo "Para monitorización continua, ejecutar:"
echo "watch -n 900 '/tmp/monitor_v4_0_0_manual.sh'"
```

### 📝 **PASO 13: Configuración de Logs Permanentes**

```bash
# Crear directorio para logs específicos de v4.0.0
mkdir -p /opt/parking/logs/v4_0_0

# Crear script para capturar logs de nueva lógica
cat > /opt/parking/logs/v4_0_0/capture_new_logic_logs.sh << 'EOF'
#!/bin/bash
LOG_FILE="/opt/parking/logs/v4_0_0/new_logic_$(date +%Y%m%d).log"
journalctl -u parking-camera.service --since "1 hour ago" | grep "NEW LOGIC" >> $LOG_FILE
journalctl -u parking-camera.service --since "1 hour ago" | grep "Reset detected (NEW LOGIC)" >> $LOG_FILE
journalctl -u parking-camera.service --since "1 hour ago" | grep "DUPLICATE MESSAGE DETECTED (NEW LOGIC)" >> $LOG_FILE
echo "$(date): Logs captured to $LOG_FILE"
EOF

chmod +x /opt/parking/logs/v4_0_0/capture_new_logic_logs.sh

# Ejecutar captura inicial
/opt/parking/logs/v4_0_0/capture_new_logic_logs.sh

# Mostrar logs capturados
ls -la /opt/parking/logs/v4_0_0/
```

---

## 🚨 COMANDOS DE ROLLBACK MANUAL (Si hay problemas)

### 🔄 **Opción 1: Rollback por Feature Flag (Más Rápido)**

```bash
echo "🔄 Iniciando rollback por feature flag..."

# Parar servicio
systemctl stop parking-camera.service

# Cambiar feature flag a False
sed -i 's/USE_NEW_DELTA_LOGIC = True/USE_NEW_DELTA_LOGIC = False/g' src/camera_server.py

# Verificar el cambio
grep -n "USE_NEW_DELTA_LOGIC" src/camera_server.py

# Reiniciar servicio
systemctl start parking-camera.service

# Verificar que usa lógica legacy
sleep 5
journalctl -u parking-camera.service --since "1 minute ago" | grep "LEGACY DELTA LOGIC ENABLED"

echo "✅ Rollback por feature flag completado"
```

### 🔄 **Opción 2: Rollback Completo desde Backup**

```bash
echo "🔄 Iniciando rollback completo desde backup..."

# Parar servicio
systemctl stop parking-camera.service

# Restaurar backup (usar el directorio creado en PASO 2)
# Reemplazar BACKUP_DIR con el directorio real
BACKUP_DIR="/opt/parking/backups/YYYYMMDD_HHMMSS"  # Ajustar con directorio real
cp $BACKUP_DIR/camera_server.py.backup src/camera_server.py

# Verificar restauración
ls -la src/camera_server.py
grep -n "USE_NEW_DELTA_LOGIC" src/camera_server.py || echo "Feature flag no encontrado (versión original)"

# Reiniciar servicio
systemctl start parking-camera.service

# Verificar estado
systemctl status parking-camera.service

echo "✅ Rollback completo desde backup completado"
```

### 🔄 **Opción 3: Rollback por Git**

```bash
echo "🔄 Iniciando rollback por Git..."

# Parar servicio
systemctl stop parking-camera.service

# Ver commits recientes
git log --oneline -5

# Revertir al commit anterior a la implementación v4.0.0
git reset --hard d3f8e64  # Commit anterior a v4.0.0

# O revertir el commit específico
# git revert 9ae9976 --no-edit

# Verificar estado
git status
git log --oneline -3

# Reiniciar servicio
systemctl start parking-camera.service

# Verificar estado
systemctl status parking-camera.service

echo "✅ Rollback por Git completado"
```

---

## ✅ VERIFICACIÓN FINAL DE ÉXITO

### **El despliegue es exitoso cuando todos estos comandos muestren resultados positivos:**

```bash
echo "=== VERIFICACIÓN FINAL DE ÉXITO ==="

# 1. Servicio activo
echo "1. Estado del servicio:"
systemctl is-active parking-camera.service

# 2. Nueva lógica activa
echo "2. Nueva lógica activa:"
journalctl -u parking-camera.service --since "10 minutes ago" | grep -q "NEW DELTA LOGIC ENABLED" && echo "✅ SÍ" || echo "❌ NO"

# 3. Endpoint responde
echo "3. Endpoint responde:"
curl -s -f http://localhost:6400/camera > /dev/null && echo "✅ SÍ" || echo "❌ NO"

# 4. Mensajes procesándose
echo "4. Mensajes procesándose con nueva lógica:"
COUNT=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -c "NEW LOGIC - Delta final" || echo "0")
echo "Mensajes procesados: $COUNT"

# 5. Sin errores críticos
echo "5. Sin errores críticos:"
ERROR_COUNT=$(journalctl -u parking-camera.service --since "10 minutes ago" | grep -i -c "error\|exception" || echo "0")
echo "Errores encontrados: $ERROR_COUNT"

# 6. Puerto activo
echo "6. Puerto 6400 activo:"
netstat -tlnp | grep -q 6400 && echo "✅ SÍ" || echo "❌ NO"

echo "=== FIN VERIFICACIÓN ==="

# Resumen final
if systemctl is-active parking-camera.service > /dev/null && \
   journalctl -u parking-camera.service --since "10 minutes ago" | grep -q "NEW DELTA LOGIC ENABLED" && \
   curl -s -f http://localhost:6400/camera > /dev/null; then
    echo
    echo "🎉 ¡DESPLIEGUE v4.0.0 EXITOSO!"
    echo "✅ Nueva lógica de cálculo de deltas activa y funcionando"
else
    echo
    echo "⚠️  VERIFICAR DESPLIEGUE - Algunos tests fallaron"
    echo "Revisar logs: journalctl -u parking-camera.service --since '10 minutes ago'"
fi
```

---

## 📋 CHECKLIST MANUAL DE DESPLIEGUE

**Marcar cada paso completado:**

### Pre-Despliegue:
- [ ] Conectado al servidor (ssh root@157.180.91.63)
- [ ] Navegado al directorio (/opt/parking)
- [ ] Backup creado del estado actual
- [ ] Estado del servicio verificado (activo)

### Actualización:
- [ ] Cambios locales guardados (git stash)
- [ ] Rama v4.0.0 activada
- [ ] Código actualizado desde Git (git pull)
- [ ] Archivos de implementación verificados

### Despliegue:
- [ ] Servicio detenido correctamente
- [ ] Dependencias verificadas
- [ ] Servicio reiniciado con nueva lógica
- [ ] Nueva lógica activa confirmada en logs

### Verificación:
- [ ] Tests manuales ejecutados (normal, duplicado, reinicio)
- [ ] Estadísticas de procesamiento verificadas
- [ ] Base de datos funcionando correctamente
- [ ] Monitorización configurada

### Post-Despliegue:
- [ ] Verificación final exitosa
- [ ] Scripts de rollback preparados
- [ ] Logs de nueva lógica capturados
- [ ] Sistema funcionando establemente

---

**🎯 TODOS LOS COMANDOS MANUALES LISTOS PARA EJECUCIÓN**

*Ejecutar comando por comando, verificando cada resultado antes de continuar.*
