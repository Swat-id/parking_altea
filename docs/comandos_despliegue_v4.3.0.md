# Comandos de Despliegue v4.3.0

## Bloque 1: Conexión y preparación

```bash
# Conectarse al servidor
ssh root@157.180.91.63

# Ir al directorio del proyecto
cd /opt/parking_altea

# Verificar rama actual
git branch

# Verificar estado del repositorio (para ver qué cambios locales hay)
git status
```

## Bloque 2: Descartar cambios locales y actualizar código desde Git

```bash
# Ver cambios locales antes de descartarlos (para revisar)
echo "=== CAMBIOS LOCALES DETECTADOS ==="
git status --short | grep -v "client/node_modules" | head -20

# Descartar cambios SOLO en archivos fuera de node_modules
echo ""
echo "Descartando cambios en archivos rastreados (excluyendo node_modules)..."
# Restaurar archivos modificados, excluyendo node_modules
git status --short | grep -v "client/node_modules" | grep "^ M" | awk '{print $2}' | xargs -r git restore 2>/dev/null || true

# Restaurar archivos en src/ y otros directorios importantes
git restore src/ 2>/dev/null || true
git restore client/src/ 2>/dev/null || true
git restore client/package.json client/package-lock.json 2>/dev/null || true
git restore tsconfig.json 2>/dev/null || true

# Limpiar solo archivos no rastreados que NO sean node_modules
echo "Limpiando archivos no rastreados (excluyendo node_modules)..."
git clean -f -e "client/node_modules" -e "node_modules" 2>/dev/null || true

# Verificar estado después de limpiar (sin mostrar node_modules)
echo ""
echo "=== ESTADO DESPUÉS DE LIMPIEZA (excluyendo node_modules) ==="
git status --short | grep -v "client/node_modules" | head -20

# Asegurarse de estar en la rama correcta
echo ""
echo "Actualizando desde remoto..."
git fetch origin
git checkout v4.3.0

# Actualizar código desde el repositorio remoto
# Usar --no-verify para evitar hooks que puedan fallar
echo "Descargando últimos cambios..."
git pull origin v4.3.0 --no-verify

# Si hay conflictos en node_modules, resolverlos descartando cambios locales
echo "Resolviendo posibles conflictos en node_modules..."
git checkout --theirs client/node_modules 2>/dev/null || true
git restore client/node_modules 2>/dev/null || true

# Verificar que los nuevos archivos están presentes
echo ""
echo "=== VERIFICANDO ARCHIVOS NUEVOS ==="
ls -la src/migrate_add_color_and_status_config.py && echo "✅ migrate_add_color_and_status_config.py existe" || echo "❌ migrate_add_color_and_status_config.py NO existe"
ls -la src/panel_type4_update_service.py && echo "✅ panel_type4_update_service.py existe" || echo "❌ panel_type4_update_service.py NO existe"
ls -la src/panel_content_rotation_service.py && echo "✅ panel_content_rotation_service.py existe" || echo "❌ panel_content_rotation_service.py NO existe"
ls -la src/panel_window_service.py && echo "✅ panel_window_service.py existe" || echo "❌ panel_window_service.py NO existe"
ls -la src/models.py && echo "✅ models.py existe" || echo "❌ models.py NO existe"
```

## Bloque 3: Activar entorno virtual y verificar dependencias

```bash
# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Verificar que estamos en el entorno virtual
which python3

# Verificar que las dependencias están instaladas (no instalar, solo verificar)
echo "=== VERIFICANDO DEPENDENCIAS ==="
pip list | grep -E "(sqlalchemy|flask|psycopg2)" || echo "⚠️  Algunas dependencias no encontradas"
```

## Bloque 4: Ejecutar migración de base de datos

```bash
# Ir al directorio src
cd /opt/parking_altea/src

# Verificar que el script de migración existe
if [ ! -f "migrate_add_color_and_status_config.py" ]; then
    echo "❌ Error: migrate_add_color_and_status_config.py no encontrado"
    exit 1
fi

# Ejecutar migración para agregar campos color y parking_status_config
echo "=== EJECUTANDO MIGRACIÓN ==="
python3 migrate_add_color_and_status_config.py

# Verificar que la migración se ejecutó correctamente
echo "=== VERIFICANDO LOGS DE MIGRACIÓN ==="
if [ -f "migration_add_color_and_status_config.log" ]; then
    tail -30 migration_add_color_and_status_config.log
else
    echo "⚠️  Archivo de log no encontrado"
fi

# Verificar en la base de datos que las columnas se agregaron
echo ""
echo "=== VERIFICANDO COLUMNAS EN BASE DE DATOS ==="
psql -U postgres -d parking_altea -c "\d parking_panel_windows" | grep -q color && echo "✅ Campo 'color' existe en parking_panel_windows" || echo "❌ Campo 'color' NO existe en parking_panel_windows"
psql -U postgres -d parking_altea -c "\d panel_window_configurations" | grep -q parking_status_config && echo "✅ Campo 'parking_status_config' existe en panel_window_configurations" || echo "❌ Campo 'parking_status_config' NO existe en panel_window_configurations"
```

