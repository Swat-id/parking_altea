# Guía de Despliegue en Producción - Nueva Lógica de Deltas v4.0.0

## 📋 Información del Documento

- **Rama**: v4.0.0
- **Fecha**: 12 de septiembre de 2025
- **Propósito**: Guía paso a paso para desplegar la nueva lógica de cálculo de deltas en producción
- **Estado**: Lista para ejecución

---

## 🎯 Resumen del Despliegue

Esta guía proporciona **todos los comandos exactos** para desplegar la nueva lógica de cálculo de deltas v4.0.0 en el servidor de producción, incluyendo:

- ✅ Actualización desde Git
- ✅ Backup del estado actual
- ✅ Despliegue automatizado
- ✅ Verificación funcional
- ✅ Monitorización post-despliegue
- ✅ Procedimientos de rollback

---

## 🚨 Pre-requisitos

### Antes de comenzar:
- [x] Acceso SSH al servidor de producción
- [x] Permisos sudo en el servidor
- [x] Servicio `parking-camera.service` funcionando
- [x] Git configurado en el servidor

### Información del servidor:
- **IP**: 157.180.91.63
- **Usuario**: root
- **Servicio**: parking-camera.service
- **Puerto**: 6400
- **Directorio**: /opt/parking/ (asumir ubicación estándar)

---

## 📝 COMANDOS PASO A PASO

### 🔌 PASO 1: Conexión al Servidor

```bash
# Conectar al servidor de producción
ssh root@157.180.91.63
```

### 📁 PASO 2: Navegación al Directorio del Proyecto

```bash
# Navegar al directorio del proyecto
cd /opt/parking

# Verificar que estamos en el directorio correcto
pwd
ls -la

# Verificar rama actual
git branch
```

### 💾 PASO 3: Backup del Estado Actual

```bash
# Crear directorio de backup si no existe
mkdir -p /opt/parking/backups/$(date +%Y%m%d)

# Backup del archivo principal
cp src/camera_server.py /opt/parking/backups/$(date +%Y%m%d)/camera_server.py.backup.$(date +%H%M%S)

# Verificar estado del servicio antes del despliegue
systemctl status parking-camera.service

# Backup de logs actuales
journalctl -u parking-camera.service --since "24 hours ago" > /opt/parking/backups/$(date +%Y%m%d)/camera_service_logs_pre_deployment.log

echo "✅ Backup completado en /opt/parking/backups/$(date +%Y%m%d)/"
```

### 🔄 PASO 4: Actualización desde Git

```bash
# Verificar estado actual del repositorio
git status

# Guardar cambios locales si los hay (stash)
git stash

# Cambiar a la rama v4.0.0
git checkout v4.0.0

# Actualizar desde el repositorio remoto
git pull origin v4.0.0

# Verificar que tenemos la última versión
git log --oneline -3

# Verificar que el commit de implementación está presente
git log --grep="Implementar nueva lógica de cálculo de deltas v4.0.0" --oneline
```

### 🔍 PASO 5: Verificación de Archivos

```bash
# Verificar que los archivos necesarios están presentes
echo "🔍 Verificando archivos de la implementación v4.0.0..."

# Archivo principal
ls -la src/camera_server.py

# Scripts de despliegue
ls -la deploy/deploy_v4_0_0_nueva_logica_deltas.sh
ls -la deploy/test_v4_0_0_camera_server.sh

# Tests
ls -la test/test_delta_calculation_v4_0_0.py

# Documentación
ls -la docs/v4.0.0/

echo "✅ Verificación de archivos completada"
```

### 🔧 PASO 6: Preparación de Scripts

```bash
# Hacer ejecutables los scripts de despliegue
chmod +x deploy/deploy_v4_0_0_nueva_logica_deltas.sh
chmod +x deploy/test_v4_0_0_camera_server.sh

# Verificar permisos
ls -la deploy/deploy_v4_0_0_nueva_logica_deltas.sh
ls -la deploy/test_v4_0_0_camera_server.sh

echo "✅ Scripts preparados"
```

### 🚀 PASO 7: Despliegue Automatizado

```bash
echo "🚀 Iniciando despliegue automatizado v4.0.0..."

# Ejecutar script de despliegue
./deploy/deploy_v4_0_0_nueva_logica_deltas.sh

# El script hará automáticamente:
# - Backup adicional
# - Verificación de feature flag
# - Reinicio del servicio
# - Verificación de estado
# - Configuración de monitorización
# - Creación de scripts de rollback
```

### ✅ PASO 8: Verificación Post-Despliegue

```bash
echo "🔍 Verificando despliegue..."

# Verificar estado del servicio
systemctl status parking-camera.service

# Verificar que la nueva lógica está activa
journalctl -u parking-camera.service --since "5 minutes ago" | grep "NEW DELTA LOGIC ENABLED"

# Verificar conectividad del endpoint
curl -s http://localhost:6400/camera

echo "✅ Verificación básica completada"
```

### 🧪 PASO 9: Tests Funcionales

