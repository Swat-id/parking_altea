# Despliegue v2.7.1 - Parking Altea

## 📋 Resumen del Despliegue

**Versión**: v2.7.1 - Corrección de Cálculo de Deltas + Sistema de Programaciones  
**Fecha**: 1 de Julio de 2025  
**Servidor**: 157.180.91.63  
**Rama Git**: `v2.7_no_login_Panel_prog`

### 🎯 Funcionalidades Incluidas

- ✅ **Sistema de programaciones de paneles** completo
- ✅ **Corrección crítica del cálculo de deltas** en procesamiento de cámaras
- ✅ **Servicio de monitorización automática** de programaciones
- ✅ **Frontend actualizado** con interfaz de programaciones
- ✅ **API completa** para gestión de programaciones
- ✅ **Base de datos extendida** con nuevas tablas

---

## 🚀 Scripts de Despliegue

### 1. Despliegue Completo
```bash
chmod +x deploy/deploy_v2.7.1_complete.sh
./deploy/deploy_v2.7.1_complete.sh
```

**Funcionalidades del script:**
- Backup completo del sistema actual
- Actualización de código desde Git
- Migración de base de datos
- Reinicio de servicios backend
- Configuración del servicio de monitorización
- Construcción y despliegue del frontend
- Verificación de todos los servicios
- Prueba de nuevos endpoints

### 2. Verificación Post-Despliegue
```bash
chmod +x deploy/verify_v2.7.1_deployment.sh
./deploy/verify_v2.7.1_deployment.sh
```

**Funcionalidades del script:**
- Verificación de servicios del sistema
- Validación de endpoints básicos y nuevos
- Verificación de corrección de deltas
- Validación de base de datos
- Verificación de frontend
- Revisión de logs recientes
- Pruebas de funcionalidades específicas

### 3. Rollback (En caso de problemas)
```bash
chmod +x deploy/rollback_v2.7.1.sh
./deploy/rollback_v2.7.1.sh
```

**Funcionalidades del script:**
- Restauración completa del sistema anterior
- Eliminación de nuevas funcionalidades
- Restauración de base de datos
- Eliminación del servicio de monitorización
- Restauración del frontend anterior

---

## 📊 Proceso de Despliegue

### Fase 1: Preparación
1. **Backup completo** del sistema actual
   - Base de datos PostgreSQL
   - Código fuente
   - Logs del sistema

2. **Verificación de dependencias**
   - Node.js y npm (frontend)
   - Python 3 y dependencias (backend)
   - PostgreSQL (base de datos)
   - systemd (servicios)

### Fase 2: Actualización de Código
1. **Git fetch y checkout** de la rama v2.7_no_login_Panel_prog
2. **Git pull** de los últimos cambios
3. **Verificación** de que el código se actualizó correctamente

### Fase 3: Base de Datos
1. **Ejecución de migración** `migrate_panel_schedules.py`
2. **Creación de nuevas tablas**:
   - `panel_schedules`
   - `panel_schedule_logs`
3. **Modificación de tabla existente**:
   - Añadir `panel_display_text` a `parkings`

### Fase 4: Servicios Backend
1. **Detener servicios** actuales
2. **Reiniciar servicios** con código actualizado
3. **Verificación** de que los servicios están activos

### Fase 5: Servicio de Monitorización
1. **Configuración** del archivo de servicio systemd
2. **Habilitación** del servicio
3. **Inicio** del servicio de monitorización

### Fase 6: Frontend
1. **Instalación** de dependencias npm
2. **Construcción** del frontend
3. **Despliegue** en nginx

### Fase 7: Verificación
1. **Pruebas** de todos los endpoints
2. **Validación** de nuevas funcionalidades
3. **Verificación** de corrección de deltas

---

## 🔧 Configuración de Servicios

### Servicios del Sistema
- **parking-api.service** (Puerto 6001) - API REST principal
- **parking-camera.service** (Puerto 6400) - Servidor de cámaras
- **parking-schedule-monitor.service** - Monitor de programaciones (NUEVO)
- **panel-service.service** (Puerto 5656) - Servicio de paneles Java

### Comandos de Gestión
```bash
# Ver estado de servicios
systemctl status parking-api.service
systemctl status parking-camera.service
systemctl status parking-schedule-monitor.service
systemctl status panel-service.service

# Ver logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u parking-schedule-monitor.service -f

# Reiniciar servicios
systemctl restart parking-api.service
systemctl restart parking-camera.service
systemctl restart parking-schedule-monitor.service
```

---

## 🌐 URLs de Acceso

