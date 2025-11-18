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
from models import (
    Base, User, Parking, Access, Panel, OccupancyHistory, ScheduledMessage, ActivityLog, 
    PanelMessageLog, VehicleCount, CameraLog, UserParking, UserPanel, UserAccess, 
    PanelSchedule, PanelScheduleLog, PanelType, CameraParking, AlarmConfiguration, 
    AlarmConfigurationTarget, AlarmConfigurationThreshold, Alarm, AlarmHistory, 
    IndividualSensor, SensorStatusHistory, SensorCurrentStatus, ParkingSensorSummary,
    ParkingPanelWindow, PanelWindowConfiguration
)
from panel_schedule_service import PanelScheduleService
from panel_window_service import PanelWindowService
from auth import (
    create_user, authenticate_user, delete_user, change_password, 
    get_user_permissions, assign_user_to_resources, require_auth, require_superadmin,
    require_parking_access, require_panel_access, filter_by_user_permissions
)

# Token authentication decorator (placeholder for v4.1.0)
def token_required(f):
    """Placeholder decorator - replace with actual auth logic when needed"""
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://157.180.91.63:5789', 'http://localhost:5173', 'http://localhost:3000'], supports_credentials=True)

# Crear Blueprint para API
from flask import Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# ============================================================================
# ENDPOINTS DE AUTENTICACIÓN Y USUARIOS
# ============================================================================

@api_bp.route('/auth/register', methods=['POST'])
def register_user():
    """Crear un nuevo usuario"""
    try:
        req = request.get_json(force=True)
        name = req.get('name')
        email = req.get('email')
        password = req.get('password')
        role = req.get('role', 'user')  # Nuevo: permitir especificar rol
        
        if not all([name, email, password]):
            return jsonify({'error': 'Faltan campos requeridos: name, email, password'}), 400
        
        session = Session()
        result = create_user(session, name, email, password, role)  # Nuevo: pasar rol
        session.close()
        
        if result['success']:
            logger.info(f"Usuario creado: {email} (rol: {role})")
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/auth/login', methods=['POST'])
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
        # Nuevo: incluir el rol en la respuesta
        return jsonify({'token': result['token'], 'user': result['user']})
    except Exception as e:
        # LOG: Imprimir excepción completa
        import traceback
        print(f"[ERROR] Excepción en /auth/login: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/auth/user', methods=['DELETE'])
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

@api_bp.route('/auth/password', methods=['PUT'])
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

@api_bp.route('/auth/permissions', methods=['GET'])
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

@api_bp.route('/auth/assign', methods=['POST'])
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

@api_bp.route('/user/parkings', methods=['GET'])
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
                'threshold_full': p.threshold_full,
                'message_type': p.message_type
            }
            for p in parks
        ]
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo parkings del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/user/panels', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_user_panels():
    """Obtener paneles a los que tiene acceso el usuario autenticado"""
    try:
        session = Session()
        
        # Usar el filtrado automático por permisos
        accessible_panel_ids = getattr(request, 'accessible_panel_ids', [])
        user_role = request.user_data.get('role', 'user')
        user_id = request.user_data.get('user_id')
        
        logger.info(f"DEBUG Paneles - Usuario {user_id} (rol: {user_role}): {len(accessible_panel_ids)} paneles accesibles: {accessible_panel_ids}")
        
        if accessible_panel_ids:
            panels = session.query(Panel).filter(Panel.id.in_(accessible_panel_ids)).all()
        else:
            # Usuario no tiene acceso a ningún panel
            logger.warning(f"Usuario {user_id} no tiene acceso a ningún panel - devolviendo lista vacía")
            panels = []
        
        data = []
        for p in panels:
            panel_data = {
                'id': p.id,
                'name': p.name,
                'ip': p.ip,
                'ip_address': p.ip,  # Alias para compatibilidad
                'parking_id': p.parking_id,
                'parking_name': p.parking.name if p.parking else None,
                'status': p.status,
                'last_message': p.last_message,
                'last_update': p.last_update.isoformat() if p.last_update else None,
                'panel_type_id': p.panel_type_id,
                'panel_type': {
                    'id': p.panel_type.id,
                    'name': p.panel_type.name,
                    'manufacturer': p.panel_type.manufacturer.name,
                    'protocol': p.panel_type.protocol_type,
                    'windows_count': p.panel_type.windows_count
                } if p.panel_type else None,
                'port': p.port,
                'is_active': p.is_active,
                'windows_count': p.windows_count,
                # NUEVO v4.3.0: Mensajes por ventana para Tipo 3 y Tipo 4
                'last_message_window_0': getattr(p, 'last_message_window_0', None),
                'last_message_window_1': getattr(p, 'last_message_window_1', None),
                'last_update_window_0': p.last_update_window_0.isoformat() if hasattr(p, 'last_update_window_0') and p.last_update_window_0 else None,
                'last_update_window_1': p.last_update_window_1.isoformat() if hasattr(p, 'last_update_window_1') and p.last_update_window_1 else None
            }
            data.append(panel_data)
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo paneles del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/user/cameras', methods=['GET'])
@require_auth
def get_user_cameras():
    """Obtener cámaras a las que tiene acceso el usuario autenticado"""
    try:
        user_id = request.user_data['user_id']
        user_role = request.user_data.get('role', 'user')
        
        session = Session()
        
        if user_role == 'superadmin':
            # Superadmin ve todas las cámaras
            cameras = session.query(Access).all()
        else:
            # Usuario normal solo ve sus cámaras asignadas
            user_accesses = session.query(UserAccess).filter(UserAccess.user_id == user_id).all()
            access_ids = [ua.access_id for ua in user_accesses]
            cameras = session.query(Access).filter(Access.id.in_(access_ids)).all()
        
        data = []
        for c in cameras:
            # Obtener los parkings asociados a esta cámara usando la relación muchos a muchos
            camera_parkings = session.query(CameraParking).filter(CameraParking.camera_id == c.id).all()
            
            for cp in camera_parkings:
                parking = cp.parking
                data.append({
                    'id': c.id,
                    'name': c.name,
                    'ip': c.ip,
                    'line': c.line,
                    'parking_id': parking.id,
                    'parking_name': parking.name,
                    'status': getattr(c, 'status', 'OFFLINE'),
                    'last_message_received': c.last_message_received.isoformat() if c.last_message_received else None
                })
        
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo cámaras del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/user/panel-config', methods=['GET'])
@require_auth
def get_user_panel_config():
    """Obtener configuración de paneles del usuario autenticado"""
    try:
        user_id = request.user_data['user_id']
        user_role = request.user_data.get('role', 'user')
        
        # Si es superadmin, puede especificar company_id para ver configuración de otra empresa
        company_id = request.args.get('company_id', type=int)
        target_user_id = company_id if (user_role == 'superadmin' and company_id) else user_id
        
        session = Session()
        
        from user_panel_config_service import UserPanelConfigService
        config_service = UserPanelConfigService(session)
        
        config = config_service.get_user_config(target_user_id)
        session.close()
        
        if config:
            return jsonify(config), 200
        else:
            return jsonify({'error': 'Configuración no encontrada'}), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo configuración de paneles del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/user/panel-config', methods=['POST', 'PUT'])
@require_auth
def update_user_panel_config():
    """Actualizar configuración de paneles del usuario autenticado"""
    try:
        user_id = request.user_data['user_id']
        user_role = request.user_data.get('role', 'user')
        req = request.get_json() or {}
        
        # Si es superadmin, puede especificar company_id para actualizar configuración de otra empresa
        company_id = req.get('company_id')
        target_user_id = company_id if (user_role == 'superadmin' and company_id) else user_id
        
        session = Session()
        
        from user_panel_config_service import UserPanelConfigService
        config_service = UserPanelConfigService(session)
        
        # Preparar datos de configuración
        config_data = {
            'panel_update_interval_seconds': req.get('panel_update_interval_seconds'),
            'is_active': req.get('is_active', True)
        }
        
        # Validar que panel_update_interval_seconds esté presente y sea válido
        if 'panel_update_interval_seconds' not in config_data or config_data['panel_update_interval_seconds'] is None:
            session.close()
            return jsonify({'error': 'panel_update_interval_seconds es requerido'}), 400
        
        if config_data['panel_update_interval_seconds'] <= 0:
            session.close()
            return jsonify({'error': 'panel_update_interval_seconds debe ser mayor que 0'}), 400
        
        result = config_service.update_user_config(target_user_id, config_data)
        session.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error actualizando configuración de paneles del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/user/parking/<int:pid>', methods=['GET'])
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