```bash
echo "🧪 Ejecutando tests funcionales..."

# Ejecutar suite completa de tests
./deploy/test_v4_0_0_camera_server.sh

# Los tests verificarán:
# - Estado del servicio
# - Activación de nueva lógica
# - Conectividad
# - Procesamiento de mensajes normales
# - Detección de duplicados
# - Manejo de reinicios
# - Rendimiento básico
```

### 📊 PASO 10: Monitorización Inicial

```bash
echo "📊 Iniciando monitorización..."

# Logs en tiempo real (ejecutar en terminal separado)
journalctl -u parking-camera.service -f &

# Estadísticas de la nueva lógica
/opt/parking/scripts/monitor_v4_0_0.sh

# Verificar procesamiento en los últimos 10 minutos
journalctl -u parking-camera.service --since "10 minutes ago" | grep "NEW LOGIC - Delta final" | wc -l

echo "✅ Monitorización configurada"
```

---

## 📋 COMANDOS DE VERIFICACIÓN CONTINUA

### Durante las primeras 2 horas:

```bash
# Cada 15 minutos, ejecutar:
echo "=== VERIFICACIÓN $(date) ==="

# Estado del servicio
systemctl is-active parking-camera.service

# Mensajes procesados con nueva lógica
journalctl -u parking-camera.service --since "15 minutes ago" | grep -c "NEW LOGIC - Delta final"

# Reinicios detectados
journalctl -u parking-camera.service --since "15 minutes ago" | grep -c "Reset detected (NEW LOGIC)"

# Errores críticos
journalctl -u parking-camera.service --since "15 minutes ago" | grep -i -c "error\|exception"

# Tiempo de respuesta (test rápido)
time curl -s http://localhost:6400/camera > /dev/null

echo "=== FIN VERIFICACIÓN ==="
echo
```

### Comando de monitorización completa:

```bash
# Ejecutar cada hora durante las primeras 24 horas
/opt/parking/scripts/monitor_v4_0_0.sh
```

---

## 🔄 COMANDOS DE ROLLBACK (Si es necesario)

### Opción 1: Rollback Rápido (Feature Flag)

```bash
echo "🔄 Ejecutando rollback rápido..."

# Usar script automatizado
/opt/parking/scripts/rollback_v4_0_0.sh

# Seleccionar opción 1 cuando pregunte
# Esto cambiará USE_NEW_DELTA_LOGIC = False
```

### Opción 2: Rollback Manual (Feature Flag)

```bash
echo "🔄 Rollback manual por feature flag..."

# Editar archivo
nano src/camera_server.py

# Cambiar línea 23:
# DE: USE_NEW_DELTA_LOGIC = True
# A:  USE_NEW_DELTA_LOGIC = False

# Reiniciar servicio
systemctl restart parking-camera.service

# Verificar que usa lógica legacy
journalctl -u parking-camera.service --since "1 minute ago" | grep "LEGACY DELTA LOGIC ENABLED"
```

### Opción 3: Rollback Completo (Restaurar Backup)

```bash
echo "🔄 Rollback completo desde backup..."

# Parar servicio
systemctl stop parking-camera.service

# Restaurar backup
cp /opt/parking/backups/$(date +%Y%m%d)/camera_server.py.backup.* src/camera_server.py

# Reiniciar servicio
systemctl start parking-camera.service

# Verificar estado
systemctl status parking-camera.service
```

### Opción 4: Rollback por Git

```bash
echo "🔄 Rollback por Git..."

# Revertir commit específico
git revert 9ae9976 --no-edit

# O resetear a commit anterior
git reset --hard d3f8e64

# Reiniciar servicio
systemctl restart parking-camera.service

# Verificar estado
systemctl status parking-camera.service
```

---

## 📊 COMANDOS DE MONITORIZACIÓN AVANZADA

### Análisis de rendimiento:

```bash
# Tiempo de respuesta promedio
for i in {1..10}; do
    time curl -s -X POST http://localhost:6400/camera \
        -H "Content-Type: application/json" \
        -d '{"device": "TEST", "line": 0, "Vehicle In": 100, "Vehicle Out": 95}' > /dev/null
    sleep 1
done
```

### Estadísticas detalladas:

```bash
echo "📊 ESTADÍSTICAS DETALLADAS v4.0.0"
echo "================================="

# Mensajes procesados por hora
for hour in {0..23}; do
    count=$(journalctl -u parking-camera.service --since "24 hours ago" --until "23 hours ago" | grep "NEW LOGIC - Delta final" | wc -l)
    echo "Hora $hour: $count mensajes"
done

# Tipos de procesamiento
echo
echo "Tipos de procesamiento (últimas 24h):"
echo "- Normales: $(journalctl -u parking-camera.service --since "24 hours ago" | grep -c "incremental_difference")"
echo "- Reinicios: $(journalctl -u parking-camera.service --since "24 hours ago" | grep -c "absolute_difference")"
echo "- Duplicados: $(journalctl -u parking-camera.service --since "24 hours ago" | grep -c "DUPLICATE MESSAGE DETECTED (NEW LOGIC)")"

# Deltas promedio
echo
echo "Análisis de deltas:"
journalctl -u parking-camera.service --since "24 hours ago" | grep "NEW LOGIC - Delta final" | awk '{print $NF}' | sort -n
```

