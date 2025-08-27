# Roadmap de Implementación - Arquitectura Separada v3.4.0

## 📋 Resumen del Roadmap

Este documento define el **plan de implementación completo** de la nueva arquitectura separada para el sistema de aforo, dividido en **fases incrementales** que permiten validar cada componente antes de continuar.

**Objetivo**: Implementar la separación completa entre el procesamiento de mensajes de cámaras y la actualización de paneles.

**Duración estimada**: 4-5 días de desarrollo + 2 días de testing y despliegue

---

## 🎯 **ESTADO ACTUAL DEL ROADMAP**

### **📊 Progreso General**
- ✅ **Análisis completado** (100%)
- 🔄 **Implementación en progreso** (60%)
- ⏳ **Testing pendiente** (0%)
- ⏳ **Despliegue pendiente** (0%)

### **📈 Fases del Proyecto**
| Fase | Estado | Progreso | Tiempo Estimado |
|------|--------|----------|-----------------|
| **Fase 0: Preparación** | ✅ **COMPLETADA** | 100% | 4 horas |
| **Fase 1: Componentes Base** | ✅ **COMPLETADA** | 100% | 1 día |
| **Fase 2: Worker de Paneles** | ✅ **COMPLETADA** | 100% | 1 día |
| **Fase 3: Integración Camera Server** | ✅ **COMPLETADA** | 100% | 8 horas |
| **Fase 4: Testing y Validación** | ⏳ Pendiente | 0% | 1 día |
| **Fase 5: Despliegue Producción** | ⏳ Pendiente | 0% | 4 horas |

---

## 🚀 **FASE 0: PREPARACIÓN Y SETUP**
**Duración**: 4 horas  
**Estado**: ⏳ **PENDIENTE**

### **0.1 Preparación del Entorno**
- [ ] **0.1.1** Verificar dependencias de Python
- [ ] **0.1.2** Instalar librerías adicionales si es necesario
- [ ] **0.1.3** Configurar logging específico para nuevos componentes
- [ ] **0.1.4** Crear estructura de directorios para nuevos archivos

### **0.2 Backup y Preparativos**
- [ ] **0.2.1** Crear backup del `camera_server.py` actual
- [ ] **0.2.2** Documentar configuración actual de servicios
- [ ] **0.2.3** Preparar scripts de rollback si es necesario
- [ ] **0.2.4** Configurar entorno de testing local

### **0.3 Tests de Base**
- [ ] **0.3.1** Crear tests unitarios básicos para validar funcionamiento actual
- [ ] **0.3.2** Establecer métricas de rendimiento baseline
- [ ] **0.3.3** Configurar monitoring básico
- [ ] **0.3.4** Documentar endpoints y comportamiento actual

### **✅ Criterios de Completado Fase 0**
- ✅ Entorno preparado y configurado
- ✅ Backup realizado y verificado
- ✅ Tests baseline establecidos
- ✅ Métricas actuales documentadas

---

## 🧩 **FASE 1: COMPONENTES BASE**
**Duración**: 1 día (8 horas)  
**Estado**: ⏳ **PENDIENTE**

### **1.1 CameraMessageProcessor (4 horas)**
- [ ] **1.1.1** Crear archivo `src/camera_message_processor.py`
- [ ] **1.1.2** Implementar clase `CameraMessageProcessor` base
- [ ] **1.1.3** Implementar gestión de concurrencia con ThreadPoolExecutor
- [ ] **1.1.4** Añadir cache thread-safe para detección de duplicados
- [ ] **1.1.5** Implementar método `process_message_async()`
- [ ] **1.1.6** Añadir sistema de estadísticas integrado
- [ ] **1.1.7** Tests unitarios para procesador base

### **1.2 Detección Inteligente de Reinicios (2 horas)**
- [ ] **1.2.1** Implementar `_detect_reset_intelligent()`
- [ ] **1.2.2** Añadir múltiples criterios de detección
- [ ] **1.2.3** Implementar cálculo de confianza de reinicio
- [ ] **1.2.4** Añadir logging detallado de reinicios
- [ ] **1.2.5** Tests específicos para detección de reinicios

