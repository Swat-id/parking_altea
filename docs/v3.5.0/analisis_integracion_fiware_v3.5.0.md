# 🔗 Análisis Integración FIWARE v3.5.0

## 🎯 **INFORMACIÓN GENERAL**

### **Error Identificado**: EC-003
### **Prioridad**: 🔴 CRÍTICA
### **Estado**: 🔍 EN ANÁLISIS
### **Descripción**: Campo "status" faltante en envío a FIWARE

---

## 🐛 **PROBLEMA IDENTIFICADO**

### **Descripción del Error**
El sistema está enviando información a FIWARE pero **omite el campo "status"** que debería contener el estado actual de cada parking.

### **Impacto**
- FIWARE no recibe información completa del estado de parkings
- Sistemas externos no pueden determinar el estado real (LIBRE, DENSO, COMPLETO)
- Pérdida de información crítica para toma de decisiones

### **Estado Esperado vs Actual**
```json
// ACTUAL (campo status faltante)
{
  "parking_id": 1,
  "name": "Parking Centro",
  "current_occupancy": 85,
  "max_capacity": 100,
  "free_spaces": 15
  // ❌ FALTA: "status": "DENSO"
}

// ESPERADO (con campo status)
{
  "parking_id": 1,
  "name": "Parking Centro", 
  "current_occupancy": 85,
  "max_capacity": 100,
  "free_spaces": 15,
  "status": "DENSO"  // ✅ CAMPO REQUERIDO
}
```

---

## 🔍 **ANÁLISIS TÉCNICO**

### **Valores Posibles del Campo Status**
El campo `status` debe contener uno de estos valores según la lógica del sistema:

#### **Estados Estándar**
- **"LIBRE"**: Parking con plazas disponibles (verde)
- **"DENSO"**: Parking con pocas plazas disponibles (amarillo)  
- **"COMPLETO"**: Parking lleno o sin plazas (rojo)

#### **Estados por Programación**
- **Mensaje de programación activa**: Si hay una programación activa, el status debería ser el mensaje configurado en la programación

#### **Estados Especiales**
- **Número de plazas libres**: Según configuración del parking (message_type)

### **Lógica de Determinación del Status**
```python
def get_parking_status(parking, active_schedule=None):
    """Determinar el status que debe enviarse a FIWARE"""
    
    # 1. Si hay programación activa, usar mensaje de programación
    if active_schedule:
        return active_schedule.message
    
    # 2. Si el parking está configurado para mostrar número de plazas
    if parking.message_type == 'PLAZAS_LIBRES':
        free_spaces = parking.max_capacity - parking.current_occupancy
        return str(free_spaces)
    
    # 3. Estado estándar basado en umbrales
    free_spaces = parking.max_capacity - parking.current_occupancy
    
    if free_spaces <= parking.threshold_full:
        return "COMPLETO"
    elif free_spaces <= parking.threshold_dense:
        return "DENSO"
    else:
        return "LIBRE"
```

---

## 🔧 **LOCALIZACIÓN DEL PROBLEMA**

### **Archivos a Revisar**
Basándome en el análisis del código, los lugares más probables donde debería implementarse el envío a FIWARE:

#### **1. Endpoint de Estado de Parkings**
```python
# src/api_server.py - Línea ~606
@api_bp.route('/parkings/status', methods=['GET'])
def get_parkings_status():
    # Aquí se genera la respuesta con datos de parkings
    # POSIBLE UBICACIÓN: Agregar envío a FIWARE después de generar respuesta
```

#### **2. Actualización de Paneles**
```python
# src/panel_communication_service.py - Línea ~413
def update_parking_panels(parking_id, current_occupancy, max_capacity, status, db_session=None):
    # POSIBLE UBICACIÓN: Agregar envío a FIWARE después de actualizar paneles
```

