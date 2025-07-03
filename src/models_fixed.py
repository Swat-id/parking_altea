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
    panel_display_text = Column(Text)
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
    ip = Column(String, nullable=False)
    name = Column(String)
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

# Tablas para estadísticas
class ParkingStatistics(Base):
    __tablename__ = 'parking_statistics'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    total_vehicles_in = Column(Integer, default=0)
    total_vehicles_out = Column(Integer, default=0)
    max_occupancy = Column(Integer, default=0)
    avg_occupancy = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Tablas para logs de cámaras
class CameraLog(Base):
    __tablename__ = 'camera_logs'
    id = Column(Integer, primary_key=True)
    access_id = Column(Integer, ForeignKey('accesses.id'))
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    camera_ip = Column(String, nullable=False)
    camera_line = Column(Integer, nullable=False)
    camera_name = Column(String)
    raw_message = Column(Text)
    vehicle_in = Column(Integer)
    vehicle_out = Column(Integer)
    previous_vehicle_in = Column(Integer)
    previous_vehicle_out = Column(Integer)
    delta_in = Column(Integer)
    delta_out = Column(Integer)
    status = Column(String, nullable=False)
    error_message = Column(Text)
    processing_time = Column(Float)
    new_occupancy = Column(Integer)
    occupancy_change = Column(Integer)
    parking_status = Column(String)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

# Clases adicionales necesarias para api_server.py
class OccupancyHistory(Base):
    __tablename__ = 'occupancy_history'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    occupancy = Column(Integer, nullable=False)
    source = Column(String)  # Fuente de los datos (camera, manual, etc.)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ScheduledMessage(Base):
    __tablename__ = 'scheduled_messages'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    message = Column(Text, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class PanelMessageLog(Base):
    __tablename__ = 'panel_message_logs'
    id = Column(Integer, primary_key=True)
    panel_id = Column(Integer, ForeignKey('panels.id'), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default='SENT')  # SENT, FAILED
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class VehicleCount(Base):
    __tablename__ = 'vehicle_counts'
    id = Column(Integer, primary_key=True)
    access_id = Column(Integer, ForeignKey('accesses.id'), nullable=False)
    count_in = Column(Integer, default=0)
    count_out = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class PanelSchedule(Base):
    __tablename__ = 'panel_schedules'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    monday = Column(Boolean, default=False)
    tuesday = Column(Boolean, default=False)
    wednesday = Column(Boolean, default=False)
    thursday = Column(Boolean, default=False)
    friday = Column(Boolean, default=False)
    saturday = Column(Boolean, default=False)
    sunday = Column(Boolean, default=False)
    message = Column(Text, nullable=False)
    color = Column(Integer, default=2)
    font_size = Column(Integer, default=2)
    effect = Column(String, default='static')
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class PanelScheduleLog(Base):
    __tablename__ = 'panel_schedule_logs'
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('panel_schedules.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    execution_type = Column(String, nullable=False)
    message_sent = Column(Text)
    panels_affected = Column(Integer, default=0)
    executed_at = Column(DateTime(timezone=True), server_default=func.now()) 