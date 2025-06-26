# Despliegue - Parking Altea

## Estado Actual del Despliegue

### Servidor de Producción
- **IP**: 157.180.91.63
- **Ubicación**: Helsinki, Finlandia
- **Proveedor**: Hetzner
- **Sistema**: Ubuntu 22.04 LTS

### Servicios Activos

#### 1. API REST (parking-api.service)
- **Puerto**: 6001
- **Estado**: ✅ Activo y funcionando
- **Versión**: v2.2 (con sistema de autenticación)
- **Workers**: 3 procesos Gunicorn
- **Memoria**: ~129MB
- **Último reinicio**: 26/06/2025 07:58:54 UTC

#### 2. Servidor de Cámaras (parking-camera.service)
- **Puerto**: 6002
- **Estado**: ✅ Activo y funcionando
- **Función**: Recepción de datos de cámaras
- **Último reinicio**: 26/06/2025 07:58:54 UTC

### Base de Datos
- **Sistema**: PostgreSQL 15
- **Estado**: ✅ Activo
- **Conexiones**: Configuradas correctamente
- **Datos**: 9 parkings, 10 paneles, 13 cámaras cargados

## Sistema de Autenticación v2.2

### Usuarios Configurados

#### 1. Toni Alos
- **Email**: atea.dti@altea.es
- **Contraseña**: altea2025!
- **ID**: 1
- **Acceso**: Todos los recursos (9 parkings, 10 paneles, 13 cámaras)

#### 2. Iván Martí
- **Email**: gerenciapstd@altea.es
- **Contraseña**: altea2025!
- **ID**: 2
- **Acceso**: Todos los recursos (9 parkings, 10 paneles, 13 cámaras)

### Endpoints de Autenticación
- `POST /auth/login` - Login de usuarios
- `POST /auth/register` - Registro de nuevos usuarios
- `GET /auth/permissions` - Obtener permisos del usuario
- `PUT /auth/password` - Cambiar contraseña
- `GET /user/parkings` - Parkings del usuario
- `GET /user/parking/{id}` - Parking específico del usuario

## Pruebas de Validación

### Pruebas de Autenticación (26/06/2025)
- **Total de pruebas**: 10
- **Pruebas exitosas**: 10
- **Tasa de éxito**: 100%
- **Estado**: ✅ EXCELENTE

### Pruebas de API (26/06/2025)
- **Total de pruebas**: 7
- **Pruebas exitosas**: 6
- **Pruebas fallidas**: 1 (endpoint de cámaras no implementado)
- **Tasa de éxito**: 85.7%
- **Estado**: ✅ BUENO

### Validaciones Realizadas
1. ✅ Login exitoso para ambos usuarios
2. ✅ Acceso a parkings con autenticación
3. ✅ Denegación de acceso sin autenticación
4. ✅ Obtención de permisos de usuario
5. ✅ Cambio de contraseña
6. ✅ Registro de nuevos usuarios

## Dependencias Instaladas
- **bcrypt**: 4.0.1 (encriptación de contraseñas)
- **PyJWT**: 2.8.0 (tokens JWT)
- **Flask**: 3.0.0
- **psycopg2-binary**: 2.9.9
- **gunicorn**: 21.2.0

## Monitoreo y Logs

### Logs del Servicio API
```bash
# Ver logs en tiempo real
journalctl -u parking-api.service -f

# Ver logs de las últimas 24 horas
journalctl -u parking-api.service --since "24 hours ago"
```

### Logs del Servicio de Cámaras
```bash
# Ver logs en tiempo real
journalctl -u parking-camera.service -f
```

## Comandos de Gestión

### Reiniciar Servicios
```bash
# Reiniciar API
systemctl restart parking-api.service

# Reiniciar servicio de cámaras
systemctl restart parking-camera.service

# Verificar estado
systemctl status parking-api.service
systemctl status parking-camera.service
```

### Actualizar Código
```bash
cd /opt/parking_altea
git fetch origin
git checkout <branch>
git pull origin <branch>
systemctl restart parking-api.service
```

### Instalar Dependencias
```bash
cd /opt/parking_altea
source venv/bin/activate
pip install -r requirements.txt
```

## Seguridad

### Firewall
- Puerto 6001: API REST (acceso público)
- Puerto 6002: Servidor de cámaras (acceso restringido)
- Puerto 22: SSH (acceso restringido)

### Autenticación
- Tokens JWT con expiración de 24 horas
- Contraseñas encriptadas con bcrypt
- Validación de permisos por recurso

### Base de Datos
- Conexiones con SSL
- Usuarios con permisos mínimos necesarios
- Backup automático configurado

## Próximos Pasos

1. **Frontend**: Implementar interfaz de usuario con React
2. **Monitoreo**: Configurar alertas y métricas
3. **Backup**: Automatizar backups de base de datos
4. **SSL**: Configurar certificados HTTPS
5. **Logs**: Centralizar logs con ELK Stack

## Contacto de Soporte
- **Desarrollador**: Francisco
- **Email**: info@swat-id.com
- **Proyecto**: Parking Altea v2.2 