# Pruebas de Endpoint de Cámaras - Parking Altea

## URL del Endpoint

```
POST http://157.180.91.63:6400/camera
```

## Ejemplo de Body JSON (formato completo)

```json
{
  "event": "Object Counting",
  "device": "ciutat_esportiva camera 1",
  "time": "2025-04-22 18:38:09",
  "line": 0,
  "Vehicle In": 163,
  "Vehicle Out": 312
}
```

## Ejemplo de Body JSON (mínimo requerido)

```json
{
  "device": "ciutat_esportiva camera 1",
  "line": 0,
  "Vehicle In": 163,
  "Vehicle Out": 312
}
```

## Ejemplo de Body JSON mal formado (para probar robustez)

```json
{"device": "ciutat_esportiva camera 1", "line": 0, "Vehicle In": 163, "Vehicle Out": 312,}
```

## Comandos de Prueba (desde el servidor)

### 1. Crear archivo JSON válido

```bash
echo '{"device": "ciutat_esportiva camera 1", "line": 0, "Vehicle In": 163, "Vehicle Out": 312}' > /tmp/test.json
```

### 2. Enviar petición con archivo JSON

```bash
curl -X POST http://localhost:6400/camera -H 'Content-Type: application/json' -d @/tmp/test.json
```

### 3. Enviar petición con JSON mal formado

```bash
echo '{"device": "ciutat_esportiva camera 1", "line": 0, "Vehicle In": 163, "Vehicle Out": 312,}' > /tmp/test_bad.json
curl -X POST http://localhost:6400/camera -H 'Content-Type: application/json' -d @/tmp/test_bad.json
```

### 4. Enviar petición con todos los campos

```bash
echo '{"event": "Object Counting", "device": "ciutat_esportiva camera 1", "time": "2025-04-22 18:38:09", "line": 0, "Vehicle In": 163, "Vehicle Out": 312}' > /tmp/test_full.json
curl -X POST http://localhost:6400/camera -H 'Content-Type: application/json' -d @/tmp/test_full.json
```

## Ver logs en tiempo real para comprobar llegada de datos

```bash
journalctl -u parking-camera -f
```

Esto mostrará en tiempo real los logs del servicio de cámaras y permitirá ver si llegan correctamente los datos y cómo los procesa el sistema. 