#!/bin/bash
# Configurar PostgreSQL para Parking Altea

echo "Configurando PostgreSQL..."

# Crear usuario y base de datos
sudo -u postgres psql <<EOF
CREATE USER parking_user WITH PASSWORD 'parking_pass';
CREATE DATABASE parking_db OWNER parking_user;
GRANT ALL PRIVILEGES ON DATABASE parking_db TO parking_user;
\q
EOF

echo "PostgreSQL configurado correctamente" 