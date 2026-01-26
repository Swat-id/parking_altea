"""
Spot Detection Server v4.4.0
============================
Servidor para recibir mensajes de cámaras de detección de plazas individuales.

Puerto: 6401 (configurable via SPOT_DETECTION_PORT)

Endpoints:
- POST /detection - Recibir mensajes de detección (trigger o interval)
- GET /detection/health - Health check

Formato de mensajes esperados:
- Trigger: Evento individual de una plaza
- Interval: Reporte periódico con todas las plazas

Autor: Parking Altea Team
Fecha: 2026-01-26
"""

from flask import Flask, request, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config
import json
import logging
import time
from models import (
    Base, Parking, Access, CameraParking, 
    MonitoredSpot, SpotStatusHistory, SpotOccupancyCorrection, SpotDetectionLog
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('spot_detection_server')

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)

# Límites de ocupación desde config
MAX_OCCUPANCY_PERCENT = config.OCCUPANCY_MAX_LIMIT_PERCENT  # 110%
MIN_OCCUPANCY = config.OCCUPANCY_MIN_LIMIT  # 0


def log_detection_message(session, camera_id, parking_id, device_name, camera_ip,
                          report_type, total_occupied, total_available, spots_processed,
                          status, error_message=None, processing_time_ms=None, raw_message=None):
    """Registrar mensaje de detección en la base de datos"""
    try:
        # Eliminar snapshot del raw_message para ahorrar espacio
        if raw_message and 'snapshot' in raw_message:
            raw_message = {k: v for k, v in raw_message.items() if k != 'snapshot'}
        
        log_entry = SpotDetectionLog(
            camera_id=camera_id,
            parking_id=parking_id,
            device_name=device_name,
            camera_ip=camera_ip,
            report_type=report_type,
            total_occupied=total_occupied,
            total_available=total_available,
            spots_processed=spots_processed,
            status=status,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
            raw_message=raw_message
        )
        session.add(log_entry)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error registrando log de detección: {e}")
        session.rollback()
        return False


def get_or_create_spot(session, parking_id, camera_id, area_name, spot_number):
    """
    Obtener o crear una plaza monitorizada.
    Las plazas se crean automáticamente al llegar el primer mensaje.
    """
    spot = session.query(MonitoredSpot).filter(
        MonitoredSpot.camera_id == camera_id,
        MonitoredSpot.area_name == area_name,
        MonitoredSpot.spot_number == spot_number
    ).first()
    
    if not spot:
        spot = MonitoredSpot(
            parking_id=parking_id,
            camera_id=camera_id,
            area_name=area_name,
            spot_number=spot_number,
            current_status=0,  # Inicialmente libre
            created_at=datetime.now()
        )
        session.add(spot)
        logger.info(f"Nueva plaza creada: {area_name}-{spot_number} para cámara {camera_id}")
    
    return spot


def update_spot_status(session, spot, new_status, report_type, device_name):
    """
    Actualizar estado de una plaza y registrar en histórico si cambió.
    """
    previous_status = spot.current_status
    status_changed = previous_status != new_status
    
    spot.current_status = new_status
    spot.last_update = datetime.now()
    
    if status_changed:
        spot.last_status_change = datetime.now()
        
        # Registrar en histórico
        history = SpotStatusHistory(
            spot_id=spot.id,
            parking_id=spot.parking_id,
            camera_id=spot.camera_id,
            previous_status=previous_status,
            new_status=new_status,
            report_type=report_type,
            device_name=device_name
        )
        session.add(history)
        logger.info(f"Plaza {spot.area_name}-{spot.spot_number} cambió: {previous_status} -> {new_status}")
    
    return status_changed


def update_parking_totals(session, parking):
    """
    Recalcular totales del parking sumando todas las cámaras de detección.
    """
    # Contar total de plazas monitorizadas del parking
    total_monitored = session.query(func.count(MonitoredSpot.id)).filter(
        MonitoredSpot.parking_id == parking.id
    ).scalar() or 0
    
    # Contar plazas ocupadas
    total_occupied = session.query(func.count(MonitoredSpot.id)).filter(
        MonitoredSpot.parking_id == parking.id,
        MonitoredSpot.current_status == 1
    ).scalar() or 0
    
    parking.total_monitored_spots = total_monitored
    parking.total_spot_occupied = total_occupied
    parking.last_spot_sync = datetime.now()
    
    logger.info(f"Parking {parking.name}: {total_occupied}/{total_monitored} plazas ocupadas (monitorización)")
    
    return total_monitored, total_occupied


