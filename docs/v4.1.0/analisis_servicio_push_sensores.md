# Análisis: Servicio de Recepción de Push de Sensores (Puerto 3535)

## Descripción General

El servicio en puerto 3535 recibirá notificaciones push de cambios de estado de sensores Fleximodo, procesará la información y actualizará la base de datos con los estados individuales de las plazas de parking.

## Especificación del Protocolo Push

### Estructura del Mensaje Push

Según la especificación proporcionada, el endpoint recibirá:

```json
{
  "carpark_id": 123,
  "carpark_code": "PARKING_A",
  "floor": "0",
  "id": 456,
  "number": "A01",
  "status": "busy",
  "idle": false,
  "timestamp": "2025-09-19 10:30:00",
  "parking_cards": ["1A2B3C4D", "5E6F7G8H"],
  "floor_stats": {
    "slot_count": 50,
    "free_count": 25,
    "busy_count": 23,
    "notcalib_count": 2
  },
  "sensor_info": {
    "serial_number": "FLX001234",
    "network_info": {
      "ip_address": "192.168.1.100",
      "signal_strength": -65,
      "connection_type": "WiFi"
    },
    "temperature": 23.5,
    "battery_voltage": 3.2,
    "battery_capacity": 85,
    "visible_cards": ["1A2B3C4D"],
    "radar_only": false
  }
}
```

### Estados Posibles

- **busy**: Plaza ocupada
- **free**: Plaza libre  
- **error**: Sensor con error
- **unknown**: Estado desconocido
- **notcalib**: Sensor no calibrado

### Campos Críticos

1. **sensor_info.serial_number**: Identificador único del sensor
2. **status**: Estado actual de la plaza
3. **timestamp**: Momento del cambio de estado
4. **idle**: Indica si es un mensaje de keep-alive
5. **sensor_info**: Información técnica del sensor

## Arquitectura del Servicio

### Componente Principal: Servidor Flask

```python
# Archivo: src/sensor_push_service.py

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import logging
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import IndividualSensor, SensorStatusHistory, SensorCurrentStatus, ParkingSensorSummary
import config

app = Flask(__name__)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de base de datos
engine = create_engine(config.DB_URL)
Session = sessionmaker(bind=engine)

class SensorPushProcessor:
    """Procesador de mensajes push de sensores"""
    
    def __init__(self):
        self.session = Session()
    
    def process_push_message(self, push_data):
        """Procesar mensaje push recibido"""
        try:
            # Validar estructura del mensaje
            if not self._validate_push_structure(push_data):
                return {'success': False, 'error': 'Invalid message structure'}
            
            # Extraer información del sensor
            sensor_info = push_data.get('sensor_info', {})
            serial_number = sensor_info.get('serial_number')
            
            if not serial_number:
                return {'success': False, 'error': 'Missing serial_number'}
            
            # Buscar sensor en base de datos
            sensor = self._find_sensor_by_serial(serial_number)
            if not sensor:
                return {'success': False, 'error': f'Sensor not found: {serial_number}'}
            
            # Procesar cambio de estado
            result = self._process_status_change(sensor, push_data)
            
            # Actualizar resumen por parking si está vinculado
            if sensor.parking_id:
                self._update_parking_summary(sensor.parking_id, sensor.sensor_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing push message: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.session.close()
```

### Endpoint Principal

```python
@app.route('/push', methods=['POST'])
def receive_sensor_push():
    """
    Endpoint principal para recibir push de sensores
    URL: http://157.180.91.63:3535/push
    """
    try:
        # Obtener datos del request
        push_data = request.get_json()
        
        if not push_data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        # Log del mensaje recibido (solo en desarrollo)
        logger.info(f"Push received from sensor: {push_data.get('sensor_info', {}).get('serial_number', 'unknown')}")
        
        # Procesar mensaje
        processor = SensorPushProcessor()
        result = processor.process_push_message(push_data)
        
        # Responder al sensor
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Push processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'timestamp': datetime.utcnow().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Error in push endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del servicio"""
    return jsonify({
        'status': 'healthy',
        'service': 'sensor-push-service',
        'version': '4.1.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/stats', methods=['GET'])
def service_stats():
    """Estadísticas del servicio"""
    # Implementar métricas básicas
    return jsonify({
        'messages_processed': 0,  # Implementar contador
        'errors': 0,              # Implementar contador de errores
        'uptime': '0h 0m',        # Implementar cálculo de uptime
        'last_message': None      # Timestamp del último mensaje
    })
```

