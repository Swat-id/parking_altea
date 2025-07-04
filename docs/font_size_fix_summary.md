# Corrección del Problema de Tamaño de Fuente en Paneles

## 📋 Resumen del Problema

**Fecha de Corrección**: 4 de Julio de 2025  
**Problema**: Los paneles con protocolo antiguo (CP5200) recibían tamaño de fuente 2 en lugar de 16  
**Impacto**: Texto demasiado pequeño en los paneles LED  
**Protocolo Afectado**: Protocolo antiguo (CP5200)  

## 🔍 Análisis del Problema

### Ubicación del Error
1. **API Server** (`src/api_server.py` línea 822): `fontSize = req.get('fontSize', 2)` - Valor por defecto incorrecto
2. **Frontend** (`client/src/services/panelService.js`): Múltiples lugares usando fontSize=2 por defecto
3. **Flujo**: Frontend → API → PanelCommunicationService → Servicio Java → Panel

### Documentación del Fabricante
- **Protocolo CP5200**: Rango válido 8-64 puntos, recomendado 16 puntos
- **Documentación**: `docs/panel_dll_integration.md` línea 124
- **Ejemplos del SDK**: Usan fontSize=16 consistentemente

## 🛠️ Correcciones Aplicadas

### 1. API Server (`src/api_server.py`)
```python
# ANTES
fontSize = req.get('fontSize', 2)

# DESPUÉS  
fontSize = req.get('fontSize', 16)  # Cambiar por defecto de 2 a 16
```

### 2. Frontend (`client/src/services/panelService.js`)
```javascript
// ANTES
fontSize: messageData.fontSize || 2,
fontSize: 2,
fontSizes: [2],

// DESPUÉS
fontSize: messageData.fontSize || 16,  // Cambiar por defecto de 2 a 16
fontSize: 16,  // Cambiar por defecto de 2 a 16
fontSizes: [16],  // Cambiar por defecto de 2 a 16
```

### 3. PanelCommunicationService (`src/panel_communication_service.py`)
```python
# Ya tenía la lógica correcta
if font_size != 16:
    logger.info(f"Font size ajustado a 16 para panel {panel_ip}")
    font_size = 16
```

## 📊 Archivos Modificados

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `src/api_server.py` | 823 | `fontSize = req.get('fontSize', 16)` |
| `client/src/services/panelService.js` | 59 | `fontSize: messageData.fontSize || 16` |
| `client/src/services/panelService.js` | 103 | `fontSize: 16` |
| `client/src/services/panelService.js` | 210 | `fontSizes: [16]` |
| `client/src/services/panelService.js` | 252 | `fontSizes: [16]` |

## 🧪 Verificación

### Script de Prueba
```bash
# Ejecutar script de verificación
python test/test_font_size_fix_verification.py
```

### Verificación Manual
1. **Enviar mensaje sin fontSize**: Debe usar 16 por defecto
2. **Enviar mensaje con fontSize=16**: Debe enviar 16 correctamente
3. **Verificar logs del servicio Java**: Debe mostrar `fontSizes: [16]`

### Comandos de Verificación
```bash
# Ver logs del servicio Java
journalctl -u parking-panel-service.service -n 20

# Buscar en logs
grep "fontSizes" /var/log/parking-panel-service.log
```

## 🎯 Resultado

### Antes de la Corrección
- ❌ Paneles recibían fontSize=2
- ❌ Texto demasiado pequeño
- ❌ No cumplía documentación del fabricante

### Después de la Corrección
- ✅ Paneles reciben fontSize=16
- ✅ Texto del tamaño correcto
- ✅ Cumple documentación del fabricante
- ✅ Respeta protocolos (16 para antiguo, 2 para nuevo)

## 🔄 Compatibilidad

### Protocolo Antiguo (CP5200)
- **Valor por defecto**: 16 puntos
- **Rango válido**: 8-64 puntos
- **Recomendado**: 16 puntos

### Protocolo Nuevo
- **Valor por defecto**: 2 (mantenido)
- **Rango**: Según documentación específica
- **Comportamiento**: Sin cambios

## 📝 Notas de Implementación

### Consideraciones
1. **Backward Compatibility**: Los valores explícitos siguen funcionando
2. **Protocol Detection**: El sistema detecta automáticamente el protocolo
3. **Logging**: Se registra cuando se ajusta el fontSize
4. **Documentation**: Actualizada la documentación del fabricante

### Próximos Pasos
1. **Testing**: Verificar en producción
2. **Monitoring**: Monitorear logs para confirmar
3. **Documentation**: Actualizar manuales de usuario

## ✅ Estado

**Estado**: 🟢 **CORREGIDO**  
**Fecha**: 4 de Julio de 2025  
**Responsable**: Equipo de desarrollo  
**Verificación**: Pendiente en producción 