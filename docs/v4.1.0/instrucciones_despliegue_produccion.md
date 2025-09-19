# Instrucciones de Despliegue Producción v4.1.0

## 🎯 **Resumen del Despliegue**

**Servidor**: 157.180.91.63  
**Versión**: v4.1.0  
**Funcionalidades nuevas**: Sistema sensores individuales + Dashboard + Servicio Push  
**Puerto nuevo**: 3535 (servicio push sensores)  
**Estrategia**: Despliegue incremental con backup automático  

---

## 📋 **Pre-requisitos**

### **Acceso al Servidor:**
```bash
ssh root@157.180.91.63
```

### **Verificación Estado Actual:**
```bash
cd /opt/fleximodo
git status
git branch
systemctl status parking-*
```

---

## 🚀 **Proceso de Despliegue**

### **PASO 1: Descargar Scripts de Despliegue**

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Ir al directorio del proyecto
cd /opt/fleximodo

# Descargar actualizaciones
git fetch origin
git checkout v4.1.0
git pull origin v4.1.0
```

### **PASO 2: Ejecutar Despliegue Automático**

```bash
# Dar permisos de ejecución
chmod +x deploy/deploy_v4.1.0_production.sh
chmod +x deploy/validate_v4.1.0_deployment.sh
chmod +x deploy/rollback_v4.1.0.sh

# Ejecutar despliegue completo
./deploy/deploy_v4.1.0_production.sh
```

**⏱️ Duración estimada**: 10-15 minutos

### **PASO 3: Validar Despliegue**

```bash
# Ejecutar validación completa
./deploy/validate_v4.1.0_deployment.sh
```

**✅ Resultado esperado**: Todos los tests en verde, sistema operativo al 100%

---

## 🔧 **Lo que Hace el Script de Despliegue**

### **1. Verificación Sistema Actual (2 min)**
- ✅ Verifica servidor correcto (157.180.91.63)
- ✅ Comprueba permisos root
- ✅ Valida directorio proyecto y git
- ✅ Revisa servicios y puertos actuales

### **2. Backup Automático (3 min)**
- ✅ Backup código fuente → `/opt/fleximodo/backups/TIMESTAMP/`
- ✅ Backup base de datos → `database_backup.sql`
- ✅ Backup servicios systemd → `systemd/`

### **3. Actualización Código (1 min)**
- ✅ Stash cambios locales si existen
- ✅ Checkout y pull rama v4.1.0
- ✅ Verifica último commit

### **4. Migración Base de Datos (2 min)**
```sql
-- Nuevas tablas creadas:
- individual_sensors          -- Sensores PMR/Eléctricos/etc
- sensor_status_history       -- Historial estados
- sensor_current_status       -- Estado actual
- parking_sensor_summary      -- Resúmenes por parking

-- Nuevas columnas en panels:
- last_message_window_0/1     -- Mensajes por ventana
- last_update_window_0/1      -- Timestamps ventanas
- window_config_json          -- Configuración ventanas
```

### **5. Despliegue Frontend (3 min)**
- ✅ Instala/actualiza dependencias npm
- ✅ Compila build para producción
- ✅ Verifica generación correcta

### **6. Despliegue Servicio Push (2 min)**
- ✅ Crea servicio systemd `parking-sensor-push`
- ✅ Configura puerto 3535
- ✅ Inicia y habilita servicio

### **7. Configuración Sistema (2 min)**
- ✅ Reinicia servicios existentes
- ✅ Configura firewall puerto 3535
- ✅ Actualiza dependencias Python

### **8. Validación Final (1 min)**
- ✅ Verifica servicios activos
- ✅ Prueba conectividad HTTP
- ✅ Valida base de datos
- ✅ Muestra resumen completo

---

## 📊 **Servicios Desplegados**

### **Servicios Systemd:**
```bash
# Servicios que estarán activos:
systemctl status parking-api              # Puerto 5000 - API Backend
systemctl status parking-sensor-push      # Puerto 3535 - Servicio Push (NUEVO)
systemctl status parking-panel-worker     # Worker paneles (si existe)
```

### **Puertos Utilizados:**
- **5000**: API Backend (existente)
- **3535**: Servicio Push Sensores (**NUEVO**)
- **5789**: Frontend (existente)

### **Endpoints Nuevos:**
```bash
# Servicio Push:
http://157.180.91.63:3535/health          # Health check
http://157.180.91.63:3535/push            # Recepción push sensores
http://157.180.91.63:3535/stats           # Estadísticas servicio

