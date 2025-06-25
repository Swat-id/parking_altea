# Guía de Despliegue - Parking Altea

## Información del Servidor

- **IP**: 157.180.91.63
- **Sistema Operativo**: Ubuntu 20.04 LTS
- **Usuario**: root
- **Contraseña**: Sudv9uvSvdu!
- **Arquitectura**: x86_64

## Requisitos del Sistema

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disco**: 20 GB
- **Red**: 100 Mbps

### Software Requerido
- Ubuntu 20.04 LTS o superior
- Python 3.8+
- PostgreSQL 12+
- Git
- UFW (firewall)

## Instalación Paso a Paso

### 1. Preparación del Sistema

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Actualizar sistema
apt update && apt upgrade -y

# Instalar paquetes básicos
apt install -y python3-venv python3-pip postgresql libpq-dev build-essential git curl wget
```

### 2. Configuración de PostgreSQL

```bash
# Iniciar y habilitar PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Crear usuario y base de datos
sudo -u postgres psql <<EOF
CREATE USER parking_user WITH PASSWORD 'parking_pass';
CREATE DATABASE parking_db OWNER parking_user;
GRANT ALL PRIVILEGES ON DATABASE parking_db TO parking_user;
\q
EOF

# Verificar instalación
sudo -u postgres psql -d parking_db -c "\dt"
```

### 3. Clonación del Repositorio

```bash
# Crear directorio de aplicación
mkdir -p /opt
cd /opt

# Clonar repositorio (asumiendo que ya está disponible)
# Si no está clonado, clonar desde el repositorio
git clone https://github.com/Swat-id/parking_altea.git parking_altea
cd parking_altea
```

### 4. Configuración del Entorno Python

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python3 -c "import flask, sqlalchemy, psycopg2; print('Dependencias instaladas correctamente')"
```

### 5. Configuración de Variables de Entorno

```bash
# Crear archivo .env
cat > .env <<EOF
DATABASE_URL=postgresql://parking_user:parking_pass@localhost:5432/parking_db
CAMERA_PORT=6400
API_PORT=6001
LOG_RETENTION_DAYS=15
EOF

# Verificar archivo
cat .env
```

### 6. Inicialización de la Base de Datos

```bash
# Crear tablas
cd src
python3 init_db.py

# Cargar datos iniciales
python3 load_data.py

# Verificar datos cargados
python3 -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Parking, Access, Panel

engine = create_engine(config.DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

parkings = session.query(Parking).count()
accesses = session.query(Access).count()
panels = session.query(Panel).count()

print(f'Parkings: {parkings}')
print(f'Accesos: {accesses}')
print(f'Paneles: {panels}')

session.close()
"
```

### 7. Configuración de Servicios Systemd

```bash
# Copiar archivos de servicio
cp deploy/parking-api.service /etc/systemd/system/
cp deploy/parking-camera.service /etc/systemd/system/

# Recargar configuración de systemd
systemctl daemon-reload

# Habilitar servicios
systemctl enable parking-api.service
systemctl enable parking-camera.service
```

### 8. Configuración del Firewall

```bash
# Configurar UFW
ufw allow 22/tcp    # SSH
ufw allow 6001/tcp  # API REST
ufw allow 6400/tcp  # Servidor de cámaras
ufw allow 5432/tcp  # PostgreSQL (solo local)

# Habilitar firewall
ufw --force enable

# Verificar reglas
ufw status numbered
```

### 9. Inicio de Servicios

```bash
# Iniciar servicios
systemctl start parking-api.service
systemctl start parking-camera.service

# Verificar estado
systemctl status parking-api.service
systemctl status parking-camera.service

# Verificar logs
journalctl -u parking-api.service --no-pager -n 20
journalctl -u parking-camera.service --no-pager -n 20
```

## Verificación de la Instalación

### 1. Verificar API REST

```bash
# Probar endpoint de listado de aparcamientos
curl http://localhost:6001/parkings

# Probar endpoint de detalle de aparcamiento
curl http://localhost:6001/parking/1

# Probar actualización manual de ocupación
curl -X POST http://localhost:6001/parking/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"occupancy": 100}'
```

### 2. Verificar Servidor de Cámaras

```bash
# Probar recepción de mensaje de cámara
curl -X POST http://localhost:6400/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 172.20.17.146" \
  -d '{
    "event": "Object Counting",
    "device": "ciutat_esportiva camera 1",
    "line": 1,
    "Vehicle In": 10,
    "Vehicle Out": 5
  }'
```

### 3. Verificar Base de Datos

```bash
# Conectar a PostgreSQL
sudo -u postgres psql -d parking_db

# Verificar tablas
\dt

# Verificar datos
SELECT * FROM parkings LIMIT 5;
SELECT * FROM accesses LIMIT 5;
SELECT * FROM panels LIMIT 5;

# Salir
\q
```

## Script de Despliegue Automático