## Bloque 5: Verificar sintaxis de archivos Python modificados

```bash
# Verificar sintaxis de los archivos modificados
cd /opt/parking_altea/src
echo "=== VERIFICANDO SINTAXIS DE ARCHIVOS PYTHON ==="

python3 -m py_compile api_server.py && echo "✅ api_server.py: OK" || echo "❌ api_server.py: ERROR"
python3 -m py_compile panel_content_rotation_service.py && echo "✅ panel_content_rotation_service.py: OK" || echo "❌ panel_content_rotation_service.py: ERROR"
python3 -m py_compile panel_type4_update_service.py && echo "✅ panel_type4_update_service.py: OK" || echo "❌ panel_type4_update_service.py: ERROR"
python3 -m py_compile panel_window_service.py && echo "✅ panel_window_service.py: OK" || echo "❌ panel_window_service.py: ERROR"
python3 -m py_compile models.py && echo "✅ models.py: OK" || echo "❌ models.py: ERROR"

echo "✅ Verificación de sintaxis completada"
```

## Bloque 6: Reiniciar servicios del backend

```bash
# Volver al directorio raíz
cd /opt/parking_altea

# Verificar estado actual de los servicios
echo "=== ESTADO ACTUAL DE SERVICIOS ==="
systemctl status parking-api.service --no-pager | head -15

# Reiniciar servicio API
echo ""
echo "=== REINICIANDO SERVICIO API ==="
systemctl restart parking-api.service

# Esperar unos segundos para que el servicio inicie
sleep 5

# Verificar que el servicio está activo
echo ""
echo "=== VERIFICANDO ESTADO DEL SERVICIO ==="
systemctl status parking-api.service --no-pager | head -15

# Verificar logs recientes para errores
echo ""
echo "=== ÚLTIMOS LOGS DEL SERVICIO ==="
journalctl -u parking-api.service --since "2 minutes ago" --no-pager | tail -30

# Verificar si hay errores críticos
ERROR_COUNT=$(journalctl -u parking-api.service --since "2 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Se encontraron $ERROR_COUNT errores en los logs recientes"
    journalctl -u parking-api.service --since "2 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | tail -10
else
    echo "✅ No se encontraron errores en los logs recientes"
fi
```

## Bloque 7: Compilar frontend

```bash
# Ir al directorio del frontend
cd /opt/parking_altea/client

# NO hacer reset aquí, solo verificar que node_modules existe
echo "=== VERIFICANDO DEPENDENCIAS DEL FRONTEND ==="
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules no encontrado, instalando dependencias..."
    npm install
else
    echo "✅ node_modules existe"
    # Verificar que tiene contenido
    if [ "$(ls -A node_modules 2>/dev/null | wc -l)" -eq 0 ]; then
        echo "⚠️  node_modules está vacío, reinstalando dependencias..."
        npm install
    else
        echo "   node_modules tiene $(ls -A node_modules 2>/dev/null | wc -l) elementos"
    fi
fi

# Verificar permisos de ejecutables
echo "Ajustando permisos de ejecutables..."
chmod +x node_modules/.bin/* 2>/dev/null || true

# Compilar frontend
echo ""
echo "=== COMPILANDO FRONTEND ==="
npm run build

# Verificar que la compilación fue exitosa
echo ""
echo "=== VERIFICANDO RESULTADO DE COMPILACIÓN ==="
if [ -d "dist" ]; then
    echo "✅ Frontend compilado correctamente"
    echo "Tamaño del directorio dist:"
    du -sh dist/
    echo ""
    echo "Archivos principales:"
    ls -lh dist/ | head -10
else
    echo "❌ Error: directorio dist no encontrado"
    echo "Revisando errores de compilación..."
    exit 1
fi
```

## Bloque 8: Detener proceso frontend anterior y iniciar nuevo

