# Documentación del Sistema Parking Altea v2.6

## Índice de Documentación

Esta documentación proporciona información completa sobre el sistema de gestión de aparcamientos Parking Altea v2.6, incluyendo su arquitectura, API, protocolos de comunicación, base de datos, despliegue y mantenimiento.

**Versión Actual**: v2.6 - Sistema Completo con Paneles Electrónicos  
**Fecha de Actualización**: 1 de Julio de 2025  
**Estado**: ✅ PRODUCCIÓN - FUNCIONAL COMPLETO

---

## 📋 Documentación Principal

### [README.md](./README.md)
Documentación general del proyecto con descripción, arquitectura, componentes principales y estado del proyecto.

**Contenido:**
- Descripción general del sistema
- Arquitectura y diagramas
- Componentes principales
- Tecnologías utilizadas
- Estado del proyecto

### [Estado del Proyecto](./project_status.md)
Documento completo del estado actual del proyecto con resultados de pruebas y funcionalidades implementadas.

**Contenido:**
- Información general del proyecto v2.6
- Arquitectura del sistema completo
- Flujos de gestión de mensajes
- Endpoints implementados y probados
- Métricas de rendimiento
- Problemas resueltos y soluciones
- Configuración de producción

### [Estado de Desarrollo](./development_status.md)
Documentación detallada del estado de desarrollo con progreso por componentes.

**Contenido:**
- Progreso general del proyecto
- Estado detallado por componentes
- Funcionalidades completadas v2.6
- Problemas resueltos
- Métricas de rendimiento
- Estado final del desarrollo

### [Estado v2.6](./v2.6_status.md)
Documentación específica de la versión v2.6 con detalles de implementación.

**Contenido:**
- Objetivos de la versión v2.6
- Arquitectura del sistema v2.6
- Problemas resueltos en v2.6
- Funcionalidades implementadas
- Pruebas y validación
- Configuración de producción

---

## 🔌 API y Comunicación

### [API REST - Endpoints](./api_endpoints.md)
Documentación detallada de todos los endpoints de la API REST con ejemplos reales de pruebas.

**Contenido:**
- Todos los endpoints disponibles
- Ejemplos de respuestas reales
- Estados de parking implementados
- Manejo de errores
- Códigos de estado HTTP
- Notas importantes sobre descuadres y paneles

### [API REST](./api.md)
Documentación completa de la API REST pública del sistema.

**Contenido:**
- Endpoints disponibles
- Formatos de respuesta
- Ejemplos de uso
- Códigos de estado HTTP
- Estados de aparcamiento
- Ejemplos de integración

### [Protocolo de Cámaras](./cameras.md)
Especificación del protocolo de comunicación con las cámaras de conteo.

**Contenido:**
- Formato de mensajes HTTP POST
- Campos requeridos y opcionales
- Procesamiento de mensajes
- Configuración de cámaras
- Troubleshooting

### [Comunicación con Paneles](./panels.md)
Protocolo de comunicación con los paneles electrónicos.

**Contenido:**
- Endpoints de paneles
- Tipos de mensajes
- Lógica de envío
- Configuración de paneles
- Gestión de errores

### [Paneles v2.6](./panels_v2.6.md)
Documentación específica de la integración de paneles en v2.6.

**Contenido:**
- Workflow de paneles v2.6
- Servicio Java REST
- PanelCommunicationService
- Mensajes en valenciano
- Colores dinámicos

---

## 🗄️ Base de Datos

### [Esquema de Base de Datos](./database.md)
Documentación completa del esquema de base de datos PostgreSQL.

**Contenido:**
- Diagrama ER
- Definición de tablas
- Modelos SQLAlchemy
- Consultas frecuentes
- Mantenimiento de BD
- Configuración PostgreSQL

---

## 🚀 Despliegue y Configuración

### [Guía de Despliegue](./deployment.md)
Guía completa de instalación y configuración del sistema.

**Contenido:**
- Requisitos del sistema
- Instalación paso a paso
- Configuración de servicios
- Verificación de instalación
- Scripts de despliegue
- Troubleshooting

### [Despliegue Paneles v2.6](./panels_v2.6_deployment_summary.md)
Resumen del despliegue de la funcionalidad de paneles v2.6.

**Contenido:**
- Proceso de despliegue
- Configuración de servicios
- Validación de funcionalidad
- Troubleshooting

---

## 🔧 Mantenimiento y Monitoreo

### [Mantenimiento y Monitoreo](./maintenance.md)
Guía de mantenimiento rutinario y monitoreo del sistema.

**Contenido:**
- Monitoreo diario
- Mantenimiento semanal/mensual
- Scripts de monitoreo automático
- Troubleshooting avanzado
- Alertas y notificaciones
- Reportes automáticos

### [Pruebas Automatizadas](./test_automation.md)
Sistema de pruebas automatizadas para verificar el funcionamiento de la API.

**Contenido:**
- Script de pruebas automatizadas
- Endpoints probados
- Interpretación de resultados
- Integración con CI/CD
- Monitoreo continuo
- Troubleshooting de pruebas

---

## 📊 Análisis y Reportes

### [Análisis de SDK](./sdk_analysis_summary.md)
Análisis del SDK de paneles electrónicos.

