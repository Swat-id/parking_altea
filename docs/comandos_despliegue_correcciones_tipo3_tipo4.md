# Comandos de Despliegue - Correcciones Paneles Tipo 3 y Tipo 4

## Fecha: 2025-11-12
## Servidor: root@ubuntu-16gb-hel1-1
## Ruta: /opt/parking_altea
## Rama: v4.3.0

## Cambios a desplegar:
1. `src/panel_type4_update_service.py` - Tipo 3 sin texto previo (solo valores numéricos)
2. `src/panel_content_rotation_service.py` - Incluir `status_config` en contenido retornado
3. Documentación de análisis

---

## BLOQUE 1: Preparación y Backup

```bash
# Conectar al servidor
ssh root@ubuntu-16gb-hel1-1

# Ir al directorio del proyecto
cd /opt/parking_altea

# Verificar rama actual
git branch

# Verificar estado
git status

# Crear backup de los archivos modificados
cp src/panel_type4_update_service.py src/panel_type4_update_service.py.backup
cp src/panel_content_rotation_service.py src/panel_content_rotation_service.py.backup
```

---

## BLOQUE 2: Actualizar Código desde Git

```bash
# Descartar cambios locales si existen
cd /opt/parking_altea
git fetch origin
git reset --hard origin/v4.3.0

# Verificar que los cambios están presentes
git log --oneline -5
git diff HEAD~1 src/panel_type4_update_service.py | grep -A 5 "texto_fijo_previo"
git diff HEAD~1 src/panel_content_rotation_service.py | grep -A 5 "status_config"
```

---

## BLOQUE 3: Verificar Archivos Modificados

```bash
# Verificar que los archivos tienen los cambios correctos
cd /opt/parking_altea

# Verificar panel_type4_update_service.py (Tipo 3 sin texto previo)
grep -A 3 "Para Tipo 3, NO usar texto_fijo_previo" src/panel_type4_update_service.py

# Verificar panel_content_rotation_service.py (status_config)
grep -A 3 "Incluir status_config" src/panel_content_rotation_service.py
```

---

## BLOQUE 4: Reiniciar Servicios (si es necesario)

```bash
# Verificar servicios relacionados con paneles
systemctl list-units | grep -E "(panel|parking)"

# Si existe un worker específico para Tipo 3/4, reiniciarlo
# (Ajustar nombre del servicio según corresponda)
# systemctl restart parking-panel-worker-type3-4.service

# Verificar logs del worker principal (si aplica)
# journalctl -u parking-panel-worker.service -f --no-pager | tail -20
```

---

## BLOQUE 5: Verificación Post-Despliegue

```bash
# Verificar que los servicios están corriendo
systemctl status parking-api.service --no-pager | head -20

# Verificar logs recientes
tail -50 logs/panel_worker.log 2>/dev/null || echo "Log no encontrado"

# Verificar que no hay errores de sintaxis
cd /opt/parking_altea/src
python3 -m py_compile panel_type4_update_service.py
python3 -m py_compile panel_content_rotation_service.py
echo "✅ Verificación de sintaxis completada"
```

---

## BLOQUE 6: Pruebas Rápidas (Opcional)

```bash
# Si hay paneles Tipo 3 configurados, verificar que funcionan
# (Esto requiere acceso a la API o base de datos)

# Verificar que el servicio de rotación funciona
cd /opt/parking_altea/src
python3 -c "
from panel_content_rotation_service import PanelContentRotationService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()
service = PanelContentRotationService(session)
print('✅ PanelContentRotationService se importa correctamente')
session.close()
"

# Verificar que el servicio de actualización funciona
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

## Notas Importantes:

1. **No hay cambios en base de datos**: Solo cambios en código Python
2. **No hay migraciones**: No es necesario ejecutar scripts de migración
3. **Worker original**: NO se modifica, sigue funcionando para Tipo 1, 2 y 3
4. **Servicios afectados**: 
   - `PanelType3And4UpdateService` (para actualizaciones manuales de Tipo 3/4)
   - `PanelContentRotationService` (para rotación de contenido Tipo 4)
5. **Reinicio de servicios**: Solo necesario si hay un worker específico para Tipo 3/4

---

## Rollback (si es necesario)

```bash
# Restaurar archivos desde backup
cd /opt/parking_altea
cp src/panel_type4_update_service.py.backup src/panel_type4_update_service.py
cp src/panel_content_rotation_service.py.backup src/panel_content_rotation_service.py

# O volver al commit anterior
git reset --hard HEAD~1
```