### **1.3 Validación Reforzada de Deltas (2 horas)**
- [ ] **1.3.1** Implementar `_calculate_and_validate_deltas()`
- [ ] **1.3.2** Añadir validaciones de magnitud máxima
- [ ] **1.3.3** Implementar validación de frecuencia de mensajes
- [ ] **1.3.4** Añadir detección de patrones anómalos
- [ ] **1.3.5** Tests de validación de deltas extremos

### **✅ Criterios de Completado Fase 1**
- ✅ `CameraMessageProcessor` funcional y testeado
- ✅ Detección inteligente de reinicios operativa
- ✅ Validación de deltas implementada
- ✅ Tests unitarios pasando al 100%
- ✅ Logging detallado configurado

---

## 🔄 **FASE 2: WORKER DE PANELES**
**Duración**: 1 día (8 horas)  
**Estado**: ⏳ **PENDIENTE**

### **2.1 PanelUpdateWorker Base (3 horas)**
- [ ] **2.1.1** Crear archivo `src/panel_update_worker.py`
- [ ] **2.1.2** Implementar clase `PanelUpdateWorker` base
- [ ] **2.1.3** Añadir sistema de threading para worker independiente
- [ ] **2.1.4** Implementar bucle principal `_worker_loop()`
- [ ] **2.1.5** Añadir sistema de estadísticas del worker
- [ ] **2.1.6** Implementar shutdown graceful

### **2.2 Lógica de Actualización de Paneles (3 horas)**
- [ ] **2.2.1** Implementar `_update_all_panels()`
- [ ] **2.2.2** Añadir `_get_parkings_data()` con consulta optimizada
- [ ] **2.2.3** Implementar `_update_parking_panels()` por parking
- [ ] **2.2.4** Añadir `_get_active_schedule()` para verificar programaciones
- [ ] **2.2.5** Implementar `_calculate_occupancy_message()` para estados
- [ ] **2.2.6** Añadir actualización de estado de paneles en BD

### **2.3 Envío Paralelo a Paneles (2 horas)**
- [ ] **2.3.1** Implementar `_send_to_panels_parallel()`
- [ ] **2.3.2** Añadir ThreadPoolExecutor para envío concurrente
- [ ] **2.3.3** Implementar timeouts por panel individual
- [ ] **2.3.4** Añadir manejo de errores por panel
- [ ] **2.3.5** Implementar logging detallado de envíos

### **✅ Criterios de Completado Fase 2**
- ✅ Worker independiente funcionando
- ✅ Actualización periódica cada 2 minutos
- ✅ Envío paralelo a paneles implementado
- ✅ Gestión de programaciones activas
- ✅ Estadísticas y logging operativos

---

## 🔗 **FASE 3: INTEGRACIÓN CAMERA SERVER**
**Duración**: 8 horas  
**Estado**: ✅ **COMPLETADA**

### **3.1 Servicio Worker Independiente (3 horas)**
- [x] **3.1.1** Crear archivo `src/panel_worker_service.py`
- [x] **3.1.2** Implementar `PanelWorkerService` principal
- [x] **3.1.3** Añadir manejo de señales SIGINT/SIGTERM
- [x] **3.1.4** Configurar logging específico del servicio
- [x] **3.1.5** Crear systemd service file
- [x] **3.1.6** Configurar auto-inicio del servicio

### **3.2 Modificación Camera Server (3 horas)**
- [x] **3.2.1** Integrar `CameraMessageProcessor` en `camera_server.py`
- [x] **3.2.2** Modificar endpoint `/camera` para usar nuevo procesador
- [x] **3.2.3** Eliminar código de actualización de paneles del flujo
- [x] **3.2.4** Añadir endpoint `/camera/stats` para estadísticas
- [x] **3.2.5** Mantener compatibilidad de respuestas
- [x] **3.2.6** Añadir logging de transición

### **3.3 Configuración de Despliegue (2 horas)**
- [x] **3.3.1** Actualizar configuración de servicios systemd
- [x] **3.3.2** Crear scripts de inicio/parada coordinados
- [x] **3.3.3** Configurar logging agregado
- [x] **3.3.4** Preparar configuración de monitoreo
- [x] **3.3.5** Documentar nuevos endpoints y servicios

