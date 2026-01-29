"""
Servicio de gestión de eventos pendientes de validación cruzada v4.4.1

Este módulo coordina la sincronización entre:
- Eventos de entrada/salida por acceso (camera_server.py)
- Eventos de ocupación/liberación de plaza (spot_detection_server.py)

El conteo plaza a plaza (detección) se considera la fuente de verdad.
Los eventos de acceso se validan contra los eventos de detección.

FLUJOS:
1. ENTRADA por acceso → espera validación por OCUPACIÓN de plaza
2. LIBERACIÓN de plaza → espera validación por SALIDA de acceso
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from models import Parking, PendingParkingEvent, OccupancyHistory

logger = logging.getLogger(__name__)

# Configuración de timeouts (en minutos)
ENTRY_TIMEOUT_MINUTES = 5   # Tiempo máximo para validar una entrada
EXIT_TIMEOUT_MINUTES = 10   # Tiempo máximo para validar una salida (puede ser reubicación)


def check_and_register_pending_entry(session, parking, camera_id=None, notes=None):
    """
    Verificar si una entrada debe registrarse como pendiente.
    
    Se registra como pendiente si:
    - El parking tiene monitorización de plazas habilitada
    - Las plazas libres del conteo serían menores que las detectadas
    
    Returns:
        tuple: (should_apply_entry, pending_event_created)
        - should_apply_entry: True si la entrada debe aplicarse normalmente
        - pending_event_created: El PendingParkingEvent creado (o None)
    """
    try:
        # Si no hay monitorización habilitada, aplicar entrada normalmente
        if not getattr(parking, 'spot_monitoring_enabled', False):
            return True, None
        
        # Obtener datos de monitorización
        total_monitored = getattr(parking, 'total_monitored_spots', 0)
        spot_occupied = getattr(parking, 'total_spot_occupied', 0)
        
        if total_monitored == 0:
            # Sin plazas monitorizadas, aplicar normalmente
            return True, None
        
        # Calcular plazas libres actuales según cada fuente
        conteo_libres = parking.max_capacity - parking.current_occupancy
        deteccion_libres = total_monitored - spot_occupied
        
        # Si la entrada haría que las libres del conteo sean menores que las de detección
        # significa que estaríamos indicando más ocupación de la que la detección confirma
        conteo_libres_despues = conteo_libres - 1
        
        if conteo_libres_despues < deteccion_libres:
            # La entrada produciría un descuadre - registrar como pendiente
            logger.info(f"PENDING ENTRY REGISTERED - Parking: {parking.name}, "
                       f"Conteo libres actual: {conteo_libres}, Después: {conteo_libres_despues}, "
                       f"Detección libres: {deteccion_libres}")
            
            pending_event = PendingParkingEvent(
                parking_id=parking.id,
                event_type='entry',
                source='camera_access',
                camera_id=camera_id,
                occupancy_at_creation=parking.current_occupancy,
                notes=notes or f"Entrada bloqueada: conteo_libres({conteo_libres_despues}) < deteccion_libres({deteccion_libres})"
            )
            session.add(pending_event)
            
            # Actualizar contador en parking
            parking.pending_entries = (parking.pending_entries or 0) + 1
            
            session.flush()  # Para obtener el ID
            
            return False, pending_event
        
        # La entrada puede aplicarse normalmente
        return True, None
        
    except Exception as e:
        logger.error(f"Error en check_and_register_pending_entry: {e}", exc_info=True)
        # En caso de error, permitir la entrada (fail-safe)
        return True, None


def check_and_register_pending_exit(session, parking, spot_id=None, notes=None):
    """
    Verificar si una liberación de plaza debe registrarse como salida pendiente.
    
    Se registra como pendiente cuando:
    - Una plaza pasa de ocupada a libre
    - No ha llegado aún el evento de salida por acceso
    
    Returns:
        tuple: (pending_event_created)
    """
    try:
        # Si no hay monitorización habilitada, no registrar
        if not getattr(parking, 'spot_monitoring_enabled', False):
            return None
        
        # Registrar salida pendiente (liberación de plaza)
        logger.info(f"PENDING EXIT REGISTERED - Parking: {parking.name}, Spot ID: {spot_id}")
        
        pending_event = PendingParkingEvent(
            parking_id=parking.id,
            event_type='exit',
            source='spot_detection',
            spot_id=spot_id,
            occupancy_at_creation=parking.current_occupancy,
            notes=notes or "Plaza liberada, esperando salida por acceso"
        )
        session.add(pending_event)
        
        # Actualizar contador en parking
        parking.pending_exits = (parking.pending_exits or 0) + 1
        
        session.flush()
        
        return pending_event
        
    except Exception as e:
        logger.error(f"Error en check_and_register_pending_exit: {e}", exc_info=True)
        return None


def validate_pending_entry_on_spot_occupied(session, parking, spot_id=None):
    """
    Validar una entrada pendiente cuando se detecta ocupación de plaza.
    
    Cuando una plaza pasa de libre a ocupada:
    1. Si hay entradas pendientes → validar una (el vehículo llegó a la plaza)
    2. Aplicar la ocupación que estaba pendiente
    
    Returns:
        bool: True si se validó una entrada pendiente
    """
    try:
        if not getattr(parking, 'spot_monitoring_enabled', False):
            return False
        
        pending_entries = (parking.pending_entries or 0)
        
        if pending_entries <= 0:
            return False
        
        # Buscar la entrada pendiente más antigua
        oldest_pending = session.query(PendingParkingEvent).filter(
            PendingParkingEvent.parking_id == parking.id,
            PendingParkingEvent.event_type == 'entry',
            PendingParkingEvent.status == 'pending'
        ).order_by(PendingParkingEvent.created_at.asc()).first()
        
        if oldest_pending:
            logger.info(f"VALIDATING PENDING ENTRY - Parking: {parking.name}, "
                       f"Event ID: {oldest_pending.id}, Spot ID: {spot_id}")
            
            # Marcar como validado
            oldest_pending.status = 'validated'
            oldest_pending.validated_at = datetime.now(timezone.utc)
            oldest_pending.notes = (oldest_pending.notes or '') + f" | Validado por ocupación de plaza {spot_id}"
            
            # Reducir contador
            parking.pending_entries = max(0, pending_entries - 1)
            
            # Aplicar la ocupación que estaba pendiente
            previous_occupancy = parking.current_occupancy
            parking.current_occupancy += 1
            
            # Registrar en histórico
            hist = OccupancyHistory(
                parking_id=parking.id,
                occupancy=parking.current_occupancy,
                source='pending_entry_validated',
                previous_occupancy=previous_occupancy,
                change_amount=1,
                adjustment_type='pending_entry_validated'
            )
            session.add(hist)
            
            logger.info(f"Pending entry validated - Parking: {parking.name}, "
                       f"Occupancy: {previous_occupancy} -> {parking.current_occupancy}")
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error en validate_pending_entry_on_spot_occupied: {e}", exc_info=True)
        return False


def validate_pending_exit_on_access_exit(session, parking, camera_id=None):
    """
    Validar una salida pendiente cuando hay salida por acceso.
    
    Cuando un vehículo sale por acceso:
    1. Si hay salidas pendientes → validar una (el vehículo que liberó plaza salió)
    2. Si no hay salidas pendientes → reducir ocupación normalmente
    
    Returns:
        bool: True si se validó una salida pendiente (no aplicar reducción normal)
    """
    try:
        if not getattr(parking, 'spot_monitoring_enabled', False):
            return False
        
        pending_exits = (parking.pending_exits or 0)
        
        if pending_exits <= 0:
            return False
        
        # Buscar la salida pendiente más antigua
        oldest_pending = session.query(PendingParkingEvent).filter(
            PendingParkingEvent.parking_id == parking.id,
            PendingParkingEvent.event_type == 'exit',
            PendingParkingEvent.status == 'pending'
        ).order_by(PendingParkingEvent.created_at.asc()).first()
        
        if oldest_pending:
            logger.info(f"VALIDATING PENDING EXIT - Parking: {parking.name}, "
                       f"Event ID: {oldest_pending.id}, Camera ID: {camera_id}")
            
            # Marcar como validado
            oldest_pending.status = 'validated'
            oldest_pending.validated_at = datetime.now(timezone.utc)
            oldest_pending.notes = (oldest_pending.notes or '') + f" | Validado por salida de acceso (camera {camera_id})"
            
            # Reducir contador
            parking.pending_exits = max(0, pending_exits - 1)
            
            logger.info(f"Pending exit validated - Parking: {parking.name}, "
                       f"Remaining pending exits: {parking.pending_exits}")
            
            # La ocupación ya se redujo cuando se detectó la liberación de plaza
            # No hay que hacer nada más con la ocupación
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error en validate_pending_exit_on_access_exit: {e}", exc_info=True)
        return False


def cancel_pending_entry_on_access_exit(session, parking, camera_id=None):
    """
    Cancelar una entrada pendiente cuando hay salida por acceso.
    
    Si hay entrada pendiente y llega una salida:
    - El vehículo que entró (pendiente) salió sin ocupar plaza monitorizada
    - Cancelar la entrada pendiente (no afecta ocupación)
    
    Returns:
        bool: True si se canceló una entrada pendiente
    """
    try:
        if not getattr(parking, 'spot_monitoring_enabled', False):
            return False
        
        pending_entries = (parking.pending_entries or 0)
        
        if pending_entries <= 0:
            return False
        
        # Buscar la entrada pendiente más antigua
        oldest_pending = session.query(PendingParkingEvent).filter(
            PendingParkingEvent.parking_id == parking.id,
            PendingParkingEvent.event_type == 'entry',
            PendingParkingEvent.status == 'pending'
        ).order_by(PendingParkingEvent.created_at.asc()).first()
        
        if oldest_pending:
            logger.info(f"CANCELLING PENDING ENTRY - Parking: {parking.name}, "
                       f"Event ID: {oldest_pending.id}, Camera ID: {camera_id}")
            
            # Marcar como cancelado
            oldest_pending.status = 'cancelled'
            oldest_pending.expired_at = datetime.now(timezone.utc)
            oldest_pending.notes = (oldest_pending.notes or '') + f" | Cancelado por salida de acceso (camera {camera_id})"
            
            # Reducir contador
            parking.pending_entries = max(0, pending_entries - 1)
            
            logger.info(f"Pending entry cancelled - Parking: {parking.name}")
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error en cancel_pending_entry_on_access_exit: {e}", exc_info=True)
        return False


def cleanup_expired_events(session, entry_timeout=ENTRY_TIMEOUT_MINUTES, exit_timeout=EXIT_TIMEOUT_MINUTES):
    """
    Limpiar eventos pendientes que han expirado.
    
    - Entradas pendientes > entry_timeout: El vehículo entró a zona no monitorizada
    - Salidas pendientes > exit_timeout: El vehículo cambió de plaza (no salió)
    
    Returns:
        tuple: (expired_entries_count, expired_exits_count)
    """
    try:
        now = datetime.now(timezone.utc)
        entry_cutoff = now - timedelta(minutes=entry_timeout)
        exit_cutoff = now - timedelta(minutes=exit_timeout)
        
        expired_entries = 0
        expired_exits = 0
        
        # Expirar entradas pendientes
        entry_events = session.query(PendingParkingEvent).filter(
            PendingParkingEvent.event_type == 'entry',
            PendingParkingEvent.status == 'pending',
            PendingParkingEvent.created_at < entry_cutoff
        ).all()
        
        for event in entry_events:
            event.status = 'expired'
            event.expired_at = now
            event.notes = (event.notes or '') + f" | Expirado tras {entry_timeout} minutos sin validación"
            
            # Actualizar contador del parking
            parking = session.query(Parking).get(event.parking_id)
            if parking:
                parking.pending_entries = max(0, (parking.pending_entries or 0) - 1)
            
            expired_entries += 1
            logger.info(f"ENTRY EXPIRED - Parking ID: {event.parking_id}, Event ID: {event.id}")
        
        # Expirar salidas pendientes (probablemente cambio de plaza)
        exit_events = session.query(PendingParkingEvent).filter(
            PendingParkingEvent.event_type == 'exit',
            PendingParkingEvent.status == 'pending',
            PendingParkingEvent.created_at < exit_cutoff
        ).all()
        
        for event in exit_events:
            event.status = 'expired'
            event.expired_at = now
            event.notes = (event.notes or '') + f" | Expirado tras {exit_timeout} minutos (probable cambio de plaza)"
            
            # Actualizar contador del parking
            parking = session.query(Parking).get(event.parking_id)
            if parking:
                parking.pending_exits = max(0, (parking.pending_exits or 0) - 1)
            
            expired_exits += 1
            logger.info(f"EXIT EXPIRED - Parking ID: {event.parking_id}, Event ID: {event.id}")
        
        if expired_entries > 0 or expired_exits > 0:
            logger.info(f"CLEANUP COMPLETED - Expired entries: {expired_entries}, Expired exits: {expired_exits}")
        
        return expired_entries, expired_exits
        
    except Exception as e:
        logger.error(f"Error en cleanup_expired_events: {e}", exc_info=True)
        return 0, 0


def get_pending_events_summary(session, parking_id=None):
    """
    Obtener resumen de eventos pendientes.
    
    Returns:
        dict con estadísticas de eventos pendientes
    """
    try:
        query = session.query(PendingParkingEvent)
        
        if parking_id:
            query = query.filter(PendingParkingEvent.parking_id == parking_id)
        
        pending_entries = query.filter(
            PendingParkingEvent.event_type == 'entry',
            PendingParkingEvent.status == 'pending'
        ).count()
        
        pending_exits = query.filter(
            PendingParkingEvent.event_type == 'exit',
            PendingParkingEvent.status == 'pending'
        ).count()
        
        validated_today = query.filter(
            PendingParkingEvent.status == 'validated',
            PendingParkingEvent.validated_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        ).count()
        
        expired_today = query.filter(
            PendingParkingEvent.status == 'expired',
            PendingParkingEvent.expired_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        ).count()
        
        return {
            'pending_entries': pending_entries,
            'pending_exits': pending_exits,
            'validated_today': validated_today,
            'expired_today': expired_today
        }
        
    except Exception as e:
        logger.error(f"Error en get_pending_events_summary: {e}", exc_info=True)
        return {
            'pending_entries': 0,
            'pending_exits': 0,
            'validated_today': 0,
            'expired_today': 0
        }
