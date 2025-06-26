#!/bin/bash

# Script para reconstruir el frontend de Parking Altea
# Este script asegura que el frontend esté configurado correctamente

set -e

echo "=========================================="
echo "RECONSTRUCCIÓN DEL FRONTEND - PARKING ALTEA"
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

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "client/package.json" ]; then
    print_error "No se encontró client/package.json. Ejecutar desde el directorio raíz del proyecto."
    exit 1
fi

# 2. Ir al directorio del cliente
cd client

# 3. Verificar que Node.js esté instalado
print_status "Verificando Node.js..."
if ! command -v node &> /dev/null; then
    print_error "Node.js no está instalado"
    exit 1
fi

# 4. Instalar dependencias si no existen
print_status "Verificando dependencias..."
if [ ! -d "node_modules" ]; then
    print_status "Instalando dependencias..."
    npm install
else
    print_warning "Dependencias ya instaladas"
fi

# 5. Limpiar build anterior
print_status "Limpiando build anterior..."
rm -rf dist

# 6. Reconstruir el frontend
print_status "Reconstruyendo el frontend..."
npm run build

# 7. Verificar que el build se creó correctamente
if [ ! -d "dist" ]; then
    print_error "El build no se creó correctamente"
    exit 1
fi

print_status "Frontend reconstruido correctamente"

# 8. Crear directorio de Nginx si no existe y copiar archivos
print_status "Creando directorio de Nginx..."
sudo mkdir -p /var/www/parking_altea

print_status "Copiando archivos a Nginx..."
sudo cp -r dist/* /var/www/parking_altea/

# 9. Verificar permisos
print_status "Ajustando permisos..."
sudo chown -R www-data:www-data /var/www/parking_altea/
sudo chmod -R 755 /var/www/parking_altea/

# 10. Recargar Nginx
print_status "Recargando Nginx..."
sudo systemctl reload nginx

# 11. Verificar que Nginx esté funcionando
print_status "Verificando estado de Nginx..."
if systemctl is-active --quiet nginx; then
    print_status "Nginx está funcionando correctamente"
else
    print_error "Nginx no está funcionando"
    exit 1
fi

echo ""
echo "=========================================="
echo "FRONTEND RECONSTRUIDO EXITOSAMENTE"
echo "=========================================="
echo "URL del frontend: http://157.180.91.63:5789"
echo "URL de la API: http://157.180.91.63:6001"
echo ""
echo "Credenciales de prueba:"
echo "  - Toni Alos: atea.dti@altea.es / altea2025!"
echo "  - Iván Martí: gerenciapstd@altea.es / altea2025!"
echo "==========================================" 