def update_camera_spot_count(session, camera):
    """
    Actualizar el contador de plazas monitorizadas de una cámara.
    """
    count = session.query(func.count(MonitoredSpot.id)).filter(
        MonitoredSpot.camera_id == camera.id
    ).scalar() or 0
    
    camera.monitored_spots_count = count
    logger.info(f"Cámara {camera.name}: {count} plazas monitorizadas")
    
    return count


def apply_occupancy_limits(parking, raw_occupancy, session):
    """
    Aplicar límites a la ocupación:
    - Mínimo: 0
    - Máximo: 110% de max_capacity
    
    Todos los eventos se registran, pero la ocupación mostrada respeta los límites.
    """
    max_allowed = int(parking.max_capacity * (MAX_OCCUPANCY_PERCENT / 100))
    
    previous_occupancy = parking.current_occupancy
    correction_reason = None
    
    if raw_occupancy < MIN_OCCUPANCY:
        new_occupancy = MIN_OCCUPANCY
        correction_reason = 'limit_min'
        logger.warning(f"Parking {parking.name}: Ocupación {raw_occupancy} limitada a {new_occupancy} (mínimo)")
    elif raw_occupancy > max_allowed:
        new_occupancy = max_allowed
        correction_reason = 'limit_max'
        logger.warning(f"Parking {parking.name}: Ocupación {raw_occupancy} limitada a {new_occupancy} (máximo 110%)")
    else:
        new_occupancy = raw_occupancy
    
    # Registrar corrección si se aplicó límite
    if correction_reason:
        correction = SpotOccupancyCorrection(
            parking_id=parking.id,
            previous_occupancy=previous_occupancy,
            new_occupancy=new_occupancy,
            correction_amount=new_occupancy - previous_occupancy,
            correction_reason=correction_reason,
            spot_occupied_count=parking.total_spot_occupied,
            total_monitored_spots=parking.total_monitored_spots,
            max_capacity=parking.max_capacity,
            raw_calculated_occupancy=raw_occupancy
        )
        session.add(correction)
    
    return new_occupancy


def process_trigger_message(session, camera, parking, data, device_name, client_ip, start_time):
    """
    Procesar mensaje tipo 'trigger' (evento individual de una plaza).
    """
    area_name = data.get('parking_area', '')
    spot_number = data.get('index_number', 0)
    occupancy = data.get('occupancy', 0)  # 0=libre, 1=ocupado
    
    if not area_name or spot_number is None:
        error_msg = f"Campos requeridos faltantes: parking_area={area_name}, index_number={spot_number}"
        logger.error(error_msg)
        log_detection_message(
            session, camera.id, parking.id, device_name, client_ip,
            'trigger', None, None, 0, 'error', error_msg,
            (time.time() - start_time) * 1000, data
        )
        return {'error': error_msg}, 400
    
    # Obtener o crear la plaza
    spot = get_or_create_spot(session, parking.id, camera.id, area_name, spot_number)
    session.flush()  # Para obtener el ID si es nueva
    
    # Actualizar estado
    status_changed = update_spot_status(session, spot, occupancy, 'trigger', device_name)
    
    # Actualizar contadores de cámara y parking
    update_camera_spot_count(session, camera)
    update_parking_totals(session, parking)
    
    # Registrar log
    processing_time = (time.time() - start_time) * 1000
    log_detection_message(
        session, camera.id, parking.id, device_name, client_ip,
        'trigger', occupancy, 1 - occupancy, 1, 'processed', None,
        processing_time, data
    )
    
    session.commit()
    
    return {
        'status': 'ok',
        'spot': f"{area_name}-{spot_number}",
        'new_status': 'occupied' if occupancy == 1 else 'available',
        'status_changed': status_changed,
        'processing_time_ms': processing_time
    }, 200


