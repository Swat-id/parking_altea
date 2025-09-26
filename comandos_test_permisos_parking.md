# 🧪 COMANDOS PARA PROBAR CORRECCIÓN DE PERMISOS POR PARKING

## **📋 PROBLEMA SOLUCIONADO:**

**Antes**: Al asignar un usuario a un parking, NO veía automáticamente los paneles y sensores de ese parking.

**Después**: Al asignar un usuario a un parking, automáticamente ve:
- ✅ **Parkings** asignados
- ✅ **Paneles** del parking (directo + por parking)
- ✅ **Sensores** del parking (ya funcionaba)
- ✅ **Cámaras** del parking (directo + por parking)

---

## **🔧 CAMBIOS REALIZADOS:**

### **Backend Changes:**
```python
# src/auth.py - get_user_accessible_panel_ids()
# ANTES: Solo paneles asignados directamente en UserPanel
# DESPUÉS: Paneles directos + paneles de parkings asignados

# src/auth.py - get_user_accessible_access_ids()  
# ANTES: Solo accesos asignados directamente en UserAccess
# DESPUÉS: Accesos directos + accesos de parkings asignados

# src/api_server.py - /api/panels endpoint
# Simplificado para usar solo accessible_panel_ids (que ahora incluye por parking)
```

---

## **🚀 COMANDOS DE DESPLIEGUE:**

### **1. Subir cambios a Git (LOCAL):**
```bash
# Verificar cambios
git status

# Agregar cambios
git add .

# Commit descriptivo
git commit -m "🔧 Fix: Paneles y cámaras ahora heredan permisos de parkings asignados

- Backend: get_user_accessible_panel_ids() incluye paneles de parkings asignados
- Backend: get_user_accessible_access_ids() incluye cámaras de parkings asignados  
- Logic: Usuario con parking asignado → ve automáticamente paneles/cámaras del parking
- Simplify: /api/panels usa solo accessible_panel_ids (más eficiente)

Fixes: Usuarios con parkings asignados no veían paneles/cámaras
Affects: Páginas de Paneles, Camera Logs con permisos por parking"

# Push al repositorio
git push origin v4.1.0
```

### **2. Desplegar en servidor:**
```bash
# Conectar al servidor
ssh root@ubuntu-16gb-hel1-1

# Actualizar código
cd /opt/parking_altea
git pull origin v4.1.0

# Reiniciar API para aplicar cambios backend
systemctl restart parking-api.service

# Verificar estado
systemctl status parking-api.service --no-pager
```

---

## **🧪 COMANDOS DE VERIFICACIÓN:**

### **Ejecuta en el servidor para probar la corrección:**

```bash
# Test básico de login
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('token', 'ERROR'))" 2>/dev/null || echo "ERROR")

if [ "$TOKEN" != "ERROR" ] && [ "$TOKEN" != "" ]; then
    echo "✅ Login exitoso como superadmin"
    
    # Crear usuario de prueba (si no existe)
    echo "🔸 Creando usuario de prueba..."
    curl -s -X POST http://localhost/api/users \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name": "Usuario Test", "email": "test@parking.com", "password": "test123", "role": "user"}' > /dev/null
    
    # Obtener ID del usuario de prueba
    USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/users | \
        python3 -c "
import sys, json
try:
    users = json.load(sys.stdin)
    for user in users:
        if user.get('email') == 'test@parking.com':
            print(user['id'])
            break
    else:
        print('ERROR')
except:
    print('ERROR')
")
    
    if [ "$USER_ID" != "ERROR" ] && [ "$USER_ID" != "" ]; then
        echo "   - Usuario test ID: $USER_ID"
        
        # Asignar parking al usuario (solo parking, NO paneles directos)
        echo "🔸 Asignando parking 1 al usuario test..."
        curl -s -X POST http://localhost/api/users/$USER_ID/assign \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"parking_ids": [1]}' > /dev/null
        
        # Login como usuario test
        TEST_TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
          -H "Content-Type: application/json" \
          -d '{"email": "test@parking.com", "password": "test123"}' | \
          python3 -c "import sys, json; print(json.load(sys.stdin).get('token', 'ERROR'))" 2>/dev/null || echo "ERROR")
        
        if [ "$TEST_TOKEN" != "ERROR" ] && [ "$TEST_TOKEN" != "" ]; then
            echo "✅ Login exitoso como usuario test"
            
            # Test 1: Parkings accesibles
            PARKINGS_COUNT=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" http://localhost/api/parkings | \
                python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "ERROR")
            echo "   - Parkings accesibles: $PARKINGS_COUNT (debería ser >= 1)"
            
            # Test 2: Paneles accesibles (CORREGIDO - ahora debería ver paneles del parking)
            PANELS_COUNT=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" http://localhost/api/panels | \
                python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "ERROR")
            echo "   - Paneles accesibles: $PANELS_COUNT (ANTES: 0, DESPUÉS: >= 1 si hay paneles en parking 1)"
            
            # Test 3: Sensores accesibles
            SENSORS_COUNT=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" http://localhost/api/sensors | \
                python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "ERROR")
            echo "   - Sensores accesibles: $SENSORS_COUNT (debería ver sensores del parking 1)"
            
            # Test 4: Camera logs accesibles
            curl -s -H "Authorization: Bearer $TEST_TOKEN" "http://localhost/api/camera-logs-v2?per_page=1" | \
                python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    total = data.get('pagination', {}).get('total_count', 0)
    print(f'   - Camera logs accesibles: {total} (debería ver logs del parking 1)')
except:
    print('   - Camera logs: Error en respuesta')
"
            
            echo ""
            echo "🎯 RESULTADO ESPERADO:"
            echo "   ✅ Parkings: >= 1 (parking asignado)"
            echo "   ✅ Paneles: >= 1 (paneles del parking - CORREGIDO)"
            echo "   ✅ Sensores: >= 0 (sensores del parking - ya funcionaba)"
            echo "   ✅ Camera logs: >= 0 (logs del parking - CORREGIDO)"
            
        else
            echo "❌ Error en login como usuario test"
        fi
    else
        echo "❌ Error obteniendo ID del usuario test"
    fi
else
    echo "❌ Error en login como superadmin"
fi

echo ""
echo "🌐 PRUEBA MANUAL DESDE NAVEGADOR:"
echo "1. Login como: test@parking.com / test123"
echo "2. Ir a: http://157.180.91.63/panels"
echo "3. Verificar que ahora SÍ aparecen paneles del parking asignado"
echo "4. Ir a: http://157.180.91.63/camera-logs"
echo "5. Verificar que SÍ aparecen logs de cámaras del parking"
```

---

## **📊 COMPARACIÓN ANTES/DESPUÉS:**

### **❌ ANTES (Problema):**
```
Usuario asignado a Parking 1:
✅ Ve Parking 1 en /parkings
❌ NO ve paneles en /panels (lista vacía)
❌ NO ve camera logs en /camera-logs (lista vacía)
✅ Ve sensores en /sensors (funcionaba)
```

### **✅ DESPUÉS (Solucionado):**
```
Usuario asignado a Parking 1:
✅ Ve Parking 1 en /parkings
✅ Ve paneles del Parking 1 en /panels (CORREGIDO)
✅ Ve camera logs del Parking 1 en /camera-logs (CORREGIDO)
✅ Ve sensores del Parking 1 en /sensors (funcionaba)
```

---

**📅 Fecha:** $(date)  
**🎯 Objetivo:** Permisos por parking funcionando completamente  
**🔖 Versión:** v4.2.1 - Parking Permission Inheritance Fix
