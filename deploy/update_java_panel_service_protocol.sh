#!/bin/bash

# Script para actualizar el servicio Java con el protocolo correcto
# Mapeo correcto de fontSize y colors según documentación del fabricante

echo "🚀 ACTUALIZACIÓN DEL SERVICIO JAVA PANEL"
echo "========================================"

# Configuración
PROJECT_DIR="/opt/parking_altea"
JAVA_SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="parking-panel-service"

echo "1️⃣ Cambiando al directorio del proyecto..."
cd $PROJECT_DIR

echo "2️⃣ Actualizando código desde git..."
git pull origin v3.0.0

echo "3️⃣ Verificando Java y Maven..."
java -version
mvn -version

echo "4️⃣ Compilando servicio Java..."
cd $JAVA_SERVICE_DIR

# Limpiar y compilar
mvn clean compile package -DskipTests

if [ $? -ne 0 ]; then
    echo "❌ Error compilando el servicio Java"
    exit 1
fi

echo "✅ Compilación exitosa"

echo "5️⃣ Deteniendo servicio actual..."
sudo systemctl stop $SERVICE_NAME

echo "6️⃣ Copiando archivo JAR..."
sudo cp target/panel-service-1.0.0.jar /opt/parking_altea/java-panel-service.jar

echo "7️⃣ Reiniciando servicio..."
sudo systemctl start $SERVICE_NAME

echo "8️⃣ Verificando estado del servicio..."
sudo systemctl status $SERVICE_NAME --no-pager

echo "9️⃣ Esperando que el servicio esté listo..."
sleep 5

echo "🔍 Verificando que el servicio responde..."
curl -s http://127.0.0.1:5656/api/v1/panels/health

if [ $? -eq 0 ]; then
    echo "✅ Servicio respondiendo correctamente"
else
    echo "❌ Error: El servicio no responde"
    echo "📋 Logs del servicio:"
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
    exit 1
fi

echo ""
echo "🧪 PRUEBA DE MAPEO DE PROTOCOLO"
echo "==============================="

# Test 1: Probar mapeo fontSize 16 -> valor 2
echo "1️⃣ Probando mapeo fontSize 16 -> valor 2..."

curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "172.20.4.52",
    "itemNum": 1,
    "texts": ["FONT 16 TEST"],
    "colors": [1],
    "fontSizes": [16],
    "showEffects": [1]
  }'

echo ""
echo ""

# Test 2: Probar mapeo color rojo (valor 1)
echo "2️⃣ Probando mapeo color rojo (valor 1)..."

curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "172.20.4.52",
    "itemNum": 1,
    "texts": ["COLOR ROJO TEST"],
    "colors": [1],
    "fontSizes": [16],
    "showEffects": [1]
  }'

echo ""
echo ""

# Test 3: Probar diferentes tamaños de fuente
echo "3️⃣ Probando diferentes tamaños de fuente..."

font_sizes=(8 12 16 24 32 40 48 56)
protocol_values=(0 1 2 3 4 5 6 7)

for i in "${!font_sizes[@]}"; do
    fontSize=${font_sizes[$i]}
    protocolValue=${protocol_values[$i]}
    echo "   📝 Probando fontSize ${fontSize}px -> valor ${protocolValue}"
    
    curl -X POST http://127.0.0.1:5656/api/v1/panels/sendMulti \
      -H "Content-Type: application/json" \
      -d "{
        \"ip\": \"172.20.4.52\",
        \"itemNum\": 1,
        \"texts\": [\"FONT ${fontSize} TEST\"],
        \"colors\": [1],
        \"fontSizes\": [${fontSize}],
        \"showEffects\": [1]
      }"
    
    echo ""
    sleep 1
done

echo ""
echo "📋 VERIFICACIÓN DE LOGS"
echo "======================="
echo "Comando para ver logs:"
echo "sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Buscar en logs:"
echo "- 'Parámetros mapeados - fontSize: 16->2'"
echo "- 'Simulando envío de mensaje con fontSize=2 y color=1'"
echo ""
echo "✅ Actualización completada"
echo ""
echo "📋 RESUMEN DEL MAPEO IMPLEMENTADO:"
echo "   fontSize: 16px -> valor 2 (FONTSIZE_16)"
echo "   color: 1 -> Rojo"
echo "   protocolo: sendMulti con mapeo correcto" 