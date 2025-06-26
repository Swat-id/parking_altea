import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps
from sqlalchemy.orm import Session
from models import User, UserParking, UserPanel, Parking, Panel
from config import DB_URL
from sqlalchemy import create_engine

engine = create_engine(DB_URL)

# Configuración JWT (en producción usar una clave secreta segura)
JWT_SECRET_KEY = "parking_altea_secret_key_2025"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def hash_password(password):
    """Genera un hash de la contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password, password_hash):
    """Verifica si la contraseña coincide con el hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_token(user_id):
    """Genera un token JWT para el usuario"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Obtener token del header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'message': 'Token requerido'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token inválido o expirado'}), 401
        
        # Agregar user_id al request para uso posterior
        request.user_id = payload['user_id']
        return f(*args, **kwargs)
    
    return decorated

def get_user_by_id(user_id):
    """Obtiene un usuario por su ID"""
    with Session(engine) as session:
        return session.query(User).filter(User.id == user_id).first()

def get_user_by_email(email):
    """Obtiene un usuario por su email"""
    with Session(engine) as session:
        return session.query(User).filter(User.email == email).first()

def create_user(name, email, password):
    """Crea un nuevo usuario"""
    with Session(engine) as session:
        # Verificar si el email ya existe
        existing_user = get_user_by_email(email)
        if existing_user:
            return None, "El email ya está registrado"
        
        # Crear nuevo usuario
        password_hash = hash_password(password)
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        return new_user, None

def authenticate_user(email, password):
    """Autentica un usuario con email y contraseña"""
    user = get_user_by_email(email)
    if not user:
        return None
    
    if verify_password(password, user.password_hash):
        return user
    
    return None

def get_user_parkings(user_id):
    """Obtiene todos los parkings asociados a un usuario"""
    with Session(engine) as session:
        user_parkings = session.query(UserParking).filter(UserParking.user_id == user_id).all()
        parking_ids = [up.parking_id for up in user_parkings]
        return session.query(Parking).filter(Parking.id.in_(parking_ids)).all()

def get_user_panels(user_id):
    """Obtiene todos los paneles asociados a un usuario"""
    with Session(engine) as session:
        user_panels = session.query(UserPanel).filter(UserPanel.user_id == user_id).all()
        panel_ids = [up.panel_id for up in user_panels]
        return session.query(Panel).filter(Panel.id.in_(panel_ids)).all()

def assign_parking_to_user(user_id, parking_id):
    """Asigna un parking a un usuario"""
    with Session(engine) as session:
        # Verificar si la asignación ya existe
        existing = session.query(UserParking).filter(
            UserParking.user_id == user_id,
            UserParking.parking_id == parking_id
        ).first()
        
        if existing:
            return False, "El parking ya está asignado a este usuario"
        
        # Verificar que el parking existe
        parking = session.query(Parking).filter(Parking.id == parking_id).first()
        if not parking:
            return False, "El parking no existe"
        
        # Crear la asignación
        user_parking = UserParking(
            user_id=user_id,
            parking_id=parking_id
        )
        
        session.add(user_parking)
        session.commit()
        return True, None

def assign_panel_to_user(user_id, panel_id):
    """Asigna un panel a un usuario"""
    with Session(engine) as session:
        # Verificar si la asignación ya existe
        existing = session.query(UserPanel).filter(
            UserPanel.user_id == user_id,
            UserPanel.panel_id == panel_id
        ).first()
        
        if existing:
            return False, "El panel ya está asignado a este usuario"
        
        # Verificar que el panel existe
        panel = session.query(Panel).filter(Panel.id == panel_id).first()
        if not panel:
            return False, "El panel no existe"
        
        # Crear la asignación
        user_panel = UserPanel(
            user_id=user_id,
            panel_id=panel_id
        )
        
        session.add(user_panel)
        session.commit()
        return True, None 