### Validaciones y Procesamiento

```python
class SensorPushProcessor:
    
    def _validate_push_structure(self, push_data):
        """Validar estructura básica del mensaje push"""
        required_fields = ['status', 'timestamp', 'sensor_info']
        
        for field in required_fields:
            if field not in push_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validar sensor_info
        sensor_info = push_data['sensor_info']
        if 'serial_number' not in sensor_info:
            logger.warning("Missing serial_number in sensor_info")
            return False
        
        # Validar formato de timestamp
        try:
            datetime.strptime(push_data['timestamp'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.warning(f"Invalid timestamp format: {push_data['timestamp']}")
            return False
        
        return True
    
    def _find_sensor_by_serial(self, serial_number):
        """Buscar sensor por número de serie"""
        try:
            return self.session.query(IndividualSensor).filter(
                IndividualSensor.serial_number == serial_number,
                IndividualSensor.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Error finding sensor {serial_number}: {e}")
            return None
    
    def _process_status_change(self, sensor, push_data):
        """Procesar cambio de estado del sensor"""
        try:
            # Extraer datos del push
            new_status = push_data['status']
            timestamp_str = push_data['timestamp']
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            sensor_info = push_data.get('sensor_info', {})
            is_idle = push_data.get('idle', False)
            
            # Verificar si es un mensaje IDLE (keep-alive)
            if is_idle:
                logger.debug(f"IDLE message received from sensor {sensor.serial_number}")
                # Solo actualizar last_successful_ping
                self._update_last_ping(sensor, timestamp)
                return {'success': True, 'message': 'IDLE message processed'}
            
            # Verificar si el estado realmente cambió
            current_status = self._get_current_status(sensor)
            if current_status and current_status.current_status == new_status:
                logger.debug(f"Status unchanged for sensor {sensor.serial_number}: {new_status}")
                return {'success': True, 'message': 'Status unchanged'}
            
            # Crear registro histórico
            history_record = SensorStatusHistory(
                sensor_id=sensor.id,
                status=new_status,
                timestamp=timestamp,
                battery_voltage=sensor_info.get('battery_voltage'),
                battery_capacity=sensor_info.get('battery_capacity'),
                temperature=sensor_info.get('temperature'),
                network_signal_strength=sensor_info.get('network_info', {}).get('signal_strength'),
                radar_only=sensor_info.get('radar_only', False),
                raw_data=push_data  # Almacenar datos completos
            )
            
            self.session.add(history_record)
            
            # Actualizar estado actual
            self._update_current_status(sensor, new_status, timestamp, sensor_info)
            
            # Commit de cambios
            self.session.commit()
            
            logger.info(f"Status updated for sensor {sensor.serial_number}: {new_status}")
            
            return {
                'success': True,
                'message': 'Status change processed',
                'sensor_id': sensor.id,
                'old_status': current_status.current_status if current_status else 'unknown',
                'new_status': new_status,
                'timestamp': timestamp_str
            }
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error processing status change: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_current_status(self, sensor, new_status, timestamp, sensor_info):
        """Actualizar estado actual del sensor"""
        current_status = self.session.query(SensorCurrentStatus).filter(
            SensorCurrentStatus.sensor_id == sensor.id
        ).first()
        
        if current_status:
            # Actualizar registro existente
            current_status.current_status = new_status
            current_status.last_update = timestamp
            current_status.battery_voltage = sensor_info.get('battery_voltage')
            current_status.battery_capacity = sensor_info.get('battery_capacity')
            current_status.temperature = sensor_info.get('temperature')
            current_status.network_signal_strength = sensor_info.get('network_info', {}).get('signal_strength')
            current_status.last_successful_ping = timestamp
            
            # Reset contador de errores si el status no es error
            if new_status != 'error':
                current_status.consecutive_errors = 0
            else:
                current_status.consecutive_errors = (current_status.consecutive_errors or 0) + 1
        else:
            # Crear nuevo registro
            current_status = SensorCurrentStatus(
                sensor_id=sensor.id,
                current_status=new_status,
                last_update=timestamp,
                battery_voltage=sensor_info.get('battery_voltage'),
                battery_capacity=sensor_info.get('battery_capacity'),
                temperature=sensor_info.get('temperature'),
                network_signal_strength=sensor_info.get('network_info', {}).get('signal_strength'),
                consecutive_errors=1 if new_status == 'error' else 0,
                last_successful_ping=timestamp
            )
            self.session.add(current_status)
    
    def _update_parking_summary(self, parking_id, sensor_type):
        """Actualizar resumen de sensores por parking"""
        try:
            # Obtener todos los sensores del parking y tipo
            sensors_query = self.session.query(IndividualSensor).filter(
                IndividualSensor.parking_id == parking_id,
                IndividualSensor.sensor_type == sensor_type,
                IndividualSensor.is_active == True
            )
            
            total_sensors = sensors_query.count()
            
            # Contar por estado
            free_count = 0
            busy_count = 0
            error_count = 0
            
            for sensor in sensors_query:
                current_status = self.session.query(SensorCurrentStatus).filter(
                    SensorCurrentStatus.sensor_id == sensor.id
                ).first()
                
                if current_status:
                    if current_status.current_status == 'free':
                        free_count += 1
                    elif current_status.current_status == 'busy':
                        busy_count += 1
                    elif current_status.current_status in ['error', 'unknown', 'notcalib']:
                        error_count += 1
            
            # Buscar o crear resumen
            summary = self.session.query(ParkingSensorSummary).filter(
                ParkingSensorSummary.parking_id == parking_id,
                ParkingSensorSummary.sensor_type == sensor_type
            ).first()
            
            if summary:
                # Actualizar existente
                summary.total_sensors = total_sensors
                summary.free_sensors = free_count
                summary.busy_sensors = busy_count
                summary.error_sensors = error_count
                summary.last_update = datetime.utcnow()
            else:
                # Crear nuevo
                summary = ParkingSensorSummary(
                    parking_id=parking_id,
                    sensor_type=sensor_type,
                    total_sensors=total_sensors,
                    free_sensors=free_count,
                    busy_sensors=busy_count,
                    error_sensors=error_count,
                    last_update=datetime.utcnow()
                )
                self.session.add(summary)
            
            logger.debug(f"Updated parking summary: {parking_id}, {sensor_type} - Total: {total_sensors}, Free: {free_count}, Busy: {busy_count}, Error: {error_count}")
            
        except Exception as e:
            logger.error(f"Error updating parking summary: {e}")
```

