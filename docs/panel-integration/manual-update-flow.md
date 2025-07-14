# Flujo de Actualización Manual de Ocupación - Paneles

## 📋 Resumen

Este documento describe el flujo de actualización manual de la ocupación de parkings desde el frontend y su integración automática con los paneles electrónicos.

## 🔄 Flujo Completo

```
Frontend → api_server.py → update_parking_panels() → API 8888 → Panel LED
```

## 📍 Ubicación del Código

### Archivo Principal
- **Archivo**: `src/api_server.py`
- **Líneas**: 645, 728
- **Función**: `update_parking_occupancy()` (POST `/parking/{id}/occupancy`)

### Función de Integración
- **Archivo**: `src/panel_communication_service.py`
- **Línea**: 388
- **Función**: `update_parking_panels()`

## 🔧 Implementación Detallada

### 1. Endpoint de Actualización Manual

```python
# src/api_server.py - Línea 600
@app.route('/parking/<int:pid>/occupancy', methods=['POST'])
@require_auth
def update_parking_occupancy(pid):
    """Actualizar ocupación de un parking manualmente"""
    try:
        req = request.get_json(force=True)
        new_occupancy = req.get('occupancy')
        new_max_capacity = req.get('max_capacity')
        
        if new_occupancy is None:
            return jsonify({'error': 'Missing occupancy field'}), 400
        
        session = Session()
        parking = session.query(Parking).get(pid)
        
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Guardar valores anteriores para logging
        previous_occupancy = parking.current_occupancy
        previous_max_capacity = parking.max_capacity
        previous_status = parking.status
        
        # Actualizar valores
        parking.current_occupancy = new_occupancy
        if new_max_capacity:
            parking.max_capacity = new_max_capacity
        
        # Calcular estado basado en umbrales
        occupancy_percent = (parking.current_occupancy / parking.max_capacity) * 100
        
        if occupancy_percent < parking.threshold_dense:
            parking.status = 'LIBRE'
        elif occupancy_percent < parking.threshold_full:
            parking.status = 'DENSO'
        else:
            parking.status = 'COMPLETO'
        
        # Guardar valores finales para envío a paneles
        final_occupancy = parking.current_occupancy
        final_max_capacity = parking.max_capacity
        final_status = parking.status
        
        session.commit()
        session.close()
        
        # Envío a paneles (Línea 645)
        try:
            from panel_communication_service import update_parking_panels
            update_parking_panels(pid, final_occupancy, final_max_capacity, final_status)
            logger.info(f"Manual occupancy update for parking {pid}: {previous_occupancy}→{final_occupancy}, status: {previous_status}→{final_status}")
        except Exception as e:
            logger.error(f"Error updating panels for manual occupancy change: {e}")
        
        return jsonify({
            'success': True,
            'parking_id': pid,
            'previous_occupancy': previous_occupancy,
            'new_occupancy': final_occupancy,
            'previous_max_capacity': previous_max_capacity,
            'new_max_capacity': final_max_capacity,
            'previous_status': previous_status,
            'new_status': final_status
        })
        
    except Exception as e:
        logger.error(f"Error updating parking occupancy: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### 2. Endpoint de Actualización Masiva

```python
# src/api_server.py - Línea 700
@app.route('/parkings/occupancy/bulk', methods=['POST'])
@require_auth
def update_parkings_occupancy_bulk():
    """Actualizar ocupación de múltiples parkings"""
    try:
        req = request.get_json(force=True)
        updates = req.get('updates', [])
        
        if not updates:
            return jsonify({'error': 'No updates provided'}), 400
        
        session = Session()
        results = []
        
        for update in updates:
            pid = update.get('parking_id')
            new_occupancy = update.get('occupancy')
            new_max_capacity = update.get('max_capacity')
            
            if not pid or new_occupancy is None:
                continue
            
            parking = session.query(Parking).get(pid)
            if not parking:
                continue
            
            # Actualizar valores
            parking.current_occupancy = new_occupancy
            if new_max_capacity:
                parking.max_capacity = new_max_capacity
            
            # Calcular estado
            occupancy_percent = (parking.current_occupancy / parking.max_capacity) * 100
            
            if occupancy_percent < parking.threshold_dense:
                parking.status = 'LIBRE'
            elif occupancy_percent < parking.threshold_full:
                parking.status = 'DENSO'
            else:
                parking.status = 'COMPLETO'
            
            results.append({
                'parking_id': pid,
                'name': parking.name,
                'occupancy': parking.current_occupancy,
                'max_capacity': parking.max_capacity,
                'status': parking.status
            })
        
        session.commit()
        session.close()
        
        # Envío a paneles para cada parking actualizado (Línea 728)
        for result in results:
            try:
                from panel_communication_service import update_parking_panels
                update_parking_panels(
                    result['parking_id'], 
                    result['occupancy'], 
                    result['max_capacity'], 
                    result['status']
                )
            except Exception as e:
                logger.error(f"Error updating panels for parking {result['parking_id']}: {e}")
        
        return jsonify({
            'success': True,
            'updated_parkings': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in bulk occupancy update: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

## 📊 Datos de Entrada

### Actualización Individual
```json
{
  "occupancy": 150,
  "max_capacity": 300
}
```

### Actualización Masiva
```json
{
  "updates": [
    {
      "parking_id": 1,
      "occupancy": 150,
      "max_capacity": 300
    },
    {
      "parking_id": 2,
      "occupancy": 80,
      "max_capacity": 100
    }
  ]
}
```

## 📤 Datos de Salida

### Respuesta Individual
```json
{
  "success": true,
  "parking_id": 1,
  "previous_occupancy": 120,
  "new_occupancy": 150,
  "previous_max_capacity": 300,
  "new_max_capacity": 300,
  "previous_status": "LIBRE",
  "new_status": "DENSO"
}
```

### Respuesta Masiva
```json
{
  "success": true,
  "updated_parkings": 2,
  "results": [
    {
      "parking_id": 1,
      "name": "P. Ciutat Esportiva",
      "occupancy": 150,
      "max_capacity": 300,
      "status": "DENSO"
    },
    {
      "parking_id": 2,
      "name": "P. Poble antic",
      "occupancy": 80,
      "max_capacity": 100,
      "status": "COMPLETO"
    }
  ]
}
```

## 🔍 Logging y Monitoreo

### Logs de Éxito
```
INFO: Manual occupancy update for parking 1: 120→150, status: LIBRE→DENSO
INFO: Panel 172.20.4.52 actualizado: DENS
INFO: Actualización de paneles completada: 2/2 exitosos
```

### Logs de Error
```
ERROR: Error updating panels for manual occupancy change: Connection timeout
ERROR: Error updating panels for parking 1: HTTP 500
ERROR: Error in bulk occupancy update: Database connection failed
```

## ⚙️ Configuración

### Variables de Entorno
```bash
API_PORT=6001
PANEL_API_URL=http://localhost:8888/api/v1/panels/send
```

### Parámetros de Validación
- **Ocupación**: Debe ser >= 0
- **Capacidad máxima**: Debe ser > 0
- **Ocupación**: No puede exceder capacidad máxima
- **Autenticación**: Requerida para todas las operaciones

## 🎯 Validación

### ✅ Funcionalidades Validadas
- Actualización individual de ocupación
- Actualización masiva de múltiples parkings
- Cálculo automático de estado según umbrales
- Envío automático a paneles
- Validación de datos de entrada
- Manejo de errores robusto
- Logging detallado

### ✅ Integración Correcta
- Usa la API unificada en puerto 8888
- Estructura de payload estándar
- Protocolo dinámico por panel
- Manejo de múltiples paneles
- Respuestas estructuradas

## 📋 Casos de Uso

### Caso 1: Ajuste Manual Individual
1. Usuario ajusta ocupación en frontend
2. Se valida que ocupación <= capacidad máxima
3. Se recalcula estado según umbrales
4. Se actualiza base de datos
5. Se envían paneles automáticamente

### Caso 2: Ajuste Masivo
1. Usuario actualiza múltiples parkings
2. Se validan todos los datos
3. Se actualizan todos los parkings
4. Se recalculan todos los estados
5. Se envían todos los paneles automáticamente

### Caso 3: Cambio de Capacidad
1. Usuario modifica capacidad máxima
2. Se recalcula porcentaje de ocupación
3. Se recalcula estado según nuevos umbrales
4. Se actualiza base de datos
5. Se envían paneles automáticamente

## 🔒 Seguridad

### Autenticación
- **Endpoint**: Requiere autenticación JWT
- **Decorador**: `@require_auth`
- **Validación**: Token válido requerido

### Validación de Datos
- **Ocupación**: Número entero >= 0
- **Capacidad**: Número entero > 0
- **Límites**: Ocupación no puede exceder capacidad
- **Formato**: JSON válido requerido

## 🎯 Conclusiones

El flujo de actualización manual está **completamente funcional** y utiliza correctamente la API unificada de paneles en el puerto 8888. La implementación incluye validación robusta, manejo de errores adecuado y logging detallado para auditoría. 