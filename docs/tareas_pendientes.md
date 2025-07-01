# Tareas Pendientes - Parking Altea

## 📋 Estado General

**Fecha de Actualización**: 1 de Julio de 2025  
**Versión Actual**: v2.7.1 - Corrección de Cálculo de Deltas  
**Estado**: 🟡 **DESARROLLO COMPLETADO - CORRECCIÓN APLICADA**

---

## 🎯 Tareas Pendientes v2.7.1

### 🔴 Críticas (Antes del Despliegue)

#### 1. Pruebas en Servidor de Producción
- [ ] **Desplegar código v2.7.1** en servidor 157.180.91.63
- [ ] **Ejecutar migración de base de datos** (`migrate_panel_schedules.py`)
- [ ] **Reiniciar servicios backend** (parking-api, parking-camera)
- [ ] **Construir y desplegar frontend** actualizado
- [ ] **Configurar servicio de monitorización** (`setup_schedule_monitor.sh`)
- [ ] **Verificar funcionamiento** de todos los endpoints nuevos
- [ ] **Probar creación de programaciones** desde la interfaz web
- [ ] **Validar ejecución automática** del servicio de monitorización
- [ ] **Verificar corrección del cálculo de deltas** con datos reales

#### 2. Validación de Funcionalidad Completa
- [ ] **Probar flujo completo** de creación de programación
- [ ] **Verificar ejecución automática** según horarios
- [ ] **Comprobar finalización automática** y restauración de estado
- [ ] **Validar logs de auditoría** en base de datos
- [ ] **Probar integración** con sistema de paneles existente
- [ ] **Verificar que no afecta** funcionalidades actuales
- [ ] **Comprobar rendimiento** del sistema con programaciones activas
- [ ] **Validar corrección de deltas** con mensajes de cámaras reales

#### 3. Configuración de Servicios
- [ ] **Instalar servicio systemd** para monitor de programaciones
- [ ] **Configurar inicio automático** del servicio
- [ ] **Verificar logs del servicio** en journalctl
- [ ] **Configurar rotación de logs** para evitar crecimiento excesivo
- [ ] **Probar reinicio automático** del servicio en caso de fallo

### 🟡 Importantes (Después del Despliegue)

#### 4. Entrenamiento y Documentación de Usuario
- [ ] **Crear manual de usuario** para gestión de programaciones
- [ ] **Documentar casos de uso** comunes
- [ ] **Crear guía de troubleshooting** para problemas frecuentes
- [ ] **Entrenar usuarios finales** en nuevas funcionalidades
- [ ] **Crear videos tutoriales** para funciones complejas

#### 5. Optimización y Monitoreo
- [ ] **Optimizar consultas** de base de datos para programaciones
- [ ] **Configurar alertas** para fallos del servicio de monitorización
- [ ] **Implementar métricas** de rendimiento del sistema
- [ ] **Configurar backup automático** de programaciones
- [ ] **Optimizar uso de memoria** del servicio de monitorización

#### 6. Pruebas de Carga y Estabilidad
- [ ] **Probar con múltiples programaciones** simultáneas
- [ ] **Verificar comportamiento** con muchos parkings
- [ ] **Probar recuperación** tras fallos del sistema
- [ ] **Validar funcionamiento** durante 24/7
- [ ] **Comprobar integridad** de datos tras reinicios

### 🟢 Mejoras Futuras (v2.7.2 y v2.8)

#### 7. Funcionalidades Avanzadas (v2.7.2)
- [ ] **Programaciones recurrentes** con patrones complejos
- [ ] **Notificaciones por email** cuando programaciones fallan
- [ ] **Dashboard de programaciones** con vista general
- [ ] **Exportar/importar** programaciones (backup/restore)
- [ ] **Programaciones condicionales** basadas en ocupación
- [ ] **Interfaz de programación visual** tipo calendario

#### 8. Nuevas Características (v2.8)
- [ ] **Programaciones por panel individual** en lugar de por parking
- [ ] **App móvil** para gestión de programaciones
- [ ] **Programaciones desde API externa** (integración con otros sistemas)
- [ ] **Programaciones con imágenes** o contenido multimedia
- [ ] **Sistema de plantillas** para programaciones comunes
- [ ] **Programaciones inteligentes** con IA (predicción de ocupación)

---

## 🔧 Corrección de Cálculo de Deltas (v2.7.1)

