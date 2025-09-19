# Roadmap de Implementación v4.1.0

## Resumen Ejecutivo

La versión 4.1.0 introduce tres mejoras principales al sistema de gestión de parking:

1. **Selección de ventanas para paneles Tipo 3** (10 horas)
2. **Sistema de gestión de plazas individuales PMR** (74 horas) 
3. **Servicio de push de sensores en puerto 3535** (37 horas)

**Estimación total**: 121 horas (~15 días de desarrollo)

### Nuevas Funcionalidades Añadidas

- **Actualización manual de estados**: Interfaz para cambiar manualmente el estado de cualquier plaza individual
- **Campo nombre para sensores**: Además del serial_number, cada sensor tendrá un nombre descriptivo
- **Integración en página de parking**: Sección específica mostrando sensores por tipo con información detallada
- **Procesamiento similar a cámaras**: El servicio push mantendrá actualizados tanto estados individuales como conteos agrupados

## Fases de Implementación

### FASE 1: Selección de Ventanas en Paneles Tipo 3
**Duración**: 2 días  
**Prioridad**: Media  
**Dependencias**: Ninguna

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Frontend - Modificar interfaz** | 4h | Frontend | Agregar selector de ventana en modal de mensaje |
| **Backend - Modificar API** | 3h | Backend | Actualizar endpoint de envío de mensajes |
| **Backend - Validaciones** | 2h | Backend | Validar ventana según tipo de panel |
| **Testing y validación** | 1h | QA | Pruebas con paneles reales |

#### Entregables
- [ ] Selector de ventana en interfaz de paneles
- [ ] API actualizada para soportar selección de ventana
- [ ] Validaciones de tipo de panel
- [ ] Tests unitarios y de integración

#### Criterios de Aceptación
- ✅ Usuario puede seleccionar ventana 0 o 1 para paneles Tipo 3
- ✅ Selector solo aparece para paneles con múltiples ventanas
- ✅ Paneles no Tipo 3 mantienen comportamiento actual
- ✅ Validación de ventana inválida funciona correctamente

---

### FASE 2: Base de Datos y Modelos para Sensores Individuales
**Duración**: 2 días  
**Prioridad**: Alta  
**Dependencias**: Ninguna

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Diseño de tablas** | 2h | Backend | Crear scripts SQL para nuevas tablas |
| **Modelos SQLAlchemy** | 4h | Backend | Implementar modelos en Python |
| **Scripts de migración** | 2h | Backend | Scripts para crear/migrar base de datos |
| **Testing de modelos** | 2h | Backend | Tests unitarios de modelos |
| **Validación en desarrollo** | 2h | Backend | Probar creación/consulta de datos |

#### Entregables
- [ ] Scripts SQL de creación de tablas
- [ ] Modelos Python para sensores individuales
- [ ] Scripts de migración de base de datos
- [ ] Tests de modelos y relaciones

#### Criterios de Aceptación
- ✅ Tablas creadas correctamente en base de datos
- ✅ Modelos Python funcionan con relaciones
- ✅ Migración desde versión anterior funciona
- ✅ Tests de modelos pasan exitosamente

---

### FASE 3: API y Servicios de Sensores Individuales
**Duración**: 3 días  
**Prioridad**: Alta  
**Dependencias**: Fase 2 completada

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Endpoints CRUD** | 8h | Backend | Crear, leer, actualizar, eliminar sensores |
| **Servicios de negocio** | 6h | Backend | Lógica de actualización de estados |
| **Endpoints de consulta** | 4h | Backend | Estados por parking, resúmenes |
| **Autenticación** | 3h | Backend | Validar permisos por usuario |
| **Testing de API** | 3h | Backend | Tests de endpoints y servicios |

#### Entregables
- [ ] Endpoints CRUD para sensores individuales
- [ ] Servicios de actualización de estados
- [ ] Endpoints de consulta y resúmenes
- [ ] Sistema de autenticación integrado

#### Criterios de Aceptación
- ✅ CRUD completo de sensores funciona
- ✅ Consultas por parking devuelven datos correctos
- ✅ Autenticación restringe acceso correctamente
- ✅ API responde en tiempo adecuado (<500ms)

---

