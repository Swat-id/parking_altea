# 🚀 Guía de Despliegue v3.5.0

## 📋 **INFORMACIÓN GENERAL**

### **Versión**: v3.5.0
### **Fecha**: Enero 2025
### **Tipo**: Corrección de errores críticos
### **Estado**: ✅ Listo para despliegue

---

## 🔍 **RESUMEN DE CAMBIOS**

### **Errores Corregidos:**
- **EC-001**: ✅ Error de edición de información general de parking
- **EC-002**: ✅ Error de zona horaria en programaciones y worker

### **Archivos Modificados:**
```
📁 Backend (Python):
├── src/api_server.py              # Nuevo endpoint PUT /parkings/{id}
├── src/panel_update_methods.py    # Zona horaria Europa/Madrid
├── src/schedule_monitor_service.py # Zona horaria Europa/Madrid
├── src/panel_schedule_service.py  # Zona horaria Europa/Madrid
├── src/timezone_utils.py          # NUEVO: Utilidades de zona horaria
└── requirements.txt               # Agregado pytz==2023.3

📁 Frontend (React):
├── client/src/services/parkingService.js  # Método editParking()
└── client/src/pages/Parkings.jsx          # Formulario edición extendido

📁 Documentación:
├── docs/v3.5.0/                   # Nueva documentación de rama
├── docs/README.md                 # Actualizado con v3.5.0
└── docs/v3.5.0/analisis_errores_v3.5.0.md
```

---

## 🛠️ **COMANDOS DE DESPLIEGUE**

### **PASO 1: Preparación del Servidor**

#### 1.1. Conectar al servidor
```bash
ssh root@157.180.91.63
```

#### 1.2. Navegar al directorio del proyecto
```bash
cd /var/www/parking_altea
```

#### 1.3. Verificar rama actual
```bash
git branch --show-current
git status
```

### **PASO 2: Actualización del Código**

#### 2.1. Cambiar a rama v3.5.0
```bash
git fetch origin
git checkout v3.5.0
git pull origin v3.5.0
```

#### 2.2. Verificar cambios descargados
```bash
git log --oneline -5
```

### **PASO 3: Actualización de Dependencias Backend**

#### 3.1. Activar entorno virtual (si existe)
```bash
# Si hay entorno virtual
source venv/bin/activate
# O si usa otro nombre
source parking_env/bin/activate
```

#### 3.2. Instalar nueva dependencia pytz
```bash
pip install pytz==2023.3
```

#### 3.3. Verificar instalación
```bash
pip list | grep pytz
```

### **PASO 4: Compilación Frontend** ⚠️ **CRÍTICO**

#### 4.1. Navegar al directorio del cliente
```bash
cd client
```

#### 4.2. Instalar dependencias (si es necesario)
```bash
npm install
```

#### 4.3. Compilar frontend para producción
```bash
npm run build
```

#### 4.4. Verificar compilación exitosa
```bash
ls -la dist/
```

#### 4.5. Regresar al directorio raíz
```bash
cd ..
```

### **PASO 5: Detener Servicios Existentes**

#### 5.1. Detener servicios backend
```bash
# Detener API server
pkill -f "python.*api_server.py" || echo "API server no estaba ejecutándose"

# Detener camera server  
pkill -f "python.*camera_server.py" || echo "Camera server no estaba ejecutándose"

# Detener schedule monitor
pkill -f "python.*schedule_monitor" || echo "Schedule monitor no estaba ejecutándose"

# Detener panel worker
pkill -f "python.*panel_worker" || echo "Panel worker no estaba ejecutándose"
```

#### 5.2. Detener frontend en puerto 5789 [[memory:4536083]]
```bash
# Verificar qué está usando el puerto 5789
lsof -ti:5789 | xargs -r kill -9
```

#### 5.3. Verificar que los servicios se han detenido
```bash
ps aux | grep python | grep -E "(api_server|camera_server|schedule_monitor|panel_worker)"
lsof -i:5789
```

### **PASO 6: Iniciar Servicios Actualizados**

#### 6.1. Iniciar API Server
```bash
nohup python src/api_server.py > logs/api_server.log 2>&1 &
echo "API Server iniciado - PID: $!"
```

#### 6.2. Iniciar Camera Server
```bash
nohup python src/camera_server.py > logs/camera_server.log 2>&1 &
echo "Camera Server iniciado - PID: $!"
```

#### 6.3. Iniciar Schedule Monitor (con nueva zona horaria)
```bash
nohup python src/schedule_monitor_service.py > logs/schedule_monitor.log 2>&1 &
echo "Schedule Monitor iniciado - PID: $!"
```