## Configuración del Servicio

### Archivo de Configuración

```python
# Archivo: src/sensor_push_config.py

import os

class SensorPushConfig:
    # Configuración del servidor
    HOST = '0.0.0.0'  # Escuchar en todas las interfaces
    PORT = 3535
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configuración de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configuración de base de datos
    DATABASE_URL = os.getenv('DATABASE_URL', config.DB_URL)
    
    # Configuración de seguridad
    ALLOWED_IPS = os.getenv('ALLOWED_IPS', '').split(',') if os.getenv('ALLOWED_IPS') else []
    API_KEY = os.getenv('SENSOR_API_KEY', '')  # Para autenticación opcional
    
    # Configuración de procesamiento
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB máximo por mensaje
    MESSAGE_TIMEOUT = 30  # Timeout en segundos
    
    # Configuración de métricas
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
    METRICS_RETENTION_DAYS = int(os.getenv('METRICS_RETENTION_DAYS', '30'))
```

### Script de Inicio

```python
# Archivo: src/start_sensor_push_service.py

#!/usr/bin/env python3
"""
Servicio de recepción de push de sensores
Puerto: 3535
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sensor_push_service import app
from sensor_push_config import SensorPushConfig
import logging

def setup_logging():
    """Configurar logging del servicio"""
    logging.basicConfig(
        level=getattr(logging, SensorPushConfig.LOG_LEVEL),
        format=SensorPushConfig.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/sensor_push_service.log', mode='a')
        ]
    )

def main():
    """Función principal del servicio"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Sensor Push Service v4.1.0")
    logger.info(f"Listening on {SensorPushConfig.HOST}:{SensorPushConfig.PORT}")
    
    try:
        app.run(
            host=SensorPushConfig.HOST,
            port=SensorPushConfig.PORT,
            debug=SensorPushConfig.DEBUG,
            threaded=True  # Permitir múltiples conexiones simultáneas
        )
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Integración con Sistema Existente

### Middleware de Seguridad

```python
# Archivo: src/sensor_push_middleware.py