#### **3. Procesamiento de Cámaras**
```python
# src/camera_server.py - Línea ~508
# Después de actualizar paneles, también enviar a FIWARE
update_parking_panels(parking.id, parking.current_occupancy, parking.max_capacity, parking.status)
# AGREGAR AQUÍ: send_to_fiware(parking_data)
```

---

## 💡 **SOLUCIÓN PROPUESTA**

### **Paso 1: Crear Servicio FIWARE**
```python
# src/fiware_service.py (NUEVO ARCHIVO)
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from models import Parking, PanelSchedule

logger = logging.getLogger(__name__)

class FiwareService:
    """Servicio para envío de datos a FIWARE"""
    
    def __init__(self, fiware_url: str = None, api_key: str = None):
        self.fiware_url = fiware_url or os.getenv('FIWARE_URL')
        self.api_key = api_key or os.getenv('FIWARE_API_KEY')
        self.timeout = 30
        
    def send_parking_status(self, parking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar estado de parking a FIWARE"""
        try:
            # Preparar payload con campo status incluido
            payload = {
                "parking_id": parking_data['parking_id'],
                "name": parking_data['name'],
                "location": parking_data.get('location', ''),
                "current_occupancy": parking_data['current_occupancy'],
                "max_capacity": parking_data['max_capacity'],
                "free_spaces": parking_data['free_spaces'],
                "status": parking_data['status'],  # ✅ CAMPO CRÍTICO
                "occupancy_percentage": parking_data.get('occupancy_percentage', 0),
                "timestamp": datetime.now().isoformat(),
                "last_updated": parking_data.get('last_updated')
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else None
            }
            
            response = requests.post(
                self.fiware_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"FIWARE: Status sent successfully for parking {parking_data['name']}")
                return {'success': True, 'response': response.json()}
            else:
                logger.error(f"FIWARE: Error {response.status_code} for parking {parking_data['name']}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logger.error(f"FIWARE: Exception sending status for parking {parking_data.get('name', 'unknown')}: {e}")
            return {'success': False, 'error': str(e)}
```

### **Paso 2: Función Helper para Status**
```python
# src/parking_status_helper.py (NUEVO ARCHIVO)
from models import Parking, PanelSchedule
from panel_schedule_service import PanelScheduleService

def get_parking_status_for_fiware(parking: Parking, session) -> str:
    """Obtener el status correcto para envío a FIWARE"""
    
    # 1. Verificar programaciones activas
    schedule_service = PanelScheduleService(session)
    active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
    
    if active_schedules:
        # Usar mensaje de programación activa
        return active_schedules[0].message
    
    # 2. Verificar tipo de mensaje configurado
    if parking.message_type == 'PLAZAS_LIBRES':
        free_spaces = parking.max_capacity - parking.current_occupancy
        return str(max(0, free_spaces))  # No mostrar negativos
    
    # 3. Estado estándar
    return parking.status  # LIBRE, DENSO, COMPLETO
```

### **Paso 3: Integrar en Puntos Clave**
```python
# Modificar src/panel_communication_service.py
def update_parking_panels(parking_id: int, current_occupancy: int, max_capacity: int, status: str, db_session=None) -> Dict:
    # ... código existente ...
    
    # NUEVO: Enviar a FIWARE después de actualizar paneles
    try:
        from fiware_service import FiwareService
        from parking_status_helper import get_parking_status_for_fiware
        
        session = db_session or Session()
        parking = session.query(Parking).get(parking_id)
        
        if parking:
            fiware_status = get_parking_status_for_fiware(parking, session)
            
            fiware_data = {
                'parking_id': parking.id,
                'name': parking.name,
                'location': parking.location,
                'current_occupancy': current_occupancy,
                'max_capacity': max_capacity,
                'free_spaces': max_capacity - current_occupancy,
                'status': fiware_status,  # ✅ CAMPO INCLUIDO
                'occupancy_percentage': occupancy_percentage,
                'last_updated': datetime.now().isoformat()
            }
            
            fiware_service = FiwareService()
            fiware_result = fiware_service.send_parking_status(fiware_data)
            
            if fiware_result['success']:
                logger.info(f"FIWARE: Status sent for {parking.name}: {fiware_status}")
            else:
                logger.error(f"FIWARE: Failed to send status for {parking.name}: {fiware_result['error']}")
        
        if not db_session:
            session.close()
            
    except Exception as e:
        logger.error(f"FIWARE: Error in integration: {e}")
```

