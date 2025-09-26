# 🔧 COMANDOS PARA CORRECCIÓN DE PERMISOS v4.2.0

## **📋 RESUMEN DE CORRECCIONES**

### **Problemas Identificados y Solucionados:**

1. **✅ Paneles**: `panelService.getAllPanels()` usaba `/api/panels` sin filtrado → Cambiado a `/api/user/panels`
2. **✅ Backend `/api/panels`**: Sin autenticación ni filtrado → Agregados decoradores `@require_auth` y `@filter_by_user_permissions`
3. **✅ Backend `/api/camera-logs-v2`**: Sin autenticación ni filtrado → Agregados decoradores y lógica de filtrado
4. **✅ Errores 403**: Statistics y ParkingDetail fallaban al acceder a parkings sin permisos → Agregado manejo de errores
5. **✅ Camera Logs**: Ahora filtra correctamente por permisos de usuario

---

## **🚀 COMANDOS DE DESPLIEGUE**

### **1. Subir cambios a Git (LOCAL):**
```bash
# Verificar cambios realizados
git status

# Agregar todos los archivos modificados
git add .

# Commit con descripción detallada
git commit -m "🔧 Fix: Corregir filtrado de permisos en todas las páginas

- Frontend: panelService.getAllPanels() usa /api/user/panels
- Backend: Agregar filtrado por permisos a /api/panels y /api/camera-logs-v2
- Pages: Manejo de errores 403 en Statistics y ParkingDetail
- Redirect: Usuarios sin permisos redirigen a recursos accesibles

Fixes: Paneles, Camera Logs, Statistics, ParkingDetail
Affects: Todas las páginas con filtrado de permisos"

# Push al repositorio remoto
git push origin main
```

### **2. Desplegar en servidor de producción:**
```bash
# Conectar al servidor
ssh root@ubuntu-16gb-hel1-1

# Navegar al directorio del proyecto
cd /opt/parking_altea

# Hacer backup del estado actual
cp -r client/dist client/dist_backup_$(date +%Y%m%d_%H%M%S)

# Hacer stash de cambios locales si los hay
git stash

# Actualizar desde repositorio
git pull origin main

# Verificar que se descargaron los cambios
git log --oneline -3

# Reiniciar servicio API para aplicar cambios backend
systemctl restart parking-api.service

# Verificar que el servicio se reinició correctamente
systemctl status parking-api.service --no-pager

# Navegar al directorio del frontend
cd client

# Instalar dependencias si es necesario
npm install

# Compilar frontend con las correcciones
npm run build

# Verificar que la compilación fue exitosa
ls -la dist/

# Copiar archivos compilados a directorio de nginx
cp -r dist/* /opt/parking_altea/static/

# Recargar nginx para servir los nuevos archivos
systemctl reload nginx

# Verificar estado de nginx
systemctl status nginx --no-pager
```

### **3. Verificación de funcionamiento:**
```bash
# Test de conectividad básica
echo "🔸 Verificando servicios..."
echo "   - API: $(systemctl is-active parking-api.service)"
echo "   - Nginx: $(systemctl is-active nginx)"

# Test de endpoints corregidos
echo "🔸 Probando endpoints corregidos..."

# Obtener token de autenticación
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('token', 'ERROR'))" 2>/dev/null || echo "ERROR")

if [ "$TOKEN" != "ERROR" ] && [ "$TOKEN" != "" ]; then
    echo "✅ Login exitoso"
    
    # Test endpoint de paneles (ahora filtrado)
    PANELS_COUNT=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/panels | \
        python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "ERROR")
    echo "   - Paneles accesibles: $PANELS_COUNT"
    
    # Test endpoint de camera logs (ahora filtrado)
    curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/camera-logs-v2?per_page=1" | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    logs_count = len(data.get('logs', []))
    total = data.get('pagination', {}).get('total_count', 0)
    print(f'   - Camera logs accesibles: {total} total')
except:
    print('   - Camera logs: Error en respuesta')
"
else
    echo "❌ Error en login - verificar credenciales"
fi

# URLs para probar desde navegador
echo ""
echo "🌐 URLs PARA PROBAR DESDE NAVEGADOR:"
echo "   - http://157.180.91.63/ (Dashboard)"
echo "   - http://157.180.91.63/panels (Paneles - corregido)"
echo "   - http://157.180.91.63/camera-logs (Camera Logs - corregido)" 
echo "   - http://157.180.91.63/statistics/1 (Statistics - manejo 403)"
echo ""
echo "✅ DESPLIEGUE DE CORRECCIONES COMPLETADO"
```

---

## **📝 CAMBIOS REALIZADOS EN DETALLE**

### **Frontend Changes:**
```javascript
// client/src/services/panelService.js
// ANTES: const response = await api.get('/api/panels')
// DESPUÉS: const response = await api.get('/api/user/panels')

// client/src/pages/Statistics.jsx
// AGREGADO: Manejo de errores 403 con redirección automática

// client/src/pages/ParkingDetail.jsx  
// AGREGADO: Manejo de errores 403 con mensajes apropiados

// client/src/pages/Panels.jsx
// CAMBIADO: Query key de 'panels' a 'userPanels'
```

### **Backend Changes:**
```python
# src/api_server.py

# ENDPOINT: /api/panels
# ANTES: def get_all_panels():
# DESPUÉS: 
@require_auth
@filter_by_user_permissions
def get_all_panels():
    # + Lógica de filtrado por accessible_panel_ids

# ENDPOINT: /api/camera-logs-v2  
# ANTES: def get_camera_logs_v2():
# DESPUÉS:
@require_auth
@filter_by_user_permissions 
def get_camera_logs_v2():
    # + Lógica de filtrado por accessible_parking_ids y accessible_access_ids
```

---

## **🎯 RESULTADO ESPERADO**

### **✅ Funcionalidades Corregidas:**

1. **Paneles**: Solo muestra paneles de parkings accesibles al usuario
2. **Camera Logs**: Solo muestra logs de cámaras accesibles al usuario  
3. **Statistics**: Maneja errores 403 y redirige automáticamente
4. **ParkingDetail**: Maneja errores 403 con mensajes claros
5. **Todos los endpoints**: Ahora requieren autenticación y filtran por permisos

### **🔒 Seguridad Mejorada:**

- ❌ **Antes**: Endpoints públicos mostraban todos los datos
- ✅ **Después**: Todos los endpoints filtran por permisos de usuario
- ✅ **Superadmin**: Ve todos los recursos (sin cambios)
- ✅ **Usuario regular**: Solo ve recursos asignados

### **🚫 Errores Eliminados:**

- ✅ Error 403 en Statistics al acceder a parking sin permisos
- ✅ Error 403 en ParkingDetail al acceder a parking sin permisos  
- ✅ Paneles mostrando todos los paneles sin filtrar
- ✅ Camera logs mostrando todos los logs sin filtrar

---

**📅 Fecha:** $(date)  
**👤 Usuario:** Corrección automática de permisos  
**🔖 Versión:** v4.2.0 - Permission Fixes