from flask import request, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def validate_ip_whitelist(allowed_ips):
    """Middleware para validar IPs permitidas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if allowed_ips and request.remote_addr not in allowed_ips:
                logger.warning(f"Unauthorized IP attempt: {request.remote_addr}")
                return jsonify({'error': 'Unauthorized IP'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_api_key(api_key):
    """Middleware para validar API key opcional"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if api_key:
                provided_key = request.headers.get('X-API-Key')
                if provided_key != api_key:
                    logger.warning(f"Invalid API key from {request.remote_addr}")
                    return jsonify({'error': 'Invalid API key'}), 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_request():
    """Middleware para logging de requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.info(f"Push request from {request.remote_addr} - Size: {len(request.data)} bytes")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Métricas y Monitorización

```python
# Archivo: src/sensor_push_metrics.py

import time
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class SensorPushMetrics:
    """Clase para recopilar métricas del servicio"""
    
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.error_count = 0
        self.status_changes = defaultdict(int)
        self.sensors_active = set()
        self.last_message_time = None
        self._lock = threading.Lock()
    
    def record_message(self, sensor_serial, status, success=True):
        """Registrar mensaje procesado"""
        with self._lock:
            self.message_count += 1
            if not success:
                self.error_count += 1
            else:
                self.status_changes[status] += 1
                self.sensors_active.add(sensor_serial)
            self.last_message_time = datetime.utcnow()
    
    def get_stats(self):
        """Obtener estadísticas actuales"""
        with self._lock:
            uptime_seconds = time.time() - self.start_time
            uptime_hours = uptime_seconds // 3600
            uptime_minutes = (uptime_seconds % 3600) // 60
            
            return {
                'uptime': f"{int(uptime_hours)}h {int(uptime_minutes)}m",
                'messages_processed': self.message_count,
                'errors': self.error_count,
                'success_rate': (self.message_count - self.error_count) / max(self.message_count, 1) * 100,
                'active_sensors': len(self.sensors_active),
                'status_distribution': dict(self.status_changes),
                'last_message': self.last_message_time.isoformat() if self.last_message_time else None,
                'messages_per_hour': self.message_count / max(uptime_seconds / 3600, 1)
            }

# Instancia global de métricas
metrics = SensorPushMetrics()
```

## Despliegue y Configuración

### Archivo de Servicio Systemd

```ini
# Archivo: deploy/sensor-push-service.service

[Unit]
Description=Sensor Push Service v4.1.0
After=network.target postgresql.service

[Service]
Type=simple
User=parking
Group=parking
WorkingDirectory=/opt/parking_altea/src
Environment=PYTHONPATH=/opt/parking_altea
Environment=FLASK_ENV=production
Environment=LOG_LEVEL=INFO
ExecStart=/opt/parking_altea/venv/bin/python start_sensor_push_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Configuración de recursos
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### Script de Despliegue

```bash
#!/bin/bash
# Archivo: deploy/deploy_sensor_push_service.sh

set -e

echo "🚀 Deploying Sensor Push Service v4.1.0"

# Variables
SERVICE_NAME="sensor-push-service"
SERVICE_PORT="3535"
DEPLOY_DIR="/opt/parking_altea"
LOG_DIR="$DEPLOY_DIR/logs"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Detener servicio si está corriendo
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Stopping existing service..."
    sudo systemctl stop "$SERVICE_NAME"
fi

# Copiar archivos del servicio
echo "Copying service files..."
cp src/sensor_push_service.py "$DEPLOY_DIR/src/"
cp src/sensor_push_config.py "$DEPLOY_DIR/src/"
cp src/start_sensor_push_service.py "$DEPLOY_DIR/src/"
cp src/sensor_push_middleware.py "$DEPLOY_DIR/src/"
cp src/sensor_push_metrics.py "$DEPLOY_DIR/src/"

# Instalar archivo de servicio
echo "Installing systemd service..."
sudo cp "deploy/$SERVICE_NAME.service" "/etc/systemd/system/"
sudo systemctl daemon-reload

# Verificar puerto disponible
if netstat -tuln | grep ":$SERVICE_PORT "; then
    echo "⚠️  Warning: Port $SERVICE_PORT is already in use"
    echo "Killing processes on port $SERVICE_PORT..."
    sudo fuser -k "$SERVICE_PORT/tcp" || true
    sleep 2
fi

# Iniciar servicio
echo "Starting service..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# Verificar estado
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service started successfully"
    echo "Service status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    
    echo ""
    echo "Testing service endpoint..."
    curl -s "http://localhost:$SERVICE_PORT/health" | jq . || echo "Service responding"
else
    echo "❌ Service failed to start"
    echo "Service logs:"
    sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi

echo ""
echo "🎉 Sensor Push Service deployment completed!"
echo "Service URL: http://157.180.91.63:$SERVICE_PORT"
echo "Health check: http://157.180.91.63:$SERVICE_PORT/health"
echo "Stats: http://157.180.91.63:$SERVICE_PORT/stats"
```

### Configuración de Firewall

```bash
#!/bin/bash
# Archivo: deploy/configure_firewall_sensor_push.sh

echo "Configuring firewall for Sensor Push Service..."

# Permitir tráfico en puerto 3535
sudo ufw allow 3535/tcp comment "Sensor Push Service"

# Opcional: Restringir a IPs específicas si se conocen
# sudo ufw allow from 192.168.1.0/24 to any port 3535

echo "Firewall configured for port 3535"
sudo ufw status
```

## Testing y Validación

### Tests del Servicio

```python
# Archivo: tests/test_sensor_push_service.py

import unittest
import json
import requests
from datetime import datetime

class TestSensorPushService(unittest.TestCase):
    
    def setUp(self):
        self.base_url = "http://localhost:3535"
        self.test_push_data = {
            "carpark_id": 1,
            "carpark_code": "TEST_PARKING",
            "floor": "0",
            "id": 1,
            "number": "A01",
            "status": "busy",
            "idle": False,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "parking_cards": ["1A2B3C4D"],
            "floor_stats": {
                "slot_count": 10,
                "free_count": 5,
                "busy_count": 4,
                "notcalib_count": 1
            },
            "sensor_info": {
                "serial_number": "TEST001",
                "network_info": {
                    "ip_address": "192.168.1.100",
                    "signal_strength": -65
                },
                "temperature": 23.5,
                "battery_voltage": 3.2,
                "battery_capacity": 85,
                "visible_cards": ["1A2B3C4D"],
                "radar_only": False
            }
        }
    
    def test_health_endpoint(self):
        """Test endpoint de salud"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_valid_push_message(self):
        """Test procesamiento de mensaje push válido"""
        response = requests.post(
            f"{self.base_url}/push",
            json=self.test_push_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Debería responder exitosamente o con error conocido
        self.assertIn(response.status_code, [200, 400])
        data = response.json()
        self.assertIn('success', data)
    
    def test_invalid_push_message(self):
        """Test mensaje push inválido"""
        invalid_data = {"invalid": "data"}
        response = requests.post(
            f"{self.base_url}/push",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_stats_endpoint(self):
        """Test endpoint de estadísticas"""
        response = requests.get(f"{self.base_url}/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('messages_processed', data)

if __name__ == '__main__':
    unittest.main()
```

### Script de Testing Manual

```bash
#!/bin/bash
# Archivo: tests/manual_test_sensor_push.sh

SERVICE_URL="http://157.180.91.63:3535"

echo "🧪 Testing Sensor Push Service"

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$SERVICE_URL/health" | jq .

# Test 2: Stats endpoint
echo -e "\n2. Testing stats endpoint..."
curl -s "$SERVICE_URL/stats" | jq .

# Test 3: Valid push message
echo -e "\n3. Testing valid push message..."
curl -X POST "$SERVICE_URL/push" \
  -H "Content-Type: application/json" \
  -d '{
    "carpark_id": 1,
    "carpark_code": "TEST",
    "floor": "0",
    "id": 1,
    "number": "A01",
    "status": "busy",
    "idle": false,
    "timestamp": "'$(date '+%Y-%m-%d %H:%M:%S')'",
    "parking_cards": ["1A2B3C4D"],
    "floor_stats": {
      "slot_count": 10,
      "free_count": 5,
      "busy_count": 4,
      "notcalib_count": 1
    },
    "sensor_info": {
      "serial_number": "TEST001",
      "temperature": 23.5,
      "battery_voltage": 3.2,
      "battery_capacity": 85,
      "radar_only": false
    }
  }' | jq .

# Test 4: Invalid message
echo -e "\n4. Testing invalid message..."
curl -X POST "$SERVICE_URL/push" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}' | jq .

echo -e "\n✅ Testing completed"
```

## Monitorización y Alertas

### Script de Monitorización

```bash
#!/bin/bash
# Archivo: scripts/monitor_sensor_push_service.sh

SERVICE_NAME="sensor-push-service"
SERVICE_URL="http://localhost:3535"
LOG_FILE="/var/log/parking/sensor_push_monitor.log"

# Función de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Verificar si el servicio está corriendo
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    log_message "ERROR: Service $SERVICE_NAME is not running"
    # Intentar reiniciar
    sudo systemctl start "$SERVICE_NAME"
    sleep 5
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_message "INFO: Service $SERVICE_NAME restarted successfully"
    else
        log_message "CRITICAL: Failed to restart service $SERVICE_NAME"
        exit 1
    fi
fi

# Verificar endpoint de salud
if ! curl -s --max-time 10 "$SERVICE_URL/health" > /dev/null; then
    log_message "ERROR: Health endpoint not responding"
    exit 1
fi

# Obtener estadísticas
STATS=$(curl -s --max-time 10 "$SERVICE_URL/stats")
if [ $? -eq 0 ]; then
    ERROR_RATE=$(echo "$STATS" | jq -r '.error_rate // 0')
    MESSAGES_PROCESSED=$(echo "$STATS" | jq -r '.messages_processed // 0')
    
    log_message "INFO: Messages processed: $MESSAGES_PROCESSED, Error rate: $ERROR_RATE%"
    
    # Alertar si hay muchos errores
    if (( $(echo "$ERROR_RATE > 10" | bc -l) )); then
        log_message "WARNING: High error rate detected: $ERROR_RATE%"
    fi
else
    log_message "ERROR: Failed to get service statistics"
fi

log_message "INFO: Service monitoring completed successfully"
```

## Estimación de Esfuerzo

| Componente | Estimación | Descripción |
|------------|------------|-------------|
| **Servicio Flask Base** | 6 horas | Endpoint, validaciones, estructura básica |
| **Procesamiento de Push** | 8 horas | Lógica de procesamiento, actualización BD |
| **Middleware y Seguridad** | 4 horas | Validaciones IP, API key, logging |
| **Métricas y Monitorización** | 4 horas | Estadísticas, health checks |
| **Scripts de Despliegue** | 3 horas | Systemd, firewall, automatización |
| **Testing y Validación** | 5 horas | Tests unitarios, integración, manual |
| **Documentación** | 2 horas | Docs de API, configuración |
| **Total** | **32 horas** | Aproximadamente 4 días de trabajo |

## Consideraciones de Producción

### Escalabilidad
- Usar Gunicorn o uWSGI en lugar de Flask dev server
- Implementar pool de conexiones a base de datos
- Considerar Redis para cache de estados frecuentes

### Seguridad
- Implementar rate limiting
- Validar tamaño de mensajes
- Logs de seguridad para intentos no autorizados

### Rendimiento
- Procesar mensajes de forma asíncrona si el volumen es alto
- Implementar batch updates para resúmenes de parking
- Optimizar consultas de base de datos

### Monitorización
- Integrar con Prometheus/Grafana para métricas
- Alertas automáticas por email/Slack
- Dashboard de estado en tiempo real

---

*Análisis completado para el servicio de recepción de push de sensores en puerto 3535*