**Contenido:**
- Análisis del protocolo CP5200
- Documentación del fabricante
- Ejemplos de implementación
- Recomendaciones

### [Implementación de Estadísticas](./statistics_implementation.md)
Documentación de la implementación del sistema de estadísticas.

**Contenido:**
- Funcionalidades de estadísticas
- Gráficos implementados
- Consultas de base de datos
- Optimización de rendimiento

---

## 📁 Estructura del Proyecto v2.6

```
parking_altea/
├── docs/                          # Documentación
│   ├── README.md                  # Documentación principal
│   ├── project_status.md          # Estado del proyecto v2.6
│   ├── development_status.md      # Estado de desarrollo
│   ├── v2.6_status.md             # Estado específico v2.6
│   ├── api_endpoints.md           # Endpoints API con ejemplos
│   ├── api.md                     # API REST
│   ├── cameras.md                 # Protocolo cámaras
│   ├── panels.md                  # Protocolo paneles
│   ├── panels_v2.6.md             # Paneles v2.6
│   ├── database.md                # Esquema BD
│   ├── deployment.md              # Guía despliegue
│   ├── maintenance.md             # Mantenimiento
│   └── index.md                   # Este archivo
├── client/                        # Frontend React
│   ├── src/                       # Código fuente React
│   ├── package.json               # Dependencias
│   └── vite.config.js             # Configuración Vite
├── server/                        # Backend Python
│   ├── api_server.py             # Servidor API REST
│   ├── camera_server.py          # Servidor de cámaras
│   ├── panel_communication_service.py # Servicio de comunicación
│   ├── models.py                 # Modelos de BD
│   ├── config.py                 # Configuración
│   ├── init_db.py                # Inicialización BD
│   └── load_data.py              # Carga de datos
├── csv_templates/                 # Plantillas CSV
│   ├── parkings.csv              # Datos de aparcamientos
│   ├── accesses.csv              # Datos de cámaras
│   └── panels.csv                # Datos de paneles
├── deploy/                        # Archivos de despliegue
│   ├── setup.sh                  # Script de instalación
│   ├── deploy_frontend.sh        # Despliegue frontend
│   ├── deploy_and_validate.sh    # Despliegue completo
│   ├── parking-api.service       # Servicio systemd API
│   ├── parking-camera.service    # Servicio systemd cámaras
│   └── panel-service.service     # Servicio systemd paneles
├── requirements.txt               # Dependencias Python
└── README.md                      # README del proyecto
```

---

## 🔗 Enlaces Rápidos

### Servicios del Sistema
- **API REST**: http://157.180.91.63:6001
- **Servidor de Cámaras**: http://157.180.91.63:6400
- **Base de Datos**: localhost:5432

### Comandos Útiles
```bash
# Verificar estado de servicios
systemctl status parking-api.service parking-camera.service

# Ver logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f

# Probar API
curl http://157.180.91.63:6001/parkings

# Conectar a base de datos
sudo -u postgres psql -d parking_db
```

### Archivos de Configuración Importantes
- **Variables de entorno**: `/opt/parking_altea/.env`
- **Logs del sistema**: `/var/log/`
- **Configuración systemd**: `/etc/systemd/system/`

---

## 📞 Soporte y Contacto

### Información de Contacto
- **Email**: info@swat-id.com
- **Servidor**: 157.180.91.63
- **Usuario**: root

### Recursos de Ayuda
- [Troubleshooting](./maintenance.md#troubleshooting-avanzado)
- [Logs del sistema](./maintenance.md#monitoreo-diario)
- [Verificación de estado](./deployment.md#verificación-de-la-instalación)
- [Estado del proyecto](./project_status.md)

---

## 📝 Notas de Versión

### Versión Actual: 1.1
- **Fecha**: Junio 2025
- **Estado**: Producción
- **Última actualización**: Documentación completa con ejemplos de pruebas

### Características Implementadas
✅ Servidor de recepción de cámaras  
✅ API REST pública  
✅ Comunicación con paneles  
✅ Base de datos PostgreSQL  
✅ Scripts de despliegue  
✅ Documentación completa  
✅ Monitoreo y mantenimiento  
✅ Gestión de descuadres de ocupación  
✅ Logging completo de operaciones  
✅ Análisis de discrepancias  

### Próximas Mejoras
🔄 Panel de administración web (React)  
🔄 Sistema de programación de mensajes  
🔄 API de histórico de ocupación  
🔄 Sistema de autenticación de usuarios  
🔄 Notificaciones por email/SMS  

---

## 📚 Referencias Técnicas

### Tecnologías Utilizadas
- **Backend**: Python 3.x, Flask
- **Base de Datos**: PostgreSQL 12+
- **ORM**: SQLAlchemy 2.0
- **Servidor WSGI**: Gunicorn
- **Gestión de Servicios**: Systemd
- **Comunicación**: HTTP REST

### Estándares y Protocolos
- **API**: RESTful HTTP
- **Formato de Datos**: JSON
- **Base de Datos**: SQL (PostgreSQL)
- **Logs**: Systemd Journal

---

*Esta documentación se actualiza regularmente. Para sugerencias o correcciones, contactar al equipo de desarrollo.* 