# API de Parkings - Parking Altea v3.1.0

## Información General

- **URL Base**: `http://157.180.91.63:6001`
- **Versión**: v3.1.0
- **Estado**: ✅ **OPERATIVA**
- **Última Verificación**: 16/07/2025 23:25

## Endpoints Disponibles

### 1. Listar Todos los Parkings

**GET** `/parkings`

Obtiene la lista completa de todos los parkings con información básica.

#### Respuesta Exitosa (200)

```json
[
  {
    "estado": "LIBRE",
    "id": 7,
    "location": "38.59233612295076,-0.054784805753995615",
    "name": "7 - P. Port Altea",
    "plazas_libres": 166,
    "plazas_ocupadas": 0,
    "threshold_dense": 10,
    "threshold_full": 4,
    "total_plazas": 166
  },
  {
    "estado": "COMPLETO",
    "id": 8,
    "location": "38.596740725369926,-0.051435704787314886",
    "name": "8 - P. Estació Altea",
    "plazas_libres": -90,
    "plazas_ocupadas": 170,
    "threshold_dense": 10,
    "threshold_full": 4,
    "total_plazas": 80
  }
]
```

#### Estados Posibles
- `LIBRE`: Plazas libres suficientes
- `DENSO`: Ocupación alta pero no completa
- `COMPLETO`: Parking lleno
- `DESCUADRE_NEGATIVO`: Ocupación mayor que capacidad máxima
- `DESCUADRE_POSITIVO`: Ocupación negativa (error de datos)

#### Ejemplo de Uso

```bash
# PowerShell
(Invoke-WebRequest -Uri "http://157.180.91.63:6001/parkings" -Method GET).Content

# cURL
curl -X GET http://157.180.91.63:6001/parkings

# JavaScript
fetch('http://157.180.91.63:6001/parkings')
  .then(response => response.json())
  .then(data => console.log(data));
```

### 2. Estado Completo de Parkings

**GET** `/parkings/status`

Obtiene información detallada de todos los parkings incluyendo estado de paneles y programaciones.

#### Respuesta Exitosa (200)

```json
{
  "success": true,
  "total_parkings": 9,
  "timestamp": "2025-07-16T23:25:08.230512",
  "parkings": [
    {
      "id": 7,
      "name": "7 - P. Port Altea",
      "location": "38.59233612295076,-0.054784805753995615",
      "total_plazas": 166,
      "plazas_ocupadas": 0,
      "plazas_libres": 166,
      "estado": "LIBRE",
      "estado_valenciano": "LLIURE",
      "panel_display_text": "LLIURE",
      "has_active_schedules": false,
      "active_schedules_count": 0,
      "threshold_dense": 10,
      "threshold_full": 4,
      "panels": [],
      "last_update": "2025-07-16T23:25:08.206634"
    },
    {
      "id": 8,
      "name": "8 - P. Estació Altea",
      "location": "38.596740725369926,-0.051435704787314886",
      "total_plazas": 80,
      "plazas_ocupadas": 170,
      "plazas_libres": -90,
      "estado": "COMPLETO",
      "estado_valenciano": "COMPLET",
      "panel_display_text": "COMPLET",
      "has_active_schedules": false,
      "active_schedules_count": 0,
      "threshold_dense": 10,
      "threshold_full": 4,
      "panels": [
        {
          "id": 9,
          "ip": "172.20.2.50",
          "name": "PANEL RENFE",
          "protocol_version": "old",
          "status": "ONLINE",
          "last_message": "EN PROVES  ",
          "last_update": "2025-07-16T06:49:56.160791"
        }
      ],
      "last_update": "2025-07-16T23:25:08.209409"
    }
  ]
}
```

#### Campos de Información

**Información General del Parking:**
- `id`: ID único del parking
- `name`: Nombre del parking
- `location`: Coordenadas GPS (latitud,longitud)
- `total_plazas`: Capacidad máxima del parking
- `plazas_ocupadas`: Número de plazas ocupadas
- `plazas_libres`: Número de plazas libres (puede ser negativo en descuadres)

**Estados:**
- `estado`: Estado en español (LIBRE, DENSO, COMPLETO, DESCUADRE_*)
- `estado_valenciano`: Estado en valenciano (LLIURE, DENS, COMPLET)
- `panel_display_text`: Texto que se está mostrando actualmente en los paneles

**Configuración:**
- `threshold_dense`: Umbral para estado DENSO
- `threshold_full`: Umbral para estado COMPLETO

**Programaciones:**
- `has_active_schedules`: Si hay programaciones activas
- `active_schedules_count`: Número de programaciones activas

**Paneles:**
- `panels`: Array con información de cada panel del parking
  - `id`: ID del panel
  - `ip`: Dirección IP del panel
  - `name`: Nombre del panel
  - `protocol_version`: Versión del protocolo (old/new)
  - `status`: Estado del panel (ONLINE/OFFLINE)
  - `last_message`: Último mensaje enviado
  - `last_update`: Última actualización