def process_interval_message(session, camera, parking, data, device_name, client_ip, start_time):
    """
    Procesar mensaje tipo 'interval' (reporte periódico con todas las plazas).
    """
    total_occupied_reported = data.get('total_occupied', 0)
    total_available_reported = data.get('total_available', 0)
    parking_detail = data.get('parking_detail', [])
    
    if not parking_detail:
        error_msg = "parking_detail vacío o no presente"
        logger.warning(error_msg)
        log_detection_message(
            session, camera.id, parking.id, device_name, client_ip,
            'interval', total_occupied_reported, total_available_reported, 0, 
            'error', error_msg, (time.time() - start_time) * 1000, data
        )
        return {'error': error_msg}, 400
    
    spots_processed = 0
    spots_changed = 0
    
    # Procesar cada área
    for area in parking_detail:
        area_name = area.get('area_name', '')
        numbering_scheme = area.get('numbering_scheme', [])
        occupancy_list = area.get('occupancy', [])
        
        if len(numbering_scheme) != len(occupancy_list):
            logger.warning(f"Área {area_name}: numbering_scheme y occupancy tienen diferente longitud")
            continue
        
        # Procesar cada plaza del área
        for i, spot_number in enumerate(numbering_scheme):
            occupancy = occupancy_list[i]
            
            # Obtener o crear la plaza
            spot = get_or_create_spot(session, parking.id, camera.id, area_name, spot_number)
            session.flush()
            
            # Actualizar estado
            if update_spot_status(session, spot, occupancy, 'interval', device_name):
                spots_changed += 1
            
            spots_processed += 1
    
    # Actualizar contadores de cámara y parking
    update_camera_spot_count(session, camera)
    total_monitored, total_occupied = update_parking_totals(session, parking)
    
    # Registrar log
    processing_time = (time.time() - start_time) * 1000
    log_detection_message(
        session, camera.id, parking.id, device_name, client_ip,
        'interval', total_occupied_reported, total_available_reported, spots_processed,
        'processed', None, processing_time, data
    )
    
    session.commit()
    
    return {
        'status': 'ok',
        'spots_processed': spots_processed,
        'spots_changed': spots_changed,
        'total_monitored': total_monitored,
        'total_occupied': total_occupied,
        'processing_time_ms': processing_time
    }, 200


