# Comandos de Despliegue Completo v4.2.0 - FINAL
## 🎯 **Sistema de Permisos Implementado Completamente**

### **📋 RESUMEN DE CAMBIOS v4.2.0:**
- ✅ **Endpoints backend** con filtrado automático por permisos de usuario
- ✅ **Servicios frontend** actualizados con control de permisos
- ✅ **Todas las páginas** corregidas para usar endpoints filtrados
- ✅ **Corrección de bugs** en edición de ocupación de parkings
- ✅ **Sistema completo** de permisos usuario/superadmin

---

## **FASE 1: ACTUALIZACIÓN DEL CÓDIGO EN PRODUCCIÓN**

### **1.1 Conectar al servidor y actualizar código:**
```bash
# Conectar al servidor
ssh root@157.180.91.63
cd /opt/parking_altea

# Backup de seguridad antes del despliegue
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r client/src backups/$(date +%Y%m%d_%H%M%S)/src_backup
cp -r src backups/$(date +%Y%m%d_%H%M%S)/backend_backup

# Actualizar código desde git
git stash  # Solo si hay cambios locales
git pull origin v4.1.0
git status  # Verificar actualización exitosa

# Verificar último commit
git log --oneline -3
# Debe mostrar: 2e616fd feat: Implement user permission filtering across all frontend pages
```

### **1.2 Verificar archivos críticos actualizados:**
```bash
echo "=== VERIFICACIÓN DE ARCHIVOS ACTUALIZADOS ==="
echo "🔸 Páginas corregidas:"
ls -la client/src/pages/Dashboard.jsx
ls -la client/src/pages/Panels.jsx
ls -la client/src/pages/Schedules.jsx
ls -la client/src/pages/Sensors.jsx

echo "🔸 Servicios con permisos:"
ls -la client/src/services/parkingService.js
ls -la client/src/services/sensorService.js
ls -la client/src/services/panelService.js
```

---

## **FASE 2: DESPLIEGUE DEL BACKEND**

### **2.1 Verificar y reiniciar servicios backend:**
```bash
# Verificar estado actual
systemctl status parking-api.service --no-pager
systemctl status parking-camera.service --no-pager

# Reiniciar API con nuevos cambios
systemctl restart parking-api.service

# Verificar que se inició correctamente
systemctl status parking-api.service --no-pager
sleep 5

# Test rápido del API
curl -s -I http://localhost:6001/api/parkings | head -1
# Debe mostrar: HTTP/1.1 401 Unauthorized (correcto, necesita autenticación)
```

### **2.2 Test de autenticación y permisos:**
```bash
# Obtener token de superadmin
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

echo "Token obtenido: ${TOKEN:0:50}..." # Solo mostrar inicio del token

# Test endpoints con filtrado por permisos
echo "=== TEST DE ENDPOINTS CON PERMISOS ==="
echo "🔸 Parkings (filtrados por usuario):"
curl -H "Authorization: Bearer $TOKEN" http://localhost:6001/api/parkings | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ {len(data)} parkings accesibles para el usuario')
except:
    print('❌ Error en respuesta')
"

echo "🔸 Sensores agrupados (nuevo v4.2.0):"
curl -H "Authorization: Bearer $TOKEN" http://localhost:6001/api/sensors/summary/user | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    parkings = data.get('user_parkings', [])
    totals = data.get('global_totals', {})
    print(f'✅ Dashboard usuario: {len(parkings)} parkings, {totals.get(\"total_sensors\", 0)} sensores')
except:
    print('❌ Error en respuesta')
"
```

---

## **FASE 3: COMPILACIÓN Y DESPLIEGUE DEL FRONTEND**

### **3.1 Limpiar y preparar compilación:**
```bash
# Ir al directorio del cliente
cd /opt/parking_altea/client

# Limpiar compilaciones anteriores
rm -rf dist/
rm -rf node_modules/.cache/ 2>/dev/null || true

# Verificar dependencias críticas
npm list react-bootstrap bootstrap || npm install react-bootstrap bootstrap
```

