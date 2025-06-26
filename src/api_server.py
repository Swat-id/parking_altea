import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from config import DB_URL, API_PORT
from models import Base, User, Parking, Access, Panel, OccupancyHistory, ScheduledMessage, ActivityLog, PanelMessageLog, VehicleCount, CameraLog, UserParking, UserPanel, UserAccess
from panel_client import send_to_panel, ping_panel
from auth import (
    create_user, authenticate_user, delete_user, change_password, 
    get_user_permissions, assign_user_to_resources, require_auth
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://157.180.91.63:5789', 'http://localhost:5173', 'http://localhost:3000'], supports_credentials=True)

engine = create_engine(DB_URL, echo=False)
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
def login():
    try:
        req = request.get_json()
        email = req.get('email')
        password = req.get('password')
        if not all([email, password]):
            return jsonify({'error': 'Faltan campos requeridos: email, password'}), 400
        
        # LOG: Imprimir email recibido
        print(f"[DEBUG] Intentando login para: {email}")
        
        session = Session()
        result = authenticate_user(session, email, password)
        
        # LOG: Imprimir resultado de autenticación
        print(f"[DEBUG] Resultado autenticación: {result}")
        
        if not result['success']:
            return jsonify({'error': result['error']}), 401
        return jsonify({'token': result['token'], 'user': result['user']})
    except Exception as e:
        # LOG: Imprimir excepción completa
        import traceback
        print(f"[ERROR] Excepción en /auth/login: {e}")
        traceback.print_exc()
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
                'estado': p.status,
                'threshold_dense': p.threshold_dense,
                'threshold_full': p.threshold_full
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
        
        # Validaciones adicionales
        if occupancy > p.max_capacity * 2:
            session.close()
            return jsonify({'error': f'Occupancy cannot exceed {p.max_capacity * 2} (double capacity)'}), 400
        
        # Actualizar ocupación
        p.current_occupancy = occupancy
        
        # Recalcular estado con nueva lógica: descuadre negativo = COMPLETO
        free = p.max_capacity - p.current_occupancy
        
        if free < 0:
            # Descuadre negativo - mostrar como COMPLETO
            p.status = 'COMPLETO'
            logger.warning(f"Manual adjustment: Descuadre negativo - Parking: {p.name}, Free spaces: {free}, Status set to COMPLETO")
        elif free <= p.threshold_full:
            p.status = 'COMPLETO'
        elif free <= p.threshold_dense:
            p.status = 'DENSO'
        else:
            p.status = 'LIBRE'
        
        # Guardar en historial con marca de ajuste manual
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
        final_free_spaces = p.max_capacity - final_occupancy
        
        session.commit()
        session.close()
        
        logger.info(f"Manual occupancy update - Parking: {parking_name}, Previous: {previous_occupancy}, New: {final_occupancy}, Change: {change_amount}, Status: {final_status}")
        
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'occupancy': final_occupancy,
            'free_spaces': final_free_spaces,
            'status': final_status,
            'previous_occupancy': previous_occupancy,
            'change_amount': change_amount,
            'adjustment_type': 'manual'
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
        parking_id = request.args.get('parking_id', type=int)
        
        session = Session()
        
        # Construir query
        query = session.query(Panel)
        
        # Filtrar por parking si se especifica
        if parking_id:
            query = query.filter(Panel.parking_id == parking_id)
        
        panels = query.all()
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

@app.route('/camera/logs', methods=['GET'])
def get_camera_logs():
    """Obtener logs de cámaras con filtros"""
    try:
        # Parámetros de filtrado
        parking_id = request.args.get('parking_id', type=int)
        access_id = request.args.get('access_id', type=int)
        status = request.args.get('status')  # 'processed', 'discarded', 'error'
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        session = Session()
        
        # Construir query
        query = session.query(CameraLog)
        
        if parking_id:
            query = query.filter(CameraLog.parking_id == parking_id)
        if access_id:
            query = query.filter(CameraLog.access_id == access_id)
        if status:
            query = query.filter(CameraLog.status == status)
        
        # Ordenar por fecha de recepción (más reciente primero)
        query = query.order_by(CameraLog.received_at.desc())
        
        # Aplicar límite y offset
        total_count = query.count()
        logs = query.offset(offset).limit(limit).all()
        
        # Formatear respuesta
        data = []
        for log in logs:
            log_data = {
                'id': log.id,
                'camera_ip': log.camera_ip,
                'camera_line': log.camera_line,
                'camera_name': log.camera_name,
                'parking_id': log.parking_id,
                'parking_name': log.parking.name if log.parking else None,
                'vehicle_in': log.vehicle_in,
                'vehicle_out': log.vehicle_out,
                'previous_vehicle_in': log.previous_vehicle_in,
                'previous_vehicle_out': log.previous_vehicle_out,
                'delta_in': log.delta_in,
                'delta_out': log.delta_out,
                'status': log.status,
                'error_message': log.error_message,
                'processing_time': log.processing_time,
                'new_occupancy': log.new_occupancy,
                'occupancy_change': log.occupancy_change,
                'parking_status': log.parking_status,
                'raw_message': log.raw_message,
                'received_at': log.received_at.isoformat() if log.received_at else None,
                'processed_at': log.processed_at.isoformat() if log.processed_at else None
            }
            data.append(log_data)
        
        session.close()
        
        return jsonify({
            'logs': data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo logs de cámaras: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/camera/logs/stats', methods=['GET'])
def get_camera_logs_stats():
    """Obtener estadísticas de logs de cámaras"""
    try:
        parking_id = request.args.get('parking_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        session = Session()
        
        # Calcular fecha límite
        from datetime import datetime, timedelta
        limit_date = datetime.now() - timedelta(days=days)
        
        # Construir query
        query = session.query(CameraLog).filter(CameraLog.received_at >= limit_date)
        
        if parking_id:
            query = query.filter(CameraLog.parking_id == parking_id)
        
        # Obtener estadísticas
        total_logs = query.count()
        processed_logs = query.filter(CameraLog.status == 'processed').count()
        error_logs = query.filter(CameraLog.status == 'error').count()
        discarded_logs = query.filter(CameraLog.status == 'discarded').count()
        
        # Obtener logs por parking
        parking_stats = []
        if not parking_id:
            parking_stats_query = session.query(
                CameraLog.parking_id,
                func.count(CameraLog.id).label('total'),
                func.count(CameraLog.id).filter(CameraLog.status == 'processed').label('processed'),
                func.count(CameraLog.id).filter(CameraLog.status == 'error').label('errors')
            ).filter(CameraLog.received_at >= limit_date).group_by(CameraLog.parking_id)
            
            for stat in parking_stats_query.all():
                parking = session.query(Parking).get(stat.parking_id)
                parking_stats.append({
                    'parking_id': stat.parking_id,
                    'parking_name': parking.name if parking else 'Unknown',
                    'total_logs': stat.total,
                    'processed_logs': stat.processed,
                    'error_logs': stat.errors
                })
        
        session.close()
        
        return jsonify({
            'period_days': days,
            'total_logs': total_logs,
            'processed_logs': processed_logs,
            'error_logs': error_logs,
            'discarded_logs': discarded_logs,
            'success_rate': (processed_logs / total_logs * 100) if total_logs > 0 else 0,
            'parking_stats': parking_stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de logs de cámaras: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/cameras', methods=['GET'])
def get_parking_cameras(pid):
    """Obtener cámaras de un parking específico"""
    try:
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Obtener cámaras del parking
        cameras = session.query(Access).filter_by(parking_id=pid).all()
        
        data = []
        for camera in cameras:
            camera_data = {
                'id': camera.id,
                'name': camera.name,
                'ip': camera.ip,
                'line': camera.line,
                'status': getattr(camera, 'status', 'OFFLINE'),
                'last_message_received': camera.last_message_received.isoformat() if camera.last_message_received else None,
                'last_ping_check': camera.last_ping_check.isoformat() if camera.last_ping_check else None,
                'ping_status': getattr(camera, 'ping_status', 'UNKNOWN'),
                'last_vehicle_in': camera.last_vehicle_in,
                'last_vehicle_out': camera.last_vehicle_out
            }
            data.append(camera_data)
        
        session.close()
        
        return jsonify({
            'parking_id': pid,
            'parking_name': parking.name,
            'cameras': data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo cámaras del parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/access/<int:access_id>/line', methods=['PUT'])
def update_camera_line(access_id):
    """Actualizar línea de una cámara"""
    try:
        req = request.get_json(force=True)
        new_line = req.get('line')
        
        if new_line is None:
            return jsonify({'error': 'Missing line field'}), 400
        
        if not isinstance(new_line, int) or new_line < 1:
            return jsonify({'error': 'Line must be a positive integer'}), 400
        
        session = Session()
        access = session.query(Access).get(access_id)
        
        if not access:
            session.close()
            return jsonify({'error': 'Camera not found'}), 404
        
        # Verificar que no haya conflicto con otra cámara del mismo parking
        existing_camera = session.query(Access).filter(
            Access.parking_id == access.parking_id,
            Access.line == new_line,
            Access.id != access_id
        ).first()
        
        if existing_camera:
            session.close()
            return jsonify({'error': f'Line {new_line} is already used by camera {existing_camera.name}'}), 400
        
        # Guardar línea anterior para logging
        old_line = access.line
        camera_name = access.name
        parking_name = access.parking.name
        
        # Actualizar línea
        access.line = new_line
        
        session.commit()
        session.close()
        
        logger.info(f"Camera line updated - Camera: {camera_name}, Parking: {parking_name}, Old line: {old_line}, New line: {new_line}")
        
        return jsonify({
            'status': 'ok',
            'camera_id': access_id,
            'camera_name': camera_name,
            'parking_name': parking_name,
            'old_line': old_line,
            'new_line': new_line
        })
        
    except Exception as e:
        logger.error(f"Error updating camera line for access {access_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/cameras/status', methods=['GET'])
def get_all_cameras_status():
    """Obtener estado de todas las cámaras"""
    try:
        session = Session()
        
        # Obtener todas las cámaras con información del parking
        cameras = session.query(Access).join(Parking).all()
        
        data = []
        for camera in cameras:
            camera_data = {
                'id': camera.id,
                'name': camera.name,
                'ip': camera.ip,
                'line': camera.line,
                'status': getattr(camera, 'status', 'OFFLINE'),
                'last_message_received': camera.last_message_received.isoformat() if camera.last_message_received else None,
                'last_ping_check': camera.last_ping_check.isoformat() if camera.last_ping_check else None,
                'ping_status': getattr(camera, 'ping_status', 'UNKNOWN'),
                'parking_id': camera.parking_id,
                'parking_name': camera.parking.name,
                'last_vehicle_in': camera.last_vehicle_in,
                'last_vehicle_out': camera.last_vehicle_out
            }
            data.append(camera_data)
        
        session.close()
        
        return jsonify({
            'cameras': data,
            'total_count': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cámaras: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/parking/<int:pid>/hourly-statistics', methods=['GET'])
def get_parking_hourly_statistics(pid):
    """Obtener estadísticas por horas de un parking"""
    try:
        # Parámetros
        date = request.args.get('date')  # YYYY-MM-DD
        days = request.args.get('days', 7, type=int)
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Calcular fechas
        from datetime import datetime, timedelta
        if date:
            start_date = datetime.strptime(date, '%Y-%m-%d')
            end_date = start_date + timedelta(days=1)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
        # Obtener estadísticas por horas
        hourly_stats = []
        for hour in range(24):
            hour_start = start_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Obtener logs de cámaras para esta hora
            camera_logs = session.query(CameraLog).filter(
                CameraLog.parking_id == pid,
                CameraLog.received_at >= hour_start,
                CameraLog.received_at < hour_end,
                CameraLog.status == 'processed'
            ).all()
            
            # Calcular métricas
            total_vehicles_in = sum(log.delta_in or 0 for log in camera_logs)
            total_vehicles_out = sum(log.delta_out or 0 for log in camera_logs)
            message_count = len(camera_logs)
            
            # Obtener ocupación promedio de la hora (si hay datos)
            occupancy_data = session.query(OccupancyHistory).filter(
                OccupancyHistory.parking_id == pid,
                OccupancyHistory.timestamp >= hour_start,
                OccupancyHistory.timestamp < hour_end
            ).all()
            
            avg_occupancy = 0
            max_occupancy = 0
            min_occupancy = 0
            
            if occupancy_data:
                occupancies = [data.occupancy for data in occupancy_data]
                avg_occupancy = sum(occupancies) / len(occupancies)
                max_occupancy = max(occupancies)
                min_occupancy = min(occupancies)
            
            hourly_stats.append({
                'hour': hour,
                'hour_label': f'{hour:02d}:00',
                'total_vehicles_in': total_vehicles_in,
                'total_vehicles_out': total_vehicles_out,
                'net_change': total_vehicles_in - total_vehicles_out,
                'message_count': message_count,
                'avg_occupancy': round(avg_occupancy, 1),
                'max_occupancy': max_occupancy,
                'min_occupancy': min_occupancy
            })
        
        # Obtener estadísticas de cámaras para el período
        camera_stats = []
        cameras = session.query(Access).filter(Access.parking_id == pid).all()
        
        for camera in cameras:
            camera_logs = session.query(CameraLog).filter(
                CameraLog.access_id == camera.id,
                CameraLog.received_at >= start_date,
                CameraLog.received_at < end_date
            ).all()
            
            total_messages = len(camera_logs)
            processed_messages = len([log for log in camera_logs if log.status == 'processed'])
            error_messages = len([log for log in camera_logs if log.status == 'error'])
            duplicate_messages = len([log for log in camera_logs if log.status == 'duplicate'])
            
            total_vehicles_in = sum(log.delta_in or 0 for log in camera_logs if log.status == 'processed')
            total_vehicles_out = sum(log.delta_out or 0 for log in camera_logs if log.status == 'processed')
            
            camera_stats.append({
                'camera_id': camera.id,
                'camera_name': camera.name,
                'camera_ip': camera.ip,
                'camera_line': camera.line,
                'status': camera.status,
                'total_messages': total_messages,
                'processed_messages': processed_messages,
                'error_messages': error_messages,
                'duplicate_messages': duplicate_messages,
                'success_rate': round((processed_messages / total_messages * 100) if total_messages > 0 else 0, 1),
                'total_vehicles_in': total_vehicles_in,
                'total_vehicles_out': total_vehicles_out,
                'last_message': camera.last_message_received.isoformat() if camera.last_message_received else None
            })
        
        session.close()
        
        return jsonify({
            'parking_id': pid,
            'parking_name': parking.name,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'hourly_statistics': hourly_stats,
            'camera_statistics': camera_stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas por horas del parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/panels/verify', methods=['POST'])
def verify_all_panels():
    """Verificar el estado de todos los paneles mediante ping"""
    try:
        session = Session()
        panels = session.query(Panel).all()
        
        results = []
        updated_count = 0
        
        from panel_client import ping_panel
        
        logger.info(f"Iniciando verificación de {len(panels)} paneles")
        
        for panel in panels:
            try:
                logger.info(f"Verificando panel {panel.id} ({panel.name}) - IP: {panel.ip} - Estado actual: {panel.status}")
                
                start_time = datetime.now()
                success = ping_panel(panel.ip)
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                new_status = 'ONLINE' if success else 'OFFLINE'
                previous_status = panel.status
                status_changed = previous_status != new_status
                
                logger.info(f"Panel {panel.id}: ping_success={success}, previous_status={previous_status}, new_status={new_status}, status_changed={status_changed}")
                
                # Actualizar estado del panel
                panel.status = new_status
                panel.last_update = datetime.now()
                
                if status_changed:
                    updated_count += 1
                    logger.info(f"Panel {panel.id} actualizado: {previous_status} → {new_status}")
                
                results.append({
                    'panel_id': panel.id,
                    'panel_name': panel.name,
                    'ip': panel.ip,
                    'previous_status': previous_status,
                    'new_status': new_status,
                    'response_time': response_time if success else None,
                    'status_changed': status_changed,
                    'ping_success': success
                })
                
            except Exception as e:
                logger.error(f"Error verificando panel {panel.id}: {e}")
                results.append({
                    'panel_id': panel.id,
                    'panel_name': panel.name,
                    'ip': panel.ip,
                    'error': str(e),
                    'status_changed': False,
                    'ping_success': False
                })
        
        logger.info(f"Commit de cambios: {updated_count} paneles actualizados")
        session.commit()
        
        # Refrescar los objetos panel para asegurar persistencia
        for panel in panels:
            session.refresh(panel)
            logger.info(f"Panel {panel.id} después del refresh: status={panel.status}")
        
        session.close()
        
        logger.info(f"Verificación completada: {len(panels)} total, {updated_count} actualizados")
        
        return jsonify({
            'status': 'ok',
            'total_panels': len(panels),
            'updated_count': updated_count,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error verificando paneles: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=API_PORT, debug=False)