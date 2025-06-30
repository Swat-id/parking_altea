#!/bin/bash

# Script para actualizar, recompilar y probar el flujo correcto de comunicación con paneles
# Uso: ./update_and_test_panel_flow.sh

set -e

echo "=== Actualizando y probando flujo de comunicación con paneles ==="

# Variables
PROJECT_DIR="/opt/parking_altea"
JAVA_SERVICE_DIR="$PROJECT_DIR/server/java-panel-service"
SERVICE_NAME="java-panel-service"
JAR_NAME="java-panel-service-1.0.0.jar"
TEST_PANEL_IP="172.20.4.52"
SERVICE_URL="http://localhost:5002/api"

echo "🎯 Panel de prueba: $TEST_PANEL_IP"
echo "🔗 URL del servicio: $SERVICE_URL"

# ===== PASO 1: ACTUALIZAR CÓDIGO =====
echo ""
echo "=== PASO 1: Actualizando código desde Git ==="
cd $PROJECT_DIR

echo "1.1. Obteniendo últimos cambios..."
git fetch origin
git checkout java-panel-service
git pull origin java-panel-service

echo "1.2. Verificando cambios..."
git log --oneline -5

# ===== PASO 2: RECOMPILAR SERVICIO JAVA =====
echo ""
echo "=== PASO 2: Recompilando servicio Java ==="
cd $JAVA_SERVICE_DIR

echo "2.1. Limpiando compilación anterior..."
mvn clean

echo "2.2. Compilando el proyecto..."
mvn compile

echo "2.3. Creando JAR ejecutable..."
mvn package -DskipTests

echo "2.4. Verificando que el JAR se creó correctamente..."
if [ ! -f "target/$JAR_NAME" ]; then
    echo "❌ ERROR: No se pudo crear el JAR ejecutable"
    exit 1
fi
echo "✅ JAR creado correctamente: target/$JAR_NAME"

# ===== PASO 3: REINICIAR SERVICIO =====
echo ""
echo "=== PASO 3: Reiniciando servicio ==="

echo "3.1. Deteniendo el servicio si está ejecutándose..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Deteniendo servicio $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
    sleep 3
fi

echo "3.2. Copiando el nuevo JAR..."
cp target/$JAR_NAME /opt/$JAR_NAME

echo "3.3. Reiniciando el servicio..."
systemctl start $SERVICE_NAME

echo "3.4. Verificando estado del servicio..."
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Servicio $SERVICE_NAME iniciado correctamente"
else
    echo "❌ ERROR: El servicio no se pudo iniciar"
    systemctl status $SERVICE_NAME
    exit 1
fi

echo "3.5. Verificando logs del servicio..."
echo "Últimas líneas del log:"
journalctl -u $SERVICE_NAME --no-pager -n 10

# ===== PASO 4: VERIFICAR SERVICIO =====
echo ""
echo "=== PASO 4: Verificando servicio ==="

echo "4.1. Probando health check..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" $SERVICE_URL/panel/health)
HTTP_CODE="${HEALTH_RESPONSE: -3}"
RESPONSE_BODY="${HEALTH_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check exitoso"
    echo "$RESPONSE_BODY" | jq .
else
    echo "❌ ERROR: Health check falló (HTTP $HTTP_CODE)"
    echo "$RESPONSE_BODY"
    exit 1
fi

echo "4.2. Verificando estado de paneles..."
STATUS_RESPONSE=$(curl -s $SERVICE_URL/panel/status)
echo "$STATUS_RESPONSE" | jq .

# ===== PASO 5: PROBAR FLUJO CORRECTO =====
echo ""
echo "=== PASO 5: Probando flujo correcto con panel $TEST_PANEL_IP ==="

echo "5.1. Probando initNetwork..."
INIT_DATA="{\"panelIP\":\"$TEST_PANEL_IP\",\"port\":5200,\"idCode\":\"255.255.255.255\",\"timeout\":3000}"
INIT_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$INIT_DATA" $SERVICE_URL/panel/init-network)
echo "$INIT_RESPONSE" | jq .

# Verificar si initNetwork fue exitoso
INIT_SUCCESS=$(echo "$INIT_RESPONSE" | jq -r '.success')
if [ "$INIT_SUCCESS" = "true" ]; then
    echo "✅ initNetwork exitoso"
else
    echo "❌ ERROR: initNetwork falló"
    echo "$INIT_RESPONSE" | jq .
fi

echo "5.2. Probando setListener..."
LISTENER_DATA="{\"panelIP\":\"$TEST_PANEL_IP\",\"enableListener\":true,\"callbackPort\":5001}"
LISTENER_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$LISTENER_DATA" $SERVICE_URL/panel/set-listener)
echo "$LISTENER_RESPONSE" | jq .

# Verificar si setListener fue exitoso
LISTENER_SUCCESS=$(echo "$LISTENER_RESPONSE" | jq -r '.success')
if [ "$LISTENER_SUCCESS" = "true" ]; then
    echo "✅ setListener exitoso"
else
    echo "❌ ERROR: setListener falló"
    echo "$LISTENER_RESPONSE" | jq .
fi

echo "5.3. Probando sendMulti..."
TIMESTAMP=$(date +"%H:%M:%S")
SEND_MULTI_DATA="{\"panelIP\":\"$TEST_PANEL_IP\",\"itemNum\":1,\"texts\":[\"TEST SENDMULTI - $TIMESTAMP\"],\"colors\":[1],\"fontSizes\":[2],\"showEffects\":[0]}"
SEND_MULTI_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$SEND_MULTI_DATA" $SERVICE_URL/panel/send-multi)
echo "$SEND_MULTI_RESPONSE" | jq .

# Verificar si sendMulti fue exitoso
SEND_MULTI_SUCCESS=$(echo "$SEND_MULTI_RESPONSE" | jq -r '.success')
if [ "$SEND_MULTI_SUCCESS" = "true" ]; then
    echo "✅ sendMulti exitoso"
else
    echo "❌ ERROR: sendMulti falló"
    echo "$SEND_MULTI_RESPONSE" | jq .
fi

# ===== PASO 6: PROBAR FLUJO COMPLETO =====
echo ""
echo "=== PASO 6: Probando flujo completo (sendManual) ==="

MANUAL_DATA="{\"panelIP\":\"$TEST_PANEL_IP\",\"port\":5200,\"idCode\":\"255.255.255.255\",\"timeout\":600,\"cardId\":1,\"windowNo\":0,\"message\":\"MANUAL TEST - $TIMESTAMP\",\"color\":1,\"fontSize\":24,\"speed\":3,\"effect\":0,\"stayTime\":5,\"alignment\":1}"
MANUAL_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$MANUAL_DATA" $SERVICE_URL/panel/send-manual)
echo "$MANUAL_RESPONSE" | jq .

# Verificar si sendManual fue exitoso
MANUAL_SUCCESS=$(echo "$MANUAL_RESPONSE" | jq -r '.success')
if [ "$MANUAL_SUCCESS" = "true" ]; then
    echo "✅ Flujo completo exitoso"
else
    echo "❌ ERROR: Flujo completo falló"
    echo "$MANUAL_RESPONSE" | jq .
fi

# ===== PASO 7: PROBAR ENVÍO DE TEXTO ROJO =====
echo ""
echo "=== PASO 7: Probando envío de texto rojo (como el ejemplo que funciona) ==="

RED_TEXT_DATA="{\"panelIP\":\"$TEST_PANEL_IP\",\"itemNum\":1,\"texts\":[\"PANEL 3\"],\"colors\":[1],\"fontSizes\":[2],\"showEffects\":[0]}"
RED_TEXT_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$RED_TEXT_DATA" $SERVICE_URL/panel/send-multi)
echo "$RED_TEXT_RESPONSE" | jq .

# Verificar si el envío de texto rojo fue exitoso
RED_TEXT_SUCCESS=$(echo "$RED_TEXT_RESPONSE" | jq -r '.success')
if [ "$RED_TEXT_SUCCESS" = "true" ]; then
    echo "✅ Envío de texto rojo exitoso"
else
    echo "❌ ERROR: Envío de texto rojo falló"
    echo "$RED_TEXT_RESPONSE" | jq .
fi

# ===== PASO 8: VERIFICAR ESTADO FINAL =====
echo ""
echo "=== PASO 8: Verificando estado final ==="

echo "8.1. Estado de paneles inicializados..."
FINAL_STATUS=$(curl -s $SERVICE_URL/panel/status)
echo "$FINAL_STATUS" | jq .

# Verificar si el panel está inicializado
PANEL_INITIALIZED=$(echo "$FINAL_STATUS" | jq -r ".data.initializedPanels.\"$TEST_PANEL_IP\"")
if [ "$PANEL_INITIALIZED" = "true" ]; then
    echo "✅ Panel $TEST_PANEL_IP está inicializado"
else
    echo "⚠️ Panel $TEST_PANEL_IP no está inicializado"
fi

echo "8.2. Logs del servicio después de las pruebas..."
echo "Últimas líneas del log:"
journalctl -u $SERVICE_NAME --no-pager -n 15

# ===== RESUMEN =====
echo ""
echo "=== RESUMEN DE PRUEBAS ==="
echo "🎯 Panel probado: $TEST_PANEL_IP"
echo "🔗 Servicio: $SERVICE_URL"
echo "📊 Resultados:"
echo "   - initNetwork: $([ "$INIT_SUCCESS" = "true" ] && echo "✅" || echo "❌")"
echo "   - setListener: $([ "$LISTENER_SUCCESS" = "true" ] && echo "✅" || echo "❌")"
echo "   - sendMulti: $([ "$SEND_MULTI_SUCCESS" = "true" ] && echo "✅" || echo "❌")"
echo "   - Flujo completo: $([ "$MANUAL_SUCCESS" = "true" ] && echo "✅" || echo "❌")"
echo "   - Texto rojo: $([ "$RED_TEXT_SUCCESS" = "true" ] && echo "✅" || echo "❌")"
echo "   - Panel inicializado: $([ "$PANEL_INITIALIZED" = "true" ] && echo "✅" || echo "❌")"

if [ "$INIT_SUCCESS" = "true" ] && [ "$LISTENER_SUCCESS" = "true" ] && [ "$SEND_MULTI_SUCCESS" = "true" ] && [ "$MANUAL_SUCCESS" = "true" ] && [ "$RED_TEXT_SUCCESS" = "true" ]; then
    echo ""
    echo "🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!"
    echo "✅ El flujo correcto de comunicación con paneles está funcionando"
    echo "✅ El texto rojo se envía correctamente como en el ejemplo"
    exit 0
else
    echo ""
    echo "⚠️ Algunas pruebas fallaron. Revisar logs para más detalles."
    exit 1
fi 