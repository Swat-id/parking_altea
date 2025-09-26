# Actualización de Servicios Frontend v4.2.0: Control de Permisos

## Resumen de Cambios

Todos los servicios del frontend han sido actualizados para respetar automáticamente los permisos del usuario, asegurando que:

- **Superadmin**: Ve todos los datos sin filtros
- **Usuario regular**: Solo ve datos de recursos asignados
- **Manejo de errores**: Respuestas 403 se manejan elegantemente
- **Compatibilidad**: Todos los métodos existentes mantienen su interfaz

## Servicios Actualizados

### 1. `parkingService.js` - COMPLETAMENTE RENOVADO

#### **Métodos Mejorados:**
- `getParkings()` - Ahora filtra automáticamente por permisos
- `getParking(id)` - Verifica acceso antes de mostrar
- `getParkingStatistics(id)` - Solo si tiene permisos al parking

#### **Nuevos Métodos v4.2.0:**
```javascript
// Obtener parkings del usuario
await parkingService.getUserParkings()

// Resumen de sensores de un parking
await parkingService.getParkingSensorsSummary(parkingId)

// Sensores detallados de un parking
await parkingService.getParkingSensorsDetailed(parkingId, filters)

// Utilidades
await parkingService.utils.hasAccessToParking(parkingId)
await parkingService.utils.getParkingsWithSensors()
```

### 2. `panelService.js` - COMPLETAMENTE RENOVADO

#### **Métodos Mejorados:**
- `getAllPanels()` - Filtra por paneles accesibles
- `getParkingPanels(parkingId)` - Solo si tiene acceso al parking
- `getPanelLogs(panelId)` - Solo si tiene acceso al panel

#### **Nuevos Métodos v4.2.0:**
```javascript
// Paneles agrupados por parking
await panelService.getUserPanelsGrouped()

// Estadísticas de paneles
await panelService.utils.getPanelsStatistics()

// Verificar acceso
await panelService.utils.hasAccessToPanel(panelId)
```

### 3. `sensorService.js` - MEJORADO CON NUEVOS ENDPOINTS

#### **Métodos Existentes Mejorados:**
- `getAllSensors()` - Filtra automáticamente por parkings accesibles
- `getGroupedStatus()` - Respeta permisos del usuario

#### **Nuevos Métodos v4.2.0:**
```javascript
// Resumen personalizado del usuario
await sensorService.getUserSensorsSummary()

// Sensores por tipo específico
await sensorService.getSensorsByType('PMR')

// Dashboard personalizado
await sensorService.getUserDashboard()

// Resumen de parking específico
await sensorService.getParkingSummary(parkingId)
```

### 4. `statisticsService.js` - COMPLETAMENTE RENOVADO

#### **Métodos Mejorados:**
- `getAllStatistics()` - Filtra por parkings accesibles
- `getActivityLogs()` - Solo logs de recursos accesibles
- `getPanelLogs()` - Solo paneles accesibles

#### **Nuevos Métodos v4.2.0:**
```javascript
// Dashboard del usuario
await statisticsService.getUserDashboardStats()

// Resumen de ocupación del usuario
await statisticsService.getUserOccupancySummary(days)

// Estadísticas de sensores del usuario
await statisticsService.getUserSensorStats()

// Comparación entre parkings del usuario
await statisticsService.getUserParkingsComparison(days)
```

#### **Utilidades Agregadas:**
```javascript
// Procesar datos para gráficos
statisticsService.utils.processOccupancyData(data)

// Calcular métricas de resumen
statisticsService.utils.calculateSummaryMetrics(data)

// Formatear para exportación
statisticsService.utils.formatForExport(data, 'csv')
```

### 5. `logService.js` - NUEVO SERVICIO COMPLETO

#### **Servicios de Logs con Permisos:**
```javascript
// Logs de actividad filtrados
await logService.getActivityLogs(params)

// Logs de paneles accesibles
await logService.getPanelLogs(params)

// Logs de cámaras accesibles
await logService.getCameraLogs(params)

// Logs de sensores accesibles
await logService.getSensorLogs(params)

// Logs del usuario
await logService.getUserLogs(params)

// Dashboard de logs del usuario
await logService.getUserDashboardLogs(limit)
```

#### **Utilidades de Logs:**
```javascript
// Agrupar por fecha
logService.utils.groupByDate(logs)

// Estadísticas de logs
logService.utils.getLogsStatistics(logs)

// Exportar a CSV
logService.utils.exportToCSV(logs)
```

### 6. `sensorGroupService.js` - NUEVO SERVICIO ESPECIALIZADO

#### **Endpoints Agrupados:**
```javascript
// Resumen de parking específico
await sensorGroupService.getParkingSummary(parkingId)

// Resumen del usuario
await sensorGroupService.getUserSummary()

// Por tipo de sensor
await sensorGroupService.getSensorTypeSummary(sensorType)

// Dashboard personalizado
await sensorGroupService.getUserDashboard()
```

