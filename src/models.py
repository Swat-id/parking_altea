from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, Text, func, Float, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), default='user', nullable=False)  # NUEVO: Campo para roles
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # NUEVO: Campo para auditoría
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones con tablas intermedias
    user_parkings = relationship('UserParking', back_populates='user')
    user_panels = relationship('UserPanel', back_populates='user')
    user_accesses = relationship('UserAccess', back_populates='user')
    
    # Relaciones con sistema de alarmas
    alarm_configurations = relationship('AlarmConfiguration', back_populates='user')
    alarms = relationship('Alarm', back_populates='user')
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role='{self.role}')>"
    
    @property
    def is_superadmin(self):
        """Verificar si el usuario es superadmin"""
        return self.role == 'superadmin'
    
    @property
    def is_regular_user(self):
        """Verificar si el usuario es usuario regular"""
        return self.role == 'user'

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
    message_type = Column(String(20), default='ESTADO', nullable=False)  # 'ESTADO', 'PLAZAS_LIBRES'
    # Relación muchos a muchos con cámaras a través de tabla intermedia
    camera_parkings = relationship('CameraParking', back_populates='parking')
    panels = relationship('Panel', back_populates='parking')
    
    # Relación con usuarios a través de tabla intermedia
    user_parkings = relationship('UserParking', back_populates='parking')
    
    # NUEVA: Relación muchos a muchos con cámaras
    camera_parkings = relationship('CameraParking', back_populates='parking')
    
    # NUEVO v4.1.0: Relaciones con sensores individuales
    individual_sensors = relationship('IndividualSensor', back_populates='parking')
    sensor_summaries = relationship('ParkingSensorSummary', back_populates='parking')
    
    # NUEVO v4.3.0: Relaciones con ventanas de paneles
    panel_windows = relationship('ParkingPanelWindow', back_populates='parking')
    window_configurations = relationship('PanelWindowConfiguration', back_populates='parking')

class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True)
    # QUITADO: parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    ip = Column(String, nullable=False)
    line = Column(Integer, nullable=False)
    name = Column(String)
    last_vehicle_in = Column(Integer, default=0, nullable=False)
    last_vehicle_out = Column(Integer, default=0, nullable=False)
    status = Column(String, default='OFFLINE', nullable=False)  # ONLINE, OFFLINE
    last_message_received = Column(DateTime(timezone=True))  # Último mensaje recibido
    last_ping_check = Column(DateTime(timezone=True))  # Última verificación por ping
    ping_status = Column(String, default='UNKNOWN')  # ONLINE, OFFLINE, UNKNOWN
    
    # QUITADO: parking = relationship('Parking', back_populates='accesses')
    
    # NUEVA: Relación muchos a muchos con parkings
    camera_parkings = relationship('CameraParking', back_populates='camera')
    
    # Relación con usuarios a través de tabla intermedia
    user_accesses = relationship('UserAccess', back_populates='access')

