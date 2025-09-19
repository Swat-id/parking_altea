# Análisis: Selección de Ventanas para Paneles Tipo 3

## Descripción de la Funcionalidad

La mejora consiste en permitir la selección específica de la ventana (0 o 1) al enviar mensajes a paneles Tipo 3, que son paneles con múltiples ventanas de visualización.

## Estado Actual del Sistema

### Estructura Actual de Paneles

Según el análisis del código actual:

1. **Modelo Panel** (`src/models.py`):
   - Campo `window_config` (JSON) para configuración de ventanas
   - Campo `panel_type_id` que vincula con tipos de panel
   - Relación con `PanelType` que incluye `windows_count`

2. **Envío de Mensajes Actual**:
   - En `src/panel_client.py`, línea 77-89: Se configura solo ventana ID 0
   - En `client/src/services/panelService.js`, línea 71: Campo `window` con valor por defecto 1
   - En `client/src/pages/Panels.jsx`, línea 303: Campo `window: 1` hardcodeado

### Protocolo de Comunicación

El sistema actual utiliza una estructura de ventanas en el payload:

```json
{
  "windows": [
    {
      "id": 0,
      "text": "mensaje",
      "color": 1,
      "fontSize": 2,
      "speed": 100,
      "effect": 2,
      "stayTime": 50,
      "alignmentH": 1,
      "alignmentV": 1
    }
  ]
}
```

## Análisis de Cambios Requeridos

### 1. Frontend - Interfaz de Usuario

**Archivo**: `client/src/pages/Panels.jsx`

**Cambios necesarios**:
- Agregar selector de ventana en el modal de envío de mensaje (líneas 726-758)
- Detectar si el panel seleccionado es Tipo 3 para mostrar el selector
- Modificar el objeto `messageData` para incluir la ventana seleccionada

**Nuevo componente UI**:
```jsx
{selectedPanel && isPanelType3(selectedPanel) && (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      Ventana de Destino
    </label>
    <select
      value={selectedWindow}
      onChange={(e) => setSelectedWindow(parseInt(e.target.value))}
      className="input-field"
    >
      <option value={0}>Ventana 0</option>
      <option value={1}>Ventana 1</option>
    </select>
  </div>
)}
```

### 2. Backend - API y Servicios

**Archivo**: `src/api_server.py`

**Cambios necesarios**:
- Modificar endpoint `/panel/<int:panel_id>/message` (líneas 1613-1666)
- Agregar parámetro `window` al request
- Validar que la ventana seleccionada sea válida para el tipo de panel

**Archivo**: `src/panel_communication_service.py`

**Cambios necesarios**:
- Modificar método `_send_to_unified_api` (líneas 109-130)
- Permitir especificación de ventana específica
- Mantener compatibilidad con paneles de una sola ventana

### 3. Validaciones y Lógica de Negocio

**Validaciones requeridas**:
1. Verificar que el panel sea Tipo 3 antes de permitir selección de ventana
2. Validar que la ventana seleccionada (0 o 1) sea válida
3. Para paneles no Tipo 3, usar ventana 0 por defecto
4. Mantener retrocompatibilidad con el sistema actual

## Implementación Detallada

### Fase 1: Identificación de Paneles Tipo 3

```sql
-- Query para identificar paneles Tipo 3
SELECT p.id, p.name, pt.name as panel_type_name, pt.windows_count 
FROM panels p 
JOIN panel_types pt ON p.panel_type_id = pt.id 
WHERE pt.windows_count > 1;
```

### Fase 2: Modificación del Frontend

1. **Estado del componente**:
   ```jsx
   const [selectedWindow, setSelectedWindow] = useState(0)
   ```

2. **Función de validación**:
   ```jsx
   const isPanelType3 = (panel) => {
     return panel.panel_type && panel.panel_type.windows_count > 1
   }
   ```

3. **Modificación del handler**:
   ```jsx
   const messageData = {
     message: messageText,
     duration: messageDuration,
     color: selectedColor,
     fontSize: 2,
     showEffect: "fijo",
     window: isPanelType3(selectedPanel) ? selectedWindow : 0
   }
   ```

### Fase 3: Modificación del Backend

1. **API Endpoint**:
   ```python
   @api_bp.route('/panel/<int:panel_id>/message', methods=['POST'])
   @require_panel_access('panel_id')
   def send_message_to_panel(panel_id):
       req = request.get_json(force=True)
       window = req.get('window', 0)  # Ventana por defecto 0
       
       # Validar ventana para paneles Tipo 3
       if panel.panel_type and panel.panel_type.windows_count > 1:
           if window not in [0, 1]:
               return jsonify({'error': 'Invalid window for panel type'}), 400
   ```

2. **Servicio de comunicación**:
   ```python
   def send_custom_text(self, panel_ip: str, text: str, window: int = 0, ...):
       windows = [{
           "id": window,
           "text": text,
           "color": color,
           "fontSize": font_size,
           "effect": effect,
           ...
       }]
   ```

## Casos de Prueba

### Caso 1: Panel Tipo 3 - Ventana 0
- **Input**: Panel Tipo 3, mensaje "TEST", ventana 0
- **Expected**: Mensaje enviado a ventana 0 del panel

### Caso 2: Panel Tipo 3 - Ventana 1
- **Input**: Panel Tipo 3, mensaje "TEST", ventana 1
- **Expected**: Mensaje enviado a ventana 1 del panel

### Caso 3: Panel No Tipo 3
- **Input**: Panel normal, mensaje "TEST", ventana especificada
- **Expected**: Mensaje enviado a ventana 0 (ignorar selección)

### Caso 4: Validación de Ventana Inválida
- **Input**: Panel Tipo 3, ventana 2
- **Expected**: Error de validación

## Compatibilidad y Migración

### Retrocompatibilidad
- Los paneles existentes continuarán funcionando sin cambios
- El campo `window` será opcional en la API
- Valor por defecto: ventana 0

### Base de Datos
- No se requieren cambios en la estructura de base de datos
- La información de ventanas ya está en `panel_types.windows_count`

## Estimación de Esfuerzo

- **Frontend**: 4 horas
- **Backend**: 3 horas  
- **Testing**: 2 horas
- **Documentación**: 1 hora
- **Total**: 10 horas

## Riesgos y Consideraciones

1. **Compatibilidad**: Asegurar que paneles antiguos no se vean afectados
2. **Validación**: Implementar validaciones robustas para evitar errores
3. **UI/UX**: El selector debe ser intuitivo y aparecer solo cuando sea necesario
4. **Testing**: Probar con paneles reales Tipo 3 antes del despliegue

---

*Análisis completado para la funcionalidad de selección de ventanas en paneles Tipo 3*
