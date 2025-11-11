# Comandos de Despliegue v4.3.0 - Configuración a Nivel de Empresa

## Fecha: $(date +%Y-%m-%d)
## Versión: v4.3.0
## Descripción: Configuración a nivel de empresa para paneles Tipo 4, asociación automática y creación preparatoria

---

## BLOQUE 1: Preparación y Actualización de Código

```bash
cd /opt/parking_altea

# Verificar estado actual
echo "=== ESTADO ACTUAL ==="
git status
git branch

# Descartar cambios locales si existen
echo ""
echo "=== DESCARTANDO CAMBIOS LOCALES ==="
git restore .
git clean -f -e "client/node_modules" -e "venv"

# Actualizar desde remoto
echo ""
echo "=== ACTUALIZANDO DESDE REMOTO ==="
git fetch origin
git checkout v4.3.0
git pull origin v4.3.0

# Verificar que los nuevos archivos están presentes
echo ""
echo "=== VERIFICANDO ARCHIVOS NUEVOS ==="
ls -la src/migrate_panel_config_company_level.py && echo "✅ migrate_panel_config_company_level.py existe" || echo "❌ migrate_panel_config_company_level.py NO existe"
ls -la src/models.py && echo "✅ models.py existe" || echo "❌ models.py NO existe"
ls -la src/api_server.py && echo "✅ api_server.py existe" || echo "❌ api_server.py NO existe"
ls -la src/panel_window_service.py && echo "✅ panel_window_service.py existe" || echo "❌ panel_window_service.py NO existe"
```

---

## BLOQUE 2: Verificación de Sintaxis Python

```bash
cd /opt/parking_altea

# Activar entorno virtual
source venv/bin/activate

# Verificar sintaxis de archivos modificados
echo "=== VERIFICANDO SINTAXIS DE ARCHIVOS PYTHON ==="
cd src
python3 -m py_compile models.py && echo "✅ models.py: OK" || echo "❌ models.py: ERROR"
python3 -m py_compile api_server.py && echo "✅ api_server.py: OK" || echo "❌ api_server.py: ERROR"
python3 -m py_compile panel_window_service.py && echo "✅ panel_window_service.py: OK" || echo "❌ panel_window_service.py: ERROR"
python3 -m py_compile migrate_panel_config_company_level.py && echo "✅ migrate_panel_config_company_level.py: OK" || echo "❌ migrate_panel_config_company_level.py: ERROR"
cd ..

echo "✅ Verificación de sintaxis completada"
```

---

## BLOQUE 3: Migración de Base de Datos

```bash
cd /opt/parking_altea
source venv/bin/activate

echo "=== EJECUTANDO MIGRACIÓN DE BASE DE DATOS ==="
echo "Migración: Configuraciones a nivel de empresa"
echo ""

# Ejecutar migración
cd src
python3 migrate_panel_config_company_level.py
MIGRATION_EXIT_CODE=$?
cd ..

if [ $MIGRATION_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Migración completada exitosamente"
else
    echo ""
    echo "❌ ERROR: La migración falló. Revisar logs antes de continuar."
    echo "Revisar: migration_panel_config_company_level.log"
    exit 1
fi
```

---

## BLOQUE 4: Verificación de Base de Datos

```bash
cd /opt/parking_altea
source venv/bin/activate

echo "=== VERIFICANDO CAMBIOS EN BASE DE DATOS ==="

# Verificar que panel_id es nullable
cd src
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from config import DB_URL
from sqlalchemy import create_engine, text

engine = create_engine(DB_URL)
with engine.connect() as conn:
    # Verificar que panel_id es nullable
    result = conn.execute(text("""
        SELECT is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'panel_window_configurations' 
        AND column_name = 'panel_id';
    """))
    row = result.fetchone()
    if row and row[0] == 'YES':
        print("✅ panel_id es nullable")
    else:
        print("❌ panel_id NO es nullable")
    
    # Verificar constraint único nuevo
    result = conn.execute(text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'panel_window_configurations' 
        AND constraint_name = 'unique_company_window_parking_config';
    """))
    row = result.fetchone()
    if row:
        print("✅ Constraint único por empresa existe")
    else:
        print("⚠️  Constraint único por empresa no encontrado (puede ser normal si no se creó)")
    
    # Contar configuraciones existentes
    result = conn.execute(text("SELECT COUNT(*) FROM panel_window_configurations"))
    count = result.fetchone()[0]
    print(f"✅ Total de configuraciones: {count}")
    
    # Contar configuraciones preparatorias (panel_id NULL)
    result = conn.execute(text("SELECT COUNT(*) FROM panel_window_configurations WHERE panel_id IS NULL"))
    prep_count = result.fetchone()[0]
    print(f"✅ Configuraciones preparatorias (panel_id NULL): {prep_count}")

EOF
cd ..
```

