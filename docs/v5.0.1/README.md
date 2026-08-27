# v5.0.1 — Reenvío de ingestión a parking-monitor

**Rama**: `v5.0.1` (desde `v5.0.0`)  
**Alcance**: solo los tres servicios que reciben POST de dispositivos. API 6001, paneles y workers no cambian.

## Qué hace

Al llegar un mensaje de cámara o sensor, el servicio **copia el body HTTP tal cual** (bytes + `Content-Type`) hacia parking-monitor y **sigue procesando en local** igual que en v5.0.0. El reenvío corre en un hilo daemon: no espera respuesta y un fallo remoto no altera el aforo ni la respuesta al dispositivo.

## Destinos

| Origen | Endpoint local | Destino |
|--------|----------------|---------|
| Cruce de línea | `POST :6400/camera` | `https://parking-monitor.swat-id.com/api/ingest/line-count` |
| Cámara plaza a plaza | `POST :6401/detection` | `https://parking-monitor.swat-id.com/api/ingest/spot` |
| Sensor de plaza | `POST :3535/push` y `POST :3535/` | `https://parking-monitor.swat-id.com/api/ingest/sensor` |

No se reenvían: GET health/stats ni `POST :3535/manual-update`.

## Código

- [`src/ingest_forwarder.py`](../../src/ingest_forwarder.py) — reenvío asíncrono
- [`src/config.py`](../../src/config.py) — URLs, timeout y flag
- Enganches: `camera_server.py`, `spot_detection_server.py`, `sensor_push_service.py`

El body **no** se re-serializa con `json.dumps`; se usa `request.get_data()`.

## Variables de entorno

| Variable | Default |
|----------|---------|
| `INGEST_FORWARD_ENABLED` | `true` |
| `INGEST_FORWARD_TIMEOUT` | `3` (segundos) |
| `INGEST_FORWARD_LINE_COUNT_URL` | `https://parking-monitor.swat-id.com/api/ingest/line-count` |
| `INGEST_FORWARD_SPOT_URL` | `https://parking-monitor.swat-id.com/api/ingest/spot` |
| `INGEST_FORWARD_SENSOR_URL` | `https://parking-monitor.swat-id.com/api/ingest/sensor` |

Para desactivar el reenvío sin revertir código: `INGEST_FORWARD_ENABLED=false`.

## Despliegue

```bash
cd /opt/parking_altea
git fetch origin
git checkout v5.0.1
git pull

systemctl restart parking-camera
systemctl restart parking-spot-detection
systemctl restart parking-sensor-push
```

Comprobar logs: `Ingest forward OK` o `Ingest forward falló`. El procesamiento local debe continuar en ambos casos.
