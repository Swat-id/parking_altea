#!/bin/bash

# Script de configuración de base de datos para Parking Altea
# Este script configura la base de datos y los usuarios según la documentación

set -e

echo "=========================================="
echo "CONFIGURACIÓN DE BASE DE DATOS - PARKING ALTEA"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Verificar que PostgreSQL esté instalado
print_status "Verificando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL no está instalado"
    exit 1
fi

# 2. Crear base de datos si no existe
print_status "Verificando base de datos parking_altea..."
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw parking_altea; then
    print_status "Creando base de datos parking_altea..."
    sudo -u postgres createdb parking_altea
    print_status "Base de datos parking_altea creada"
else
    print_warning "Base de datos parking_altea ya existe"
fi

# 3. Instalar dependencias de Python
print_status "Instalando dependencias de Python..."
apt update
apt install -y python3-sqlalchemy python3-psycopg2 python3-flask python3-bcrypt python3-jwt python3-dotenv

# 4. Verificar que las dependencias se instalaron
print_status "Verificando dependencias..."
python3 -c "import sqlalchemy, psycopg2, flask, bcrypt, jwt, dotenv; print('Todas las dependencias OK')"

# 5. Inicializar esquema de base de datos
print_status "Inicializando esquema de base de datos..."
python3 src/init_db.py

# 6. Inicializar usuarios
print_status "Inicializando usuarios..."
python3 src/init_users.py

# 7. Verificar usuarios creados
print_status "Verificando usuarios creados..."
sudo -u postgres psql parking_altea -c "SELECT id, name, email FROM users;"

# 8. Verificar tablas creadas
print_status "Verificando tablas creadas..."
sudo -u postgres psql parking_altea -c "\dt"

echo ""
echo "=========================================="
echo "CONFIGURACIÓN COMPLETADA"
echo "=========================================="
echo "Base de datos: parking_altea"
echo "Usuarios configurados:"
echo "  - Toni Alos: atea.dti@altea.es / altea2025!"
echo "  - Iván Martí: gerenciapstd@altea.es / altea2025!"
echo ""
echo "Para ejecutar tests:"
echo "  python3 test_complete_validation.py"
echo "==========================================" 