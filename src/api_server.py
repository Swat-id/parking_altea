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
    """Obtener un parking específico del usuario autenticado"""
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
            return jsonify({'error': 'Parking not found or access denied'}), 404
        
        # Obtener datos del parking
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        data = {
            'id': parking.id,
            'name': parking.name,
            'location': parking.location,
            'total_plazas': parking.max_capacity,
            'plazas_ocupadas': parking.current_occupancy,
            'plazas_libres': parking.max_capacity - parking.current_occupancy,
            'estado': parking.status,
            'threshold_dense': parking.threshold_dense,
            'threshold_full': parking.threshold_full
        }
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo parking del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# ENDPOINTS PÚBLICOS DE PARKINGS
# ============================================================================

@app.route('/parkings', methods=['GET'])
def list_parkings():
    """Listar todos los parkings"""
    try:
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
                'estado': p.status
            }
            for p in parks
        ]
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error listando parkings: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>', methods=['GET'])
def get_parking(pid):
    """Obtener un parking específico"""
    try:
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
        
    except Exception as e:
        logger.error(f"Error obteniendo parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/occupancy', methods=['POST'])
def set_occupancy(pid):
    """Establecer ocupación de un parking"""
    try:
        req = request.get_json(force=True)
        occupancy = req.get('occupancy')
        
        if occupancy is None:
            return jsonify({'error': 'Missing occupancy field'}), 400
        
        if not isinstance(occupancy, int) or occupancy < 0:
            return jsonify({'error': 'Occupancy must be a non-negative integer'}), 400
        
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Parking not found'}), 404
        
        # Guardar ocupación anterior para el historial
        previous_occupancy = p.current_occupancy
        change_amount = occupancy - previous_occupancy
        
        # Actualizar ocupación
        p.current_occupancy = occupancy
        
        # Recalcular estado
        free = p.max_capacity - p.current_occupancy
        if free <= p.threshold_full:
            p.status = 'COMPLETO'
        elif free <= p.threshold_dense:
            p.status = 'DENSO'
        else:
            p.status = 'LIBRE'
        
        # Guardar en historial
        history = OccupancyHistory(
            parking_id=pid,
            occupancy=occupancy,
            source='manual',
            previous_occupancy=previous_occupancy,
            change_amount=change_amount
        )
        session.add(history)
        
        # Guardar nombres antes de cerrar la sesión
        parking_name = p.name
        final_occupancy = p.current_occupancy
        final_status = p.status
        
        session.commit()
        session.close()
        
        logger.info(f"Parking occupancy updated - Parking: {parking_name}, Occupancy: {final_occupancy}, Status: {final_status}")
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'occupancy': final_occupancy,
            'free_spaces': p.max_capacity - final_occupancy,
            'status': final_status
        })
        
    except Exception as e:
        logger.error(f"Error updating occupancy for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/config', methods=['POST'])
def update_parking_config(pid):
    """Actualizar configuración de un parking"""
    try:
        req = request.get_json(force=True)
        max_capacity = req.get('total_plazas')
        threshold_dense = req.get('threshold_dense')
        threshold_full = req.get('threshold_full')
        
        if max_capacity is not None and (not isinstance(max_capacity, int) or max_capacity <= 0):
            return jsonify({'error': 'total_plazas must be a positive integer'}), 400
        
        if threshold_dense is not None and (not isinstance(threshold_dense, int) or threshold_dense < 0):
            return jsonify({'error': 'threshold_dense must be a non-negative integer'}), 400
        
        if threshold_full is not None and (not isinstance(threshold_full, int) or threshold_full < 0):
            return jsonify({'error': 'threshold_full must be a non-negative integer'}), 400
        
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Parking not found'}), 404
        
        # Guardar el nombre antes de cerrar la sesión
        parking_name = p.name
        
        # Actualizar campos si se proporcionan
        if max_capacity is not None:
            p.max_capacity = max_capacity
        if threshold_dense is not None:
            p.threshold_dense = threshold_dense
        if threshold_full is not None:
            p.threshold_full = threshold_full
        
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

# ============================================================================
# ENDPOINTS DE ESTADÍSTICAS Y LOGS
# ============================================================================

@app.route('/panels', methods=['GET'])
def get_all_panels():
    """Obtener todos los paneles con su estado actual"""
    try:
        session = Session()
        panels = session.query(Panel).all()
        data = []
        
        for panel in panels:
            panel_data = {
                'id': panel.id,
                'name': panel.name,
                'ip_address': panel.ip,
                'parking_id': panel.parking_id,
                'parking_name': panel.parking.name if panel.parking else None,
                'status': getattr(panel, 'status', 'OFFLINE'),
                'last_message': getattr(panel, 'last_message', None),
                'last_update': getattr(panel, 'last_update', None)
            }
            if panel_data['last_update']:
                panel_data['last_update'] = panel_data['last_update'].isoformat()
            data.append(panel_data)
        
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo paneles: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/panel/<int:panel_id>/message', methods=['POST'])
def send_message_to_panel(panel_id):
    """Enviar mensaje a un panel específico por ID"""
    try:
        req = request.get_json(force=True)
        message = req.get('message')
        duration = req.get('duration', 30)
        
        if not message:
            return jsonify({'error': 'Missing message field'}), 400
        
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Enviar mensaje al panel
        from panel_client import send_to_panel
        formatted_message = f"{message}|VERDE|CENTER"
        
        start_time = datetime.now()
        success = send_to_panel(panel.ip, formatted_message)
        response_time = (datetime.now() - start_time).total_seconds() * 1000  # en ms
        
        # Actualizar estado del panel
        panel.status = 'ONLINE' if success else 'OFFLINE'
        panel.last_message = message
        panel.last_update = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'status': 'ok' if success else 'failed',
            'panel_id': panel_id,
            'panel_name': panel.name,
            'message': message,
            'duration': duration,
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error enviando mensaje al panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/panel/<int:panel_id>/test', methods=['POST'])
def test_panel(panel_id):
    """Probar comunicación con un panel"""
    try:
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Enviar mensaje de prueba
        from panel_client import send_to_panel
        test_message = "PRUEBA|VERDE|CENTER"
        
        start_time = datetime.now()
        success = send_to_panel(panel.ip, test_message)
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Actualizar estado del panel
        panel.status = 'ONLINE' if success else 'OFFLINE'
        panel.last_update = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'status': 'ok' if success else 'failed',
            'panel_id': panel_id,
            'panel_name': panel.name,
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error probando panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/statistics', methods=['GET'])
def get_parking_statistics(pid):
    """Obtener estadísticas de un parking"""
    try:
        days = request.args.get('days', 7, type=int)
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Importar el gestor de estadísticas
        from statistics import StatisticsManager
        stats_manager = StatisticsManager(session)
        
        # Obtener estadísticas
        statistics = stats_manager.get_parking_statistics(pid, days)
        
        session.close()
        
        if statistics:
            return jsonify({
                'parking_id': pid,
                'parking_name': parking.name,
                'days': days,
                **statistics
            })
        else:
            return jsonify({'error': 'No statistics available'}), 404
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/statistics', methods=['GET'])
def get_all_statistics():
    """Obtener estadísticas de todos los parkings"""
    try:
        days = request.args.get('days', 7, type=int)
        
        session = Session()
        
        # Importar el gestor de estadísticas
        from statistics import StatisticsManager
        stats_manager = StatisticsManager(session)
        
        # Obtener estadísticas de todos los parkings
        statistics = stats_manager.get_all_parkings_statistics(days)
        
        session.close()
        
        if statistics:
            return jsonify({
                'days': days,
                'statistics': statistics
            })
        else:
            return jsonify({'error': 'No statistics available'}), 404
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/history', methods=['GET'])
def get_occupancy_history(pid):
    """Obtener historial de ocupación de un parking"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Obtener historial
        history = session.query(OccupancyHistory)\
            .filter(OccupancyHistory.parking_id == pid)\
            .order_by(OccupancyHistory.timestamp.desc())\
            .limit(limit)\
            .all()
        
        data = [
            {
                'id': h.id,
                'timestamp': h.timestamp.isoformat(),
                'occupancy': h.occupancy,
                'source': h.source,
                'previous_occupancy': getattr(h, 'previous_occupancy', None),
                'change_amount': getattr(h, 'change_amount', None)
            }
            for h in history
        ]
        
        session.close()
        return jsonify({
            'parking_id': pid,
            'parking_name': parking.name,
            'history': data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial del parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/logs/activity', methods=['GET'])
@require_auth
def get_activity_logs():
    """Obtener logs de actividad (requiere autenticación)"""
    try:
        user_id = request.args.get('user_id', type=int)
        parking_id = request.args.get('parking_id', type=int)
        action_type = request.args.get('action_type')
        limit = request.args.get('limit', 100, type=int)
        
        session = Session()
        
        # Importar el gestor de estadísticas
        from statistics import StatisticsManager
        stats_manager = StatisticsManager(session)
        
        # Obtener logs
        logs = stats_manager.get_activity_logs(
            user_id=user_id,
            parking_id=parking_id,
            action_type=action_type,
            limit=limit
        )
        
        session.close()
        
        if logs is not None:
            return jsonify({
                'logs': logs,
                'total': len(logs)
            })
        else:
            return jsonify({'error': 'Error retrieving logs'}), 500
        
    except Exception as e:
        logger.error(f"Error obteniendo logs de actividad: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/logs/panels', methods=['GET'])
@require_auth
def get_panel_logs():
    """Obtener logs de mensajes de paneles (requiere autenticación)"""
    try:
        panel_id = request.args.get('panel_id', type=int)
        parking_id = request.args.get('parking_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        session = Session()
        
        # Importar el gestor de estadísticas
        from statistics import StatisticsManager
        stats_manager = StatisticsManager(session)
        
        # Obtener logs
        logs = stats_manager.get_panel_message_logs(
            panel_id=panel_id,
            parking_id=parking_id,
            limit=limit
        )
        
        session.close()
        
        if logs is not None:
            return jsonify({
                'logs': logs,
                'total': len(logs)
            })
        else:
            return jsonify({'error': 'Error retrieving logs'}), 500
        
    except Exception as e:
        logger.error(f"Error obteniendo logs de paneles: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT)