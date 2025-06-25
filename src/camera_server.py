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
    try:
        # Obtener IP del cliente
        ip = request.headers.get('X-Forwarded-For') or request.remote_addr
        
        # Intentar parsear JSON de forma robusta
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logger.error(f"Error parsing JSON from {ip}: {e}")
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        if not data:
            logger.error(f"Empty JSON data from {ip}")
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
        
        # Validar campos requeridos
        if line is None or veh_in is None or veh_out is None:
            logger.error(f"Missing required fields from {ip}: line={line}, veh_in={veh_in}, veh_out={veh_out}")
            return jsonify({'error': 'Missing required fields: line, Vehicle In, Vehicle Out'}), 400
        
        # Convertir a enteros de forma segura
        try:
            line = int(line)
            veh_in = int(veh_in)
            veh_out = int(veh_out)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid numeric values from {ip}: {e}")
            return jsonify({'error': 'Invalid numeric values'}), 400
        
        session = Session()
        
        # Buscar acceso por IP y línea
        access = session.query(Access).filter_by(ip=ip, line=line).first()
        
        # Si no se encuentra por IP, intentar buscar por nombre de dispositivo
        if not access and device:
            access = session.query(Access).filter_by(name=device).first()
            if access:
                logger.info(f"Found access by device name: {device}")
        
        if not access:
            session.close()
            logger.warning(f"Access not found for IP: {ip}, Line: {line}, Device: {device}")
            return jsonify({'error': 'Access not found'}), 404
        
        # Calcular deltas
        delta_in = veh_in - access.last_vehicle_in if access.last_vehicle_in is not None else 0
        delta_out = veh_out - access.last_vehicle_out if access.last_vehicle_out is not None else 0
        
        # Actualizar contadores de acceso
        access.last_vehicle_in = veh_in
        access.last_vehicle_out = veh_out
        
        # Actualizar parking
        parking = access.parking
        parking.current_occupancy += (delta_in - delta_out)
        parking.current_occupancy = max(0, min(parking.current_occupancy, parking.max_capacity))
        
        # Registrar histórico
        hist = OccupancyHistory(
            parking_id=parking.id,
            occupancy=parking.current_occupancy,
            source='camera'
        )
        session.add(hist)
        
        # Calcular estado
        occ = parking.current_occupancy
        if parking.fixed_message_flag:
            message = None
        else:
            if occ >= parking.threshold_full:
                parking.status = 'OCUPADO'
            elif occ >= parking.threshold_dense:
                parking.status = 'DENSO'
            else:
                parking.status = 'LIBRE'
            free = parking.max_capacity - occ
            message = f"{parking.name}: {free} libres ({parking.status})"
            
            # Enviar mensaje a paneles (con manejo de errores)
            try:
                broadcast(parking, message)
            except Exception as e:
                logger.error(f"Error broadcasting to panels: {e}")
        
        session.commit()
        session.close()
        
        logger.info(f"Successfully processed camera data for parking {parking.name} - Occupancy: {occ}")
        return jsonify({'status': 'ok', 'parking': parking.name, 'occupancy': occ})
        
    except Exception as e:
        logger.error(f"Unexpected error processing camera data: {e}")
        # Asegurar que la sesión se cierre en caso de error
        try:
            session.close()
        except:
            pass
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/camera', methods=['GET'])
def camera_status():
    """Endpoint para verificar el estado del servidor de cámaras"""
    return jsonify({'status': 'ok', 'service': 'camera_server'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.CAMERA_PORT)