# NUEVA: Tabla intermedia para relación muchos a muchos entre cámaras y parkings
class CameraParking(Base):
    __tablename__ = 'camera_parkings'
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('accesses.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    camera = relationship('Access', back_populates='camera_parkings')
    parking = relationship('Parking', back_populates='camera_parkings')
    
    # Índice único para evitar duplicados
    __table_args__ = (UniqueConstraint('camera_id', 'parking_id'),)

class Panel(Base):
    __tablename__ = 'panels'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    status = Column(String, default='OFFLINE', nullable=False)  # ONLINE, OFFLINE
    last_message = Column(Text)
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    
    # Nuevos campos para tipos de paneles
    panel_type_id = Column(Integer, ForeignKey('panel_types.id'), nullable=True)
    port = Column(Integer, default=5200)
    window_config = Column(JSON)  # Configuración de ventanas en JSON
    protocol_version = Column(String(20), default='old')  # 'old', 'new'
    service_endpoint = Column(String(255))  # URL del servicio a usar
    is_active = Column(Boolean, default=True)
    last_protocol_check = Column(DateTime(timezone=True))
    protocol_status = Column(String(20), default='unknown')  # 'online', 'offline', 'unknown'
    
    # NUEVOS CAMPOS v4.1.0: Soporte para ventanas múltiples
    last_message_window_0 = Column(Text)  # Último mensaje enviado a ventana 0
    last_message_window_1 = Column(Text)  # Último mensaje enviado a ventana 1
    last_update_window_0 = Column(DateTime(timezone=True))  # Última actualización ventana 0
    last_update_window_1 = Column(DateTime(timezone=True))  # Última actualización ventana 1
    window_config_json = Column(JSON)  # Configuración detallada de ventanas
    
    # NUEVO v4.3.0: Campo para soportar hasta 16 ventanas
    windows_count = Column(Integer, default=1)  # Número de ventanas soportadas (1-16)
    
    # Relaciones
    parking = relationship('Parking', back_populates='panels')
    panel_type = relationship('PanelType', back_populates='panels')
    user_panels = relationship('UserPanel', back_populates='panel')
    
    # NUEVO v4.3.0: Relaciones con ventanas
    window_assignments = relationship('ParkingPanelWindow', back_populates='panel', cascade='all, delete-orphan')
    window_configurations = relationship('PanelWindowConfiguration', back_populates='panel', cascade='all, delete-orphan')
    
    def supports_multiple_windows(self):
        """Verificar si el panel soporta múltiples ventanas (Tipo 3)"""
        if self.panel_type and hasattr(self.panel_type, 'windows_count'):
            return self.panel_type.windows_count > 1
        return False
    
    def get_window_config(self):
        """Obtener configuración de ventanas del panel"""
        if self.window_config_json:
            return self.window_config_json
        # Configuración por defecto
        return {
            "windows": [
                {"id": 0, "enabled": True},
                {"id": 1, "enabled": self.supports_multiple_windows()}
            ]
        }
    
    def get_last_message_for_window(self, window_id):
        """Obtener último mensaje para una ventana específica"""
        if window_id == 0:
            return self.last_message_window_0
        elif window_id == 1:
            return self.last_message_window_1
        return None
    
    def get_last_update_for_window(self, window_id):
        """Obtener última actualización para una ventana específica"""
        if window_id == 0:
            return self.last_update_window_0
        elif window_id == 1:
            return self.last_update_window_1
        return None

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
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=True)  # Nullable para relación muchos a muchos
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

class PanelSchedule(Base):
    __tablename__ = 'panel_schedules'
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Información básica
    name = Column(String, nullable=False)  # Nombre de la programación
    description = Column(Text)  # Descripción opcional
    
    # Fechas de vigencia
    start_date = Column(DateTime(timezone=True), nullable=False)  # Fecha de inicio
    end_date = Column(DateTime(timezone=True), nullable=False)  # Fecha de fin
    
    # Horario diario
    start_time = Column(String, nullable=False)  # Hora de inicio (HH:MM)
    end_time = Column(String, nullable=False)  # Hora de fin (HH:MM)
    
    # Días de la semana (0=domingo, 1=lunes, ..., 6=sábado)
    monday = Column(Boolean, default=False)
    tuesday = Column(Boolean, default=False)
    wednesday = Column(Boolean, default=False)
    thursday = Column(Boolean, default=False)
    friday = Column(Boolean, default=False)
    saturday = Column(Boolean, default=False)
    sunday = Column(Boolean, default=False)
    
    # Configuración del mensaje
    message = Column(Text, nullable=False)  # Texto a mostrar
    color = Column(Integer, default=2)  # Color del texto (1=Rojo, 2=Verde, 3=Amarillo, etc.)
    font_size = Column(Integer, default=2)  # Tamaño de fuente
    effect = Column(String, default='static')  # 'static', 'scroll_left', 'scroll_right', 'center'
    
    # Estado de la programación
    is_active = Column(Boolean, default=True)  # Programación activa/inactiva
    priority = Column(Integer, default=1)  # Prioridad (1=baja, 5=alta)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    parking = relationship('Parking')
    user = relationship('User')

class PanelScheduleLog(Base):
    __tablename__ = 'panel_schedule_logs'
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('panel_schedules.id'), nullable=False)
    parking_id = Column(Integer, ForeignKey('parkings.id'), nullable=False)
    
    # Información de ejecución
    execution_type = Column(String, nullable=False)  # 'started', 'ended', 'skipped', 'error'
    message_sent = Column(Text)  # Mensaje enviado
    panels_affected = Column(Integer, default=0)  # Número de paneles afectados
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    schedule = relationship('PanelSchedule')
    parking = relationship('Parking')

# Nuevas tablas para fabricantes y tipos de paneles
class Manufacturer(Base):
    __tablename__ = 'manufacturers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    website = Column(String(255))
    contact_email = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    panel_types = relationship('PanelType', back_populates='manufacturer')