#### Ejemplo de Uso

```bash
# PowerShell
(Invoke-WebRequest -Uri "http://157.180.91.63:6001/parkings/status" -Method GET).Content

# cURL
curl -X GET http://157.180.91.63:6001/parkings/status

# JavaScript
fetch('http://157.180.91.63:6001/parkings/status')
  .then(response => response.json())
  .then(data => {
    console.log(`Total parkings: ${data.total_parkings}`);
    data.parkings.forEach(parking => {
      console.log(`${parking.name}: ${parking.estado} (${parking.plazas_libres} libres)`);
    });
  });
```

### 3. Obtener Parking Específico

**GET** `/parking/{id}`

Obtiene información detallada de un parking específico.

#### Parámetros
- `id` (integer, requerido): ID del parking

#### Respuesta Exitosa (200)

```json
{
  "id": 1,
  "name": "1 - P. Ciutat Esportiva",
  "location": "38.607426920203615,-0.04519652478288384",
  "total_plazas": 500,
  "plazas_ocupadas": 288,
  "plazas_libres": 212,
  "estado": "LIBRE",
  "threshold_dense": 15,
  "threshold_full": 5
}
```

#### Respuesta de Error (404)

```json
{
  "error": "Parking not found"
}
```

#### Ejemplo de Uso

```bash
# PowerShell
(Invoke-WebRequest -Uri "http://157.180.91.63:6001/parking/1" -Method GET).Content

# cURL
curl -X GET http://157.180.91.63:6001/parking/1

# JavaScript
fetch('http://157.180.91.63:6001/parking/1')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Casos de Uso Prácticos

### 1. Monitoreo en Tiempo Real

```javascript
// Función para obtener estado actual de todos los parkings
async function getParkingsStatus() {
  try {
    const response = await fetch('http://157.180.91.63:6001/parkings/status');
    const data = await response.json();
    
    if (data.success) {
      console.log(`Estado de ${data.total_parkings} parkings:`);
      
      data.parkings.forEach(parking => {
        const status = parking.estado;
        const freeSpaces = parking.plazas_libres;
        const totalSpaces = parking.total_plazas;
        const occupancy = ((parking.plazas_ocupadas / totalSpaces) * 100).toFixed(1);
        
        console.log(`${parking.name}:`);
        console.log(`  - Estado: ${status}`);
        console.log(`  - Ocupación: ${occupancy}% (${parking.plazas_ocupadas}/${totalSpaces})`);
        console.log(`  - Plazas libres: ${freeSpaces}`);
        console.log(`  - Paneles: ${parking.panels.length} (${parking.panels.filter(p => p.status === 'ONLINE').length} online)`);
      });
    }
  } catch (error) {
    console.error('Error obteniendo estado de parkings:', error);
  }
}

// Ejecutar cada 30 segundos
setInterval(getParkingsStatus, 30000);
```

### 2. Detección de Parkings Completos

```javascript
// Función para detectar parkings completos o con problemas
function detectFullParkings(parkings) {
  const fullParkings = parkings.filter(parking => 
    parking.estado === 'COMPLETO' || 
    parking.estado === 'DESCUADRE_NEGATIVO'
  );
  
  if (fullParkings.length > 0) {
    console.log('⚠️ Parkings con problemas:');
    fullParkings.forEach(parking => {
      console.log(`  - ${parking.name}: ${parking.estado}`);
      if (parking.estado === 'DESCUADRE_NEGATIVO') {
        console.log(`    Error: ${parking.plazas_ocupadas} ocupadas de ${parking.total_plazas} total`);
      }
    });
  }
  
  return fullParkings;
}
```

### 3. Verificación de Paneles

```javascript
// Función para verificar estado de paneles
function checkPanelsStatus(parkings) {
  const allPanels = parkings.flatMap(parking => 
    parking.panels.map(panel => ({
      ...panel,
      parking_name: parking.name
    }))
  );
  
  const offlinePanels = allPanels.filter(panel => panel.status === 'OFFLINE');
  const onlinePanels = allPanels.filter(panel => panel.status === 'ONLINE');
  
  console.log(`📊 Estado de Paneles:`);
  console.log(`  - Total: ${allPanels.length}`);
  console.log(`  - Online: ${onlinePanels.length}`);
  console.log(`  - Offline: ${offlinePanels.length}`);
  
  if (offlinePanels.length > 0) {
    console.log('❌ Paneles offline:');
    offlinePanels.forEach(panel => {
      console.log(`  - ${panel.name} (${panel.parking_name}) - ${panel.ip}`);
    });
  }
  
  return { allPanels, onlinePanels, offlinePanels };
}
```

### 4. Análisis de Ocupación

```javascript
// Función para analizar ocupación de parkings
function analyzeOccupancy(parkings) {
  const analysis = {
    total_spaces: 0,
    total_occupied: 0,
    total_free: 0,
    average_occupancy: 0,
    parkings_by_status: {
      LIBRE: 0,
      DENSO: 0,
      COMPLETO: 0,
      DESCUADRE_NEGATIVO: 0,
      DESCUADRE_POSITIVO: 0
    }
  };
  
  parkings.forEach(parking => {
    analysis.total_spaces += parking.total_plazas;
    analysis.total_occupied += parking.plazas_ocupadas;
    analysis.total_free += parking.plazas_libres;
    analysis.parkings_by_status[parking.estado]++;
  });
  
  analysis.average_occupancy = ((analysis.total_occupied / analysis.total_spaces) * 100).toFixed(1);
  
  console.log('📈 Análisis de Ocupación:');
  console.log(`  - Total plazas: ${analysis.total_spaces}`);
  console.log(`  - Total ocupadas: ${analysis.total_occupied}`);
  console.log(`  - Total libres: ${analysis.total_free}`);
  console.log(`  - Ocupación media: ${analysis.average_occupancy}%`);
  console.log('  - Por estado:');
  Object.entries(analysis.parkings_by_status).forEach(([status, count]) => {
    if (count > 0) {
      console.log(`    ${status}: ${count} parkings`);
    }
  });
  
  return analysis;
}
```

## Integración con Frontend

### React Hook Personalizado

```javascript
// hooks/useParkings.js
import { useState, useEffect } from 'react';

