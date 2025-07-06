# Análisis Detallado - Sprint 2: Autenticación, Roles y Gestión de Usuarios

## 1. Estado Actual del Backend

### 1.1. Autenticación y Registro de Usuarios
- El backend utiliza Flask y SQLAlchemy.
- El registro de usuario se realiza vía `/auth/register` y la autenticación vía `/auth/login`.
- El registro llama a `create_user(session, name, email, password)` en `auth.py`.
- La autenticación llama a `authenticate_user(session, email, password)` en `auth.py`.
- El token JWT generado **NO incluye el rol** del usuario actualmente, solo: `user_id`, `email`, `name`, `exp`.
- El modelo `User` ya tiene el campo `role` (`superadmin` o `user`).

### 1.2. Gestión de Roles
- El rol no se asigna explícitamente al crear usuario (por defecto es 'user' en el modelo).
- No hay lógica para crear usuarios con rol `superadmin` desde la API.
- No se utiliza el rol en la autenticación ni en los endpoints.
- No se incluye el rol en el JWT ni en la respuesta de login.

### 1.3. Permisos y Decoradores
- Solo existe el decorador `@require_auth` para proteger endpoints.
- No existen decoradores para roles (`superadmin`) ni para permisos granulares (acceso a parkings, etc).
- `require_auth` solo verifica el token y añade `request.user_data`.
- En modo desarrollo, si no hay token, asigna el usuario `info@swat-id.com` como superadmin por defecto.

### 1.4. Endpoints de Gestión de Usuarios
- No existen endpoints `/admin/users` ni similares para gestión avanzada de usuarios.
- Los endpoints actuales de usuario son:
  - `/auth/register` (POST): crear usuario
  - `/auth/login` (POST): login
  - `/auth/user` (DELETE): eliminar usuario autenticado
  - `/auth/password` (PUT): cambiar contraseña
  - `/auth/permissions` (GET): obtener recursos asignados
  - `/auth/assign` (POST): asignar recursos a usuario
- No hay endpoints para listar todos los usuarios, crear usuario con rol, asignar parkings de forma granular, ni eliminar usuarios por id.

### 1.5. Gestión de Recursos
- Los recursos (parkings, paneles, accesos) se asignan vía `/auth/assign` pero no hay control de permisos por rol.
- No hay validación de que solo un superadmin pueda asignar recursos o crear usuarios.

## 2. Implicaciones para Sprint 2

### 2.1. Cambios Necesarios para T2.1
- Modificar `create_user` para aceptar y validar el campo `role`.
- Modificar `authenticate_user` para incluir el `role` en el JWT y en la respuesta.
- Añadir función `get_user_resources` para obtener recursos por usuario (ya existe parcialmente como `get_user_permissions`).

### 2.2. Cambios Necesarios para T2.2
- Implementar decorador `require_superadmin` para proteger endpoints solo para superadmins.
- Implementar decorador `require_parking_access` para validar acceso a recursos.
- Añadir validación de permisos granular en endpoints sensibles.

### 2.3. Cambios Necesarios para T2.3
- Crear endpoints:
  - `GET /admin/users` - Listar todos los usuarios (solo superadmin)
  - `POST /admin/users` - Crear usuario (solo superadmin, con rol)
  - `POST /admin/users/{id}/assign` - Asignar parkings a usuario (solo superadmin)
  - `DELETE /admin/users/{id}` - Eliminar usuario (solo superadmin)
- Añadir validación de permisos en estos endpoints.

## 3. Resumen de Gaps Detectados
- El sistema actual no usa el campo `role` para controlar acceso ni en el JWT.
- No existen endpoints de administración de usuarios.
- No hay decoradores de permisos por rol.
- No hay validación de permisos en la asignación de recursos.

## 4. Recomendaciones para la Implementación
- Añadir y validar el campo `role` en la creación y autenticación de usuario.
- Incluir el rol en el JWT y en la respuesta de login.
- Implementar decoradores de permisos para superadmin y recursos.
- Crear endpoints RESTful para gestión de usuarios y asignación de parkings.
- Documentar todos los cambios y actualizar los tests.

---

**Este análisis servirá de base para la implementación de las tareas T2.1, T2.2 y T2.3.** 