# Proceso de Despliegue y Actualización

## 1. Información del Servidor de Producción

| Elemento | Valor |
|----------|-------|
| Hostname | `ubuntu-16gb-hel1-1` |
| IP | (Configurar según entorno) |
| OS | Ubuntu 22.04 LTS |
| Usuario | root |
| Directorio proyecto | `/opt/parking_altea` |
| Repositorio | `https://github.com/Swat-id/parking_altea` |
| Rama principal | `v4.5.0` |

## 2. Estructura en Servidor

```
/opt/
├── parking_altea/          # Proyecto principal
│   ├── src/
│   ├── client/
│   ├── docs/
│   ├── venv/               # Entorno virtual Python
│   ├── .env                # Variables de entorno
│   └── requirements.txt
│
├── panelSender/            # SDK Java para paneles antiguos
│   ├── main.py
│   ├── sender_oldProtocol/
│   └── venv/
│
/var/log/
├── panel_worker.log        # Log del worker
├── panel_type3_4_worker.log
└── nginx/
    ├── access.log
    └── error.log
```

## 3. Proceso de Actualización Estándar

### 3.1 Script de Actualización Completo

```bash
#!/bin/bash
# Script: update_parking_altea.sh
# Ubicación: /opt/parking_altea/scripts/

set -e  # Detener en caso de error

echo "=== INICIANDO ACTUALIZACIÓN PARKING ALTEA ==="
echo "Fecha: $(date)"

# 1. Ir al directorio del proyecto
cd /opt/parking_altea

# 2. Obtener últimos cambios
echo ">>> Obteniendo cambios de Git..."
git fetch origin v4.5.0
git pull origin v4.5.0

# 3. Limpiar caché de Python
echo ">>> Limpiando caché de Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 4. Activar entorno virtual y actualizar dependencias
echo ">>> Actualizando dependencias..."
source venv/bin/activate
pip install -r requirements.txt --quiet

# 5. Reiniciar servicios systemd
echo ">>> Reiniciando servicios systemd..."
sudo systemctl restart parking-api.service
sudo systemctl restart parking-panel-protocol.service
sudo systemctl restart parking-schedule-monitor.service
# Opcional: panelsender si hubo cambios
# sudo systemctl restart panelsender.service

# 6. Reiniciar workers
echo ">>> Reiniciando workers..."
pkill -9 -f panel_worker_service.py 2>/dev/null || true
pkill -9 -f panel_type3_and_4_worker_service.py 2>/dev/null || true
sleep 2

nohup /opt/parking_altea/venv/bin/python /opt/parking_altea/src/panel_worker_service.py --interval 120 >> /var/log/panel_worker.log 2>&1 &
nohup /opt/parking_altea/venv/bin/python /opt/parking_altea/src/panel_type3_and_4_worker_service.py --interval 120 >> /var/log/panel_type3_4_worker.log 2>&1 &

sleep 3

# 7. Verificar estado
echo ">>> Verificando estado de servicios..."
systemctl is-active --quiet parking-api.service && echo "parking-api: OK" || echo "parking-api: ERROR"
systemctl is-active --quiet parking-panel-protocol.service && echo "parking-panel-protocol: OK" || echo "parking-panel-protocol: ERROR"

ps aux | grep panel_worker | grep -v grep && echo "panel_worker: OK" || echo "panel_worker: ERROR"
ps aux | grep type3_and_4 | grep -v grep && echo "panel_type3_4_worker: OK" || echo "panel_type3_4_worker: ERROR"

echo "=== ACTUALIZACIÓN COMPLETADA ==="
echo "Verificar logs: journalctl -u parking-api.service -f"
```

### 3.2 Comandos Manuales Paso a Paso

