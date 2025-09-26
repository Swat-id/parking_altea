# Resolución de Conflicto de Merge - Despliegue v4.2.0

## Situación
El archivo `client/src/services/panelService.js` tiene cambios locales en el servidor que conflictan con nuestros cambios.

## Comandos de Resolución

### 1. Ver qué cambios hay localmente
```bash
git status
git diff client/src/services/panelService.js
```

### 2. Respaldar cambios locales (por si acaso)
```bash
cp client/src/services/panelService.js client/src/services/panelService.js.backup
```

### 3. Opción A: Stash y aplicar nuestros cambios (RECOMENDADO)
```bash
# Guardar cambios locales temporalmente
git stash

# Hacer pull de nuestros cambios
git pull origin v4.1.0

# Ver si hay conflictos en el stash
git stash list

# Si queremos recuperar cambios locales después (opcional)
# git stash pop
```

### 4. Opción B: Forzar nuestros cambios (si los locales no son importantes)
```bash
# Descartar cambios locales
git checkout -- client/src/services/panelService.js

# Hacer pull
git pull origin v4.1.0
```

### 5. Verificar que el pull fue exitoso
```bash
git status
git log --oneline -3
```

### 6. Continuar con el despliegue
```bash
# Reiniciar servicio API
systemctl restart parking-api.service
systemctl status parking-api.service

# Verificar que funciona
curl -X GET http://localhost:6001/api/sensors
```
