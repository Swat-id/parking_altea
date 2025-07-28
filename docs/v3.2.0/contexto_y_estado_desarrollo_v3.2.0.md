# Contexto y Estado del Desarrollo - v3.2.0_alarms

## 📋 Información General

- **Versión**: v3.2.0_alarms
- **Fecha de Creación**: 28/07/2025
- **Rama Base**: v3.1.0_login
- **Estado**: En desarrollo
- **Última Actualización**: Sistema completamente operativo con mejoras de Fase 1 y 2 implementadas

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **Backend (Python/Flask)**
   - API Server (`api_server.py`) - Puerto 6001
   - Camera Server (`camera_server.py`) - Procesamiento de mensajes de cámaras
   - Panel Communication Service (`panel_communication_service.py`) - Comunicación con paneles LED
   - Panel Schedule Service (`panel_schedule_service.py`) - Gestión de programaciones
   - Schedule Monitor Service (`schedule_monitor_service.py`) - Monitorización de programaciones activas

2. **Frontend (React/Vite)**
   - Puerto de desarrollo: 5789
   - Puerto de producción: 80 (nginx)
   - Interfaz de administración completa

3. **Base de Datos (PostgreSQL)**
   - Gestión de usuarios, parkings, cámaras, paneles y programaciones

## 🌐 Información del Servidor Remoto

### Datos de Conexión
- **IP**: 157.180.91.63
- **Usuario**: root
- **Directorio**: `/opt/parking_altea`
- **Entorno Virtual**: `/opt/parking_altea/venv`

### Servicios del Sistema
```bash
# Servicios principales
parking-api.service          # API Server (Puerto 6001)
parking-camera.service       # Camera Server
parking-schedule-monitor.service  # Schedule Monitor

# Comandos de gestión
systemctl start/stop/restart/status [servicio]
```

### Puertos Utilizados
- **6001**: API Server (Backend)
- **5789**: Frontend Development
- **80**: Frontend Production (nginx)
- **5432**: PostgreSQL Database

## 📊 Estado Actual del Sistema

### ✅ Funcionalidades Implementadas y Validadas

#### Fase 1 - Correcciones Críticas (COMPLETADA)
1. **Verificación de Programaciones Activas en Camera Server**
   - Modificado `camera_server.py` para verificar programaciones activas antes de actualizar paneles
   - Si hay programación activa, se omite la actualización del panel
   - Logging detallado del estado de procesamiento

2. **API Enriquecida para Paneles**
   - Endpoint `/api/panels` actualizado con información de programaciones activas
   - Nuevos campos: `active_schedule`, `message_type`
   - Información completa de programaciones activas

#### Fase 2 - Mejoras del Frontend (COMPLETADA)
1. **Nueva Columna "Programación Activa"**
   - Muestra detalles de programaciones activas
   - Información de horarios y mensajes
   - Botón para ver detalles completos

2. **Indicadores Visuales de Tipo de Mensaje**
   - Iconos y colores para diferentes tipos de mensaje
   - Programación, Ocupación, Temporal
   - Mejor experiencia de usuario

3. **Modal de Información de Programación**
   - Componente `ScheduleInfoModal.jsx` creado
   - Muestra detalles completos de programaciones
   - Formato de fechas y horarios

4. **Servicios Frontend Mejorados**
   - `panelService.js` actualizado con nuevos métodos
   - Estadísticas de programaciones activas
   - Mejor manejo de datos

### 🔧 Estado de los Paneles (Validado - 28/07/2025)

**Todos los paneles funcionando correctamente:**

| Panel | Estado | Mensaje | Programación Activa |
|-------|--------|---------|-------------------|
| PANEL PALAU | ✅ ONLINE | "EN PROVES " | ✅ ID: 38 |
| PANEL C. ESPORTIVA | ✅ ONLINE | "EN PROVES " | ✅ ID: 33 |
| PANEL BASSETA 1 | ✅ ONLINE | "EN PROVES " | ✅ ID: 37 |
| PANEL BASSETA 2 | ✅ ONLINE | "EN PROVES " | ✅ ID: 37 |
| PANEL PITERES | ✅ ONLINE | "EN PROVES " | ✅ ID: 31 |
| PANEL RENFE | ✅ ONLINE | "EN PROVES " | ✅ ID: 32 |
| PANEL ALTEA VELLA | ✅ ONLINE | "EN PROVES " | ✅ ID: 34 |
| PANEL PITERES 2 | ✅ ONLINE | "EN PROVES " | ✅ ID: 31 |
| PANEL COCOLISO | ✅ ONLINE | "EN PROVES " | ✅ ID: 38 |
| BELLES ARTS 2 | ✅ ONLINE | "EN PROVES " | ✅ ID: 36 |
| BELLES ARTS | ✅ ONLINE | "EN PROVES " | ✅ ID: 35 |

## 🚀 Proceso de Despliegue

### Preparación Local
```bash
# 1. Verificar cambios
git status
git add .
git commit -m "Descripción de cambios"

# 2. Subir a repositorio
git push origin v3.2.0_alarms
```

### Despliegue en Servidor Remoto

#### Paso 1: Parar Servicios
```bash
ssh root@157.180.91.63
systemctl stop parking-api.service
systemctl stop parking-camera.service
systemctl stop parking-schedule-monitor.service
```

#### Paso 2: Actualizar Código
```bash
cd /opt/parking_altea
git fetch --all
git reset --hard origin/v3.2.0_alarms
```

#### Paso 3: Instalar Dependencias Backend
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### Paso 4: Instalar y Compilar Frontend
```bash
cd client
npm install
npm run build
```

#### Paso 5: Copiar Archivos Compilados
```bash
cp -r dist/* /opt/parking_altea/static/
```

#### Paso 6: Reiniciar Servicios
```bash
systemctl start parking-api.service
systemctl start parking-camera.service
systemctl start parking-schedule-monitor.service
```

#### Paso 7: Verificar Estado
```bash
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service
curl http://localhost:6001/api/panels
```

## 🔍 Verificación del Sistema

### Comandos de Verificación
```bash
# Estado de servicios
systemctl status parking-api.service parking-camera.service parking-schedule-monitor.service

# API funcionando
curl http://localhost:6001/api/panels

# Frontend accesible
curl http://157.180.91.63

# Logs de servicios
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f
journalctl -u parking-schedule-monitor.service -f
```

### Validación de Funcionalidades
1. **API de Paneles**: Endpoint `/api/panels` con información completa
2. **Programaciones Activas**: Verificación de programaciones "EN PROVES"
3. **Comunicación con Paneles**: Mensajes correctos en todos los paneles
4. **Frontend**: Interfaz de administración funcional

## 📁 Estructura de Archivos Importantes

### Backend
- `src/api_server.py` - API principal
- `src/camera_server.py` - Servicio de cámaras
- `src/panel_communication_service.py` - Comunicación con paneles
- `src/panel_schedule_service.py` - Gestión de programaciones
- `src/schedule_monitor_service.py` - Monitorización
- `src/models.py` - Modelos de base de datos

### Frontend
- `client/src/pages/Panels.jsx` - Página de paneles
- `client/src/components/ScheduleInfoModal.jsx` - Modal de programaciones
- `client/src/services/panelService.js` - Servicios de paneles

### Configuración
- `deploy/parking-api.service` - Servicio API
- `deploy/parking-camera.service` - Servicio Cámaras
- `deploy/parking-schedule-monitor.service` - Servicio Monitor

## 🎯 Próximos Pasos para v3.2.0_alarms

### Funcionalidades Planificadas
1. **Sistema de Alarmas**
   - Detección de anomalías en cámaras
   - Alertas de desconexión de paneles
   - Notificaciones de errores críticos

2. **Mejoras de Monitoreo**
   - Dashboard de estado del sistema
   - Métricas de rendimiento
   - Logs centralizados

3. **Optimizaciones**
   - Mejoras de rendimiento
   - Optimización de consultas de base de datos
   - Cache de datos frecuentes

## 📞 Contacto y Soporte

- **Desarrollador**: Asistente AI
- **Fecha de Documentación**: 28/07/2025
- **Estado**: Sistema operativo y estable

---

**Nota**: Este documento debe actualizarse con cada nueva funcionalidad implementada en v3.2.0_alarms. 