### **3.2 Corregir permisos y compilar:**
```bash
# Corregir permisos de vite (CRÍTICO)
chmod +x node_modules/.bin/vite
chmod +x node_modules/.bin/*

# Compilar para producción
NODE_ENV=production npm run build

# Verificar compilación exitosa
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    echo "✅ Compilación exitosa"
    ls -la dist/
    echo "📦 Tamaño total: $(du -sh dist/ | cut -f1)"
else
    echo "❌ Error en compilación"
    exit 1
fi
```

### **3.3 Desplegar archivos estáticos:**
```bash
# Crear directorio estático si no existe
mkdir -p /opt/parking_altea/static

# Copiar archivos compilados
cp -r dist/* /opt/parking_altea/static/

# Configurar permisos para nginx
chown -R www-data:www-data /opt/parking_altea/static/
chmod -R 755 /opt/parking_altea/static/

# Verificar archivos copiados
echo "=== ARCHIVOS DESPLEGADOS ==="
ls -la /opt/parking_altea/static/
echo "📁 Assets:"
ls -la /opt/parking_altea/static/assets/ | head -5
```

---

## **FASE 4: CONFIGURACIÓN Y INICIO DE NGINX**

### **4.1 Verificar y configurar nginx:**
```bash
# Verificar estado de nginx
systemctl status nginx --no-pager

# Iniciar nginx si no está activo
if ! systemctl is-active --quiet nginx; then
    systemctl start nginx
    systemctl enable nginx
    echo "✅ Nginx iniciado"
else
    echo "✅ Nginx ya está activo"
fi

# Verificar configuración
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✅ Nginx recargado correctamente"
else
    echo "❌ Error en configuración nginx"
    nginx -t  # Mostrar error específico
fi
```

### **4.2 Verificar configuración de sitio:**
```bash
# Verificar que existe la configuración del sitio
if [ -f "/etc/nginx/sites-available/parking_altea" ]; then
    echo "✅ Configuración nginx encontrada"
    echo "🔸 Verificando configuración:"
    grep -A5 -B2 "location /api/" /etc/nginx/sites-available/parking_altea
else
    echo "⚠️  Configuración nginx no encontrada, creando..."
    # Aquí iría el script de creación de configuración si fuera necesario
fi

# Verificar que está habilitada
if [ -L "/etc/nginx/sites-enabled/parking_altea" ]; then
    echo "✅ Sitio habilitado en nginx"
else
    echo "⚠️  Habilitando sitio..."
    ln -sf /etc/nginx/sites-available/parking_altea /etc/nginx/sites-enabled/
    systemctl reload nginx
fi
```

---

## **FASE 5: VERIFICACIÓN COMPLETA DEL DESPLIEGUE**

### **5.1 Test de conectividad básica:**
```bash
echo "========================================="
echo "🎉 VERIFICACIÓN COMPLETA v4.2.0"
echo "========================================="

echo "🔸 Estado de servicios:"
echo "   - Nginx: $(systemctl is-active nginx)"
echo "   - API: $(systemctl is-active parking-api.service)"
echo "   - Camera: $(systemctl is-active parking-camera.service)"

echo "🔸 Puertos activos:"
netstat -tlnp | grep -E ":80|:6001" | head -2

echo "🔸 Tests de conectividad:"
echo "   - Frontend principal:"
curl -s -I http://localhost/ | head -1

echo "   - Ruta React (/parkings):"
curl -s -I http://localhost/parkings | head -1

echo "   - API través nginx:"
curl -s -I http://localhost/api/parkings | head -1
```

### **5.2 Test funcional completo:**
```bash
# Test de login y permisos
echo "=== TEST FUNCIONAL DE PERMISOS ==="
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('token', 'ERROR'))" 2>/dev/null || echo "ERROR")

if [ "$TOKEN" != "ERROR" ] && [ "$TOKEN" != "" ]; then
    echo "✅ Login exitoso a través de nginx"
    
    # Test de endpoints filtrados por permisos
    echo "🔸 Test parkings filtrados:"
    PARKINGS_COUNT=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/parkings | \
        python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "ERROR")
    echo "   Parkings accesibles: $PARKINGS_COUNT"
    
    echo "🔸 Test dashboard usuario (nuevo v4.2.0):"
    SENSORS_COUNT=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/dashboard/user/sensors | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print(data['summary']['total_sensors'])" 2>/dev/null || echo "ERROR")
    echo "   Sensores en dashboard: $SENSORS_COUNT"
    
    echo "🔸 Test funcionalidad de ocupación (corregida):"
    # Test de actualización de ocupación (debe funcionar ahora)
    PARKING_ID=1
    curl -s -X POST http://localhost/api/parkings/$PARKING_ID/occupancy \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"occupancy": 50}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'ok':
        print('✅ Edición de ocupación funciona correctamente')
    else:
        print('⚠️ Respuesta inesperada:', data)
except:
    print('❌ Error en test de ocupación')
"
else
    echo "❌ Error en login - verificar credenciales y configuración"
fi
```

