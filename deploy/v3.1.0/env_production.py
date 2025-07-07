# Configuración de Entorno de Producción v3.1.0 - Parking Altea
# Autor: Sistema de Despliegue
# Fecha: 2025-01-07

import os

class ProductionConfig:
    """Configuración para entorno de producción"""
    
    # Configuración básica
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'parking-altea-prod-secret-key-v3.1.0'
    
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://parking:parking123@localhost/parking_altea'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'parking-altea-jwt-secret-v3.1.0'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hora
    JWT_REFRESH_TOKEN_EXPIRES = 86400  # 24 horas
    
    # Configuración de logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/opt/parking_altea/logs/api.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Configuración de servidor
    HOST = '127.0.0.1'
    PORT = 5000
    WORKERS = 4
    
    # Configuración de seguridad
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de CORS
    CORS_ORIGINS = [
        'http://157.180.91.63',
        'https://157.180.91.63',
        'http://localhost',
        'http://127.0.0.1'
    ]
    
    # Configuración de rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per minute'
    RATELIMIT_HEADERS_ENABLED = True
    
    # Configuración de caché
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configuración de archivos
    UPLOAD_FOLDER = '/opt/parking_altea/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Configuración de email (si se implementa en el futuro)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configuración de monitoreo
    ENABLE_METRICS = True
    METRICS_PORT = 9090
    
    # Configuración específica de la aplicación
    PARKING_SYSTEM_VERSION = 'v3.1.0'
    MAX_PARKINGS_PER_USER = 50
    MAX_PANELS_PER_PARKING = 10
    CAMERA_TIMEOUT = 30  # segundos
    SCHEDULE_CHECK_INTERVAL = 60  # segundos
    
    # Configuración de backup
    BACKUP_ENABLED = True
    BACKUP_DIR = '/opt/backups/parking_altea'
    BACKUP_RETENTION_DAYS = 30
    
    # Configuración de notificaciones
    ENABLE_NOTIFICATIONS = True
    NOTIFICATION_WEBHOOK_URL = os.environ.get('NOTIFICATION_WEBHOOK_URL')
    
    @staticmethod
    def init_app(app):
        """Inicializar configuración específica de la aplicación"""
        
        # Crear directorios necesarios
        import os
        os.makedirs('/opt/parking_altea/logs', exist_ok=True)
        os.makedirs('/opt/parking_altea/uploads', exist_ok=True)
        os.makedirs('/opt/parking_altea/data', exist_ok=True)
        os.makedirs('/opt/backups/parking_altea', exist_ok=True)
        
        # Configurar logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_FILE,
                maxBytes=ProductionConfig.LOG_MAX_BYTES,
                backupCount=ProductionConfig.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Parking Altea startup')

class DevelopmentConfig:
    """Configuración para entorno de desarrollo"""
    
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'dev-secret-key'
    
    SQLALCHEMY_DATABASE_URI = 'postgresql://parking:parking123@localhost/parking_altea_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    JWT_SECRET_KEY = 'dev-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas para desarrollo
    
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = 'logs/api_dev.log'
    
    HOST = '127.0.0.1'
    PORT = 5000
    WORKERS = 1
    
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    RATELIMIT_ENABLED = False
    CACHE_TYPE = 'null'
    
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    ENABLE_METRICS = False
    BACKUP_ENABLED = False
    ENABLE_NOTIFICATIONS = False

class TestingConfig:
    """Configuración para entorno de testing"""
    
    DEBUG = False
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    
    SQLALCHEMY_DATABASE_URI = 'postgresql://parking:parking123@localhost/parking_altea_test'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    LOG_LEVEL = 'WARNING'
    LOG_FILE = 'logs/api_test.log'
    
    HOST = '127.0.0.1'
    PORT = 5001
    WORKERS = 1
    
    CORS_ORIGINS = []
    
    RATELIMIT_ENABLED = False
    CACHE_TYPE = 'null'
    
    UPLOAD_FOLDER = 'test_uploads'
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    
    ENABLE_METRICS = False
    BACKUP_ENABLED = False
    ENABLE_NOTIFICATIONS = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 