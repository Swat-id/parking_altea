# 📘 MANUAL DE DESPLIEGUE Y USO

## 📌 Requisitos

- Ubuntu 22.04 o superior
- Python 3.10+

## 📌 Instalación

Clona o descomprime este proyecto en la ruta que quieras, por ejemplo:

```
/opt/led-service
```

Instala las dependencias:

```
cd /opt/led-service
pip install -r requirements.txt
```

## 📌 Ejecución en desarrollo

```
uvicorn led_service.server:app --host 0.0.0.0 --port 8000
```

Accede a la documentación automática:

- Swagger: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 📌 Configuración del servicio (Systemd)

Crea este archivo:

```
sudo nano /etc/systemd/system/led-service.service
```

Contenido recomendado:

```
[Unit]
Description=LED Panel Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/led-service
ExecStart=/usr/bin/uvicorn led_service.server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Recarga systemd y habilita:

```
sudo systemctl daemon-reload
sudo systemctl enable led-service
sudo systemctl start led-service
sudo systemctl status led-service
```

## 📌 Pruebas de la API

```
curl -X POST "http://localhost:8000/send-text" -H "Content-Type: application/json" -d '{
  "window_no": 1,
  "mode": 0,
  "alignment": 0,
  "speed": 10,
  "stay_time": 5,
  "text": "Hola mundo"
}'
```

Respuesta típica:

```json
{
  "status": "sent",
  "response": "..."
}
```

## 📌 Variables de configuración

Edita `led_service/server.py` para definir:

- NETWORK_ID
- CARD_ID
- PANEL_IP
- PANEL_PORT

## 📌 Logs y monitoreo

```
journalctl -u led-service -f
```

Para reiniciar:

```
sudo systemctl restart led-service
```

## 📌 Personalización

- Añade más comandos en protocol.py
- Crea más endpoints en server.py
