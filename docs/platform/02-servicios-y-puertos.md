# Servicios y Puertos

## 1. Mapa de Puertos

| Puerto | Servicio | Protocolo | Descripción |
|--------|----------|-----------|-------------|
| 5200 | Paneles LED | TCP | Puerto de comunicación con paneles físicos |
| 6001 | parking-api | HTTP | API REST principal |
| 7110 | parking-panel-protocol | HTTP | API protocolo nuevo (Python directo) |
| 8888 | panelsender | HTTP | API protocolo antiguo (SDK Java) |
| 3535 | camera-server | HTTP | Servidor de eventos de cámaras |
| 3210 | panel-v4-server | HTTP | Servidor protocolo v4 (16 ventanas) |
| 6400 | - | HTTP | Servicio auxiliar |
| 6401 | - | HTTP | Servicio auxiliar |
| 7777 | - | HTTP | Servicio auxiliar |
| 15000 | nginx (frontend) | HTTP | Servidor web frontend React |
| 5432 | postgresql | TCP | Base de datos |

## 2. Servicios Systemd

### 2.1 parking-api.service
```ini
[Unit]
Description=Parking API Server
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea/src
ExecStart=/opt/parking_altea/venv/bin/python api_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
sudo systemctl status parking-api.service
sudo systemctl restart parking-api.service
sudo journalctl -u parking-api.service -f
```

### 2.2 parking-panel-protocol.service
```ini
[Unit]
Description=Parking Panel Protocol Service v4.3.0
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea/src
ExecStartPre=/bin/sleep 5
ExecStart=/opt/parking_altea/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:7110 --timeout 120 --max-requests 1000 --preload panel_protocol_service:app
Restart=always
MemoryMax=512M

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
sudo systemctl status parking-panel-protocol.service
sudo systemctl restart parking-panel-protocol.service
sudo journalctl -u parking-panel-protocol.service -f
```

### 2.3 panelsender.service
```ini
[Unit]
Description=PanelSender Service (SDK Java)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/panelSender
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
sudo systemctl status panelsender.service
sudo systemctl restart panelsender.service
sudo journalctl -u panelsender.service -f
```

### 2.4 parking-schedule-monitor.service
```ini
[Unit]
Description=Parking Altea Schedule Monitor Service
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea/src
ExecStart=/opt/parking_altea/venv/bin/python schedule_monitor_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 3. Workers (Procesos en Background)

### 3.1 Panel Worker Service
**Ubicación**: `src/panel_worker_service.py`

**Inicio manual:**
```bash
cd /opt/parking_altea
nohup /opt/parking_altea/venv/bin/python src/panel_worker_service.py --interval 120 >> /var/log/panel_worker.log 2>&1 &
```

**Verificar:**
```bash
ps aux | grep panel_worker
tail -f /var/log/panel_worker.log
```

**Matar:**
```bash
pkill -9 -f panel_worker_service.py
```

### 3.2 Panel Type 3/4 Worker Service
**Ubicación**: `src/panel_type3_and_4_worker_service.py`

**Inicio manual:**
```bash
cd /opt/parking_altea
nohup /opt/parking_altea/venv/bin/python src/panel_type3_and_4_worker_service.py --interval 120 >> /var/log/panel_type3_4_worker.log 2>&1 &
```

**Verificar:**
```bash
ps aux | grep type3
tail -f /var/log/panel_type3_4_worker.log
```

## 4. Verificación de Estado

### Script de verificación completa
```bash
#!/bin/bash
echo "=== Estado de Servicios Parking Altea ==="

echo -e "\n--- Servicios Systemd ---"
for service in parking-api parking-panel-protocol panelsender parking-schedule-monitor; do
    status=$(systemctl is-active ${service}.service 2>/dev/null || echo "not-found")
    echo "${service}: ${status}"
done

echo -e "\n--- Workers ---"
ps aux | grep -E "panel_worker|type3_and_4" | grep -v grep | awk '{print $11, $12}'

echo -e "\n--- Puertos en uso ---"
netstat -tlnp 2>/dev/null | grep -E "6001|7110|8888|3535|5432" | awk '{print $4, $7}'

echo -e "\n--- Conexión BD ---"
sudo -u postgres psql -d parking_db -c "SELECT 1;" > /dev/null 2>&1 && echo "PostgreSQL: OK" || echo "PostgreSQL: ERROR"
```

## 5. Logs

| Servicio | Ubicación Log |
|----------|---------------|
| parking-api | `journalctl -u parking-api.service` |
| parking-panel-protocol | `journalctl -u parking-panel-protocol.service` |
| panelsender | `journalctl -u panelsender.service` |
| panel-worker | `/var/log/panel_worker.log` |
| panel-type3-4-worker | `/var/log/panel_type3_4_worker.log` |
| schedule-monitor | `journalctl -u parking-schedule-monitor.service` |
| nginx | `/var/log/nginx/access.log`, `/var/log/nginx/error.log` |

### Comandos útiles de logs
```bash
# Ver logs en tiempo real de un servicio
sudo journalctl -u parking-api.service -f

# Ver últimas 100 líneas
sudo journalctl -u parking-api.service -n 100 --no-pager

# Filtrar por patrón
sudo journalctl -u parking-api.service | grep -E "ERROR|ROUTING"

# Ver logs de hoy
sudo journalctl -u parking-api.service --since today
```

## 6. Dependencias entre Servicios

```
┌─────────────────────┐
│     PostgreSQL      │
│    (puerto 5432)    │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌─────────────┐
│ parking │  │   Workers   │
│   api   │  │ (panel,     │
│ (6001)  │  │  type3/4,   │
└────┬────┘  │  schedule)  │
     │       └──────┬──────┘
     │              │
     └──────┬───────┘
            ▼
┌───────────────────────────┐
│   panel_communication_    │
│        service.py         │
└───────────┬───────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌─────────┐    ┌─────────┐
│  7110   │    │  8888   │
│ (nuevo) │    │(antiguo)│
└────┬────┘    └────┬────┘
     │              │
     └──────┬───────┘
            ▼
┌───────────────────────────┐
│    Paneles LED (5200)     │
└───────────────────────────┘
```

---

*Anterior: [01-descripcion-general.md](./01-descripcion-general.md)*
*Siguiente: [03-estructura-directorios.md](./03-estructura-directorios.md)*