### Problema Identificado
- **Error**: Cálculo incorrecto de deltas causando descuadres en ocupación
- **Ejemplo**: Contador 408→409 reportaba +3 en lugar de +1
- **Impacto**: Afectaba la precisión del conteo de vehículos

### Causa Raíz
- Lógica incorrecta en función `detect_camera_reset`
- Ajuste incorrecto de contadores anteriores en caso de reinicio
- Fórmula problemática: `adjusted_previous_in = 0 if new_in <= previous_in else previous_in`

### Solución Implementada
- ✅ **Corrección de función** `detect_camera_reset`
- ✅ **Simplificación de lógica**: siempre usar 0 en caso de reinicio
- ✅ **Logging detallado** para diagnóstico
- ✅ **Script de pruebas** `test_delta_calculation.py` para validar corrección

### Archivos Modificados
- `src/camera_server.py` - Corrección de funciones de cálculo de deltas
- `test/test_delta_calculation.py` - Script de pruebas para validar corrección

### Estado
✅ **Corregido y probado** - Listo para despliegue

---

## 🚀 Plan de Despliegue

### Fase 1: Preparación (1-2 días)
1. **Backup completo** de base de datos actual
2. **Preparar scripts** de despliegue
3. **Verificar dependencias** en servidor
4. **Crear rama de producción** en git

### Fase 2: Despliegue (1 día)
1. **Ejecutar migración** de base de datos
2. **Desplegar código backend** actualizado (incluyendo corrección de deltas)
3. **Construir y desplegar frontend**
4. **Configurar servicio de monitorización**
5. **Verificar servicios** funcionando

### Fase 3: Validación (2-3 días)
1. **Pruebas funcionales** completas
2. **Validación de integración** con sistema existente
3. **Pruebas de carga** y rendimiento
4. **Verificación de logs** y auditoría
5. **Validación específica** de corrección de deltas
6. **Corrección de problemas** encontrados

### Fase 4: Entrenamiento (1 día)
1. **Crear documentación** de usuario
2. **Entrenar usuarios** finales
3. **Configurar alertas** y monitoreo
4. **Documentar lecciones aprendidas**

---

## 📊 Métricas de Seguimiento

### Indicadores de Éxito
- [ ] **100% de endpoints** funcionando correctamente
- [ ] **0 errores críticos** en logs del sistema
- [ ] **Tiempo de respuesta** < 2 segundos para operaciones de programación
- [ ] **Uptime del servicio** de monitorización > 99.9%
- [ ] **Usuarios entrenados** y capaces de usar nuevas funcionalidades
- [ ] **Cálculo de deltas** preciso (sin descuadres)

### Indicadores de Rendimiento
- [ ] **Uso de memoria** del servicio de monitorización < 512MB
- [ ] **Tiempo de procesamiento** de programaciones < 5 segundos
- [ ] **Número de logs** de auditoría generados correctamente
- [ ] **Integridad de datos** en base de datos mantenida
- [ ] **Precisión de conteo** de vehículos (deltas correctos)

---

## 🔧 Recursos Necesarios

### Servidor de Producción
- **IP**: 157.180.91.63
- **Sistema**: Ubuntu/Debian
- **Servicios**: parking-api, parking-camera, panel-service
- **Base de datos**: PostgreSQL

### Archivos de Despliegue
- `deploy/setup_panel_schedules.sh` - Script principal de despliegue
- `deploy/setup_schedule_monitor.sh` - Configuración del monitor
- `src/migrate_panel_schedules.py` - Migración de base de datos
- `deploy/parking-schedule-monitor.service` - Servicio systemd

### Archivos de Corrección
- `src/camera_server.py` - Corrección de cálculo de deltas
- `test/test_delta_calculation.py` - Pruebas de validación

### Documentación
- `docs/v2.7_status.md` - Estado completo de la versión
- `docs/project_status.md` - Estado general del proyecto
- `docs/development_status.md` - Estado técnico detallado

---

## 📞 Contactos y Responsabilidades

### Desarrollo
- **Responsable**: Equipo de desarrollo
- **Tareas**: Despliegue, configuración, pruebas técnicas

### Operaciones
- **Responsable**: Administrador del servidor
- **Tareas**: Configuración de servicios, monitoreo, backup

### Usuarios Finales
- **Responsable**: Gestores de parking
- **Tareas**: Pruebas de funcionalidad, entrenamiento, uso diario

---

**Última actualización**: 1 de Julio de 2025  
**Próxima revisión**: Después del despliegue en producción 