Se incluye un script de despliegue completo en `deploy/setup.sh`:

```bash
# Dar permisos de ejecución
chmod +x deploy/setup.sh

# Ejecutar despliegue completo
./deploy/setup.sh
```

## Configuración de Logs

### Logs de Systemd

```bash
# Ver logs en tiempo real
journalctl -u parking-api.service -f
journalctl -u parking-camera.service -f

# Ver logs de las últimas 24 horas
journalctl -u parking-api.service --since "24 hours ago"
journalctl -u parking-camera.service --since "24 hours ago"

# Ver logs de errores
journalctl -u parking-api.service -p err
journalctl -u parking-camera.service -p err
```

### Configuración de Rotación de Logs

```bash
# Crear configuración de logrotate
cat > /etc/logrotate.d/parking-altea <<EOF
/var/log/parking-altea/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload parking-api.service
        systemctl reload parking-camera.service
    endscript
}
EOF
```

## Monitoreo del Sistema

### Verificación de Estado

```bash
# Script de verificación
cat > /opt/parking_altea/check_status.sh <<'EOF'
#!/bin/bash

echo "=== Estado del Sistema Parking Altea ==="
echo

echo "1. Servicios Systemd:"
systemctl is-active parking-api.service
systemctl is-active parking-camera.service
echo

echo "2. Puertos en uso:"
netstat -tlnp | grep -E ':(6001|6400|5432)'
echo

echo "3. Uso de memoria:"
free -h
echo

echo "4. Uso de disco:"
df -h /
echo

echo "5. Conexiones a la API:"
curl -s http://localhost:6001/parkings | jq '.[0:3]' 2>/dev/null || echo "API no responde"
echo

echo "6. Últimos logs de error:"
journalctl -u parking-api.service -p err --no-pager -n 5
journalctl -u parking-camera.service -p err --no-pager -n 5
EOF

chmod +x /opt/parking_altea/check_status.sh
```

### Monitoreo Automático

```bash
# Crear servicio de monitoreo
cat > /etc/systemd/system/parking-monitor.service <<EOF
[Unit]
Description=Parking System Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/parking_altea/check_status.sh
User=root

[Install]
WantedBy=multi-user.target
EOF

# Crear timer para ejecución periódica
cat > /etc/systemd/system/parking-monitor.timer <<EOF
[Unit]
Description=Run Parking Monitor every 5 minutes
Requires=parking-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable parking-monitor.timer
systemctl start parking-monitor.timer
```

## Backup y Recuperación

### Backup Automático

```bash
# Crear script de backup
cat > /opt/parking_altea/backup.sh <<'EOF'
#!/bin/bash

BACKUP_DIR="/backup/parking-altea"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup de base de datos
pg_dump parking_db > $BACKUP_DIR/parking_db_$DATE.sql

# Backup de configuración
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/parking_altea/.env /opt/parking_altea/src/

# Mantener solo los últimos 7 días
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
EOF

chmod +x /opt/parking_altea/backup.sh

# Programar backup diario
echo "0 2 * * * /opt/parking_altea/backup.sh" | crontab -
```

### Recuperación

```bash
# Restaurar base de datos
pg_restore -d parking_db /backup/parking-altea/parking_db_YYYYMMDD_HHMMSS.sql

# Restaurar configuración
tar -xzf /backup/parking-altea/config_YYYYMMDD_HHMMSS.tar.gz -C /
```

## Troubleshooting

### Problemas Comunes

#### 1. Servicio no inicia
```bash
# Verificar logs
journalctl -u parking-api.service --no-pager -n 50
journalctl -u parking-camera.service --no-pager -n 50

# Verificar configuración
systemctl cat parking-api.service
systemctl cat parking-camera.service
```

#### 2. Error de conexión a base de datos
```bash
# Verificar PostgreSQL
systemctl status postgresql
sudo -u postgres psql -d parking_db -c "SELECT version();"

# Verificar variables de entorno
cat /opt/parking_altea/.env
```

#### 3. Puerto no disponible
```bash
# Verificar puertos en uso
netstat -tlnp | grep -E ':(6001|6400)'

# Verificar firewall
ufw status
```

#### 4. Permisos de archivos
```bash
# Verificar permisos
ls -la /opt/parking_altea/
ls -la /opt/parking_altea/src/

# Corregir permisos si es necesario
chown -R root:root /opt/parking_altea/
chmod -R 755 /opt/parking_altea/
```

## Actualizaciones

### Actualización de Código

```bash
cd /opt/parking_altea

# Hacer backup antes de actualizar
./backup.sh

# Actualizar código
git pull origin main

# Reiniciar servicios
systemctl restart parking-api.service
systemctl restart parking-camera.service

# Verificar funcionamiento
./check_status.sh
```

### Actualización de Dependencias

```bash
cd /opt/parking_altea
source venv/bin/activate

# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Reiniciar servicios
systemctl restart parking-api.service
systemctl restart parking-camera.service
``` 