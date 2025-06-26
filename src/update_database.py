#!/usr/bin/env python3
"""
Script para actualizar la base de datos con las nuevas tablas de estadísticas
"""

import config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingStatistics, DailyStatistics, ActivityLog, PanelMessageLog, VehicleCount
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """Actualizar la base de datos con las nuevas tablas"""
    try:
        # Crear engine y sesión
        engine = create_engine(config.DB_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("Conectando a la base de datos...")
        
        # Crear las nuevas tablas
        logger.info("Creando nuevas tablas de estadísticas...")
        Base.metadata.create_all(engine)
        
        # Verificar que las tablas se crearon correctamente
        inspector = engine.dialect.inspector(engine)
        existing_tables = inspector.get_table_names()
        
        new_tables = [
            'parking_statistics',
            'daily_statistics', 
            'activity_logs',
            'panel_message_logs',
            'vehicle_counts'
        ]
        
        for table in new_tables:
            if table in existing_tables:
                logger.info(f"✅ Tabla {table} creada correctamente")
            else:
                logger.error(f"❌ Error: Tabla {table} no se creó")
        
        # Actualizar tabla de paneles con nuevos campos si no existen
        logger.info("Actualizando tabla de paneles...")
        try:
            # Verificar si los campos ya existen
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'panels' 
                AND column_name IN ('status', 'last_message', 'last_update')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'status' not in existing_columns:
                session.execute(text("ALTER TABLE panels ADD COLUMN status VARCHAR DEFAULT 'OFFLINE'"))
                logger.info("✅ Campo 'status' añadido a tabla panels")
            
            if 'last_message' not in existing_columns:
                session.execute(text("ALTER TABLE panels ADD COLUMN last_message TEXT"))
                logger.info("✅ Campo 'last_message' añadido a tabla panels")
            
            if 'last_update' not in existing_columns:
                session.execute(text("ALTER TABLE panels ADD COLUMN last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                logger.info("✅ Campo 'last_update' añadido a tabla panels")
                
        except Exception as e:
            logger.warning(f"Advertencia al actualizar tabla panels: {e}")
        
        # Actualizar tabla de occupancy_history con nuevos campos
        logger.info("Actualizando tabla de occupancy_history...")
        try:
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'occupancy_history' 
                AND column_name IN ('previous_occupancy', 'change_amount')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'previous_occupancy' not in existing_columns:
                session.execute(text("ALTER TABLE occupancy_history ADD COLUMN previous_occupancy INTEGER"))
                logger.info("✅ Campo 'previous_occupancy' añadido a tabla occupancy_history")
            
            if 'change_amount' not in existing_columns:
                session.execute(text("ALTER TABLE occupancy_history ADD COLUMN change_amount INTEGER"))
                logger.info("✅ Campo 'change_amount' añadido a tabla occupancy_history")
                
        except Exception as e:
            logger.warning(f"Advertencia al actualizar tabla occupancy_history: {e}")
        
        # Crear índices para mejorar rendimiento
        logger.info("Creando índices para optimizar consultas...")
        try:
            # Índices para parking_statistics
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_parking_statistics_parking_date 
                ON parking_statistics(parking_id, date)
            """))
            
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_parking_statistics_date_hour 
                ON parking_statistics(date, hour)
            """))
            
            # Índices para daily_statistics
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_daily_statistics_parking_date 
                ON daily_statistics(parking_id, date)
            """))
            
            # Índices para activity_logs
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp 
                ON activity_logs(timestamp)
            """))
            
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_activity_logs_user_action 
                ON activity_logs(user_id, action_type)
            """))
            
            # Índices para vehicle_counts
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vehicle_counts_parking_timestamp 
                ON vehicle_counts(parking_id, timestamp)
            """))
            
            logger.info("✅ Índices creados correctamente")
            
        except Exception as e:
            logger.warning(f"Advertencia al crear índices: {e}")
        
        # Commit de los cambios
        session.commit()
        session.close()
        
        logger.info("🎉 Base de datos actualizada correctamente")
        logger.info("Nuevas tablas disponibles:")
        for table in new_tables:
            logger.info(f"  - {table}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando la base de datos: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def populate_sample_data():
    """Poblar datos de ejemplo para las nuevas tablas"""
    try:
        engine = create_engine(config.DB_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("Poblando datos de ejemplo...")
        
        # Obtener parkings existentes
        from models import Parking
        parkings = session.query(Parking).all()
        
        if not parkings:
            logger.warning("No hay parkings en la base de datos")
            return False
        
        # Crear algunos registros de ejemplo para estadísticas
        from datetime import datetime, timedelta
        import random
        
        # Datos de ejemplo para las últimas 7 días
        for parking in parkings:
            for days_ago in range(7):
                date = datetime.now() - timedelta(days=days_ago)
                
                # Estadísticas por hora
                for hour in range(24):
                    # Simular datos realistas
                    avg_occupancy = random.randint(20, 80)
                    max_occupancy = min(avg_occupancy + random.randint(10, 30), parking.max_capacity)
                    min_occupancy = max(avg_occupancy - random.randint(10, 30), 0)
                    
                    # Determinar estado predominante
                    if avg_occupancy < parking.threshold_dense:
                        time_libre = 60
                        time_denso = 0
                        time_completo = 0
                    elif avg_occupancy < parking.threshold_full:
                        time_libre = 0
                        time_denso = 60
                        time_completo = 0
                    else:
                        time_libre = 0
                        time_denso = 0
                        time_completo = 60
                    
                    # Crear registro de estadísticas por hora
                    hourly_stats = ParkingStatistics(
                        parking_id=parking.id,
                        date=date.replace(hour=0, minute=0, second=0, microsecond=0),
                        hour=hour,
                        avg_occupancy=avg_occupancy,
                        max_occupancy=max_occupancy,
                        min_occupancy=min_occupancy,
                        total_vehicles_in=random.randint(5, 25),
                        total_vehicles_out=random.randint(5, 25),
                        time_libre=time_libre,
                        time_denso=time_denso,
                        time_completo=time_completo
                    )
                    session.add(hourly_stats)
                
                # Estadísticas diarias
                daily_avg = random.randint(30, 70)
                daily_max = min(daily_avg + random.randint(20, 40), parking.max_capacity)
                daily_min = max(daily_avg - random.randint(20, 40), 0)
                
                daily_stats = DailyStatistics(
                    parking_id=parking.id,
                    date=date.replace(hour=0, minute=0, second=0, microsecond=0),
                    avg_occupancy=daily_avg,
                    max_occupancy=daily_max,
                    min_occupancy=daily_min,
                    peak_hour=random.randint(10, 18),
                    total_vehicles_in=random.randint(100, 500),
                    total_vehicles_out=random.randint(100, 500),
                    time_libre=random.randint(200, 800),
                    time_denso=random.randint(100, 600),
                    time_completo=random.randint(0, 300)
                )
                session.add(daily_stats)
        
        # Commit de los datos de ejemplo
        session.commit()
        session.close()
        
        logger.info("✅ Datos de ejemplo creados correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando datos de ejemplo: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    print("🔄 Actualizando base de datos Parking Altea...")
    print("=" * 50)
    
    if update_database():
        print("\n📊 ¿Deseas crear datos de ejemplo para las estadísticas? (s/n): ", end="")
        response = input().lower().strip()
        
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            if populate_sample_data():
                print("✅ Base de datos actualizada y poblada con datos de ejemplo")
            else:
                print("⚠️  Base de datos actualizada pero error al crear datos de ejemplo")
        else:
            print("✅ Base de datos actualizada correctamente")
    else:
        print("❌ Error actualizando la base de datos")
        exit(1) 