#!/bin/bash

# Comandos individuales para actualizar Java Panel Service
# Ejecutar cada sección según sea necesario

echo "=== COMANDOS PARA ACTUALIZAR JAVA PANEL SERVICE ==="
echo ""

echo "1. ACTUALIZAR CÓDIGO:"
echo "cd /opt/parking_altea"
echo "git fetch origin"
echo "git checkout java-panel-service"
echo "git pull origin java-panel-service"
echo ""

echo "2. RECOMPILAR SERVICIO:"
echo "cd /opt/parking_altea/server/java-panel-service"
echo "mvn clean"
echo "mvn compile"
echo "mvn package -DskipTests"
echo ""

echo "3. VERIFICAR JAR:"
echo "ls -la target/panel-service-1.0.0.jar"
echo ""

echo "4. DETENER SERVICIO:"
echo "systemctl stop java-panel-service"
echo ""

echo "5. COPIAR NUEVO JAR:"
echo "cp target/panel-service-1.0.0.jar /opt/panel-service-1.0.0.jar"
echo ""

echo "6. INICIAR SERVICIO:"
echo "systemctl start java-panel-service"
echo ""

echo "7. VERIFICAR ESTADO:"
echo "systemctl status java-panel-service"
echo ""

echo "8. VER LOGS:"
echo "journalctl -u java-panel-service --no-pager -n 20"
echo ""

echo "9. PROBAR ENDPOINTS:"
echo "curl http://localhost:5002/api/panel/health"
echo "curl http://localhost:5002/api/panel/status"
echo "curl http://localhost:5002/api/panel/colors"
echo ""

echo "10. PROBAR TEST PANEL:"
echo "curl http://localhost:5002/api/panel/test/172.20.17.50"
echo "" 