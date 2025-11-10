"""
Servicio HTTP/REST para el Panel Protocol Service
Expone la funcionalidad del servicio a través de una API REST
"""

import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from functools import wraps

# Configurar logger primero
logger = logging.getLogger(__name__)

# Añadir el directorio src al path para importar auth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .panel_protocol_service import PanelProtocolService
from .constants import Color, FontSize, Effect, Alignment, DEFAULT_PORT

# Importar sistema de autenticación del backend
try:
    from auth import verify_token, require_auth as backend_require_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logger.warning("No se pudo importar auth.py, el servicio funcionará sin autenticación")

# Puerto por defecto para el servicio HTTP
PANEL_PROTOCOL_SERVICE_PORT = 7000


class PanelProtocolAPIServer:
    """
    Servidor HTTP/REST para el Panel Protocol Service.
    Expone la funcionalidad del servicio a través de endpoints REST.
    """
    
    def __init__(
        self,
        port: int = PANEL_PROTOCOL_SERVICE_PORT,
        host: str = '0.0.0.0',
        max_concurrent_tasks: int = 10,
        max_connections_per_panel: int = 5
    ):
        """
        Inicializa el servidor API.
        
        Args:
            port: Puerto donde escuchará el servidor (default: 7000)
            host: Host donde escuchará (default: 0.0.0.0)
            max_concurrent_tasks: Máximo de tareas concurrentes
            max_connections_per_panel: Máximo de conexiones por panel
        """
        self.port = port
        self.host = host
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Crear servicio de protocolo
        self.service = PanelProtocolService(
            max_concurrent_tasks=max_concurrent_tasks,
            max_connections_per_panel=max_connections_per_panel
        )
        
        # Event loop para operaciones asíncronas
        self.loop = None
        self.loop_thread = None
        
        # Configurar autenticación
        self.auth_available = AUTH_AVAILABLE
        
        # Configurar rutas
        self._setup_routes()
        
        auth_status = "con autenticación JWT" if self.auth_available else "sin autenticación"
        logger.info(f"PanelProtocolAPIServer inicializado en puerto {port} ({auth_status})")
    
    def _check_auth(self, f):
        """
        Decorador para verificar autenticación usando el mismo sistema JWT del backend.
        Usa los mismos usuarios y contraseñas de la base de datos.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.auth_available:
                # Si no hay sistema de autenticación disponible, permitir acceso
                return f(*args, **kwargs)
            
            # Obtener token del header Authorization
            token = None
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                # Modo sin login: asignar usuario superadmin por defecto (igual que el backend)
                try:
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
                except Exception as e:
                    logger.error(f"Error en autenticación por defecto: {e}")
                    return jsonify({"error": "Error de autenticación"}), 401
            else:
                # Verificar token JWT usando el mismo sistema del backend
                token_data = verify_token(token)
                if not token_data["success"]:
                    return jsonify({"error": token_data["error"]}), 401
                request.user_data = token_data["user_data"]
            
            return f(*args, **kwargs)
        return decorated_function
    
    def _setup_routes(self):
        """Configura las rutas de la API"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Endpoint de salud"""
            return jsonify({
                'status': 'ok',
                'service': 'panel-protocol-service',
                'version': '4.3.0',
                'port': self.port,
                'auth_enabled': self.auth_available
            })
        
        @self.app.route('/api/v1/auth/login', methods=['POST'])
        def login():
            """Endpoint de login - Usa el mismo sistema de autenticación del backend"""
            if not self.auth_available:
                return jsonify({'error': 'Autenticación no disponible'}), 503
            
            try:
                data = request.json
                email = data.get('email')
                password = data.get('password')
                
                if not email or not password:
                    return jsonify({'error': 'Email y contraseña son requeridos'}), 400
                
                # Usar el mismo sistema de autenticación del backend
                from sqlalchemy.orm import sessionmaker
                from config import DB_URL
                from sqlalchemy import create_engine
                from auth import authenticate_user
                
                engine = create_engine(DB_URL, echo=False)
                SessionLocal = sessionmaker(bind=engine)
                db_session = SessionLocal()
                
                try:
                    result = authenticate_user(db_session, email, password)
                    if not result['success']:
                        return jsonify({'error': result['error']}), 401
                    
                    return jsonify({
                        'success': True,
                        'token': result['token'],
                        'user': result['user']
                    })
                finally:
                    db_session.close()
                    
            except Exception as e:
                logger.error(f"Error en login: {e}")
                return jsonify({'error': 'Error interno del servidor'}), 500
        
        @self.app.route('/api/v1/auth/me', methods=['GET'])
        @self._check_auth
        def get_current_user():
            """Obtiene información del usuario autenticado"""
            if not self.auth_available:
                return jsonify({'error': 'Autenticación no disponible'}), 503
            
            user_data = getattr(request, 'user_data', None)
            if not user_data:
                return jsonify({'error': 'No autenticado'}), 401
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user_data.get('user_id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'role': user_data.get('role')
                }
            })
        
        @self.app.route('/api/v1/panels/create-window', methods=['POST'])
        @self._check_auth
        def create_window():
            """Crear ventanas en un panel"""
            try:
                data = request.json
                panel_ip = data.get('panel_ip')
                panel_port = data.get('panel_port', DEFAULT_PORT)
                windows = data.get('windows', [])
                card_id = data.get('card_id', 0xFF)
                wait_for_response = data.get('wait_for_response', False)
                
                if not panel_ip:
                    return jsonify({'error': 'panel_ip es requerido'}), 400
                
                if not windows:
                    return jsonify({'error': 'windows es requerido'}), 400
                
                # Convertir windows a tuplas
                windows_tuples = [
                    (w['x'], w['y'], w['width'], w['height'])
                    for w in windows
                ]
                
                # Ejecutar operación asíncrona
                task_id = asyncio.run_coroutine_threadsafe(
                    self.service.create_window(
                        panel_ip=panel_ip,
                        panel_port=panel_port,
                        windows=windows_tuples,
                        card_id=card_id,
                        wait_for_response=wait_for_response
                    ),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Ventana creada' if not wait_for_response else 'Ventana creada y confirmada'
                })
                
            except Exception as e:
                logger.error(f"Error creando ventana: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/panels/send-text', methods=['POST'])
        @self._check_auth
        def send_text():
            """Enviar texto a un panel"""
            try:
                data = request.json
                panel_ip = data.get('panel_ip')
                panel_port = data.get('panel_port', DEFAULT_PORT)
                window_id = data.get('window_id', 0)
                text = data.get('text', '')
                color = data.get('color', Color.GREEN)
                font_size = data.get('font_size', FontSize.SIZE_16)
                effect = data.get('effect', Effect.DRAW)
                alignment = data.get('alignment', Alignment.CENTER_CENTER)
                speed = data.get('speed', 0x00)
                stay_time = data.get('stay_time', 3)
                card_id = data.get('card_id', 0xFF)
                wait_for_response = data.get('wait_for_response', False)
                
                if not panel_ip:
                    return jsonify({'error': 'panel_ip es requerido'}), 400
                
                if not text:
                    return jsonify({'error': 'text es requerido'}), 400
                
                # Ejecutar operación asíncrona
                task_id = asyncio.run_coroutine_threadsafe(
                    self.service.send_text(
                        panel_ip=panel_ip,
                        panel_port=panel_port,
                        window_id=window_id,
                        text=text,
                        color=color,
                        font_size=font_size,
                        effect=effect,
                        alignment=alignment,
                        speed=speed,
                        stay_time=stay_time,
                        card_id=card_id,
                        wait_for_response=wait_for_response
                    ),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Texto enviado' if not wait_for_response else 'Texto enviado y confirmado'
                })
                
            except Exception as e:
                logger.error(f"Error enviando texto: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/panels/send-image', methods=['POST'])
        @self._check_auth
        def send_image():
            """Enviar imagen a un panel"""
            try:
                data = request.json
                panel_ip = data.get('panel_ip')
                panel_port = data.get('panel_port', DEFAULT_PORT)
                window_id = data.get('window_id', 0)
                filename = data.get('filename', '')
                draw_mode = data.get('draw_mode', 0x00)
                speed = data.get('speed', 0x01)
                stay_time = data.get('stay_time', 3)
                x = data.get('x', 0)
                y = data.get('y', 0)
                card_id = data.get('card_id', 0xFF)
                wait_for_response = data.get('wait_for_response', False)
                
                if not panel_ip:
                    return jsonify({'error': 'panel_ip es requerido'}), 400
                
                if not filename:
                    return jsonify({'error': 'filename es requerido'}), 400
                
                # Ejecutar operación asíncrona
                task_id = asyncio.run_coroutine_threadsafe(
                    self.service.send_image(
                        panel_ip=panel_ip,
                        panel_port=panel_port,
                        window_id=window_id,
                        filename=filename,
                        draw_mode=draw_mode,
                        speed=speed,
                        stay_time=stay_time,
                        x=x,
                        y=y,
                        card_id=card_id,
                        wait_for_response=wait_for_response
                    ),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Imagen enviada' if not wait_for_response else 'Imagen enviada y confirmada'
                })
                
            except Exception as e:
                logger.error(f"Error enviando imagen: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/tasks/<task_id>', methods=['GET'])
        def get_task_result(task_id):
            """Obtener resultado de una tarea"""
            try:
                timeout = request.args.get('timeout', type=float)
                
                result = asyncio.run_coroutine_threadsafe(
                    self.service.get_task_result(task_id, timeout=timeout),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'result': result
                })
                
            except asyncio.TimeoutError:
                return jsonify({'error': 'Timeout esperando resultado'}), 408
            except KeyError:
                return jsonify({'error': 'Tarea no encontrada'}), 404
            except Exception as e:
                logger.error(f"Error obteniendo resultado: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/tasks/<task_id>/status', methods=['GET'])
        def get_task_status(task_id):
            """Obtener estado de una tarea"""
            try:
                status = asyncio.run_coroutine_threadsafe(
                    self.service.get_task_status(task_id),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'status': status
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estado: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/panels/<panel_ip>/results', methods=['GET'])
        def get_panel_results(panel_ip):
            """Obtener resultados de un panel"""
            try:
                panel_port = request.args.get('port', type=int, default=DEFAULT_PORT)
                limit = request.args.get('limit', type=int)
                since_str = request.args.get('since')
                
                since = None
                if since_str:
                    since = datetime.fromisoformat(since_str)
                
                results = asyncio.run_coroutine_threadsafe(
                    self.service.get_panel_results(
                        panel_ip=panel_ip,
                        panel_port=panel_port,
                        limit=limit,
                        since=since
                    ),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'panel_ip': panel_ip,
                    'panel_port': panel_port,
                    'results': [r.to_dict() for r in results]
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo resultados: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/panels/<panel_ip>/statistics', methods=['GET'])
        def get_panel_statistics(panel_ip):
            """Obtener estadísticas de un panel"""
            try:
                panel_port = request.args.get('port', type=int, default=DEFAULT_PORT)
                since_str = request.args.get('since')
                
                since = None
                if since_str:
                    since = datetime.fromisoformat(since_str)
                
                stats = asyncio.run_coroutine_threadsafe(
                    self.service.get_panel_success_rate(
                        panel_ip=panel_ip,
                        panel_port=panel_port,
                        since=since
                    ),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'panel_ip': panel_ip,
                    'panel_port': panel_port,
                    'statistics': stats
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/statistics', methods=['GET'])
        def get_statistics():
            """Obtener estadísticas generales"""
            try:
                stats = asyncio.run_coroutine_threadsafe(
                    self.service.get_statistics(),
                    self.loop
                ).result()
                
                return jsonify({
                    'success': True,
                    'statistics': stats
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _run_event_loop(self):
        """Ejecuta el event loop en un thread separado"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def start(self):
        """Inicia el servidor"""
        # Iniciar event loop en thread separado
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()
        
        # Esperar a que el loop esté listo
        import time
        while self.loop is None:
            time.sleep(0.1)
        
        logger.info(f"Iniciando PanelProtocolAPIServer en {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
    
    def stop(self):
        """Detiene el servidor"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        asyncio.run_coroutine_threadsafe(
            self.service.close(),
            self.loop
        ).result()
        
        logger.info("PanelProtocolAPIServer detenido")


if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y ejecutar servidor
    server = PanelProtocolAPIServer(port=PANEL_PROTOCOL_SERVICE_PORT)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