@api_bp.route('/parkings', methods=['GET'])
@require_auth
def list_parkings():
    """Listar todos los parkings (requiere autenticación)"""
    try:
        user_id = request.user_data['user_id']
        user_role = request.user_data.get('role', 'user')
        
        session = Session()
        
        if user_role == 'superadmin':
            # Superadmin ve todos los parkings
            parks = session.query(Parking).all()
        else:
            # Usuario normal solo ve sus parkings asignados
            user_parkings = session.query(UserParking).filter(UserParking.user_id == user_id).all()
            parking_ids = [up.parking_id for up in user_parkings]
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
                'threshold_full': p.threshold_full,
                'message_type': p.message_type
            }
            for p in parks
        ]
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error listando parkings: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings', methods=['POST'])
@require_superadmin
def create_parking():
    """Crear un nuevo parking (solo superadmin)"""
    try:
        req = request.get_json(force=True)
        name = req.get('name')
        location = req.get('location', '')
        total_plazas = req.get('total_plazas')
        threshold_dense = req.get('threshold_dense')
        threshold_full = req.get('threshold_full')
        message_type = req.get('message_type', 'ESTADO')  # NUEVO: Campo opcional
        cameras = req.get('cameras', [])  # Lista de cámaras a asignar
        
        if not all([name, total_plazas, threshold_dense, threshold_full]):
            return jsonify({'error': 'Faltan campos requeridos: name, total_plazas, threshold_dense, threshold_full'}), 400
        
        if total_plazas <= 0:
            return jsonify({'error': 'total_plazas debe ser mayor que 0'}), 400
        
        if threshold_dense < 0:
            return jsonify({'error': 'threshold_dense debe ser mayor o igual que 0'}), 400
        
        if threshold_full < 0:
            return jsonify({'error': 'threshold_full debe ser mayor o igual que 0'}), 400
        
        # Validar message_type
        valid_message_types = ['ESTADO', 'PLAZAS_LIBRES']
        if message_type not in valid_message_types:
            return jsonify({'error': f'message_type debe ser uno de: {valid_message_types}'}), 400
        
        session = Session()
        
        # Verificar que el nombre no exista
        existing_parking = session.query(Parking).filter(Parking.name == name).first()
        if existing_parking:
            session.close()
            return jsonify({'error': 'Ya existe un parking con ese nombre'}), 400
        
        # Crear el parking
        new_parking = Parking(
            name=name,
            location=location,
            max_capacity=total_plazas,
            threshold_dense=threshold_dense,
            threshold_full=threshold_full,
            current_occupancy=0,
            status='LIBRE',
            message_type=message_type  # NUEVO: Incluir message_type
        )
        
        session.add(new_parking)
        session.commit()
        
        # Obtener el parking creado con el ID asignado
        session.refresh(new_parking)
        parking_id = new_parking.id
        
        # Asignar cámaras al parking usando la nueva relación muchos a muchos
        cameras_created = []
        for camera_data in cameras:
            if camera_data.get('ip'):
                # Verificar si ya existe una cámara con esa IP y línea
                existing_access = session.query(Access).filter(
                    Access.ip == camera_data['ip'],
                    Access.line == camera_data.get('line', 0)
                ).first()
                
                if existing_access:
                    # Si existe, crear relación con el parking actual
                    new_camera_parking = CameraParking(
                        camera_id=existing_access.id,
                        parking_id=parking_id
                    )
                    session.add(new_camera_parking)
                    cameras_created.append({
                        'id': existing_access.id,
                        'ip': existing_access.ip,
                        'line': existing_access.line,
                        'name': existing_access.name,
                        'status': 'existing'
                    })
                else:
                    # Crear nueva cámara
                    new_access = Access(
                        ip=camera_data['ip'],
                        line=camera_data.get('line', 0),
                        name=camera_data.get('name', ''),
                        last_vehicle_in=0,
                        last_vehicle_out=0,
                        status='OFFLINE'
                    )
                    session.add(new_access)
                    session.flush()  # Para obtener el ID
                    
                    # Crear relación con el parking
                    new_camera_parking = CameraParking(
                        camera_id=new_access.id,
                        parking_id=parking_id
                    )
                    session.add(new_camera_parking)
                    cameras_created.append({
                        'id': new_access.id,
                        'ip': new_access.ip,
                        'line': new_access.line,
                        'name': new_access.name,
                        'status': 'new'
                    })
        
        session.commit()
        session.close()
        
        logger.info(f"Parking creado: {name} (ID: {parking_id}) con {len(cameras_created)} cámaras")
        return jsonify({
            'success': True,
            'parking': {
                'id': parking_id,
                'name': name,
                'location': location,
                'total_plazas': total_plazas,
                'threshold_dense': threshold_dense,
                'threshold_full': threshold_full,
                'estado': 'LIBRE'
            },
            'cameras': cameras_created
        }), 201
        
    except Exception as e:
        logger.error(f"Error creando parking: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:parking_id>', methods=['GET'])
@require_auth
def get_parking_by_id(parking_id):
    """Obtener un parking específico por ID (requiere autenticación)"""
    try:
        user_id = request.user_data['user_id']
        user_role = request.user_data.get('role', 'user')
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(parking_id)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Verificar permisos (superadmin ve todo, usuario normal solo sus parkings)
        if user_role != 'superadmin':
            user_parking = session.query(UserParking).filter(
                UserParking.user_id == user_id,
                UserParking.parking_id == parking_id
            ).first()
            if not user_parking:
                session.close()
                return jsonify({'error': 'Access denied'}), 403
        
        # Formatear respuesta
        data = {
            'id': parking.id,
            'name': parking.name,
            'location': parking.location,
            'total_plazas': parking.max_capacity,
            'plazas_ocupadas': parking.current_occupancy,
            'plazas_libres': parking.max_capacity - parking.current_occupancy,
            'estado': parking.status,
            'threshold_dense': parking.threshold_dense,
            'threshold_full': parking.threshold_full,
            'message_type': parking.message_type
        }
        
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo parking {parking_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:parking_id>', methods=['PUT'])
@require_superadmin
def edit_parking(parking_id):
    """Editar información general de un parking (solo superadmin)"""
    try:
        req = request.get_json(force=True)
        name = req.get('name')
        location = req.get('location')
        
        # Validar campos requeridos
        if not name:
            return jsonify({'error': 'El nombre del parking es requerido'}), 400
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).filter(Parking.id == parking_id).first()
        if not parking:
            session.close()
            return jsonify({'error': 'Parking no encontrado'}), 404
        
        # Verificar que el nombre no exista en otro parking
        existing_parking = session.query(Parking).filter(
            Parking.name == name,
            Parking.id != parking_id
        ).first()
        if existing_parking:
            session.close()
            return jsonify({'error': 'Ya existe otro parking con ese nombre'}), 400
        
        # Guardar valores anteriores para el log
        old_name = parking.name
        old_location = parking.location
        
        # Actualizar campos
        parking.name = name
        if location is not None:
            parking.location = location
        
        session.commit()
        
        # Preparar respuesta con datos actualizados
        updated_parking = {
            'id': parking.id,
            'name': parking.name,
            'location': parking.location,
            'total_plazas': parking.max_capacity,
            'plazas_ocupadas': parking.current_occupancy,
            'plazas_libres': parking.max_capacity - parking.current_occupancy,
            'status': parking.status,
            'threshold_dense': parking.threshold_dense,
            'threshold_full': parking.threshold_full,
            'message_type': parking.message_type
        }
        
        session.close()
        
        logger.info(f"Parking editado: ID {parking_id}, Nombre: '{old_name}' -> '{name}', Ubicación: '{old_location}' -> '{location}'")
        
        return jsonify({
            'message': 'Parking actualizado correctamente',
            'parking': updated_parking
        }), 200
        
    except Exception as e:
        logger.error(f"Error editando parking: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/status', methods=['GET'])
@require_auth
def get_parkings_status():
    """Obtener estado completo de todos los parkings con información de paneles (requiere autenticación)"""
    try:
        user_id = request.user_data['user_id']
        user_role = request.user_data.get('role', 'user')
        
        session = Session()
        
        # Importar servicios necesarios
        from panel_schedule_service import PanelScheduleService
        
        # Obtener parkings según el rol del usuario
        if user_role == 'superadmin':
            # Superadmin ve todos los parkings
            parks = session.query(Parking).all()
        else:
            # Usuario normal solo ve sus parkings asignados
            user_parkings = session.query(UserParking).filter(UserParking.user_id == user_id).all()
            parking_ids = [up.parking_id for up in user_parkings]
            parks = session.query(Parking).filter(Parking.id.in_(parking_ids)).all()
        data = []
        
        for parking in parks:
            # Calcular valores básicos
            plazas_libres = parking.max_capacity - parking.current_occupancy
            plazas_ocupadas = parking.current_occupancy
            
            # Determinar estado en valenciano para paneles
            estado_valenciano = ""
            if parking.status == "LIBRE":
                estado_valenciano = "LLIURE"
            elif parking.status == "DENSO":
                estado_valenciano = "DENS"
            elif parking.status == "COMPLETO":
                estado_valenciano = "COMPLET"
            else:
                estado_valenciano = parking.status
            
            # Verificar si hay programaciones activas
            schedule_service = PanelScheduleService(session)
            active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
            
            # Determinar qué se está mostrando en los paneles
            panel_display_text = ""
            if active_schedules:
                # Si hay programaciones activas, mostrar el mensaje de la programación
                panel_display_text = active_schedules[0].message
            else:
                # Si no hay programaciones activas, mostrar el estado en valenciano
                panel_display_text = estado_valenciano
            
            # Obtener información de paneles del parking
            panels = session.query(Panel).filter(Panel.parking_id == parking.id).all()
            panel_info = []
            for panel in panels:
                panel_info.append({
                    'id': panel.id,
                    'name': panel.name,
                    'ip': panel.ip,
                    'status': panel.status,
                    'protocol_version': panel.protocol_version,
                    'last_message': panel.last_message,
                    'last_update': panel.last_update.isoformat() if panel.last_update else None
                })
            
            # Construir objeto de datos del parking
            parking_data = {
                'id': parking.id,
                'name': parking.name,
                'location': parking.location,
                'total_plazas': parking.max_capacity,
                'plazas_ocupadas': plazas_ocupadas,
                'plazas_libres': plazas_libres,
                'estado': parking.status,  # Estado en español (LIBRE, DENSO, OCUPADO)
                'estado_valenciano': estado_valenciano,  # Estado en valenciano (LLIURE, DENS, COMPLET)
                'panel_display_text': panel_display_text,  # Texto que se está mostrando en los paneles
                'has_active_schedules': len(active_schedules) > 0,  # Si hay programaciones activas
                'active_schedules_count': len(active_schedules),
                'threshold_dense': parking.threshold_dense,
                'threshold_full': parking.threshold_full,
                'panels': panel_info,
                'last_update': datetime.now().isoformat()
            }
            
            data.append(parking_data)
        
        session.close()
        
        return jsonify({
            'success': True,
            'total_parkings': len(data),
            'timestamp': datetime.now().isoformat(),
            'parkings': data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de parkings: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>', methods=['GET'])
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

@api_bp.route('/parkings/<int:pid>/occupancy', methods=['POST'])
@require_parking_access('pid')
def set_occupancy(pid):
    """Establecer ocupación de un parking"""
    try:
        # Log de debugging
        logger.info(f"Received occupancy update request for parking {pid}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request data: {request.get_data()}")
        
        # Manejar JSON de forma más robusta
        try:
            req = request.get_json(force=True)
        except Exception as json_error:
            logger.error(f"Error parsing JSON: {json_error}")
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        logger.info(f"Parsed JSON: {req}")
        
        occupancy = req.get('occupancy')
        
        if occupancy is None:
            logger.error("Missing occupancy field in request")
            return jsonify({'error': 'Missing occupancy field'}), 400
        
        if not isinstance(occupancy, int) or occupancy < 0:
            logger.error(f"Invalid occupancy value: {occupancy} (type: {type(occupancy)})")
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
        if occupancy > p.max_capacity * 5:
            session.close()
            return jsonify({'error': f'Occupancy cannot exceed {p.max_capacity * 5} (5x capacity). For higher values, contact administrator.'}), 400
        
        # Advertencia si excede la capacidad máxima pero es permitido
        if occupancy > p.max_capacity:
            logger.warning(f"Manual adjustment exceeds capacity - Parking: {p.name}, Capacity: {p.max_capacity}, Requested: {occupancy}, Excess: {occupancy - p.max_capacity}")
        
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
        final_max_capacity = p.max_capacity  # Guardar antes de cerrar sesión
        
        session.commit()
        session.close()
        
        # CORRECCIÓN EC-004: Solo actualizar paneles si hay programación activa
        # El worker se encarga de actualizaciones regulares respetando message_type
        try:
            from panel_schedule_service import PanelScheduleService
            session_temp = Session()
            schedule_service = PanelScheduleService(session_temp)
            active_schedules = schedule_service.get_active_schedules_for_parking(pid)
            
            if active_schedules:
                # Solo actualizar si hay programación activa para mostrarla inmediatamente
                from panel_communication_service import update_parking_panels
                update_parking_panels(pid, final_occupancy, final_max_capacity, final_status)
                logger.info(f"Panel updated due to active schedule after manual occupancy update for parking {parking_name}")
            else:
                logger.info(f"Manual occupancy update for {parking_name} - Panel will be updated by worker in next cycle (respects message_type)")
            
            session_temp.close()
        except Exception as e:
            logger.error(f"Error checking schedules after manual occupancy update: {e}")
        
        logger.info(f"Manual occupancy update - Parking: {parking_name}, Previous: {previous_occupancy}, New: {final_occupancy}, Change: {change_amount}, Status: {final_status}")
        
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'occupancy': final_occupancy,
            'free_spaces': final_free_spaces,
            'parking_status': final_status,
            'previous_occupancy': previous_occupancy,
            'change_amount': change_amount,
            'adjustment_type': 'manual'
        })
        
    except Exception as e:
        logger.error(f"Error updating occupancy for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/config', methods=['POST'])
@require_parking_access('pid')
def update_parking_config(pid):
    """Actualizar configuración de un parking"""
    try:
        req = request.get_json(force=True)
        max_capacity = req.get('total_plazas')
        threshold_dense = req.get('threshold_dense')
        threshold_full = req.get('threshold_full')
        message_type = req.get('message_type')  # NUEVO: Campo opcional para edición
        
        if max_capacity is not None and (not isinstance(max_capacity, int) or max_capacity <= 0):
            return jsonify({'error': 'total_plazas must be a positive integer'}), 400
        
        if threshold_dense is not None and (not isinstance(threshold_dense, int) or threshold_dense < 0):
            return jsonify({'error': 'threshold_dense must be a non-negative integer'}), 400
        
        if threshold_full is not None and (not isinstance(threshold_full, int) or threshold_full < 0):
            return jsonify({'error': 'threshold_full must be a non-negative integer'}), 400
        
        # Validar message_type si se proporciona
        if message_type is not None:
            valid_message_types = ['ESTADO', 'PLAZAS_LIBRES']
            if message_type not in valid_message_types:
                return jsonify({'error': f'message_type debe ser uno de: {valid_message_types}'}), 400
        
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
        if message_type is not None:
            p.message_type = message_type  # NUEVO: Actualizar message_type
        
        # Recalcular estado con nuevos umbrales
        free = p.max_capacity - p.current_occupancy
        if free <= p.threshold_full:
            p.status = 'COMPLETO'
        elif free <= p.threshold_dense:
            p.status = 'DENSO'
        else:
            p.status = 'LIBRE'
        
        # Guardar valores antes de cerrar la sesión
        final_occupancy = p.current_occupancy
        final_max_capacity = p.max_capacity
        final_threshold_dense = p.threshold_dense
        final_threshold_full = p.threshold_full
        final_status = p.status
        final_message_type = p.message_type  # NUEVO: Guardar message_type
        
        session.commit()
        session.close()
        
        # CORRECCIÓN EC-004: Actualizar paneles usando lógica del worker que respeta message_type
        try:
            from panel_update_methods import PanelUpdateMethods
            
            # Preparar datos como lo hace el worker
            parking_data = {
                'id': pid,
                'name': parking_name,
                'current_occupancy': final_occupancy,
                'max_capacity': final_max_capacity,
                'status': final_status,
                'message_type': final_message_type or 'ESTADO',
                'fixed_message_flag': False  # Los cambios de config no deberían tener mensaje fijo
            }
            
            # Usar la lógica correcta del worker (crear instancia mock)
            class MockWorker:
                def Session(self):
                    return Session()
            
            mock_worker = MockWorker()
            result = PanelUpdateMethods.update_parking_panels(mock_worker, parking_data)
            
            if result and result.panels_updated > 0:
                logger.info(f"Panel updated after config change for {parking_name} using worker logic (respects message_type)")
            else:
                logger.info(f"Config change for {parking_name} - Panel update handled by worker logic")
                
        except Exception as e:
            logger.error(f"Error updating panels after config change using worker logic: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"Parking config updated - Parking: {parking_name}, Max: {final_max_capacity}, Dense: {final_threshold_dense}, Full: {final_threshold_full}")
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'max_capacity': final_max_capacity,
            'threshold_dense': final_threshold_dense,
            'threshold_full': final_threshold_full,
            'current_status': final_status,
            'message_type': final_message_type  # NUEVO: Incluir en respuesta
        })
        
    except Exception as e:
        logger.error(f"Error updating config for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/cameras', methods=['PUT'])
@require_parking_access('pid')
def update_parking_cameras(pid):
    """Actualizar cámaras de un parking usando la nueva relación muchos a muchos"""
    try:
        req = request.get_json(force=True)
        cameras = req.get('cameras', [])
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Guardar el nombre del parking antes de cerrar la sesión
        parking_name = parking.name
        
        # Eliminar relaciones existentes del parking
        session.query(CameraParking).filter(CameraParking.parking_id == pid).delete()
        
        # Crear nuevas relaciones
        cameras_created = []
        for camera_data in cameras:
            if camera_data.get('ip'):
                # Verificar si ya existe una cámara con esa IP y línea
                existing_access = session.query(Access).filter(
                    Access.ip == camera_data['ip'],
                    Access.line == camera_data.get('line', 0)
                ).first()
                
                if existing_access:
                    # Si existe, crear relación con el parking actual
                    new_camera_parking = CameraParking(
                        camera_id=existing_access.id,
                        parking_id=pid
                    )
                    session.add(new_camera_parking)
                    cameras_created.append({
                        'id': existing_access.id,
                        'ip': existing_access.ip,
                        'line': existing_access.line,
                        'name': existing_access.name,
                        'status': 'existing'
                    })
                else:
                    # Crear nueva cámara
                    new_access = Access(
                        ip=camera_data['ip'],
                        line=camera_data.get('line', 0),
                        name=camera_data.get('name', ''),
                        last_vehicle_in=0,
                        last_vehicle_out=0,
                        status='OFFLINE'
                    )
                    session.add(new_access)
                    session.flush()  # Para obtener el ID
                    
                    # Crear relación con el parking
                    new_camera_parking = CameraParking(
                        camera_id=new_access.id,
                        parking_id=pid
                    )
                    session.add(new_camera_parking)
                    cameras_created.append({
                        'id': new_access.id,
                        'ip': new_access.ip,
                        'line': new_access.line,
                        'name': new_access.name,
                        'status': 'new'
                    })
        
        session.commit()
        session.close()
        
        logger.info(f"Parking cameras updated - Parking: {parking_name}, Cameras: {len(cameras_created)}")
        return jsonify({
            'status': 'ok',
            'parking': parking_name,
            'cameras': cameras_created
        })
        
    except Exception as e:
        logger.error(f"Error updating cameras for parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/message', methods=['POST'])
@require_parking_access('pid')
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
        
        # Enviar mensaje a todos los paneles del parking usando PanelCommunicationService
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        success_count = 0
        failed_panels = []
        
        # Convertir colores de texto a códigos numéricos
        color_codes = {
            'VERDE': 2,
            'ROJO': 1,
            'AMARILLO': 3
        }
        color_code = color_codes.get(color, 2)  # Verde por defecto
        
        # Convertir scroll a efecto
        effect_code = 12 if scroll else 2  # 12=scroll, 2=fijo
        
        for panel in panels:
            try:
                result = panel_service.send_custom_text(
                    panel_ip=panel.ip,
                    text=message,
                    color=color_code,
                    font_size=2,  # Tamaño 16 píxeles (código 2) - CORREGIDO
                    effect=effect_code  # Usar código numérico correcto
                )
                if result.get('success'):
                    success_count += 1
                else:
                    failed_panels.append(panel.ip)
                    logger.error(f"Error sending message to panel {panel.ip}: {result.get('message')}")
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

@api_bp.route('/panel/<ip>/message', methods=['POST'])
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
        
        # Enviar mensaje al panel específico usando PanelCommunicationService
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        # Convertir colores de texto a códigos numéricos
        color_codes = {
            'VERDE': 2,
            'ROJO': 1,
            'AMARILLO': 3
        }
        color_code = color_codes.get(color, 2)  # Verde por defecto
        
        # Convertir scroll a efecto
        effect_code = 12 if scroll else 2  # 12=scroll, 2=fijo
        
        result = panel_service.send_custom_text(
            panel_ip=panel.ip,
            text=message,
            color=color_code,
            font_size=2,  # Tamaño 16 píxeles (código 2) - CORREGIDO
            effect=effect_code  # Usar código numérico correcto
        )
        
        if result.get('success'):
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
            logger.error(f"Failed to send message to panel {ip}: {result.get('message')}")
            return jsonify({'error': 'Failed to send message to panel'}), 500
        
    except Exception as e:
        logger.error(f"Error setting panel message for IP {ip}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/message', methods=['GET'])
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

@api_bp.route('/parkings/<int:pid>/message', methods=['DELETE'])
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

@api_bp.route('/panels', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_all_panels():
    """Obtener todos los paneles con su estado actual e información de programaciones activas"""
    try:
        parking_id = request.args.get('parking_id', type=int)
        
        session = Session()
        
        # FILTRAR POR PERMISOS: Solo paneles accesibles al usuario
        # Ahora accessible_panel_ids incluye tanto paneles directos como paneles de parkings asignados
        accessible_panel_ids = getattr(request, 'accessible_panel_ids', [])
        
        # Construir query con filtrado por permisos
        query = session.query(Panel)
        
        if accessible_panel_ids:
            # Filtrar por paneles accesibles (incluye directos + por parking)
            query = query.filter(Panel.id.in_(accessible_panel_ids))
        else:
            # Usuario no tiene acceso a ningún panel, devolver lista vacía
            session.close()
            return jsonify([])
        
        # Filtrar por parking específico si se especifica
        if parking_id:
            query = query.filter(Panel.parking_id == parking_id)
        
        panels = query.all()
        data = []
        
        for panel in panels:
            # Verificar programaciones activas para este parking
            from panel_schedule_service import PanelScheduleService
            schedule_service = PanelScheduleService(session)
            active_schedules = schedule_service.get_active_schedules_for_parking(panel.parking_id)
            
            # NUEVO v4.1.0: Información de ventanas
            supports_multiple = panel.supports_multiple_windows()
            window_config = panel.get_window_config()
            
            # Información de ventanas con últimos mensajes
            windows_info = []
            for window in window_config.get('windows', []):
                window_id = window.get('id', 0)
                windows_info.append({
                    'id': window_id,
                    'enabled': window.get('enabled', True),
                    'last_message': panel.get_last_message_for_window(window_id),
                    'last_update': panel.get_last_update_for_window(window_id).isoformat() if panel.get_last_update_for_window(window_id) else None
                })
            
            panel_data = {
                'id': panel.id,
                'name': panel.name,
                'ip_address': panel.ip,
                'parking_id': panel.parking_id,
                'parking_name': panel.parking.name if panel.parking else None,
                'status': getattr(panel, 'status', 'OFFLINE'),
                'last_message': getattr(panel, 'last_message', None),
                'last_update': getattr(panel, 'last_update', None),
                'panel_type_id': panel.panel_type_id,
                'panel_type': {
                    'id': panel.panel_type.id,
                    'name': panel.panel_type.name,
                    'manufacturer': panel.panel_type.manufacturer.name,
                    'protocol': panel.panel_type.protocol_type,
                    'windows_count': panel.panel_type.windows_count
                } if panel.panel_type else None,
                'active_schedule': None,
                'message_type': 'occupancy',  # Por defecto
                # NUEVO v4.1.0: Información de ventanas
                'supports_multiple_windows': supports_multiple,
                'window_config': window_config,
                'windows': windows_info
            }
            
            # Determinar tipo de mensaje y programación activa
            if active_schedules:
                panel_data['active_schedule'] = {
                    'id': active_schedules[0].id,
                    'name': active_schedules[0].name,
                    'start_time': active_schedules[0].start_time,
                    'end_time': active_schedules[0].end_time,
                    'message': active_schedules[0].message
                }
                panel_data['message_type'] = 'schedule'
            
            if panel_data['last_update']:
                panel_data['last_update'] = panel_data['last_update'].isoformat()
            data.append(panel_data)
        
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo paneles: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels', methods=['POST'])
@require_auth
def create_panel():
    """Crear un nuevo panel"""
    try:
        user_role = request.user_data.get('role', 'user')
        
        # Solo superadmin puede crear paneles
        if user_role != 'superadmin':
            return jsonify({'error': 'Acceso denegado: solo superadmin puede crear paneles'}), 403
        
        req = request.get_json(force=True)
        name = req.get('name')
        ip = req.get('ip')
        parking_id = req.get('parking_id')
        panel_type_id = req.get('panel_type_id')
        port = req.get('port', 5200)  # Puerto por defecto
        
        # Validar campos requeridos
        if not all([name, ip, parking_id, panel_type_id]):
            return jsonify({'error': 'Faltan campos requeridos: name, ip, parking_id, panel_type_id'}), 400
        
        # Validar formato de IP
        import re
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, ip):
            return jsonify({'error': 'Formato de IP inválido'}), 400
        
        # Validar puerto
        if not isinstance(port, int) or port < 1 or port > 65535:
            return jsonify({'error': 'Puerto debe ser un número entre 1 y 65535'}), 400
        
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).filter(Parking.id == parking_id).first()
        if not parking:
            session.close()
            return jsonify({'error': 'Parking no encontrado'}), 404
        
        # Verificar que el panel_type existe
        panel_type = session.query(PanelType).filter(PanelType.id == panel_type_id).first()
        if not panel_type:
            session.close()
            return jsonify({'error': 'Tipo de panel no encontrado'}), 404
        
        # Verificar que no existe otro panel con la misma IP
        existing_panel = session.query(Panel).filter(Panel.ip == ip).first()
        if existing_panel:
            session.close()
            return jsonify({'error': f'Ya existe un panel con la IP {ip}'}), 400
        
        # Verificar que no existe otro panel con el mismo nombre en este parking
        existing_name = session.query(Panel).filter(
            Panel.name == name, 
            Panel.parking_id == parking_id
        ).first()
        if existing_name:
            session.close()
            return jsonify({'error': f'Ya existe un panel con el nombre "{name}" en este parking'}), 400
        
        # Determinar windows_count
        windows_count = req.get('windows_count')
        if windows_count and 1 <= windows_count <= 16:
            final_windows_count = windows_count
        elif panel_type.windows_count:
            final_windows_count = panel_type.windows_count
        else:
            final_windows_count = 1  # Por defecto
        
        # Crear el nuevo panel
        new_panel = Panel(
            name=name,
            ip=ip,
            parking_id=parking_id,
            panel_type_id=panel_type_id,
            port=port,
            status='OFFLINE',  # Estado inicial
            protocol_version=panel_type.protocol_type,
            service_endpoint=panel_type.service_endpoint,
            windows_count=final_windows_count,
            is_active=True
        )
        
        session.add(new_panel)
        session.commit()
        
        # Si es un panel Tipo 3 o Tipo 4, buscar y asociar configuraciones preparatorias de la empresa
        if panel_type.windows_count in [2, 16]:  # Tipo 3 = 2 ventanas, Tipo 4 = 16 ventanas
            try:
                from panel_window_service import PanelWindowService
                window_service = PanelWindowService(session)
                
                # Obtener company_id del parking (a través de UserParking)
                # Buscar el primer usuario que tenga acceso al parking (normalmente será la empresa)
                user_parking = session.query(UserParking).filter(
                    UserParking.parking_id == parking_id
                ).first()
                
                if user_parking:
                    company_id = user_parking.user_id
                    
                    # Buscar configuraciones preparatorias (panel_id = NULL o 0) para esta empresa
                    prep_configs = session.query(PanelWindowConfiguration).filter(
                        and_(
                            PanelWindowConfiguration.parking_id == parking_id,
                            PanelWindowConfiguration.company_id == company_id,
                            or_(
                                PanelWindowConfiguration.panel_id.is_(None),
                                PanelWindowConfiguration.panel_id == 0
                            ),
                            PanelWindowConfiguration.is_active == True
                        )
                    ).all()
                    
                    # Asociar cada configuración preparatoria al panel recién creado
                    for prep_config in prep_configs:
                        prep_config.panel_id = new_panel.id
                        logger.info(f"Configuración preparatoria {prep_config.id} asociada al panel {new_panel.id}")
                    
                    if prep_configs:
                        session.commit()
                        logger.info(f"✅ {len(prep_configs)} configuración(es) preparatoria(s) asociada(s) automáticamente al panel {new_panel.id}")
            except Exception as e:
                logger.warning(f"No se pudieron asociar configuraciones preparatorias: {e}")
                # No fallar la creación del panel si hay error al asociar configuraciones
        
        # Obtener el panel creado con sus relaciones
        created_panel = session.query(Panel).filter(Panel.id == new_panel.id).first()
        
        panel_data = {
            'id': created_panel.id,
            'name': created_panel.name,
            'ip_address': created_panel.ip,
            'parking_id': created_panel.parking_id,
            'parking_name': created_panel.parking.name,
            'panel_type_id': created_panel.panel_type_id,
            'panel_type': {
                'id': created_panel.panel_type.id,
                'name': created_panel.panel_type.name,
                'manufacturer': created_panel.panel_type.manufacturer.name,
                'protocol': created_panel.panel_type.protocol_type,
                'windows_count': created_panel.panel_type.windows_count
            },
            'port': created_panel.port,
            'status': created_panel.status,
            'protocol_version': created_panel.protocol_version,
            'is_active': created_panel.is_active,
            'windows_count': created_panel.windows_count
        }
        
        session.close()
        
        logger.info(f"Panel creado: {name} (ID: {new_panel.id}) en parking {parking.name}")
        
        return jsonify({
            'success': True,
            'message': f'Panel "{name}" creado correctamente',
            'panel': panel_data
        }), 201
        
    except Exception as e:
        logger.error(f"Error creando panel: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>', methods=['PUT'])
@require_auth
def update_panel(panel_id):
    """Actualizar datos completos de un panel"""
    try:
        user_role = request.user_data.get('role', 'user')
        
        # Solo superadmin puede editar paneles
        if user_role != 'superadmin':
            return jsonify({'error': 'Acceso denegado: solo superadmin puede editar paneles'}), 403
        
        req = request.get_json(force=True)
        name = req.get('name')
        ip = req.get('ip')
        parking_id = req.get('parking_id')
        panel_type_id = req.get('panel_type_id')
        port = req.get('port', 5200)
        is_active = req.get('is_active', True)
        
        # Validar campos requeridos
        if not all([name, ip, parking_id, panel_type_id]):
            return jsonify({'error': 'Faltan campos requeridos: name, ip, parking_id, panel_type_id'}), 400
        
        # Validar formato de IP
        import re
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, ip):
            return jsonify({'error': 'Formato de IP inválido'}), 400
        
        # Validar puerto
        if not isinstance(port, int) or port < 1 or port > 65535:
            return jsonify({'error': 'Puerto debe ser un número entre 1 y 65535'}), 400
        
        session = Session()
        
        # Verificar que el panel existe
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        # Verificar que el parking existe
        parking = session.query(Parking).filter(Parking.id == parking_id).first()
        if not parking:
            session.close()
            return jsonify({'error': 'Parking no encontrado'}), 404
        
        # Verificar que el panel_type existe
        panel_type = session.query(PanelType).filter(PanelType.id == panel_type_id).first()
        if not panel_type:
            session.close()
            return jsonify({'error': 'Tipo de panel no encontrado'}), 404
        
        # Verificar que no existe otro panel con la misma IP (excluyendo el actual)
        existing_panel = session.query(Panel).filter(
            Panel.ip == ip, 
            Panel.id != panel_id
        ).first()
        if existing_panel:
            session.close()
            return jsonify({'error': f'Ya existe otro panel con la IP {ip}'}), 400
        
        # Verificar que no existe otro panel con el mismo nombre en este parking (excluyendo el actual)
        existing_name = session.query(Panel).filter(
            Panel.name == name, 
            Panel.parking_id == parking_id,
            Panel.id != panel_id
        ).first()
        if existing_name:
            session.close()
            return jsonify({'error': f'Ya existe otro panel con el nombre "{name}" en este parking'}), 400
        
        # Actualizar los datos del panel
        old_name = panel.name
        old_ip = panel.ip
        old_panel_type_id = panel.panel_type_id  # Guardar tipo anterior
        old_parking_id = panel.parking_id  # Guardar parking_id anterior para actualizar configuraciones
        
        panel.name = name
        panel.ip = ip
        panel.parking_id = parking_id
        panel.panel_type_id = panel_type_id
        panel.port = port
        panel.is_active = is_active
        panel.protocol_version = panel_type.protocol_type
        panel.service_endpoint = panel_type.service_endpoint
        
        # Actualizar windows_count
        # Si se proporciona explícitamente, usarlo (validado)
        if 'windows_count' in req:
            windows_count = req.get('windows_count')
            if windows_count and 1 <= windows_count <= 16:
                panel.windows_count = windows_count
            elif panel_type.windows_count:
                panel.windows_count = panel_type.windows_count
        # Si no se proporciona pero cambió el tipo de panel, actualizar según el nuevo tipo
        elif old_panel_type_id != panel_type_id or not panel.windows_count:
            if panel_type.windows_count:
                panel.windows_count = panel_type.windows_count
            else:
                panel.windows_count = 1  # Por defecto
        
        session.commit()
        
        # Si es Tipo 3 o Tipo 4, actualizar configuraciones de ventanas
        if panel_type.windows_count in [2, 16]:
            try:
                from panel_window_service import PanelWindowService
                window_service = PanelWindowService(session)
                
                # Obtener company_id del nuevo parking (a través de UserParking)
                user_parking = session.query(UserParking).filter(
                    UserParking.parking_id == parking_id
                ).first()
                
                if user_parking:
                    company_id = user_parking.user_id
                    
                    # Si cambió el parking_id, actualizar las configuraciones existentes
                    if old_parking_id != parking_id:
                        # Actualizar parking_id en configuraciones existentes del panel
                        existing_configs = session.query(PanelWindowConfiguration).filter(
                            and_(
                                PanelWindowConfiguration.panel_id == panel_id,
                                PanelWindowConfiguration.is_active == True
                            )
                        ).all()
                        
                        for config in existing_configs:
                            config.parking_id = parking_id
                            config.company_id = company_id
                            logger.info(f"Configuración {config.id} actualizada: parking_id {old_parking_id} -> {parking_id}")
                        
                        # Actualizar parking_id en asignaciones existentes del panel
                        existing_assignments = session.query(ParkingPanelWindow).filter(
                            and_(
                                ParkingPanelWindow.panel_id == panel_id,
                                ParkingPanelWindow.is_active == True
                            )
                        ).all()
                        
                        for assignment in existing_assignments:
                            assignment.parking_id = parking_id
                            logger.info(f"Asignación {assignment.id} actualizada: parking_id {old_parking_id} -> {parking_id}")
                        
                        if existing_configs or existing_assignments:
                            session.commit()
                            logger.info(f"✅ {len(existing_configs)} configuración(es) y {len(existing_assignments)} asignación(es) actualizada(s) al cambiar parking_id")
                    
                    # Si cambió a Tipo 3 o Tipo 4 (o ya lo era), buscar y asociar configuraciones preparatorias
                    if old_panel_type_id != panel_type_id:
                        # Buscar configuraciones preparatorias (panel_id = NULL o 0) para esta empresa
                        prep_configs = session.query(PanelWindowConfiguration).filter(
                            and_(
                                PanelWindowConfiguration.parking_id == parking_id,
                                PanelWindowConfiguration.company_id == company_id,
                                or_(
                                    PanelWindowConfiguration.panel_id.is_(None),
                                    PanelWindowConfiguration.panel_id == 0
                                ),
                                PanelWindowConfiguration.is_active == True
                            )
                        ).all()
                        
                        # Asociar cada configuración preparatoria al panel
                        for prep_config in prep_configs:
                            prep_config.panel_id = panel_id
                            logger.info(f"Configuración preparatoria {prep_config.id} asociada al panel {panel_id}")
                        
                        if prep_configs:
                            session.commit()
                            logger.info(f"✅ {len(prep_configs)} configuración(es) preparatoria(s) asociada(s) automáticamente al panel {panel_id}")
            except Exception as e:
                logger.warning(f"No se pudieron actualizar configuraciones de ventanas: {e}")
                # No fallar la actualización del panel si hay error al actualizar configuraciones
        
        # Obtener el panel actualizado con sus relaciones
        updated_panel = session.query(Panel).filter(Panel.id == panel_id).first()
        
        panel_data = {
            'id': updated_panel.id,
            'name': updated_panel.name,
            'ip_address': updated_panel.ip,
            'parking_id': updated_panel.parking_id,
            'parking_name': updated_panel.parking.name,
            'panel_type_id': updated_panel.panel_type_id,
            'panel_type': {
                'id': updated_panel.panel_type.id,
                'name': updated_panel.panel_type.name,
                'manufacturer': updated_panel.panel_type.manufacturer.name,
                'protocol': updated_panel.panel_type.protocol_type,
                'windows_count': updated_panel.panel_type.windows_count
            },
            'port': updated_panel.port,
            'status': updated_panel.status,
            'protocol_version': updated_panel.protocol_version,
            'is_active': updated_panel.is_active,
            'windows_count': updated_panel.windows_count,
            'last_update': updated_panel.last_update.isoformat() if updated_panel.last_update else None
        }
        
        session.close()
        
        logger.info(f"Panel actualizado: {old_name} -> {name}, IP: {old_ip} -> {ip} (ID: {panel_id})")
        
        return jsonify({
            'success': True,
            'message': f'Panel "{name}" actualizado correctamente',
            'panel': panel_data
        })
        
    except Exception as e:
        logger.error(f"Error actualizando panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>', methods=['DELETE'])
@require_auth
def delete_panel(panel_id):
    """Eliminar un panel"""
    try:
        user_role = request.user_data.get('role', 'user')
        
        # Solo superadmin puede eliminar paneles
        if user_role != 'superadmin':
            return jsonify({'error': 'Acceso denegado: solo superadmin puede eliminar paneles'}), 403
        
        session = Session()
        
        # Verificar que el panel existe
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        panel_name = panel.name
        panel_ip = panel.ip
        parking_name = panel.parking.name if panel.parking else "Unknown"
        
        # Eliminar asignaciones de usuarios a este panel
        session.query(UserPanel).filter(UserPanel.panel_id == panel_id).delete()
        
        # Eliminar el panel
        session.delete(panel)
        session.commit()
        session.close()
        
        logger.info(f"Panel eliminado: {panel_name} (IP: {panel_ip}, ID: {panel_id}) del parking {parking_name}")
        
        return jsonify({
            'success': True,
            'message': f'Panel "{panel_name}" eliminado correctamente',
            'panel_id': panel_id
        })
        
    except Exception as e:
        logger.error(f"Error eliminando panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panel/<int:panel_id>/message', methods=['POST'])
@require_panel_access('panel_id')
def send_message_to_panel(panel_id):
    """Enviar mensaje a un panel específico por ID"""
    try:
        req = request.get_json(force=True)
        message = req.get('message')
        duration = req.get('duration', 30)
        color = req.get('color', 1)
        fontSize = req.get('fontSize', 2)  # Recibir código de fuente directamente
        showEffect = req.get('showEffect', "fijo")  # Fijo por defecto - CORREGIDO
        window = req.get('window', 0)  # NUEVO v4.1.0: Ventana de destino (0 o 1)
        
        if not message:
            return jsonify({'error': 'Missing message field'}), 400
        
        # VALIDACIONES v4.1.0
        if window not in [0, 1]:
            return jsonify({'error': 'Window must be 0 or 1'}), 400
        
        # Validar longitud del mensaje
        if len(message) > 200:
            return jsonify({'error': 'Message too long. Maximum 200 characters allowed.'}), 400
        
        # Validar parámetros de color y fuente
        if color not in range(1, 8):  # Colores válidos 1-7
            return jsonify({'error': 'Color must be between 1 and 7'}), 400
        
        if fontSize not in range(0, 5):  # Tamaños válidos 0-4
            return jsonify({'error': 'Font size must be between 0 and 4'}), 400
        
        # No convertir fontSize ya que viene como código
        font_size_code = fontSize
        
        # Convertir efecto string a código numérico
        effect_codes = {
            'fijo': 2,
            'scroll': 12,
            'static': 2,
            'center': 2
        }
        effect_code = effect_codes.get(showEffect, 2)  # Fijo por defecto
        
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # NUEVO v4.1.0: Validar ventana para paneles Tipo 3
        if window == 1 and not panel.supports_multiple_windows():
            session.close()
            return jsonify({'error': 'Panel does not support window 1. Only Tipo 3 panels support multiple windows.'}), 400
        
        # Guardar información del panel antes de cerrar la sesión
        panel_name = panel.name
        panel_ip = panel.ip
        panel_supports_windows = panel.supports_multiple_windows()
        
        # Usar el PanelCommunicationService
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        start_time = datetime.now()
        
        # NUEVO v4.1.0: Enviar mensaje con ventana específica
        if panel_supports_windows and window == 1:
            # Para paneles Tipo 3, enviar a ventana específica
            result = panel_service.send_custom_text_to_window(
                panel_ip=panel_ip,
                text=message,
                color=color,
                font_size=font_size_code,
                effect=effect_code,
                window_id=window
            )
        else:
            # Comportamiento original para ventana 0 o paneles sin múltiples ventanas
            result = panel_service.send_custom_text(
                panel_ip=panel_ip,
                text=message,
                color=color,
                font_size=font_size_code,
                effect=effect_code
            )
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000  # en ms
        
        # NUEVO v4.1.0: Actualizar estado del panel por ventana
        panel.status = 'ONLINE' if result['success'] else 'OFFLINE'
        current_time = datetime.now()
        
        # Actualizar campos específicos de la ventana
        if result['success']:
            if window == 0:
                panel.last_message_window_0 = message
                panel.last_update_window_0 = current_time
                # Mantener compatibilidad con campo original
                panel.last_message = message
            elif window == 1:
                panel.last_message_window_1 = message
                panel.last_update_window_1 = current_time
        
        panel.last_update = current_time
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'panel_id': panel_id,
            'panel_name': panel_name,
            'panel_ip': panel_ip,
            'text_message': message,  # Renombrado para evitar conflicto
            'window': window,  # NUEVO v4.1.0: Ventana utilizada
            'supports_multiple_windows': panel_supports_windows,  # NUEVO v4.1.0: Capacidad del panel
            'duration': duration,
            'responseTime': response_time
        })
        
    except Exception as e:
        logger.error(f"Error enviando mensaje al panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panel/<int:panel_id>/test', methods=['POST'])
def test_panel(panel_id):
    """Probar comunicación con un panel"""
    try:
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Guardar información del panel antes de cerrar la sesión
        panel_name = panel.name
        panel_ip = panel.ip
        
        # Usar el PanelCommunicationService
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        start_time = datetime.now()
        result = panel_service.send_custom_text(
            panel_ip=panel_ip,
            text='PRUEBA',
            color=2,  # Verde para prueba
            font_size=2,  # Tamaño 16 píxeles (código 2) - CORREGIDO
            effect=2  # Fijo por defecto (valor correcto)
        )
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Actualizar estado del panel (usar el objeto dentro de la sesión)
        panel.status = 'ONLINE' if result['success'] else 'OFFLINE'
        panel.last_update = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'panel_id': panel_id,
            'panel_name': panel_name,
            'panel_ip': panel_ip,
            'responseTime': response_time
        })
        
    except Exception as e:
        logger.error(f"Error probando panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panel/<int:panel_id>/type', methods=['PUT'])
@require_auth
def update_panel_type(panel_id):
    """Actualizar el tipo de panel y sincronizar el protocolo"""
    try:
        req = request.get_json(force=True)
        panel_type_id = req.get('panel_type_id')
        
        if panel_type_id is None:
            return jsonify({'error': 'Missing panel_type_id field'}), 400
        
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Verificar que el tipo de panel existe
        panel_type = session.query(PanelType).get(panel_type_id)
        if not panel_type:
            session.close()
            return jsonify({'error': 'Panel type not found'}), 404
        
        # Actualizar el tipo de panel y el protocolo
        panel.panel_type_id = panel_type_id
        panel.protocol_version = panel_type.protocol_type  # Sincronizar protocolo
        session.commit()
        
        # Obtener datos actualizados para la respuesta
        updated_panel = session.query(Panel).get(panel_id)
        panel_data = {
            'id': updated_panel.id,
            'name': updated_panel.name,
            'panel_type_id': updated_panel.panel_type_id,
            'protocol_version': updated_panel.protocol_version,
            'panel_type': {
                'id': updated_panel.panel_type.id,
                'name': updated_panel.panel_type.name,
                'manufacturer': updated_panel.panel_type.manufacturer.name,
                'protocol': updated_panel.panel_type.protocol_type
            } if updated_panel.panel_type else None
        }
        
        session.close()
        return jsonify(panel_data)
        
    except Exception as e:
        logger.error(f"Error actualizando tipo de panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>/type', methods=['PUT'])
@require_auth
def update_panel_type_plural(panel_id):
    """Actualizar el tipo de panel (ruta plural para compatibilidad con frontend)"""
    return update_panel_type(panel_id)

@api_bp.route('/panels/<int:panel_id>/message', methods=['POST'])
@require_panel_access('panel_id')
def send_message_to_panel_plural(panel_id):
    """Enviar mensaje a un panel específico por ID (ruta plural para compatibilidad con frontend)"""
    return send_message_to_panel(panel_id)

@api_bp.route('/panels/<int:panel_id>/test', methods=['POST'])
def test_panel_plural(panel_id):
    """Probar comunicación con un panel (ruta plural para compatibilidad con frontend)"""
    return test_panel(panel_id)

@api_bp.route('/panels/<int:panel_id>/windows', methods=['GET'])
@require_panel_access('panel_id')
def get_panel_windows_info(panel_id):
    """NUEVO v4.1.0: Obtener información de ventanas de un panel"""
    try:
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Obtener configuración de ventanas
        window_config = panel.get_window_config()
        supports_multiple = panel.supports_multiple_windows()
        
        # Obtener información de cada ventana
        windows_info = []
        for window in window_config.get('windows', []):
            window_id = window.get('id', 0)
            windows_info.append({
                'id': window_id,
                'enabled': window.get('enabled', True),
                'last_message': panel.get_last_message_for_window(window_id),
                'last_update': panel.get_last_update_for_window(window_id).isoformat() if panel.get_last_update_for_window(window_id) else None
            })
        
        session.close()
        
        return jsonify({
            'panel_id': panel_id,
            'panel_name': panel.name,
            'supports_multiple_windows': supports_multiple,
            'panel_type': {
                'id': panel.panel_type.id,
                'name': panel.panel_type.name,
                'windows_count': panel.panel_type.windows_count
            } if panel.panel_type else None,
            'window_config': window_config,
            'windows': windows_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo información de ventanas del panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>/validate', methods=['POST'])
@require_panel_access('panel_id')
def validate_panel_message(panel_id):
    """NUEVO v4.1.0: Validar mensaje antes de envío (sin enviar realmente)"""
    try:
        req = request.get_json(force=True)
        message = req.get('message', '')
        window = req.get('window', 0)
        color = req.get('color', 1)
        fontSize = req.get('fontSize', 2)
        
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Recopilar validaciones
        validations = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'panel_info': {
                'id': panel_id,
                'name': panel.name,
                'supports_multiple_windows': panel.supports_multiple_windows(),
                'panel_type': panel.panel_type.name if panel.panel_type else 'Unknown'
            }
        }
        
        # Validar mensaje
        if not message:
            validations['errors'].append('Message is required')
            validations['valid'] = False
        elif len(message) > 200:
            validations['errors'].append('Message too long (max 200 characters)')
            validations['valid'] = False
        
        # Validar ventana
        if window not in [0, 1]:
            validations['errors'].append('Window must be 0 or 1')
            validations['valid'] = False
        elif window == 1 and not panel.supports_multiple_windows():
            validations['errors'].append('Panel does not support window 1 (only Tipo 3 panels)')
            validations['valid'] = False
        
        # Validar parámetros
        if color not in range(1, 8):
            validations['errors'].append('Color must be between 1 and 7')
            validations['valid'] = False
        
        if fontSize not in range(0, 5):
            validations['errors'].append('Font size must be between 0 and 4')
            validations['valid'] = False
        
        # Añadir advertencias
        if len(message) > 100:
            validations['warnings'].append('Long message may not display properly on some panels')
        
        if panel.status == 'OFFLINE':
            validations['warnings'].append('Panel is currently offline')
        
        session.close()
        
        return jsonify(validations)
        
    except Exception as e:
        logger.error(f"Error validando mensaje para panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>/multi-message', methods=['POST'])
@require_panel_access('panel_id')
def send_multi_message_to_panel(panel_id):
    """Enviar múltiples mensajes a un panel específico por ID"""
    try:
        req = request.get_json(force=True)
        messages = req.get('messages', [])
        
        if not messages or not isinstance(messages, list):
            return jsonify({'error': 'Messages field must be a non-empty array'}), 400
        
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        # Guardar información del panel antes de cerrar la sesión
        panel_name = panel.name
        panel_ip = panel.ip
        
        # Usar el PanelCommunicationService
        from panel_communication_service import get_panel_service
        panel_service = get_panel_service()
        
        start_time = datetime.now()
        
        # Enviar cada mensaje
        results = []
        for i, message_data in enumerate(messages):
            try:
                result = panel_service.send_custom_text(
                    panel_ip=panel_ip,
                    text=message_data.get('text', ''),
                    color=message_data.get('color', 1),
                    font_size=message_data.get('fontSize', 2),
                    effect=message_data.get('showEffect', 'fijo')
                )
                results.append({
                    'window_id': i,
                    'success': result.get('success', False),
                    'message': result.get('message', '')
                })
            except Exception as e:
                results.append({
                    'window_id': i,
                    'success': False,
                    'message': str(e)
                })
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Actualizar estado del panel
        panel.status = 'ONLINE' if any(r['success'] for r in results) else 'OFFLINE'
        panel.last_update = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': any(r['success'] for r in results),
            'message': 'Mensajes enviados',
            'panel_id': panel_id,
            'panel_name': panel_name,
            'panel_ip': panel_ip,
            'results': results,
            'responseTime': response_time
        })
        
    except Exception as e:
        logger.error(f"Error sending multi-message to panel {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>/status', methods=['GET'])
def get_panel_status(panel_id):
    """Obtener estado de un panel específico por ID"""
    try:
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        panel_data = {
            'id': panel.id,
            'name': panel.name,
            'ip': panel.ip,
            'status': panel.status,
            'last_message': panel.last_message,
            'last_update': panel.last_update.isoformat() if panel.last_update else None
        }
        
        session.close()
        return jsonify(panel_data)
        
    except Exception as e:
        logger.error(f"Error getting panel status {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panels/<int:panel_id>/protocol-info', methods=['GET'])
def get_panel_protocol_info(panel_id):
    """Obtener información del protocolo de un panel específico por ID"""
    try:
        session = Session()
        panel = session.query(Panel).get(panel_id)
        
        if not panel:
            session.close()
            return jsonify({'error': 'Panel not found'}), 404
        
        protocol_info = {
            'panel_id': panel.id,
            'panel_name': panel.name,
            'panel_ip': panel.ip,
            'protocol_version': panel.protocol_version or 'old',
            'panel_type': {
                'id': panel.panel_type.id,
                'name': panel.panel_type.name,
                'manufacturer': panel.panel_type.manufacturer.name,
                'protocol': panel.panel_type.protocol_type
            } if panel.panel_type else None
        }
        
        session.close()
        return jsonify(protocol_info)
        
    except Exception as e:
        logger.error(f"Error getting panel protocol info {panel_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/panel-types', methods=['GET'])
def get_all_panel_types():
    """Obtener todos los tipos de panel"""
    try:
        session = Session()
        
        panel_types = session.query(PanelType).filter(PanelType.is_active == True).all()
        data = []
        
        for panel_type in panel_types:
            panel_type_data = {
                'id': panel_type.id,
                'name': panel_type.name,
                'manufacturer': panel_type.manufacturer.name,
                'protocol': panel_type.protocol_type,
                'description': panel_type.description,
                'is_active': panel_type.is_active
            }
            data.append(panel_type_data)
        
        session.close()
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error obteniendo tipos de panel: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/statistics', methods=['GET'])
@require_parking_access('pid')
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

@api_bp.route('/statistics', methods=['GET'])
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

@api_bp.route('/parkings/<int:pid>/history', methods=['GET'])
@require_parking_access('pid')
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

@api_bp.route('/logs/activity', methods=['GET'])
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

@api_bp.route('/logs/panels', methods=['GET'])
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

@api_bp.route('/camera/logs', methods=['GET'])
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

@api_bp.route('/camera-logs-v2', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_camera_logs_v2():
    """
    Endpoint avanzado para logs de cámaras con filtros completos
    
    Parámetros:
    - parking_id: ID del parking
    - access_id: ID del acceso 
    - camera_ip: IP específica de la cámara
    - camera_name: Nombre de la cámara (búsqueda parcial)
    - status: processed|discarded|error
    - date_from: YYYY-MM-DD (fecha desde)
    - date_to: YYYY-MM-DD (fecha hasta)
    - time_from: HH:MM (hora desde)
    - time_to: HH:MM (hora hasta)
    - has_changes: true/false (solo logs con cambios de ocupación)
    - error_only: true/false (solo logs con errores)
    - order_by: received_at|processed_at|processing_time
    - order_direction: asc|desc
    - page: número de página (desde 1)
    - per_page: elementos por página (máx 500)
    """
    try:
        logger.info("=== INICIO camera-logs-v2 ===")
        logger.info(f"Parámetros recibidos: {dict(request.args)}")
        
        from datetime import datetime, time
        
        # Parámetros de filtrado
        parking_id = request.args.get('parking_id', type=int)
        access_id = request.args.get('access_id', type=int)
        camera_ip = request.args.get('camera_ip')
        camera_name = request.args.get('camera_name')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        time_from = request.args.get('time_from')
        time_to = request.args.get('time_to')
        has_changes = request.args.get('has_changes', type=bool)
        error_only = request.args.get('error_only', type=bool)
        
        # Parámetros de ordenación
        order_by = request.args.get('order_by', 'received_at')
        order_direction = request.args.get('order_direction', 'desc')
        
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 500)
        
        session = Session()
        
        # Construir query base con filtrado por permisos
        query = session.query(CameraLog)
        
        # FILTRAR POR PERMISOS: Solo logs de parkings y accesos permitidos
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        accessible_access_ids = getattr(request, 'accessible_access_ids', [])
        
        logger.info(f"Permisos obtenidos - Parkings: {len(accessible_parking_ids)}, Accesos: {len(accessible_access_ids)}")
        logger.info(f"Usuario: {getattr(request, 'user_data', {}).get('email', 'N/A')}")
        
        if accessible_parking_ids or accessible_access_ids:
            # Filtrar por parkings O accesos accesibles
            filters = []
            
            if accessible_parking_ids:
                filters.append(CameraLog.parking_id.in_(accessible_parking_ids))
            
            if accessible_access_ids:
                filters.append(CameraLog.access_id.in_(accessible_access_ids))
            
            if filters:
                # Combinar filtros con OR
                from sqlalchemy import or_
                query = query.filter(or_(*filters))
            else:
                # Usuario no tiene acceso a ningún recurso, devolver lista vacía
                session.close()
                return jsonify({
                    'logs': [],
                    'pagination': {'current_page': 1, 'per_page': per_page, 'total_pages': 0, 'total_count': 0},
                    'filters_applied': {},
                    'stats': {'processed_count': 0, 'error_count': 0, 'discarded_count': 0, 'total_changes': 0}
                })
        
        # Aplicar filtros adicionales
        filters_applied = {}
        
        if parking_id:
            query = query.filter(CameraLog.parking_id == parking_id)
            filters_applied['parking_id'] = parking_id
            
        if access_id:
            query = query.filter(CameraLog.access_id == access_id)
            filters_applied['access_id'] = access_id
            
        if camera_ip:
            query = query.filter(CameraLog.camera_ip == camera_ip)
            filters_applied['camera_ip'] = camera_ip
            
        if camera_name:
            query = query.filter(CameraLog.camera_name.ilike(f'%{camera_name}%'))
            filters_applied['camera_name'] = camera_name
            
        if status:
            query = query.filter(CameraLog.status == status)
            filters_applied['status'] = status
            
        if error_only:
            query = query.filter(CameraLog.status == 'error')
            filters_applied['error_only'] = True
            
        if has_changes:
            query = query.filter(CameraLog.occupancy_change != 0)
            filters_applied['has_changes'] = True
        
        # Filtros de fecha y hora
        if date_from:
            try:
                date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
                if time_from:
                    time_from_parsed = datetime.strptime(time_from, '%H:%M').time()
                    datetime_from = datetime.combine(date_from_parsed, time_from_parsed)
                else:
                    datetime_from = datetime.combine(date_from_parsed, time.min)
                
                query = query.filter(CameraLog.received_at >= datetime_from)
                filters_applied['date_from'] = date_from
                if time_from:
                    filters_applied['time_from'] = time_from
                    
            except ValueError:
                return jsonify({'error': 'Formato de fecha_from inválido. Usar YYYY-MM-DD'}), 400
        
        if date_to:
            try:
                date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
                if time_to:
                    time_to_parsed = datetime.strptime(time_to, '%H:%M').time()
                    datetime_to = datetime.combine(date_to_parsed, time_to_parsed)
                else:
                    datetime_to = datetime.combine(date_to_parsed, time.max)
                
                query = query.filter(CameraLog.received_at <= datetime_to)
                filters_applied['date_to'] = date_to
                if time_to:
                    filters_applied['time_to'] = time_to
                    
            except ValueError:
                return jsonify({'error': 'Formato de date_to inválido. Usar YYYY-MM-DD'}), 400
        
        # Aplicar ordenación
        if order_by == 'received_at':
            order_field = CameraLog.received_at
        elif order_by == 'processed_at':
            order_field = CameraLog.processed_at
        elif order_by == 'processing_time':
            order_field = CameraLog.processing_time
        else:
            order_field = CameraLog.received_at
            
        if order_direction == 'asc':
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
        
        # Calcular estadísticas antes de paginar
        logger.info("Calculando total_count")
        total_count = query.count()
        logger.info(f"Total count obtenido: {total_count}")
        
        stats_query = query
        processed_count = stats_query.filter(CameraLog.status == 'processed').count()
        error_count = stats_query.filter(CameraLog.status == 'error').count()
        discarded_count = stats_query.filter(CameraLog.status == 'discarded').count()
        changes_count = stats_query.filter(CameraLog.occupancy_change != 0).count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()
        
        # Calcular información de paginación
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
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
                'access_id': log.access_id,
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
        
        # Respuesta estructurada
        response = {
            'logs': data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_count': total_count,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1 if has_next else None,
                'prev_page': page - 1 if has_prev else None
            },
            'filters_applied': filters_applied,
            'stats': {
                'processed_count': processed_count,
                'error_count': error_count,
                'discarded_count': discarded_count,
                'total_changes': changes_count
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        logger.error(f"Error obteniendo logs de cámaras v2: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        logger.error(f"Argumentos del error: {e.args}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@api_bp.route('/camera/logs/stats', methods=['GET'])
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

@api_bp.route('/parkings/<int:pid>/cameras', methods=['GET'])
def get_parking_cameras(pid):
    """Obtener cámaras de un parking específico usando la nueva relación muchos a muchos"""
    try:
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(pid)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        # Obtener cámaras del parking usando la nueva relación muchos a muchos
        camera_parkings = session.query(CameraParking).filter_by(parking_id=pid).all()
        
        data = []
        for cp in camera_parkings:
            camera = cp.camera
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

@api_bp.route('/access/<int:access_id>/line', methods=['PUT'])
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
        
        # Obtener los parkings asociados a esta cámara
        camera_parkings = session.query(CameraParking).filter(CameraParking.camera_id == access_id).all()
        parking_ids = [cp.parking_id for cp in camera_parkings]
        
        # Verificar que no haya conflicto con otra cámara de los mismos parkings
        for parking_id in parking_ids:
            existing_camera = session.query(Access).join(CameraParking).filter(
                CameraParking.parking_id == parking_id,
                Access.line == new_line,
                Access.id != access_id
            ).first()
            
            if existing_camera:
                session.close()
                return jsonify({'error': f'Line {new_line} is already used by camera {existing_camera.name} in parking {parking_id}'}), 400
        
        # Guardar línea anterior para logging
        old_line = access.line
        camera_name = access.name
        
        # Obtener nombres de parkings para logging
        parking_names = []
        for cp in camera_parkings:
            parking = session.query(Parking).get(cp.parking_id)
            if parking:
                parking_names.append(parking.name)
        parking_name = ", ".join(parking_names) if parking_names else "Unknown"
        
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

@api_bp.route('/cameras/status', methods=['GET'])
def get_all_cameras_status():
    """Obtener estado de todas las cámaras usando la nueva relación muchos a muchos"""
    try:
        session = Session()
        
        # Obtener todas las cámaras con información de sus parkings asociados
        camera_parkings = session.query(CameraParking).join(Access).join(Parking).all()
        
        data = []
        for cp in camera_parkings:
            camera = cp.camera
            parking = cp.parking
            camera_data = {
                'id': camera.id,
                'name': camera.name,
                'ip': camera.ip,
                'line': camera.line,
                'status': getattr(camera, 'status', 'OFFLINE'),
                'last_message_received': camera.last_message_received.isoformat() if camera.last_message_received else None,
                'last_ping_check': camera.last_ping_check.isoformat() if camera.last_ping_check else None,
                'ping_status': getattr(camera, 'ping_status', 'UNKNOWN'),
                'parking_id': parking.id,
                'parking_name': parking.name,
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

@api_bp.route('/parkings/<int:pid>/hourly-statistics', methods=['GET'])
@require_auth
@require_parking_access('pid')
def get_parking_hourly_statistics(pid):
    """Obtener estadísticas por horas de un parking"""
    try:
        logger.info(f"=== INICIO hourly-statistics para parking {pid} ===")
        logger.info(f"Parámetros: date={request.args.get('date')}, days={request.args.get('days', 7)}")
        
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
        
        # Si se especifica una fecha, usar solo ese día; si no, usar el rango completo
        if date:
            # Para una fecha específica, calcular por horas de ese día
            date_range = [start_date.date()]
        else:
            # Para múltiples días, promediar por hora a través de todos los días
            date_range = [(start_date + timedelta(days=i)).date() for i in range(days)]
        
        logger.info(f"Calculando estadísticas para {len(date_range)} días: {date_range}")
        
        # Debug: Verificar si hay datos de CameraLog para este parking
        total_logs_parking = session.query(CameraLog).filter(CameraLog.parking_id == pid).count()
        processed_logs_parking = session.query(CameraLog).filter(
            CameraLog.parking_id == pid,
            CameraLog.status == 'processed'
        ).count()
        recent_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == pid,
            CameraLog.received_at >= start_date,
            CameraLog.received_at < end_date
        ).count()
        
        logger.info(f"DEBUG - Parking {pid}: {total_logs_parking} logs totales, {processed_logs_parking} procesados, {recent_logs} en rango de fechas")
        
        # Debug: Mostrar algunos logs recientes
        sample_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == pid,
            CameraLog.status == 'processed'
        ).order_by(CameraLog.received_at.desc()).limit(5).all()
        
        for log in sample_logs:
            logger.info(f"  Sample log: ID={log.id}, fecha={log.received_at}, delta_in={log.delta_in}, delta_out={log.delta_out}")
        
        for hour in range(24):
            total_vehicles_in_hour = 0
            total_vehicles_out_hour = 0
            total_messages_hour = 0
            occupancy_values = []
            
            # Procesar cada día en el rango
            for current_date in date_range:
                hour_start = datetime.combine(current_date, datetime.min.time()).replace(hour=hour)
                hour_end = hour_start + timedelta(hours=1)
                
                # Obtener logs de cámaras para esta hora específica
                camera_logs = session.query(CameraLog).filter(
                    CameraLog.parking_id == pid,
                    CameraLog.received_at >= hour_start,
                    CameraLog.received_at < hour_end,
                    CameraLog.status == 'processed'
                ).all()
                
                # Debug: Log detalles de esta hora si hay datos
                if camera_logs:
                    logger.info(f"Hora {hour:02d}:00 - {len(camera_logs)} logs encontrados")
                    for log in camera_logs[:3]:  # Solo los primeros 3 para no saturar
                        logger.info(f"  Log ID {log.id}: delta_in={log.delta_in}, delta_out={log.delta_out}")
                
                # Sumar métricas del día
                hour_vehicles_in = sum(log.delta_in or 0 for log in camera_logs)
                hour_vehicles_out = sum(log.delta_out or 0 for log in camera_logs)
                hour_messages = len(camera_logs)
                
                total_vehicles_in_hour += hour_vehicles_in
                total_vehicles_out_hour += hour_vehicles_out
                total_messages_hour += hour_messages
                
                # Debug adicional - mostrar siempre para las primeras horas
                if hour < 3 or hour_vehicles_in > 0 or hour_vehicles_out > 0:
                    logger.info(f"Hora {hour:02d}:00 del {current_date} - Entradas: {hour_vehicles_in}, Salidas: {hour_vehicles_out}, Mensajes: {hour_messages}")
                    if hour_messages > 0:
                        logger.info(f"  Rango: {hour_start} a {hour_end}")
                        logger.info(f"  Query: parking_id={pid}, status='processed'")
                
                # Obtener ocupación de esta hora
                occupancy_data = session.query(OccupancyHistory).filter(
                    OccupancyHistory.parking_id == pid,
                    OccupancyHistory.timestamp >= hour_start,
                    OccupancyHistory.timestamp < hour_end
                ).all()
                
                if occupancy_data:
                    hour_occupancies = [data.occupancy for data in occupancy_data]
                    if hour_occupancies:
                        occupancy_values.extend(hour_occupancies)
            
            # Calcular métricas finales para esta hora
            avg_occupancy = 0
            max_occupancy = 0
            min_occupancy = 0
            
            if occupancy_values:
                avg_occupancy = sum(occupancy_values) / len(occupancy_values)
                max_occupancy = max(occupancy_values)
                min_occupancy = min(occupancy_values)
            
            # Promediar por número de días si es necesario
            if not date and len(date_range) > 1:
                avg_vehicles_in = total_vehicles_in_hour / len(date_range)
                avg_vehicles_out = total_vehicles_out_hour / len(date_range)
                avg_messages = total_messages_hour / len(date_range)
            else:
                avg_vehicles_in = total_vehicles_in_hour
                avg_vehicles_out = total_vehicles_out_hour
                avg_messages = total_messages_hour
            
            hourly_stats.append({
                'hour': hour,
                'hour_label': f'{hour:02d}:00',
                'total_vehicles_in': round(avg_vehicles_in, 1),
                'total_vehicles_out': round(avg_vehicles_out, 1),
                'net_change': round(avg_vehicles_in - avg_vehicles_out, 1),
                'message_count': round(avg_messages, 1),
                'avg_occupancy': round(avg_occupancy, 1),
                'max_occupancy': max_occupancy,
                'min_occupancy': min_occupancy,
                'occupancy_percentage': round(avg_occupancy, 1),  # Para la visualización
                'traffic_intensity': round(avg_vehicles_in + avg_vehicles_out, 1)  # Para el tab de tráfico
            })
        
        # Obtener estadísticas de cámaras para el período
        camera_stats = []
        # Usar la nueva relación muchos a muchos para obtener cámaras del parking
        camera_parkings = session.query(CameraParking).filter(CameraParking.parking_id == pid).all()
        
        logger.info(f"Encontradas {len(camera_parkings)} relaciones cámara-parking para parking {pid}")
        
        for cp in camera_parkings:
            camera = cp.camera
            # Corregir la consulta: usar camera_ip en lugar de access_id
            camera_logs = session.query(CameraLog).filter(
                CameraLog.camera_ip == camera.ip,
                CameraLog.received_at >= start_date,
                CameraLog.received_at < end_date
            ).all()
            
            logger.info(f"Cámara {camera.name} ({camera.ip}): {len(camera_logs)} logs encontrados")
            
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
        
        # Debug final: Resumen de estadísticas generadas
        hours_with_traffic = [h for h in hourly_stats if h['total_vehicles_in'] > 0 or h['total_vehicles_out'] > 0]
        total_traffic_in = sum(h['total_vehicles_in'] for h in hourly_stats)
        total_traffic_out = sum(h['total_vehicles_out'] for h in hourly_stats)
        total_messages = sum(h['message_count'] for h in hourly_stats)
        
        logger.info(f"=== RESUMEN ESTADÍSTICAS PARKING {pid} ===")
        logger.info(f"Horas con tráfico: {len(hours_with_traffic)}/24")
        logger.info(f"Total entradas: {total_traffic_in}")
        logger.info(f"Total salidas: {total_traffic_out}")
        logger.info(f"Total mensajes: {total_messages}")
        logger.info(f"Cámaras con estadísticas: {len(camera_stats)}")
        
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
        import traceback
        logger.error(f"Error obteniendo estadísticas por horas del parking {pid}: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@api_bp.route('/panels/verify', methods=['POST'])
def verify_all_panels():
    """Verificar el estado de todos los paneles mediante ping"""
    try:
        session = Session()
        panels = session.query(Panel).all()
        
        results = []
        updated_count = 0
        online_count = 0
        offline_count = 0
        
        from panel_client import ping_panel, test_panel_api_connection
        
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
                
                # Contar estados
                if success:
                    online_count += 1
                else:
                    offline_count += 1
                
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
                    'response_time': round(response_time, 2) if success else None,
                    'status_changed': status_changed,
                    'ping_success': success,
                    'ping_time_ms': round(response_time, 2) if success else None
                })
                
            except Exception as e:
                logger.error(f"Error verificando panel {panel.id}: {e}")
                offline_count += 1
                results.append({
                    'panel_id': panel.id,
                    'panel_name': panel.name,
                    'ip': panel.ip,
                    'error': str(e),
                    'status_changed': False,
                    'ping_success': False,
                    'ping_time_ms': None
                })
        
        logger.info(f"Commit de cambios: {updated_count} paneles actualizados")
        session.commit()
        
        # Refrescar los objetos panel para asegurar persistencia
        for panel in panels:
            session.refresh(panel)
            logger.info(f"Panel {panel.id} después del refresh: status={panel.status}")
        
        session.close()
        
        logger.info(f"Verificación completada: {len(panels)} total, {updated_count} actualizados, {online_count} online, {offline_count} offline")
        
        return jsonify({
            'status': 'ok',
            'total_panels': len(panels),
            'updated_count': updated_count,
            'online_count': online_count,
            'offline_count': offline_count,
            'results': results,
            'summary': {
                'total': len(panels),
                'online': online_count,
                'offline': offline_count,
                'updated': updated_count
            }
        })
    except Exception as e:
        logger.error(f"Error verificando paneles: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# ENDPOINTS DE PROGRAMACIONES DE PANELES
# ============================================================================

@api_bp.route('/schedules', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_schedules():
    """Obtener programaciones filtradas por permisos de usuario"""
    try:
        parking_id = request.args.get('parking_id', type=int)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # Obtener parkings accesibles al usuario
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        user_role = request.user_data.get('role', 'user')
        user_id = request.user_data.get('user_id')
        
        logger.info(f"DEBUG Schedules - Usuario {user_id} (rol: {user_role}): {len(accessible_parking_ids)} parkings accesibles")
        
        if not accessible_parking_ids:
            # Usuario no tiene acceso a ningún parking
            logger.warning(f"Usuario {user_id} no tiene acceso a ningún parking - devolviendo lista vacía")
            return jsonify({'success': True, 'schedules': []})
        
        session = Session()
        schedule_service = PanelScheduleService(session)
        
        # Si se especifica un parking_id, verificar que el usuario tenga acceso
        if parking_id and parking_id not in accessible_parking_ids:
            session.close()
            return jsonify({'error': 'No tienes permisos para ver programaciones de este parking'}), 403
        
        # Si no se especifica parking_id, obtener programaciones de todos los parkings accesibles
        if not parking_id:
            all_schedules = []
            for pid in accessible_parking_ids:
                result = schedule_service.get_schedules(pid, active_only)
                if result['success']:
                    all_schedules.extend(result.get('schedules', []))
            
            session.close()
            return jsonify({'success': True, 'schedules': all_schedules})
        else:
            # Obtener programaciones del parking específico
            result = schedule_service.get_schedules(parking_id, active_only)
            session.close()
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error obteniendo programaciones: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules', methods=['POST'])
@require_superadmin
def create_schedule():
    """Crear una nueva programación"""
    try:
        req = request.get_json(force=True)
        
        session = Session()
        schedule_service = PanelScheduleService(session)
        result = schedule_service.create_schedule(req)
        session.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error creando programación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Obtener una programación específica"""
    try:
        session = Session()
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
        session.close()
        
        if not schedule:
            return jsonify({'error': 'Programación no encontrada'}), 404
        
        return jsonify({
            'id': schedule.id,
            'parking_id': schedule.parking_id,
            'user_id': schedule.user_id,
            'name': schedule.name,
            'description': schedule.description,
            'start_date': schedule.start_date.isoformat(),
            'end_date': schedule.end_date.isoformat(),
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'monday': schedule.monday,
            'tuesday': schedule.tuesday,
            'wednesday': schedule.wednesday,
            'thursday': schedule.thursday,
            'friday': schedule.friday,
            'saturday': schedule.saturday,
            'sunday': schedule.sunday,
            'message': schedule.message,
            'color': schedule.color,
            'font_size': schedule.font_size,
            'effect': schedule.effect,
            'is_active': schedule.is_active,
            'priority': schedule.priority,
            'created_at': schedule.created_at.isoformat(),
            'updated_at': schedule.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo programación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Actualizar una programación"""
    try:
        req = request.get_json(force=True)
        
        session = Session()
        schedule_service = PanelScheduleService(session)
        result = schedule_service.update_schedule(schedule_id, req)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error actualizando programación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Eliminar una programación"""
    try:
        session = Session()
        schedule_service = PanelScheduleService(session)
        result = schedule_service.delete_schedule(schedule_id)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error eliminando programación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/<int:schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    """Activar/desactivar una programación"""
    try:
        session = Session()
        schedule_service = PanelScheduleService(session)
        result = schedule_service.toggle_schedule(schedule_id)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error cambiando estado de programación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/<int:schedule_id>/execute', methods=['POST'])
def execute_schedule(schedule_id):
    """Ejecutar una programación manualmente"""
    try:
        session = Session()
        schedule = session.query(PanelSchedule).filter(PanelSchedule.id == schedule_id).first()
        
        if not schedule:
            session.close()
            return jsonify({'error': 'Programación no encontrada'}), 404
        
        schedule_service = PanelScheduleService(session, "http://localhost:8888/api/v1/panels/send")
        result = schedule_service.execute_schedule(schedule)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error ejecutando programación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/execute-all', methods=['POST'])
@require_auth
def execute_all_schedules():
    """Ejecutar todas las programaciones activas"""
    try:
        session = Session()
        schedule_service = PanelScheduleService(session, "http://localhost:8888/api/v1/panels/send")
        result = schedule_service.execute_all_active_schedules()
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error ejecutando todas las programaciones: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/schedules/logs', methods=['GET'])
def get_schedule_logs():
    """Obtener logs de programaciones"""
    try:
        schedule_id = request.args.get('schedule_id', type=int)
        parking_id = request.args.get('parking_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        session = Session()
        schedule_service = PanelScheduleService(session)
        result = schedule_service.get_schedule_logs(schedule_id, parking_id, limit)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error obteniendo logs de programaciones: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/schedules', methods=['GET'])
def get_parking_schedules(pid):
    """Obtener programaciones de un parking específico"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        session = Session()
        schedule_service = PanelScheduleService(session)
        result = schedule_service.get_schedules(pid, active_only)
        session.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error obteniendo programaciones del parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:pid>/active-schedules', methods=['GET'])
def get_parking_active_schedules(pid):
    """Obtener programaciones activas para un parking en el momento actual"""
    try:
        session = Session()
        schedule_service = PanelScheduleService(session)
        schedules = schedule_service.get_active_schedules_for_parking(pid)
        session.close()
        
        result = []
        for schedule in schedules:
            result.append({
                'id': schedule.id,
                'name': schedule.name,
                'message': schedule.message,
                'color': schedule.color,
                'font_size': schedule.font_size,
                'effect': schedule.effect,
                'priority': schedule.priority
            })
        
        return jsonify({'success': True, 'schedules': result})
        
    except Exception as e:
        logger.error(f"Error obteniendo programaciones activas del parking {pid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# ENDPOINTS DE ADMINISTRACIÓN DE USUARIOS (solo superadmin)
# ============================================================================

@api_bp.route('/admin/users', methods=['GET'])
@require_superadmin
def get_all_users():
    """Listar todos los usuarios (solo superadmin)"""
    try:
        session = Session()
        
        # Obtener todos los usuarios activos
        users = session.query(User).filter(User.is_active == True).all()
        
        # Formatear respuesta
        users_data = []
        for user in users:
            # Obtener parkings asignados
            user_parkings = session.query(UserParking).filter(UserParking.user_id == user.id).all()
            parking_ids = [up.parking_id for up in user_parkings]
            
            # Obtener paneles asignados
            user_panels = session.query(UserPanel).filter(UserPanel.user_id == user.id).all()
            panel_ids = [up.panel_id for up in user_panels]
            
            # Obtener cámaras asignadas
            user_accesses = session.query(UserAccess).filter(UserAccess.user_id == user.id).all()
            access_ids = [ua.access_id for ua in user_accesses]
            
            users_data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'parking_ids': parking_ids,
                'panel_ids': panel_ids,
                'access_ids': access_ids,
                'parking_count': len(parking_ids)  # Agregar conteo de parkings
            })
        
        session.close()
        
        logger.info(f"Lista de usuarios obtenida por superadmin")
        return jsonify({
            'success': True,
            'users': users_data,
            'total': len(users_data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/admin/users', methods=['POST'])
@require_superadmin
def create_admin_user():
    """Crear un nuevo usuario (solo superadmin)"""
    try:
        req = request.get_json(force=True)
        name = req.get('name')
        email = req.get('email')
        password = req.get('password')
        role = req.get('role', 'user')
        
        if not all([name, email, password]):
            return jsonify({'error': 'Faltan campos requeridos: name, email, password'}), 400
        
        # Validar rol
        allowed_roles = ['superadmin', 'user']
        if role not in allowed_roles:
            return jsonify({'error': f'Rol no permitido: {role}. Roles válidos: {allowed_roles}'}), 400
        
        session = Session()
        result = create_user(session, name, email, password, role)
        session.close()
        
        if result['success']:
            logger.info(f"Usuario creado por superadmin: {email} (rol: {role})")
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@require_superadmin
def get_user_details(user_id):
    """Obtener detalles de un usuario específico (solo superadmin)"""
    try:
        session = Session()
        
        user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            session.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener parkings asignados con detalles
        user_parkings = session.query(UserParking, Parking).join(
            Parking, UserParking.parking_id == Parking.id
        ).filter(UserParking.user_id == user_id).all()
        
        parking_details = []
        for up, parking in user_parkings:
            parking_details.append({
                'id': parking.id,
                'name': parking.name,
                'address': parking.address
            })
        
        # Obtener paneles asignados con detalles
        user_panels = session.query(UserPanel, Panel).join(
            Panel, UserPanel.panel_id == Panel.id
        ).filter(UserPanel.user_id == user_id).all()
        
        panel_details = []
        for up, panel in user_panels:
            panel_details.append({
                'id': panel.id,
                'ip': panel.ip,
                'name': panel.name
            })
        
        # Obtener cámaras asignadas con detalles
        user_accesses = session.query(UserAccess, Access).join(
            Access, UserAccess.access_id == Access.id
        ).filter(UserAccess.user_id == user_id).all()
        
        access_details = []
        for ua, access in user_accesses:
            access_details.append({
                'id': access.id,
                'name': access.name,
                'line': access.line
            })
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'parkings': parking_details,
            'panels': panel_details,
            'accesses': access_details
        }
        
        session.close()
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo detalles de usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/admin/users/<int:user_id>/assign', methods=['POST'])
@require_superadmin
def assign_user_resources(user_id):
    """Asignar recursos (parkings, paneles, cámaras) a un usuario (solo superadmin)"""
    try:
        req = request.get_json(force=True)
        parking_ids = req.get('parking_ids', [])
        panel_ids = req.get('panel_ids', [])
        access_ids = req.get('access_ids', [])
        
        # Verificar que el usuario existe
        session = Session()
        user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            session.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Asignar recursos
        result = assign_user_to_resources(
            session, user_id, parking_ids, panel_ids, access_ids
        )
        session.close()
        
        if result['success']:
            logger.info(f"Recursos asignados a usuario {user_id} por superadmin")
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error asignando recursos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@require_superadmin
def delete_admin_user(user_id):
    """Eliminar un usuario (solo superadmin)"""
    try:
        # Verificar que no se elimine a sí mismo
        current_user_id = request.user_data['user_id']
        if current_user_id == user_id:
            return jsonify({'error': 'No puedes eliminar tu propia cuenta'}), 400
        
        session = Session()
        result = delete_user(session, user_id)
        session.close()
        
        if result['success']:
            logger.info(f"Usuario {user_id} eliminado por superadmin")
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@require_superadmin
def update_user_role(user_id):
    """Actualizar rol de un usuario (solo superadmin)"""
    try:
        req = request.get_json(force=True)
        new_role = req.get('role')
        
        if not new_role:
            return jsonify({'error': 'Falta campo requerido: role'}), 400
        
        # Validar rol
        allowed_roles = ['superadmin', 'user']
        if new_role not in allowed_roles:
            return jsonify({'error': f'Rol no permitido: {new_role}. Roles válidos: {allowed_roles}'}), 400
        
        # Verificar que no se cambie su propio rol
        current_user_id = request.user_data['user_id']
        if current_user_id == user_id:
            return jsonify({'error': 'No puedes cambiar tu propio rol'}), 400
        
        session = Session()
        
        user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            session.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        old_role = user.role
        user.role = new_role
        session.commit()
        session.close()
        
        logger.info(f"Rol de usuario {user_id} cambiado de {old_role} a {new_role} por superadmin")
        return jsonify({
            'success': True,
            'message': f'Rol actualizado de {old_role} a {new_role}',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        })
        
    except Exception as e:
        logger.error(f"Error actualizando rol: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@require_superadmin
def toggle_user_status(user_id):
    """Activar/desactivar un usuario (solo superadmin)"""
    try:
        # Verificar que no se desactive a sí mismo
        current_user_id = request.user_data['user_id']
        if current_user_id == user_id:
            return jsonify({'error': 'No puedes desactivar tu propia cuenta'}), 400
        
        session = Session()
        
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        old_status = user.is_active
        user.is_active = not old_status
        session.commit()
        session.close()
        
        new_status = "activado" if user.is_active else "desactivado"
        logger.info(f"Usuario {user_id} {new_status} por superadmin")
        
        return jsonify({
            'success': True,
            'message': f'Usuario {new_status} correctamente',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
        })
        
    except Exception as e:
        logger.error(f"Error cambiando estado de usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/parkings/<int:parking_id>', methods=['DELETE'])
@require_superadmin
def delete_parking(parking_id):
    """Eliminar un parking (solo superadmin)"""
    try:
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).get(parking_id)
        if not parking:
            session.close()
            return jsonify({'error': 'Parking not found'}), 404
        
        parking_name = parking.name
        
        # Verificar que no hay ocupación actual
        if parking.current_occupancy > 0:
            session.close()
            return jsonify({
                'error': 'No se puede eliminar un parking con ocupación actual',
                'current_occupancy': parking.current_occupancy
            }), 400
        
        # Eliminar asignaciones de usuarios
        session.query(UserParking).filter(UserParking.parking_id == parking_id).delete()
        
        # Eliminar relaciones de cámaras del parking (usando la nueva relación muchos a muchos)
        session.query(CameraParking).filter(CameraParking.parking_id == parking_id).delete()
        
        # Eliminar paneles del parking
        session.query(Panel).filter(Panel.parking_id == parking_id).delete()
        
        # Eliminar programaciones del parking
        session.query(ScheduledMessage).filter(ScheduledMessage.parking_id == parking_id).delete()
        
        # Eliminar el parking
        session.delete(parking)
        session.commit()
        session.close()
        
        logger.info(f"Parking deleted - ID: {parking_id}, Name: {parking_name}")
        return jsonify({
            'status': 'ok',
            'message': f'Parking "{parking_name}" eliminado correctamente',
            'parking_id': parking_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting parking {parking_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# ENDPOINTS DEL SISTEMA DE ALARMAS v3.2.0_alarms
# ============================================================================

@api_bp.route('/alarms/configurations', methods=['GET'])
@require_auth
def get_alarm_configurations():
    """Obtener configuraciones de alarmas del usuario autenticado"""
    try:
        user_id = request.user_data['user_id']
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        configurations = alarm_service.get_user_alarm_configurations(user_id)
        
        # Formatear respuesta con información completa
        configs_data = []
        for config in configurations:
            # Obtener objetivos
            targets = []
            for target in config.targets:
                if target.target_type == 'panel':
                    panel = session.query(Panel).filter(Panel.id == target.target_id).first()
                    if panel:
                        targets.append({
                            'id': panel.id,
                            'name': panel.name,
                            'type': 'panel',
                            'ip': panel.ip
                        })
                elif target.target_type == 'camera':
                    camera = session.query(Access).filter(Access.id == target.target_id).first()
                    if camera:
                        targets.append({
                            'id': camera.id,
                            'name': camera.device,
                            'type': 'camera',
                            'ip': camera.ip
                        })
                elif target.target_type == 'parking':
                    parking = session.query(Parking).filter(Parking.id == target.target_id).first()
                    if parking:
                        targets.append({
                            'id': parking.id,
                            'name': parking.name,
                            'type': 'parking'
                        })
            
            # Obtener umbrales
            thresholds = []
            for threshold in config.thresholds:
                thresholds.append({
                    'severity': threshold.severity,
                    'threshold_value': threshold.threshold_value,
                    'threshold_type': threshold.threshold_type
                })
            
            configs_data.append({
                'id': config.id,
                'name': config.name,
                'description': config.description,
                'alarm_type': config.alarm_type,
                'status': config.status,
                'targets': targets,
                'thresholds': thresholds,
                'created_at': config.created_at.isoformat() if config.created_at else None
            })
        
        session.close()
        
        return jsonify({
            'configurations': configs_data,
            'total': len(configs_data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo configuraciones de alarmas: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/configurations', methods=['POST'])
@require_auth
def create_alarm_configuration():
    """Crear nueva configuración de alarma"""
    try:
        user_id = request.user_data['user_id']
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['name', 'alarm_type', 'targets', 'thresholds']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Validar tipo de alarma
        valid_types = ['panel', 'camera', 'parking']
        if data['alarm_type'] not in valid_types:
            return jsonify({'error': f'Tipo de alarma inválido. Debe ser uno de: {valid_types}'}), 400
        
        # Validar umbrales
        valid_severities = ['LEVE', 'NORMAL', 'GRAVE']
        for threshold in data['thresholds']:
            if threshold.get('severity') not in valid_severities:
                return jsonify({'error': f'Severidad inválida. Debe ser una de: {valid_severities}'}), 400
        
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        configuration = alarm_service.create_alarm_configuration(user_id, data)
        
        if configuration:
            session.close()
            return jsonify({
                'success': True,
                'message': 'Configuración de alarma creada correctamente',
                'configuration_id': configuration.id
            }), 201
        else:
            session.close()
            return jsonify({'error': 'Error creando configuración de alarma'}), 500
        
    except Exception as e:
        logger.error(f"Error creando configuración de alarma: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/configurations/<int:config_id>', methods=['GET'])
@require_auth
def get_alarm_configuration(config_id):
    """Obtener configuración específica de alarma"""
    try:
        user_id = request.user_data['user_id']
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        configuration = alarm_service.get_alarm_configuration(config_id, user_id)
        
        if not configuration:
            session.close()
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Formatear respuesta completa
        targets = []
        for target in configuration.targets:
            if target.target_type == 'panel':
                panel = session.query(Panel).filter(Panel.id == target.target_id).first()
                if panel:
                    targets.append({
                        'id': panel.id,
                        'name': panel.name,
                        'type': 'panel',
                        'ip': panel.ip
                    })
            elif target.target_type == 'camera':
                camera = session.query(Access).filter(Access.id == target.target_id).first()
                if camera:
                    targets.append({
                        'id': camera.id,
                        'name': camera.device,
                        'type': 'camera',
                        'ip': camera.ip
                    })
            elif target.target_type == 'parking':
                parking = session.query(Parking).filter(Parking.id == target.target_id).first()
                if parking:
                    targets.append({
                        'id': parking.id,
                        'name': parking.name,
                        'type': 'parking'
                    })
        
        thresholds = []
        for threshold in configuration.thresholds:
            thresholds.append({
                'severity': threshold.severity,
                'threshold_value': threshold.threshold_value,
                'threshold_type': threshold.threshold_type
            })
        
        config_data = {
            'id': configuration.id,
            'name': configuration.name,
            'description': configuration.description,
            'alarm_type': configuration.alarm_type,
            'status': configuration.status,
            'targets': targets,
            'thresholds': thresholds,
            'created_at': configuration.created_at.isoformat() if configuration.created_at else None,
            'updated_at': configuration.updated_at.isoformat() if configuration.updated_at else None
        }
        
        session.close()
        
        return jsonify(config_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración de alarma: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/configurations/<int:config_id>', methods=['PUT'])
@require_auth
def update_alarm_configuration(config_id):
    """Actualizar configuración de alarma"""
    try:
        user_id = request.user_data['user_id']
        data = request.get_json()
        
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        # Verificar que la configuración pertenece al usuario
        configuration = alarm_service.get_alarm_configuration(config_id, user_id)
        if not configuration:
            session.close()
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Actualizar campos permitidos
        if 'name' in data:
            configuration.name = data['name']
        if 'description' in data:
            configuration.description = data['description']
        if 'status' in data:
            if data['status'] not in ['active', 'paused']:
                return jsonify({'error': 'Estado inválido. Debe ser "active" o "paused"'}), 400
            configuration.status = data['status']
        
        # Actualizar umbrales si se proporcionan
        if 'thresholds' in data:
            # Eliminar umbrales existentes
            session.query(AlarmConfigurationThreshold).filter(
                AlarmConfigurationThreshold.alarm_configuration_id == config_id
            ).delete()
            
            # Crear nuevos umbrales
            for threshold_data in data['thresholds']:
                threshold = AlarmConfigurationThreshold(
                    alarm_configuration_id=config_id,
                    severity=threshold_data['severity'],
                    threshold_value=threshold_data['threshold_value'],
                    threshold_type=threshold_data['threshold_type']
                )
                session.add(threshold)
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'message': 'Configuración de alarma actualizada correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error actualizando configuración de alarma: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/configurations/<int:config_id>', methods=['DELETE'])
@require_auth
def delete_alarm_configuration(config_id):
    """Eliminar configuración de alarma"""
    try:
        user_id = request.user_data['user_id']
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        # Verificar que la configuración pertenece al usuario
        configuration = alarm_service.get_alarm_configuration(config_id, user_id)
        if not configuration:
            session.close()
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Verificar que no hay alarmas activas
        active_alarms = session.query(Alarm).filter(
            and_(
                Alarm.alarm_configuration_id == config_id,
                Alarm.status == 'active'
            )
        ).count()
        
        if active_alarms > 0:
            session.close()
            return jsonify({
                'error': 'No se puede eliminar una configuración con alarmas activas',
                'active_alarms': active_alarms
            }), 400
        
        # Eliminar la configuración (cascada automática)
        session.delete(configuration)
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'message': 'Configuración de alarma eliminada correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error eliminando configuración de alarma: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms', methods=['GET'])
@require_auth
def get_active_alarms():
    """Obtener alarmas activas del usuario"""
    try:
        user_id = request.user_data['user_id']
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        alarms = alarm_service.get_active_alarms(user_id)
        
        alarms_data = []
        for alarm in alarms:
            # Obtener información de la configuración
            config_name = alarm.configuration.name if alarm.configuration else 'Configuración eliminada'
            
            # Parsear targets afectados
            affected_targets = []
            if alarm.affected_targets:
                try:
                    targets_json = json.loads(alarm.affected_targets)
                    affected_targets = targets_json
                except:
                    affected_targets = []
            
            alarms_data.append({
                'id': alarm.id,
                'configuration_name': config_name,
                'severity': alarm.severity,
                'status': alarm.status,
                'message': alarm.message,
                'affected_targets': affected_targets,
                'created_at': alarm.created_at.isoformat() if alarm.created_at else None
            })
        
        session.close()
        
        return jsonify({
            'alarms': alarms_data,
            'total': len(alarms_data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo alarmas activas: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/<int:alarm_id>/resolve', methods=['POST'])
@require_auth
def resolve_alarm(alarm_id):
    """Resolver una alarma activa"""
    try:
        user_id = request.user_data['user_id']
        data = request.get_json()
        
        resolution_description = data.get('resolution_description', 'Resuelto por el usuario')
        
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        success = alarm_service.resolve_alarm(alarm_id, user_id, resolution_description)
        
        if success:
            # Enviar notificación de resolución por email
            try:
                from email_service import EmailService
                email_service = EmailService()
                
                alarm = session.query(Alarm).filter(Alarm.id == alarm_id).first()
                if alarm and alarm.configuration:
                    user = session.query(User).filter(User.id == user_id).first()
                    if user and user.email:
                        email_service.send_alarm_resolution_notification(user.email, {
                            'alarm_id': alarm.id,
                            'severity': alarm.severity,
                            'message': alarm.message,
                            'configuration_name': alarm.configuration.name,
                            'resolution_description': resolution_description,
                            'resolved_at': datetime.utcnow().isoformat()
                        })
            except Exception as e:
                logger.error(f"Error enviando notificación de resolución: {e}")
            
            session.close()
            return jsonify({
                'success': True,
                'message': 'Alarma resuelta correctamente'
            })
        else:
            session.close()
            return jsonify({'error': 'Error resolviendo alarma'}), 500
        
    except Exception as e:
        logger.error(f"Error resolviendo alarma: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/history', methods=['GET'])
@require_auth
def get_alarm_history():
    """Obtener histórico de alarmas con filtros"""
    try:
        user_id = request.user_data['user_id']
        
        # Obtener filtros de query parameters
        severity = request.args.get('severity')
        status = request.args.get('status')
        alarm_type = request.args.get('alarm_type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit', 100, type=int)
        
        filters = {}
        if severity:
            filters['severity'] = severity
        if status:
            filters['status'] = status
        if alarm_type:
            filters['alarm_type'] = alarm_type
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        alarms = alarm_service.get_alarm_history(user_id, filters)
        
        # Limitar resultados
        alarms = alarms[:limit]
        
        alarms_data = []
        for alarm in alarms:
            config_name = alarm.configuration.name if alarm.configuration else 'Configuración eliminada'
            
            affected_targets = []
            if alarm.affected_targets:
                try:
                    targets_json = json.loads(alarm.affected_targets)
                    affected_targets = targets_json
                except:
                    affected_targets = []
            
            alarms_data.append({
                'id': alarm.id,
                'configuration_name': config_name,
                'severity': alarm.severity,
                'status': alarm.status,
                'message': alarm.message,
                'affected_targets': affected_targets,
                'created_at': alarm.created_at.isoformat() if alarm.created_at else None,
                'resolved_at': alarm.resolved_at.isoformat() if alarm.resolved_at else None,
                'resolution_description': alarm.resolution_description
            })
        
        session.close()
        
        return jsonify({
            'alarms': alarms_data,
            'total': len(alarms_data),
            'filters_applied': filters
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo histórico de alarmas: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/equipment-status', methods=['GET'])
@require_auth
def get_equipment_status():
    """Obtener estado de conectividad de equipos"""
    try:
        session = Session()
        
        # Obtener estado de paneles
        panels_data = []
        panels = session.query(Panel).all()
        
        for panel in panels:
            # Simular ping (en producción se usaría el servicio de monitorización)
            is_online = True  # Por defecto, en producción se verificaría con ping
            last_ping = datetime.utcnow().isoformat()
            response_time = 15  # ms, en producción se mediría
            
            panels_data.append({
                'id': panel.id,
                'name': panel.name,
                'ip': panel.ip,
                'status': 'online' if is_online else 'offline',
                'last_ping': last_ping,
                'response_time': response_time
            })
        
        # Obtener estado de cámaras
        cameras_data = []
        cameras = session.query(Access).all()
        
        for camera in cameras:
            # Simular ping
            is_online = True
            last_ping = datetime.utcnow().isoformat()
            response_time = 20
            
            cameras_data.append({
                'id': camera.id,
                'name': camera.device,
                'ip': camera.ip,
                'status': 'online' if is_online else 'offline',
                'last_ping': last_ping,
                'response_time': response_time
            })
        
        # Obtener estado de aparcamientos
        parkings_data = []
        parkings = session.query(Parking).all()
        
        for parking in parkings:
            # Verificar si hay información disponible
            has_cameras = session.query(Access).join(CameraParking).filter(
                CameraParking.parking_id == parking.id
            ).count() > 0
            
            has_panels = session.query(Panel).filter(
                Panel.parking_id == parking.id
            ).count() > 0
            
            parkings_data.append({
                'id': parking.id,
                'name': parking.name,
                'status': 'online' if (has_cameras or has_panels) else 'offline',
                'has_cameras': has_cameras,
                'has_panels': has_panels,
                'current_occupancy': parking.current_occupancy,
                'max_capacity': parking.max_capacity
            })
        
        session.close()
        
        return jsonify({
            'panels': panels_data,
            'cameras': cameras_data,
            'parkings': parkings_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de equipos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/alarms/statistics', methods=['GET'])
@require_auth
def get_alarm_statistics():
    """Obtener estadísticas de alarmas del usuario"""
    try:
        user_id = request.user_data['user_id']
        session = Session()
        
        from alarm_service import AlarmService
        alarm_service = AlarmService(session)
        
        statistics = alarm_service.get_alarm_statistics(user_id)
        
        session.close()
        
        return jsonify(statistics)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de alarmas: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# NUEVO v4.1.0: ENDPOINTS PARA SISTEMA DE SENSORES INDIVIDUALES
# ============================================================================

@api_bp.route('/sensors', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_individual_sensors():
    """Obtener todos los sensores individuales con filtros opcionales - FILTRADO POR PERMISOS"""
    try:
        session = Session()
        
        # Parámetros de filtro
        parking_id = request.args.get('parking_id', type=int)
        sensor_type = request.args.get('sensor_type')
        is_active = request.args.get('is_active', type=bool)
        
        # Query base con filtrado por permisos
        query = session.query(IndividualSensor)
        
        # Filtrar por parkings accesibles al usuario
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        user_role = request.user_data.get('role', 'user')
        user_id = request.user_data.get('user_id')
        
        logger.info(f"DEBUG Sensores - Usuario {user_id} (rol: {user_role}): {len(accessible_parking_ids)} parkings accesibles: {accessible_parking_ids}")
        
        # CRÍTICO: Verificar si el filtrado se está aplicando
        total_sensors_before = session.query(IndividualSensor).count()
        logger.info(f"DEBUG - Total sensores en BD antes del filtro: {total_sensors_before}")
        
        # Permitir buscar por serial_number sin filtros de parking (para encontrar sensores "ocultos")
        search_serial = request.args.get('search_serial')
        # NUEVO v4.3.0: Permitir mostrar todos los sensores (incluyendo sin parking)
        show_all = request.args.get('show_all', 'false').lower() == 'true'
        
        if accessible_parking_ids:
            if show_all or search_serial:
                # Si show_all está activado o se busca por serial_number, mostrar todos los sensores
                # (incluyendo sin parking y en parkings no accesibles)
                if search_serial:
                    query = query.filter(
                        IndividualSensor.serial_number.ilike(f'%{search_serial}%')
                    )
                # Si show_all, no aplicar filtro de parking
            else:
                # Filtrar solo sensores de parkings accesibles (excluyendo sensores sin parking)
                query = query.filter(
                    IndividualSensor.parking_id.in_(accessible_parking_ids)
                )
            
            # Debug: contar sensores después del filtro
            sensors_after_filter = query.count()
            logger.info(f"DEBUG - Sensores después del filtro: {sensors_after_filter} (show_all={show_all}, search_serial={search_serial})")
            
        else:
            # Si no tiene acceso a ningún parking, solo permitir búsqueda por serial_number o show_all
            if show_all or search_serial:
                if search_serial:
                    query = query.filter(
                        IndividualSensor.serial_number.ilike(f'%{search_serial}%')
                    )
                # Si show_all, no aplicar filtro de parking
            else:
                # Si no tiene acceso a ningún parking y no busca por serial ni show_all, devolver vacío
                logger.warning(f"Usuario {user_id} no tiene acceso a ningún parking - devolviendo lista vacía")
                session.close()
                return jsonify([])
        
        # Aplicar filtros adicionales
        if parking_id:
            query = query.filter(IndividualSensor.parking_id == parking_id)
        if sensor_type:
            query = query.filter(IndividualSensor.sensor_type == sensor_type)
        if is_active is not None:
            query = query.filter(IndividualSensor.is_active == is_active)
        
        sensors = query.all()
        
        # Formatear respuesta
        sensors_data = []
        for sensor in sensors:
            sensor_data = {
                'id': sensor.id,
                'serial_number': sensor.serial_number,
                'name': sensor.name,
                'sensor_type': sensor.sensor_type,
                'parking_id': sensor.parking_id,
                'parking_name': sensor.parking.name if sensor.parking else None,
                'description': sensor.description,
                'location_coordinates': sensor.location_coordinates,
                'manufacturer': sensor.manufacturer,
                'is_active': sensor.is_active,
                'created_at': sensor.created_at.isoformat() if sensor.created_at else None,
                'updated_at': sensor.updated_at.isoformat() if sensor.updated_at else None,
                'current_status': sensor.current_status,
                'last_update': sensor.last_update.isoformat() if sensor.last_update else None,
                'battery_info': sensor.battery_info
            }
            sensors_data.append(sensor_data)
        
        session.close()
        return jsonify(sensors_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo sensores individuales: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors', methods=['POST'])
@require_auth
def create_individual_sensor():
    """Crear un nuevo sensor individual"""
    try:
        data = request.get_json()
        
        # Validaciones
        required_fields = ['serial_number', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validar tipo de sensor
        valid_types = ['PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros']
        sensor_type = data.get('sensor_type', 'PMR')
        if sensor_type not in valid_types:
            return jsonify({'error': f'Invalid sensor_type. Must be one of: {valid_types}'}), 400
        
        session = Session()
        
        # Verificar que el serial_number no exista (solo sensores activos o en parkings accesibles)
        # Permitir reutilizar serial_numbers de sensores inactivos o no accesibles
        existing_sensor = session.query(IndividualSensor).filter(
            IndividualSensor.serial_number == data['serial_number'],
            IndividualSensor.is_active == True
        ).first()
        
        # Si existe un sensor activo con ese serial, verificar si está en parkings accesibles
        if existing_sensor:
            accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
            user_role = request.user_data.get('role', 'user')
            
            # Superadmin puede ver todos los sensores, así que no puede duplicar
            if user_role == 'superadmin':
                session.close()
                return jsonify({'error': 'Serial number already exists'}), 400
            
            # Si el sensor existente está en un parking accesible, no permitir duplicar
            if existing_sensor.parking_id and existing_sensor.parking_id in accessible_parking_ids:
                session.close()
                return jsonify({'error': 'Serial number already exists'}), 400
            
            # Si el sensor existente no está en parkings accesibles, permitir reutilizar
            # pero primero desactivar el sensor anterior
            logger.info(f"Reutilizando serial_number {data['serial_number']} de sensor inactivo/no accesible (ID: {existing_sensor.id})")
            existing_sensor.is_active = False
            session.commit()
        
        # Verificar que el parking existe si se especifica
        parking_id = data.get('parking_id')
        if parking_id:
            parking = session.query(Parking).get(parking_id)
            if not parking:
                session.close()
                return jsonify({'error': 'Parking not found'}), 404
        
        # Crear sensor
        sensor = IndividualSensor(
            serial_number=data['serial_number'],
            name=data['name'],
            sensor_type=sensor_type,
            parking_id=parking_id,
            description=data.get('description'),
            location_coordinates=data.get('location_coordinates'),
            manufacturer=data.get('manufacturer', 'Fleximodo'),
            is_active=data.get('is_active', True)
        )
        
        session.add(sensor)
        session.commit()
        
        # Crear estado inicial
        initial_status = SensorCurrentStatus(
            sensor_id=sensor.id,
            current_status='unknown',
            last_update=datetime.now()
        )
        session.add(initial_status)
        session.commit()
        
        # Respuesta
        response_data = {
            'id': sensor.id,
            'serial_number': sensor.serial_number,
            'name': sensor.name,
            'sensor_type': sensor.sensor_type,
            'parking_id': sensor.parking_id,
            'parking_name': sensor.parking.name if sensor.parking else None,
            'description': sensor.description,
            'location_coordinates': sensor.location_coordinates,
            'manufacturer': sensor.manufacturer,
            'is_active': sensor.is_active,
            'created_at': sensor.created_at.isoformat(),
            'current_status': 'unknown'
        }
        
        session.close()
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Error creando sensor individual: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/by-serial/<serial_number>', methods=['GET'])
@require_auth
def get_sensor_by_serial(serial_number):
    """Obtener un sensor por su serial_number (sin filtros de parking, útil para encontrar sensores ocultos)"""
    try:
        session = Session()
        sensor = session.query(IndividualSensor).filter(
            IndividualSensor.serial_number == serial_number
        ).first()
        
        if not sensor:
            session.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        response_data = {
            'id': sensor.id,
            'serial_number': sensor.serial_number,
            'name': sensor.name,
            'sensor_type': sensor.sensor_type,
            'parking_id': sensor.parking_id,
            'parking_name': sensor.parking.name if sensor.parking else None,
            'description': sensor.description,
            'location_coordinates': sensor.location_coordinates,
            'manufacturer': sensor.manufacturer,
            'is_active': sensor.is_active,
            'created_at': sensor.created_at.isoformat() if sensor.created_at else None,
            'updated_at': sensor.updated_at.isoformat() if sensor.updated_at else None,
            'current_status': sensor.current_status,
            'last_update': sensor.last_update.isoformat() if sensor.last_update else None,
            'battery_info': sensor.battery_info
        }
        
        session.close()
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo sensor por serial {serial_number}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/<int:sensor_id>', methods=['GET'])
@require_auth
def get_individual_sensor(sensor_id):
    """Obtener un sensor individual por ID"""
    try:
        session = Session()
        sensor = session.query(IndividualSensor).get(sensor_id)
        
        if not sensor:
            session.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        # Obtener historial reciente (últimas 24 horas)
        recent_history = session.query(SensorStatusHistory).filter(
            SensorStatusHistory.sensor_id == sensor_id,
            SensorStatusHistory.timestamp >= datetime.now() - timedelta(hours=24)
        ).order_by(SensorStatusHistory.timestamp.desc()).limit(50).all()
        
        history_data = []
        for record in recent_history:
            history_data.append({
                'status': record.status,
                'timestamp': record.timestamp.isoformat(),
                'battery_voltage': record.battery_voltage,
                'battery_capacity': record.battery_capacity,
                'temperature': record.temperature
            })
        
        response_data = {
            'id': sensor.id,
            'serial_number': sensor.serial_number,
            'name': sensor.name,
            'sensor_type': sensor.sensor_type,
            'parking_id': sensor.parking_id,
            'parking_name': sensor.parking.name if sensor.parking else None,
            'description': sensor.description,
            'location_coordinates': sensor.location_coordinates,
            'manufacturer': sensor.manufacturer,
            'is_active': sensor.is_active,
            'created_at': sensor.created_at.isoformat() if sensor.created_at else None,
            'updated_at': sensor.updated_at.isoformat() if sensor.updated_at else None,
            'current_status': sensor.current_status,
            'last_update': sensor.last_update.isoformat() if sensor.last_update else None,
            'battery_info': sensor.battery_info,
            'recent_history': history_data
        }
        
        session.close()
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo sensor {sensor_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/<int:sensor_id>', methods=['PUT'])
@require_auth
def update_individual_sensor(sensor_id):
    """Actualizar un sensor individual"""
    try:
        data = request.get_json()
        session = Session()
        
        sensor = session.query(IndividualSensor).get(sensor_id)
        if not sensor:
            session.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        # Validar tipo de sensor si se proporciona
        if 'sensor_type' in data:
            valid_types = ['PMR', 'Electrico', 'Caravanas', 'Emergencias', 'Policia', 'Otros']
            if data['sensor_type'] not in valid_types:
                session.close()
                return jsonify({'error': f'Invalid sensor_type. Must be one of: {valid_types}'}), 400
        
        # Verificar serial_number único si se cambia
        # Permitir reutilizar serial_numbers de sensores inactivos o no accesibles
        if 'serial_number' in data and data['serial_number'] != sensor.serial_number:
            existing = session.query(IndividualSensor).filter(
                IndividualSensor.serial_number == data['serial_number'],
                IndividualSensor.id != sensor_id,
                IndividualSensor.is_active == True
            ).first()
            
            if existing:
                accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
                user_role = request.user_data.get('role', 'user')
                
                # Superadmin puede ver todos los sensores, así que no puede duplicar
                if user_role == 'superadmin':
                    session.close()
                    return jsonify({'error': 'Serial number already exists'}), 400
                
                # Si el sensor existente está en un parking accesible, no permitir duplicar
                if existing.parking_id and existing.parking_id in accessible_parking_ids:
                    session.close()
                    return jsonify({'error': 'Serial number already exists'}), 400
                
                # Si el sensor existente no está en parkings accesibles, permitir reutilizar
                # pero primero desactivar el sensor anterior
                logger.info(f"Reutilizando serial_number {data['serial_number']} de sensor inactivo/no accesible (ID: {existing.id})")
                existing.is_active = False
                session.commit()
        
        # Verificar parking si se proporciona
        if 'parking_id' in data and data['parking_id']:
            parking = session.query(Parking).get(data['parking_id'])
            if not parking:
                session.close()
                return jsonify({'error': 'Parking not found'}), 404
        
        # Actualizar campos
        updatable_fields = [
            'serial_number', 'name', 'sensor_type', 'parking_id', 
            'description', 'location_coordinates', 'manufacturer', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(sensor, field, data[field])
        
        sensor.updated_at = datetime.now()
        session.commit()
        
        response_data = {
            'id': sensor.id,
            'serial_number': sensor.serial_number,
            'name': sensor.name,
            'sensor_type': sensor.sensor_type,
            'parking_id': sensor.parking_id,
            'parking_name': sensor.parking.name if sensor.parking else None,
            'description': sensor.description,
            'location_coordinates': sensor.location_coordinates,
            'manufacturer': sensor.manufacturer,
            'is_active': sensor.is_active,
            'updated_at': sensor.updated_at.isoformat()
        }
        
        session.close()
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error actualizando sensor {sensor_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/<int:sensor_id>', methods=['DELETE'])
@require_auth
def delete_individual_sensor(sensor_id):
    """Eliminar un sensor individual"""
    try:
        session = Session()
        sensor = session.query(IndividualSensor).get(sensor_id)
        
        if not sensor:
            session.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        sensor_name = sensor.name
        session.delete(sensor)
        session.commit()
        session.close()
        
        return jsonify({
            'message': f'Sensor "{sensor_name}" deleted successfully',
            'id': sensor_id
        })
        
    except Exception as e:
        logger.error(f"Error eliminando sensor {sensor_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/<int:sensor_id>/status', methods=['PUT'])
@require_auth
def update_sensor_status(sensor_id):
    """NUEVO v4.1.0: Actualizar manualmente el estado de un sensor"""
    try:
        data = request.get_json()
        
        # Validaciones
        if 'status' not in data:
            return jsonify({'error': 'Missing required field: status'}), 400
        
        valid_statuses = ['free', 'busy', 'error', 'unknown', 'notcalib']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        session = Session()
        sensor = session.query(IndividualSensor).get(sensor_id)
        
        if not sensor:
            session.close()
            return jsonify({'error': 'Sensor not found'}), 404
        
        # Obtener o crear estado actual
        current_status = session.query(SensorCurrentStatus).filter(
            SensorCurrentStatus.sensor_id == sensor_id
        ).first()
        
        if not current_status:
            current_status = SensorCurrentStatus(sensor_id=sensor_id)
            session.add(current_status)
        
        # Actualizar estado actual
        old_status = current_status.current_status
        current_status.current_status = data['status']
        current_status.last_update = datetime.now()
        
        # Datos opcionales
        if 'battery_capacity' in data:
            current_status.battery_capacity = data['battery_capacity']
        if 'battery_voltage' in data:
            current_status.battery_voltage = data['battery_voltage']
        if 'temperature' in data:
            current_status.temperature = data['temperature']
        
        # Crear registro en historial
        history_record = SensorStatusHistory(
            sensor_id=sensor_id,
            status=data['status'],
            timestamp=datetime.now(),
            battery_capacity=data.get('battery_capacity'),
            battery_voltage=data.get('battery_voltage'),
            temperature=data.get('temperature'),
            raw_data={'manual_update': True, 'user_id': 'manual'}
        )
        session.add(history_record)
        
        session.commit()
        
        # Actualizar resúmenes si el sensor está vinculado a un parking
        if sensor.parking_id:
            _update_parking_sensor_summary(session, sensor.parking_id, sensor.sensor_type)
        
        session.close()
        
        return jsonify({
            'message': 'Sensor status updated successfully',
            'sensor_id': sensor_id,
            'old_status': old_status,
            'new_status': data['status'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error actualizando estado del sensor {sensor_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/summary', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_sensors_summary():
    """Obtener resumen de sensores agrupados por parking y tipo - FILTRADO POR PERMISOS"""
    try:
        parking_id = request.args.get('parking_id', type=int)
        
        session = Session()
        
        # Query base para resúmenes con filtrado por permisos
        query = session.query(ParkingSensorSummary)
        
        # Filtrar por parkings accesibles al usuario
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        if accessible_parking_ids:
            query = query.filter(ParkingSensorSummary.parking_id.in_(accessible_parking_ids))
        else:
            # Si no tiene acceso a ningún parking, devolver vacío
            session.close()
            return jsonify([])
        
        # Filtro adicional por parking específico si se proporciona
        if parking_id:
            query = query.filter(ParkingSensorSummary.parking_id == parking_id)
        
        summaries = query.all()
        
        # Formatear respuesta
        summary_data = []
        for summary in summaries:
            summary_data.append({
                'parking_id': summary.parking_id,
                'parking_name': summary.parking.name,
                'sensor_type': summary.sensor_type,
                'total_sensors': summary.total_sensors,
                'free_sensors': summary.free_sensors,
                'busy_sensors': summary.busy_sensors,
                'error_sensors': summary.error_sensors,
                'occupancy_rate': summary.occupancy_rate,
                'available_sensors': summary.available_sensors,
                'status_distribution': summary.status_distribution,
                'last_update': summary.last_update.isoformat() if summary.last_update else None
            })
        
        session.close()
        return jsonify(summary_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de sensores: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/status/complete', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_complete_sensors_status():
    """Endpoint autenticado para estado completo de sensores individuales - FILTRADO POR PERMISOS"""
    try:
        parking_id = request.args.get('parking_id', type=int)
        sensor_type = request.args.get('sensor_type')
        
        session = Session()
        
        # Query base con filtrado por permisos
        query = session.query(IndividualSensor).filter(IndividualSensor.is_active == True)
        
        # Filtrar por parkings accesibles al usuario
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        if accessible_parking_ids:
            query = query.filter(IndividualSensor.parking_id.in_(accessible_parking_ids))
        else:
            # Si no tiene acceso a ningún parking, devolver vacío
            session.close()
            return jsonify({'sensors': [], 'statistics': {'total_sensors': 0}})
        
        # Aplicar filtros adicionales
        if parking_id:
            query = query.filter(IndividualSensor.parking_id == parking_id)
        if sensor_type:
            query = query.filter(IndividualSensor.sensor_type == sensor_type)
        
        sensors = query.all()
        
        # Formatear respuesta completa
        sensors_data = []
        for sensor in sensors:
            sensor_data = {
                'id': sensor.id,
                'serial_number': sensor.serial_number,
                'name': sensor.name,
                'sensor_type': sensor.sensor_type,
                'parking_id': sensor.parking_id,
                'parking_name': sensor.parking.name if sensor.parking else None,
                'description': sensor.description,
                'location_coordinates': sensor.location_coordinates,
                'manufacturer': sensor.manufacturer,
                'current_status': sensor.current_status,
                'last_update': sensor.last_update.isoformat() if sensor.last_update else None,
                'battery_info': sensor.battery_info,
                'is_online': sensor.current_status_rel.is_online if sensor.current_status_rel else False,
                'needs_attention': sensor.current_status_rel.needs_attention if sensor.current_status_rel else True
            }
            sensors_data.append(sensor_data)
        
        # Estadísticas generales
        total_sensors = len(sensors_data)
        status_counts = {}
        battery_alerts = 0
        offline_sensors = 0
        
        for sensor_data in sensors_data:
            status = sensor_data['current_status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if sensor_data['battery_info'] and sensor_data['battery_info']['is_low']:
                battery_alerts += 1
            
            if not sensor_data['is_online']:
                offline_sensors += 1
        
        response = {
            'sensors': sensors_data,
            'statistics': {
                'total_sensors': total_sensors,
                'status_distribution': status_counts,
                'battery_alerts': battery_alerts,
                'offline_sensors': offline_sensors,
                'health_score': round(((total_sensors - offline_sensors - battery_alerts) / max(total_sensors, 1)) * 100, 2)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        session.close()
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado completo de sensores: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/status/grouped', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_grouped_sensors_status():
    """Endpoint autenticado para estado agrupado por parking - FILTRADO POR PERMISOS"""
    try:
        session = Session()
        
        # Obtener parkings accesibles
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        if not accessible_parking_ids:
            # Si no tiene acceso a ningún parking, devolver vacío
            session.close()
            return jsonify({'grouped_data': [], 'timestamp': datetime.now().isoformat()})
        
        # Usar las vistas materializadas para datos optimizados
        try:
            # Intentar usar la función optimizada de la base de datos con filtrado
            parking_ids_str = ','.join(map(str, accessible_parking_ids))
            sql_query = f"SELECT * FROM get_sensors_dashboard_data() WHERE parking_id IN ({parking_ids_str})"
            result = session.execute(sql_query).fetchall()
            
            grouped_data = []
            for row in result:
                grouped_data.append({
                    'parking_id': row[0],
                    'parking_name': row[1],
                    'sensor_type': row[2],
                    'total_sensors': row[3],
                    'free_count': row[4],
                    'busy_count': row[5],
                    'error_count': row[6],
                    'occupancy_rate': float(row[7]) if row[7] else 0,
                    'avg_battery': float(row[8]) if row[8] else None,
                    'low_battery_count': row[9],
                    'stale_sensors': row[10],
                    'health_score': float(row[11]) if row[11] else 0
                })
            
        except Exception as db_error:
            logger.warning(f"Error usando función optimizada, fallback a query manual: {db_error}")
            
            # Fallback a query manual con filtrado por permisos
            parkings = session.query(Parking).filter(Parking.id.in_(accessible_parking_ids)).all()
            grouped_data = []
            
            for parking in parkings:
                # Obtener sensores por tipo para este parking
                sensor_types = session.query(IndividualSensor.sensor_type).filter(
                    IndividualSensor.parking_id == parking.id,
                    IndividualSensor.is_active == True
                ).distinct().all()
                
                for sensor_type_row in sensor_types:
                    sensor_type = sensor_type_row[0]
                    
                    # Estadísticas para este tipo
                    sensors = session.query(IndividualSensor).filter(
                        IndividualSensor.parking_id == parking.id,
                        IndividualSensor.sensor_type == sensor_type,
                        IndividualSensor.is_active == True
                    ).all()
                    
                    total = len(sensors)
                    free = sum(1 for s in sensors if s.current_status == 'free')
                    busy = sum(1 for s in sensors if s.current_status == 'busy')
                    error = sum(1 for s in sensors if s.current_status == 'error')
                    
                    grouped_data.append({
                        'parking_id': parking.id,
                        'parking_name': parking.name,
                        'sensor_type': sensor_type,
                        'total_sensors': total,
                        'free_count': free,
                        'busy_count': busy,
                        'error_count': error,
                        'occupancy_rate': round((busy / total * 100) if total > 0 else 0, 2),
                        'health_score': round(((total - error) / total * 100) if total > 0 else 0, 2)
                    })
        
        session.close()
        return jsonify({
            'grouped_data': grouped_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo datos agrupados de sensores: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# NUEVOS ENDPOINTS v4.2.0: SENSORES AGRUPADOS CON CONTROL DE PERMISOS
# ============================================================================

@api_bp.route('/parkings/<int:parking_id>/sensors/summary', methods=['GET'])
@require_parking_access('parking_id')
def get_parking_sensors_summary(parking_id):
    """
    Obtener resumen de sensores de un parking específico agrupado por tipo
    - Solo usuarios con acceso al parking pueden ver los datos
    - Superadmin ve todos los parkings
    """
    try:
        session = Session()
        
        # Verificar que el parking existe
        parking = session.query(Parking).filter(Parking.id == parking_id).first()
        if not parking:
            session.close()
            return jsonify({'error': 'Parking no encontrado'}), 404
        
        # Obtener sensores agrupados por tipo
        sensor_types_query = session.query(IndividualSensor.sensor_type).filter(
            IndividualSensor.parking_id == parking_id,
            IndividualSensor.is_active == True
        ).distinct()
        
        sensor_types_data = {}
        total_sensors = 0
        total_free = 0
        total_busy = 0
        total_error = 0
        
        for sensor_type_row in sensor_types_query:
            sensor_type = sensor_type_row[0]
            
            # Obtener sensores de este tipo
            sensors = session.query(IndividualSensor).filter(
                IndividualSensor.parking_id == parking_id,
                IndividualSensor.sensor_type == sensor_type,
                IndividualSensor.is_active == True
            ).all()
            
            # Contar por estado
            type_total = len(sensors)
            type_free = sum(1 for s in sensors if s.current_status == 'free')
            type_busy = sum(1 for s in sensors if s.current_status == 'busy')
            type_error = sum(1 for s in sensors if s.current_status == 'error')
            
            # Calcular métricas
            occupancy_rate = round((type_busy / type_total * 100) if type_total > 0 else 0, 2)
            health_score = round(((type_total - type_error) / type_total * 100) if type_total > 0 else 0, 2)
            
            sensor_types_data[sensor_type] = {
                'total': type_total,
                'free': type_free,
                'busy': type_busy,
                'error': type_error,
                'occupancy_rate': occupancy_rate,
                'health_score': health_score
            }
            
            # Sumar a totales
            total_sensors += type_total
            total_free += type_free
            total_busy += type_busy
            total_error += type_error
        
        # Calcular métricas globales
        overall_occupancy = round((total_busy / total_sensors * 100) if total_sensors > 0 else 0, 2)
        overall_health = round(((total_sensors - total_error) / total_sensors * 100) if total_sensors > 0 else 0, 2)
        
        response = {
            'parking_id': parking_id,
            'parking_name': parking.name,
            'sensor_types': sensor_types_data,
            'totals': {
                'total_sensors': total_sensors,
                'total_free': total_free,
                'total_busy': total_busy,
                'total_error': total_error,
                'overall_occupancy': overall_occupancy,
                'overall_health': overall_health
            },
            'last_update': datetime.now().isoformat()
        }
        
        session.close()
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de sensores del parking {parking_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/summary/user', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_user_sensors_summary():
    """
    Obtener resumen de sensores de todos los parkings del usuario
    - Filtra automáticamente por parkings asignados al usuario
    - Agrupa por parking y tipo de sensor
    """
    try:
        session = Session()
        
        # Obtener parkings accesibles
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        if not accessible_parking_ids:
            session.close()
            return jsonify({
                'user_parkings': [],
                'global_totals': {'total_sensors': 0, 'total_free': 0, 'total_busy': 0, 'total_error': 0}
            })
        
        # Obtener parkings del usuario
        parkings = session.query(Parking).filter(Parking.id.in_(accessible_parking_ids)).all()
        
        user_parkings = []
        global_total_sensors = 0
        global_total_free = 0
        global_total_busy = 0
        global_total_error = 0
        
        for parking in parkings:
            # Obtener tipos de sensores para este parking
            sensor_types_query = session.query(IndividualSensor.sensor_type).filter(
                IndividualSensor.parking_id == parking.id,
                IndividualSensor.is_active == True
            ).distinct()
            
            parking_sensor_types = {}
            
            for sensor_type_row in sensor_types_query:
                sensor_type = sensor_type_row[0]
                
                # Contar sensores de este tipo
                sensors = session.query(IndividualSensor).filter(
                    IndividualSensor.parking_id == parking.id,
                    IndividualSensor.sensor_type == sensor_type,
                    IndividualSensor.is_active == True
                ).all()
                
                type_total = len(sensors)
                type_free = sum(1 for s in sensors if s.current_status == 'free')
                type_busy = sum(1 for s in sensors if s.current_status == 'busy')
                type_error = sum(1 for s in sensors if s.current_status == 'error')
                
                parking_sensor_types[sensor_type] = {
                    'total': type_total,
                    'free': type_free,
                    'busy': type_busy,
                    'error': type_error
                }
                
                # Sumar a globales
                global_total_sensors += type_total
                global_total_free += type_free
                global_total_busy += type_busy
                global_total_error += type_error
            
            if parking_sensor_types:  # Solo agregar si tiene sensores
                user_parkings.append({
                    'parking_id': parking.id,
                    'parking_name': parking.name,
                    'sensor_types': parking_sensor_types
                })
        
        response = {
            'user_parkings': user_parkings,
            'global_totals': {
                'total_sensors': global_total_sensors,
                'total_free': global_total_free,
                'total_busy': global_total_busy,
                'total_error': global_total_error
            },
            'timestamp': datetime.now().isoformat()
        }
        
        session.close()
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de sensores del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/sensors/type/<sensor_type>/summary', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_sensors_by_type_summary(sensor_type):
    """
    Obtener resumen de sensores de un tipo específico
    - Filtra por parkings del usuario
    - Agrupa por parking
    """
    try:
        session = Session()
        
        # Obtener parkings accesibles
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        if not accessible_parking_ids:
            session.close()
            return jsonify({
                'sensor_type': sensor_type,
                'parkings': [],
                'totals': {'total_sensors': 0, 'total_free': 0, 'total_busy': 0, 'total_error': 0}
            })
        
        # Obtener parkings que tienen sensores de este tipo
        parkings_with_sensors = session.query(Parking).join(IndividualSensor).filter(
            Parking.id.in_(accessible_parking_ids),
            IndividualSensor.sensor_type == sensor_type,
            IndividualSensor.is_active == True
        ).distinct().all()
        
        parkings_data = []
        total_sensors = 0
        total_free = 0
        total_busy = 0
        total_error = 0
        
        for parking in parkings_with_sensors:
            # Obtener sensores de este tipo en este parking
            sensors = session.query(IndividualSensor).filter(
                IndividualSensor.parking_id == parking.id,
                IndividualSensor.sensor_type == sensor_type,
                IndividualSensor.is_active == True
            ).all()
            
            parking_total = len(sensors)
            parking_free = sum(1 for s in sensors if s.current_status == 'free')
            parking_busy = sum(1 for s in sensors if s.current_status == 'busy')
            parking_error = sum(1 for s in sensors if s.current_status == 'error')
            
            parkings_data.append({
                'parking_id': parking.id,
                'parking_name': parking.name,
                'total': parking_total,
                'free': parking_free,
                'busy': parking_busy,
                'error': parking_error,
                'occupancy_rate': round((parking_busy / parking_total * 100) if parking_total > 0 else 0, 2),
                'health_score': round(((parking_total - parking_error) / parking_total * 100) if parking_total > 0 else 0, 2)
            })
            
            # Sumar a totales
            total_sensors += parking_total
            total_free += parking_free
            total_busy += parking_busy
            total_error += parking_error
        
        response = {
            'sensor_type': sensor_type,
            'parkings': parkings_data,
            'totals': {
                'total_sensors': total_sensors,
                'total_free': total_free,
                'total_busy': total_busy,
                'total_error': total_error,
                'overall_occupancy': round((total_busy / total_sensors * 100) if total_sensors > 0 else 0, 2),
                'overall_health': round(((total_sensors - total_error) / total_sensors * 100) if total_sensors > 0 else 0, 2)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        session.close()
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de sensores tipo {sensor_type}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/dashboard/user/sensors', methods=['GET'])
@require_auth
@filter_by_user_permissions
def get_user_sensors_dashboard():
    """
    Dashboard personalizado con todos los datos de sensores del usuario
    - Resumen por parking
    - Alertas y notificaciones
    - Estadísticas rápidas
    """
    try:
        session = Session()
        
        # Obtener parkings accesibles
        accessible_parking_ids = getattr(request, 'accessible_parking_ids', [])
        if not accessible_parking_ids:
            session.close()
            return jsonify({
                'summary': {'total_sensors': 0, 'total_free': 0, 'total_busy': 0, 'total_error': 0},
                'parkings': [],
                'alerts': [],
                'statistics': {}
            })
        
        # Obtener información del usuario
        user_id = request.user_data.get('user_id')
        user_name = request.user_data.get('name')
        
        # Resumen global
        all_sensors = session.query(IndividualSensor).filter(
            IndividualSensor.parking_id.in_(accessible_parking_ids),
            IndividualSensor.is_active == True
        ).all()
        
        summary = {
            'total_sensors': len(all_sensors),
            'total_free': sum(1 for s in all_sensors if s.current_status == 'free'),
            'total_busy': sum(1 for s in all_sensors if s.current_status == 'busy'),
            'total_error': sum(1 for s in all_sensors if s.current_status == 'error'),
        }
        summary['occupancy_rate'] = round((summary['total_busy'] / summary['total_sensors'] * 100) if summary['total_sensors'] > 0 else 0, 2)
        summary['health_score'] = round(((summary['total_sensors'] - summary['total_error']) / summary['total_sensors'] * 100) if summary['total_sensors'] > 0 else 0, 2)
        
        # Resumen por parking
        parkings = session.query(Parking).filter(Parking.id.in_(accessible_parking_ids)).all()
        parkings_data = []
        
        for parking in parkings:
            parking_sensors = [s for s in all_sensors if s.parking_id == parking.id]
            if not parking_sensors:
                continue
                
            parking_summary = {
                'parking_id': parking.id,
                'parking_name': parking.name,
                'total_sensors': len(parking_sensors),
                'free': sum(1 for s in parking_sensors if s.current_status == 'free'),
                'busy': sum(1 for s in parking_sensors if s.current_status == 'busy'),
                'error': sum(1 for s in parking_sensors if s.current_status == 'error'),
            }
            parking_summary['occupancy_rate'] = round((parking_summary['busy'] / parking_summary['total_sensors'] * 100) if parking_summary['total_sensors'] > 0 else 0, 2)
            
            parkings_data.append(parking_summary)
        
        # Alertas y notificaciones
        alerts = []
        
        # Sensores con error
        error_sensors = [s for s in all_sensors if s.current_status == 'error']
        if error_sensors:
            alerts.append({
                'type': 'error',
                'severity': 'high',
                'message': f'{len(error_sensors)} sensores con error requieren atención',
                'count': len(error_sensors)
            })
        
        # Sensores con batería baja (si existe información)
        low_battery_sensors = [s for s in all_sensors if s.battery_info and s.battery_info.get('is_low', False)]
        if low_battery_sensors:
            alerts.append({
                'type': 'battery',
                'severity': 'medium',
                'message': f'{len(low_battery_sensors)} sensores con batería baja',
                'count': len(low_battery_sensors)
            })
        
        # Estadísticas adicionales
        statistics = {
            'sensor_types': {},
            'most_occupied_parking': None,
            'least_occupied_parking': None
        }
        
        # Contar por tipo de sensor
        for sensor in all_sensors:
            sensor_type = sensor.sensor_type
            if sensor_type not in statistics['sensor_types']:
                statistics['sensor_types'][sensor_type] = {'total': 0, 'busy': 0}
            statistics['sensor_types'][sensor_type]['total'] += 1
            if sensor.current_status == 'busy':
                statistics['sensor_types'][sensor_type]['busy'] += 1
        
        # Parking más y menos ocupado
        if parkings_data:
            most_occupied = max(parkings_data, key=lambda p: p['occupancy_rate'])
            least_occupied = min(parkings_data, key=lambda p: p['occupancy_rate'])
            statistics['most_occupied_parking'] = {
                'name': most_occupied['parking_name'],
                'occupancy_rate': most_occupied['occupancy_rate']
            }
            statistics['least_occupied_parking'] = {
                'name': least_occupied['parking_name'],
                'occupancy_rate': least_occupied['occupancy_rate']
            }
        
        response = {
            'user_info': {
                'user_id': user_id,
                'user_name': user_name,
                'accessible_parkings': len(accessible_parking_ids)
            },
            'summary': summary,
            'parkings': parkings_data,
            'alerts': alerts,
            'statistics': statistics,
            'timestamp': datetime.now().isoformat()
        }
        
        session.close()
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error obteniendo dashboard de sensores del usuario: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def _update_parking_sensor_summary(session, parking_id, sensor_type):
    """Función auxiliar para actualizar resúmenes por parking y tipo"""
    try:
        # Contar sensores por estado
        sensors = session.query(IndividualSensor).filter(
            IndividualSensor.parking_id == parking_id,
            IndividualSensor.sensor_type == sensor_type,
            IndividualSensor.is_active == True
        ).all()
        
        total = len(sensors)
        free = sum(1 for s in sensors if s.current_status == 'free')
        busy = sum(1 for s in sensors if s.current_status == 'busy')
        error = sum(1 for s in sensors if s.current_status == 'error')
        
        # Obtener o crear resumen
        summary = session.query(ParkingSensorSummary).filter(
            ParkingSensorSummary.parking_id == parking_id,
            ParkingSensorSummary.sensor_type == sensor_type
        ).first()
        
        if not summary:
            summary = ParkingSensorSummary(
                parking_id=parking_id,
                sensor_type=sensor_type
            )
            session.add(summary)
        
        # Actualizar valores
        summary.total_sensors = total
        summary.free_sensors = free
        summary.busy_sensors = busy
        summary.error_sensors = error
        summary.last_update = datetime.now()
        
        session.commit()
        logger.info(f"Resumen actualizado para parking {parking_id}, tipo {sensor_type}: {total} total, {free} libres, {busy} ocupados, {error} errores")
        
    except Exception as e:
        logger.error(f"Error actualizando resumen de parking {parking_id}, tipo {sensor_type}: {e}")


# ============================================================================
# ENDPOINTS DASHBOARD Y ESTADÍSTICAS
# ============================================================================

@api_bp.route('/sensors/stats', methods=['GET'])
@token_required
def get_sensor_stats():
    """
    Endpoint para obtener estadísticas generales de sensores para dashboard
    """
    session = Session()
    try:
        # Estadísticas básicas
        total_sensors = session.query(IndividualSensor).filter_by(is_active=True).count()
        
        # Distribución por estados
        status_query = session.query(
            SensorCurrentStatus.current_status,
            func.count(SensorCurrentStatus.sensor_id)
        ).join(
            IndividualSensor, 
            IndividualSensor.id == SensorCurrentStatus.sensor_id
        ).filter(
            IndividualSensor.is_active == True
        ).group_by(SensorCurrentStatus.current_status).all()
        
        status_distribution = {status: count for status, count in status_query}
        
        # Distribución por tipos
        type_query = session.query(
            IndividualSensor.sensor_type,
            func.count(IndividualSensor.id)
        ).filter(
            IndividualSensor.is_active == True
        ).group_by(IndividualSensor.sensor_type).all()
        
        type_distribution = {sensor_type: count for sensor_type, count in type_query}
        
        # Sensores con batería baja
        low_battery_count = session.query(SensorCurrentStatus).join(
            IndividualSensor,
            IndividualSensor.id == SensorCurrentStatus.sensor_id
        ).filter(
            IndividualSensor.is_active == True,
            SensorCurrentStatus.battery_capacity < 20
        ).count()
        
        # Sensores por parking
        parking_stats = session.query(
            Parking.id,
            Parking.name,
            func.count(IndividualSensor.id).label('sensor_count')
        ).outerjoin(
            IndividualSensor,
            Parking.id == IndividualSensor.parking_id
        ).filter(
            IndividualSensor.is_active == True
        ).group_by(Parking.id, Parking.name).all()
        
        parking_distribution = {
            parking.name: parking.sensor_count 
            for parking in parking_stats 
            if parking.sensor_count > 0
        }
        
        # Métricas de salud
        error_sensors = status_distribution.get('error', 0) + status_distribution.get('unknown', 0)
        health_percentage = ((total_sensors - error_sensors) / total_sensors * 100) if total_sensors > 0 else 100
        
        # Tasa de ocupación
        busy_sensors = status_distribution.get('busy', 0)
        occupancy_rate = (busy_sensors / total_sensors * 100) if total_sensors > 0 else 0
        
        return jsonify({
            'total_sensors': total_sensors,
            'status_distribution': status_distribution,
            'type_distribution': type_distribution,
            'parking_distribution': parking_distribution,
            'low_battery_count': low_battery_count,
            'health_percentage': round(health_percentage, 1),
            'occupancy_rate': round(occupancy_rate, 1),
            'last_update': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de sensores: {str(e)}")
        return jsonify({'error': 'Error obteniendo estadísticas'}), 500
    finally:
        session.close()

@api_bp.route('/dashboard/complete', methods=['GET'])
@token_required
def get_complete_dashboard():
    """
    Endpoint para obtener datos completos del dashboard incluyendo parkings y sensores
    """
    session = Session()
    try:
        # Datos de parkings existentes
        parkings = session.query(Parking).all()
        parking_data = []
        
        for parking in parkings:
            # Contar paneles
            panels_count = session.query(Panel).filter_by(
                parking_id=parking.id,
                is_active=True
            ).count()
            
            # Contar sensores individuales
            sensors_count = session.query(IndividualSensor).filter_by(
                parking_id=parking.id,
                is_active=True
            ).count()
            
            # Estados de sensores
            sensor_states = session.query(
                SensorCurrentStatus.current_status,
                func.count(SensorCurrentStatus.sensor_id)
            ).join(
                IndividualSensor,
                IndividualSensor.id == SensorCurrentStatus.sensor_id
            ).filter(
                IndividualSensor.parking_id == parking.id,
                IndividualSensor.is_active == True
            ).group_by(SensorCurrentStatus.current_status).all()
            
            sensor_status_counts = {status: count for status, count in sensor_states}
            
            parking_data.append({
                'id': parking.id,
                'name': parking.name,
                'location': parking.location,
                'max_capacity': parking.max_capacity,
                'current_occupancy': parking.current_occupancy,
                'status': parking.status,
                'panels_count': panels_count,
                'sensors_count': sensors_count,
                'sensor_states': sensor_status_counts,
                'last_update': parking.last_update.isoformat() if parking.last_update else None
            })
        
        # Estadísticas generales de sensores (obtener directamente para evitar recursión)
        total_sensors_count = session.query(IndividualSensor).filter_by(is_active=True).count()
        
        # Resumen general del sistema
        total_parkings = len(parkings)
        total_panels = session.query(Panel).filter_by(is_active=True).count()
        
        return jsonify({
            'summary': {
                'total_parkings': total_parkings,
                'total_panels': total_panels,
                'total_sensors': total_sensors_count,
                'last_update': datetime.utcnow().isoformat()
            },
            'parkings': parking_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo datos completos del dashboard: {str(e)}")
        return jsonify({'error': 'Error obteniendo datos del dashboard'}), 500
    finally:
        session.close()

# Registrar el Blueprint con la aplicación
# ============================================================================
# NUEVO v4.3.0: ENDPOINTS PARA GESTIÓN DE VENTANAS (PANEL TIPO 4)
# ============================================================================

@api_bp.route('/v1/panels/<int:panel_id>/windows/<int:window_id>/assign', methods=['POST'])
@require_auth
@require_panel_access('panel_id')
def assign_parking_to_window(panel_id, window_id):
    """Asignar parking o grupo de sensores a una ventana (solo para paneles Tipo 3 y Tipo 4)"""
    try:
        req = request.get_json(force=True)
        parking_id = req.get('parking_id')
        sensor_type = req.get('sensor_type')  # None, 'PMR', 'Electrico', etc.
        texto_fijo_previo = req.get('texto_fijo_previo')  # Texto fijo previo para sensores
        color = req.get('color')  # Color para sensores (1=Rojo, 2=Verde, 3=Amarillo/Naranja, etc.)
        
        if not parking_id:
            return jsonify({'error': 'parking_id es requerido'}), 400
        
        session = Session()
        
        # Verificar que el panel existe
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        # Verificar que el panel es Tipo 3 o Tipo 4
        if panel.panel_type_id:
            panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
            if not panel_type or panel_type.windows_count not in [2, 16]:
                session.close()
                return jsonify({
                    'error': f'Esta operación solo está disponible para paneles Tipo 3 o Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"} (soporta {panel_type.windows_count if panel_type else 0} ventanas)'
                }), 400
            
            # Validar window_id según el tipo de panel
            if panel_type.windows_count == 2:
                # Tipo 3: solo ventanas 0 y 1
                if window_id < 0 or window_id > 1:
                    session.close()
                    return jsonify({'error': 'window_id debe ser 0 o 1 para paneles Tipo 3'}), 400
            elif panel_type.windows_count == 16:
                # Tipo 4: ventanas 0 a 15
                if window_id < 0 or window_id > 15:
                    session.close()
                    return jsonify({'error': 'window_id debe estar entre 0 y 15 para paneles Tipo 4'}), 400
        
        window_service = PanelWindowService(session)
        
        result = window_service.assign_parking_to_window(
            panel_id=panel_id,
            window_id=window_id,
            parking_id=parking_id,
            sensor_type=sensor_type,
            texto_fijo_previo=texto_fijo_previo,
            color=color
        )
        
        session.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error asignando parking a ventana: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/panels/<int:panel_id>/windows/<int:window_id>/unassign', methods=['DELETE'])
@require_auth
@require_panel_access('panel_id')
def unassign_parking_from_window(panel_id, window_id):
    """Eliminar asignación de parking/sensor de una ventana (solo para paneles Tipo 3 y Tipo 4)"""
    try:
        # Verificar que el panel existe
        session = Session()
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        # Verificar que el panel es Tipo 3 o Tipo 4
        if panel.panel_type_id:
            panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
            if not panel_type or panel_type.windows_count not in [2, 16]:
                session.close()
                return jsonify({
                    'error': f'Esta operación solo está disponible para paneles Tipo 3 o Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"} (soporta {panel_type.windows_count if panel_type else 0} ventanas)'
                }), 400
            
            # Validar window_id según el tipo de panel
            if panel_type.windows_count == 2:
                # Tipo 3: solo ventanas 0 y 1
                if window_id < 0 or window_id > 1:
                    session.close()
                    return jsonify({'error': 'window_id debe ser 0 o 1 para paneles Tipo 3'}), 400
            elif panel_type.windows_count == 16:
                # Tipo 4: ventanas 0 a 15
                if window_id < 0 or window_id > 15:
                    session.close()
                    return jsonify({'error': 'window_id debe estar entre 0 y 15 para paneles Tipo 4'}), 400
        
        req = request.get_json(force=True)
        parking_id = req.get('parking_id')
        sensor_type = req.get('sensor_type')  # None, 'PMR', 'Electrico', etc.
        
        if not parking_id:
            session.close()
            return jsonify({'error': 'parking_id es requerido'}), 400
        
        window_service = PanelWindowService(session)
        
        result = window_service.remove_window_assignment(
            panel_id=panel_id,
            window_id=window_id,
            parking_id=parking_id,
            sensor_type=sensor_type
        )
        
        session.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error eliminando asignación: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/panels/<int:panel_id>/windows', methods=['GET'])
@require_auth
@require_panel_access('panel_id')
def get_panel_windows(panel_id):
    """Obtener todas las asignaciones de ventanas de un panel"""
    try:
        session = Session()
        window_service = PanelWindowService(session)
        
        assignments = window_service.get_window_assignments(panel_id)
        
        session.close()
        return jsonify(assignments), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo ventanas del panel: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/parkings/<int:parking_id>/windows', methods=['GET'])
@require_auth
@require_parking_access('parking_id')
def get_parking_windows(parking_id):
    """Obtener todas las ventanas asignadas a un parking"""
    try:
        session = Session()
        window_service = PanelWindowService(session)
        
        windows = window_service.get_parking_windows(parking_id)
        
        session.close()
        return jsonify(windows), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo ventanas del parking: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/parkings/<int:parking_id>/sensor-types', methods=['GET'])
@require_auth
@require_parking_access('parking_id')
def get_parking_sensor_types(parking_id):
    """Obtener tipos de sensores disponibles en un parking"""
    try:
        session = Session()
        window_service = PanelWindowService(session)
        
        sensor_types = window_service.get_parking_sensor_types(parking_id)
        
        session.close()
        return jsonify({'sensor_types': sensor_types}), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo tipos de sensores: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/parkings/<int:parking_id>/panels/<int:panel_id>/windows/<int:window_id>/config', methods=['POST', 'PUT'])
@require_auth
@require_parking_access('parking_id')
def update_window_config(parking_id, panel_id, window_id):
    """Crear o actualizar configuración de rotación para una ventana (solo para paneles Tipo 4)
    
    Permite crear configuración aunque el panel no exista aún (para preparar configuración antes de crear el panel).
    Si el panel existe, debe ser Tipo 4.
    """
    try:
        session = Session()
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        
        # Si el panel existe, verificar que es Tipo 4
        if panel:
            if panel.parking_id != parking_id:
                session.close()
                return jsonify({'error': 'El panel no pertenece al parking especificado'}), 400
            
            if panel.panel_type_id:
                panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
                if not panel_type or panel_type.windows_count != 16:
                    session.close()
                    return jsonify({
                        'error': f'Esta operación solo está disponible para paneles Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"}'
                    }), 400
        # Si el panel no existe, permitir crear la configuración de todas formas
        # (se validará cuando se cree el panel que sea Tipo 4)
        
        req = request.get_json(force=True)
        
        # Validar window_id
        if window_id < 0 or window_id > 15:
            session.close()
            return jsonify({'error': 'window_id debe estar entre 0 y 15'}), 400
        
        # Validar rotation_order si se proporciona
        if 'rotation_order' in req:
            rotation_order = req['rotation_order']
            if not isinstance(rotation_order, list):
                return jsonify({'error': 'rotation_order debe ser una lista'}), 400
            
            # Validar que los porcentajes sumen 100
            total_percentage = sum(item.get('percentage', 0) for item in rotation_order if isinstance(item, dict))
            if abs(total_percentage - 100) > 0.01:  # Tolerancia para errores de punto flotante
                return jsonify({'error': f'Los porcentajes en rotation_order deben sumar 100, actual: {total_percentage}'}), 400
        
        # Obtener company_id
        user_data = request.user_data
        company_id = None
        
        # Si es superadmin, puede especificar company_id
        if user_data.get('role') == 'superadmin' and 'company_id' in req:
            company_id = req.get('company_id')
        
        # Si no se especifica company_id, obtenerlo del parking (a través de UserParking)
        if not company_id:
            user_parking = session.query(UserParking).filter(
                UserParking.parking_id == parking_id
            ).first()
            if user_parking:
                company_id = user_parking.user_id
        
        config = {
            'rotation_enabled': req.get('rotation_enabled', True),
            'rotation_order': req.get('rotation_order'),
            'refresh_time_seconds': req.get('refresh_time_seconds', 5),
            'company_id': company_id,
            'parking_status_config': req.get('parking_status_config')  # Configuración de colores y textos para estados
        }
        
        window_service = PanelWindowService(session)
        
        result = window_service.update_window_configuration(
            panel_id=panel_id,
            window_id=window_id,
            parking_id=parking_id,
            config=config
        )
        
        session.close()
        
        if result['success']:
            # Reiniciar el servicio de paneles para que cargue la nueva configuración
            try:
                import subprocess
                # Reiniciar el panel worker service si existe
                subprocess.run(['systemctl', 'restart', 'parking-panel-worker'], 
                             capture_output=True, timeout=5, check=False)
                logger.info("Servicio parking-panel-worker reiniciado después de actualizar configuración")
            except Exception as restart_error:
                logger.warning(f"No se pudo reiniciar el servicio parking-panel-worker: {restart_error}")
                # No fallar la operación si no se puede reiniciar el servicio
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error actualizando configuración de ventana: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/parkings/<int:parking_id>/panels/<int:panel_id>/windows/<int:window_id>/config', methods=['GET'])
@api_bp.route('/v1/parkings/<int:parking_id>/panels/0/windows/<int:window_id>/config', methods=['GET'])  # Ruta alternativa sin panel_id
@require_auth
@require_parking_access('parking_id')
def get_window_config(parking_id, panel_id, window_id):
    """Obtener configuración de rotación de una ventana (solo para paneles Tipo 4)
    
    Permite obtener configuración preparatoria si panel_id es 0.
    """
    try:
        session = Session()
        
        # Si panel_id es 0, es una configuración preparatoria (no requiere panel existente)
        if panel_id != 0:
            # Verificar que el panel es Tipo 4
            panel = session.query(Panel).filter(Panel.id == panel_id).first()
            if not panel:
                session.close()
                return jsonify({'error': 'Panel no encontrado'}), 404
            
            if panel.panel_type_id:
                panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
                if not panel_type or panel_type.windows_count != 16:
                    session.close()
                    return jsonify({
                        'error': f'Esta operación solo está disponible para paneles Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"}'
                    }), 400
        
        # Obtener company_id
        user_data = request.user_data
        company_id = None
        
        # Si es superadmin, puede especificar company_id
        if user_data.get('role') == 'superadmin':
            company_id = request.args.get('company_id', type=int)
        
        # Si no se especifica company_id, obtenerlo del parking (a través de UserParking)
        if not company_id:
            user_parking = session.query(UserParking).filter(
                UserParking.parking_id == parking_id
            ).first()
            if user_parking:
                company_id = user_parking.user_id
        
        window_service = PanelWindowService(session)
        
        config = window_service.get_window_configuration(
            panel_id=panel_id if panel_id != 0 else None,  # Pasar None si es 0
            window_id=window_id,
            parking_id=parking_id,
            company_id=company_id
        )
        
        session.close()
        
        if config:
            return jsonify(config), 200
        else:
            return jsonify({'error': 'Configuración no encontrada'}), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo configuración de ventana: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/panels/<int:panel_id>/windows/<int:window_id>/content', methods=['GET'])
@require_auth
@require_panel_access('panel_id')
def get_window_content(panel_id, window_id):
    """Obtener contenido actual para una ventana (según rotación) - solo para paneles Tipo 4"""
    try:
        session = Session()
        
        # Verificar que el panel es Tipo 4
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        if panel.panel_type_id:
            panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
            if not panel_type or panel_type.windows_count != 16:
                session.close()
                return jsonify({
                    'error': f'Esta operación solo está disponible para paneles Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"}'
                }), 400
        
        from panel_content_rotation_service import PanelContentRotationService
        rotation_service = PanelContentRotationService(session)
        
        content = rotation_service.get_content_for_window(
            panel_id=panel_id,
            window_id=window_id
        )
        
        # Obtener parking para message_type
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        parking = None
        if panel:
            parking = session.query(Parking).filter(Parking.id == panel.parking_id).first()
        
        message_type = parking.message_type if parking else 'ESTADO'
        
        if content:
            status_config = content.get('status_config')
            message, color = rotation_service.format_message_for_panel(
                content, 
                message_type,
                status_config
            )
            return jsonify({
                'success': True,
                'content': content,
                'message': message,
                'color': color,
                'message_type': message_type
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No hay contenido configurado para esta ventana'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo contenido de ventana: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/panels/<int:panel_id>/windows/<int:window_id>/next-changes', methods=['GET'])
@require_auth
@require_panel_access('panel_id')
def get_window_next_changes(panel_id, window_id):
    """Obtener próximos cambios programados para una ventana (solo para paneles Tipo 4)"""
    try:
        session = Session()
        
        # Verificar que el panel es Tipo 4
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        if panel.panel_type_id:
            panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
            if not panel_type or panel_type.windows_count != 16:
                session.close()
                return jsonify({
                    'error': f'Esta operación solo está disponible para paneles Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"}'
                }), 400
        
        from panel_type4_update_service import PanelType3And4UpdateService
        update_service = PanelType3And4UpdateService(session)
        
        changes = update_service.get_next_changes(panel_id, window_id)
        
        session.close()
        
        return jsonify({
            'success': True,
            'changes': [
                {
                    'time': change['time'].isoformat(),
                    'content_type': change['content_type'],
                    'sensor_type': change.get('sensor_type'),
                    'texto_fijo_previo': change.get('texto_fijo_previo'),
                    'duration_seconds': change['duration_seconds'],
                    'percentage': change['percentage']
                }
                for change in changes
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo próximos cambios: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/v1/panels/<int:panel_id>/update-type4', methods=['POST'])
@api_bp.route('/v1/panels/<int:panel_id>/update-type3', methods=['POST'])
@require_auth
@require_panel_access('panel_id')
def update_panel_type3_or_type4(panel_id):
    """Forzar actualización de un panel Tipo 3 o Tipo 4"""
    try:
        session = Session()
        
        # Verificar que el panel existe
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            session.close()
            return jsonify({'error': 'Panel no encontrado'}), 404
        
        if panel.panel_type_id:
            panel_type = session.query(PanelType).filter(PanelType.id == panel.panel_type_id).first()
            if not panel_type or panel_type.windows_count not in [2, 16]:
                session.close()
                return jsonify({
                    'error': f'Esta operación solo está disponible para paneles Tipo 3 o Tipo 4. El panel actual es Tipo {panel_type.id if panel_type else "desconocido"} (windows_count: {panel_type.windows_count if panel_type else "N/A"})'
                }), 400
        
        from panel_type4_update_service import PanelType3And4UpdateService
        update_service = PanelType3And4UpdateService(session)
        
        result = update_service.update_panel(panel_id)
        
        session.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error actualizando panel Tipo 4: {e}")
        return jsonify({'error': 'Internal server error'}), 500

app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=API_PORT, debug=False)
