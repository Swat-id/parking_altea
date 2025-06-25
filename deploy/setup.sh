#!/bin/bash

# Script de despliegue para Parking Altea
# Servidor: 157.180.91.63
# Usuario: root
# Contraseña: Sudv9uvSvdu!

set -e

echo "=== Iniciando despliegue de Parking Altea ==="

# 1. Actualizar paquetes del sistema
echo "Actualizando paquetes del sistema..."
apt update
apt install -y python3-venv python3-pip postgresql libpq-dev build-essential git

# 2. Configurar PostgreSQL
echo "Configurando PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Crear usuario y base de datos
sudo -u postgres psql <<EOF
CREATE USER parking_user WITH PASSWORD 'parking_pass';
CREATE DATABASE parking_db OWNER parking_user;
\q
EOF

# 3. Clonar repositorio (asumiendo que ya está en /opt/parking_altea)
echo "Configurando directorio del proyecto..."
cd /opt
if [ ! -d "parking_altea" ]; then
    echo "Error: El directorio parking_altea no existe en /opt"
    exit 1
fi

cd parking_altea

# 4. Crear entorno virtual
echo "Creando entorno virtual Python..."
python3 -m venv venv
source venv/bin/activate

# 5. Instalar dependencias
echo "Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Crear archivo .env
echo "Creando archivo de configuración..."
cat > .env <<EOF
DATABASE_URL=postgresql://parking_user:parking_pass@localhost:5432/parking_db
CAMERA_PORT=6400
API_PORT=6001
LOG_RETENTION_DAYS=15
EOF

# 7. Inicializar base de datos
echo "Inicializando base de datos..."
cd src
python3 init_db.py
python3 load_data.py
cd ..

# 8. Configurar servicios systemd
echo "Configurando servicios systemd..."
cp deploy/parking-api.service /etc/systemd/system/
cp deploy/parking-camera.service /etc/systemd/system/

# 9. Habilitar y arrancar servicios
echo "Habilitando y arrancando servicios..."
systemctl daemon-reload
systemctl enable parking-api.service parking-camera.service
systemctl start parking-api.service parking-camera.service

# 10. Verificar estado de servicios
echo "Verificando estado de servicios..."
systemctl status parking-api.service --no-pager
systemctl status parking-camera.service --no-pager

# 11. Configurar firewall
echo "Configurando firewall..."
ufw allow 6001/tcp
ufw allow 6400/tcp
ufw allow 22/tcp
ufw --force enable

echo "=== Despliegue completado ==="
echo "API disponible en: http://157.180.91.63:6001"
echo "Servidor de cámaras en puerto: 6400"
echo ""
echo "Para verificar la instalación:"
echo "curl http://localhost:6001/parkings"
echo ""
echo "Para ver logs:"
echo "journalctl -u parking-api.service -f"
echo "journalctl -u parking-camera.service -f" 