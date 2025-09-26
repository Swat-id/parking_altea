# Comandos de Despliegue v4.2.0 - Sistema de Endpoints Agrupados

## Servidor de Producción
- **Host**: `root@ubuntu-16gb-hel1-1`
- **Path**: `/opt/parking_altea`
- **Puerto API**: `6001`
- **Puerto Frontend**: `5789`

## Secuencia de Despliegue

### 1. Conectar al servidor y actualizar código
```bash
ssh root@ubuntu-16gb-hel1-1
cd /opt/parking_altea
git pull origin v4.1.0
```

### 2. Verificar cambios descargados
```bash
git log --oneline -5
git status
```

### 3. Reiniciar servicios backend
```bash
# Reiniciar servicio API
systemctl stop parking-api.service
systemctl start parking-api.service
systemctl status parking-api.service

# Verificar que el API está funcionando
curl -X GET http://localhost:6001/api/sensors
```

### 4. Compilar y desplegar frontend
```bash
cd /opt/parking_altea/client

# Instalar dependencias si hay nuevas
npm install

# Compilar frontend para producción
npm run build

# Matar procesos en puerto 5789
pkill -f ".*:5789" || true

# Iniciar frontend en background
cd /opt/parking_altea/client/dist
nohup python3 -m http.server 5789 > /opt/parking_altea/frontend.log 2>&1 &

# Verificar que está corriendo
netstat -tlnp | grep :5789
```

### 5. Verificar nuevos endpoints
```bash
# Test endpoints agrupados (requiere autenticación)
TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

echo "Token: $TOKEN"

# Test nuevos endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:6001/api/sensors/summary/user
curl -H "Authorization: Bearer $TOKEN" http://localhost:6001/api/dashboard/user/sensors
```

### 6. Verificar logs
```bash
# Logs del API
tail -f /opt/parking_altea/api_server.log

# Logs del frontend
tail -f /opt/parking_altea/frontend.log

# Logs del sistema
journalctl -u parking-api.service -f
```

## Comandos de Verificación Post-Despliegue

### Verificar servicios activos
```bash
systemctl status parking-api.service
systemctl status parking-camera.service
ps aux | grep python | grep -E "(api_server|http.server)"
netstat -tlnp | grep -E "(6001|5789)"
```

### Test de endpoints existentes (deben seguir funcionando)
```bash
curl -X GET http://localhost:6001/api/sensors
curl -X GET http://localhost:6001/api/parkings
curl -X GET http://localhost:6001/api/sensors/summary
```

### Test de permisos (superadmin vs usuario regular)
```bash
# Login como superadmin
ADMIN_TOKEN=$(curl -s -X POST http://localhost:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

# Test acceso completo del superadmin
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:6001/api/sensors/summary/user | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Superadmin parkings: {len(data.get(\"user_parkings\", []))}')"
```

## Rollback en caso de problemas

### Si hay errores en el API
```bash
# Volver a commit anterior
git log --oneline -5
git checkout [COMMIT_ANTERIOR]

# Reiniciar servicio
systemctl restart parking-api.service
```

### Si hay errores en el frontend
```bash
# Matar proceso del frontend
pkill -f ".*:5789"

# Volver a versión anterior y recompilar
git checkout [COMMIT_ANTERIOR]
cd /opt/parking_altea/client
npm run build
nohup python3 -m http.server 5789 > /opt/parking_altea/frontend.log 2>&1 &
```

## Verificación Final

### Checklist de verificación
- [ ] API responde en puerto 6001
- [ ] Frontend responde en puerto 5789
- [ ] Endpoints existentes funcionan
- [ ] Nuevos endpoints responden correctamente
- [ ] Superadmin tiene acceso completo
- [ ] Usuarios regulares tienen acceso filtrado
- [ ] Logs no muestran errores críticos
- [ ] Servicios systemd están activos