class PanelType(Base):
    __tablename__ = 'panel_types'
    id = Column(Integer, primary_key=True)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    protocol_type = Column(String(50), nullable=False)  # 'old', 'new'
    windows_count = Column(Integer, nullable=False, default=1)
    window_width = Column(Integer, nullable=False)  # Ancho de cada ventana
    window_height = Column(Integer, nullable=False)  # Alto de cada ventana
    total_width = Column(Integer, nullable=False)  # Ancho total del panel
    total_height = Column(Integer, nullable=False)  # Alto total del panel
    port = Column(Integer, nullable=False, default=5200)
    service_endpoint = Column(String(255))  # URL del servicio a usar
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    manufacturer = relationship('Manufacturer', back_populates='panel_types')
    panels = relationship('Panel', back_populates='panel_type')
    
    def __repr__(self):
        return f"<PanelType(id={self.id}, name='{self.name}', protocol_type='{self.protocol_type}')>"

# ============================================================================
# MODELOS DEL SISTEMA DE ALARMAS v3.2.0_alarms
# ============================================================================

class AlarmConfiguration(Base):
    """Configuración de alarmas por usuario"""
    __tablename__ = 'alarm_configurations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    alarm_type = Column(String(50), nullable=False)  # 'panel', 'camera', 'parking'
    status = Column(String(20), default='active', nullable=False)  # 'active', 'paused'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    user = relationship('User', back_populates='alarm_configurations')
    targets = relationship('AlarmConfigurationTarget', back_populates='configuration', cascade='all, delete-orphan')
    thresholds = relationship('AlarmConfigurationThreshold', back_populates='configuration', cascade='all, delete-orphan')
    alarms = relationship('Alarm', back_populates='configuration')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='unique_user_alarm_name'),
    )
    
    def __repr__(self):
        return f"<AlarmConfiguration(id={self.id}, name='{self.name}', type='{self.alarm_type}')>"

class AlarmConfigurationTarget(Base):
    """Objetivos de una configuración de alarma (paneles, cámaras, aparcamientos)"""
    __tablename__ = 'alarm_configuration_targets'
    
    id = Column(Integer, primary_key=True)
    alarm_configuration_id = Column(Integer, ForeignKey('alarm_configurations.id', ondelete='CASCADE'), nullable=False)
    target_type = Column(String(50), nullable=False)  # 'panel', 'camera', 'parking'
    target_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    configuration = relationship('AlarmConfiguration', back_populates='targets')
    
    def __repr__(self):
        return f"<AlarmConfigurationTarget(id={self.id}, type='{self.target_type}', target_id={self.target_id})>"

class AlarmConfigurationThreshold(Base):
    """Umbrales de una configuración de alarma por gravedad"""
    __tablename__ = 'alarm_configuration_thresholds'
    
    id = Column(Integer, primary_key=True)
    alarm_configuration_id = Column(Integer, ForeignKey('alarm_configurations.id', ondelete='CASCADE'), nullable=False)
    severity = Column(String(20), nullable=False)  # 'LEVE', 'NORMAL', 'GRAVE'
    threshold_value = Column(Integer, nullable=False)  # minutos para desconexión o % para ocupación
    threshold_type = Column(String(50), nullable=False)  # 'disconnection_time', 'occupancy_high', 'occupancy_low'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    configuration = relationship('AlarmConfiguration', back_populates='thresholds')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('alarm_configuration_id', 'severity', name='unique_config_severity'),
    )
    
    def __repr__(self):
        return f"<AlarmConfigurationThreshold(id={self.id}, severity='{self.severity}', value={self.threshold_value})>"

