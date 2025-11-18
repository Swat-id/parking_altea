# Comandos de Despliegue: Corrección de Sensores Ocultos v4.3.0

## Problema Resuelto

**Problema**: Los sensores con `serial_number` que no están en parkings accesibles al usuario no aparecían en el listado, pero impedían crear nuevos sensores con ese mismo `serial_number` porque la validación de duplicados los encontraba.

**Ejemplo**: 
- Sensor `FD010E56` existe pero está en un parking no accesible o tiene `parking_id=None`
- No aparece en el listado de sensores
- Al intentar crear un sensor con `FD010E56`, el sistema dice que ya existe
- No se puede editar el sensor `FD010E65` para cambiarlo a `FD010E56`

## Solución Implementada

1. **Validación inteligente de duplicados**: 
   - Al crear/editar un sensor, si existe uno con el mismo `serial_number` pero no está accesible, se desactiva automáticamente
   - Permite reutilizar `serial_numbers` de sensores "ocultos"

2. **Búsqueda por serial_number**: 
   - Nuevo parámetro `search_serial` en el listado para buscar sensores por `serial_number` sin filtros de parking
   - Nuevo endpoint `/api/sensors/by-serial/<serial_number>` para encontrar sensores específicos

3. **Edición mejorada**: 
   - Al editar un sensor y cambiar su `serial_number`, si existe otro con ese serial pero no accesible, se desactiva automáticamente

## Comandos de Despliegue

### 1. Conectar al servidor de producción

```bash
ssh root@157.180.91.63
```

### 2. Navegar al directorio del proyecto

```bash
cd /opt/parking_altea
```

### 3. Activar el entorno virtual

```bash
source venv/bin/activate
```

### 4. Actualizar código desde la rama v4.3.0

```bash
git fetch origin
git checkout v4.3.0
git pull origin v4.3.0
```

### 5. Verificar que el archivo se actualizó

```bash
grep -n "Reutilizando serial_number" src/api_server.py
```

### 6. Reiniciar el servicio API

```bash
systemctl restart parking-api
```

### 7. Verificar que el servicio está activo

```bash
systemctl status parking-api --no-pager
```

### 8. Ver logs para verificar que no hay errores

```bash
journalctl -u parking-api -n 50 --no-pager
```

## Uso de las Nuevas Funcionalidades

### Buscar un sensor por serial_number

**Endpoint nuevo**: `GET /api/sensors/by-serial/<serial_number>`

```bash
# Ejemplo: Buscar el sensor FD010E56
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/sensors/by-serial/FD010E56
```

### Buscar sensores en el listado por serial_number

**Parámetro nuevo**: `search_serial`

```bash
# Ejemplo: Buscar todos los sensores que contengan "FD010E5"
curl -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/sensors?search_serial=FD010E5"
```

### Editar sensor FD010E65 para cambiar a FD010E56

1. **Primero, buscar el sensor FD010E65**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/sensors?search_serial=FD010E65"
```

2. **Obtener el ID del sensor** (por ejemplo, ID: 123)

3. **Editar el sensor cambiando el serial_number**:
```bash
curl -X PUT \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "FD010E56",
    "name": "Nuevo nombre",
    "sensor_type": "PMR",
    "parking_id": 1
  }' \
  http://localhost:5000/api/sensors/123
```

**Nota**: Si existe un sensor con `FD010E56` que no está accesible, se desactivará automáticamente y se permitirá el cambio.

### Crear un sensor con serial_number que "existe pero no aparece"

Si intentas crear un sensor con `FD010E56` y el sistema dice que ya existe:

1. **El sistema automáticamente desactivará el sensor anterior** si no está accesible
2. **Se creará el nuevo sensor** con ese `serial_number`
3. **El sensor anterior quedará con `is_active=False`**

## Verificación Post-Despliegue

### Verificar que el endpoint nuevo funciona

```bash
# Buscar sensor por serial
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/sensors/by-serial/FD010E56
```

### Verificar que se pueden crear sensores con serials "ocultos"

```bash
# Intentar crear sensor (debería funcionar ahora)
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "FD010E56",
    "name": "Sensor Test",
    "sensor_type": "PMR",
    "parking_id": 1
  }' \
  http://localhost:5000/api/sensors
```

### Verificar en la base de datos

```bash
# Ver todos los sensores con serial que empieza con FD010E5
sudo -u postgres psql parking_db -c "
SELECT id, serial_number, name, is_active, parking_id 
FROM individual_sensors 
WHERE serial_number LIKE 'FD010E5%' 
ORDER BY serial_number;
"
```

## Solución al Problema Específico

### Para el caso de FD010E56 y FD010E65:

1. **Buscar el sensor FD010E65**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/sensors?search_serial=FD010E65"
```

2. **Obtener su ID** (por ejemplo, ID: 456)

3. **Editar el sensor FD010E65 para cambiar su serial_number a FD010E56**:
```bash
curl -X PUT \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "FD010E56"
  }' \
  http://localhost:5000/api/sensors/456
```

4. **Si el sensor FD010E56 existía pero no estaba accesible, se desactivará automáticamente**

5. **El sensor FD010E65 ahora tendrá el serial_number FD010E56**

## Notas Importantes

- **Superadmin**: Los superadmins no pueden reutilizar serial_numbers porque tienen acceso a todos los sensores. Si un superadmin intenta crear un sensor con un serial que ya existe, se rechazará.

- **Usuarios regulares**: Pueden reutilizar serial_numbers de sensores que no están en sus parkings accesibles.

- **Desactivación automática**: Cuando se reutiliza un serial_number, el sensor anterior se desactiva automáticamente (`is_active=False`), pero no se elimina de la base de datos.

- **Búsqueda**: El parámetro `search_serial` permite encontrar sensores incluso si no están en parkings accesibles, lo cual es útil para diagnosticar problemas.

