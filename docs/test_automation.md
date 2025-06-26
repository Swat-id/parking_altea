# Pruebas Automatizadas - Parking Altea

## Descripción

El sistema incluye un script de pruebas automatizadas (`test_api.py`) que verifica el funcionamiento de todos los endpoints de la API REST y el servidor de cámaras.

## Archivos de Pruebas

### `test_api.py`
Script principal de pruebas automatizadas que:
- Ejecuta pruebas contra todos los endpoints principales
- Genera reportes detallados en formato JSON
- Proporciona resúmenes de éxito/fallo
- Guarda resultados para análisis posterior

### `docs/latest_test_report.json`
Último reporte de pruebas generado automáticamente.

## Endpoints Probados

| Endpoint | Método | Descripción | Estado |
|----------|--------|-------------|--------|
| `/parkings` | GET | Listar todos los parkings | ✅ Probado |
| `/parking/{id}` | GET | Obtener parking específico | ✅ Probado |
| `/parking/{id}/occupancy` | POST | Actualizar ocupación | ✅ Probado |
| `/parking/{id}/config` | POST | Actualizar configuración | ✅ Probado |
| `/parking/{id}/message` | POST | Enviar mensaje a paneles | ✅ Probado |
| `/parking/{id}/message` | GET | Obtener mensajes programados | ✅ Probado |
| `/camera` | POST | Recepción de datos de cámaras | ✅ Probado |

## Ejecución de Pruebas

### Requisitos
```bash
pip install requests
```

### Ejecutar Pruebas
```bash
python test_api.py
```

### Salida Esperada
```
🚀 Iniciando pruebas automatizadas de la API Parking Altea
============================================================

🔍 Ejecutando: GET /parkings
[✅ EXITOSO] GET /parkings - Lista de 9 parkings obtenida

🔍 Ejecutando: GET /parking/1
[✅ EXITOSO] GET /parking/1 - Parking 1 - P. Ciutat Esportiva obtenido

🔍 Ejecutando: POST /parking/1/occupancy
[✅ EXITOSO] POST /parking/1/occupancy - Ocupación actualizada a 450

🔍 Ejecutando: POST /parking/1/config
[✅ EXITOSO] POST /parking/1/config - Configuración actualizada

🔍 Ejecutando: POST /parking/1/message
[✅ EXITOSO] POST /parking/1/message - Mensaje enviado - 0 exitosos, 1 fallidos

🔍 Ejecutando: GET /parking/1/message
[✅ EXITOSO] GET /parking/1/message - 0 mensajes programados

🔍 Ejecutando: POST /camera
[✅ EXITOSO] POST /camera - Datos de cámara enviados correctamente

============================================================
📊 RESUMEN DE PRUEBAS
============================================================
Fecha: 2025-06-26T00:30:00
Duración: 8.45 segundos
Total de pruebas: 7
Pruebas exitosas: 7
Pruebas fallidas: 0
Tasa de éxito: 100.0%
🎉 Estado: EXCELENTE

📄 Reporte guardado en: test_report_20250626_003000.json
📄 Reporte guardado en: docs/latest_test_report.json
```

## Estructura del Reporte

El reporte se guarda en formato JSON con la siguiente estructura:

```json
{
  "test_date": "2025-06-26T00:30:00",
  "duration_seconds": 8.45,
  "total_tests": 7,
  "successful_tests": 7,
  "failed_tests": 0,
  "success_rate": 100.0,
  "results": [
    {
      "timestamp": "2025-06-26T00:30:01",
      "endpoint": "/parkings",
      "method": "GET",
      "status": "✅ EXITOSO",
      "details": "Lista de 9 parkings obtenida",
      "response_data": [...]
    }
  ]
}
```

## Interpretación de Resultados

### Estados de Pruebas
- **✅ EXITOSO**: Endpoint responde correctamente
- **❌ ERROR**: Endpoint falla o no responde

### Tasa de Éxito
- **90-100%**: EXCELENTE - Sistema funcionando perfectamente
- **70-89%**: BUENO - Algunos problemas menores
- **50-69%**: REGULAR - Problemas significativos
- **<50%**: CRÍTICO - Sistema con fallos graves

## Pruebas Específicas

### Prueba de Ocupación
- Actualiza la ocupación del parking 1 a 450 vehículos
- Verifica que se registre correctamente
- Comprueba el manejo de descuadres

### Prueba de Configuración
- Actualiza capacidad máxima y umbrales
- Verifica que los cambios se apliquen
- Comprueba el cálculo de estados

### Prueba de Mensajes
- Envía mensaje de prueba a paneles
- Registra paneles exitosos y fallidos
- Verifica la respuesta del sistema

### Prueba de Cámaras
- Simula envío de datos desde cámara
- Verifica recepción en servidor de cámaras
- Comprueba procesamiento de datos

## Integración con CI/CD

El script puede integrarse en pipelines de CI/CD:

```yaml
# Ejemplo para GitHub Actions
- name: Run API Tests
  run: |
    pip install requests
    python test_api.py
    
- name: Upload Test Report
  uses: actions/upload-artifact@v2
  with:
    name: test-report
    path: test_report_*.json
```

## Monitoreo Continuo

### Programación Automática
```bash
# Ejecutar pruebas cada hora
0 * * * * cd /path/to/parking_altea && python test_api.py

# Ejecutar pruebas diarias a las 6:00 AM
0 6 * * * cd /path/to/parking_altea && python test_api.py
```

### Alertas
- Configurar notificaciones por email cuando la tasa de éxito < 90%
- Enviar alertas a Slack/Teams en caso de fallos críticos
- Generar reportes semanales de tendencias

## Troubleshooting

### Problemas Comunes

#### Error de Conexión
```
❌ ERROR - Excepción: Connection refused
```
**Solución**: Verificar que los servicios estén ejecutándose
```bash
systemctl status parking-api.service parking-camera.service
```

#### Timeout en Pruebas
```
❌ ERROR - Excepción: Read timeout
```
**Solución**: Aumentar timeout en el script o verificar latencia de red

#### Error de Autenticación
```
❌ ERROR - Status code: 401
```
**Solución**: Verificar configuración de autenticación si está implementada

### Logs de Debug
Para obtener más información, modificar el script para incluir logs detallados:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Próximas Mejoras

1. **Pruebas de Carga**: Simular múltiples usuarios concurrentes
2. **Pruebas de Seguridad**: Verificar vulnerabilidades comunes
3. **Pruebas de Base de Datos**: Verificar integridad de datos
4. **Pruebas de Frontend**: Integrar con herramientas como Selenium
5. **Métricas de Rendimiento**: Medir tiempos de respuesta
6. **Pruebas de Recuperación**: Simular fallos y recuperación

## Contacto

Para problemas con las pruebas automatizadas:
- Revisar logs del sistema
- Verificar conectividad de red
- Consultar documentación de endpoints
- Contactar al equipo de desarrollo 