class Alarm(Base):
    """Alarmas generadas por el sistema"""
    __tablename__ = 'alarms'
    
    id = Column(Integer, primary_key=True)
    alarm_configuration_id = Column(Integer, ForeignKey('alarm_configurations.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    severity = Column(String(20), nullable=False)  # 'LEVE', 'NORMAL', 'GRAVE'
    status = Column(String(20), default='active', nullable=False)  # 'active', 'resolved'
    message = Column(Text, nullable=False)
    affected_targets = Column(JSON)  # Lista de equipos afectados en formato JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolution_description = Column(Text)
    
    # Relaciones
    configuration = relationship('AlarmConfiguration', back_populates='alarms')
    user = relationship('User', back_populates='alarms')
    history = relationship('AlarmHistory', back_populates='alarm', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Alarm(id={self.id}, severity='{self.severity}', status='{self.status}')>"

class AlarmHistory(Base):
    """Histórico de acciones sobre alarmas"""
    __tablename__ = 'alarm_history'
    
    id = Column(Integer, primary_key=True)
    alarm_id = Column(Integer, ForeignKey('alarms.id', ondelete='CASCADE'), nullable=False)
    action = Column(String(50), nullable=False)  # 'created', 'resolved', 'escalated'
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    alarm = relationship('Alarm', back_populates='history')
    
    def __repr__(self):
        return f"<AlarmHistory(id={self.id}, action='{self.action}', alarm_id={self.alarm_id})>"


# ============================================================================
# NUEVO v4.1.0: MODELOS PARA SISTEMA DE SENSORES INDIVIDUALES
# ============================================================================

class IndividualSensor(Base):
    """Modelo para sensores de parking individuales (PMR, Eléctrico, etc.)"""
    __tablename__ = 'individual_sensors'
    
    id = Column(Integer, primary_key=True)
    serial_number = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)  # Nombre descriptivo de la plaza
    sensor_type = Column(String(20), default='PMR', nullable=False)  # PMR, Electrico, Caravanas, Emergencias, Policia, Otros
    parking_id = Column(Integer, ForeignKey('parkings.id', ondelete='SET NULL'), nullable=True)
    description = Column(Text, nullable=True)
    location_coordinates = Column(String(100), nullable=True)  # "lat,lng" format
    manufacturer = Column(String(50), default='Fleximodo', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    parking = relationship('Parking', back_populates='individual_sensors')
    status_history = relationship('SensorStatusHistory', back_populates='sensor', cascade='all, delete-orphan')
    current_status_rel = relationship('SensorCurrentStatus', back_populates='sensor', uselist=False, cascade='all, delete-orphan')
    
    # Constraintes
    __table_args__ = (
        UniqueConstraint('serial_number', name='unique_sensor_serial'),
    )
    
    def __repr__(self):
        return f"<IndividualSensor(id={self.id}, serial='{self.serial_number}', name='{self.name}', type='{self.sensor_type}')>"
    
    @property
    def current_status(self):
        """Obtener el estado actual del sensor"""
        if self.current_status_rel:
            return self.current_status_rel.current_status
        return 'unknown'
    
    @property
    def last_update(self):
        """Obtener la última actualización del sensor"""
        if self.current_status_rel:
            return self.current_status_rel.last_update
        return None
    
    @property
    def battery_info(self):
        """Obtener información de batería del sensor"""
        if self.current_status_rel:
            return {
                'voltage': self.current_status_rel.battery_voltage,
                'capacity': self.current_status_rel.battery_capacity,
                'is_low': self.current_status_rel.battery_capacity < 20 if self.current_status_rel.battery_capacity else False
            }
        return None


class SensorStatusHistory(Base):
    """Historial de cambios de estado de sensores individuales"""
    __tablename__ = 'sensor_status_history'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey('individual_sensors.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), nullable=False)  # free, busy, error, unknown, notcalib
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    battery_voltage = Column(Float(precision=2), nullable=True)
    battery_capacity = Column(Integer, nullable=True)  # 0-100%
    temperature = Column(Float(precision=2), nullable=True)
    network_signal_strength = Column(Integer, nullable=True)
    radar_only = Column(Boolean, default=False)
    raw_data = Column(JSON, nullable=True)  # Datos completos del push
    
    # Relaciones
    sensor = relationship('IndividualSensor', back_populates='status_history')
    
    def __repr__(self):
        return f"<SensorStatusHistory(id={self.id}, sensor_id={self.sensor_id}, status='{self.status}', timestamp={self.timestamp})>"


class SensorCurrentStatus(Base):
    """Estado actual de cada sensor individual"""
    __tablename__ = 'sensor_current_status'
    
    sensor_id = Column(Integer, ForeignKey('individual_sensors.id', ondelete='CASCADE'), primary_key=True)
    current_status = Column(String(20), nullable=False)  # free, busy, error, unknown, notcalib
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    battery_voltage = Column(Float(precision=2), nullable=True)
    battery_capacity = Column(Integer, nullable=True)  # 0-100%
    temperature = Column(Float(precision=2), nullable=True)
    network_signal_strength = Column(Integer, nullable=True)
    consecutive_errors = Column(Integer, default=0)
    last_successful_ping = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    sensor = relationship('IndividualSensor', back_populates='current_status_rel')
    
    def __repr__(self):
        return f"<SensorCurrentStatus(sensor_id={self.sensor_id}, status='{self.current_status}', last_update={self.last_update})>"
    
    @property
    def is_online(self):
        """Verificar si el sensor está online (actualizado en las últimas 2 horas)"""
        if not self.last_update:
            return False
        from datetime import datetime, timedelta
        return (datetime.now() - self.last_update) < timedelta(hours=2)
    
    @property
    def needs_attention(self):
        """Verificar si el sensor necesita atención (batería baja, errores consecutivos, offline)"""
        conditions = [
            self.battery_capacity and self.battery_capacity < 20,
            self.consecutive_errors > 3,
            not self.is_online,
            self.current_status == 'error'
        ]
        return any(conditions)


class ParkingSensorSummary(Base):
    """Resumen de sensores por parking y tipo"""
    __tablename__ = 'parking_sensor_summary'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id', ondelete='CASCADE'), nullable=False)
    sensor_type = Column(String(20), nullable=False)  # PMR, Electrico, Caravanas, etc.
    total_sensors = Column(Integer, default=0)
    free_sensors = Column(Integer, default=0)
    busy_sensors = Column(Integer, default=0)
    error_sensors = Column(Integer, default=0)
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    parking = relationship('Parking', back_populates='sensor_summaries')
    
    # Constraintes
    __table_args__ = (
        UniqueConstraint('parking_id', 'sensor_type', name='unique_parking_sensor_type'),
    )
    
    def __repr__(self):
        return f"<ParkingSensorSummary(parking_id={self.parking_id}, type='{self.sensor_type}', total={self.total_sensors})>"
    
    @property
    def occupancy_rate(self):
        """Calcular tasa de ocupación para este tipo de sensor"""
        if self.total_sensors == 0:
            return 0
        return round((self.busy_sensors / self.total_sensors) * 100, 2)
    
    @property
    def available_sensors(self):
        """Sensores disponibles (libres)"""
        return self.free_sensors
    
    @property
    def status_distribution(self):
        """Distribución de estados"""
        return {
            'free': self.free_sensors,
            'busy': self.busy_sensors,
            'error': self.error_sensors,
            'unknown': self.total_sensors - (self.free_sensors + self.busy_sensors + self.error_sensors)
        }


# ============================================================================
# NUEVO v4.3.0: MODELOS PARA PANEL TIPO 4 - GESTIÓN DE VENTANAS
# ============================================================================

class ParkingPanelWindow(Base):
    """Asignación de parking/sensores a ventanas de paneles"""
    __tablename__ = 'parking_panel_windows'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id', ondelete='CASCADE'), nullable=False)
    panel_id = Column(Integer, ForeignKey('panels.id', ondelete='CASCADE'), nullable=False)
    window_id = Column(Integer, nullable=False)  # 0-15
    sensor_type = Column(String(20), nullable=True)  # NULL = parking general, 'PMR', 'Electrico', etc.
    display_type = Column(String(20), default='parking')  # 'parking', 'sensor_group', 'mixed'
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    parking = relationship('Parking', back_populates='panel_windows')
    panel = relationship('Panel', back_populates='window_assignments')
    
    # Constraintes
    __table_args__ = (
        UniqueConstraint('panel_id', 'window_id', 'parking_id', 'sensor_type', name='unique_panel_window_parking_sensor'),
        CheckConstraint('window_id >= 0 AND window_id <= 15', name='check_window_id_range'),
    )
    
    def __repr__(self):
        sensor_info = f", sensor_type='{self.sensor_type}'" if self.sensor_type else ", sensor_type=NULL"
        return f"<ParkingPanelWindow(id={self.id}, panel_id={self.panel_id}, window_id={self.window_id}, parking_id={self.parking_id}{sensor_info})>"


class PanelWindowConfiguration(Base):
    """Configuración de rotación y visualización para ventanas de paneles"""
    __tablename__ = 'panel_window_configurations'
    
    id = Column(Integer, primary_key=True)
    parking_id = Column(Integer, ForeignKey('parkings.id', ondelete='CASCADE'), nullable=False)
    panel_id = Column(Integer, ForeignKey('panels.id', ondelete='CASCADE'), nullable=False)
    window_id = Column(Integer, nullable=False)  # 0-15
    company_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)  # NULL = usuario, ID = superadmin para empresa
    rotation_enabled = Column(Boolean, default=True)
    rotation_order = Column(JSON, nullable=True)  # JSONB: [{"type": "parking", "percentage": 50, "sensor_type": null}, ...]
    refresh_time_seconds = Column(Integer, default=5)  # Tiempo total de ciclo
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    parking = relationship('Parking', back_populates='window_configurations')
    panel = relationship('Panel', back_populates='window_configurations')
    company = relationship('User', foreign_keys=[company_id])
    
    # Constraintes
    __table_args__ = (
        UniqueConstraint('panel_id', 'window_id', 'parking_id', name='unique_panel_window_parking_config'),
        CheckConstraint('window_id >= 0 AND window_id <= 15', name='check_window_id_range_config'),
        CheckConstraint('refresh_time_seconds > 0', name='check_refresh_time_positive'),
    )
    
    def __repr__(self):
        return f"<PanelWindowConfiguration(id={self.id}, panel_id={self.panel_id}, window_id={self.window_id}, parking_id={self.parking_id})>"