# Descripción General de la Plataforma

## 1. Visión General

Parking Altea es una plataforma integral de gestión de aparcamientos que incluye:

- **Gestión de ocupación** en tiempo real mediante cámaras de conteo
- **Paneles LED informativos** con diferentes protocolos de comunicación
- **Programaciones automáticas** de mensajes en paneles
- **API REST** para integración con sistemas externos
- **Dashboard web** para administración

## 2. Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│                          client/ - Puerto 15000 (Nginx)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API BACKEND (Flask)                                │
│                       src/api_server.py - Puerto 6001                        │
└─────────────────────────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   PostgreSQL │  │ Panel Worker │  │Camera Server │  │  Schedule    │
│   parking_db │  │  (Tipo 1,2)  │  │   Conteo     │  │   Monitor    │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  Protocolo Nuevo     │    │  Protocolo Antiguo   │
│  Puerto 7110         │    │  Puerto 8888         │
│  (Python directo)    │    │  (SDK Java)          │
└──────────────────────┘    └──────────────────────┘
           │                           │
           └─────────────┬─────────────┘
                         ▼
              ┌───────────────────────┐
              │   PANELES LED FÍSICOS │
              │     Puerto TCP 5200   │
              └───────────────────────┘
```

## 3. Componentes Principales

### 3.1 Backend API (Flask)
- **Ubicación**: `src/api_server.py`
- **Puerto**: 6001
- **Responsabilidades**:
  - API REST para frontend y sistemas externos
  - Gestión de parkings, paneles, usuarios
  - Endpoints de programaciones
  - Autenticación JWT

### 3.2 Sistema de Paneles LED

#### Protocolo Nuevo (Puerto 7110)
- **Servicio**: `parking-panel-protocol.service`
- **Ubicación**: `src/panel_protocol/`
- **Tecnología**: Python directo, generación de hexadecimal
- **Paneles**: Tipo 2, 3, 4 con `protocol_version = 'new'`

#### Protocolo Antiguo (Puerto 8888)
- **Servicio**: `panelsender.service`
- **Ubicación**: `/opt/panelSender/`
- **Tecnología**: Java SDK (`protocol.jar`)
- **Paneles**: Tipo 1 con `protocol_version = 'old'`

### 3.3 Workers de Actualización

#### Panel Worker (Tipo 1 y 2)
- **Servicio**: `panel_worker_service.py`
- **Intervalo**: 120 segundos
- **Responsabilidades**:
  - Verificar programaciones activas
  - Enviar estado de ocupación o mensaje programado
  - Actualizar estado de paneles en BD

#### Panel Type 3/4 Worker
- **Servicio**: `panel_type3_and_4_worker_service.py`
- **Intervalo**: 120 segundos
- **Responsabilidades**:
  - Actualizar paneles con múltiples ventanas
  - Gestionar rotación de contenido
  - Verificar programaciones activas

### 3.4 Sistema de Conteo (Cámaras)
- **Servicio**: `camera_server.py`
- **Puerto**: 3535
- **Responsabilidades**:
  - Recibir eventos de cámaras de conteo
  - Actualizar ocupación de parkings
  - Calcular estado (LIBRE, DENSO, COMPLETO)

### 3.5 Monitor de Programaciones
- **Servicio**: `schedule_monitor_service.py`
- **Intervalo**: 300 segundos (5 minutos)
- **Responsabilidades**:
  - Detectar programaciones que inician/finalizan
  - Ejecutar programaciones automáticamente
  - Restaurar estado normal al finalizar

## 4. Tipos de Paneles

| Tipo | Ventanas | Protocolo | Descripción |
|------|----------|-----------|-------------|
| Tipo 1 | 1 | Antiguo (8888) | Paneles básicos, SDK Java |
| Tipo 2 | 1 | Nuevo (7110) | Paneles nuevos, Python directo |
| Tipo 3 | 2 | Nuevo (7110) | Paneles con 2 ventanas (plazas + PMR) |
| Tipo 4 | 16 | Nuevo (7110) | Paneles grandes, múltiples zonas |

## 5. Flujo de Datos Principal

```
Cámara → Camera Server → BD (ocupación) → Panel Worker → Panel LED
                              ↓
                    Schedule Monitor
                              ↓
                    Programación activa?
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
     Sí: Enviar mensaje        No: Enviar estado
         programación              ocupación
```

## 6. Tecnologías Utilizadas

| Componente | Tecnología |
|------------|------------|
| Backend API | Python 3.10+, Flask |
| Frontend | React, Vite |
| Base de Datos | PostgreSQL 14+ |
| Servidor Web | Nginx, Gunicorn |
| Protocolo Paneles | TCP Socket, Hexadecimal |
| SDK Paneles (antiguo) | Java (protocol.jar) |
| Gestión Procesos | Systemd |
| Virtualización | Python venv |

## 7. Requisitos del Sistema

### Servidor de Producción
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 16 GB mínimo
- **CPU**: 4 cores mínimo
- **Disco**: 50 GB SSD
- **Red**: Acceso a red de paneles (172.20.x.x, 10.8.x.x)

### Software Requerido
- Python 3.10+
- PostgreSQL 14+
- Node.js 18+ (para frontend)
- Java 11+ (para SDK antiguo)
- Nginx
- Git

---

*Siguiente: [02-servicios-y-puertos.md](./02-servicios-y-puertos.md)*
