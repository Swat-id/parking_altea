# Endpoint de Estado de Parkings - Documentación

## Descripción

El endpoint `/parkings/status` proporciona información completa del estado de todos los parkings del sistema, incluyendo ocupación, estado de paneles y mensajes programados.

## URL del Endpoint

```
GET http://157.180.91.63:6001/parkings/status
```

## Configuración del Servidor

### Servicio
- **Nombre**: `parking-api.service`
- **Puerto**: `6001`
- **Bind**: `0.0.0.0:6001` (accesible desde cualquier IP)
- **Proceso**: Gunicorn con 3 workers

### Firewall
- **Estado**: Activo
- **Puerto 6001**: Permitido para cualquier origen
- **Configuración**: `6001/tcp ALLOW Anywhere`

### Verificación de Estado
```bash
# Verificar servicio
systemctl status parking-api

# Verificar puerto
netstat -tlnp | grep :6001

# Verificar firewall
ufw status | grep 6001
```

## Respuesta del Endpoint

### Estructura JSON
```json
{
  "success": true,
  "total_parkings": 9,
  "timestamp": "2025-07-03T23:36:54.908470",
  "parkings": [
    {
      "id": 4,
      "name": "4 - P. Poble antic/Belles Arts 2",
      "location": "38.59970515205105,-0.05619330432336512",
      "total_plazas": 45,
      "plazas_ocupadas": 37,
      "plazas_libres": 8,
      "estado": "LIBRE",
      "estado_valenciano": "LLIURE",
      "panel_display_text": "LLIURE",
      "has_active_schedules": false,
      "active_schedules_count": 0,
      "threshold_dense": 5,
      "threshold_full": 2,
      "panels": [
        {
          "id": 7,
          "ip": "172.20.4.52",
          "name": "BELLES ARTS 2",
          "protocol_version": "old",
          "status": "ONLINE",
          "last_message": "TEST CURL",
          "last_update": "2025-07-02T11:47:55.603479"
        }
      ],
      "last_update": "2025-07-03T23:36:54.908470"
    }
  ]
}
```

### Campos de Información

#### Información General del Parking
- `id`: ID único del parking
- `name`: Nombre del parking
- `location`: Coordenadas GPS (latitud,longitud)
- `total_plazas`: Capacidad máxima del parking
- `plazas_ocupadas`: Número de plazas ocupadas actualmente
- `plazas_libres`: Número de plazas libres actualmente

#### Estados del Parking
- `estado`: Estado en español (LIBRE, DENSO, COMPLETO)
- `estado_valenciano`: Estado en valenciano (LLIURE, DENS, COMPLET)
- `panel_display_text`: Texto que se está mostrando en los paneles
- `has_active_schedules`: Si hay programaciones activas
- `active_schedules_count`: Número de programaciones activas

#### Configuración
- `threshold_dense`: Umbral para estado DENSO
- `threshold_full`: Umbral para estado COMPLETO

#### Información de Paneles
- `panels`: Array con información de cada panel
  - `id`: ID del panel
  - `ip`: IP del panel
  - `name`: Nombre del panel
  - `protocol_version`: Protocolo (old/new)
  - `status`: Estado del panel (ONLINE/OFFLINE)
  - `last_message`: Último mensaje enviado
  - `last_update`: Última actualización

## Lógica de Funcionamiento

### Determinación del Texto en Paneles
1. **Si hay programaciones activas**: Se muestra el mensaje de la programación
2. **Si no hay programaciones**: Se muestra el estado en valenciano

### Estados del Parking
- **LIBRE**: Cuando hay más plazas libres que `threshold_dense`
- **DENSO**: Cuando las plazas libres están entre `threshold_full` y `threshold_dense`
- **COMPLETO**: Cuando las plazas libres son menores o iguales a `threshold_full`

### Protocolos de Paneles
- **Protocolo antiguo**: Usa servicio Java (puerto 5656)
- **Protocolo nuevo**: Usa servicio Node.js (puerto 3001/5657)

## Pruebas de Acceso

### Desde el Servidor Local
```bash
curl -X GET http://127.0.0.1:6001/parkings/status
```

### Desde el Exterior
```bash
curl -X GET http://157.180.91.63:6001/parkings/status
```

### Script de Prueba
```bash
python3 test_external_access.py
```

## Ejemplos de Uso

### Obtener Estado de un Parking Específico
```bash
curl -s http://157.180.91.63:6001/parkings/status | \
python3 -c "import json, sys; data=json.load(sys.stdin); \
parking = next((p for p in data['parkings'] if p['name'] == '4 - P. Poble antic/Belles Arts 2'), None); \
print(f'Parking: {parking[\"name\"]}'); \
print(f'Estado: {parking[\"estado\"]} ({parking[\"estado_valenciano\"]})'); \
print(f'Panel: {parking[\"panel_display_text\"]}'); \
print(f'Ocupación: {parking[\"plazas_ocupadas\"]}/{parking[\"total_plazas\"]}')"
```

### Monitoreo en Tiempo Real
```bash
watch -n 30 'curl -s http://157.180.91.63:6001/parkings/status | python3 format_response.py'
```

## Troubleshooting

### Problemas Comunes

#### 1. Endpoint No Responde
```bash
# Verificar servicio
systemctl status parking-api

# Verificar puerto
netstat -tlnp | grep :6001

# Reiniciar servicio
systemctl restart parking-api
```

#### 2. Error de Conexión
```bash
# Verificar firewall
ufw status | grep 6001

# Verificar conectividad
telnet 157.180.91.63 6001
```

#### 3. Error de Formato JSON
```bash
# Verificar respuesta
curl -s http://157.180.91.63:6001/parkings/status | python3 -m json.tool
```

## Seguridad

- El endpoint es de solo lectura (GET)
- No requiere autenticación para consultas públicas
- Los datos sensibles (IPs internas) están expuestos solo para paneles
- Se recomienda usar HTTPS en producción

## Mantenimiento

### Reiniciar el Servicio
```bash
systemctl restart parking-api
```

### Verificar Logs
```bash
journalctl -u parking-api -f
```

### Actualizar Código
```bash
cd /opt/parking_altea
git pull origin v3.0.0
systemctl restart parking-api
``` 