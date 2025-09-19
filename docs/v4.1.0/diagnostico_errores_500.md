# Diagnóstico de Errores 500 - API Sensores v4.1.0

## 🚨 **ERRORES IDENTIFICADOS:**

### **1. Error 500 en `/api/sensors`**
- **Causa probable**: Tablas de sensores no existen o modelo `IndividualSensor` tiene problemas
- **Síntoma**: `Internal server error` al acceder a cualquier endpoint de sensores

### **2. Error 500 en `/api/sensors/status/grouped`**
- **Causa probable**: Vistas materializadas o funciones de base de datos no creadas
- **Síntoma**: Error al acceder a datos agrupados de sensores

---

## 🔍 **COMANDOS DE DIAGNÓSTICO:**

### **1. Verificar existencia de tablas de sensores:**
```bash
sudo -u postgres psql parking_db -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%sensor%' 
ORDER BY table_name;"
```

### **2. Verificar estructura de tabla individual_sensors:**
```bash
sudo -u postgres psql parking_db -c "\d individual_sensors"
```

### **3. Verificar datos en tablas:**
```bash
sudo -u postgres psql parking_db -c "
SELECT 
    'individual_sensors' as tabla, COUNT(*) as registros 
FROM individual_sensors
UNION ALL
SELECT 
    'sensor_current_status' as tabla, COUNT(*) as registros 
FROM sensor_current_status
UNION ALL
SELECT 
    'sensor_status_history' as tabla, COUNT(*) as registros 
FROM sensor_status_history;"
```

### **4. Verificar vistas materializadas:**
```bash
sudo -u postgres psql parking_db -c "
SELECT matviewname, ispopulated 
FROM pg_matviews 
WHERE matviewname LIKE '%sensor%';"
```

### **5. Verificar funciones de base de datos:**
```bash
sudo -u postgres psql parking_db -c "
SELECT proname, proargnames 
FROM pg_proc 
WHERE proname LIKE '%sensor%';"
```

### **6. Verificar logs del API para errores específicos:**
```bash
journalctl -u parking-api.service -f --no-pager -n 100 | grep -i sensor
```

---

## 🛠️ **POSIBLES SOLUCIONES:**

### **Si las tablas no existen:**
```bash
# Ejecutar comandos de creación de tablas v4.1.0
sudo -u postgres psql parking_db -f /opt/parking_altea/docs/v4.1.0/comandos_despliegue_v4.1.0.md
```

### **Si las vistas materializadas fallan:**
```bash
sudo -u postgres psql parking_db -c "
DROP MATERIALIZED VIEW IF EXISTS parking_complete_status CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sensors_by_type_status CASCADE;
"
# Luego recrear las vistas
```

### **Si el modelo Python tiene problemas:**
```bash
# Verificar imports en api_server.py
grep -n "IndividualSensor" /opt/parking_altea/src/api_server.py
grep -n "SensorCurrentStatus" /opt/parking_altea/src/api_server.py
```

---

## 📋 **COMANDO DIAGNÓSTICO COMPLETO:**

```bash
echo "=== DIAGNÓSTICO COMPLETO SENSORES v4.1.0 ==="
echo "1. Verificando tablas..."
sudo -u postgres psql parking_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%sensor%' ORDER BY table_name;" || echo "❌ Error verificando tablas"

echo "2. Verificando datos..."
sudo -u postgres psql parking_db -c "SELECT 'individual_sensors' as tabla, COUNT(*) as registros FROM individual_sensors;" || echo "❌ Tabla individual_sensors no existe"

echo "3. Verificando vistas..."
sudo -u postgres psql parking_db -c "SELECT matviewname FROM pg_matviews WHERE matviewname LIKE '%sensor%';" || echo "❌ Error verificando vistas"

echo "4. Verificando API logs..."
journalctl -u parking-api.service --no-pager -n 20 | grep -i "error\|exception" || echo "❌ Error accediendo logs"

echo "5. Test endpoint directo..."
curl -I http://localhost:6001/api/sensors || echo "❌ API no responde"

echo "=== DIAGNÓSTICO COMPLETADO ==="
```

---

## ✅ **CRITERIOS DE ÉXITO:**

- [ ] Tablas de sensores existen y tienen estructura correcta
- [ ] Vistas materializadas creadas y pobladas
- [ ] Funciones de base de datos operativas
- [ ] API responde 200 OK a `/api/sensors`
- [ ] No hay errores 500 en logs del API
- [ ] Frontend puede cargar página de sensores sin errores

---

**Fecha**: 2025-09-19  
**Estado**: Pendiente de diagnóstico  
**Prioridad**: Alta - Bloquea funcionalidad v4.1.0