### Frontend
- **URL Principal**: http://157.180.91.63:5789
- **Programaciones**: http://157.180.91.63:5789/schedules

### API Backend
- **API Principal**: http://157.180.91.63:6001
- **Parkings**: http://157.180.91.63:6001/api/parkings
- **Programaciones**: http://157.180.91.63:6001/api/schedules
- **Logs de Programaciones**: http://157.180.91.63:6001/api/schedules/logs

### Servicios
- **Servidor de Cámaras**: http://157.180.91.63:6400
- **Servicio de Paneles**: http://157.180.91.63:5656

---

## 🧪 Pruebas Post-Despliegue

### 1. Pruebas de Endpoints
```bash
# Probar endpoints básicos
curl http://157.180.91.63:6001/api/parkings
curl http://157.180.91.63:6400/camera

# Probar nuevos endpoints de programaciones
curl http://157.180.91.63:6001/api/schedules
curl http://157.180.91.63:6001/api/schedules/logs
curl http://157.180.91.63:6001/api/parking/1/schedules
```

### 2. Pruebas de Frontend
1. **Acceder** a http://157.180.91.63:5789
2. **Navegar** a la sección "Programaciones"
3. **Crear** una programación de prueba
4. **Verificar** que se guarda correctamente

### 3. Pruebas de Corrección de Deltas
1. **Enviar** mensaje de cámara con contador 408→409
2. **Verificar** que reporta +1 (no +3)
3. **Comprobar** logs para confirmar corrección

### 4. Pruebas del Servicio de Monitorización
```bash
# Verificar que el servicio está activo
systemctl status parking-schedule-monitor.service

# Ver logs del servicio
journalctl -u parking-schedule-monitor.service -f

# Crear programación activa y verificar ejecución automática
```

---

## 📝 Logs y Monitoreo

### Logs Importantes
- **parking-api.service**: Logs de la API REST
- **parking-camera.service**: Logs de procesamiento de cámaras
- **parking-schedule-monitor.service**: Logs de monitorización de programaciones
- **panel-service.service**: Logs del servicio de paneles

### Comandos de Monitoreo
```bash
# Ver logs recientes
journalctl -u parking-api.service --no-pager -n 20
journalctl -u parking-camera.service --no-pager -n 20
journalctl -u parking-schedule-monitor.service --no-pager -n 20

# Ver logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u parking-schedule-monitor.service -f

# Ver logs con timestamps
journalctl -u parking-api.service --no-pager -n 50 --output=short-precise
```

---

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Servicio no inicia
```bash
# Verificar logs del servicio
journalctl -u parking-schedule-monitor.service --no-pager -n 20

# Verificar dependencias
systemctl list-dependencies parking-schedule-monitor.service

# Reiniciar servicio
systemctl restart parking-schedule-monitor.service
```

#### 2. Endpoints no responden
```bash
# Verificar que el servicio está activo
systemctl is-active parking-api.service

# Verificar puerto
netstat -tlnp | grep 6001

# Verificar logs
journalctl -u parking-api.service --no-pager -n 10
```

#### 3. Base de datos no conecta
```bash
# Verificar conexión PostgreSQL
psql -d parking_altea -c "SELECT version();"

# Verificar tablas nuevas
psql -d parking_altea -c "\dt panel_*"
```

#### 4. Frontend no carga
```bash
# Verificar nginx
systemctl status nginx

# Verificar archivos
ls -la /var/www/html/

# Verificar puerto
netstat -tlnp | grep 5789
```

### Rollback en caso de problemas
Si algo sale mal durante el despliegue:
```bash
./deploy/rollback_v2.7.1.sh
```

---

## 📞 Contacto y Soporte

### Información de Despliegue
- **Fecha**: 1 de Julio de 2025
- **Versión**: v2.7.1
- **Servidor**: 157.180.91.63
- **Responsable**: Equipo de desarrollo

### Archivos de Despliegue
- `deploy/deploy_v2.7.1_complete.sh` - Script principal de despliegue
- `deploy/verify_v2.7.1_deployment.sh` - Script de verificación
- `deploy/rollback_v2.7.1.sh` - Script de rollback
- `deploy/parking-schedule-monitor.service` - Archivo de servicio systemd

### Documentación Relacionada
- `docs/v2.7_status.md` - Estado completo de la versión
- `docs/project_status.md` - Estado general del proyecto
- `docs/development_status.md` - Estado técnico detallado
- `docs/tareas_pendientes.md` - Tareas pendientes

---

**¡El sistema v2.7.1 está listo para ser desplegado!** 