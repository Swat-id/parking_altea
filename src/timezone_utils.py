#!/usr/bin/env python3
"""
Utilidades para manejo consistente de zona horaria Europa/Madrid
"""

import pytz
from datetime import datetime
from typing import Optional

# Zona horaria objetivo: Europa/Madrid (UTC+1 en invierno, UTC+2 en verano)
MADRID_TZ = pytz.timezone('Europe/Madrid')

def get_madrid_now() -> datetime:
    """
    Obtener la fecha y hora actual en zona horaria Europa/Madrid
    
    Returns:
        datetime: Fecha y hora actual en Europa/Madrid con tzinfo
    """
    return datetime.now(MADRID_TZ)

def get_madrid_today() -> datetime:
    """
    Obtener la fecha actual (00:00:00) en zona horaria Europa/Madrid
    
    Returns:
        datetime: Fecha actual a las 00:00:00 en Europa/Madrid
    """
    now = get_madrid_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

def to_madrid_time(dt: datetime) -> datetime:
    """
    Convertir un datetime a zona horaria Europa/Madrid
    
    Args:
        dt: datetime a convertir (puede ser naive o con tzinfo)
        
    Returns:
        datetime: datetime convertido a Europa/Madrid
    """
    if dt.tzinfo is None:
        # Si es naive, asumir que es UTC
        dt = pytz.utc.localize(dt)
    
    return dt.astimezone(MADRID_TZ)

def from_madrid_time(dt: datetime) -> datetime:
    """
    Convertir un datetime de Europa/Madrid a UTC
    
    Args:
        dt: datetime en Europa/Madrid
        
    Returns:
        datetime: datetime convertido a UTC
    """
    if dt.tzinfo is None:
        # Si es naive, asumir que es Europa/Madrid
        dt = MADRID_TZ.localize(dt)
    
    return dt.astimezone(pytz.utc)

def parse_time_string(time_str: str) -> tuple:
    """
    Parsear string de hora HH:MM a hora y minuto
    
    Args:
        time_str: String en formato "HH:MM"
        
    Returns:
        tuple: (hora, minuto) como enteros
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return hour, minute
    except (ValueError, AttributeError):
        raise ValueError(f"Formato de hora inválido: {time_str}. Use HH:MM")

def is_time_in_range(current_time: datetime, start_time_str: str, end_time_str: str) -> bool:
    """
    Verificar si la hora actual está dentro del rango especificado
    
    Args:
        current_time: datetime actual (debe tener tzinfo)
        start_time_str: Hora de inicio en formato "HH:MM"
        end_time_str: Hora de fin en formato "HH:MM"
        
    Returns:
        bool: True si está en el rango, False si no
    """
    # Asegurar que current_time esté en Madrid
    madrid_time = to_madrid_time(current_time)
    current_time_str = madrid_time.strftime('%H:%M')
    
    # Manejar caso de rango que cruza medianoche
    if start_time_str <= end_time_str:
        # Rango normal: 09:00 - 17:00
        return start_time_str <= current_time_str <= end_time_str
    else:
        # Rango que cruza medianoche: 22:00 - 06:00
        return current_time_str >= start_time_str or current_time_str <= end_time_str

def get_weekday_madrid(dt: Optional[datetime] = None) -> int:
    """
    Obtener el día de la semana en zona horaria Europa/Madrid
    
    Args:
        dt: datetime específico, si None usa la hora actual
        
    Returns:
        int: Día de la semana (0=lunes, 6=domingo)
    """
    if dt is None:
        dt = get_madrid_now()
    else:
        dt = to_madrid_time(dt)
    
    return dt.weekday()

def format_madrid_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S %Z') -> str:
    """
    Formatear datetime en zona horaria Europa/Madrid
    
    Args:
        dt: datetime a formatear
        format_str: Formato de salida
        
    Returns:
        str: datetime formateado en Europa/Madrid
    """
    madrid_dt = to_madrid_time(dt)
    return madrid_dt.strftime(format_str)

# Mapeo de días de la semana para compatibilidad
WEEKDAY_FIELDS = {
    0: 'monday',
    1: 'tuesday', 
    2: 'wednesday',
    3: 'thursday',
    4: 'friday',
    5: 'saturday',
    6: 'sunday'
}

def get_weekday_field(dt: Optional[datetime] = None) -> str:
    """
    Obtener el nombre del campo del día de la semana para la base de datos
    
    Args:
        dt: datetime específico, si None usa la hora actual
        
    Returns:
        str: Nombre del campo ('monday', 'tuesday', etc.)
    """
    weekday = get_weekday_madrid(dt)
    return WEEKDAY_FIELDS.get(weekday, 'monday')

def log_timezone_info():
    """
    Registrar información de zona horaria para debugging
    """
    import logging
    logger = logging.getLogger(__name__)
    
    now_utc = datetime.now(pytz.utc)
    now_madrid = get_madrid_now()
    
    logger.info(f"Timezone Utils - UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"Timezone Utils - Madrid: {now_madrid.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"Timezone Utils - Offset: {now_madrid.strftime('%z')}")
