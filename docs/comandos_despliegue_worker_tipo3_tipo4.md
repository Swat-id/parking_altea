# Comandos de Despliegue - Worker Tipo 3 y Tipo 4

## Fecha: 2025-11-12
## Servidor: root@ubuntu-16gb-hel1-1
## Ruta: /opt/parking_altea
## Rama: v4.3.0

## Cambios a desplegar:
1. `src/panel_type3_and_4_worker.py` - Worker independiente para Tipo 3 y Tipo 4
2. `src/panel_type3_and_4_worker_service.py` - Servicio wrapper
3. `deploy/parking-panel-type3-and-4-worker.service` - Archivo systemd

---

## BLOQUE 1: Preparación y Actualización de Código

```bash
# Conectar al servidor
ssh root@ubuntu-16gb-hel1-1

# Ir al directorio del proyecto
cd /opt/parking_altea

# Verificar rama actual
git branch

# Verificar estado
git status

# Descartar cambios locales si existen
git fetch origin
git reset --hard origin/v4.3.0

# Verificar que los cambios están presentes
git log --oneline -3
ls -la src/panel_type3_and_4_worker.py
ls -la src/panel_type3_and_4_worker_service.py
ls -la deploy/parking-panel-type3-and-4-worker.service
```

---

## BLOQUE 2: Verificar Archivos y Sintaxis

```bash
cd /opt/parking_altea

# Activar entorno virtual
source venv/bin/activate

# Verificar sintaxis de los nuevos archivos
cd src
python3 -m py_compile panel_type3_and_4_worker.py && echo "✅ panel_type3_and_4_worker.py: OK" || echo "❌ panel_type3_and_4_worker.py: ERROR"
python3 -m py_compile panel_type3_and_4_worker_service.py && echo "✅ panel_type3_and_4_worker_service.py: OK" || echo "❌ panel_type3_and_4_worker_service.py: ERROR"

# Verificar que puede importar el servicio
python3 -c "
from panel_type4_update_service import PanelType3And4UpdateService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()
service = PanelType3And4UpdateService(session)
print('✅ PanelType3And4UpdateService se importa correctamente')
session.close()
"
```

---

## BLOQUE 3: Crear Directorio de Logs (si no existe)

```bash
cd /opt/parking_altea

# Crear directorio de logs si no existe
mkdir -p logs

# Verificar permisos
ls -ld logs
```

---

## BLOQUE 4: Copiar y Configurar Servicio Systemd

```bash
cd /opt/parking_altea

# Copiar archivo de servicio systemd
cp deploy/parking-panel-type3-and-4-worker.service /etc/systemd/system/

# Verificar que se copió correctamente
ls -la /etc/systemd/system/parking-panel-type3-and-4-worker.service

# Recargar systemd para reconocer el nuevo servicio
systemctl daemon-reload

# Verificar que systemd reconoce el servicio
systemctl list-unit-files | grep parking-panel-type3-and-4-worker
```

---

## BLOQUE 5: Habilitar e Iniciar el Servicio

```bash
# Habilitar el servicio para que se inicie automáticamente
systemctl enable parking-panel-type3-and-4-worker.service

# Iniciar el servicio
systemctl start parking-panel-type3-and-4-worker.service

# Verificar estado del servicio
systemctl status parking-panel-type3-and-4-worker.service --no-pager
```

---

## BLOQUE 6: Verificar que el Servicio Está Funcionando

```bash
# Verificar que el proceso está corriendo
ps aux | grep panel_type3_and_4_worker_service | grep -v grep

# Ver logs en tiempo real (presionar Ctrl+C para salir)
journalctl -u parking-panel-type3-and-4-worker.service -f --no-pager
```

---

## BLOQUE 7: Verificar Logs y Estadísticas

```bash
# Ver últimas 50 líneas de logs
journalctl -u parking-panel-type3-and-4-worker.service -n 50 --no-pager

# Ver logs de errores
journalctl -u parking-panel-type3-and-4-worker.service -p err --no-pager

# Verificar que el archivo de log se está creando
ls -lh /opt/parking_altea/logs/panel_type3_and_4_worker.log 2>/dev/null && echo "✅ Archivo de log existe" || echo "⚠️ Archivo de log aún no existe (se creará en el primer ciclo)"
```

---

## BLOQUE 8: Verificar que Detecta Paneles Tipo 3 y Tipo 4

```bash
cd /opt/parking_altea/src

# Verificar que hay paneles Tipo 3 y Tipo 4 en la base de datos
python3 -c "
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text
from config import DB_URL
engine = create_engine(DB_URL)
conn = engine.connect()
result = conn.execute(text('''
    SELECT p.id, p.name, pt.id as type_id, pt.windows_count
    FROM panels p
    JOIN panel_types pt ON p.panel_type_id = pt.id
    WHERE p.is_active = true AND pt.windows_count IN (2, 16)
    ORDER BY pt.windows_count, p.id
'''))
panels = result.fetchall()
print(f'Paneles Tipo 3 y Tipo 4 encontrados: {len(panels)}')
for panel in panels:
    print(f'  - Panel {panel[0]} ({panel[1]}): Tipo {panel[2]} ({panel[3]} ventanas)')
conn.close()
"
```

---

## BLOQUE 9: Verificar Configuraciones de Usuarios

```bash
cd /opt/parking_altea/src

# Verificar que hay configuraciones de usuarios
python3 -c "
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text
from config import DB_URL
engine = create_engine(DB_URL)
conn = engine.connect()
result = conn.execute(text('''
    SELECT user_id, panel_update_interval_seconds, is_active
    FROM user_panel_configs
    WHERE is_active = true
    ORDER BY user_id
'''))
configs = result.fetchall()
print(f'Configuraciones de usuarios encontradas: {len(configs)}')
for config in configs:
    print(f'  - Usuario {config[0]}: Intervalo {config[1]}s')
if len(configs) == 0:
    print('  ⚠️ No hay configuraciones. Se usará intervalo por defecto (120s)')
conn.close()
"
```

---

## BLOQUE 10: Monitoreo Continuo (Opcional)

```bash
# Ver logs en tiempo real con filtros
journalctl -u parking-panel-type3-and-4-worker.service -f --no-pager | grep -E "(INFO|ERROR|actualizado|falló)"

# Ver solo actualizaciones exitosas
journalctl -u parking-panel-type3-and-4-worker.service -f --no-pager | grep "actualizado"

# Ver solo errores
journalctl -u parking-panel-type3-and-4-worker.service -f --no-pager | grep -i error
```

---

## BLOQUE 11: Comandos de Gestión del Servicio

```bash
# Detener el servicio
systemctl stop parking-panel-type3-and-4-worker.service

# Reiniciar el servicio
systemctl restart parking-panel-type3-and-4-worker.service

# Ver estado detallado
systemctl status parking-panel-type3-and-4-worker.service

# Deshabilitar inicio automático (si es necesario)
systemctl disable parking-panel-type3-and-4-worker.service
```

---

## BLOQUE 12: Verificación Final

```bash
# Verificar que ambos workers están corriendo
echo "=== WORKER ORIGINAL ==="
systemctl status parking-panel-worker.service --no-pager | head -10

echo ""
echo "=== WORKER TIPO 3/4 ==="
systemctl status parking-panel-type3-and-4-worker.service --no-pager | head -10

# Verificar procesos
ps aux | grep -E "(panel_worker_service|panel_type3_and_4_worker_service)" | grep -v grep

# Ver estadísticas del worker Tipo 3/4 (si el servicio tiene modo stats)
cd /opt/parking_altea
source venv/bin/activate
python src/panel_type3_and_4_worker_service.py --stats 2>/dev/null || echo "Modo stats no disponible o servicio en ejecución"
```

---

## Notas Importantes:

1. **Worker Independiente**: Este worker NO modifica el worker original (`parking-panel-worker.service`)
2. **Intervalos**: El worker respeta los intervalos configurados en `UserPanelConfig` por usuario
3. **Logs Separados**: Los logs están en `logs/panel_type3_and_4_worker.log` y también en journald
4. **Solo Tipo 3 y 4**: Este worker solo actualiza paneles Tipo 3 (2 ventanas) y Tipo 4 (16 ventanas)
5. **Worker Original**: Sigue funcionando para Tipo 1, 2 y 3 con el método tradicional

---

## Rollback (si es necesario)

```bash
# Detener el servicio
systemctl stop parking-panel-type3-and-4-worker.service

# Deshabilitar inicio automático
systemctl disable parking-panel-type3-and-4-worker.service

# Eliminar archivo de servicio
rm /etc/systemd/system/parking-panel-type3-and-4-worker.service

# Recargar systemd
systemctl daemon-reload

# Volver a versión anterior del código (si es necesario)
cd /opt/parking_altea
git reset --hard HEAD~1
```

