from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, Text, func, Float
)
from sqlalchemy.orm import relationship, declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones con tablas intermedias
    user_parkings = relationship('UserParking', back_populates='user')
    user_panels = relationship('UserPanel', back_populates='user')
    user_accesses = relationship('UserAccess', back_populates='user')

class Parking(Base):
    __tablename__ = 'parkings'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String)
    max_capacity = Column(Integer, nullable=False)
    threshold_dense = Column(Integer, nullable=False)
    threshold_full = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, default=0, nullable=False)
    status = Column(String, default='LIBRE', nullable=False)
    fixed_message_flag = Column(Boolean, default=False, nullable=False)
    accesses = relationship('Access', back_populates='parking')
    panels = relationship('Panel', back_populates='parking')
    
    # Relación con usuarios a través de tabla intermedia
    user_parkings = relationship('UserParking', back_populates='parking')

class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    ip = Column(String, nullable=False)
    line = Column(Integer, nullable=False)
    name = Column(String)
    last_vehicle_in = Column(Integer, default=0, nullable=False)
    last_vehicle_out = Column(Integer, default=0, nullable=False)
    status = Column(String, default='OFFLINE', nullable=False)  # ONLINE, OFFLINE
    last_message_received = Column(DateTime(timezone=True))  # Último mensaje recibido
    last_ping_check = Column(DateTime(timezone=True))  # Última verificación por ping
    ping_status = Column(String, default='UNKNOWN')  # ONLINE, OFFLINE, UNKNOWN
    parking = relationship('Parking', back_populates='accesses')
    
    # Relación con usuarios a través de tabla intermedia
    user_accesses = relationship('UserAccess', back_populates='access')

class Panel(Base):
    __tablename__ = 'panels'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    status = Column(String, default='OFFLINE', nullable=False)  # ONLINE, OFFLINE
    last_message = Column(Text)
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    parking = relationship('Parking', back_populates='panels')
    
    # Relación con usuarios a través de tabla intermedia
    user_panels = relationship('UserPanel', back_populates='panel')

# Tablas intermedias para relaciones muchos a muchos
class UserParking(Base):
    __tablename__ = 'user_parkings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship('User', back_populates='user_parkings')
    parking = relationship('Parking', back_populates='user_parkings')

class UserPanel(Base):
    __tablename__ = 'user_panels'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    panel_id = Column(Integer, ForeignKey('panels.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship('User', back_populates='user_panels')
    panel = relationship('Panel', back_populates='user_panels')

class UserAccess(Base):
    __tablename__ = 'user_accesses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_id = Column(Integer, ForeignKey('accesses.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship('User', back_populates='user_accesses')
    access = relationship('Access', back_populates='user_accesses')

class OccupancyHistory(Base):
    __tablename__ = 'occupancy_history'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    occupancy = Column(Integer, nullable=False)
    source = Column(String, nullable=False)  # 'camera', 'manual', 'scheduled_adjust'
    previous_occupancy = Column(Integer)  # Para tracking de cambios
    change_amount = Column(Integer)  # Diferencia con ocupación anterior

class ScheduledMessage(Base):
    __tablename__ = 'scheduled_messages'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    message = Column(Text, nullable=False)

# Nuevas tablas para estadísticas y logs
class ParkingStatistics(Base):
    __tablename__ = 'parking_statistics'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)  # Fecha del día
    hour = Column(Integer, nullable=False)  # Hora (0-23)
    
    # Métricas de ocupación
    avg_occupancy = Column(Float, nullable=False)  # Ocupación promedio
    max_occupancy = Column(Integer, nullable=False)  # Ocupación máxima
    min_occupancy = Column(Integer, nullable=False)  # Ocupación mínima
    total_vehicles_in = Column(Integer, default=0)  # Total vehículos entrantes
    total_vehicles_out = Column(Integer, default=0)  # Total vehículos salientes
    
    # Estados del parking
    time_libre = Column(Integer, default=0)  # Minutos en estado LIBRE
    time_denso = Column(Integer, default=0)  # Minutos en estado DENSO
    time_completo = Column(Integer, default=0)  # Minutos en estado COMPLETO
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DailyStatistics(Base):
    __tablename__ = 'daily_statistics'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)  # Solo fecha (sin hora)
    
    # Métricas diarias
    avg_occupancy = Column(Float, nullable=False)
    max_occupancy = Column(Integer, nullable=False)
    min_occupancy = Column(Integer, nullable=False)
    peak_hour = Column(Integer)  # Hora de máxima ocupación
    total_vehicles_in = Column(Integer, default=0)
    total_vehicles_out = Column(Integer, default=0)
    
    # Estados del parking
    time_libre = Column(Integer, default=0)  # Minutos en estado LIBRE
    time_denso = Column(Integer, default=0)  # Minutos en estado DENSO
    time_completo = Column(Integer, default=0)  # Minutos en estado COMPLETO
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Puede ser null para acciones automáticas
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=True)
    panel_id = Column(Integer, ForeignKey('panels.id'), nullable=True)
    
    action_type = Column(String, nullable=False)  # 'occupancy_update', 'message_sent', 'config_change', 'login', etc.
    action_details = Column(Text)  # Detalles de la acción en JSON
    ip_address = Column(String)  # IP del usuario que realizó la acción
    user_agent = Column(String)  # User agent del navegador
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship('User')
    parking = relationship('Parking')
    panel = relationship('Panel')

