# 🚀 Comandos de Despliegue v3.5.0 - Paso a Paso

## 📋 **EJECUCIÓN SECUENCIAL**

> **Importante**: Ejecutar cada comando individualmente y verificar resultado antes del siguiente [[memory:4536086]]

---

## 🔧 **FASE 1: PREPARACIÓN**

### Comando 1: Conectar al servidor
```bash
ssh root@157.180.91.63
```

### Comando 2: Ir al directorio del proyecto
```bash
cd /opt/parking_altea
```

### Comando 3: Verificar estado actual
```bash
git branch --show-current && git status
```

---

## 📥 **FASE 2: ACTUALIZACIÓN DE CÓDIGO**

### Comando 4: Obtener última versión
```bash
git fetch origin
```

### Comando 5: Cambiar a rama v3.5.0
```bash
git checkout v3.5.0
```

### Comando 6: Actualizar código
```bash
git pull origin v3.5.0
```

### Comando 7: Verificar commits descargados
```bash
git log --oneline -4
```

---

## 📦 **FASE 3: DEPENDENCIAS BACKEND**

### Comando 8: Instalar pytz (nueva dependencia crítica)
```bash
pip install pytz==2023.3
```

### Comando 9: Verificar instalación de pytz
```bash
pip list | grep pytz
```

---

## 🏗️ **FASE 4: COMPILACIÓN FRONTEND** ⚠️ **CRÍTICO**

### Comando 10: Ir al directorio del cliente
```bash
cd client
```

### Comando 11: Instalar dependencias frontend
```bash
npm install
```

### Comando 12: Compilar frontend (OBLIGATORIO)
```bash
npm run build
```
> **Verificar**: Debe completarse sin errores y mostrar "built in XXXms"

### Comando 13: Verificar compilación
```bash
ls -la dist/
```
> **Verificar**: Debe existir directorio `dist/` con archivos compilados

### Comando 14: Volver al directorio raíz
```bash
cd ..
```

---

## 🛑 **FASE 5: DETENER SERVICIOS**

### Comando 15: Detener API Server
```bash
pkill -f "python.*api_server.py"
```

### Comando 16: Detener Camera Server
```bash
pkill -f "python.*camera_server.py"
```

### Comando 17: Detener Schedule Monitor
```bash
pkill -f "python.*schedule_monitor"
```

### Comando 18: Detener Panel Worker
```bash
pkill -f "python.*panel_worker"
```

### Comando 19: Liberar puerto 5789 [[memory:4536083]]
```bash
lsof -ti:5789 | xargs -r kill -9
```

### Comando 20: Verificar que todo se detuvo
```bash
ps aux | grep python | grep -E "(api_server|camera_server|schedule_monitor|panel_worker)" | grep -v grep
```
> **Resultado esperado**: No debe mostrar ningún proceso

### Comando 21: Verificar puerto 5789 libre
```bash
lsof -i:5789
```
> **Resultado esperado**: No debe mostrar ningún proceso

---

## ▶️ **FASE 6: INICIAR SERVICIOS ACTUALIZADOS**

### Comando 22: Crear directorio de logs si no existe
```bash
mkdir -p logs
```

### Comando 23: Iniciar API Server
```bash
nohup python src/api_server.py > logs/api_server.log 2>&1 &
```

### Comando 24: Iniciar Camera Server
```bash
nohup python src/camera_server.py > logs/camera_server.log 2>&1 &
```

### Comando 25: Iniciar Schedule Monitor (con nueva zona horaria)
```bash
nohup python src/schedule_monitor_service.py > logs/schedule_monitor.log 2>&1 &
```

### Comando 26: Iniciar Panel Worker (con nueva zona horaria)
```bash
nohup python src/panel_worker.py > logs/panel_worker.log 2>&1 &
```

### Comando 27: Esperar 5 segundos para estabilización
```bash
sleep 5
```

### Comando 28: Ir al directorio cliente para frontend
```bash
cd client
```

### Comando 29: Iniciar Frontend en puerto 5789 [[memory:4536083]]
```bash
nohup npm run preview -- --host 0.0.0.0 --port 5789 > ../logs/frontend.log 2>&1 &
```

### Comando 30: Volver al directorio raíz
```bash
cd ..
```

---

## ✅ **FASE 7: VERIFICACIÓN**

### Comando 31: Verificar procesos backend
```bash
ps aux | grep python | grep -E "(api_server|camera_server|schedule_monitor|panel_worker)" | grep -v grep
```
> **Resultado esperado**: 4 procesos Python ejecutándose

### Comando 32: Verificar frontend en puerto 5789
```bash
lsof -i:5789
```
> **Resultado esperado**: Proceso node/npm en puerto 5789

### Comando 33: Test API Server
```bash
curl -s http://localhost:8080/health
```
> **Resultado esperado**: Respuesta JSON con status OK

### Comando 34: Test Frontend
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5789
```
> **Resultado esperado**: 200

### Comando 35: Verificar logs iniciales API
```bash
tail -10 logs/api_server.log
```
> **Verificar**: No debe mostrar errores críticos

### Comando 36: Verificar logs Schedule Monitor
```bash
tail -10 logs/schedule_monitor.log
```
> **Verificar**: Debe mostrar "Timezone Utils - Madrid:" en logs

### Comando 37: Verificar logs Frontend
```bash
tail -10 logs/frontend.log
```
> **Verificar**: Debe mostrar que el servidor está corriendo en puerto 5789

---

## 🧪 **FASE 8: TESTING FUNCIONAL**

### Test 1: Acceso Frontend
```bash
echo "Acceder a: http://157.180.91.63:5789"
```

### Test 2: Verificar edición de parking
1. Ir a sección Parkings
2. Hacer clic en "Editar" 
3. **Verificar**: Campos nombre y ubicación están presentes
4. Probar guardar cambios

### Test 3: Verificar zona horaria
```bash
date
```
> **Verificar**: Hora actual del servidor, las programaciones deben usar Madrid timezone

---

## 🚨 **COMANDOS DE EMERGENCIA**

### Si algo falla, rollback a v3.4.0:
```bash
git checkout v3.4.0
git pull origin v3.4.0
# Repetir desde FASE 5
```

### Reinicio completo de servicios:
```bash
# Detener todo
pkill -f "python.*api_server.py"
pkill -f "python.*camera_server.py" 
pkill -f "python.*schedule_monitor"
pkill -f "python.*panel_worker"
lsof -ti:5789 | xargs -r kill -9

# Esperar y reiniciar desde Comando 23
sleep 10
```

### Monitoreo en tiempo real:
```bash
# En terminal separado
tail -f logs/api_server.log

# En otro terminal
tail -f logs/schedule_monitor.log

# En otro terminal  
tail -f logs/frontend.log
```

---

## 📊 **CHECKLIST FINAL**

- [ ] ✅ Código actualizado a v3.5.0
- [ ] ✅ pytz==2023.3 instalado
- [ ] ✅ Frontend compilado con npm run build
- [ ] ✅ Servicios antiguos detenidos
- [ ] ✅ Puerto 5789 liberado
- [ ] ✅ API Server iniciado (puerto 8080)
- [ ] ✅ Camera Server iniciado (puerto 5000)
- [ ] ✅ Schedule Monitor iniciado (zona Madrid)
- [ ] ✅ Panel Worker iniciado (zona Madrid)
- [ ] ✅ Frontend iniciado (puerto 5789)
- [ ] ✅ API responde correctamente
- [ ] ✅ Frontend accesible
- [ ] ✅ Edición de parkings funciona
- [ ] ✅ Zona horaria corregida

---

**Estado**: 🟢 Listo para ejecución
**Tiempo estimado**: 15-20 minutos
**Versión**: v3.5.0

---

*Comandos optimizados para ejecución paso a paso - Enero 2025*
