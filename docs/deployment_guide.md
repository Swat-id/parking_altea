# Guía de Despliegue - Parking Altea v2.1

## Descripción

Esta guía describe el proceso completo de despliegue de la versión v2.1 del sistema Parking Altea, incluyendo la actualización de la base de datos y la verificación de funcionalidades.

## Prerrequisitos

### En el servidor de desarrollo
- Git configurado con acceso al repositorio
- SSH configurado para acceso al servidor remoto
- Rama `v2.1` actualizada

### En el servidor de producción
- Python 3.8+
- PostgreSQL
- Acceso SSH configurado
- Usuario con permisos sudo para servicios

## Scripts de Despliegue

### 1. Script de Verificación (`verify_user_access.py`)

**Propósito**: Verificar que los usuarios Toni Alos e Iván Martí tienen acceso completo a todos los recursos.

**Uso**:
```bash
cd src
python verify_user_access.py
```

**Funcionalidades**:
- ✅ Verifica que ambos usuarios existen
- ✅ Cuenta todos los parkings, paneles y cámaras
- ✅ Asigna automáticamente recursos faltantes
- ✅ Genera reporte detallado de asignaciones
- ✅ Confirma acceso completo a todos los recursos

**Salida esperada**:
```
🔍 Verificando acceso de usuarios a recursos...
============================================================
✅ Toni Alos encontrado (ID: 1)
✅ Iván Martí encontrado (ID: 2)

📊 Total de parkings en el sistema: 3
📊 Total de paneles en el sistema: 2
📊 Total de cámaras/accesos en el sistema: 4

📋 RESUMEN DE VERIFICACIÓN:
========================================
Toni Alos - Parkings: ✅ (3/3)
Toni Alos - Paneles:  ✅ (2/2)
Iván Martí - Parkings: ✅ (3/3)
Iván Martí - Paneles:  ✅ (2/2)

🎉 ¡VERIFICACIÓN EXITOSA! Ambos usuarios tienen acceso completo a todos los recursos.
```

### 2. Script de Actualización de Base de Datos (`update_database.py`)

**Propósito**: Actualización completa de la base de datos con todas las nuevas tablas y datos.

**Uso**:
```bash
cd src
python update_database.py
```

**Funcionalidades**:
- 📋 Crea todas las tablas necesarias
- 🔍 Verifica conexión a PostgreSQL
- 👥 Crea usuarios iniciales (si no existen)
- 📊 Carga datos desde archivos CSV
- 🔗 Asigna todos los recursos a usuarios
- 💾 Guarda todos los cambios
- 📋 Genera resumen final

**Pasos del script**:
1. **Crear tablas**: Todas las tablas del modelo SQLAlchemy
2. **Verificar conexión**: Confirma acceso a PostgreSQL
3. **Crear usuarios**: Toni Alos e Iván Martí con contraseñas hash
4. **Cargar CSV**: Parkings, accesos y paneles desde archivos CSV
5. **Asignar recursos**: Todos los parkings y paneles a ambos usuarios
6. **Commit**: Guarda todos los cambios en la base de datos
7. **Resumen**: Muestra estadísticas finales

### 3. Script de Despliegue Automático (`deploy.sh`)

**Propósito**: Despliegue automatizado en el servidor de producción.

**Uso**:
```bash
# Configurar variables en deploy.sh
./deploy.sh
```

**Configuración previa**:
```bash
# Editar deploy.sh y configurar:
REMOTE_HOST="tu-servidor.com"
REMOTE_USER="usuario-servidor"
REMOTE_PATH="/ruta/al/proyecto"
```

**Funcionalidades**:
- 🔍 Verifica rama y cambios pendientes
- 📥 Actualiza código en servidor remoto
- 📦 Instala dependencias actualizadas
- 🗄️ Ejecuta actualización de base de datos
- 🔍 Ejecuta verificación de acceso de usuarios
- 🔄 Reinicia servicios del sistema
- 📋 Proporciona guía de próximos pasos

## Proceso de Despliegue Completo

