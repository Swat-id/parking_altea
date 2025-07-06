import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from sqlalchemy.orm import Session
from models import User, UserParking, UserPanel, UserAccess, Parking, Panel, Access

# Configuración JWT
JWT_SECRET = "parking_altea_secret_key_2025"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(db_session: Session, name: str, email: str, password: str, role: str = 'user') -> dict:
    """Crea un nuevo usuario con rol"""
    try:
        # Verificar si el email ya existe
        existing_user = db_session.query(User).filter(User.email == email).first()
        if existing_user:
            return {"success": False, "error": "El email ya está registrado"}
        
        # Validar rol
        allowed_roles = ['superadmin', 'user']
        if role not in allowed_roles:
            return {"success": False, "error": f"Rol no permitido: {role}"}
        
        # Crear nuevo usuario
        password_hash = hash_password(password)
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role
        )
        
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        
        return {
            "success": True,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "created_at": new_user.created_at.isoformat()
            }
        }
    except Exception as e:
        db_session.rollback()
        return {"success": False, "error": str(e)}

def authenticate_user(db_session: Session, email: str, password: str) -> dict:
    """Autentica un usuario y devuelve un token JWT con rol"""
    try:
        user = db_session.query(User).filter(User.email == email, User.is_active == True).first()
        
        if not user:
            return {"success": False, "error": "Usuario no encontrado"}
        
        if not verify_password(password, user.password_hash):
            return {"success": False, "error": "Contraseña incorrecta"}
        
        # Generar token JWT con rol
        payload = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_token(token: str) -> dict:
    """Verifica un token JWT y devuelve la información del usuario"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"success": True, "user_data": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "error": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"success": False, "error": "Token inválido"}

def get_user_from_token(db_session: Session, token: str) -> User:
    """Obtiene el usuario desde el token JWT"""
    token_data = verify_token(token)
    if not token_data["success"]:
        return None
    
    user_id = token_data["user_data"]["user_id"]
    return db_session.query(User).filter(User.id == user_id, User.is_active == True).first()

def delete_user(db_session: Session, user_id: int) -> dict:
    """Elimina un usuario (desactiva en lugar de borrar físicamente)"""
    try:
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "Usuario no encontrado"}
        
        user.is_active = False
        db_session.commit()
        
        return {"success": True, "message": "Usuario eliminado correctamente"}
    except Exception as e:
        db_session.rollback()
        return {"success": False, "error": str(e)}

def change_password(db_session: Session, user_id: int, current_password: str, new_password: str) -> dict:
    """Cambia la contraseña de un usuario"""
    try:
        user = db_session.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return {"success": False, "error": "Usuario no encontrado"}
        
        if not verify_password(current_password, user.password_hash):
            return {"success": False, "error": "Contraseña actual incorrecta"}
        
        user.password_hash = hash_password(new_password)
        db_session.commit()
        
        return {"success": True, "message": "Contraseña cambiada correctamente"}
    except Exception as e:
        db_session.rollback()
        return {"success": False, "error": str(e)}

def get_user_permissions(db_session: Session, user_id: int) -> dict:
    """Obtiene los parkings, paneles y cámaras a los que tiene acceso un usuario"""
    try:
        # Obtener parkings del usuario
        user_parkings = db_session.query(UserParking).filter(UserParking.user_id == user_id).all()
        parking_ids = [up.parking_id for up in user_parkings]
        
        # Obtener paneles del usuario
        user_panels = db_session.query(UserPanel).filter(UserPanel.user_id == user_id).all()
        panel_ids = [up.panel_id for up in user_panels]
        
        # Obtener cámaras del usuario
        user_accesses = db_session.query(UserAccess).filter(UserAccess.user_id == user_id).all()
        access_ids = [ua.access_id for ua in user_accesses]
        
        return {
            "success": True,
            "permissions": {
                "parking_ids": parking_ids,
                "panel_ids": panel_ids,
                "access_ids": access_ids
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def assign_user_to_resources(db_session: Session, user_id: int, parking_ids: list = None, 
                           panel_ids: list = None, access_ids: list = None) -> dict:
    """Asigna recursos (parkings, paneles, cámaras) a un usuario"""
    try:
        # Asignar parkings
        if parking_ids:
            for parking_id in parking_ids:
                existing = db_session.query(UserParking).filter(
                    UserParking.user_id == user_id,
                    UserParking.parking_id == parking_id
                ).first()
                if not existing:
                    user_parking = UserParking(user_id=user_id, parking_id=parking_id)
                    db_session.add(user_parking)
        
        # Asignar paneles
        if panel_ids:
            for panel_id in panel_ids:
                existing = db_session.query(UserPanel).filter(
                    UserPanel.user_id == user_id,
                    UserPanel.panel_id == panel_id
                ).first()
                if not existing:
                    user_panel = UserPanel(user_id=user_id, panel_id=panel_id)
                    db_session.add(user_panel)
        
        # Asignar cámaras
        if access_ids:
            for access_id in access_ids:
                existing = db_session.query(UserAccess).filter(
                    UserAccess.user_id == user_id,
                    UserAccess.access_id == access_id
                ).first()
                if not existing:
                    user_access = UserAccess(user_id=user_id, access_id=access_id)
                    db_session.add(user_access)
        
        db_session.commit()
        return {"success": True, "message": "Recursos asignados correctamente"}
    except Exception as e:
        db_session.rollback()
        return {"success": False, "error": str(e)}

# Decorador para proteger endpoints
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # Obtener token del header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            # Modo sin login: asignar usuario superadmin por defecto
            from models import User
            from sqlalchemy.orm import sessionmaker
            from config import DB_URL
            from sqlalchemy import create_engine
            engine = create_engine(DB_URL, echo=False)
            SessionLocal = sessionmaker(bind=engine)
            db_session = SessionLocal()
            user = db_session.query(User).filter(User.email == 'info@swat-id.com').first()
            db_session.close()
            if not user:
                return jsonify({"error": "Usuario superadmin info@swat-id.com no existe"}), 401
            request.user_data = {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
            return f(*args, **kwargs)

        # Verificar token normalmente
        token_data = verify_token(token)
        if not token_data["success"]:
            return jsonify({"error": token_data["error"]}), 401
        request.user_data = token_data["user_data"]
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir rol superadmin
def require_superadmin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primero verificar autenticación
        auth_result = require_auth(lambda: None)()
        if hasattr(auth_result, 'status_code') and auth_result.status_code == 401:
            return auth_result
        
        # Verificar que el usuario es superadmin
        user_role = request.user_data.get('role')
        if user_role != 'superadmin':
            return jsonify({"error": "Acceso denegado: se requiere rol superadmin"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir acceso a un parking específico
def require_parking_access(parking_id_param='pid'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Primero verificar autenticación
            auth_result = require_auth(lambda: None)()
            if hasattr(auth_result, 'status_code') and auth_result.status_code == 401:
                return auth_result
            
            user_id = request.user_data.get('user_id')
            user_role = request.user_data.get('role')
            
            # Superadmin tiene acceso a todos los parkings
            if user_role == 'superadmin':
                return f(*args, **kwargs)
            
            # Obtener el parking_id del parámetro de la URL
            parking_id = kwargs.get(parking_id_param)
            if not parking_id:
                return jsonify({"error": f"Parámetro {parking_id_param} no encontrado"}), 400
            
            # Verificar si el usuario tiene acceso al parking
            from sqlalchemy.orm import sessionmaker
            from config import DB_URL
            from sqlalchemy import create_engine
            engine = create_engine(DB_URL, echo=False)
            SessionLocal = sessionmaker(bind=engine)
            db_session = SessionLocal()
            
            try:
                # Verificar si existe la asignación
                user_parking = db_session.query(UserParking).filter(
                    UserParking.user_id == user_id,
                    UserParking.parking_id == parking_id
                ).first()
                
                if not user_parking:
                    return jsonify({"error": "Acceso denegado: no tienes permisos para este parking"}), 403
                
                return f(*args, **kwargs)
            finally:
                db_session.close()
        
        return decorated_function
    return decorator

# Decorador para requerir acceso a un panel específico
def require_panel_access(panel_id_param='panel_id'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Primero verificar autenticación
            auth_result = require_auth(lambda: None)()
            if hasattr(auth_result, 'status_code') and auth_result.status_code == 401:
                return auth_result
            
            user_id = request.user_data.get('user_id')
            user_role = request.user_data.get('role')
            
            # Superadmin tiene acceso a todos los paneles
            if user_role == 'superadmin':
                return f(*args, **kwargs)
            
            # Obtener el panel_id del parámetro de la URL
            panel_id = kwargs.get(panel_id_param)
            if not panel_id:
                return jsonify({"error": f"Parámetro {panel_id_param} no encontrado"}), 400
            
            # Verificar si el usuario tiene acceso al panel
            from sqlalchemy.orm import sessionmaker
            from config import DB_URL
            from sqlalchemy import create_engine
            engine = create_engine(DB_URL, echo=False)
            SessionLocal = sessionmaker(bind=engine)
            db_session = SessionLocal()
            
            try:
                # Verificar si existe la asignación
                user_panel = db_session.query(UserPanel).filter(
                    UserPanel.user_id == user_id,
                    UserPanel.panel_id == panel_id
                ).first()
                
                if not user_panel:
                    return jsonify({"error": "Acceso denegado: no tienes permisos para este panel"}), 403
                
                return f(*args, **kwargs)
            finally:
                db_session.close()
        
        return decorated_function
    return decorator 