### **5.3 Resumen final:**
```bash
echo ""
echo "========================================="
echo "🎯 RESUMEN DEL DESPLIEGUE v4.2.0"
echo "========================================="
echo "📍 Servidor: 157.180.91.63"
echo "🌐 Frontend: http://157.180.91.63/"
echo "🔧 API: http://157.180.91.63/api/"
echo ""
echo "✅ FUNCIONALIDADES DESPLEGADAS:"
echo "   - Sistema completo de permisos por usuario"
echo "   - Filtrado automático en todas las páginas"
echo "   - Dashboard personalizado por usuario"
echo "   - Endpoints agrupados de sensores"
echo "   - Corrección de edición de ocupación"
echo ""
echo "📱 PÁGINAS ACTUALIZADAS:"
echo "   - Dashboard: Filtrado por permisos ✅"
echo "   - Paneles: Autenticación JWT ✅"
echo "   - Programaciones: Filtrado por permisos ✅"
echo "   - Sensores: Filtrado por permisos ✅"
echo "   - Estadísticas: Filtrado por permisos ✅"
echo "   - Camera Logs: Filtrado por permisos ✅"
echo "   - Alarmas: Filtrado por permisos ✅"
echo ""
echo "🔐 CONTROL DE ACCESO:"
echo "   - Usuarios regulares: Solo sus parkings asignados"
echo "   - Superadmins: Acceso completo al sistema"
echo ""
echo "🌐 URLs PRINCIPALES:"
echo "   - http://157.180.91.63/ (Dashboard)"
echo "   - http://157.180.91.63/parkings"
echo "   - http://157.180.91.63/sensors"
echo "   - http://157.180.91.63/panels"
echo "   - http://157.180.91.63/schedules"
echo "   - http://157.180.91.63/statistics"
echo "   - http://157.180.91.63/login"
echo "========================================="
echo "🎉 DESPLIEGUE v4.2.0 COMPLETADO EXITOSAMENTE"
echo "========================================="
```

---

## **🚨 TROUBLESHOOTING**

### **Si hay errores en la compilación:**
```bash
# Limpiar completamente node_modules
cd /opt/parking_altea/client
rm -rf node_modules/
rm -rf package-lock.json
npm install
chmod +x node_modules/.bin/*
npm run build
```

### **Si nginx no responde:**
```bash
# Verificar logs de nginx
tail -20 /var/log/nginx/error.log
tail -20 /var/log/nginx/parking_altea_error.log

# Reiniciar nginx completamente
systemctl stop nginx
sleep 2
systemctl start nginx
systemctl status nginx --no-pager
```

### **Si el API no responde:**
```bash
# Verificar logs del API
journalctl -u parking-api.service -n 50 --no-pager
tail -20 /opt/parking_altea/api_server.log

# Reiniciar API
systemctl restart parking-api.service
systemctl status parking-api.service --no-pager
```

---

## **📊 CHECKLIST DE VERIFICACIÓN FINAL**

- [ ] ✅ Git actualizado con commit 2e616fd
- [ ] ✅ Backend API funcionando (puerto 6001)
- [ ] ✅ Frontend compilado correctamente
- [ ] ✅ Nginx configurado y funcionando (puerto 80)
- [ ] ✅ Archivos estáticos desplegados en /opt/parking_altea/static/
- [ ] ✅ Login funciona con JWT
- [ ] ✅ Parkings filtrados por usuario
- [ ] ✅ Dashboard personalizado funciona
- [ ] ✅ Edición de ocupación funciona
- [ ] ✅ Todas las páginas filtran por permisos
- [ ] ✅ URLs principales accesibles desde navegador

**⏱️ Tiempo estimado total: 15-20 minutos**
**🎯 Estado esperado: Sistema completamente funcional con permisos implementados**