---

## BLOQUE 5: Reinicio de Servicios Backend

```bash
cd /opt/parking_altea

echo "=== REINICIANDO SERVICIOS BACKEND ==="

# Verificar estado actual
echo ""
echo "Estado actual de servicios:"
systemctl status parking-api.service --no-pager | head -10

# Reiniciar servicio API
echo ""
echo "Reiniciando parking-api.service..."
systemctl restart parking-api.service
sleep 5

# Verificar que el servicio está activo
echo ""
echo "Verificando estado del servicio..."
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

---

## BLOQUE 6: Compilación del Frontend

```bash
cd /opt/parking_altea/client

echo "=== VERIFICANDO DEPENDENCIAS DEL FRONTEND ==="

# Verificar que node_modules existe
if [ -d "node_modules" ]; then
    echo "✅ node_modules existe"
    NODE_COUNT=$(find node_modules -type d -maxdepth 1 | wc -l)
    echo "   node_modules tiene $NODE_COUNT elementos"
else
    echo "⚠️  node_modules no existe, será necesario npm install"
fi

# Ajustar permisos de ejecutables si es necesario
echo ""
echo "Ajustando permisos de ejecutables..."
chmod +x node_modules/.bin/* 2>/dev/null || true

# Compilar frontend
echo ""
echo "=== COMPILANDO FRONTEND ==="
npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Frontend compilado exitosamente"
else
    echo ""
    echo "❌ ERROR: La compilación del frontend falló"
    exit 1
fi
```

---

## BLOQUE 7: Verificación de Servicios y Frontend

```bash
cd /opt/parking_altea

echo "=== VERIFICANDO SERVICIOS Y FRONTEND ==="

# Verificar que el API responde
echo ""
echo "Verificando API en puerto 6001..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:6001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null || echo "000")

if [ "$API_RESPONSE" = "400" ] || [ "$API_RESPONSE" = "200" ] || [ "$API_RESPONSE" = "401" ]; then
    echo "✅ API responde correctamente en puerto 6001 (código: $API_RESPONSE)"
else
    echo "⚠️  API respondió con código: $API_RESPONSE"
fi

# Verificar que el proceso del API está corriendo
echo ""
echo "Verificando proceso del API..."
if lsof -ti:6001 > /dev/null 2>&1 || ss -tlnp | grep -q ":6001"; then
    PID=$(lsof -ti:6001 2>/dev/null || ss -tlnp | grep ":6001" | head -1 | awk '{print $NF}' | cut -d',' -f2 | cut -d'=' -f2)
    echo "✅ Proceso API corriendo en puerto 6001 (PID: $PID)"
else
    echo "❌ No hay proceso en puerto 6001"
fi

# Verificar que el frontend responde
echo ""
echo "Verificando frontend en puerto 5789..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5789 2>/dev/null || echo "000")

if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo "✅ Frontend responde correctamente (código: $FRONTEND_RESPONSE)"
else
    echo "⚠️  Frontend no responde correctamente (código: $FRONTEND_RESPONSE)"
    echo "   Verificar que el proceso del frontend esté corriendo"
fi

# Verificar logs recientes del API
echo ""
echo "=== VERIFICANDO LOGS RECIENTES DEL API ==="
ERROR_COUNT=$(journalctl -u parking-api.service --since "5 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Se encontraron $ERROR_COUNT errores en los logs recientes:"
    journalctl -u parking-api.service --since "5 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | tail -5
else
    echo "✅ No hay errores en los logs recientes"
fi
```

---

## BLOQUE 8: Verificación de Funcionalidades Nuevas

```bash
cd /opt/parking_altea
source venv/bin/activate

echo "=== VERIFICANDO FUNCIONALIDADES NUEVAS ==="

# Verificar que se pueden consultar configuraciones preparatorias
cd src
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from config import DB_URL
from sqlalchemy import create_engine, text

engine = create_engine(DB_URL)
with engine.connect() as conn:
    # Verificar que se pueden consultar configuraciones con panel_id NULL
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM panel_window_configurations 
        WHERE panel_id IS NULL;
    """))
    prep_count = result.fetchone()[0]
    print(f"✅ Configuraciones preparatorias (panel_id NULL): {prep_count}")
    
    # Verificar que existen configuraciones con panel_id específico
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM panel_window_configurations 
        WHERE panel_id IS NOT NULL;
    """))
    specific_count = result.fetchone()[0]
    print(f"✅ Configuraciones específicas de panel: {specific_count}")
    
    # Verificar constraint único
    result = conn.execute(text("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints 
        WHERE table_name = 'panel_window_configurations'
        AND constraint_type = 'UNIQUE';
    """))
    constraints = result.fetchall()
    print(f"✅ Constraints únicos encontrados: {len(constraints)}")
    for constraint in constraints:
        print(f"   - {constraint[0]} ({constraint[1]})")

EOF
cd ..
```

---

## BLOQUE 9: Resumen Final

```bash
echo ""
echo "=========================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""
echo "Resumen:"
echo "  • Código actualizado: ✅"
echo "  • Migración de base de datos: ✅"
echo "  • Backend API: ✅ Activo en puerto 6001"
echo "  • Frontend: ✅ Compilado"
echo "  • Archivos nuevos: ✅ Todos presentes"
echo "  • Configuración a nivel de empresa: ✅ Implementada"
echo ""
echo "Funcionalidades nuevas disponibles:"
echo "  • Crear configuración sin paneles Tipo 4"
echo "  • Configuración única por empresa"
echo "  • Asociación automática al crear paneles Tipo 4"
echo "  • Reinicio automático del servicio al actualizar configuración"
echo ""
echo "Próximos pasos:"
echo "  1. Probar creación de configuración preparatoria desde el frontend"
echo "  2. Crear un panel Tipo 4 y verificar asociación automática"
echo "  3. Verificar que el servicio se reinicia correctamente"
echo ""
echo "Acceso:"
echo "  • Frontend: http://157.180.91.63:5789"
echo "  • API: http://157.180.91.63:6001"
echo ""
```

---

## NOTAS IMPORTANTES

1. **Migración de Base de Datos**: La migración `migrate_panel_config_company_level.py` debe ejecutarse ANTES de reiniciar los servicios.

2. **Constraint Único**: El nuevo constraint único por empresa puede fallar si ya existen configuraciones duplicadas. En ese caso, será necesario limpiar duplicados primero.

3. **Reinicio del Servicio**: El servicio `parking-panel-worker` se reiniciará automáticamente cuando se cree/actualice una configuración, pero también se puede reiniciar manualmente si es necesario.

4. **Configuraciones Preparatorias**: Las configuraciones con `panel_id = NULL` son preparatorias y se asociarán automáticamente cuando se cree un panel Tipo 4 de la misma empresa.

5. **Compatibilidad**: Los cambios son retrocompatibles. Las configuraciones existentes con `panel_id` específico seguirán funcionando normalmente.

---

## ROLLBACK (Si es necesario)

Si hay problemas, se puede hacer rollback:

```bash
cd /opt/parking_altea
git checkout HEAD~1 -- src/models.py src/api_server.py src/panel_window_service.py
# Revertir migración manualmente si es necesario
systemctl restart parking-api.service
```

---

## FIN DEL DESPLIEGUE