# API Backend:
http://157.180.91.63:5000/api/sensors/stats      # Estadísticas dashboard
http://157.180.91.63:5000/api/dashboard/complete # Dashboard completo
http://157.180.91.63:5000/api/sensors            # CRUD sensores
```

---

## 🔍 **Validación Post-Despliegue**

### **Tests Automáticos (35+ verificaciones):**

1. **Servicios Systemd** (3 tests)
   - parking-api activo
   - parking-sensor-push activo
   - parking-panel-worker (opcional)

2. **Puertos** (3 tests)
   - Puerto 5000 (API)
   - Puerto 3535 (Push Service)
   - Puerto 5789 (Frontend)

3. **Conectividad HTTP** (4 tests)
   - API health endpoint
   - Push service health
   - Push service stats
   - Información servicio correcta

4. **Base de Datos** (4 tests)
   - Conexión PostgreSQL
   - 4 tablas nuevas sensores
   - 3 columnas nuevas panels
   - Conteo sensores existentes

5. **APIs Específicas** (3 tests)
   - /api/sensors/stats
   - /api/dashboard/complete
   - /api/sensors

6. **Archivos Estáticos** (2 tests)
   - Build frontend (client/dist)
   - Servicio push Python

7. **Logs** (2 tests)
   - Logs API sin errores
   - Logs Push sin errores

8. **Firewall** (1 test)
   - Puerto 3535 permitido

### **Resultado Esperado:**
```
✅ Tests pasados: 35+
❌ Tests fallidos: 0
🎉 VALIDACIÓN EXITOSA - SISTEMA OPERATIVO AL 100%
```

---

## 🔄 **Rollback (Si es Necesario)**

### **En caso de problemas:**
```bash
# Ejecutar rollback inmediato
./deploy/rollback_v4.1.0.sh
```

**Lo que hace el rollback:**
- ✅ Detiene servicio push
- ✅ Restaura código desde backup
- ✅ Opción restaurar BD (con confirmación)
- ✅ Reinicia servicios originales
- ✅ Limpia configuración firewall
- ✅ Valida estado post-rollback

---

## 🛠️ **Comandos Útiles Post-Despliegue**

### **Monitorización:**
```bash
# Ver logs en tiempo real
journalctl -u parking-api -f
journalctl -u parking-sensor-push -f

# Estado de servicios
systemctl status parking-*

# Verificar puertos
lsof -i :5000
lsof -i :3535
lsof -i :5789

# Test endpoints
curl http://localhost:5000/api/health
curl http://localhost:3535/health
curl http://localhost:3535/stats
```

### **Gestión Servicios:**
```bash
# Reiniciar servicios
systemctl restart parking-api
systemctl restart parking-sensor-push

# Ver configuración
systemctl cat parking-sensor-push

# Logs específicos
journalctl -u parking-sensor-push --since="1 hour ago"
```

### **Base de Datos:**
```bash
# Conectar a BD
sudo -u postgres psql parking_db

# Verificar tablas nuevas
\dt individual_sensors
\dt sensor_*

# Contar sensores
SELECT COUNT(*) FROM individual_sensors;
```

---

## 🎊 **Funcionalidades Desplegadas**

### **✅ Sistema Sensores Individuales:**
- Dashboard principal con métricas tiempo real
- Gestión completa CRUD sensores PMR/Eléctricos
- Integración página parking con sensores por tipo
- Actualización manual estados desde UI

### **✅ Dashboard Avanzado:**
- Estadísticas tiempo real con auto-refresh
- Visualizaciones: ocupación, salud sistema, distribución tipos
- Dashboard administrativo con métricas servicio push
- Alertas batería baja con navegación directa

### **✅ Servicio Push Puerto 3535:**
- Recepción automática push sensores Fleximodo
- Procesamiento `CarparkSlotStatusBody`
- Actualización automática estados BD
- Endpoints health, stats, manual-update

### **✅ Gestión Paneles Mejorada:**
- Selección ventana 0/1 en paneles Tipo 3
- Almacenamiento último mensaje por ventana
- Validación y pre-visualización mensajes

---

## 📞 **Soporte y Troubleshooting**

### **Si algo no funciona:**

1. **Verificar logs:**
   ```bash
   journalctl -u parking-sensor-push --no-pager -n 50
   ```

2. **Reiniciar servicio:**
   ```bash
   systemctl restart parking-sensor-push
   ```

3. **Validar BD:**
   ```bash
   sudo -u postgres psql parking_db -c "SELECT COUNT(*) FROM individual_sensors;"
   ```

4. **Test conectividad:**
   ```bash
   curl -v http://localhost:3535/health
   ```

5. **Rollback si es crítico:**
   ```bash
   ./deploy/rollback_v4.1.0.sh
   ```

---

## ✅ **Checklist Final**

- [ ] Scripts descargados y con permisos
- [ ] Despliegue ejecutado sin errores
- [ ] Validación pasada (35+ tests en verde)
- [ ] Servicios activos (parking-api, parking-sensor-push)
- [ ] Puertos operativos (5000, 3535, 5789)
- [ ] Endpoints responden correctamente
- [ ] Frontend accesible con nuevas funcionalidades
- [ ] Base de datos migrada correctamente
- [ ] Logs sin errores críticos
- [ ] Firewall configurado

**🎉 ¡DESPLIEGUE v4.1.0 COMPLETADO EXITOSAMENTE!**
