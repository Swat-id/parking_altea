# Estado del Proyecto - Parking Altea

## Información General

- **Proyecto:** Sistema de Gestión de Parking Altea
- **Versión:** 1.1
- **Fecha de Actualización:** 26 de Junio de 2025
- **Estado:** En Producción
- **Servidor:** 157.180.91.63:6001 (API), 157.180.91.63:6400 (Cámaras)

## Arquitectura del Sistema

### Backend (Python Flask)
- **Lenguaje:** Python 3.x
- **Framework:** Flask
- **Base de Datos:** PostgreSQL
- **ORM:** SQLAlchemy
- **Servidor:** Gunicorn

### Frontend (React Vite)
- **Framework:** React con Vite
- **Estado:** Pendiente de desarrollo

### Base de Datos
- **Sistema:** PostgreSQL
- **Nomenclatura:** snake_case
- **Usuario por defecto:** superadmin (info@swat-id.com / admin123!)

## Estructura de Archivos

### Directorio Raíz
```
parking_altea/
├── csv_templates/          # Plantillas CSV para carga inicial
├── deploy/                 # Scripts de despliegue
├── docs/                   # Documentación del proyecto
├── src/                    # Código fuente del backend
├── README.md              # Documentación principal
└── requirements.txt       # Dependencias Python
```

### Archivos Principales

#### `/src/`
| Archivo | Funcionalidad | Estado |
|---------|---------------|--------|
| `api_server.py` | Servidor API REST principal | ✅ Funcionando |
| `camera_server.py` | Servidor para recepción de datos de cámaras | ✅ Funcionando |
| `models.py` | Modelos de base de datos SQLAlchemy | ✅ Funcionando |
| `config.py` | Configuración del sistema | ✅ Funcionando |
| `init_db.py` | Inicialización de base de datos | ✅ Funcionando |
| `load_data.py` | Carga de datos iniciales desde CSV | ✅ Funcionando |
| `panel_client.py` | Cliente para comunicación con paneles | ✅ Funcionando |
| `analyze_discrepancies.py` | Análisis de descuadres de ocupación | ✅ Funcionando |

#### `/deploy/`
| Archivo | Funcionalidad | Estado |
|---------|---------------|--------|
| `parking-api.service` | Servicio systemd para API | ✅ Desplegado |
| `parking-camera.service` | Servicio systemd para cámaras | ✅ Desplegado |
| `setup.sh` | Script de instalación inicial | ✅ Funcionando |
| `update.sh` | Script de actualización | ✅ Funcionando |

#### `/csv_templates/`
| Archivo | Funcionalidad | Estado |
|---------|---------------|--------|
| `parkings.csv` | Datos iniciales de parkings | ✅ Cargado |
| `accesses.csv` | Datos iniciales de cámaras/accesos | ✅ Cargado |
| `panels.csv` | Datos iniciales de paneles | ✅ Cargado |

## Endpoints de la API REST

### Base URL: `http://157.180.91.63:6001`

| Endpoint | Método | Descripción | Estado | Pruebas |
|----------|--------|-------------|--------|---------|
| `/parkings` | GET | Listar todos los parkings | ✅ Funcionando | ✅ Exitosas |
| `/parking/{id}` | GET | Obtener parking específico | ✅ Funcionando | ✅ Exitosas |
| `/parking/{id}/occupancy` | POST | Actualizar ocupación | ✅ Funcionando | ✅ Exitosas |
| `/parking/{id}/config` | POST | Actualizar configuración | ✅ Funcionando | ✅ Exitosas |
| `/parking/{id}/message` | POST | Enviar mensaje a paneles | ✅ Funcionando | ✅ Exitosas |
| `/parking/{id}/message` | GET | Obtener mensajes programados | ✅ Funcionando | ✅ Exitosas |
| `/panel/{ip}/message` | POST | Enviar mensaje a panel específico | ❓ No probado | ❌ Pendiente |
| `/parking/{id}/schedule` | POST | Programar mensaje | ❓ No probado | ❌ Pendiente |
| `/schedule/{id}` | DELETE | Eliminar mensaje programado | ❓ No probado | ❌ Pendiente |

## Endpoint de Cámaras

### Base URL: `http://157.180.91.63:6400`

| Endpoint | Método | Descripción | Estado | Pruebas |
|----------|--------|-------------|--------|---------|
| `/camera` | POST | Recepción de datos de ocupación | ✅ Funcionando | ✅ Exitosas |

