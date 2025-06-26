#!/usr/bin/env python3
"""
Script para actualizar la base de datos con las nuevas tablas de la versión 2.3
- Tabla CameraLog para logs de cámaras
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from models import Base, CameraLog
    import config
    
    logger.info("🚀 Iniciando actualización de base de datos v2.3")
    logger.info("=" * 60)
    
    # Crear engine y sesión
    engine = create_engine(config.DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    logger.info("✅ Conectado a la base de datos")
    
    # Crear la nueva tabla CameraLog
    logger.info("📋 Creando tabla CameraLog...")
    try:
        CameraLog.__table__.create(engine, checkfirst=True)
        logger.info("✅ Tabla CameraLog creada correctamente")
    except Exception as e:
        logger.warning(f"⚠️  Advertencia al crear tabla CameraLog: {e}")
        # Verificar si ya existe
        try:
            result = session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'camera_logs')"))
            exists = result.scalar()
            if exists:
                logger.info("✅ Tabla CameraLog ya existe")
            else:
                logger.error(f"❌ Error: No se pudo crear la tabla CameraLog")
        except Exception as e2:
            logger.error(f"❌ Error verificando tabla CameraLog: {e2}")
    
    # Verificar que todas las tablas necesarias existen
    logger.info("🔍 Verificando tablas del sistema...")
    required_tables = [
        'parkings',
        'accesses', 
        'panels',
        'users',
        'occupancy_history',
        'camera_logs'
    ]
    
    for table in required_tables:
        try:
            result = session.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
            exists = result.scalar()
            if exists:
                logger.info(f"✅ Tabla {table} existe")
            else:
                logger.warning(f"⚠️  Tabla {table} no existe")
        except Exception as e:
            logger.error(f"❌ Error verificando tabla {table}: {e}")
    
    # Verificar columnas de la tabla CameraLog
    logger.info("🔍 Verificando columnas de CameraLog...")
    camera_log_columns = [
        'id', 'access_id', 'parking_id', 'camera_ip', 'camera_line', 'camera_name',
        'raw_message', 'vehicle_in', 'vehicle_out', 'previous_vehicle_in', 'previous_vehicle_out',
        'delta_in', 'delta_out', 'status', 'error_message', 'processing_time',
        'new_occupancy', 'occupancy_change', 'parking_status', 'received_at', 'processed_at'
    ]
    
    for column in camera_log_columns:
        try:
            result = session.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'camera_logs' AND column_name = '{column}'
                )
            """))
            exists = result.scalar()
            if exists:
                logger.info(f"✅ Columna {column} existe en camera_logs")
            else:
                logger.warning(f"⚠️  Columna {column} no existe en camera_logs")
        except Exception as e:
            logger.error(f"❌ Error verificando columna {column}: {e}")
    
    # Crear índices para mejorar rendimiento
    logger.info("📊 Creando índices para CameraLog...")
    try:
        # Índice por parking_id y fecha
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_camera_logs_parking_date 
            ON camera_logs (parking_id, received_at DESC)
        """))
        logger.info("✅ Índice por parking_id y fecha creado")
        
        # Índice por status
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_camera_logs_status 
            ON camera_logs (status)
        """))
        logger.info("✅ Índice por status creado")
        
        # Índice por camera_ip
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_camera_logs_ip 
            ON camera_logs (camera_ip)
        """))
        logger.info("✅ Índice por camera_ip creado")
        
    except Exception as e:
        logger.warning(f"⚠️  Advertencia al crear índices: {e}")
    
    session.commit()
    session.close()
    
    logger.info("=" * 60)
    logger.info("✅ Actualización de base de datos v2.3 completada")
    logger.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
except Exception as e:
    logger.error(f"❌ Error en la actualización: {e}")
    if 'session' in locals():
        session.rollback()
        session.close()
    sys.exit(1) 