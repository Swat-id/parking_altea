from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, Text, func
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
    parking = relationship('Parking', back_populates='accesses')
    
    # Relación con usuarios a través de tabla intermedia
    user_accesses = relationship('UserAccess', back_populates='access')

class Panel(Base):
    __tablename__ = 'panels'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
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

class ScheduledMessage(Base):
    __tablename__ = 'scheduled_messages'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    message = Column(Text, nullable=False)