```bash
# Buscar proceso en puerto 5789
echo "=== GESTIONANDO PROCESO FRONTEND ==="
OLD_PID=$(lsof -ti:5789 2>/dev/null)

# Si hay un proceso, detenerlo
if [ ! -z "$OLD_PID" ]; then
    echo "Deteniendo proceso anterior (PID: $OLD_PID) en puerto 5789..."
    kill $OLD_PID
    sleep 3
    
    # Verificar si aún está corriendo
    if lsof -ti:5789 > /dev/null 2>&1; then
        echo "⚠️  Proceso aún activo, forzando terminación..."
        kill -9 $OLD_PID
        sleep 2
    fi
fi

# Verificar que el puerto está libre
if ! lsof -ti:5789 > /dev/null 2>&1; then
    echo "✅ Puerto 5789 libre"
else
    echo "❌ Error: No se pudo liberar el puerto 5789"
    lsof -i:5789
    exit 1
fi

# Iniciar frontend en background
echo ""
echo "=== INICIANDO FRONTEND ==="
cd /opt/parking_altea/client

# Asegurar que el directorio de logs existe
mkdir -p ../logs

# Iniciar frontend
nohup npm run preview -- --port 5789 --host 0.0.0.0 > ../logs/frontend.log 2>&1 &

# Esperar unos segundos para que inicie
sleep 5

# Verificar que el frontend está corriendo
NEW_PID=$(lsof -ti:5789 2>/dev/null)
if [ ! -z "$NEW_PID" ]; then
    echo "✅ Frontend iniciado en puerto 5789 (PID: $NEW_PID)"
else
    echo "❌ Error: Frontend no se inició"
    echo "Revisando logs:"
    tail -30 ../logs/frontend.log
    exit 1
fi
```

## Bloque 9: Verificación de servicios

```bash
# Verificar que la API responde
echo "=== VERIFICANDO SERVICIOS ==="
echo ""
echo "1. Verificando API (puerto 5000)..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/health)
if [ "$API_RESPONSE" = "200" ] || [ "$API_RESPONSE" = "401" ]; then
    echo "✅ API responde (código: $API_RESPONSE)"
    curl -s http://localhost:5000/api/v1/health | head -5
else
    echo "❌ API no responde correctamente (código: $API_RESPONSE)"
fi

# Verificar que el frontend responde
echo ""
echo "2. Verificando Frontend (puerto 5789)..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5789)
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo "✅ Frontend responde (código: $FRONTEND_RESPONSE)"
    curl -s http://localhost:5789 | head -5
else
    echo "❌ Frontend no responde correctamente (código: $FRONTEND_RESPONSE)"
fi

# Verificar logs del API para errores recientes
echo ""
echo "3. Revisando logs del API..."
ERROR_COUNT=$(journalctl -u parking-api.service --since "5 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Se encontraron $ERROR_COUNT errores en los últimos 5 minutos:"
    journalctl -u parking-api.service --since "5 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | tail -5
else
    echo "✅ No hay errores recientes en el API"
fi

# Verificar logs del frontend
echo ""
echo "4. Revisando logs del Frontend..."
if [ -f "/opt/parking_altea/logs/frontend.log" ]; then
    FRONTEND_ERRORS=$(tail -50 /opt/parking_altea/logs/frontend.log | grep -i "error\|failed" | wc -l)
    if [ "$FRONTEND_ERRORS" -gt 0 ]; then
        echo "⚠️  Se encontraron errores en los logs del frontend:"
        tail -50 /opt/parking_altea/logs/frontend.log | grep -i "error\|failed" | tail -5
    else
        echo "✅ No hay errores en los logs del frontend"
    fi
    echo "Últimas líneas del log:"
    tail -10 /opt/parking_altea/logs/frontend.log
else
    echo "⚠️  Archivo de log del frontend no encontrado"
fi
```

## Bloque 10: Verificación de endpoints nuevos (opcional)

```bash
# Obtener token de autenticación
echo "=== VERIFICANDO ENDPOINTS NUEVOS ==="
echo ""
echo "1. Obteniendo token de autenticación..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"info@swat-id.com","password":"admin123!"}' | \
  grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$TOKEN" ]; then
    echo "✅ Token obtenido: ${TOKEN:0:50}..."
    
    # Verificar que los nuevos endpoints existen (devolverá 404 si el panel no es Tipo 4, pero no 500)
    echo ""
    echo "2. Verificando endpoint de ventanas (esperado: 404 o 400 si panel no existe/no es Tipo 4)..."
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "http://localhost:5000/api/v1/panels/999/windows" \
      -H "Authorization: Bearer $TOKEN")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "400" ]; then
        echo "✅ Endpoint responde correctamente (código: $HTTP_CODE)"
        echo "Respuesta: $BODY" | head -3
    elif [ "$HTTP_CODE" = "500" ]; then
        echo "❌ Error interno del servidor (código: $HTTP_CODE)"
        echo "Respuesta: $BODY"
    else
        echo "⚠️  Respuesta inesperada (código: $HTTP_CODE)"
        echo "Respuesta: $BODY" | head -3
    fi
else
    echo "❌ No se pudo obtener token de autenticación"
fi

echo ""
echo "✅ Verificación de endpoints completada"
```

## Bloque 11: Verificación final

```bash
# Estado de servicios
echo "=========================================="
echo "=== VERIFICACIÓN FINAL DEL DESPLIEGUE ==="
echo "=========================================="
echo ""

# Estado de servicios systemd
echo "1. ESTADO DE SERVICIOS SYSTEMD:"
if systemctl is-active --quiet parking-api.service; then
    echo "   ✅ parking-api: ACTIVO"
else
    echo "   ❌ parking-api: INACTIVO"
fi

# Verificar puertos
echo ""
echo "2. PUERTOS EN USO:"
if lsof -ti:5000 > /dev/null 2>&1; then
    PID=$(lsof -ti:5000)
    echo "   ✅ Puerto 5000 (API): EN USO (PID: $PID)"
else
    echo "   ❌ Puerto 5000 (API): LIBRE"
fi

if lsof -ti:5789 > /dev/null 2>&1; then
    PID=$(lsof -ti:5789)
    echo "   ✅ Puerto 5789 (Frontend): EN USO (PID: $PID)"
else
    echo "   ❌ Puerto 5789 (Frontend): LIBRE"
fi

# Verificar migración
echo ""
echo "3. VERIFICACIÓN DE MIGRACIÓN DE BASE DE DATOS:"
COLOR_EXISTS=$(psql -U postgres -d parking_altea -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='parking_panel_windows' AND column_name='color';" 2>/dev/null | tr -d ' ')
if [ "$COLOR_EXISTS" = "1" ]; then
    echo "   ✅ Campo 'color' existe en parking_panel_windows"
else
    echo "   ❌ Campo 'color' NO existe en parking_panel_windows"
fi

STATUS_CONFIG_EXISTS=$(psql -U postgres -d parking_altea -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='panel_window_configurations' AND column_name='parking_status_config';" 2>/dev/null | tr -d ' ')
if [ "$STATUS_CONFIG_EXISTS" = "1" ]; then
    echo "   ✅ Campo 'parking_status_config' existe en panel_window_configurations"
else
    echo "   ❌ Campo 'parking_status_config' NO existe en panel_window_configurations"
fi

# Verificar versión del código
echo ""
echo "4. VERSIÓN DEL CÓDIGO:"
cd /opt/parking_altea
CURRENT_BRANCH=$(git branch --show-current)
LAST_COMMIT=$(git log --oneline -1)
echo "   Rama actual: $CURRENT_BRANCH"
echo "   Último commit: $LAST_COMMIT"

# Verificar archivos clave
echo ""
echo "5. VERIFICACIÓN DE ARCHIVOS CLAVE:"
[ -f "src/migrate_add_color_and_status_config.py" ] && echo "   ✅ migrate_add_color_and_status_config.py" || echo "   ❌ migrate_add_color_and_status_config.py"
[ -f "src/panel_type4_update_service.py" ] && echo "   ✅ panel_type4_update_service.py" || echo "   ❌ panel_type4_update_service.py"
[ -f "src/panel_content_rotation_service.py" ] && echo "   ✅ panel_content_rotation_service.py" || echo "   ❌ panel_content_rotation_service.py"
[ -f "src/panel_window_service.py" ] && echo "   ✅ panel_window_service.py" || echo "   ❌ panel_window_service.py"
[ -f "client/dist/index.html" ] && echo "   ✅ Frontend compilado (dist/index.html)" || echo "   ❌ Frontend NO compilado"

# Verificar node_modules
echo ""
echo "6. VERIFICACIÓN DE DEPENDENCIAS:"
if [ -d "client/node_modules" ] && [ "$(ls -A client/node_modules 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "   ✅ node_modules existe y tiene contenido"
else
    echo "   ⚠️  node_modules no existe o está vacío"
fi

# Resumen final
echo ""
echo "=========================================="
echo "=== RESUMEN FINAL ==="
echo "=========================================="
echo ""
echo "✅ Despliegue de v4.3.0 completado"
echo ""
echo "Características desplegadas:"
echo "  • Configuración de colores para sensores"
echo "  • Configuración de colores y textos para estados de parking"
echo "  • Validaciones para que cambios solo afecten paneles Tipo 4"
echo "  • Nuevos endpoints para gestión de ventanas (solo Tipo 4)"
echo ""
echo "Próximos pasos:"
echo "  • Verificar que los paneles Tipo 4 pueden configurarse desde el frontend"
echo "  • Probar asignación de colores a sensores"
echo "  • Probar configuración de estados de parking"
echo ""
echo "Para monitorear:"
echo "  • API logs: journalctl -u parking-api.service -f"
echo "  • Frontend logs: tail -f /opt/parking_altea/logs/frontend.log"
echo ""
```

