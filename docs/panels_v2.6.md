# Paneles LED v2.6 - Documentación Completa

## 📋 Resumen

La versión 2.6 introduce una gestión avanzada de paneles LED con soporte para múltiples pantallas, múltiples idiomas y comunicación a través de API REST.

---

## 🆕 Nuevas Características

### 1. Configuración de Múltiples Pantallas
- **1 pantalla**: 64x16 píxeles (configuración actual)
- **2 pantallas**: 32x16 píxeles cada una
- **3-6 pantallas**: 64x16 o 32x16 píxeles cada una
- Configuración flexible por panel

### 2. Soporte Multiidioma
- **Castellano**: LIBRE / DENSO / COMPLETO
- **Valenciano**: LLIURE / DENSA / COMPLET
- **Inglés**: FREE / BUSY / FULL
- **Francés**: LIBRE / OCCUPÉ / COMPLET
- **Alemán**: FREI / BESETZT / VOLL

### 3. API REST de Comunicación
- **Endpoint**: `http://127.0.0.1:5656/sendMulti`
- **Método**: POST
- **Formato**: JSON
- **Timeout**: 30 segundos
- **Reintentos**: 3 intentos

---

## 🗄️ Estructura de Base de Datos

### Tabla `panels` - Nuevas Columnas

| Columna | Tipo | Descripción | Valor por Defecto |
|---------|------|-------------|-------------------|
| `fabricante` | VARCHAR(100) | Fabricante del panel | 'Rótulos electrónicos' |
| `num_pantallas` | INTEGER | Número de pantallas | 1 |
| `resolucion_ancho` | INTEGER | Ancho en píxeles | 64 |
| `resolucion_alto` | INTEGER | Alto en píxeles | 16 |
| `tipo_visualizacion` | VARCHAR(20) | Tipo de visualización | 'plazas' |
| `idioma_principal` | VARCHAR(10) | Idioma principal | 'valenciano' |
| `idiomas_secundarios` | TEXT | Idiomas adicionales | '' |
| `intervalo_cambio` | INTEGER | Intervalo entre idiomas (seg) | 0 |

### Tabla `panel_languages`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL | Identificador único |
| `language_code` | VARCHAR(10) | Código de idioma (es, va, en, fr, de) |
| `language_name` | VARCHAR(50) | Nombre del idioma |
| `libre_text` | VARCHAR(50) | Texto para estado libre |
| `denso_text` | VARCHAR(50) | Texto para estado denso |
| `completo_text` | VARCHAR(50) | Texto para estado completo |

### Tabla `panel_api_config`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL | Identificador único |
| `api_url` | VARCHAR(255) | URL de la API REST |
| `api_timeout` | INTEGER | Timeout en segundos |
| `retry_attempts` | INTEGER | Número de reintentos |
| `retry_delay` | INTEGER | Delay entre reintentos |
| `enabled` | BOOLEAN | Estado habilitado/deshabilitado |

---

## 🔌 API REST de Paneles

### Endpoint Principal

**POST** `http://127.0.0.1:5656/sendMulti`

### Request Body

```json
{
  "ip": "172.20.4.52",
  "itemNum": 1,
  "texts": ["PANEL 3"],
  "colors": [1],
  "fontSizes": [2],
  "showEffects": [1]
}
```

### Parámetros

| Campo | Tipo | Descripción | Valores |
|-------|------|-------------|---------|
| `ip` | string | IP del panel destino | - |
| `itemNum` | int | Número de textos | - |
| `texts` | string[] | Array de textos | - |
| `colors` | int[] | Array de colores | 1=Rojo, 2=Verde, 3=Amarillo, 4=Azul, 5=Púrpura, 6=Azul oscuro, 7=Blanco |
| `fontSizes` | int[] | Array de tamaños | 1-5 |
| `showEffects` | int[] | Array de efectos | 0=Sin efecto, 1=Centrado, 2=Scroll, etc. |

### Response

```json
{
  "success": true,
  "message": "Sent successfully"
}
```

---

## 🐍 Servicio de Comunicación Python

### Clase `PanelCommunicationService`

```python
from panel_communication_service import PanelCommunicationService

# Crear instancia
service = PanelCommunicationService()

# Enviar texto personalizado
result = service.send_custom_text(
    panel_ip="172.20.4.52",
    text="PROVA PANEL",
    color=2,  # Verde
    font_size=2,
    effect=1  # Centrado
)

# Enviar estado de parking
result = service.send_parking_status(
    panel_ip="172.20.4.52",
    parking_name="PALAU",
    free_spaces=45,
    total_spaces=100,
    language_code='va'
)
```

### Métodos Principales

#### `send_text_to_panel()`
Envía texto personalizado a un panel específico.

#### `send_parking_status()`
Envía el estado actual del parking con formato automático.

#### `send_custom_text()`
Envía texto personalizado con configuración específica.