#### 6.4. Iniciar Panel Worker (con nueva zona horaria)
```bash
nohup python src/panel_worker.py > logs/panel_worker.log 2>&1 &
echo "Panel Worker iniciado - PID: $!"
```

#### 6.5. Iniciar Frontend en puerto 5789 [[memory:4536083]]
```bash
cd client
nohup npm run preview -- --host 0.0.0.0 --port 5789 > ../logs/frontend.log 2>&1 &
echo "Frontend iniciado - PID: $!"
cd ..
```

### **PASO 7: Verificación del Despliegue**

#### 7.1. Verificar procesos en ejecución
```bash
echo "=== PROCESOS BACKEND ==="
ps aux | grep python | grep -E "(api_server|camera_server|schedule_monitor|panel_worker)" | grep -v grep

echo "=== PROCESO FRONTEND ==="
lsof -i:5789
```

#### 7.2. Verificar logs iniciales
```bash
echo "=== API SERVER LOG ==="
tail -20 logs/api_server.log

echo "=== SCHEDULE MONITOR LOG ==="
tail -20 logs/schedule_monitor.log

echo "=== FRONTEND LOG ==="
tail -20 logs/frontend.log
```

#### 7.3. Verificar conectividad
```bash
# Test API Server
curl -s http://localhost:8080/health || echo "API Server no responde"

# Test Frontend
curl -s http://localhost:5789 > /dev/null && echo "Frontend OK" || echo "Frontend no responde"
```

---

## 🧪 **TESTING POST-DESPLIEGUE**

### **Test 1: Edición de Parking (EC-001)**
1. Acceder al frontend: `http://157.180.91.63:5789`
2. Ir a la sección de Parkings
3. Hacer clic en "Editar" en cualquier parking
4. **Verificar**: Campos de nombre y ubicación están presentes
5. Modificar nombre y ubicación
6. Guardar cambios
7. **Resultado esperado**: Cambios guardados correctamente

### **Test 2: Zona Horaria (EC-002)**
1. Crear una programación de prueba
2. Configurar horario: 14:00 - 15:00 (hora local Madrid)
3. Esperar a que se active
4. **Verificar**: La programación se ejecuta a las 14:00 hora local (no UTC)

### **Test 3: Servicios Generales**
- ✅ API responde en puerto 8080
- ✅ Frontend carga en puerto 5789
- ✅ Cámaras procesan imágenes
- ✅ Paneles reciben actualizaciones

---

## ⚠️ **NOTAS IMPORTANTES**

### **Dependencias Críticas:**
- **pytz==2023.3**: Requerido para zona horaria Europa/Madrid
- **Frontend compilado**: Cambios en Parkings.jsx requieren npm run build

### **Puertos Utilizados:** [[memory:4536083]]
- **API Server**: 8080
- **Camera Server**: 5000  
- **Frontend**: 5789 (SIEMPRE debe ser 5789)

### **Logs de Monitoreo:**
```bash
# Monitoreo continuo de logs
tail -f logs/api_server.log
tail -f logs/schedule_monitor.log
tail -f logs/frontend.log
```

### **Rollback de Emergencia:**
Si hay problemas, volver a v3.4.0:
```bash
git checkout v3.4.0
git pull origin v3.4.0
# Repetir pasos de despliegue con v3.4.0
```

---

## 🔧 **COMANDOS DE MANTENIMIENTO**

### **Reiniciar Servicios:**
```bash
# Script completo de reinicio
./scripts/restart_services.sh  # Si existe
# O manualmente repetir PASO 5 y PASO 6
```

### **Verificar Estado:**
```bash
# Ver todos los procesos del sistema
ps aux | grep -E "(python|node|npm)" | grep -v grep

# Ver puertos en uso
netstat -tlnp | grep -E ":5789|:8080|:5000"
```

### **Limpieza de Logs:**
```bash
# Rotar logs si son muy grandes
mv logs/api_server.log logs/api_server.log.old
mv logs/schedule_monitor.log logs/schedule_monitor.log.old
mv logs/frontend.log logs/frontend.log.old
```

---

## 📞 **CONTACTO DE SOPORTE**

En caso de problemas durante el despliegue:
- Verificar logs en tiempo real
- Revisar conectividad de red
- Confirmar que todos los puertos están libres
- Validar que las dependencias están instaladas

**Estado del Despliegue**: 🟢 Listo para producción

---

*Documentación generada para v3.5.0 - Enero 2025*
