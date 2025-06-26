#!/bin/bash

echo "=== VALIDACIÓN ESPECÍFICA DE CÁMARAS Y SERVIDOR ==="

echo "1. Verificando estado del servidor de cámaras..."
sudo systemctl status parking-camera

echo "2. Verificando puerto del servidor de cámaras..."
sudo netstat -tlnp | grep 6002

echo "3. Verificando logs del servidor de cámaras..."
echo "--- Últimas 20 líneas del log de cámaras ---"
sudo journalctl -u parking-camera --no-pager -n 20

echo "4. Verificando archivo de configuración de cámaras..."
if [ -f "/opt/parking_altea/src/camera_server.py" ]; then
    echo "Archivo camera_server.py encontrado"
    echo "--- Configuración de puerto ---"
    grep -n "PORT\|port" /opt/parking_altea/src/camera_server.py
else
    echo "ERROR: Archivo camera_server.py no encontrado"
fi

echo "5. Verificando endpoints de cámaras en la API..."
echo "--- Test GET /api/cameras ---"
curl -s http://localhost:6001/api/cameras | jq '.' 2>/dev/null || curl -s http://localhost:6001/api/cameras

echo "--- Test GET /api/cameras/1 ---"
curl -s http://localhost:6001/api/cameras/1 | jq '.' 2>/dev/null || curl -s http://localhost:6001/api/cameras/1

echo "6. Verificando datos de cámaras en la base de datos..."
echo "--- Consultando tabla accesses (cámaras) ---"
sudo -u postgres psql -d parking_altea -c "SELECT id, name, ip_address, port, parking_id, is_active FROM accesses;" 2>/dev/null || echo "Error consultando cámaras"

echo "7. Verificando conectividad directa al servidor de cámaras..."
echo "--- Test conexión TCP al puerto 6002 ---"
timeout 5 bash -c "</dev/tcp/localhost/6002" && echo "Puerto 6002 está abierto" || echo "Puerto 6002 no está accesible"

echo "8. Verificando procesos relacionados con cámaras..."
echo "--- Procesos Python relacionados con cámaras ---"
ps aux | grep -i camera | grep -v grep

echo "9. Verificando archivos de log específicos..."
if [ -f "/var/log/parking-camera.log" ]; then
    echo "--- Últimas líneas del log específico ---"
    tail -10 /var/log/parking-camera.log
else
    echo "Log específico no encontrado, usando journalctl"
fi

echo "10. Test de simulación de datos de cámara..."
echo "--- Simulando actualización de ocupación desde cámara ---"
curl -X POST http://localhost:6001/api/parkings/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"current_occupancy": 15, "max_occupancy": 50}' \
  -s | jq '.' 2>/dev/null || curl -X POST http://localhost:6001/api/parkings/1/occupancy \
  -H "Content-Type: application/json" \
  -d '{"current_occupancy": 15, "max_occupancy": 50}' \
  -s

echo "=== VALIDACIÓN DE CÁMARAS COMPLETADA ===" 