#### `test_connection()`
Prueba la conectividad con la API REST.

---

## 🎨 Configuraciones de Color

### Estados de Parking

| Estado | Porcentaje | Color | Código |
|--------|------------|-------|--------|
| Libre | < 50% | Verde | 2 |
| Denso | 50-90% | Amarillo | 3 |
| Completo | > 90% | Rojo | 1 |

### Colores Disponibles

| Código | Color |
|--------|-------|
| 1 | Rojo |
| 2 | Verde |
| 3 | Amarillo |
| 4 | Azul |
| 5 | Púrpura |
| 6 | Azul oscuro |
| 7 | Blanco |

---

## 🌍 Gestión de Idiomas

### Configuración por Panel

```sql
-- Ejemplo: Panel con múltiples idiomas
UPDATE panels 
SET 
    idioma_principal = 'valenciano',
    idiomas_secundarios = 'es,en',
    intervalo_cambio = 10
WHERE ip = '172.20.4.52';
```

### Textos por Idioma

| Idioma | Libre | Denso | Completo |
|--------|-------|-------|----------|
| Castellano | LIBRE | DENSO | COMPLETO |
| Valenciano | LLIURE | DENSA | COMPLET |
| Inglés | FREE | BUSY | FULL |
| Francés | LIBRE | OCCUPÉ | COMPLET |
| Alemán | FREI | BESETZT | VOLL |

---

## 🔧 Configuración de Múltiples Pantallas

### Ejemplos de Configuración

#### Panel de 1 Pantalla (64x16)
```sql
UPDATE panels 
SET num_pantallas = 1, resolucion_ancho = 64, resolucion_alto = 16
WHERE ip = '172.20.4.52';
```

#### Panel de 2 Pantallas (32x16 cada una)
```sql
UPDATE panels 
SET num_pantallas = 2, resolucion_ancho = 32, resolucion_alto = 16
WHERE ip = '172.20.4.53';
```

#### Panel de 3 Pantallas (64x16 cada una)
```sql
UPDATE panels 
SET num_pantallas = 3, resolucion_ancho = 64, resolucion_alto = 16
WHERE ip = '172.20.4.54';
```

### Envío a Múltiples Pantallas

```python
# Para panel de 2 pantallas
service.send_text_to_panel(
    panel_ip="172.20.4.53",
    texts=["PANTALLA 1", "PANTALLA 2"],
    colors=[2, 3],  # Verde y amarillo
    font_sizes=[2, 2],
    show_effects=[1, 1]  # Centrado en ambas
)
```

---

## 🚀 Despliegue

### Script de Actualización

```bash
# Ejecutar script de actualización
./deploy/update_panels_v2.6.sh
```

### Verificación

```bash
# Probar funcionalidad
python3 test/test_panel_v2.6.py
```

---

## 📊 Monitoreo y Logs

### Logs del Servicio

```bash
# Ver logs del servicio de paneles
journalctl -u parking-api -f
```

### Verificación de Estado

```python
# Verificar estado de la API
service = PanelCommunicationService()
result = service.test_connection()
print(f"API Status: {result}")
```

---

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión con API
```bash
# Verificar que el servicio esté corriendo
curl -X GET http://127.0.0.1:5656/health
```

#### 2. Error de Base de Datos
```bash
# Verificar migración
python3 src/update_database_panels_v2.6.py
```

#### 3. Panel No Responde
```bash
# Verificar conectividad de red
ping 172.20.4.52
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Panel Simple
```python
service = PanelCommunicationService()
service.send_custom_text(
    panel_ip="172.20.4.52",
    text="PARKING LLIURE",
    color=2,
    font_size=2,
    effect=1
)
```

### Ejemplo 2: Panel con Estado de Parking
```python
service.send_parking_status(
    panel_ip="172.20.4.52",
    parking_name="PALAU",
    free_spaces=25,
    total_spaces=100,
    language_code='va'
)
```

### Ejemplo 3: Panel Múltiple
```python
service.send_text_to_panel(
    panel_ip="172.20.4.53",
    texts=["PALAU", "25 LLIURES"],
    colors=[2, 2],
    font_sizes=[2, 2],
    show_effects=[1, 1]
)
```

---

## 🔄 Migración desde v2.5

### Cambios Automáticos
- Todos los paneles existentes se actualizan automáticamente
- Configuración por defecto: 1 pantalla, 64x16, Valenciano
- Fabricante: "Rótulos electrónicos"

### Configuración Manual Opcional
```sql
-- Personalizar panel específico
UPDATE panels 
SET 
    num_pantallas = 2,
    resolucion_ancho = 32,
    idioma_principal = 'es',
    idiomas_secundarios = 'va,en',
    intervalo_cambio = 15
WHERE ip = '172.20.4.52';
```

---

## 📞 Soporte

Para soporte técnico o consultas sobre la implementación de paneles v2.6, contactar con el equipo de desarrollo. 