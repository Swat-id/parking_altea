# Parking Altea - Sistema de Gestión de Aparcamientos

## Descripción

Sistema de gestión de aparcamientos inteligente para Altea que incluye:
- Gestión de ocupación en tiempo real
- Control de cámaras de acceso
- Gestión de paneles informativos
- Sistema de usuarios y autenticación
- API REST para integración

## Versión Actual: v2.1

### Nuevas Funcionalidades en v2.1
- ✅ Sistema de usuarios con autenticación JWT
- ✅ Gestión de permisos por usuario
- ✅ Hash seguro de contraseñas con bcrypt
- ✅ Tablas intermedias para relaciones usuario-parking-panel
- ✅ API protegida con tokens de autenticación

## Estructura del Proyecto

```
parking_altea/
├── src/
│   ├── api_server.py          # Servidor API REST
│   ├── camera_server.py       # Servidor de cámaras
│   ├── panel_client.py        # Cliente de paneles
│   ├── models.py              # Modelos de base de datos
│   ├── auth.py                # Autenticación y autorización
│   ├── config.py              # Configuración
│   ├── load_data.py           # Carga de datos iniciales
│   └── create_initial_users.py # Script usuarios iniciales
├── csv_templates/             # Plantillas CSV para datos
├── docs/                      # Documentación
│   └── v2.1_changelog.md      # Cambios de la versión v2.1
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## Instalación

### Prerrequisitos
- Python 3.8+
- PostgreSQL
- pip

### Configuración

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd parking_altea
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos**
```bash
# Crear archivo .env con la configuración de la base de datos
echo "DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/parking_db" > .env
```

4. **Crear usuarios iniciales**
```bash
python src/create_initial_users.py
```

## Uso

### Iniciar el servidor API
```bash
python src/api_server.py
```

### Iniciar el servidor de cámaras
```bash
python src/camera_server.py
```

### Iniciar el cliente de paneles
```bash
python src/panel_client.py
```

## API REST

### Autenticación

#### Registro de Usuario
```bash
POST /auth/register
Content-Type: application/json

{
  "name": "Nombre Usuario",
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

### Endpoints Protegidos

Todas las rutas requieren el header de autorización:
```
Authorization: Bearer <token_jwt>
```

#### Gestión de Parkings
- `GET /parkings` - Listar parkings del usuario
- `GET /parking/{id}` - Obtener información de un parking
- `POST /parking/{id}/occupancy` - Establecer ocupación
- `POST /parking/{id}/message` - Programar mensaje

#### Gestión de Usuarios
- `GET /auth/profile` - Obtener perfil del usuario
- `DELETE /auth/users/{id}` - Eliminar usuario
- `GET /auth/users/{id}/parkings` - Parkings del usuario
- `GET /auth/users/{id}/panels` - Paneles del usuario

## Usuarios Iniciales

| Nombre | Email | Contraseña |
|--------|-------|------------|
| Toni Alos | atea.dti@altea.es | altea2025! |
| Iván Martí | gerenciapstd@altea.es | altea2025! |

## Configuración

### Variables de Entorno (.env)
```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/parking_db
CAMERA_PORT=6400
API_PORT=6001
LOG_RETENTION_DAYS=15
```

### Base de Datos
- **Motor**: PostgreSQL
- **Nomenclatura**: snake_case
- **Usuario por defecto**: superadmin (info@swat-id.com / admin123!)

## Desarrollo

### Estructura de Base de Datos
- `users` - Usuarios del sistema
- `user_parkings` - Relación usuarios-parkings
- `user_panels` - Relación usuarios-paneles
- `parkings` - Aparcamientos
- `accesses` - Accesos/cámaras
- `panels` - Paneles informativos
- `occupancy_history` - Historial de ocupación
- `scheduled_messages` - Mensajes programados

### Tecnologías
- **Backend**: Python/Flask
- **Base de Datos**: PostgreSQL
- **Autenticación**: JWT + bcrypt
- **ORM**: SQLAlchemy

## Documentación

- [Changelog v2.1](docs/v2.1_changelog.md) - Detalles de la versión actual
- [API Documentation](docs/api.md) - Documentación completa de la API

## Contribución

1. Crear una rama para la nueva funcionalidad
2. Desarrollar siguiendo las reglas del proyecto
3. Documentar cambios en `/docs`
4. Crear pull request

## Licencia

Proyecto desarrollado para el Ayuntamiento de Altea.
