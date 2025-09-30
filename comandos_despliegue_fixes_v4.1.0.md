# Comandos de Despliegue - Fixes Frontend v4.1.0

## Información del Servidor
- **Servidor**: root@ubuntu-16gb-hel1-1
- **Ruta del proyecto**: /opt/parking_altea
- **Rama**: v4.1.0
- **Puerto frontend**: 5789

## Cambios incluidos en este despliegue:
1. **Fix panelService.verifyAllPanels**: Corrige error en botón verificar paneles
2. **Fix camera-logs v2**: Corrige error 500 en logs de cámaras con filtrado por permisos

---

## 1. Conectar al servidor
```bash
ssh root@ubuntu-16gb-hel1-1
```

## 2. Navegar al directorio del proyecto
```bash
cd /opt/parking_altea
```

## 3. Verificar rama actual y estado
```bash
git branch
git status
```

## 4. Actualizar código desde repositorio

### Opción A: Pull normal (si no hay cambios locales)
```bash
git fetch origin
git pull origin v4.1.0
```

### Opción B: Descartar cambios locales y actualizar (si hay conflictos)
```bash
# Verificar qué archivos tienen cambios locales
git status

# Descartar TODOS los cambios locales (CUIDADO: se perderán las modificaciones locales)
git reset --hard HEAD

# Actualizar desde repositorio
git fetch origin
git pull origin v4.1.0
```

### Opción C: Hacer stash de cambios locales (preservar cambios)
```bash
# Guardar cambios locales temporalmente
git stash push -m "Cambios locales antes de actualizar"

# Actualizar desde repositorio
git fetch origin
git pull origin v4.1.0

# Opcional: Restaurar cambios locales después (si son necesarios)
# git stash pop
```

## 5. Verificar que los cambios se han aplicado
```bash
# Verificar cambio en panelService.js
grep -A 10 "verifyAllPanels" client/src/services/panelService.js

# Verificar cambio en auth.py
grep -A 5 "from models import Access, CameraParking, UserParking" src/auth.py

# IMPORTANTE: Verificar sintaxis del archivo panelService.js
node -c client/src/services/panelService.js
echo "✅ Sintaxis de panelService.js verificada"
```

### Si hay error de sintaxis en panelService.js:
```bash
# Verificar el contenido del archivo
cat client/src/services/panelService.js | tail -20

# Si el archivo está corrupto, restaurar desde git
git checkout HEAD -- client/src/services/panelService.js

# Volver a hacer pull para aplicar los cambios
git pull origin v4.1.0

# Verificar nuevamente la sintaxis
node -c client/src/services/panelService.js
```

### Problemas adicionales detectados:
```bash
# 1. Verificar si falta función getHourlyStatistics en statisticsService
grep -n "getHourlyStatistics" client/src/services/statisticsService.js

# 2. Si no existe, agregarla manualmente (ver correcciones abajo)

# 3. Verificar logs del backend para error 500 en camera-logs-v2
sudo journalctl -u parking-api -f --lines=50 | grep -i "camera-logs-v2\|error"
```

## 6. Reiniciar servicios del backend
```bash
# Reiniciar API server
sudo systemctl restart parking-api

# Verificar estado
sudo systemctl status parking-api

# Reiniciar camera server (puerto 6400) si está activo
sudo systemctl restart parking-camera
sudo systemctl status parking-camera
```

## 7. Actualizar y desplegar frontend

### Opción A: Despliegue con nginx (RECOMENDADO - Producción)
```bash
# Navegar al directorio del cliente
cd /opt/parking_altea/client

# Verificar permisos del directorio
sudo chown -R root:root /opt/parking_altea/client
sudo chmod -R 755 /opt/parking_altea/client

# Instalar dependencias (por si hay cambios)
npm install

# Instalar dependencias específicas que pueden faltar
npm install react-bootstrap bootstrap
npm install @popperjs/core

# Construir el proyecto para producción
npm run build

# Asegurarse de estar en el directorio correcto
cd /opt/parking_altea/client

# Verificar que existe la carpeta dist
ls -la dist/

# Crear directorio estático de nginx si no existe
sudo mkdir -p /opt/parking_altea/static

# Copiar build a directorio de nginx con permisos correctos
sudo cp -r dist/* /opt/parking_altea/static/
sudo chown -R www-data:www-data /opt/parking_altea/static
sudo chmod -R 644 /opt/parking_altea/static/*
sudo find /opt/parking_altea/static -type d -exec chmod 755 {} \;

# Verificar que los archivos se copiaron correctamente
ls -la /opt/parking_altea/static/
test -f /opt/parking_altea/static/index.html && echo "✅ index.html copiado correctamente"

# Verificar configuración de nginx
sudo nginx -t

# Recargar nginx
sudo systemctl reload nginx

# Verificar estado de nginx
sudo systemctl status nginx
```

