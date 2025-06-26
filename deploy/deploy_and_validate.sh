#!/bin/bash

echo "=== DESPLIEGUE Y VALIDACIÓN COMPLETA DEL SISTEMA ==="

# Navegar al directorio del proyecto
cd /opt/parking_altea

echo "1. Obteniendo últimos cambios de Git..."
git pull origin v2.2

echo "2. Verificando estado de servicios..."
echo "--- Estado del backend API ---"
sudo systemctl status parking-api

echo "--- Estado del servidor de cámaras ---"
sudo systemctl status parking-camera

echo "--- Estado de Nginx ---"
sudo systemctl status nginx

echo "--- Estado de PostgreSQL ---"
sudo systemctl status postgresql

echo "3. Verificando puertos en uso..."
echo "--- Puertos activos ---"
sudo netstat -tlnp | grep -E ':(6001|5000|5001|5789|5432)'

echo "4. Actualizando frontend..."
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

echo "5. Reiniciando servicios..."
sudo systemctl restart parking-api
sudo systemctl restart parking-camera

echo "6. Esperando que los servicios se inicien..."
sleep 5

echo "7. Validando endpoints..."

echo "--- Test endpoint de salud del API ---"
curl -s http://localhost:6001/health || echo "Endpoint /health no disponible"

echo "--- Test endpoint de parkings ---"
curl -s http://localhost:6001/api/parkings | head -c 200

echo "--- Test endpoint de cámaras ---"
curl -s http://localhost:6001/api/cameras | head -c 200

echo "--- Test endpoint de paneles ---"
curl -s http://localhost:6001/api/panels | head -c 200

echo "--- Test endpoint de estadísticas ---"
curl -s http://localhost:6001/api/statistics | head -c 200

echo "8. Verificando conectividad del frontend..."
echo "--- Test frontend en puerto 5789 ---"
curl -s -I http://localhost:5789 | head -3

echo "9. Verificando logs de servicios..."
echo "--- Últimas líneas del log del API ---"
sudo journalctl -u parking-api --no-pager -n 10

echo "--- Últimas líneas del log de cámaras ---"
sudo journalctl -u parking-camera --no-pager -n 10

echo "10. Verificando base de datos..."
echo "--- Conectividad a PostgreSQL ---"
sudo -u postgres psql -c "SELECT version();" 2>/dev/null || echo "Error conectando a PostgreSQL"

echo "--- Verificando usuarios en la base de datos ---"
sudo -u postgres psql -d parking_altea -c "SELECT id, name, email, is_active FROM users;" 2>/dev/null || echo "Error consultando usuarios"

echo "=== DESPLIEGUE COMPLETADO ==="
echo "Frontend: http://157.180.91.63:5789"
echo "API Backend: http://157.180.91.63:6001"
echo "Servidor de cámaras: Puerto 6002 (interno)" 