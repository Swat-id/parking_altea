# 📚 Documentación Parking Altea v2.7.1

## 🎯 **Documentación Principal**

### **Estado y Contexto del Proyecto**
- **[Estado del Proyecto v2.7.1](project_status_v2.7.1.md)** - Estado completo del proyecto con todas las funcionalidades
- **[Resumen Ejecutivo](executive_summary.md)** - Resumen ejecutivo del proyecto
- **[Contexto del Proyecto](project_context.md)** - Contexto y objetivos del sistema

### **Manuales de Operación**
- **[Manual de Mantenimiento y Despliegue](maintenance_deployment_manual_v2.7.1.md)** - Manual completo desde instalación hasta mantenimiento
- **[Guía de Despliegue](deployment.md)** - Guía específica de despliegue
- **[Manual de Mantenimiento](maintenance.md)** - Mantenimiento del sistema

## 🔧 **Documentación Técnica**

### **APIs y Endpoints**
- **[Documentación de API](api.md)** - Documentación completa de la API REST
- **[Endpoints de API](api_endpoints.md)** - Lista detallada de endpoints
- **[Integración de Paneles](panel_integration.md)** - Integración con paneles LED
- **[Protocolo CP5200](cp5200_protocol.md)** - Protocolo de comunicación con paneles

### **Base de Datos**
- **[Esquema de Base de Datos](database.md)** - Estructura y relaciones de la base de datos
- **[Modelos de Datos](models.md)** - Modelos SQLAlchemy

### **Servicios y Componentes**
- **[Servicio de Cámaras](cameras.md)** - Procesamiento de mensajes de cámaras
- **[Servicio de Programaciones](panels_v2.6.md)** - Sistema de programaciones automáticas
- **[Monitor de Programaciones](schedule_integration_summary.md)** - Monitor automático de programaciones
- **[Integración de Programaciones](schedule_panel_integration.md)** - Integración completa

## 🚀 **Guías de Desarrollo**

### **Configuración y Desarrollo**
- **[Configuración de Desarrollo](development_status.md)** - Estado del desarrollo
- **[Instaladores de Cámaras](camera_installers.md)** - Instalación de cámaras
- **[Configuración de Paneles](panels.md)** - Configuración de paneles LED

### **Testing y Validación**
- **[Guía de Testing](test.md)** - Testing del sistema
- **[Automatización de Tests](test_automation.md)** - Tests automatizados
- **[Validación de Sistema](INSTRUCCIONES_TESTS.md)** - Instrucciones de testing

## 📊 **Reportes y Estadísticas**

### **Análisis y Reportes**
- **[Análisis de SDK](sdk_analysis_summary.md)** - Análisis del SDK de paneles
- **[Implementación de Estadísticas](statistics_implementation.md)** - Sistema de estadísticas
- **[Reporte de Validación](parking_validation_report_20250626_152355.json)** - Reporte de validación

### **Estado de Versiones**
- **[Estado v2.3](v2.3_status.md)** - Estado de la versión 2.3
- **[Estado v2.4](v2.4_status.md)** - Estado de la versión 2.4
- **[Estado v2.6](v2.6_status.md)** - Estado de la versión 2.6
- **[Estado v2.7](v2.7_status.md)** - Estado de la versión 2.7

### **Versiones de Desarrollo Activas**
- **[Documentación v3.1.0](v3.1.0/)** - Versión 3.1.0 con mejoras de sistema
- **[Documentación v3.2.0](v3.2.0/)** - Versión 3.2.0 con sistema de alarmas
- **[Documentación v3.3.0](v3.3.0/)** - Versión 3.3.0 con optimizaciones
- **[Documentación v3.4.0](v3.4.0/)** - Versión 3.4.0 con arquitectura separada (PRODUCCIÓN)
- **[Documentación v3.5.0](v3.5.0/)** - Versión 3.5.0 corrección de errores (EN DESARROLLO)

## 🔧 **Correcciones y Mejoras**

### **Correcciones Recientes**
- **[Correcciones v2.7.1](v2.7.1_fixes_summary.md)** - Resumen de correcciones de la versión 2.7.1
- **[Tareas Pendientes](tareas_pendientes.md)** - Lista de tareas pendientes

### **Actualizaciones Específicas**
- **[Actualización Frontend Paneles v2.6](frontend_panels_v2.6_update.md)** - Actualización del frontend
- **[Despliegue Paneles v2.6](panels_v2.6_deployment_summary.md)** - Resumen de despliegue

## 📋 **Información del Sistema**

### **Arquitectura**
- **Frontend:** React + Vite (puerto 80, nginx)
- **Backend API:** Python Flask + Gunicorn (puerto 6001)
- **Servicio de Cámaras:** Python Flask + Gunicorn (puerto 6400)
- **Monitor de Programaciones:** Python (servicio systemd)
- **Base de Datos:** PostgreSQL
- **Comunicación con Paneles:** API REST (puerto 5656)

### **Servicios Systemd**
- `parking-api.service` - API principal
- `parking-camera.service` - Procesamiento de cámaras
- `parking-schedule-monitor.service` - Monitor de programaciones

### **Puertos Utilizados**
- **80:** Frontend (nginx)
- **6001:** API Principal
- **6400:** API de Cámaras
- **5656:** Servicio de Paneles
- **5432:** PostgreSQL

## 🚨 **Estado Actual**

### **Versión en Producción:** v3.4.0
### **Estado:** ✅ **PRODUCCIÓN - OPERATIVO** (Arquitectura Separada)
### **Versión en Desarrollo:** v3.5.0 (Corrección de Errores)
### **Última Actualización:** Enero 2025
### **Última Mejora:** Arquitectura separada de mensajes y paneles implementada

### **Servicios Activos v3.4.0:**
- ✅ **API Server** (puerto 8080) - Operativo con arquitectura separada
- ✅ **Camera Server** (puerto 5000) - Operativo con procesamiento concurrente
- ✅ **Panel Worker** - Operativo con workers independientes
- ✅ **Frontend** (nginx puerto 5789) - Operativo
- ✅ **Base de Datos** (PostgreSQL) - Operativo

## 📞 **Contacto y Soporte**

- **Desarrollador:** Equipo de desarrollo
- **Documentación:** `/docs/`
- **Logs:** `journalctl -u parking-*`
- **Estado:** Todos los servicios operativos

---

*Documentación Parking Altea - Actualizada para v3.4.0 (Producción) y v3.5.0 (Desarrollo) - Enero 2025* 