**Formato de datos esperado:**
```json
{
  "device_name": "CAMERA_01",
  "occupancy": 150,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Resultados de Pruebas Realizadas

### Pruebas Exitosas ✅

#### 1. GET /parkings
- **Comando:** `Invoke-WebRequest -Uri "http://157.180.91.63:6001/parkings"`
- **Resultado:** Lista completa de 9 parkings con estados reales
- **Observaciones:** Incluye parkings con descuadres (DESCUADRE_NEGATIVO)

#### 2. GET /parking/1
- **Comando:** `Invoke-WebRequest -Uri "http://157.180.91.63:6001/parking/1"`
- **Resultado:** Detalle del parking 1 con estado DESCUADRE_NEGATIVO
- **Observaciones:** Ocupación 500, capacidad 450, plazas libres -50

#### 3. POST /parking/1/occupancy
- **Comando:** `Invoke-WebRequest -Uri "http://157.180.91.63:6001/parking/1/occupancy" -Method POST -Body '{"occupancy": 480}'`
- **Resultado:** Actualización exitosa, estado DESCUADRE_NEGATIVO
- **Observaciones:** Sistema maneja correctamente ocupaciones superiores a capacidad

#### 4. POST /parking/1/config
- **Comando:** `Invoke-WebRequest -Uri "http://157.180.91.63:6001/parking/1/config" -Method POST -Body '{"max_capacity": 500, "threshold_dense": 30, "threshold_full": 10}'`
- **Resultado:** Configuración actualizada, estado DENSO
- **Observaciones:** Umbrales actualizados correctamente

#### 5. POST /parking/1/message
- **Comando:** `Invoke-WebRequest -Uri "http://157.180.91.63:6001/parking/1/message" -Method POST -Body '{"message": "Test mensaje paneles", "color": "AMARILLO", "scroll": true}'`
- **Resultado:** Mensaje enviado, panel 172.20.17.50 no respondió
- **Observaciones:** Sistema detecta paneles no responsivos

#### 6. GET /parking/1/message
- **Comando:** `Invoke-WebRequest -Uri "http://157.180.91.63:6001/parking/1/message"`
- **Resultado:** Lista vacía (no hay mensajes programados)
- **Observaciones:** Comportamiento correcto

### Pruebas Pendientes ❌

#### 1. POST /panel/{ip}/message
- **Estado:** No probado
- **Razón:** Requiere IP específica de panel disponible

#### 2. POST /parking/{id}/schedule
- **Estado:** No probado
- **Razón:** Funcionalidad de programación no implementada

#### 3. DELETE /schedule/{id}
- **Estado:** No probado
- **Razón:** Funcionalidad de programación no implementada

## Estados de Parking Implementados

| Estado | Descripción | Ejemplo |
|--------|-------------|---------|
| `LIBRE` | Plazas libres suficientes | Parking 3: 200 libres, 0 ocupadas |
| `DENSO` | Ocupación alta pero no completa | Parking 2: 279 libres, 221 ocupadas |
| `COMPLETO` | Parking lleno | Parking 5: 0 libres, 90 ocupadas |
| `DESCUADRE_NEGATIVO` | Ocupación mayor que capacidad | Parking 1: -50 libres, 500 ocupadas |
| `DESCUADRE_POSITIVO` | Ocupación negativa (error) | No implementado |

## Funcionalidades Implementadas

### ✅ Completadas
1. **Gestión de Parkings:** CRUD completo con estados automáticos
2. **Recepción de Datos de Cámaras:** Endpoint para actualización automática
3. **Comunicación con Paneles:** Envío de mensajes con detección de fallos
4. **Gestión de Descuadres:** Registro y análisis de ocupaciones anómalas
5. **Logging Completo:** Auditoría de todas las operaciones
6. **Despliegue Automatizado:** Scripts de instalación y actualización
7. **Servicios Systemd:** Gestión automática de procesos

### ❌ Pendientes
1. **Frontend React:** Interfaz de usuario
2. **Programación de Mensajes:** Envío automático en fechas específicas
3. **Gestión de Usuarios:** Autenticación y autorización
4. **API de Histórico:** Consulta de datos históricos
5. **Notificaciones:** Sistema de alertas por email/SMS

## Problemas Conocidos y Soluciones

### ✅ Resueltos
1. **Errores SQLAlchemy:** Corregidos problemas de sesión cerrada
2. **Descuadres de Ocupación:** Sistema robusto que maneja valores anómalos
3. **Paneles No Responsivos:** Detección y logging de fallos
4. **Logging de Errores:** Sistema completo de auditoría

### ⚠️ En Observación
1. **Panel 172.20.17.50:** No responde a mensajes (posible problema de red)
2. **Descuadres Frecuentes:** Parking 1 y 9 con ocupaciones anómalas

## Métricas del Sistema

### Parkings Activos: 9
- **LIBRE:** 6 parkings
- **DENSO:** 1 parking
- **COMPLETO:** 1 parking
- **DESCUADRE_NEGATIVO:** 2 parkings

### Cámaras Configuradas: Según accesses.csv
### Paneles Configurados: Según panels.csv

## Próximos Pasos

### Prioridad Alta
1. **Desarrollo del Frontend:** Interfaz React para gestión
2. **Sistema de Usuarios:** Autenticación y roles
3. **API de Histórico:** Consulta de datos históricos

### Prioridad Media
1. **Programación de Mensajes:** Funcionalidad completa
2. **Notificaciones:** Sistema de alertas
3. **Optimización de Base de Datos:** Índices y consultas

### Prioridad Baja
1. **Métricas Avanzadas:** Dashboard de estadísticas
2. **Integración Externa:** APIs de terceros
3. **Backup Automático:** Sistema de respaldo

## Contacto y Soporte

- **Desarrollador:** Equipo SWAT-ID
- **Email:** info@swat-id.com
- **Documentación:** `/docs/`
- **Logs:** `/var/log/parking-api/` y `/var/log/parking-camera/`

## Notas de Mantenimiento

1. **Reinicio de Servicios:** `systemctl restart parking-api.service`
2. **Actualización:** Ejecutar `deploy/update.sh`
3. **Logs:** Monitorear `/var/log/parking-api/parking-api.log`
4. **Base de Datos:** Backup diario recomendado
5. **Descuadres:** Revisar semanalmente con `analyze_discrepancies.py` 