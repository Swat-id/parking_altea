# Comandos de Despliegue - Panel Protocol Service v4.3.0

## Información del Servidor
- **Servidor**: root@ubuntu-16gb-hel1-1
- **Ruta del proyecto**: /opt/parking_altea
- **Rama**: v4.3.0
- **Puerto del servicio**: 7000 (FIJO)

## Cambios incluidos en este despliegue:
1. **Nuevo servicio Panel Protocol Service** - Puerto 7000
2. **Comunicación TCP/IP directa** con paneles (puerto 5200)
3. **Gestión asíncrona y paralela** de múltiples operaciones
4. **Sistema de autenticación JWT** integrado con backend
5. **Cliente HTTP** para uso desde el backend

---

## 1. Conectar al servidor
```bash
ssh root@ubuntu-16gb-hel1-1
```

## 2. Navegar al directorio del proyecto
```bash
cd /opt/parking_altea
```

## 3. Verificar rama actual y estado
```bash
git branch
git status
```

## 4. Cambiar a la rama v4.3.0
```bash
# Si no estás en la rama v4.3.0
git fetch origin
git checkout v4.3.0
git pull origin v4.3.0
```

## 5. Verificar que los cambios se han descargado
```bash
# Verificar que existe el directorio panel_protocol
ls -la src/panel_protocol/

# Verificar archivos principales
ls -la src/panel_protocol/*.py

# Verificar documentación
ls -la docs/v4.3.0/
```

## 6. Verificar dependencias Python
```bash
# Activar entorno virtual
source venv/bin/activate

# Verificar que flask y flask-cors están instalados
pip list | grep -i flask

# Si no están instalados, instalarlos
pip install flask flask-cors
```

## 7. Verificar que el puerto 7000 está libre
```bash
# Verificar si hay algo usando el puerto 7000
sudo lsof -i :7000

# O con netstat
sudo netstat -tlnp | grep 7000
```

## 8. Probar el servicio manualmente (opcional)
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar el servicio en modo prueba
cd /opt/parking_altea
python src/panel_protocol/api_server.py
```

**Nota**: Presionar Ctrl+C para detener el servicio de prueba.

## 9. Crear servicio systemd
```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/parking-panel-protocol.service
```

**Contenido del archivo:**
```ini
[Unit]
Description=Panel Protocol Service v4.3.0
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/parking_altea
Environment="PYTHONPATH=/opt/parking_altea"
Environment="PATH=/opt/parking_altea/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/parking_altea/venv/bin/python /opt/parking_altea/src/panel_protocol/api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 10. Habilitar y iniciar el servicio
```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio para que inicie al arrancar
sudo systemctl enable parking-panel-protocol

# Iniciar el servicio
sudo systemctl start parking-panel-protocol

# Verificar estado
sudo systemctl status parking-panel-protocol
```

## 11. Verificar que el servicio está funcionando
```bash
# Verificar que está escuchando en el puerto 7000
sudo netstat -tlnp | grep 7000

# Probar health check
curl http://localhost:7000/health

# Ver logs del servicio
sudo journalctl -u parking-panel-protocol -f --lines=20
```

## 12. Probar autenticación
```bash
# Probar login
curl -X POST http://localhost:7000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "info@swat-id.com",
    "password": "admin123!"
  }'
```

## 13. Probar envío de texto (opcional)
```bash
# Primero obtener token
TOKEN=$(curl -s -X POST http://localhost:7000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "info@swat-id.com", "password": "admin123!"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# Enviar texto de prueba (reemplazar IP del panel)
curl -X POST http://localhost:7000/api/v1/panels/send-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "panel_ip": "192.168.1.221",
    "window_id": 0,
    "text": "TEST v4.3.0",
    "color": 2,
    "font_size": 2,
    "effect": 0
  }'
```

## 14. Verificar logs del servicio
```bash
# Ver logs recientes
sudo journalctl -u parking-panel-protocol --no-pager -n 50

# Ver logs en tiempo real
sudo journalctl -u parking-panel-protocol -f
```

## 15. Verificar que no hay errores
```bash
# Buscar errores en los logs
sudo journalctl -u parking-panel-protocol --since "5 minutes ago" | grep -i error

# Verificar estado del servicio
sudo systemctl status parking-panel-protocol
```

## 16. Verificar puertos del sistema
```bash
# Ver todos los puertos en uso
sudo netstat -tlnp | grep -E "(6001|6400|3535|5789|7000|80)"
```

## Comandos de gestión del servicio

### Reiniciar el servicio
```bash
sudo systemctl restart parking-panel-protocol
```

### Detener el servicio
```bash
sudo systemctl stop parking-panel-protocol
```

### Ver estado del servicio
```bash
sudo systemctl status parking-panel-protocol
```

### Ver logs del servicio
```bash
# Últimas 50 líneas
sudo journalctl -u parking-panel-protocol --no-pager -n 50

# Logs en tiempo real
sudo journalctl -u parking-panel-protocol -f

# Logs desde hace 1 hora
sudo journalctl -u parking-panel-protocol --since "1 hour ago"
```

## Verificación final

- [ ] Servicio iniciado correctamente
- [ ] Puerto 7000 escuchando
- [ ] Health check responde correctamente
- [ ] Login funciona con usuarios de la BD
- [ ] Envío de texto funciona (opcional)
- [ ] Logs sin errores críticos
- [ ] Servicio configurado para iniciar al arrancar

## Troubleshooting

### Si el servicio no inicia:
```bash
# Ver logs de error
sudo journalctl -u parking-panel-protocol --no-pager -n 100

# Verificar que el puerto no está en uso
sudo lsof -i :7000

# Verificar permisos
ls -la /opt/parking_altea/src/panel_protocol/
```

### Si hay errores de importación:
```bash
# Verificar que el entorno virtual está activo
source venv/bin/activate

# Verificar dependencias
pip list | grep -E "(flask|flask-cors|asyncio)"

# Instalar dependencias faltantes
pip install flask flask-cors
```

### Si el puerto 7000 está en uso:
```bash
# Ver qué proceso está usando el puerto
sudo lsof -i :7000

# Detener el proceso si es necesario
sudo kill -9 <PID>
```

---

**Fecha**: 2025-10-02  
**Versión**: 4.3.0  
**Puerto**: 7000 (FIJO)

