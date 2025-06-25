from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config
import json
import logging
from models import Base, Parking, Access, OccupancyHistory
from panel_client import broadcast

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

@app.route('/camera', methods=['POST'])
def handle_camera():
    # Obtener IP del cliente al inicio para logging
    ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    
    # Log de recepción de petición
    logger.info(f"=== CAMERA MESSAGE RECEIVED ===")
    logger.info(f"Source IP: {ip}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Capturar el body raw para logging
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"Raw body received: {raw_data}")
    except Exception as e:
        logger.error(f"Error reading raw body from {ip}: {e}")
        raw_data = "Unable to read raw body"
    
    try:
        # Intentar parsear JSON de forma robusta
        try:
            data = request.get_json(force=True)
            logger.info(f"JSON parsed successfully from {ip}")
        except Exception as e:
            logger.error(f"JSON mal formado descartado from {ip}: {e}")
            logger.error(f"Raw data that caused error: {raw_data}")
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        if not data:
            logger.error(f"Mensaje vacío descartado from {ip}")
            logger.error(f"Raw data was empty or null")
            return jsonify({'error': 'Empty JSON data'}), 400
        
        # Extraer campos del nuevo formato
        device = data.get('device', '')
        line = data.get('line', 0)
        veh_in = data.get('Vehicle In', 0)
        veh_out = data.get('Vehicle Out', 0)
        event = data.get('event', '')
        time_str = data.get('time', '')
        
        # Log de la petición recibida
        logger.info(f"Camera data from {ip} - Device: {device}, Line: {line}, In: {veh_in}, Out: {veh_out}")
        logger.info(f"JSON received: {json.dumps(data, indent=2)}")
        
        # Validar campos requeridos
        if line is None or veh_in is None or veh_out is None:
            logger.error(f"Campos requeridos faltantes from {ip}: line={line}, veh_in={veh_in}, veh_out={veh_out}")
            logger.error(f"JSON completo que causó el error: {json.dumps(data, indent=2)}")
            return jsonify({'error': 'Missing required fields: line, Vehicle In, Vehicle Out'}), 400
        
        # Convertir a enteros de forma segura
        try:
            line = int(line)
            veh_in = int(veh_in)
            veh_out = int(veh_out)
        except (ValueError, TypeError) as e:
            logger.error(f"Valores numéricos inválidos from {ip}: {e}")
            logger.error(f"Valores problemáticos: line='{line}', veh_in='{veh_in}', veh_out='{veh_out}'")
            return jsonify({'error': 'Invalid numeric values'}), 400
        
        session = Session()
        
        # Buscar acceso por IP y línea (método principal)
        access = session.query(Access).filter_by(ip=ip, line=line).first()
        
        # Si no se encuentra por IP+línea, intentar buscar por nombre de dispositivo Y línea
        if not access and device:
            access = session.query(Access).filter_by(name=device, line=line).first()
            if access:
                logger.info(f"Found access by device name and line: {device}, line: {line}")
            else:
                # Si no encuentra por nombre+línea, buscar solo por nombre para logging
                device_access = session.query(Access).filter_by(name=device).first()
                if device_access:
                    logger.warning(f"Device found but line mismatch - Device: {device}, Expected line: {device_access.line}, Received line: {line}")
                    logger.warning(f"Message logged but not processed - line validation failed")
                    session.close()
                    return jsonify({'error': 'Line mismatch for device'}), 400
                else:
                    logger.warning(f"Device not found in database: {device}")
        
        if not access:
            session.close()
            logger.warning(f"Access not found for IP: {ip}, Line: {line}, Device: {device}")
            logger.warning(f"JSON completo que no pudo ser procesado: {json.dumps(data, indent=2)}")
            return jsonify({'error': 'Access not found'}), 404
        
        # Log de información del acceso encontrado
        logger.info(f"Access found - ID: {access.id}, Parking ID: {access.parking_id}, Name: {access.name}")
        logger.info(f"Previous counters - Last In: {access.last_vehicle_in}, Last Out: {access.last_vehicle_out}")
        
        # Calcular deltas
        delta_in = veh_in - access.last_vehicle_in if access.last_vehicle_in is not None else 0
        delta_out = veh_out - access.last_vehicle_out if access.last_vehicle_out is not None else 0
        
        logger.info(f"Deltas calculated - Delta In: {delta_in}, Delta Out: {delta_out}")
        
        # Actualizar contadores de acceso
        access.last_vehicle_in = veh_in
        access.last_vehicle_out = veh_out
        
        # Actualizar parking
        parking = access.parking
        previous_occupancy = parking.current_occupancy
        parking.current_occupancy += (delta_in - delta_out)
        parking.current_occupancy = max(0, min(parking.current_occupancy, parking.max_capacity))
        
        logger.info(f"Parking occupancy updated - Previous: {previous_occupancy}, New: {parking.current_occupancy}, Max Capacity: {parking.max_capacity}")
        
        # Registrar histórico
        hist = OccupancyHistory(
            parking_id=parking.id,
            occupancy=parking.current_occupancy,
            source='camera'
        )
        session.add(hist)
        
        # Calcular estado
        occ = parking.current_occupancy
        parking_name = parking.name  # Obtener el nombre antes de cerrar la sesión
        previous_status = parking.status
        free = parking.max_capacity - occ
        
        if parking.fixed_message_flag:
            message = None
            logger.info(f"Fixed message flag is active - no status update")
        else:
            # Evaluar por plazas libres (no por ocupación)
            if free <= parking.threshold_full:
                parking.status = 'COMPLETO'
            elif free <= parking.threshold_dense:
                parking.status = 'DENSO'
            else:
                parking.status = 'LIBRE'
            
            message = f"{parking_name}: {free} libres ({parking.status})"
            
            logger.info(f"Status updated - Previous: {previous_status}, New: {parking.status}, Free spaces: {free}")
            logger.info(f"Thresholds evaluation - Free spaces: {free}, Dense threshold: {parking.threshold_dense}, Full threshold: {parking.threshold_full}")
            
            # Enviar mensaje a paneles (con manejo de errores)
            try:
                broadcast(parking, message)
                logger.info(f"Message broadcasted to panels: {message}")
            except Exception as e:
                logger.error(f"Error broadcasting to panels: {e}")
        
        session.commit()
        session.close()
        
        logger.info(f"Successfully processed camera data for parking {parking_name} - Occupancy: {occ}")
        logger.info(f"=== END CAMERA MESSAGE PROCESSING ===")
        return jsonify({'status': 'ok', 'parking': parking_name, 'occupancy': occ})
        
    except Exception as e:
        logger.error(f"Error inesperado procesando datos de cámara from {ip}: {e}")
        logger.error(f"Raw data that caused unexpected error: {raw_data}")
        # Asegurar que la sesión se cierre en caso de error
        try:
            session.close()
        except:
            pass
        logger.info(f"=== END CAMERA MESSAGE PROCESSING (WITH ERROR) ===")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/camera', methods=['GET'])
def camera_status():
    """Endpoint para verificar el estado del servidor de cámaras"""
    return jsonify({'status': 'ok', 'service': 'camera_server'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.CAMERA_PORT)