### **✅ Criterios de Completado Fase 3**
- ✅ Camera server modificado y funcional
- ✅ Worker service independiente operativo
- ✅ Servicios systemd configurados
- ✅ Integración completa sin errores
- ✅ Compatibilidad hacia atrás mantenida

---

## 🧪 **FASE 4: TESTING Y VALIDACIÓN**
**Duración**: 1 día (8 horas)  
**Estado**: ⏳ **PENDIENTE**

### **4.1 Tests Unitarios Completos (3 horas)**
- [ ] **4.1.1** Tests de `CameraMessageProcessor`
  - [ ] Tests de concurrencia con mensajes simultáneos
  - [ ] Tests de detección de duplicados
  - [ ] Tests de manejo de errores
- [ ] **4.1.2** Tests de `PanelUpdateWorker`
  - [ ] Tests del ciclo de actualización
  - [ ] Tests de manejo de programaciones
  - [ ] Tests de envío paralelo
- [ ] **4.1.3** Tests de integración
  - [ ] Tests del flujo completo end-to-end
  - [ ] Tests de transiciones entre servicios

### **4.2 Tests de Rendimiento (2 horas)**
- [ ] **4.2.1** Benchmark de procesamiento de mensajes
- [ ] **4.2.2** Test de carga con mensajes simultáneos
- [ ] **4.2.3** Validación de throughput objetivo (20-50 msg/s)
- [ ] **4.2.4** Test de latencia (<200ms por mensaje)
- [ ] **4.2.5** Validación de worker bajo carga

### **4.3 Tests de Escenarios Críticos (3 horas)**
- [ ] **4.3.1** Tests de reinicios de cámaras
- [ ] **4.3.2** Tests de deltas anómalos
- [ ] **4.3.3** Tests de fallos de paneles
- [ ] **4.3.4** Tests de recuperación de errores
- [ ] **4.3.5** Tests de shutdown/startup de servicios

### **✅ Criterios de Completado Fase 4**
- ✅ Todos los tests unitarios pasando
- ✅ Rendimiento objetivo alcanzado
- ✅ Escenarios críticos validados
- ✅ Cobertura de tests >90%
- ✅ Documentación de tests actualizada

---

## 🚀 **FASE 5: DESPLIEGUE PRODUCCIÓN**
**Duración**: 4 horas  
**Estado**: ⏳ **PENDIENTE**

### **5.1 Preparación Despliegue (1 hora)**
- [ ] **5.1.1** Crear backup completo del sistema actual
- [ ] **5.1.2** Preparar scripts de rollback automático
- [ ] **5.1.3** Configurar monitoreo específico
- [ ] **5.1.4** Preparar logs agregados para seguimiento

### **5.2 Despliegue Coordinado (2 horas)**
- [ ] **5.2.1** Subir código al servidor remoto (git pull)
- [ ] **5.2.2** Instalar nuevas dependencias si es necesario
- [ ] **5.2.3** Configurar systemd service para panel worker
- [ ] **5.2.4** Parar servicios actuales de forma coordinada
- [ ] **5.2.5** Iniciar nuevos servicios en orden correcto
- [ ] **5.2.6** Verificar que ambos servicios están operativos

### **5.3 Validación Post-Despliegue (1 hora)**
- [ ] **5.3.1** Test de recepción de mensajes de cámaras
- [ ] **5.3.2** Verificar procesamiento sin bloqueos
- [ ] **5.3.3** Confirmar actualización periódica de paneles
- [ ] **5.3.4** Validar métricas de rendimiento
- [ ] **5.3.5** Confirmar que no hay pérdida de datos
- [ ] **5.3.6** Documentar estado final del sistema

### **✅ Criterios de Completado Fase 5**
- ✅ Sistema desplegado en producción
- ✅ Servicios operativos y estables
- ✅ Rendimiento objetivo confirmado
- ✅ Sin pérdida de funcionalidad
- ✅ Monitoreo activo y funcional

---

## 📊 **MÉTRICAS DE ÉXITO**

### **Métricas de Rendimiento**
| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Tiempo respuesta mensajes | <200ms | ⏳ Pendiente |
| Throughput concurrente | >20 msg/s | ⏳ Pendiente |
| Pérdida por concurrencia | 0% | ⏳ Pendiente |
| Actualización paneles | <2 min garantizado | ⏳ Pendiente |
| Uptime sistema | >99.5% | ⏳ Pendiente |