class PanelMessageLog(Base):
    __tablename__ = 'panel_message_logs'
    id = Column(Integer, primary_key=True)
    panel_id = Column(Integer, ForeignKey('panels.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    message = Column(Text, nullable=False)
    duration = Column(Integer, nullable=False)  # Duración en segundos
    status = Column(String, nullable=False)  # 'sent', 'delivered', 'failed'
    response_time = Column(Float)  # Tiempo de respuesta en ms
    
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    panel = relationship('Panel')
    parking = relationship('Parking')
    user = relationship('User')

class VehicleCount(Base):
    __tablename__ = 'vehicle_counts'
    id = Column(Integer, primary_key=True)
    access_id = Column(Integer, ForeignKey('accesses.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    vehicles_in = Column(Integer, default=0)  # Vehículos entrantes en este conteo
    vehicles_out = Column(Integer, default=0)  # Vehículos salientes en este conteo
    total_vehicles_in = Column(Integer, default=0)  # Total acumulado entrantes
    total_vehicles_out = Column(Integer, default=0)  # Total acumulado salientes
    
    # Relaciones
    access = relationship('Access')
    parking = relationship('Parking')

class CameraLog(Base):
    __tablename__ = 'camera_logs'
    id = Column(Integer, primary_key=True)
    
    # Información de la cámara
    access_id = Column(Integer, ForeignKey('accesses.id'), nullable=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    camera_ip = Column(String, nullable=False)
    camera_line = Column(Integer, nullable=False)
    camera_name = Column(String)
    
    # Datos del mensaje
    raw_message = Column(Text)  # Mensaje JSON completo recibido
    vehicle_in = Column(Integer)
    vehicle_out = Column(Integer)
    previous_vehicle_in = Column(Integer)
    previous_vehicle_out = Column(Integer)
    delta_in = Column(Integer)
    delta_out = Column(Integer)
    
    # Estado del procesamiento
    status = Column(String, nullable=False)  # 'processed', 'discarded', 'error'
    error_message = Column(Text)  # Mensaje de error si aplica
    processing_time = Column(Float)  # Tiempo de procesamiento en ms
    
    # Resultado
    new_occupancy = Column(Integer)
    occupancy_change = Column(Integer)
    parking_status = Column(String)  # Estado final del parking
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relaciones
    access = relationship('Access')
    parking = relationship('Parking')