export const useParkings = () => {
  const [parkings, setParkings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchParkings = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://157.180.91.63:6001/parkings/status');
      const data = await response.json();
      
      if (data.success) {
        setParkings(data.parkings);
        setError(null);
      } else {
        setError('Error obteniendo datos de parkings');
      }
    } catch (err) {
      setError('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParkings();
    
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchParkings, 30000);
    return () => clearInterval(interval);
  }, []);

  return { parkings, loading, error, refetch: fetchParkings };
};
```

### Componente de Dashboard

```jsx
// components/ParkingsDashboard.jsx
import React from 'react';
import { useParkings } from '../hooks/useParkings';

const ParkingsDashboard = () => {
  const { parkings, loading, error } = useParkings();

  if (loading) return <div>Cargando parkings...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="parkings-dashboard">
      <h2>Estado de Parkings ({parkings.length})</h2>
      
      <div className="parkings-grid">
        {parkings.map(parking => (
          <div key={parking.id} className={`parking-card ${parking.estado.toLowerCase()}`}>
            <h3>{parking.name}</h3>
            <div className="parking-info">
              <p><strong>Estado:</strong> {parking.estado}</p>
              <p><strong>Ocupación:</strong> {parking.plazas_ocupadas}/{parking.total_plazas}</p>
              <p><strong>Libres:</strong> {parking.plazas_libres}</p>
              <p><strong>Paneles:</strong> {parking.panels.length} online</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ParkingsDashboard;
```

## Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `400 Bad Request`: Datos de entrada inválidos
- `404 Not Found`: Parking no encontrado
- `500 Internal Server Error`: Error interno del servidor

## Notas Importantes

1. **Descuadres**: El sistema permite y registra ocupaciones que superan la capacidad máxima, marcándolas como descuadres para su posterior corrección.

2. **Estados de Paneles**: Los paneles pueden estar ONLINE u OFFLINE. Los paneles offline no reciben mensajes.

3. **Protocolos**: Los paneles pueden usar protocolo "old" (v1.2.6) o "new" (v1.4.7). Esto afecta cómo se envían los mensajes.

4. **Programaciones**: Los parkings pueden tener mensajes programados que tienen prioridad sobre el estado automático.

5. **Coordenadas**: Las ubicaciones están en formato GPS (latitud,longitud) para integración con mapas.

## Ejemplos de Respuestas Reales

### Parking con Descuadre
```json
{
  "estado": "DESCUADRE_NEGATIVO",
  "id": 8,
  "name": "8 - P. Estació Altea",
  "plazas_libres": -90,
  "plazas_ocupadas": 170,
  "total_plazas": 80
}
```

### Parking con Paneles
```json
{
  "id": 2,
  "name": "2 - P. Basseta Centre",
  "panels": [
    {
      "id": 2,
      "ip": "172.20.5.50",
      "name": "PANEL BASSETA 1",
      "protocol_version": "old",
      "status": "ONLINE",
      "last_message": "EN PROVES",
      "last_update": "2025-07-16T12:34:01.078943"
    }
  ]
}
```

Esta documentación proporciona una guía completa para integrar y utilizar la API de parkings del sistema Parking Altea v3.1.0. 