#### **Utilidades de Agrupación:**
```javascript
// Calcular métricas globales
sensorGroupService.utils.calculateGlobalMetrics(parkingsData)

// Agrupar por tipo de sensor
sensorGroupService.utils.groupBySensorType(parkingsData)

// Filtrar alertas por severidad
sensorGroupService.utils.filterAlertsBySeverity(alerts, 'high')
```

## Manejo de Errores y Permisos

### **Patrón Común Implementado:**
```javascript
try {
  const response = await api.get('/api/endpoint')
  return response.data
} catch (error) {
  if (error.response?.status === 403) {
    console.warn('Sin permisos para este recurso')
    return null // o array vacío
  }
  console.error('Error:', error)
  throw error
}
```

### **Interceptor de API Mejorado:**
- Manejo automático de errores 401 (token expirado)
- Manejo elegante de errores 403 (sin permisos)
- Redirección automática a login cuando es necesario

## Compatibilidad y Migración

### **Compatibilidad Hacia Atrás:**
- ✅ Todos los métodos existentes mantienen su interfaz
- ✅ Los componentes existentes siguen funcionando
- ✅ Solo se agregaron funcionalidades, no se rompió nada

### **Migración Recomendada:**

#### **Para Componentes de Parkings:**
```javascript
// ANTES
const parkings = await parkingService.getAllParkings()

// AHORA (igual interfaz, pero con filtrado automático)
const parkings = await parkingService.getAllParkings()

// NUEVO (más específico para el usuario)
const userParkings = await parkingService.getUserParkings()
```

#### **Para Componentes de Estadísticas:**
```javascript
// ANTES
const stats = await statisticsService.getAllStatistics()

// AHORA (filtrado automático)
const stats = await statisticsService.getAllStatistics()

// NUEVO (dashboard personalizado)
const dashboard = await statisticsService.getUserDashboardStats()
```

#### **Para Componentes de Sensores:**
```javascript
// ANTES
const sensors = await sensorService.getAllSensors()

// AHORA (filtrado automático)
const sensors = await sensorService.getAllSensors()

// NUEVO (resumen del usuario)
const summary = await sensorService.getUserSensorsSummary()
```

## Ejemplos de Uso en Componentes

### **Dashboard Principal:**
```javascript
import { statisticsService } from '../services/statisticsService'
import { sensorGroupService } from '../services/sensorGroupService'

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null)
  
  useEffect(() => {
    const loadData = async () => {
      // Datos automáticamente filtrados por usuario
      const [stats, sensors] = await Promise.all([
        statisticsService.getUserDashboardStats(),
        sensorGroupService.getUserSummary()
      ])
      
      setDashboardData({ stats, sensors })
    }
    
    loadData()
  }, [])
  
  // El usuario solo ve sus datos, superadmin ve todo
}
```

### **Lista de Parkings:**
```javascript
import parkingService from '../services/parkingService'

const ParkingsList = () => {
  const [parkings, setParkings] = useState([])
  
  useEffect(() => {
    const loadParkings = async () => {
      // Automáticamente filtrado por permisos
      const data = await parkingService.getParkings()
      setParkings(data)
    }
    
    loadParkings()
  }, [])
  
  // Solo muestra parkings accesibles al usuario
}
```

### **Logs de Actividad:**
```javascript
import { logService } from '../services/logService'

const ActivityLogs = () => {
  const [logs, setLogs] = useState([])
  
  useEffect(() => {
    const loadLogs = async () => {
      // Solo logs de recursos accesibles
      const data = await logService.getActivityLogs({
        limit: 100,
        startDate: '2025-09-01'
      })
      setLogs(data)
    }
    
    loadLogs()
  }, [])
  
  // Solo muestra logs de parkings/paneles del usuario
}
```

## Beneficios Implementados

### **Seguridad:**
- ✅ Filtrado automático por permisos
- ✅ Manejo elegante de errores 403
- ✅ No exposición de datos no autorizados

### **Experiencia de Usuario:**
- ✅ Solo ve información relevante
- ✅ Dashboard personalizado
- ✅ Carga más rápida (menos datos)

### **Desarrollo:**
- ✅ Interfaz consistente
- ✅ Manejo de errores estandarizado
- ✅ Utilidades reutilizables

### **Mantenimiento:**
- ✅ Código más limpio
- ✅ Separación de responsabilidades
- ✅ Fácil testing y debugging

## Testing Recomendado

### **Casos de Prueba:**
1. **Superadmin**: Debe ver todos los recursos
2. **Usuario Regular**: Solo recursos asignados
3. **Usuario Sin Permisos**: Respuestas vacías elegantes
4. **Errores de Red**: Manejo apropiado
5. **Tokens Expirados**: Redirección a login

### **Comandos de Verificación:**
```bash
# En consola del navegador
const parkings = await parkingService.getParkings()
console.log('Parkings accesibles:', parkings.length)

const sensors = await sensorService.getUserSensorsSummary()
console.log('Resumen de sensores:', sensors)

const logs = await logService.getActivityLogs({ limit: 10 })
console.log('Logs recientes:', logs.length)
```
