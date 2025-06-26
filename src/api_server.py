from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base, Parking, ScheduledMessage, OccupancyHistory, User, UserParking, UserPanel, Panel
from auth import (
    create_user, authenticate_user, generate_token, token_required, 
    get_user_by_id, get_user_parkings, get_user_panels,
    assign_parking_to_user, assign_panel_to_user
)
from datetime import datetime

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# ============================================================================
# RUTAS DE AUTENTICACIÓN Y GESTIÓN DE USUARIOS
# ============================================================================

@app.route('/auth/register', methods=['POST'])
def register():
    """Crear un nuevo usuario"""
    try:
        data = request.get_json(force=True)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not all([name, email, password]):
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        user, error = create_user(name, email, password)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Autenticar usuario y obtener token"""
    try:
        data = request.get_json(force=True)
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400
        
        user = authenticate_user(email, password)
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Login exitoso',
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """Obtener perfil del usuario autenticado"""
    try:
        user = get_user_by_id(request.user_id)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    """Eliminar un usuario (solo el propio usuario puede eliminarse)"""
    try:
        if request.user_id != user_id:
            return jsonify({'error': 'No autorizado para eliminar este usuario'}), 403
        
        session = Session()
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Eliminar asignaciones de parkings y paneles
        session.query(UserParking).filter(UserParking.user_id == user_id).delete()
        session.query(UserPanel).filter(UserPanel.user_id == user_id).delete()
        
        # Eliminar usuario
        session.delete(user)
        session.commit()
        session.close()
        
        return jsonify({'message': 'Usuario eliminado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/users/<int:user_id>/parkings', methods=['GET'])
@token_required
def get_user_parkings_route(user_id):
    """Obtener parkings asignados a un usuario"""
    try:
        if request.user_id != user_id:
            return jsonify({'error': 'No autorizado para ver estos parkings'}), 403
        
        parkings = get_user_parkings(user_id)
        data = [{
            'id': p.id,
            'name': p.name,
            'location': p.location,
            'max_capacity': p.max_capacity,
            'current_occupancy': p.current_occupancy,
            'status': p.status
        } for p in parkings]
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/users/<int:user_id>/panels', methods=['GET'])
@token_required
def get_user_panels_route(user_id):
    """Obtener paneles asignados a un usuario"""
    try:
        if request.user_id != user_id:
            return jsonify({'error': 'No autorizado para ver estos paneles'}), 403
        
        panels = get_user_panels(user_id)
        data = [{
            'id': p.id,
            'name': p.name,
            'ip': p.ip,
            'parking_id': p.parking_id
        } for p in panels]
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/assign/parking', methods=['POST'])
@token_required
def assign_parking():
    """Asignar un parking a un usuario"""
    try:
        data = request.get_json(force=True)
        user_id = data.get('user_id')
        parking_id = data.get('parking_id')
        
        if not all([user_id, parking_id]):
            return jsonify({'error': 'user_id y parking_id son requeridos'}), 400
        
        # Solo el propio usuario puede asignarse parkings
        if request.user_id != user_id:
            return jsonify({'error': 'No autorizado para asignar parkings a otros usuarios'}), 403
        
        success, error = assign_parking_to_user(user_id, parking_id)
        if not success:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Parking asignado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/assign/panel', methods=['POST'])
@token_required
def assign_panel():
    """Asignar un panel a un usuario"""
    try:
        data = request.get_json(force=True)
        user_id = data.get('user_id')
        panel_id = data.get('panel_id')
        
        if not all([user_id, panel_id]):
            return jsonify({'error': 'user_id y panel_id son requeridos'}), 400
        
        # Solo el propio usuario puede asignarse paneles
        if request.user_id != user_id:
            return jsonify({'error': 'No autorizado para asignar paneles a otros usuarios'}), 403
        
        success, error = assign_panel_to_user(user_id, panel_id)
        if not success:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Panel asignado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# RUTAS EXISTENTES (PROTEGIDAS)
# ============================================================================

@app.route('/parkings', methods=['GET'])
@token_required
def list_parkings():
    """Listar parkings (solo los asignados al usuario)"""
    try:
        user_parkings = get_user_parkings(request.user_id)
        data = [{
            'id': p.id,
            'name': p.name,
            'location': p.location,
            'max_capacity': p.max_capacity,
            'current_occupancy': p.current_occupancy,
            'status': p.status
        } for p in user_parkings]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/parking/<int:pid>', methods=['GET'])
@token_required
def get_parking(pid):
    """Obtener información de un parking específico (solo si está asignado al usuario)"""
    try:
        user_parkings = get_user_parkings(request.user_id)
        parking_ids = [p.id for p in user_parkings]
        
        if pid not in parking_ids:
            return jsonify({'error': 'No autorizado para acceder a este parking'}), 403
        
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Not found'}), 404
        
        data = {
            'id': p.id,
            'name': p.name,
            'max_capacity': p.max_capacity,
            'current_occupancy': p.current_occupancy,
            'free_spaces': p.max_capacity - p.current_occupancy,
            'status': p.status
        }
        session.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/parking/<int:pid>/occupancy', methods=['POST'])
@token_required
def set_occupancy(pid):
    """Establecer ocupación de un parking (solo si está asignado al usuario)"""
    try:
        user_parkings = get_user_parkings(request.user_id)
        parking_ids = [p.id for p in user_parkings]
        
        if pid not in parking_ids:
            return jsonify({'error': 'No autorizado para modificar este parking'}), 403
        
        req = request.get_json(force=True)
        new_occ = req.get('occupancy')
        session = Session()
        p = session.query(Parking).get(pid)
        if not p:
            session.close()
            return jsonify({'error':'Not found'}), 404
        
        p.current_occupancy = max(0, min(new_occ, p.max_capacity))
        p.status = 'LIBRE'
        # opcional: ajustar status
        hist = OccupancyHistory(parking_id=pid, occupancy=p.current_occupancy, source='manual')
        session.add(hist)
        session.commit()
        session.close()
        return jsonify({'status':'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/parking/<int:pid>/message', methods=['POST'])
@token_required
def schedule_message(pid):
    """Programar mensaje para un parking (solo si está asignado al usuario)"""
    try:
        user_parkings = get_user_parkings(request.user_id)
        parking_ids = [p.id for p in user_parkings]
        
        if pid not in parking_ids:
            return jsonify({'error': 'No autorizado para programar mensajes en este parking'}), 403
        
        req = request.get_json(force=True)
        start = datetime.fromisoformat(req.get('start'))
        end = datetime.fromisoformat(req.get('end'))
        text = req.get('message')
        session = Session()
        msg = ScheduledMessage(parking_id=pid, start_time=start, end_time=end, message=text)
        session.add(msg)
        session.commit()
        session.close()
        return jsonify({'status':'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT)