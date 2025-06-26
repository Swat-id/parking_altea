# Implementación de Estadísticas - Parking Altea

## Resumen

Se ha implementado un sistema completo de estadísticas y logs para el sistema Parking Altea, eliminando los datos simulados del frontend y proporcionando información real basada en los datos de la base de datos.

## Nuevas Tablas de Base de Datos

### 1. ParkingStatistics
Almacena estadísticas por hora de cada parking:
- `parking_id`: ID del parking
- `date`: Fecha del día
- `hour`: Hora (0-23)
- `avg_occupancy`: Ocupación promedio
- `max_occupancy`: Ocupación máxima
- `min_occupancy`: Ocupación mínima
- `total_vehicles_in`: Total vehículos entrantes
- `total_vehicles_out`: Total vehículos salientes
- `time_libre`: Minutos en estado LIBRE
- `time_denso`: Minutos en estado DENSO
- `time_completo`: Minutos en estado COMPLETO

### 2. DailyStatistics
Almacena estadísticas diarias de cada parking:
- `parking_id`: ID del parking
- `date`: Fecha del día
- `avg_occupancy`: Ocupación promedio diaria
- `max_occupancy`: Ocupación máxima diaria
- `min_occupancy`: Ocupación mínima diaria
- `peak_hour`: Hora de máxima ocupación
- `total_vehicles_in`: Total vehículos entrantes del día
- `total_vehicles_out`: Total vehículos salientes del día
- `time_libre`: Minutos en estado LIBRE
- `time_denso`: Minutos en estado DENSO
- `time_completo`: Minutos en estado COMPLETO

### 3. ActivityLog
Registra todas las actividades del sistema:
- `user_id`: ID del usuario (opcional)
- `parking_id`: ID del parking (opcional)
- `panel_id`: ID del panel (opcional)
- `action_type`: Tipo de acción
- `action_details`: Detalles en JSON
- `ip_address`: IP del usuario
- `user_agent`: User agent del navegador
- `timestamp`: Fecha y hora

### 4. PanelMessageLog
Registra mensajes enviados a paneles:
- `panel_id`: ID del panel
- `parking_id`: ID del parking
- `user_id`: ID del usuario (opcional)
- `message`: Mensaje enviado
- `duration`: Duración en segundos
- `status`: Estado del envío
- `response_time`: Tiempo de respuesta en ms
- `sent_at`: Fecha y hora de envío

### 5. VehicleCount
Registra conteos de vehículos:
- `access_id`: ID del acceso (cámara)
- `parking_id`: ID del parking
- `timestamp`: Fecha y hora
- `vehicles_in`: Vehículos entrantes
- `vehicles_out`: Vehículos salientes
- `total_vehicles_in`: Total acumulado entrantes
- `total_vehicles_out`: Total acumulado salientes

## Mejoras en Tablas Existentes

### Panel
- `status`: Estado del panel (ONLINE/OFFLINE)
- `last_message`: Último mensaje enviado
- `last_update`: Última actualización

### OccupancyHistory
- `previous_occupancy`: Ocupación anterior
- `change_amount`: Diferencia con ocupación anterior

## Nuevos Endpoints de API

### Paneles
- `GET /panels`: Obtener todos los paneles con estado
- `POST /panel/{id}/message`: Enviar mensaje a panel específico
- `POST /panel/{id}/test`: Probar comunicación con panel

### Estadísticas
- `GET /statistics`: Estadísticas de todos los parkings
- `GET /parking/{id}/statistics`: Estadísticas de un parking
- `GET /parking/{id}/history`: Historial de ocupación

### Logs (Requieren Autenticación)
- `GET /logs/activity`: Logs de actividad
- `GET /logs/panels`: Logs de mensajes de paneles

## Módulo de Gestión de Estadísticas

### StatisticsManager
Clase principal para gestionar estadísticas:

#### Métodos Principales:
- `log_activity()`: Registrar actividad del sistema
- `log_panel_message()`: Registrar mensaje de panel
- `log_vehicle_count()`: Registrar conteo de vehículos
- `update_hourly_statistics()`: Actualizar estadísticas por hora
- `update_daily_statistics()`: Actualizar estadísticas diarias
- `get_parking_statistics()`: Obtener estadísticas de un parking
- `get_all_parkings_statistics()`: Obtener estadísticas de todos los parkings
- `get_activity_logs()`: Obtener logs de actividad
- `get_panel_message_logs()`: Obtener logs de paneles

## Scripts de Actualización

### update_database.py
Script para actualizar la base de datos:
- Crear nuevas tablas
- Actualizar tablas existentes
- Crear índices para optimización
- Poblar datos de ejemplo (opcional)

### update_database_remote.sh
Script para actualizar el servidor remoto:
- Crear backup de la base de datos
- Actualizar código desde Git
- Ejecutar script de actualización
- Reiniciar servicios

## Servicios del Frontend

### panelService.js
Servicios para gestión de paneles:
- `getAllPanels()`: Obtener todos los paneles
- `sendMessageToPanel()`: Enviar mensaje
- `testPanel()`: Probar comunicación

### statisticsService.js
Servicios para estadísticas:
- `getAllStatistics()`: Estadísticas generales
- `getParkingStatistics()`: Estadísticas de parking
- `getActivityLogs()`: Logs de actividad
- `getPanelLogs()`: Logs de paneles
- `exportData()`: Exportar datos

## Índices de Base de Datos

Se han creado índices para optimizar las consultas:
- `idx_parking_statistics_parking_date`: Para estadísticas por parking y fecha
- `idx_parking_statistics_date_hour`: Para estadísticas por fecha y hora
- `idx_daily_statistics_parking_date`: Para estadísticas diarias
- `idx_activity_logs_timestamp`: Para logs por timestamp
- `idx_activity_logs_user_action`: Para logs por usuario y acción
- `idx_vehicle_counts_parking_timestamp`: Para conteos por parking y timestamp

## Funcionalidades Implementadas

### 1. Estadísticas en Tiempo Real
- Ocupación promedio, máxima y mínima por hora
- Estadísticas diarias con hora pico
- Conteo de vehículos entrantes y salientes
- Tiempo en cada estado (LIBRE, DENSO, COMPLETO)

### 2. Gestión de Paneles
- Estado en tiempo real (ONLINE/OFFLINE)
- Historial de mensajes enviados
- Pruebas de comunicación
- Tiempo de respuesta

### 3. Logs de Actividad
- Registro de todas las acciones del sistema
- Filtrado por usuario, parking, tipo de acción
- Información de IP y user agent
- Auditoría completa

### 4. Historial Detallado
- Cambios de ocupación con valores anteriores
- Fuente de los cambios (manual, cámara, programado)
- Cantidad de cambio
- Timestamp preciso

## Ventajas de la Implementación

### 1. Datos Reales
- Eliminación completa de datos simulados
- Información basada en eventos reales del sistema
- Precisión en estadísticas y métricas

### 2. Escalabilidad
- Índices optimizados para consultas rápidas
- Estructura modular para fácil extensión
- Separación clara de responsabilidades

### 3. Auditoría
- Logs completos de todas las actividades
- Trazabilidad de cambios
- Información para debugging y análisis

### 4. Flexibilidad
- Filtros múltiples en consultas
- Exportación de datos
- Configuración de períodos de tiempo

## Próximos Pasos

### 1. Implementación de Servicios de Actualización
- Servicio automático para actualizar estadísticas por hora
- Servicio para procesar datos de cámaras
- Actualización de logs en tiempo real

### 2. Mejoras en el Frontend
- Gráficos interactivos con datos reales
- Filtros avanzados de estadísticas
- Exportación de reportes

### 3. Optimizaciones
- Caché de estadísticas frecuentes
- Compresión de datos históricos
- Limpieza automática de logs antiguos

## Archivos Modificados/Creados

### Backend
- `src/models.py`: Nuevos modelos de base de datos
- `src/statistics.py`: Módulo de gestión de estadísticas
- `src/api_server.py`: Nuevos endpoints
- `src/update_database.py`: Script de actualización
- `deploy/update_database_remote.sh`: Script de despliegue

### Frontend
- `client/src/services/panelService.js`: Servicios de paneles
- `client/src/services/statisticsService.js`: Servicios de estadísticas

### Documentación
- `docs/api_endpoints.md`: Documentación actualizada
- `docs/statistics_implementation.md`: Esta documentación
- `test_statistics.py`: Script de pruebas

## Comandos de Despliegue

### Actualizar Base de Datos Local
```bash
cd src
python3 update_database.py
```

### Actualizar Servidor Remoto
```bash
chmod +x deploy/update_database_remote.sh
./deploy/update_database_remote.sh
```

### Probar Funcionalidades
```bash
python3 test_statistics.py
```

## Conclusión

La implementación de estadísticas proporciona una base sólida para el análisis de datos del sistema Parking Altea, eliminando la dependencia de datos simulados y ofreciendo información precisa y en tiempo real sobre el funcionamiento del sistema. 