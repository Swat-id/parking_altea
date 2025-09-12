# Comandos de Despliegue Rápido v4.0.0

## 🚀 Secuencia Completa de Comandos

### Copiar y ejecutar comando por comando en el servidor:

```bash
# ===== CONEXIÓN Y PREPARACIÓN =====
ssh root@157.180.91.63
cd /opt/parking

# ===== BACKUP =====
mkdir -p /opt/parking/backups/$(date +%Y%m%d)
cp src/camera_server.py /opt/parking/backups/$(date +%Y%m%d)/camera_server.py.backup.$(date +%H%M%S)
systemctl status parking-camera.service

# ===== ACTUALIZACIÓN GIT =====
git status
git stash
git checkout v4.0.0
git pull origin v4.0.0
git log --oneline -3

# ===== VERIFICACIÓN ARCHIVOS =====
ls -la src/camera_server.py
ls -la deploy/deploy_v4_0_0_nueva_logica_deltas.sh
ls -la deploy/test_v4_0_0_camera_server.sh

# ===== PREPARACIÓN SCRIPTS =====
chmod +x deploy/deploy_v4_0_0_nueva_logica_deltas.sh
chmod +x deploy/test_v4_0_0_camera_server.sh

# ===== DESPLIEGUE AUTOMATIZADO =====
./deploy/deploy_v4_0_0_nueva_logica_deltas.sh

# ===== TESTS FUNCIONALES =====
./deploy/test_v4_0_0_camera_server.sh

# ===== VERIFICACIÓN INMEDIATA =====
systemctl status parking-camera.service
journalctl -u parking-camera.service --since "5 minutes ago" | grep "NEW DELTA LOGIC ENABLED"
curl -s http://localhost:6400/camera

# ===== MONITORIZACIÓN =====
/opt/parking/scripts/monitor_v4_0_0.sh
```

## ⚡ Comandos de Una Línea

```bash
# Todo en una secuencia (ejecutar línea por línea)
ssh root@157.180.91.63 && cd /opt/parking && mkdir -p backups/$(date +%Y%m%d) && cp src/camera_server.py backups/$(date +%Y%m%d)/camera_server.py.backup.$(date +%H%M%S) && git stash && git checkout v4.0.0 && git pull origin v4.0.0 && chmod +x deploy/deploy_v4_0_0_nueva_logica_deltas.sh && ./deploy/deploy_v4_0_0_nueva_logica_deltas.sh && chmod +x deploy/test_v4_0_0_camera_server.sh && ./deploy/test_v4_0_0_camera_server.sh
```

## 🔄 Rollback Rápido (Si hay problemas)

```bash
# Opción 1: Feature flag (más rápido)
/opt/parking/scripts/rollback_v4_0_0.sh

# Opción 2: Manual
sed -i 's/USE_NEW_DELTA_LOGIC = True/USE_NEW_DELTA_LOGIC = False/' src/camera_server.py && systemctl restart parking-camera.service

# Opción 3: Backup completo
cp /opt/parking/backups/$(date +%Y%m%d)/camera_server.py.backup.* src/camera_server.py && systemctl restart parking-camera.service
```

## ✅ Verificación de Éxito

```bash
# Debe mostrar: "NEW DELTA LOGIC ENABLED"
journalctl -u parking-camera.service --since "2 minutes ago" | grep "NEW DELTA LOGIC ENABLED"

# Debe mostrar mensajes procesados con nueva lógica
journalctl -u parking-camera.service --since "10 minutes ago" | grep "NEW LOGIC - Delta final"

# Servicio debe estar activo
systemctl is-active parking-camera.service
```

## 📊 Monitorización Continua

```bash
# Logs en tiempo real
journalctl -u parking-camera.service -f

# Estadísticas cada 15 minutos
watch -n 900 '/opt/parking/scripts/monitor_v4_0_0.sh'

# Conteo de mensajes procesados
journalctl -u parking-camera.service --since "1 hour ago" | grep -c "NEW LOGIC - Delta final"
```

---

**⚠️ IMPORTANTE**: Ejecutar comando por comando y verificar cada resultado antes de continuar al siguiente.
