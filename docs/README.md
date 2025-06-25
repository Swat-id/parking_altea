# Parking Altea - Sistema de Gestión de Aparcamientos

## Descripción General

Sistema de gestión inteligente de aparcamientos para Altea que integra cámaras de conteo de vehículos, paneles informativos electrónicos y una API REST para la gestión y consulta de datos de ocupación.

## Arquitectura del Sistema

```
┌─────────────────┐    HTTP POST    ┌─────────────────┐
│   Cámaras IP    │ ──────────────► │ Servidor Cámaras│
│                 │                 │   Puerto 6400   │
└─────────────────┘                 └─────────────────┘
                                              │
                                              ▼
┌─────────────────┐                 ┌─────────────────┐
│   API REST      │ ◄────────────── │   Base de       │
│  Puerto 6001    │                 │   Datos         │
└─────────────────┘                 │  PostgreSQL     │
       │                            └─────────────────┘
       ▼
┌─────────────────┐
│  Paneles        │
│  Electrónicos   │
└─────────────────┘
```

## Componentes Principales

### 1. Servidor de Cámaras (Puerto 6400)
- Recibe mensajes HTTP POST de las cámaras de conteo
- Procesa datos de entrada/salida de vehículos
- Actualiza contadores y ocupación en tiempo real
- Envía información a paneles electrónicos

### 2. API REST (Puerto 6001)
- Consulta de estado de aparcamientos
- Gestión manual de ocupación
- Programación de mensajes en paneles
- Endpoints públicos para integración

### 3. Base de Datos PostgreSQL
- Almacenamiento de datos de aparcamientos
- Histórico de ocupación (15 días)
- Configuración de cámaras y paneles
- Mensajes programados

### 4. Comunicación con Paneles
- Envío automático de estado de ocupación
- Mensajes personalizados programados
- Protocolo HTTP REST

## Características Principales

- **Tiempo Real**: Actualización automática de ocupación desde cámaras
- **Estados Inteligentes**: LIBRE, DENSO, OCUPADO según umbrales configurables
- **Histórico**: Registro de 15 días de evolución de ocupación
- **API Pública**: Endpoints REST para integración externa
- **Mensajes Programados**: Sistema de mensajes temporales en paneles
- **Escalable**: Arquitectura modular y servicios independientes

## Tecnologías Utilizadas

- **Backend**: Python 3.x con Flask
- **Base de Datos**: PostgreSQL
- **ORM**: SQLAlchemy
- **Servidor WSGI**: Gunicorn
- **Gestión de Servicios**: Systemd
- **Comunicación**: HTTP REST

## Despliegue

El sistema está desplegado en el servidor Ubuntu con IP: `157.180.91.63`

### Puertos Utilizados
- **6001**: API REST pública
- **6400**: Servidor de recepción de cámaras
- **5432**: PostgreSQL (interno)

## Documentación Detallada

- [API REST](./api.md) - Documentación completa de endpoints
- [Protocolo de Cámaras](./cameras.md) - Formato de mensajes de cámaras
- [Comunicación con Paneles](./panels.md) - Protocolo de comunicación
- [Base de Datos](./database.md) - Esquema y modelos de datos
- [Despliegue](./deployment.md) - Guía de instalación y configuración
- [Mantenimiento](./maintenance.md) - Tareas de mantenimiento y monitoreo

## Estado del Proyecto

✅ **Completado**:
- Arquitectura base del sistema
- Servidor de recepción de cámaras
- API REST pública
- Base de datos PostgreSQL
- Comunicación con paneles
- Scripts de despliegue
- Documentación técnica

🔄 **En Desarrollo**:
- Pruebas de integración
- Optimización de rendimiento
- Monitoreo y alertas

📋 **Pendiente**:
- Panel de administración web
- Reportes y analytics
- Integración con sistemas externos 