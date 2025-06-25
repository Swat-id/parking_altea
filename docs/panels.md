# Comunicación con Paneles Electrónicos

## Información General

El sistema envía automáticamente información de ocupación y mensajes personalizados a los paneles electrónicos ubicados en cada aparcamiento. La comunicación se realiza mediante HTTP POST a cada panel individual.

## Arquitectura de Comunicación

```
┌─────────────────┐    HTTP POST    ┌─────────────────┐
│   Sistema       │ ──────────────► │   Panel 1       │
│   Parking       │                 │   172.20.17.50  │
│                 │                 └─────────────────┘
│                 │
│                 │    HTTP POST    ┌─────────────────┐
│                 │ ──────────────► │   Panel 2       │
│                 │                 │   172.20.5.50   │
│                 │                 └─────────────────┘
└─────────────────┘
```

## Protocolo de Comunicación

### Endpoint del Panel
- **URL**: `http://{IP_PANEL}/update`
- **Método**: POST
- **Content-Type**: `application/json`
- **Timeout**: 5 segundos

### Formato del Mensaje

```json
{
  "message": "1 - P. Ciutat Esportiva: 250 libres (LIBRE)"
}
```

## Tipos de Mensajes

### 1. Mensaje de Estado Automático

Se envía automáticamente cuando cambia la ocupación del aparcamiento:

**Formato**: `{nombre_parking}: {plazas_libres} libres ({estado})`

**Ejemplos**:
- `"1 - P. Ciutat Esportiva: 250 libres (LIBRE)"`
- `"2 - P. Basseta Centre: 50 libres (DENSO)"`
- `"3 - P. Poble antic/Belles Arts 1: 0 libres (OCUPADO)"`

### 2. Mensaje Personalizado

Se envía cuando hay un mensaje programado activo:

**Formato**: El mensaje personalizado configurado

**Ejemplos**:
- `"Mantenimiento programado"`
- `"Cerrado por obras"`
- `"Evento especial - Parking completo"`

## Configuración de Paneles

### Paneles Registrados

| Parking | Nombre | IP | Descripción |
|---------|--------|----|-------------|
| 1 - P. Ciutat Esportiva | PANEL C. ESPORTIVA | 172.20.17.50 | Panel principal |
| 2 - P. Basseta Centre | PANEL BASSETA 1 | 172.20.5.50 | Panel entrada |
| 2 - P. Basseta Centre | PANEL BASSETA 2 | 172.20.5.51 | Panel salida |
| 6 - P. Poble antic/Conservatori | PANEL PITERES | 172.20.8.50 | Panel único |
| 5 - P. Poble antic/Palau Altea | PANEL PALAU | 172.20.4.50 | Panel principal |
| 5 - P. Poble antic/Palau Altea | PANEL COCOLISO | 172.20.4.51 | Panel secundario |
| 4 - P. Poble antic/Belles Arts 2 | BELLES ARTS 2 | 172.20.4.52 | Panel único |
| 3 - P. Poble antic/Belles Arts 1 | BELLES ARTS | 172.20.4.53 | Panel único |
| 8 - P. Estació Altea | PANEL RENFE | 172.20.2.50 | Panel estación |
| 9 - P. Altea la Vella | PANEL ALTEA VELLA | 172.20.1.50 | Panel único |

## Lógica de Envío

### 1. Actualización Automática

Se envía automáticamente cuando:
- Cambia la ocupación del aparcamiento (mensaje de cámara)
- Se actualiza manualmente la ocupación
- No hay mensaje fijo activo (`fixed_message_flag = false`)

### 2. Mensaje Fijo

Cuando `fixed_message_flag = true`:
- Se detiene el envío de mensajes automáticos
- Se puede enviar mensaje personalizado
- Útil para mantenimientos o eventos especiales

### 3. Mensajes Programados

Los mensajes programados tienen prioridad sobre los automáticos:
- Se verifica si hay mensaje activo en el rango de fechas
- Si existe, se envía el mensaje programado
- Si no, se envía el mensaje automático