### Opción B: Servicio standalone (puerto 5789 - Solo para desarrollo)
```bash
# Detener procesos existentes en puerto 5789
sudo pkill -f ".*:5789" || true
sudo lsof -ti:5789 | xargs sudo kill -9 2>/dev/null || true

# Navegar al directorio del cliente
cd /opt/parking_altea/client

# Instalar dependencias
npm install

# Instalar dependencias específicas que pueden faltar
npm install react-bootstrap bootstrap
npm install @popperjs/core

# Construir el proyecto
npm run build

# Iniciar el frontend en background
nohup npm run preview -- --host 0.0.0.0 --port 5789 > /tmp/frontend.log 2>&1 &

# Verificar que está corriendo
sleep 3
curl -I http://localhost:5789
```

## 8. Verificar funcionamiento
```bash
# Verificar logs del API server
sudo journalctl -u parking-api -f --lines=20

# Verificar logs de nginx (si usas Opción A)
sudo tail -f /var/log/nginx/parking_altea_access.log
sudo tail -f /var/log/nginx/parking_altea_error.log

# Verificar logs del frontend standalone (si usas Opción B)
tail -f /tmp/frontend.log

# Verificar que los puertos están activos
sudo netstat -tlnp | grep -E "(6001|6400|80|5789)"

# Verificar acceso web
curl -I http://localhost:80  # Si usas nginx
curl -I http://localhost:5789  # Si usas standalone
```

## 9. Pruebas funcionales

### Probar endpoint de verificación de paneles:
```bash
# Desde el servidor
curl -X POST http://localhost:6001/api/panels/verify \
  -H "Content-Type: application/json"
```

### Probar endpoint de camera-logs-v2:
```bash
# Desde el servidor
curl "http://localhost:6001/api/camera-logs-v2?date_from=$(date +%Y-%m-%d)&date_to=$(date +%Y-%m-%d)&page=1&per_page=10" \
  -H "Content-Type: application/json"
```

## 10. Verificación final
- [ ] Frontend accesible (puerto 80 con nginx O puerto 5789 standalone)
- [ ] API server respondiendo en puerto 6001
- [ ] Camera server respondiendo en puerto 6400 (si está activo)
- [ ] Botón "Verificar Paneles" funciona sin errores
- [ ] Página Camera Logs muestra información sin error 500
- [ ] Logs del sistema sin errores críticos
- [ ] Nginx configurado y funcionando (si usas Opción A)
- [ ] Permisos correctos en archivos estáticos

---

## Comandos de rollback (si es necesario)
```bash
# Volver al commit anterior
git log --oneline -5
git reset --hard <commit_anterior>

# Reiniciar servicios
sudo systemctl restart parking-api
sudo systemctl restart parking-camera

# Reconstruir frontend (nginx)
cd /opt/parking_altea/client
npm install
npm install react-bootstrap bootstrap @popperjs/core
npm run build
sudo cp -r dist/* /opt/parking_altea/static/
sudo chown -R www-data:www-data /opt/parking_altea/static
sudo systemctl reload nginx

# O reconstruir frontend (standalone)
# npm install
# npm install react-bootstrap bootstrap @popperjs/core
# npm run build
# sudo pkill -f ".*:5789"
# nohup npm run preview -- --host 0.0.0.0 --port 5789 > /tmp/frontend.log 2>&1 &
```

## CORRECCIONES ADICIONALES NECESARIAS

### 1. Agregar función faltante getHourlyStatistics
```bash
# Editar statisticsService.js para agregar la función faltante
cat >> client/src/services/statisticsService.js << 'EOF'

  /**
   * NUEVO: Obtener estadísticas por horas de un parking
   */
  getHourlyStatistics: async (parkingId, params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.date) queryParams.append('date', params.date)
      if (params.days) queryParams.append('days', params.days)
      
      const response = await api.get(`/api/parkings/${parkingId}/statistics/hourly?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas por horas:', error)
      throw error
    }
  },
EOF
```

### 2. Verificar encoding de panelService.js
```bash
# Verificar encoding del archivo
file client/src/services/panelService.js

# Si está en UTF-16, convertir a UTF-8
iconv -f UTF-16 -t UTF-8 client/src/services/panelService.js > client/src/services/panelService.js.tmp
mv client/src/services/panelService.js.tmp client/src/services/panelService.js

# Verificar sintaxis después de conversión
node -c client/src/services/panelService.js
```

### 3. Verificar error 500 en camera-logs-v2
```bash
# Verificar logs en tiempo real
sudo journalctl -u parking-api -f &

# En otra terminal, probar el endpoint directamente
curl -v "http://localhost:6001/api/camera-logs-v2?date_from=$(date +%Y-%m-%d)&date_to=$(date +%Y-%m-%d)&page=1&per_page=10"

# Detener el seguimiento de logs
kill %1
```

## Notas importantes:
- Los cambios son principalmente fixes de frontend y backend
- No hay cambios en base de datos
- El despliegue es de bajo riesgo
- Se recomienda hacer las pruebas funcionales después del despliegue
- **IMPORTANTE**: Aplicar las correcciones adicionales antes de las pruebas finales