### FASE 4: Servicio de Push de Sensores (Puerto 3535)
**Duración**: 5 días  
**Prioridad**: Alta  
**Dependencias**: Fase 2 y 3 completadas

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Servicio Flask base** | 6h | Backend | Servidor HTTP en puerto 3535 |
| **Procesamiento de push** | 8h | Backend | Lógica de procesamiento de mensajes |
| **Actualización manual estados** | 4h | Backend | Endpoint y lógica para cambios manuales |
| **Middleware y seguridad** | 4h | Backend | Validaciones, logging, seguridad |
| **Métricas y monitorización** | 4h | Backend | Estadísticas, health checks |
| **Scripts de despliegue** | 3h | DevOps | Systemd, firewall, automatización |
| **Testing completo** | 6h | QA | Tests unitarios, integración, manuales |
| **Documentación API** | 2h | Docs | Documentar protocolo y endpoints |

#### Entregables
- [ ] Servicio Flask funcionando en puerto 3535
- [ ] Procesamiento completo de mensajes push
- [ ] Sistema de métricas y monitorización
- [ ] Scripts de despliegue automatizado
- [ ] Suite completa de tests

#### Criterios de Aceptación
- ✅ Servicio recibe y procesa push correctamente
- ✅ Estados de sensores se actualizan en tiempo real
- ✅ Resúmenes por parking se calculan automáticamente
- ✅ Actualización manual de estados funciona correctamente
- ✅ Servicio es resiliente a fallos y se reinicia automáticamente

---

### FASE 5: Frontend de Gestión de Sensores Individuales
**Duración**: 3 días  
**Prioridad**: Media  
**Dependencias**: Fase 3 completada

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Componente principal** | 6h | Frontend | Página de gestión de sensores |
| **Formularios CRUD** | 4h | Frontend | Crear, editar, eliminar sensores |
| **Dashboard de estados** | 6h | Frontend | Visualización de estados en tiempo real |
| **Filtros y búsquedas** | 3h | Frontend | Filtrar por tipo, parking, estado |
| **Integración con API** | 3h | Frontend | Conectar con endpoints backend |

#### Entregables
- [ ] Página completa de gestión de sensores
- [ ] Formularios de creación y edición
- [ ] Dashboard de estados en tiempo real
- [ ] Sistema de filtros y búsquedas

#### Criterios de Aceptación
- ✅ Usuario puede gestionar sensores completamente
- ✅ Estados se muestran en tiempo real
- ✅ Filtros funcionan correctamente
- ✅ Interfaz es intuitiva y responsiva

---

### FASE 6: Integración con Página de Detalle de Parking
**Duración**: 2 días  
**Prioridad**: Media  
**Dependencias**: Fase 4 y 5 completadas

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Backend - Endpoints parking** | 4h | Backend | APIs para obtener sensores por parking |
| **Frontend - Sección sensores** | 4h | Frontend | Componente para mostrar sensores por tipo |
| **Frontend - Modal actualización** | 2h | Frontend | Interfaz para actualización manual |
| **Integración tiempo real** | 2h | Frontend | Auto-refresh y estados dinámicos |

#### Entregables
- [ ] Endpoints para consultar sensores por parking
- [ ] Sección de sensores individuales en página de parking
- [ ] Modal de actualización manual de estados
- [ ] Visualización por bloques de tipo con resúmenes

#### Criterios de Aceptación
- ✅ Sensores se muestran agrupados por tipo en página de parking
- ✅ Información de estado, batería y timestamp visible
- ✅ Actualización manual funciona desde la interfaz
- ✅ Datos se actualizan automáticamente cada 30 segundos

---

### FASE 7: Dashboard de Estados y Estadísticas
**Duración**: 2 días  
**Prioridad**: Baja  
**Dependencias**: Fase 6 completada

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Gráficos de ocupación** | 4h | Frontend | Visualización gráfica de estados |
| **Estadísticas históricas** | 3h | Frontend | Evolución temporal de sensores |
| **Alertas visuales** | 2h | Frontend | Indicadores de sensores con problemas |
| **Reportes básicos** | 3h | Frontend | Generación de reportes simples |

#### Entregables
- [ ] Gráficos de ocupación por tipo y parking
- [ ] Estadísticas históricas visuales
- [ ] Sistema de alertas visuales
- [ ] Reportes básicos descargables

#### Criterios de Aceptación
- ✅ Gráficos muestran datos actualizados
- ✅ Estadísticas históricas son precisas
- ✅ Alertas aparecen para sensores problemáticos
- ✅ Reportes se pueden descargar correctamente

---

### FASE 8: Testing, Optimización y Documentación
**Duración**: 1 día  
**Prioridad**: Alta  
**Dependencias**: Todas las fases anteriores

#### Tareas Específicas

| Tarea | Estimación | Responsable | Descripción |
|-------|------------|-------------|-------------|
| **Testing de integración** | 3h | QA | Tests completos del sistema |
| **Optimizaciones** | 2h | Backend | Mejoras de rendimiento |
| **Documentación final** | 2h | Docs | Guías de usuario y técnicas |
| **Preparación despliegue** | 1h | DevOps | Scripts finales de despliegue |

#### Entregables
- [ ] Suite completa de tests de integración
- [ ] Optimizaciones de rendimiento aplicadas
- [ ] Documentación completa del sistema
- [ ] Scripts de despliegue validados

#### Criterios de Aceptación
- ✅ Todos los tests pasan exitosamente
- ✅ Sistema responde en tiempos aceptables
- ✅ Documentación está completa y actualizada
- ✅ Despliegue se puede hacer automáticamente

---

## Cronograma Detallado

### Semana 1 (5 días)
- **Días 1-2**: Fase 1 - Selección de ventanas paneles
- **Días 3-4**: Fase 2 - Base de datos y modelos
- **Día 5**: Inicio Fase 3 - API básica

### Semana 2 (5 días)
- **Días 1-2**: Continuación Fase 3 - API completa
- **Días 3-5**: Fase 4 - Servicio push (días 1-3)

### Semana 3 (5 días)
- **Días 1-2**: Finalización Fase 4 - Servicio push
- **Días 3-4**: Fase 5 - Frontend gestión sensores
- **Día 5**: Fase 6 - Integración página parking (día 1)

### Día Final
- **Día 1**: Finalización Fase 6, Fases 7 y 8 - Dashboard, testing y finalización

## Recursos Necesarios

### Equipo de Desarrollo
- **1 Desarrollador Backend** (Python/Flask/SQLAlchemy)
- **1 Desarrollador Frontend** (React/JavaScript)
- **1 DevOps/QA** (Testing, despliegue)

### Infraestructura
- **Servidor de desarrollo** para pruebas
- **Base de datos PostgreSQL** con permisos de creación de tablas
- **Acceso al servidor de producción** (157.180.91.63)
- **Sensores Fleximodo de prueba** (opcional pero recomendado)

### Herramientas
- **Git** para control de versiones
- **Postman/curl** para testing de API
- **pgAdmin** para gestión de base de datos
- **Systemd** para gestión de servicios

## Riesgos y Mitigaciones

### Riesgo Alto
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Problemas de conectividad con sensores** | Media | Alto | Implementar simuladores, testing sin sensores reales |
| **Rendimiento de base de datos** | Media | Alto | Optimizar consultas, implementar índices |
| **Compatibilidad con sistema existente** | Baja | Alto | Tests de regresión exhaustivos |

### Riesgo Medio
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Retrasos en desarrollo frontend** | Media | Medio | Priorizar funcionalidad básica |
| **Problemas de despliegue** | Media | Medio | Scripts automatizados, rollback |
| **Validación de usuarios** | Media | Medio | Feedback temprano, iteraciones |

### Riesgo Bajo
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Cambios en especificaciones** | Baja | Medio | Documentación clara, comunicación |
| **Problemas de integración** | Baja | Medio | Testing continuo |

## Criterios de Éxito

### Funcionales
- ✅ Selección de ventanas funciona en paneles Tipo 3
- ✅ Sensores individuales se pueden gestionar completamente
- ✅ Push de sensores se procesa correctamente
- ✅ Estados se actualizan en tiempo real (automático y manual)
- ✅ Resúmenes por parking son precisos
- ✅ Página de parking muestra sensores por tipo con detalles
- ✅ Actualización manual de estados funciona desde interfaz
- ✅ Campo nombre permite identificación fácil de plazas
- ✅ Autenticación funciona correctamente