### Paso 1: Preparación Local
```bash
# Verificar que estamos en la rama correcta
git checkout v2.1

# Verificar que no hay cambios pendientes
git status

# Asegurar que la rama está actualizada
git pull origin v2.1
```

### Paso 2: Configurar Script de Despliegue
```bash
# Editar deploy.sh con la configuración del servidor
nano deploy.sh

# Hacer el script ejecutable
chmod +x deploy.sh
```

### Paso 3: Ejecutar Despliegue
```bash
# Ejecutar el script de despliegue
./deploy.sh
```

### Paso 4: Verificación Post-Despliegue

#### 4.1 Verificar API
```bash
# Probar que la API responde
curl -X GET http://servidor:6001/auth/profile \
  -H "Authorization: Bearer <token>"
```

#### 4.2 Probar Autenticación
```bash
# Login con Toni Alos
curl -X POST http://servidor:6001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "atea.dti@altea.es",
    "password": "altea2025!"
  }'

# Login con Iván Martí
curl -X POST http://servidor:6001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "gerenciapstd@altea.es",
    "password": "altea2025!"
  }'
```

#### 4.3 Verificar Acceso a Recursos
```bash
# Listar parkings (requiere token)
curl -X GET http://servidor:6001/parkings \
  -H "Authorization: Bearer <token>"

# Obtener parkings específicos del usuario
curl -X GET http://servidor:6001/auth/users/1/parkings \
  -H "Authorization: Bearer <token>"
```

## Estructura de Archivos CSV

### parkings.csv
```csv
name,location,max_capacity,threshold_dense,threshold_full,current_occupancy,status
"Parking Centro","Plaza Mayor",50,35,45,0,"LIBRE"
"Parking Playa","Paseo Marítimo",100,70,90,0,"LIBRE"
```

### accesses.csv
```csv
parking_name,ip,line,name,last_vehicle_in,last_vehicle_out
"Parking Centro","192.168.1.10",1,"Entrada Principal",0,0
"Parking Centro","192.168.1.11",2,"Salida Principal",0,0
```

### panels.csv
```csv
parking_name,name,ip
"Parking Centro","Panel Entrada","192.168.1.20"
"Parking Playa","Panel Principal","192.168.1.21"
```

## Troubleshooting

### Error: "Usuario no encontrado"
- Verificar que el script `create_initial_users.py` se ejecutó correctamente
- Comprobar que los emails están escritos exactamente: `atea.dti@altea.es` y `gerenciapstd@altea.es`

### Error: "No autorizado para acceder a este parking"
- Ejecutar `verify_user_access.py` para asignar recursos faltantes
- Verificar que las tablas intermedias `user_parkings` y `user_panels` tienen datos

### Error: "Token inválido o expirado"
- Los tokens JWT expiran en 24 horas
- Hacer login nuevamente para obtener un token fresco

### Error de conexión a base de datos
- Verificar variables de entorno en `.env`
- Comprobar que PostgreSQL está ejecutándose
- Verificar credenciales de base de datos

## Logs y Monitoreo

### Logs del API Server
```bash
# Ver logs en tiempo real
tail -f /var/log/parking-api.log

# Ver logs de errores
grep ERROR /var/log/parking-api.log
```

### Logs de Base de Datos
```bash
# Conectar a PostgreSQL
psql -U parking_user -d parking_db

# Verificar tablas
\dt

# Verificar usuarios
SELECT * FROM users;

# Verificar asignaciones
SELECT u.name, p.name FROM users u 
JOIN user_parkings up ON u.id = up.user_id 
JOIN parkings p ON up.parking_id = p.id;
```

## Rollback

En caso de problemas, se puede hacer rollback:

```bash
# En el servidor
cd /opt/parking_altea
git reset --hard HEAD~1
pip install -r requirements.txt
sudo systemctl restart parking-api
```

## Contacto

Para soporte técnico durante el despliegue:
- **Desarrollador**: Equipo SWAT-ID
- **Email**: info@swat-id.com
- **Documentación**: `/docs/` en el repositorio 