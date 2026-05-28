"""
Módulo centralizado de conexión a base de datos.
Gestiona el pool de conexiones y proporciona sesiones reutilizables.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
import os

logger = logging.getLogger(__name__)

# Configuración del pool de conexiones
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # 30 minutos
POOL_PRE_PING = True  # Verifica conexión antes de usar

_engine = None
_SessionFactory = None
_ScopedSession = None


def get_db_url():
    """Obtiene la URL de la base de datos desde config."""
    try:
        from config import DB_URL
        return DB_URL
    except ImportError:
        return os.getenv('DATABASE_URL', 'postgresql://parking_user:parking_pass@localhost:5432/parking_db')


def get_engine():
    """
    Retorna el engine singleton con pool de conexiones configurado.
    """
    global _engine
    if _engine is None:
        db_url = get_db_url()
        _engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=POOL_PRE_PING,
            echo=False
        )
        
        # Log de conexiones para debug
        @event.listens_for(_engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            logger.debug(f"Nueva conexión DB creada: {connection_record}")
        
        @event.listens_for(_engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug(f"Conexión obtenida del pool: {connection_record}")
        
        @event.listens_for(_engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            logger.debug(f"Conexión devuelta al pool: {connection_record}")
        
        logger.info(f"Engine creado - Pool size: {POOL_SIZE}, Max overflow: {MAX_OVERFLOW}")
    
    return _engine


def get_session_factory():
    """
    Retorna la fábrica de sesiones singleton.
    """
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory


def get_scoped_session():
    """
    Retorna una sesión con scope (thread-safe).
    Útil para aplicaciones multi-threaded.
    """
    global _ScopedSession
    if _ScopedSession is None:
        _ScopedSession = scoped_session(get_session_factory())
    return _ScopedSession


@contextmanager
def get_db_session():
    """
    Context manager para obtener una sesión de base de datos.
    Garantiza que la sesión se cierre correctamente.
    
    Uso:
        with get_db_session() as session:
            result = session.query(Model).all()
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error en sesión DB: {e}")
        raise
    finally:
        session.close()


@contextmanager
def get_db_session_no_commit():
    """
    Context manager para sesiones de solo lectura (sin commit automático).
    
    Uso:
        with get_db_session_no_commit() as session:
            result = session.query(Model).all()
    """
    session = get_session_factory()()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Error en sesión DB: {e}")
        raise
    finally:
        session.close()


def get_pool_status():
    """
    Retorna el estado actual del pool de conexiones.
    """
    engine = get_engine()
    pool = engine.pool
    return {
        'pool_size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'invalid': pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 'N/A'
    }


def dispose_engine():
    """
    Cierra todas las conexiones del pool.
    Útil para reiniciar el pool o al cerrar la aplicación.
    """
    global _engine, _SessionFactory, _ScopedSession
    if _engine is not None:
        _engine.dispose()
        logger.info("Engine disposed - todas las conexiones cerradas")
    _engine = None
    _SessionFactory = None
    _ScopedSession = None


def check_connection():
    """
    Verifica que la conexión a la base de datos funciona.
    """
    try:
        with get_db_session_no_commit() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error verificando conexión DB: {e}")
        return False
