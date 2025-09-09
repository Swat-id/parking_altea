# Parking Altea - Versión 4.0.0

## Información General

La versión 4.0.0 del sistema de gestión de parking de Altea representa una evolución significativa del proyecto, introduciendo nuevas funcionalidades y mejoras arquitectónicas importantes.

## Fecha de Inicio
**Fecha de creación de la rama:** 9 de septiembre de 2025

## Estado del Desarrollo
🚧 **EN DESARROLLO** - Rama activa para nuevas funcionalidades

## Rama Base
- **Rama origen:** v3.5.0
- **Rama actual:** v4.0.0

## Objetivos de la Versión 4.0.0

### Nuevas Funcionalidades Planificadas
- [ ] Funcionalidades por definir según evolución del proyecto
- [ ] Mejoras arquitectónicas pendientes de especificar
- [ ] Optimizaciones de rendimiento
- [ ] Nuevas integraciones

### Mejoras Técnicas
- [ ] Actualización de dependencias
- [ ] Refactorización de código legacy
- [ ] Mejoras en la documentación
- [ ] Optimización de procesos de despliegue

## Estructura de Documentación v4.0.0

```
docs/v4.0.0/
├── README.md                    # Este archivo - Información general
├── funcionalidades_nuevas.md   # Documentación de nuevas funcionalidades
├── cambios_arquitectura.md     # Cambios en la arquitectura del sistema
├── guia_migracion.md           # Guía de migración desde v3.5.0
├── guia_despliegue_v4.0.0.md   # Instrucciones de despliegue específicas
├── tests_v4.0.0.md             # Documentación de testing para v4.0.0
└── notas_desarrollo.md         # Notas y decisiones técnicas del desarrollo
```

## Compatibilidad

### Versión Base
- **Sistema base:** v3.5.0
- **Base de datos:** Compatible con esquema v3.5.0
- **API:** Retrocompatible con endpoints v3.5.0

### Requisitos del Sistema
- **Node.js:** >= 18.0.0
- **Python:** >= 3.8
- **PostgreSQL:** >= 12.0
- **Sistema operativo:** Linux Ubuntu 20.04+ (servidor)

## Configuración del Entorno

### Frontend
- **Puerto:** 5789 (mantiene consistencia con versiones anteriores)
- **Framework:** React + Vite
- **Estilos:** Tailwind CSS

### Backend
- **API:** Python Flask
- **Base de datos:** PostgreSQL
- **Servicios:** Systemd services

## Notas de Desarrollo

### Convenciones de Commit
- `feat:` para nuevas funcionalidades
- `fix:` para correcciones de errores
- `docs:` para cambios en documentación
- `refactor:` para refactorizaciones
- `test:` para añadir o modificar tests
- `chore:` para tareas de mantenimiento

### Proceso de Desarrollo
1. Desarrollo en rama v4.0.0
2. Testing local completo
3. Actualización de documentación
4. Commit y push a repositorio
5. Despliegue controlado paso a paso

## Historial de Cambios

### [4.0.0] - En Desarrollo
- Creación de la rama v4.0.0
- Establecimiento de estructura de documentación
- Preparación para nuevas funcionalidades

## Enlaces Relacionados

- [Documentación v3.5.0](../v3.5.0/README.md)
- [Documentación General del Proyecto](../README.md)
- [Guías de Despliegue Anteriores](../deploy/)

## Contacto y Soporte

Para consultas específicas sobre la versión 4.0.0, consultar la documentación técnica correspondiente en este directorio.

---

**Última actualización:** 9 de septiembre de 2025  
**Estado:** Rama creada y estructura de documentación establecida