## Implementación Técnica

### Función de Envío

```python
def send_to_panel(panel_ip: str, text: str) -> bool:
    try:
        payload = {'message': text}
        r = requests.post(
            f'http://{panel_ip}/update', 
            json=payload, 
            timeout=5
        )
        return r.status_code == 200
    except Exception:
        return False
```

### Función de Broadcast

```python
def broadcast(parking, message: str):
    for panel in parking.panels:
        send_to_panel(panel.ip, message)
```

## Estados de Aparcamiento

### Cálculo de Estados

- **LIBRE**: `occupancy < threshold_dense`
- **DENSO**: `threshold_dense ≤ occupancy < threshold_full`
- **OCUPADO**: `occupancy ≥ threshold_full`

### Umbrales por Aparcamiento

| Parking | Umbral Denso | Umbral Completo |
|---------|--------------|-----------------|
| 1 - P. Ciutat Esportiva | 25 | 5 |
| 2 - P. Basseta Centre | 25 | 5 |
| 3 - P. Poble antic/Belles Arts 1 | 25 | 5 |
| 4 - P. Poble antic/Belles Arts 2 | 5 | 5 |
| 5 - P. Poble antic/Palau Altea | 10 | 4 |
| 6 - P. Poble antic/Conservatori | 10 | 4 |
| 7 - P. Port Altea | 10 | 4 |
| 8 - P. Estació Altea | 10 | 4 |
| 9 - P. Altea la Vella | 10 | 4 |

## Gestión de Errores

### Timeout de Conexión
- **Timeout**: 5 segundos por panel
- **Comportamiento**: Si un panel no responde, se continúa con el siguiente
- **Log**: Se registra el error pero no se detiene el proceso

### Panel No Disponible
- **Comportamiento**: Se ignora el panel y se continúa
- **Recuperación**: Se reintenta en el siguiente envío automático
- **Monitoreo**: Se pueden revisar logs para detectar paneles problemáticos

### Múltiples Paneles
- **Envío Paralelo**: Se envían mensajes a todos los paneles del aparcamiento
- **Independencia**: El fallo de un panel no afecta a los demás
- **Redundancia**: Múltiples paneles por aparcamiento para mayor fiabilidad

## Ejemplos de Uso

### Envío Manual de Mensaje

```python
# Enviar mensaje a todos los paneles de un aparcamiento
parking = session.query(Parking).get(1)
broadcast(parking, "Mantenimiento programado")
```

### Verificar Estado de Panel

```python
# Verificar si un panel responde
success = send_to_panel("172.20.17.50", "Test")
if success:
    print("Panel responde correctamente")
else:
    print("Panel no disponible")
```

## Configuración de Paneles

### Requisitos del Panel
- **Protocolo**: HTTP REST
- **Endpoint**: `/update`
- **Método**: POST
- **Formato**: JSON
- **Campo**: `message` (string)

### Configuración de Red
- **IP**: Configurada en la base de datos
- **Puerto**: 80 (HTTP) o 443 (HTTPS)
- **Acceso**: Desde el servidor del sistema
- **Firewall**: Permitir conexiones desde `157.180.91.63`

## Monitoreo y Mantenimiento

### Logs de Comunicación
- Se registran todos los intentos de envío
- Se registran errores de timeout y conexión
- Se mantiene estadística de éxito/fallo por panel

### Verificación de Estado
```bash
# Verificar si un panel responde
curl -X POST http://172.20.17.50/update \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}'
```

### Troubleshooting

#### Panel No Responde
1. Verificar conectividad de red
2. Verificar que el panel esté encendido
3. Verificar configuración IP del panel
4. Revisar logs del sistema

#### Mensajes No Se Actualizan
1. Verificar que `fixed_message_flag = false`
2. Verificar que no hay mensajes programados activos
3. Verificar que la ocupación está cambiando
4. Revisar logs de comunicación

#### Múltiples Paneles Fallan
1. Verificar conectividad de red general
2. Verificar configuración de firewall
3. Verificar que el servidor puede acceder a la red de paneles 