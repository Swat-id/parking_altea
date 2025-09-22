#!/usr/bin/env python3
"""
Servicio de Recepción de Push de Sensores - Puerto 3535
Recibe notificaciones push de sensores Fleximodo y actualiza la base de datos

Autor: Sistema SWATID
Versión: 4.1.0
Puerto: 3535
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import requests
from typing import Dict, Any, Optional

# Añadir el directorio src al path para importar modelos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import (
    IndividualSensor, 
    SensorStatusHistory, 
    SensorCurrentStatus, 
    ParkingSensorSummary,
    Parking
)

# Importar configuración del proyecto
from config import DB_URL

# Configuración
class Config:
    # Base de datos - usar la misma configuración que el API
    DATABASE_URL = DB_URL
    
    # Servidor
    HOST = '0.0.0.0'
    PORT = 3535
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/sensor_push_service.log')
    
    # Configuración de push
    MAX_HISTORY_DAYS = int(os.getenv('MAX_HISTORY_DAYS', '90'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))

# Configuración de logging
def setup_logging():
    """Configura el sistema de logging"""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar logging específico para SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Inicialización
app = Flask(__name__)
logger = setup_logging()

# Configuración de base de datos (igual que api_server.py)
engine = create_engine(Config.DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

class SensorPushProcessor:
    """Procesador de mensajes push de sensores"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SensorPushProcessor")
    
    def process_push_message(self, push_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje push de sensor
        
        Args:
            push_data: Datos del mensaje push
            
        Returns:
            Resultado del procesamiento
        """
        try:
            # Validar estructura del mensaje
            validation_result = self._validate_push_data(push_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Datos inválidos',
                    'details': validation_result['errors']
                }
            
            # Extraer información del sensor
            sensor_info = push_data.get('sensor_info', {})
            serial_number = sensor_info.get('serial_number')
            
            if not serial_number:
                return {
                    'success': False,
                    'error': 'serial_number es obligatorio en sensor_info'
                }
            
            # Crear sesión de base de datos
            session = Session()
            try:
                # Buscar el sensor en la base de datos
                sensor = session.query(IndividualSensor).filter_by(
                    serial_number=serial_number
                ).first()
                
                if not sensor:
                    self.logger.warning(f"Sensor no encontrado: {serial_number}")
                    return {
                        'success': False,
                        'error': f'Sensor {serial_number} no registrado en el sistema'
                    }
                
                # Procesar actualización de estado
                result = self._update_sensor_status(sensor, push_data, session)
                
                if result['success']:
                    # Actualizar resúmenes por parking
                    self._update_parking_summaries(sensor.parking_id, session)
                    
                    # Commit de la transacción
                    session.commit()
                    
                    self.logger.info(f"Push procesado exitosamente para sensor {serial_number}")
                
                return result
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error procesando push: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return {
                'success': False,
                'error': 'Error interno del servidor',
                'details': str(e)
            }
    
    def _validate_push_data(self, push_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida la estructura del mensaje push"""
        errors = []
        required_fields = ['status', 'timestamp', 'sensor_info']
        
        for field in required_fields:
            if field not in push_data:
                errors.append(f"Campo obligatorio faltante: {field}")
        
        # Validar sensor_info
        if 'sensor_info' in push_data:
            sensor_info = push_data['sensor_info']
            if not isinstance(sensor_info, dict):
                errors.append("sensor_info debe ser un objeto")
            elif 'serial_number' not in sensor_info:
                errors.append("serial_number es obligatorio en sensor_info")
        
        # Validar estado
        valid_statuses = ['free', 'busy', 'error', 'unknown', 'notcalib']
        if 'status' in push_data and push_data['status'] not in valid_statuses:
            errors.append(f"Estado inválido: {push_data['status']}. Válidos: {valid_statuses}")
        
        # Validar timestamp
        if 'timestamp' in push_data:
            try:
                datetime.strptime(push_data['timestamp'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                errors.append("Formato de timestamp inválido. Usar: YYYY-MM-DD HH:MM:SS")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _update_sensor_status(self, sensor: IndividualSensor, push_data: Dict[str, Any], session) -> Dict[str, Any]:
        """Actualiza el estado del sensor"""
        try:
            sensor_info = push_data.get('sensor_info', {})
            timestamp_str = push_data.get('timestamp')
            
            # Convertir timestamp
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # Extraer información de batería
            battery_voltage = sensor_info.get('battery_voltage')
            battery_capacity = sensor_info.get('battery_capacity')
            temperature = sensor_info.get('temperature')
            
            # Crear registro en historial
            history_record = SensorStatusHistory(
                sensor_id=sensor.id,
                status=push_data['status'],
                timestamp=timestamp,
                battery_voltage=battery_voltage,
                battery_capacity=battery_capacity,
                temperature=temperature,
                network_signal_strength=sensor_info.get('network_info', {}).get('signal_strength'),
                radar_only=sensor_info.get('radar_only', False),
                raw_data=push_data  # Almacenar datos completos como JSONB
            )
            
            session.add(history_record)
            
            # Actualizar o crear estado actual
            current_status = session.query(SensorCurrentStatus).filter_by(
                sensor_id=sensor.id
            ).first()
            
            if current_status:
                # Actualizar estado existente
                current_status.current_status = push_data['status']
                current_status.last_update = timestamp
                current_status.battery_voltage = battery_voltage
                current_status.battery_capacity = battery_capacity
                current_status.temperature = temperature
                current_status.network_signal_strength = sensor_info.get('network_info', {}).get('signal_strength')
                current_status.consecutive_errors = 0 if push_data['status'] != 'error' else current_status.consecutive_errors + 1
                current_status.last_successful_ping = timestamp if push_data['status'] != 'error' else current_status.last_successful_ping
            else:
                # Crear nuevo estado
                current_status = SensorCurrentStatus(
                    sensor_id=sensor.id,
                    current_status=push_data['status'],
                    last_update=timestamp,
                    battery_voltage=battery_voltage,
                    battery_capacity=battery_capacity,
                    temperature=temperature,
                    network_signal_strength=sensor_info.get('network_info', {}).get('signal_strength'),
                    consecutive_errors=1 if push_data['status'] == 'error' else 0,
                    last_successful_ping=timestamp if push_data['status'] != 'error' else None
                )
                session.add(current_status)
            
            return {
                'success': True,
                'sensor_id': sensor.id,
                'sensor_name': sensor.name,
                'previous_status': current_status.current_status if current_status else None,
                'new_status': push_data['status'],
                'timestamp': timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error actualizando estado del sensor {sensor.serial_number}: {str(e)}")
            return {
                'success': False,
                'error': f'Error actualizando sensor: {str(e)}'
            }
    
    def _update_parking_summaries(self, parking_id: Optional[int], session):
        """Actualiza los resúmenes por parking"""
        if not parking_id:
            return
        
        try:
            # Obtener todos los sensores del parking
            sensors = session.query(IndividualSensor).filter_by(
                parking_id=parking_id,
                is_active=True
            ).all()
            
            # Agrupar por tipo
            summaries_by_type = {}
            
            for sensor in sensors:
                sensor_type = sensor.sensor_type
                if sensor_type not in summaries_by_type:
                    summaries_by_type[sensor_type] = {
                        'total_sensors': 0,
                        'free_sensors': 0,
                        'busy_sensors': 0,
                        'error_sensors': 0
                    }
                
                summaries_by_type[sensor_type]['total_sensors'] += 1
                
                # Obtener estado actual
                current_status = session.query(SensorCurrentStatus).filter_by(
                    sensor_id=sensor.id
                ).first()
                
                if current_status:
                    status = current_status.current_status
                    if status == 'free':
                        summaries_by_type[sensor_type]['free_sensors'] += 1
                    elif status == 'busy':
                        summaries_by_type[sensor_type]['busy_sensors'] += 1
                    elif status in ['error', 'unknown', 'notcalib']:
                        summaries_by_type[sensor_type]['error_sensors'] += 1
            
            # Actualizar o crear resúmenes
            for sensor_type, counts in summaries_by_type.items():
                summary = session.query(ParkingSensorSummary).filter_by(
                    parking_id=parking_id,
                    sensor_type=sensor_type
                ).first()
                
                if summary:
                    summary.total_sensors = counts['total_sensors']
                    summary.free_sensors = counts['free_sensors']
                    summary.busy_sensors = counts['busy_sensors']
                    summary.error_sensors = counts['error_sensors']
                    summary.last_update = datetime.utcnow()
                else:
                    summary = ParkingSensorSummary(
                        parking_id=parking_id,
                        sensor_type=sensor_type,
                        total_sensors=counts['total_sensors'],
                        free_sensors=counts['free_sensors'],
                        busy_sensors=counts['busy_sensors'],
                        error_sensors=counts['error_sensors'],
                        last_update=datetime.utcnow()
                    )
                    session.add(summary)
            
            self.logger.debug(f"Resúmenes actualizados para parking {parking_id}")
            
        except Exception as e:
            self.logger.error(f"Error actualizando resúmenes del parking {parking_id}: {str(e)}")
    
    def process_manual_update(self, sensor_id: int, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una actualización manual de estado"""
        session = Session()
        try:
            sensor = session.query(IndividualSensor).filter_by(id=sensor_id).first()
            
            if not sensor:
                return {
                    'success': False,
                    'error': f'Sensor {sensor_id} no encontrado'
                }
            
            # Crear push simulado para actualización manual
            simulated_push = {
                'status': status_data['status'],
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'sensor_info': {
                    'serial_number': sensor.serial_number,
                    'battery_voltage': status_data.get('battery_voltage'),
                    'battery_capacity': status_data.get('battery_capacity'),
                    'temperature': status_data.get('temperature')
                }
            }
            
            # Procesar como push normal
            result = self._update_sensor_status(sensor, simulated_push, session)
            
            if result['success']:
                self._update_parking_summaries(sensor.parking_id, session)
                session.commit()
                self.logger.info(f"Actualización manual procesada para sensor {sensor.serial_number}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en actualización manual: {str(e)}")
            session.rollback()
            return {
                'success': False,
                'error': f'Error en actualización manual: {str(e)}'
            }
        finally:
            session.close()

# Instancia global del procesador
processor = SensorPushProcessor()

# ============================================================================
# ENDPOINTS DE LA API
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud del servicio"""
    return jsonify({
        'status': 'healthy',
        'service': 'sensor-push-service',
        'version': '4.1.0',
        'timestamp': datetime.utcnow().isoformat(),
        'port': Config.PORT
    })

@app.route('/push', methods=['POST'])
def receive_push():
    """
    Endpoint principal para recibir push de sensores
    
    Recibe: CarparkSlotStatusBody según especificación Fleximodo
    """
    try:
        # Validar Content-Type
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type debe ser application/json'
            }), 400
        
        push_data = request.get_json()
        
        if not push_data:
            return jsonify({
                'success': False,
                'error': 'Datos JSON requeridos'
            }), 400
        
        logger.info(f"Push recibido: {push_data.get('sensor_info', {}).get('serial_number', 'UNKNOWN')}")
        
        # Procesar el mensaje
        result = processor.process_push_message(push_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint push: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/manual-update', methods=['POST'])
def manual_update():
    """
    Endpoint para actualizaciones manuales de estado
    
    Body: {
        "sensor_id": 123,
        "status": "busy",
        "battery_capacity": 85,
        "battery_voltage": 3.2,
        "temperature": 23.5
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type debe ser application/json'
            }), 400
        
        data = request.get_json()
        
        if not data or 'sensor_id' not in data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'sensor_id y status son obligatorios'
            }), 400
        
        logger.info(f"Actualización manual para sensor {data['sensor_id']}: {data['status']}")
        
        result = processor.process_manual_update(data['sensor_id'], data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en actualización manual: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/', methods=['POST'])
def receive_sensor_root():
    """
    Endpoint raíz para recibir datos de sensores
    Los sensores Fleximodo están enviando POST a / directamente
    """
    try:
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        logger.info(f"Recibiendo datos de sensor desde IP: {client_ip}")
        
        # Intentar procesar como JSON primero
        if request.is_json:
            try:
                push_data = request.get_json()
                logger.info(f"Datos JSON recibidos: {push_data}")
                
                # Si los datos tienen la estructura esperada, procesarlos normalmente
                if isinstance(push_data, dict) and 'sensor_info' in push_data:
                    result = processor.process_push_message(push_data)
                    
                    if result['success']:
                        return jsonify(result), 200
                    else:
                        return jsonify(result), 400
                else:
                    # Datos JSON pero estructura desconocida - logear para análisis
                    logger.warning(f"Estructura JSON desconocida desde {client_ip}: {push_data}")
                    return jsonify({
                        'status': 'received',
                        'message': 'Datos JSON recibidos pero estructura desconocida',
                        'timestamp': datetime.utcnow().isoformat(),
                        'client_ip': client_ip
                    }), 200
                    
            except Exception as e:
                logger.error(f"Error procesando JSON desde {client_ip}: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Error procesando datos JSON',
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
        else:
            # Datos no JSON - obtener raw data
            try:
                raw_data = request.get_data(as_text=True)
                content_type = request.headers.get('Content-Type', 'unknown')
                
                logger.info(f"Datos RAW recibidos desde {client_ip}")
                logger.info(f"Content-Type: {content_type}")
                logger.info(f"Raw data (primeros 200 chars): {raw_data[:200]}")
                
                # Intentar parsear como diferentes formatos
                parsed_data = None
                
                # Intentar JSON manual
                if raw_data.strip().startswith('{'):
                    try:
                        parsed_data = json.loads(raw_data)
                        logger.info(f"Raw data parseado como JSON: {parsed_data}")
                    except:
                        pass
                
                return jsonify({
                    'status': 'received',
                    'message': 'Datos raw recibidos y logueados',
                    'timestamp': datetime.utcnow().isoformat(),
                    'client_ip': client_ip,
                    'content_type': content_type,
                    'data_length': len(raw_data),
                    'parsed_json': parsed_data is not None
                }), 200
                
            except Exception as e:
                logger.error(f"Error procesando datos raw desde {client_ip}: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Error procesando datos raw',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
            
    except Exception as e:
        logger.error(f"Error general en endpoint raíz: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error interno del servidor',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Endpoint para obtener estadísticas del servicio"""
    session = Session()
    try:
        # Estadísticas básicas
        total_sensors = session.query(IndividualSensor).filter_by(is_active=True).count()
        
        # Conteo por estados
        status_counts = session.execute(text("""
            SELECT 
                scs.current_status,
                COUNT(*) as count
            FROM sensor_current_status scs
            JOIN individual_sensors s ON s.id = scs.sensor_id
            WHERE s.is_active = true
            GROUP BY scs.current_status
        """)).fetchall()
        
        # Conteo por tipos
        type_counts = session.execute(text("""
            SELECT 
                s.sensor_type,
                COUNT(*) as count
            FROM individual_sensors s
            WHERE s.is_active = true
            GROUP BY s.sensor_type
        """)).fetchall()
        
        return jsonify({
            'total_sensors': total_sensors,
            'status_distribution': {row[0]: row[1] for row in status_counts},
            'type_distribution': {row[0]: row[1] for row in type_counts},
            'service_info': {
                'version': '4.1.0',
                'uptime': 'N/A',  # TODO: implementar tracking de uptime
                'port': Config.PORT
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo estadísticas',
            'details': str(e)
        }), 500
    finally:
        session.close()

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_tables():
    """Crea las tablas necesarias si no existen"""
    try:
        # Las tablas ya están creadas por api_server.py
        # Solo verificamos la conexión
        session = Session()
        session.execute(text("SELECT 1"))
        session.close()
        logger.info("Conexión a base de datos verificada")
    except Exception as e:
        logger.error(f"Error verificando conexión a base de datos: {str(e)}")
        raise

def main():
    """Función principal del servicio"""
    try:
        logger.info("=== INICIANDO SERVICIO PUSH SENSORES v4.1.0 ===")
        logger.info(f"Puerto: {Config.PORT}")
        logger.info(f"Base de datos: {Config.DATABASE_URL}")
        logger.info(f"Debug: {Config.DEBUG}")
        
        # Crear tablas si es necesario
        create_tables()
        
        # Iniciar servidor
        logger.info("Servicio iniciado correctamente")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Servicio detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