### No Funcionales
- ✅ API responde en < 500ms para consultas normales
- ✅ Servicio push procesa mensajes en < 100ms
- ✅ Sistema soporta al menos 100 sensores simultáneos
- ✅ Interfaz es responsiva y usable
- ✅ Documentación está completa
- ✅ Tests tienen cobertura > 80%

### Operacionales
- ✅ Despliegue se realiza sin downtime
- ✅ Sistema es monitorizable
- ✅ Logs son informativos y útiles
- ✅ Rollback es posible si hay problemas
- ✅ Backup de datos funciona correctamente

## Plan de Despliegue

### Pre-despliegue
1. **Backup completo** de base de datos y código
2. **Validación en entorno de desarrollo**
3. **Tests de regresión** completos
4. **Revisión de código** por pares

### Despliegue
1. **Modo mantenimiento** (opcional)
2. **Migración de base de datos**
3. **Despliegue de código backend**
4. **Despliegue de frontend**
5. **Inicio de servicio push**
6. **Validación post-despliegue**

### Post-despliegue
1. **Monitorización activa** durante 24h
2. **Validación con usuarios**
3. **Ajustes menores** si es necesario
4. **Documentación de incidencias**

## Comandos de Despliegue

### Preparación
```bash
# Crear backup
./scripts/backup_database.sh
./scripts/backup_code.sh

# Validar entorno
./scripts/validate_environment.sh
```

### Migración de Base de Datos
```bash
# Crear tablas de sensores individuales
python scripts/migrate_to_individual_sensors.py

# Validar migración
python scripts/validate_migration.py
```

### Despliegue de Servicios
```bash
# Backend y API
./deploy/update_backend_v4.1.0.sh

# Frontend
./deploy/update_frontend_v4.1.0.sh

# Servicio push
./deploy/deploy_sensor_push_service.sh
```

### Validación
```bash
# Tests de sistema
./tests/run_system_tests_v4.1.0.sh

# Validación manual
./tests/manual_validation_v4.1.0.sh
```

## Métricas de Seguimiento

### Durante Desarrollo
- **Velocity**: Puntos de historia completados por sprint
- **Burn-down**: Progreso hacia objetivos de fase
- **Code coverage**: Porcentaje de código cubierto por tests
- **Bugs encontrados**: Número y severidad de bugs

### Post-despliegue
- **Tiempo de respuesta API**: < 500ms promedio
- **Disponibilidad servicio push**: > 99.5%
- **Mensajes procesados**: Número de push recibidos/procesados
- **Errores de sistema**: Número y tipo de errores
- **Satisfacción usuario**: Feedback cualitativo

## Documentación Entregable

### Técnica
- [x] [Análisis de selección de ventanas](./analisis_seleccion_ventanas_paneles.md)
- [x] [Análisis de sistema de plazas individuales](./analisis_sistema_plazas_individuales.md)
- [x] [Análisis de servicio push](./analisis_servicio_push_sensores.md)
- [ ] [Comandos de despliegue](./comandos_despliegue_v4.1.0.md)
- [ ] [Guía de testing](./guia_testing_v4.1.0.md)

### Usuario
- [ ] Manual de usuario - Gestión de sensores
- [ ] Manual de usuario - Dashboard de estados
- [ ] FAQ y troubleshooting
- [ ] Video tutoriales (opcional)

## Próximos Pasos

### Inmediatos (Esta semana)
1. **Validar roadmap** con stakeholders
2. **Preparar entorno de desarrollo**
3. **Iniciar Fase 1** - Selección de ventanas

### Corto plazo (Próximas 2 semanas)
1. **Implementar fases 2-4** según cronograma
2. **Testing continuo** de cada fase
3. **Feedback temprano** de usuarios

### Medio plazo (Próximo mes)
1. **Completar implementación**
2. **Despliegue en producción**
3. **Monitorización y ajustes**
4. **Planificación v4.2.0**

---

*Roadmap de implementación v4.1.0 - Sistema de Gestión de Parking*  
*Última actualización: 19/09/2025*
