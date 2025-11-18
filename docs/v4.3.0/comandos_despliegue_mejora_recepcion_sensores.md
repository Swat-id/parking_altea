# Comandos de Despliegue: Mejora de Recepción de Sensores v4.3.0

## Cambios Implementados

### Mejoras en `src/sensor_push_service.py`:

1. **Logging mejorado**: Se registran TODOS los mensajes recibidos, incluso los que fallan
2. **Extracción flexible de serial_number**: Busca en múltiples ubicaciones:
   - `sensor_info.serial_number` (formato estándar)
   - `serial_number` (en root del mensaje)
   - `device_id` o `device_serial` (formatos alternativos)
3. **Validación más flexible**: Acepta mensajes con diferentes estructuras
4. **Mejor diagnóstico**: Logs detallados para identificar problemas con sensores específicos (ej: FD010E5F)

## Comandos de Despliegue

### 1. Conectar al servidor de producción

```bash
ssh root@157.180.91.63
```

### 2. Navegar al directorio del proyecto

```bash
cd /opt/parking_altea
```

### 3. Activar el entorno virtual

```bash
source venv/bin/activate
```

### 4. Cambiar a la rama v4.3.0

```bash
git fetch origin
git checkout v4.3.0
git pull origin v4.3.0
```

### 5. Verificar que el archivo se actualizó

```bash
grep -n "Extraer serial_number de diferentes ubicaciones" src/sensor_push_service.py
```

### 6. Reiniciar el servicio de sensores

```bash
systemctl restart parking-sensor-push
```

### 7. Verificar que el servicio está activo

```bash
systemctl status parking-sensor-push --no-pager
```

### 8. Ver logs en tiempo real

```bash
journalctl -u parking-sensor-push -f
```

### 9. Verificar logs específicos del archivo

```bash
tail -f logs/sensor_push_service.log
```

### 10. Buscar mensajes del sensor FD010E5F

```bash
grep -i "FD010E5F" logs/sensor_push_service.log | tail -20
```

### 11. Ver todos los mensajes recibidos (últimos 50)

```bash
grep "📥\|📦\|✅\|❌" logs/sensor_push_service.log | tail -50
```

### 12. Verificar que el servicio está escuchando en el puerto 3535

```bash
netstat -tlnp | grep 3535
# O alternativamente:
ss -tlnp | grep 3535
```

### 13. Probar el endpoint de health

```bash
curl http://localhost:3535/health
```

## Verificación Post-Despliegue

### Verificar que se están recibiendo mensajes

```bash
# Ver logs en tiempo real esperando mensajes
journalctl -u parking-sensor-push -f | grep -E "📥|📦|✅|❌|FD010E5F"
```

### Verificar errores recientes

```bash
journalctl -u parking-sensor-push --since "10 minutes ago" | grep -i error
```

### Verificar mensajes procesados exitosamente

```bash
journalctl -u parking-sensor-push --since "10 minutes ago" | grep "✅"
```

### Verificar mensajes fallidos

```bash
journalctl -u parking-sensor-push --since "10 minutes ago" | grep "❌"
```

## Diagnóstico de Problemas

### Si el sensor FD010E5F no aparece en los logs:

1. **Verificar que el sensor está enviando mensajes**:
   ```bash
   # Ver todos los mensajes recibidos (sin filtro)
   journalctl -u parking-sensor-push --since "1 hour ago" | grep "📦"
   ```

2. **Verificar si hay errores de validación**:
   ```bash
   journalctl -u parking-sensor-push --since "1 hour ago" | grep "❌\|Validación falló"
   ```

3. **Ver la estructura completa de los mensajes recibidos**:
   ```bash
   # Los mensajes completos están en nivel DEBUG
   journalctl -u parking-sensor-push --since "1 hour ago" -p debug | grep "📋\|Mensaje completo"
   ```

### Si el servicio no inicia:

```bash
# Ver errores de inicio
journalctl -u parking-sensor-push -n 50 --no-pager

# Verificar sintaxis del archivo Python
python3 -m py_compile src/sensor_push_service.py
```

### Si hay problemas de permisos:

```bash
# Verificar permisos del archivo
ls -la src/sensor_push_service.py

# Verificar permisos del directorio de logs
ls -la logs/
```

## Rollback (si es necesario)

Si hay problemas, volver a la versión anterior:

```bash
cd /opt/parking_altea
git checkout HEAD~1 src/sensor_push_service.py
systemctl restart parking-sensor-push
```

## Notas Importantes

- Los logs ahora incluyen emojis para facilitar la identificación:
  - 📥 = Mensaje recibido
  - 📦 = Datos JSON recibidos
  - ✅ = Procesado exitosamente
  - ❌ = Error en procesamiento
  - ⚠️ = Advertencia

- El servicio ahora busca `serial_number` en múltiples ubicaciones, lo que permite mayor flexibilidad con diferentes formatos de mensajes.

- Todos los mensajes recibidos se loguean en nivel INFO o superior, facilitando el diagnóstico de problemas.

