#!/bin/bash

echo "=== Actualizando frontend con correcciones de autenticación ==="

# Navegar al directorio del proyecto
cd /root/parking_altea

# Obtener los últimos cambios
echo "Obteniendo últimos cambios de Git..."
git pull origin v2.2

# Navegar al directorio del cliente
cd client

# Instalar dependencias si es necesario
echo "Instalando dependencias..."
npm install

# Limpiar build anterior
echo "Limpiando build anterior..."
rm -rf dist

# Construir el frontend
echo "Construyendo frontend..."
npm run build

# Crear directorio de nginx si no existe
sudo mkdir -p /var/www/parking-altea

# Copiar archivos construidos
echo "Copiando archivos a nginx..."
sudo cp -r dist/* /var/www/parking-altea/

# Configurar permisos
sudo chown -R www-data:www-data /var/www/parking-altea
sudo chmod -R 755 /var/www/parking-altea

# Recargar nginx
echo "Recargando nginx..."
sudo systemctl reload nginx

echo "=== Frontend actualizado correctamente ==="
echo "El frontend está disponible en: http://157.180.91.63:5789" 