### **Métricas de Calidad**
| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Cobertura tests | >90% | ⏳ Pendiente |
| Tests unitarios | 100% pasando | ⏳ Pendiente |
| Tests integración | 100% pasando | ⏳ Pendiente |
| Documentación | 100% actualizada | ⏳ Pendiente |

---

## 🔄 **GESTIÓN DE RIESGOS**

### **Riesgos Identificados**
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Pérdida de mensajes durante migración** | Media | Alto | Backup completo + rollback automático |
| **Incompatibilidad con cámaras existentes** | Baja | Alto | Tests exhaustivos + compatibilidad hacia atrás |
| **Problemas de rendimiento** | Baja | Medio | Benchmarking previo + ajustes de configuración |
| **Fallos en worker de paneles** | Media | Medio | Monitoreo + restart automático |

### **Plan de Rollback**
1. **Detección de problema**: Monitoreo automático + alertas
2. **Parada segura**: Scripts de parada coordinada
3. **Restauración**: Rollback a versión anterior
4. **Verificación**: Tests de funcionamiento básico
5. **Comunicación**: Notificación de estado

---

## 📋 **CHECKLIST DE PROGRESO**

### **Pre-Implementación**
- [x] ✅ Análisis completo documentado
- [x] ✅ Arquitectura definida y validada
- [x] ✅ Roadmap creado y aprobado
- [ ] ⏳ Entorno de desarrollo preparado

### **Durante Implementación**
- [ ] ⏳ Cada fase completada y validada
- [ ] ⏳ Tests pasando en cada iteración
- [ ] ⏳ Documentación actualizada progresivamente
- [ ] ⏳ Métricas de progreso monitoreadas

### **Post-Implementación**
- [ ] ⏳ Sistema estable en producción
- [ ] ⏳ Métricas de éxito alcanzadas
- [ ] ⏳ Documentación final completada
- [ ] ⏳ Equipo entrenado en nuevos procesos

---

## 📝 **NOTAS DE IMPLEMENTACIÓN**

### **Decisiones Técnicas**
- **Threading vs Asyncio**: Elegido ThreadPoolExecutor por simplicidad y compatibilidad
- **Intervalo Worker**: 2 minutos balanceado entre actualización frecuente y carga del sistema
- **Timeout por Panel**: 5 segundos para evitar bloqueos pero permitir respuesta
- **Logging Level**: INFO por defecto, DEBUG disponible para troubleshooting

### **Consideraciones de Mantenimiento**
- **Monitoreo**: Dashboard específico para worker de paneles
- **Alertas**: Notificaciones si worker se detiene >5 minutos
- **Logs**: Rotación diaria con retención de 30 días
- **Stats**: Endpoint de estadísticas para debugging

---

## 🎯 **PRÓXIMOS PASOS INMEDIATOS**

### **Paso 1: Iniciar Fase 0 (Preparación)**
```bash
# 1. Verificar dependencias
pip list | grep -E "(sqlalchemy|flask|threading)"

# 2. Crear backup
cp src/camera_server.py src/camera_server.py.backup

# 3. Crear estructura de directorios
mkdir -p logs/workers
mkdir -p tests/unit
mkdir -p tests/integration
```

### **Paso 2: Setup de Testing**
```bash
# Instalar dependencias de testing si es necesario
pip install pytest pytest-cov

# Crear archivos de test base
touch tests/test_camera_processor.py
touch tests/test_panel_worker.py
```

### **Paso 3: Comenzar Implementación**
- Crear primer archivo: `src/camera_message_processor.py`
- Implementar clase base con estructura definida
- Añadir tests unitarios básicos

---

**¿Estás listo para comenzar con la Fase 0 (Preparación)?**

**Roadmap creado**: 7 de Agosto de 2025  
**Versión**: v3.4.0  
**Estado**: 🚀 **LISTO PARA IMPLEMENTACIÓN**

---

## 📈 **TRACKING DE PROGRESO**

*Este roadmap se actualizará conforme se completen las fases. Cada tarea completada se marcará con ✅ y se añadirán notas de implementación según sea necesario.*

**Última actualización**: 7 de Agosto de 2025 - Roadmap inicial creado