@app.route('/detection', methods=['POST'])
def handle_detection():
    """
    Endpoint principal para recibir mensajes de detección de plazas.
    
    Acepta dos tipos de mensajes:
    - trigger: Evento individual de una plaza
    - interval: Reporte periódico con todas las plazas
    """
    start_time = time.time()
    client_ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    
    logger.info(f"=== SPOT DETECTION MESSAGE RECEIVED ===")
    logger.info(f"Source IP: {client_ip}")
    
    session = Session()
    
    try:
        # Parsear JSON
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logger.error(f"JSON mal formado: {e}")
            log_detection_message(
                session, None, None, '', client_ip,
                None, None, None, 0, 'error',
                f"Invalid JSON: {e}", (time.time() - start_time) * 1000, None
            )
            session.close()
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        if not data:
            logger.error("Mensaje vacío")
            session.close()
            return jsonify({'error': 'Empty JSON data'}), 400
        
        # Extraer campos del mensaje
        device_name = data.get('device', '')
        report_type = data.get('report_type', '')
        event = data.get('event', '')
        
        logger.info(f"Device: {device_name}, Report type: {report_type}, Event: {event}")
        logger.debug(f"JSON completo: {json.dumps(data, indent=2)}")
        
        # Validar campos básicos
        if not device_name:
            error_msg = "Campo 'device' requerido"
            logger.error(error_msg)
            log_detection_message(
                session, None, None, device_name, client_ip,
                report_type, None, None, 0, 'error', error_msg,
                (time.time() - start_time) * 1000, data
            )
            session.close()
            return jsonify({'error': error_msg}), 400
        
        if report_type not in ['trigger', 'interval']:
            error_msg = f"report_type inválido: {report_type}. Debe ser 'trigger' o 'interval'"
            logger.error(error_msg)
            log_detection_message(
                session, None, None, device_name, client_ip,
                report_type, None, None, 0, 'error', error_msg,
                (time.time() - start_time) * 1000, data
            )
            session.close()
            return jsonify({'error': error_msg}), 400
        
        # Buscar cámara por device (name) Y tipo spot_detection
        camera = session.query(Access).filter(
            func.lower(Access.name) == func.lower(device_name),
            Access.camera_type == 'spot_detection'
        ).first()
        
        if not camera:
            error_msg = f"Cámara de detección no encontrada: {device_name}"
            logger.warning(error_msg)
            
            # Listar cámaras disponibles para debug
            available_cameras = session.query(Access.name).filter(
                Access.camera_type == 'spot_detection'
            ).all()
            camera_names = [c[0] for c in available_cameras]
            logger.warning(f"Cámaras de detección disponibles: {camera_names}")
            
            log_detection_message(
                session, None, None, device_name, client_ip,
                report_type, None, None, 0, 'camera_not_found', error_msg,
                (time.time() - start_time) * 1000, data
            )
            session.close()
            return jsonify({'error': error_msg}), 404
        
        # Actualizar estado de la cámara
        camera.status = 'ONLINE'
        camera.last_message_received = datetime.now()
        
        # Obtener parking asociado
        camera_parking = session.query(CameraParking).filter_by(
            camera_id=camera.id
        ).first()
        
        if not camera_parking:
            error_msg = f"Cámara {device_name} no está asignada a ningún parking"
            logger.error(error_msg)
            log_detection_message(
                session, camera.id, None, device_name, client_ip,
                report_type, None, None, 0, 'error', error_msg,
                (time.time() - start_time) * 1000, data
            )
            session.close()
            return jsonify({'error': error_msg}), 400
        
        parking = camera_parking.parking
        
        # Verificar que el parking tiene habilitada la monitorización por plaza
        if not parking.spot_monitoring_enabled:
            error_msg = f"Parking {parking.name} no tiene habilitada la monitorización por plaza"
            logger.warning(error_msg)
            log_detection_message(
                session, camera.id, parking.id, device_name, client_ip,
                report_type, None, None, 0, 'parking_disabled', error_msg,
                (time.time() - start_time) * 1000, data
            )
            session.close()
            return jsonify({'error': error_msg}), 400
        
        logger.info(f"Cámara: {camera.name} (ID: {camera.id}) -> Parking: {parking.name} (ID: {parking.id})")
        
        # Procesar según tipo de reporte
        if report_type == 'trigger':
            result, status_code = process_trigger_message(
                session, camera, parking, data, device_name, client_ip, start_time
            )
        else:  # interval
            result, status_code = process_interval_message(
                session, camera, parking, data, device_name, client_ip, start_time
            )
        
        session.close()
        logger.info(f"=== END SPOT DETECTION PROCESSING ===")
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        try:
            session.rollback()
            session.close()
        except:
            pass
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/detection', methods=['GET'])
@app.route('/detection/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado del servidor"""
    session = Session()
    try:
        # Verificar conexión a BD
        session.execute("SELECT 1")
        db_status = 'ok'
    except:
        db_status = 'error'
    finally:
        session.close()
    
    return jsonify({
        'status': 'ok',
        'service': 'spot_detection_server',
        'version': '4.4.0',
        'database': db_status,
        'port': config.SPOT_DETECTION_PORT,
        'limits': {
            'max_occupancy_percent': MAX_OCCUPANCY_PERCENT,
            'min_occupancy': MIN_OCCUPANCY
        }
    })


@app.route('/detection/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas del servidor de detección"""
    session = Session()
    try:
        # Contar cámaras de detección
        total_cameras = session.query(func.count(Access.id)).filter(
            Access.camera_type == 'spot_detection'
        ).scalar() or 0
        
        # Contar cámaras online
        cameras_online = session.query(func.count(Access.id)).filter(
            Access.camera_type == 'spot_detection',
            Access.status == 'ONLINE'
        ).scalar() or 0
        
        # Contar parkings con monitorización habilitada
        parkings_enabled = session.query(func.count(Parking.id)).filter(
            Parking.spot_monitoring_enabled == True
        ).scalar() or 0
        
        # Contar total de plazas monitorizadas
        total_spots = session.query(func.count(MonitoredSpot.id)).scalar() or 0
        
        # Contar plazas ocupadas
        occupied_spots = session.query(func.count(MonitoredSpot.id)).filter(
            MonitoredSpot.current_status == 1
        ).scalar() or 0
        
        session.close()
        
        return jsonify({
            'total_detection_cameras': total_cameras,
            'cameras_online': cameras_online,
            'parkings_with_spot_monitoring': parkings_enabled,
            'total_monitored_spots': total_spots,
            'occupied_spots': occupied_spots,
            'available_spots': total_spots - occupied_spots
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        session.close()
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info(f"🚀 SPOT DETECTION SERVER v4.4.0 starting on port {config.SPOT_DETECTION_PORT}")
    logger.info(f"Limits: max={MAX_OCCUPANCY_PERCENT}%, min={MIN_OCCUPANCY}")
    app.run(host='0.0.0.0', port=config.SPOT_DETECTION_PORT, debug=False)