```bash
# 1. Conectar al servidor
ssh root@servidor

# 2. Ir al proyecto
cd /opt/parking_altea

# 3. Obtener cambios
git pull origin v4.5.0

# 4. Limpiar caché
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# 5. Reiniciar servicios
sudo systemctl restart parking-api.service
sudo systemctl restart parking-panel-protocol.service
sudo systemctl restart parking-schedule-monitor.service

# 6. Reiniciar workers
pkill -9 -f panel_worker_service.py
pkill -9 -f panel_type3_and_4_worker_service.py
sleep 2
nohup /opt/parking_altea/venv/bin/python /opt/parking_altea/src/panel_worker_service.py --interval 120 >> /var/log/panel_worker.log 2>&1 &
nohup /opt/parking_altea/venv/bin/python /opt/parking_altea/src/panel_type3_and_4_worker_service.py --interval 120 >> /var/log/panel_type3_4_worker.log 2>&1 &

# 7. Verificar
ps aux | grep -E "panel_worker|type3" | grep -v grep
```

## 4. Actualización del Frontend

```bash
# 1. Ir al directorio del cliente
cd /opt/parking_altea/client

# 2. Instalar dependencias
npm install

# 3. Construir para producción
npm run build

# 4. Reiniciar Nginx (si es necesario)
sudo systemctl reload nginx
```

## 4.1 Credenciales de Administración

| Servicio | Usuario | Contraseña |
|----------|---------|------------|
| API Backend | info@swat-id.com | Swat2025! |

**Obtener token JWT:**
```bash
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"info@swat-id.com","password":"Swat2025!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
echo "Token: ${TOKEN:0:50}..."
```

**Enviar mensaje a panel (ejemplo):**
```bash
curl -X POST http://localhost:7110/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"panel_ip":"172.20.4.53","panel_port":5200,"window_id":0,"text":".","color":1,"font_size":2,"effect":0,"alignment":1,"speed":5,"stay_time":50,"card_id":1}'
```

## 5. Verificación Post-Despliegue

### 5.1 Verificar Servicios

```bash
# Estado de todos los servicios
for service in parking-api parking-panel-protocol panelsender parking-schedule-monitor; do
    status=$(systemctl is-active ${service}.service 2>/dev/null || echo "not-found")
    echo "${service}: ${status}"
done

# Estado de workers
ps aux | grep -E "panel_worker|type3_and_4" | grep -v grep

# Puertos en uso
netstat -tlnp | grep -E "6001|7110|8888|3535"
```

### 5.2 Verificar Logs

```bash
# Ver últimos errores de la API
sudo journalctl -u parking-api.service -n 50 --no-pager | grep -E "ERROR|Error"

# Ver envíos a paneles
sudo journalctl -u parking-api.service -n 50 --no-pager | grep -E "ROUTING|exitosamente"

# Ver logs del worker
tail -50 /var/log/panel_worker.log | grep -E "ERROR|ROUTING"
```

### 5.3 Probar Funcionalidad

```bash
# Probar API
curl -s http://localhost:6001/api/health | jq .

# Probar protocolo nuevo
curl -X POST http://localhost:7110/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -d '{"panel_ip":"172.20.4.51","panel_port":5200,"window_id":0,"text":"TEST","color":1,"font_size":2,"effect":0,"alignment":1,"speed":5,"stay_time":3,"card_id":1}'

# Ejecutar una programación manualmente
curl -X POST "http://localhost:6001/api/schedules/71/execute" \
  -H "Content-Type: application/json"
```

## 6. Rollback

### 6.1 Volver a Versión Anterior

```bash
# 1. Ir al directorio
cd /opt/parking_altea

# 2. Ver commits recientes
git log --oneline -10

# 3. Volver a commit específico
git checkout <commit_hash>
# o volver a tag anterior
git checkout v4.4.0

# 4. Reiniciar servicios (mismo proceso que actualización)
sudo systemctl restart parking-api.service
# ... resto de servicios y workers
```

### 6.2 Backup Antes de Actualizar

