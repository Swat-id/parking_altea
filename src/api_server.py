from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base, Parking, ScheduledMessage, OccupancyHistory, Panel, User, UserParking, UserPanel, UserAccess, Access
from auth import (
    create_user, authenticate_user, delete_user, change_password, 
    get_user_permissions, assign_user_to_resources, require_auth
)
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# ============================================================================
# ENDPOINTS DE AUTENTICACIÓN Y USUARIOS
# ============================================================================

@app.route('/auth/register', methods=['POST'])
def register_user():
    """Crear un nuevo usuario"""
    try:
        req = request.get_json(force=True)
        name = req.get('name')
        email = req.get('email')
        password = req.get('password')
        
        if not all([name, email, password]):
            return jsonify({'error': 'Faltan campos requeridos: name, email, password'}), 400
        
        session = Session()
        result = create_user(session, name, email, password)
        session.close()
        
        if result['success']:
            logger.info(f"Usuario creado: {email}")
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/login', methods=['POST'])
def login_user():
    """Autenticar usuario y obtener token"""
    try:
        req = request.get_json(force=True)
        email = req.get('email')
        password = req.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Faltan campos requeridos: email, password'}), 400
        
        session = Session()
        result = authenticate_user(session, email, password)
        session.close()
        
        if result['success']:
            logger.info(f"Usuario autenticado: {email}")
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        logger.error(f"Error en autenticación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/user', methods=['DELETE'])
@require_auth
def delete_user_endpoint():
    """Eliminar usuario (requiere autenticación)"""
    try:
        user_id = request.user_data['user_id']
        
        session = Session()
        result = delete_user(session, user_id)
        session.close()
        
        if result['success']:
            logger.info(f"Usuario eliminado: {user_id}")
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/password', methods=['PUT'])
@require_auth
def change_password_endpoint():
    """Cambiar contraseña (requiere autenticación)"""
    try:
        req = request.get_json(force=True)
        current_password = req.get('current_password')
        new_password = req.get('new_password')
        
        if not all([current_password, new_password]):
            return jsonify({'error': 'Faltan campos requeridos: current_password, new_password'}), 400
        
        user_id = request.user_data['user_id']
        
        session = Session()
        result = change_password(session, user_id, current_password, new_password)
        session.close()
        
        if result['success']:
            logger.info(f"Contraseña cambiada para usuario: {user_id}")
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/permissions', methods=['GET'])
@require_auth
def get_user_permissions_endpoint():
    """Obtener permisos del usuario autenticado"""
    try:
        user_id = request.user_data['user_id']
        
        session = Session()
        result = get_user_permissions(session, user_id)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error obteniendo permisos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/assign', methods=['POST'])
@require_auth
def assign_resources_endpoint():
    """Asignar recursos a un usuario (requiere autenticación)"""
    try:
        req = request.get_json(force=True)
        target_user_id = req.get('user_id')
        parking_ids = req.get('parking_ids', [])
        panel_ids = req.get('panel_ids', [])
        access_ids = req.get('access_ids', [])
        
        if not target_user_id:
            return jsonify({'error': 'Falta user_id'}), 400
        
        session = Session()
        result = assign_user_to_resources(
            session, target_user_id, parking_ids, panel_ids, access_ids
        )
        session.close()
        
        if result['success']:
            logger.info(f"Recursos asignados a usuario: {target_user_id}")
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error asignando recursos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# ENDPOINTS PROTEGIDOS DE PARKINGS (requieren autenticación)
# ============================================================================

@app.route('/user/parkings', methods=['GET'])
@require_auth
def get_user_parkings():
    """Obtener parkings a los que tiene acceso el usuario autenticado"""
    try:
        user_id = request.user_data['user_id']
        
        session = Session()
        # Obtener parkings del usuario
        user_parkings = session.query(UserParking).filter(UserParking.user_id == user_id).all()
        parking_ids = [up.parking_id for up in user_parkings]
        
        # Obtener datos de los parkings
        parks = session.query(Parking).filter(Parking.id.in_(parking_ids)).all()
        data = [
            {
                'id': p.id,
                'name': p.name,
                'location': p.location,
                'total_plazas': p.max_capacity,
                'plazas_ocupadas': p.current_occupancy,
                'plazas_libres': p.max_capacity - p.current_occupancy,
                'estado': p.status,
                'threshold_dense': p.threshold_dense,
                'threshold_full': p.threshold_full
            }
            for p in parks
        ]
        session.close()
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo parkings del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/user/parking/<int:pid>', methods=['GET'])
@require_auth
def get_user_parking(pid):
    """Obtener datos de un parking específico (si el usuario tiene acceso)"""
    try:
        user_id = request.user_data['user_id']
        
        session = Session()
        # Verificar que el usuario tiene acceso al parking
        user_parking = session.query(UserParking).filter(
            UserParking.user_id == user_id,
            UserParking.parking_id == pid
        ).first()
        
        if not user_parking:
            session.close()
            return jsonify({'error': 'Acceso denegado al parking'}), 403
        
        # Obtener datos del parking
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error': 'Parking no encontrado'}), 404
        
        data = {
            'id': p.id,
            'name': p.name,
            'location': p.location,
            'total_plazas': p.max_capacity,
            'plazas_ocupadas': p.current_occupancy,
            'plazas_libres': p.max_capacity - p.current_occupancy,
            'estado': p.status,
            'threshold_dense': p.threshold_dense,
            'threshold_full': p.threshold_full
        }
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo parking del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# ENDPOINTS PÚBLICOS (mantienen compatibilidad)
# ============================================================================

@app.route('/parkings', methods=['GET'])
def list_parkings():
    """Obtener datos de todos los aparcamientos con información completa"""
    session = Session()
    parks = session.query(Parking).all()
    data = [
        {
            'id': p.id,
            'name': p.name,
            'location': p.location,
            'total_plazas': p.max_capacity,
            'plazas_ocupadas': p.current_occupancy,
            'plazas_libres': p.max_capacity - p.current_occupancy,
            'estado': p.status,
            'threshold_dense': p.threshold_dense,
            'threshold_full': p.threshold_full
        }
        for p in parks
    ]
    session.close()
    return jsonify(data)

@app.route('/parking/<int:pid>', methods=['GET'])
def get_parking(pid):
    """Obtener datos de un parking específico"""
    session = Session()
    p = session.query(Parking).get(pid)
    if not p:
        session.close()
        return jsonify({'error':'Parking not found'}), 404
    
    data = {
        'id': p.id,
        'name': p.name,
        'location': p.location,
        'total_plazas': p.max_capacity,
        'plazas_ocupadas': p.current_occupancy,
        'plazas_libres': p.max_capacity - p.current_occupancy,
        'estado': p.status,
        'threshold_dense': p.threshold_dense,
        'threshold_full': p.threshold_full
    }
    session.close()
    return jsonify(data)

@app.route('/parking/<int:pid>/occupancy', methods=['POST'])
def set_occupancy(pid):
    """Actualizar ocupación manual de un parking"""
    try:
        req = request.get_json(force=True)
        new_occ = req.get('occupancy')
        
        if new_occ is None:
            return jsonify({'error': 'Missing occupancy field'}), 400
        
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Parking not found'}), 404
        
        # Validar y ajustar ocupación
        new_occ = int(new_occ)
        # PERMITIR OCUPACIÓN POR ENCIMA DEL MÁXIMO Y VALORES NEGATIVOS
        # No limitar la ocupación al máximo de capacidad
        # Esto permite reflejar la realidad cuando hay exceso de vehículos
        previous_occupancy = p.current_occupancy
        parking_name = p.name  # Guardar el nombre antes de cerrar la sesión
        p.current_occupancy = new_occ
        
        # Calcular descuadre para estadísticas
        free_spaces = p.max_capacity - p.current_occupancy
        occupancy_discrepancy = None
        
        if p.current_occupancy > p.max_capacity:
            # Exceso de vehículos
            occupancy_discrepancy = f"EXCESS:{p.current_occupancy - p.max_capacity}"
            logger.warning(f"MANUAL OCCUPANCY EXCESS - Parking: {parking_name}, Capacity: {p.max_capacity}, Current: {p.current_occupancy}, Excess: {p.current_occupancy - p.max_capacity}")
        elif free_spaces < 0:
            # Plazas libres negativas
            occupancy_discrepancy = f"NEGATIVE_FREE:{abs(free_spaces)}"
            logger.warning(f"MANUAL NEGATIVE FREE SPACES - Parking: {parking_name}, Free spaces: {free_spaces}")
        
        # Calcular estado basado en plazas libres (permitir estados especiales)
        free = p.max_capacity - p.current_occupancy
        
        if free < 0:
            # Estado especial para descuadres negativos
            p.status = 'DESCUADRE_NEGATIVO'
        elif p.current_occupancy > p.max_capacity:
            # Estado para exceso de ocupación
            p.status = 'COMPLETO_EXCESO'
        elif free <= p.threshold_full:
            p.status = 'COMPLETO'
        elif free <= p.threshold_dense:
            p.status = 'DENSO'
        else:
            p.status = 'LIBRE'
        
        # Registrar histórico
        hist = OccupancyHistory(parking_id=pid, occupancy=p.current_occupancy, source='manual')
        session.add(hist)
        final_status = p.status  # Guardar el estado antes de cerrar la sesión
        session.commit()
        session.close()
        
        logger.info(f"Manual occupancy update - Parking: {parking_name}, Previous: {previous_occupancy}, New: {new_occ}, Status: {final_status}")
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'previous_occupancy': previous_occupancy,
            'new_occupancy': new_occ,
            'status': final_status
        })
        
    except Exception as e:
        logger.error(f"Error updating occupancy for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/config', methods=['POST'])
def update_parking_config(pid):
    """Actualizar configuración de un parking (capacidad y umbrales)"""
    try:
        req = request.get_json(force=True)
        max_capacity = req.get('max_capacity')
        threshold_dense = req.get('threshold_dense')
        threshold_full = req.get('threshold_full')
        
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Parking not found'}), 404
        
        # Guardar el nombre antes de cerrar la sesión
        parking_name = p.name
        
        # Actualizar campos si se proporcionan
        if max_capacity is not None:
            p.max_capacity = int(max_capacity)
        if threshold_dense is not None:
            p.threshold_dense = int(threshold_dense)
        if threshold_full is not None:
            p.threshold_full = int(threshold_full)
        
        # Recalcular estado con nuevos umbrales
        free = p.max_capacity - p.current_occupancy
        if free <= p.threshold_full:
            p.status = 'COMPLETO'
        elif free <= p.threshold_dense:
            p.status = 'DENSO'
        else:
            p.status = 'LIBRE'
        
        # Guardar valores antes de cerrar la sesión
        final_max_capacity = p.max_capacity
        final_threshold_dense = p.threshold_dense
        final_threshold_full = p.threshold_full
        final_status = p.status
        
        session.commit()
        session.close()
        
        logger.info(f"Parking config updated - Parking: {parking_name}, Max: {final_max_capacity}, Dense: {final_threshold_dense}, Full: {final_threshold_full}")
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'max_capacity': final_max_capacity,
            'threshold_dense': final_threshold_dense,
            'threshold_full': final_threshold_full,
            'current_status': final_status
        })
        
    except Exception as e:
        logger.error(f"Error updating config for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/message', methods=['POST'])
def set_parking_message(pid):
    """Establecer mensaje para todos los paneles de un parking"""
    try:
        req = request.get_json(force=True)
        message = req.get('message')
        color = req.get('color', 'VERDE')  # VERDE, ROJO, AMARILLO
        scroll = req.get('scroll', False)  # True para scroll, False para centrado
        
        if not message:
            return jsonify({'error': 'Missing message field'}), 400
        
        if color not in ['VERDE', 'ROJO', 'AMARILLO']:
            return jsonify({'error': 'Invalid color. Must be VERDE, ROJO, or AMARILLO'}), 400
        
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Parking not found'}), 404
        
        # Guardar el nombre antes de cerrar la sesión
        parking_name = p.name
        
        # Obtener todos los paneles del parking
        panels = session.query(Panel).filter_by(parking_id=pid).all()
        
        if not panels:
            session.close()
            return jsonify({'error': 'No panels found for this parking'}), 404
        
        # Enviar mensaje a todos los paneles del parking
        from panel_client import send_to_panel
        success_count = 0
        failed_panels = []
        
        for panel in panels:
            try:
                # Formato del mensaje con color y scroll
                formatted_message = f"{message}|{color}|{'SCROLL' if scroll else 'CENTER'}"
                if send_to_panel(panel.ip, formatted_message):
                    success_count += 1
                else:
                    failed_panels.append(panel.ip)
            except Exception as e:
                logger.error(f"Error sending message to panel {panel.ip}: {e}")
                failed_panels.append(panel.ip)
        
        session.close()
        
        logger.info(f"Parking message sent - Parking: {parking_name}, Message: {message}, Success: {success_count}/{len(panels)}")
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'message': message,
            'color': color,
            'scroll': scroll,
            'panels_total': len(panels),
            'panels_success': success_count,
            'panels_failed': failed_panels
        })
        
    except Exception as e:
        logger.error(f"Error setting parking message for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/panel/<ip>/message', methods=['POST'])
def set_panel_message(ip):
    """Establecer mensaje para un panel específico por IP"""
    try:
        req = request.get_json(force=True)
        message = req.get('message')
        color = req.get('color', 'VERDE')  # VERDE, ROJO, AMARILLO
        scroll = req.get('scroll', False)  # True para scroll, False para centrado
        
        if not message:
            return jsonify({'error': 'Missing message field'}), 400
        
        if color not in ['VERDE', 'ROJO', 'AMARILLO']:
            return jsonify({'error': 'Invalid color. Must be VERDE, ROJO, or AMARILLO'}), 400
        
        session = Session()
        panel = session.query(Panel).filter_by(ip=ip).first()
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Guardar nombres antes de cerrar la sesión
        panel_name = panel.name
        parking_name = panel.parking.name
        
        # Enviar mensaje al panel específico
        from panel_client import send_to_panel
        formatted_message = f"{message}|{color}|{'SCROLL' if scroll else 'CENTER'}"
        
        if send_to_panel(panel.ip, formatted_message):
            session.close()
            logger.info(f"Panel message sent - IP: {ip}, Message: {message}, Color: {color}, Scroll: {scroll}")
            return jsonify({
                'status': 'ok',
                'panel_ip': ip,
                'panel_name': panel_name,
                'parking': parking_name,
                'message': message,
                'color': color,
                'scroll': scroll
            })
        else:
            session.close()
            return jsonify({'error': 'Failed to send message to panel'}), 500
        
    except Exception as e:
        logger.error(f"Error setting panel message for IP {ip}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/message', methods=['GET'])
def get_scheduled_messages(pid):
    """Obtener mensajes programados de un parking"""
    session = Session()
    p = session.query(Parking).get(pid)
    if not p:
        session.close()
        return jsonify({'error':'Parking not found'}), 404
    
    messages = session.query(ScheduledMessage).filter_by(parking_id=pid).all()
    data = [
        {
            'id': msg.id,
            'start_time': msg.start_time.isoformat(),
            'end_time': msg.end_time.isoformat(),
            'message': msg.message
        }
        for msg in messages
    ]
    session.close()
    return jsonify(data)

@app.route('/parking/<int:pid>/message', methods=['DELETE'])
def delete_scheduled_message(pid):
    """Eliminar mensaje programado de un parking"""
    try:
        req = request.get_json(force=True)
        message_id = req.get('message_id')
        
        if not message_id:
            return jsonify({'error': 'Missing message_id field'}), 400
        
        session = Session()
        msg = session.query(ScheduledMessage).filter_by(id=message_id, parking_id=pid).first()
        
        if not msg:
            session.close()
            return jsonify({'error': 'Message not found'}), 404
        
        session.delete(msg)
        session.commit()
        session.close()
        
        logger.info(f"Scheduled message deleted - Parking: {pid}, Message ID: {message_id}")
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error deleting scheduled message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT)