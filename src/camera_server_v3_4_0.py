#!/usr/bin/env python3
"""
Camera Server v3.4.0 - Integrado con CameraMessageProcessor
Servidor optimizado para procesamiento concurrente de mensajes de cámaras SIN actualización de paneles

Cambios principales en v3.4.0:
- Integración completa con CameraMessageProcessor para concurrencia total
- Eliminación del código de actualización de paneles del flujo de mensajes
- Respuestas inmediatas <200ms sin esperar paneles
- Endpoint /camera/stats para estadísticas del procesador
- Compatibilidad hacia atrás mantenida en respuestas
- Logging optimizado y estructurado
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import logging
import time
import sys
import os

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar el nuevo procesador de mensajes
try:
    from camera_message_processor import CameraMessageProcessor
    logger.info("CameraMessageProcessor importado correctamente")
except ImportError as e:
    logger.error(f"Error importando CameraMessageProcessor: {e}")
    sys.exit(1)

# Crear aplicación Flask
app = Flask(__name__)

# Inicializar procesador global de mensajes
# Configuración optimizada para producción
message_processor = CameraMessageProcessor(
    max_workers=10,      # 10 workers concurrentes
    cache_duration=300   # 5 minutos cache duplicados
)

logger.info("Camera Server v3.4.0 inicializado con CameraMessageProcessor")


@app.route('/camera', methods=['POST'])
def handle_camera():
    """
    Endpoint principal para recepción de mensajes de cámaras v3.4.0
    
    CAMBIOS PRINCIPALES:
    - Procesamiento 100% concurrente con CameraMessageProcessor
    - SIN actualización de paneles en el flujo
    - Respuestas inmediatas <200ms
    - Compatibilidad total hacia atrás en formato de respuesta
    """
    start_time = time.time()
    
    # Obtener información del cliente
    ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    
    # Log inicial de recepción
    logger.info(f"=== CAMERA MESSAGE RECEIVED v3.4.0 ===")
    logger.info(f"Source IP: {ip}")
    
    try:
        # Capturar raw data para logging
        raw_data = request.get_data(as_text=True)
        logger.debug(f"Raw body: {raw_data}")
        
        # Parsear JSON
        try:
            data = request.get_json(force=True)
            logger.info(f"JSON parsed from {ip}: {json.dumps(data)}")
        except Exception as e:
            logger.error(f"JSON inválido de {ip}: {e}")
            return jsonify({
                'error': 'Invalid JSON format',
                'status': 'error',
                'processing_time_ms': (time.time() - start_time) * 1000,
                'version': 'v3.4.0'
            }), 400
        
        if not data:
            logger.error(f"Datos vacíos de {ip}")
            return jsonify({
                'error': 'Empty JSON data',
                'status': 'error',
                'processing_time_ms': (time.time() - start_time) * 1000,
                'version': 'v3.4.0'
            }), 400
        
        # Extraer y validar campos
        device = data.get('device', '')
        line = data.get('line', 0)
        vehicle_in = data.get('Vehicle In', 0)  # Mantener compatibilidad con formato actual
        vehicle_out = data.get('Vehicle Out', 0)
        
        # Validar campos requeridos
        if line is None or vehicle_in is None or vehicle_out is None:
            error_msg = f"Campos faltantes: line={line}, vehicle_in={vehicle_in}, vehicle_out={vehicle_out}"
            logger.error(f"{error_msg} de {ip}")
            return jsonify({
                'error': error_msg,
                'status': 'error',
                'processing_time_ms': (time.time() - start_time) * 1000,
                'version': 'v3.4.0'
            }), 400
        
        # Log de datos recibidos
        logger.info(f"Camera data: Device={device}, Line={line}, In={vehicle_in}, Out={vehicle_out}")
        
        # Preparar datos para el procesador
        message_data = {
            'device': device,
            'line': line,
            'vehicle_in': vehicle_in,
            'vehicle_out': vehicle_out,
            'source_ip': ip,
            'raw_data': raw_data,
            'timestamp': datetime.now()
        }
        
        # PROCESAR MENSAJE DE FORMA ASÍNCRONA CON EL NUEVO PROCESADOR
        future = message_processor.process_message_async(message_data)
        
        # Esperar resultado con timeout de 5 segundos
        try:
            result = future.result(timeout=5)
            processing_time = (time.time() - start_time) * 1000
            
            # Preparar respuesta compatible hacia atrás
            if result.status == 'success':
                response = {
                    'status': 'ok',
                    'message_id': result.message_id,
                    'processing_time_ms': processing_time,
                    'updated_parkings': len(result.updated_parkings),
                    'parkings': [
                        {
                            'name': p['name'],
                            'occupancy': p['new_occupancy'],
                            'status': p['status']
                        } for p in result.updated_parkings
                    ],
                    'reset_detected': result.reset_detected,
                    'version': 'v3.4.0',
                    'note': 'Panels will be updated by background worker within 2 minutes'
                }
                
                logger.info(f"Mensaje procesado exitosamente en {processing_time:.2f}ms - ID: {result.message_id}")
                return jsonify(response)
                
            elif result.status == 'duplicate':
                response = {
                    'status': 'duplicate',
                    'message_id': result.message_id,
                    'processing_time_ms': processing_time,
                    'message': 'Mensaje duplicado detectado',
                    'version': 'v3.4.0'
                }
                
                logger.info(f"Mensaje duplicado detectado en {processing_time:.2f}ms")
                return jsonify(response)
                
            elif result.status == 'camera_not_found':
                response = {
                    'error': 'Camera not found',
                    'status': 'error',
                    'message_id': result.message_id,
                    'processing_time_ms': processing_time,
                    'details': f"Device: {device}, Line: {line}",
                    'version': 'v3.4.0'
                }
                
                logger.warning(f"Cámara no encontrada en {processing_time:.2f}ms: {device}:{line}")
                return jsonify(response), 404
                
            elif result.status == 'invalid_delta':
                response = {
                    'status': 'warning',
                    'message_id': result.message_id,
                    'processing_time_ms': processing_time,
                    'message': 'Delta inválido - mensaje rechazado',
                    'reason': result.error,
                    'validations': result.validations,
                    'version': 'v3.4.0'
                }
                
                logger.warning(f"Delta inválido en {processing_time:.2f}ms: {result.error}")
                return jsonify(response)
                
            else:  # error
                response = {
                    'error': 'Processing error',
                    'status': 'error',
                    'message_id': result.message_id,
                    'processing_time_ms': processing_time,
                    'details': result.error,
                    'version': 'v3.4.0'
                }
                
                logger.error(f"Error procesando mensaje en {processing_time:.2f}ms: {result.error}")
                return jsonify(response), 500
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Timeout o error obteniendo resultado: {e}")
            
            return jsonify({
                'error': 'Processing timeout',
                'status': 'error',
                'processing_time_ms': processing_time,
                'details': str(e),
                'version': 'v3.4.0'
            }), 500
    
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error inesperado de {ip}: {e}")
        
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'processing_time_ms': processing_time,
            'details': str(e),
            'version': 'v3.4.0'
        }), 500


@app.route('/camera/stats', methods=['GET'])
def get_camera_stats():
    """
    Endpoint nuevo para obtener estadísticas del procesador de mensajes
    
    Returns:
        JSON con estadísticas detalladas del CameraMessageProcessor
    """
    try:
        stats = message_processor.get_stats()
        
        # Añadir información adicional
        stats['version'] = 'v3.4.0'
        stats['current_time'] = datetime.now().isoformat()
        stats['processor_config'] = {
            'max_workers': message_processor.max_workers,
            'cache_duration': message_processor.cache_duration
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'error': 'Error retrieving stats',
            'details': str(e),
            'version': 'v3.4.0'
        }), 500


@app.route('/camera/health', methods=['GET'])
def get_health():
    """
    Endpoint de health check para el camera server
    
    Returns:
        JSON con estado de salud del servicio
    """
    try:
        stats = message_processor.get_stats()
        
        # Determinar estado de salud
        health_status = 'healthy'
        issues = []
        
        # Verificar si hay muchos errores
        if stats['messages_received'] > 0:
            error_rate = stats['errors'] / stats['messages_received']
            if error_rate > 0.1:  # Más del 10% de errores
                health_status = 'degraded'
                issues.append(f"High error rate: {error_rate:.1%}")
        
        # Verificar tiempo de procesamiento promedio
        if stats['avg_processing_time'] > 1000:  # Más de 1 segundo
            health_status = 'degraded'
            issues.append(f"High processing time: {stats['avg_processing_time']:.0f}ms")
        
        # Verificar mensajes concurrentes
        if stats['concurrent_messages'] > message_processor.max_workers * 0.8:
            health_status = 'warning'
            issues.append(f"High concurrency: {stats['concurrent_messages']}/{message_processor.max_workers}")
        
        return jsonify({
            'status': health_status,
            'version': 'v3.4.0',
            'uptime_seconds': time.time() - app.start_time if hasattr(app, 'start_time') else 0,
            'stats_summary': {
                'messages_processed': stats['messages_processed'],
                'error_rate': stats['errors'] / max(stats['messages_received'], 1),
                'avg_processing_time_ms': stats['avg_processing_time'],
                'concurrent_messages': stats['concurrent_messages']
            },
            'issues': issues if issues else None
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'version': 'v3.4.0',
            'error': str(e)
        }), 500


@app.route('/camera/version', methods=['GET'])
def get_version():
    """
    Endpoint para obtener información de versión
    
    Returns:
        JSON con información de versión y características
    """
    return jsonify({
        'version': 'v3.4.0',
        'name': 'Camera Server with Concurrent Message Processing',
        'features': [
            'Concurrent message processing',
            'Intelligent camera reset detection',
            'Enhanced delta validation',
            'Atomic occupancy updates',
            'Separated panel updates (background worker)',
            'Real-time statistics',
            'Thread-safe duplicate detection'
        ],
        'performance': {
            'max_concurrent_messages': message_processor.max_workers,
            'target_response_time_ms': '<200',
            'cache_duration_seconds': message_processor.cache_duration
        },
        'compatibility': 'Backward compatible with existing camera integrations'
    })


# Inicialización de la aplicación
if __name__ == '__main__':
    # Marcar tiempo de inicio
    app.start_time = time.time()
    
    # Log de inicio
    logger.info("=== Camera Server v3.4.0 Starting ===")
    logger.info("Features: Concurrent processing, Separated panel updates")
    logger.info(f"Configuration: {message_processor.max_workers} workers, {message_processor.cache_duration}s cache")
    
    try:
        # Iniciar servidor
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Disabled para producción
            threaded=True  # Threading habilitado para mejor concurrencia
        )
    except KeyboardInterrupt:
        logger.info("Servidor interrumpido por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
    finally:
        # Cerrar procesador limpiamente
        logger.info("Cerrando Camera Server...")
        message_processor.shutdown()
        logger.info("Camera Server cerrado")