### Verificación de ocupaciones:

```bash
# Conectar a la base de datos y verificar ocupaciones
psql -h localhost -U parking_user -d parking_db -c "
SELECT 
    name, 
    current_occupancy, 
    max_capacity,
    status,
    (current_occupancy::float / max_capacity * 100) as ocupacion_porcentaje
FROM parkings 
ORDER BY name;
"
```

---

## 🚨 COMANDOS DE EMERGENCIA

### Si el servicio no responde:

```bash
# Verificar procesos
ps aux | grep camera_server

# Verificar puertos
netstat -tlnp | grep 6400

# Logs de error del sistema
journalctl -u parking-camera.service --since "1 hour ago" -p err

# Reinicio forzado
systemctl stop parking-camera.service
sleep 5
systemctl start parking-camera.service
```

### Si hay problemas de memoria:

```bash
# Verificar uso de memoria
free -h
ps aux --sort=-%mem | head -10

# Verificar logs de memoria
dmesg | grep -i "killed process"
```

### Si la base de datos no responde:

```bash
# Verificar conexión a PostgreSQL
systemctl status postgresql
psql -h localhost -U parking_user -d parking_db -c "SELECT 1;"
```

---

## 📋 CHECKLIST DE DESPLIEGUE

### Pre-Despliegue:
- [ ] Conexión SSH al servidor establecida
- [ ] Backup del estado actual creado
- [ ] Repositorio Git actualizado a v4.0.0
- [ ] Scripts de despliegue preparados
- [ ] Servicio funcionando correctamente

### Durante el Despliegue:
- [ ] Script de despliegue ejecutado sin errores
- [ ] Servicio reiniciado correctamente
- [ ] Nueva lógica activada (logs confirman)
- [ ] Endpoint responde correctamente
- [ ] Tests funcionales pasados

### Post-Despliegue:
- [ ] Monitorización configurada
- [ ] Scripts de rollback disponibles
- [ ] Métricas iniciales recopiladas
- [ ] Documentación actualizada
- [ ] Stakeholders notificados

### Verificación Continua (Primeras 24h):
- [ ] Sin errores críticos en logs
- [ ] Ocupaciones actualizándose correctamente
- [ ] Rendimiento dentro de parámetros normales
- [ ] Reinicios manejados correctamente
- [ ] Duplicados detectados apropiadamente

---

## 📞 CONTACTOS Y SOPORTE

### En caso de problemas críticos:

1. **Rollback inmediato**: Ejecutar comandos de rollback
2. **Logs de debugging**: `journalctl -u parking-camera.service --since "1 hour ago"`
3. **Estado del sistema**: `systemctl status parking-camera.service`

### Archivos importantes:
- **Backup**: `/opt/parking/backups/$(date +%Y%m%d)/`
- **Logs**: `journalctl -u parking-camera.service`
- **Configuración**: `src/camera_server.py` (línea 23 - feature flag)
- **Scripts**: `/opt/parking/scripts/`

---

## 🎯 RESUMEN DE COMANDOS ESENCIALES

### Despliegue completo en una secuencia:

```bash
# 1. Conectar y preparar
ssh root@157.180.91.63
cd /opt/parking
mkdir -p /opt/parking/backups/$(date +%Y%m%d)
cp src/camera_server.py /opt/parking/backups/$(date +%Y%m%d)/camera_server.py.backup.$(date +%H%M%S)

# 2. Actualizar código
git stash
git checkout v4.0.0
git pull origin v4.0.0

# 3. Desplegar
chmod +x deploy/deploy_v4_0_0_nueva_logica_deltas.sh
./deploy/deploy_v4_0_0_nueva_logica_deltas.sh

# 4. Verificar
chmod +x deploy/test_v4_0_0_camera_server.sh
./deploy/test_v4_0_0_camera_server.sh

# 5. Monitorizar
journalctl -u parking-camera.service -f
```

### Rollback rápido si hay problemas:

```bash
/opt/parking/scripts/rollback_v4_0_0.sh
```

---

## 🎉 CONFIRMACIÓN DE ÉXITO

### El despliegue es exitoso cuando veas:

1. **En los logs**:
   ```
   🚀 CAMERA SERVER v4.0.0 - NEW DELTA LOGIC ENABLED
   Features: Immediate storage, unified delta calculation, improved reset handling
   ```

2. **En el procesamiento**:
   ```
   NEW LOGIC - Delta final: X, Is Reset: False
   Occupancy updated (NEW LOGIC) for parking...
   ```

3. **En los tests**:
   ```
   ✅ Tests pasados: X
   🎉 Todos los tests críticos pasaron exitosamente
   ```

4. **En la monitorización**:
   - Servicio activo y respondiendo
   - Mensajes procesándose con nueva lógica
   - Sin errores críticos en logs
   - Ocupaciones actualizándose correctamente

---

*Guía de despliegue v4.0.0 - Actualizada el 12 de septiembre de 2025*  
*Estado: Lista para ejecución en producción*