```bash
# Crear backup de la base de datos
sudo -u postgres pg_dump parking_db > /opt/backups/parking_db_$(date +%Y%m%d_%H%M%S).sql

# Crear backup del código
cp -r /opt/parking_altea /opt/backups/parking_altea_$(date +%Y%m%d_%H%M%S)
```

## 7. Migraciones de Base de Datos

### 7.1 Aplicar Migraciones

```bash
# Activar entorno virtual
source /opt/parking_altea/venv/bin/activate

# Ejecutar migraciones (si se usa Alembic)
alembic upgrade head

# O ejecutar SQL manualmente
sudo -u postgres psql -d parking_db -f /opt/parking_altea/src/migrations/migration_xxx.sql
```

### 7.2 Crear Nueva Migración

```bash
# Con Alembic
alembic revision --autogenerate -m "descripcion_cambio"

# Verificar la migración generada
cat /opt/parking_altea/src/migrations/versions/xxx_descripcion_cambio.py
```

## 8. Configuración de Servicios Systemd

### 8.1 Crear/Editar Servicio

```bash
# Editar servicio
sudo nano /etc/systemd/system/parking-api.service

# Recargar configuración de systemd
sudo systemctl daemon-reload

# Reiniciar servicio
sudo systemctl restart parking-api.service

# Habilitar inicio automático
sudo systemctl enable parking-api.service
```

### 8.2 Ejemplo de Archivo de Servicio

```ini
# /etc/systemd/system/parking-api.service
[Unit]
Description=Parking API Server
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea/src
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/parking_altea/venv/bin/python api_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 9. Troubleshooting Común

### 9.1 Servicio No Inicia

```bash
# Ver logs detallados
sudo journalctl -u parking-api.service -n 100 --no-pager

# Verificar sintaxis del archivo de servicio
systemctl cat parking-api.service

# Probar ejecutar manualmente
cd /opt/parking_altea/src
/opt/parking_altea/venv/bin/python api_server.py
```

### 9.2 Worker No Se Reinicia

```bash
# Matar todos los procesos del worker
pkill -9 -f panel_worker_service.py

# Verificar que no quedan procesos
ps aux | grep panel_worker

# Iniciar manualmente y ver salida
cd /opt/parking_altea
/opt/parking_altea/venv/bin/python src/panel_worker_service.py --interval 120
# Ctrl+C para parar y luego iniciar en background
```

### 9.3 Puerto en Uso

```bash
# Ver qué proceso usa el puerto
sudo lsof -i :6001

# Matar proceso si es necesario
kill -9 <PID>
```

### 9.4 Error de Conexión a BD

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Probar conexión
sudo -u postgres psql -d parking_db -c "SELECT 1;"

# Verificar configuración
cat /opt/parking_altea/.env | grep DB_
```

## 10. Checklist de Despliegue

```markdown
### Pre-despliegue
- [ ] Backup de base de datos realizado
- [ ] Backup de código realizado
- [ ] Comunicación al equipo sobre ventana de mantenimiento

### Durante despliegue
- [ ] Git pull exitoso
- [ ] Caché de Python limpiada
- [ ] Dependencias actualizadas (si hay nuevas)
- [ ] Servicios systemd reiniciados
- [ ] Workers reiniciados
- [ ] Migraciones de BD aplicadas (si hay)

### Post-despliegue
- [ ] Todos los servicios corriendo
- [ ] Todos los workers corriendo
- [ ] Logs sin errores críticos
- [ ] Test de funcionalidad básica pasado
- [ ] Paneles mostrando información correcta

### Rollback (si es necesario)
- [ ] Revertir código a versión anterior
- [ ] Restaurar base de datos (si se modificó)
- [ ] Reiniciar todos los servicios
```

---

*Anterior: [05-flujos-principales.md](./05-flujos-principales.md)*

---

*Documentación generada: Marzo 2026*
*Versión de la plataforma: v4.7*