---

## 📋 **PLAN DE IMPLEMENTACIÓN**

### **Fase 1: Identificación (Día 1)**
- [ ] Localizar código actual de integración FIWARE
- [ ] Identificar endpoints/funciones que envían datos
- [ ] Revisar logs para ver formato actual de envío

### **Fase 2: Desarrollo (Día 1-2)**
- [ ] Crear `fiware_service.py` con lógica de envío
- [ ] Crear `parking_status_helper.py` con lógica de status
- [ ] Modificar puntos de integración existentes
- [ ] Agregar campo `status` a payload FIWARE

### **Fase 3: Testing (Día 2)**
- [ ] Probar envío con programaciones activas
- [ ] Probar con diferentes tipos de mensaje
- [ ] Validar estados LIBRE/DENSO/COMPLETO
- [ ] Verificar logs de FIWARE

### **Fase 4: Despliegue (Día 2)**
- [ ] Actualizar variables de entorno FIWARE
- [ ] Desplegar cambios siguiendo guía v3.5.0
- [ ] Monitorear logs de integración

---

## 🧪 **CASOS DE TESTING**

### **Test 1: Estados Estándar**
```python
# Parking LIBRE (>threshold_dense plazas libres)
expected_status = "LIBRE"

# Parking DENSO (<=threshold_dense, >threshold_full)  
expected_status = "DENSO"

# Parking COMPLETO (<=threshold_full plazas libres)
expected_status = "COMPLETO"
```

### **Test 2: Programaciones Activas**
```python
# Con programación activa: "PARKING CERRADO"
expected_status = "PARKING CERRADO"

# Con programación de evento: "MERCADO SEMANAL"
expected_status = "MERCADO SEMANAL"
```

### **Test 3: Tipo de Mensaje**
```python
# message_type = 'PLAZAS_LIBRES', 15 plazas libres
expected_status = "15"

# message_type = 'ESTADO', parking denso
expected_status = "DENSO"
```

---

## ⚠️ **CONSIDERACIONES**

### **Configuración Requerida**
```bash
# Variables de entorno
FIWARE_URL=https://fiware.example.com/api/parking
FIWARE_API_KEY=your_api_key_here
```

### **Manejo de Errores**
- Timeout en envíos (30s máximo)
- Reintentos en caso de fallo temporal
- Logs detallados para debugging
- No bloquear operación principal si FIWARE falla

### **Rendimiento**
- Envíos asíncronos para no impactar respuesta
- Cache de últimos estados para evitar envíos duplicados
- Rate limiting si es necesario

---

## 📊 **IMPACTO ESPERADO**

### **Antes de la Corrección**
```json
// FIWARE recibe datos incompletos
{
  "parking_id": 1,
  "occupancy": 85,
  "capacity": 100
  // ❌ Sin información de estado
}
```

### **Después de la Corrección**
```json
// FIWARE recibe datos completos
{
  "parking_id": 1,
  "name": "Parking Centro",
  "current_occupancy": 85,
  "max_capacity": 100,
  "free_spaces": 15,
  "status": "DENSO",  // ✅ Estado incluido
  "occupancy_percentage": 85.0,
  "timestamp": "2025-01-XX T10:30:00Z"
}
```

---

**Estado**: 📋 **Análisis Completado - Pendiente Localización de Código FIWARE**
**Próximo Paso**: Identificar ubicación exacta de integración FIWARE existente
**Prioridad**: 🔴 **CRÍTICA** - Datos incompletos en sistema externo

---

*Análisis FIWARE v3.5.0 - Enero 2025*
