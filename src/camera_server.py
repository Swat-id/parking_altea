from flask import Flask, request, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import config
import json
import logging
import time
from models import Base, Parking, Access, OccupancyHistory, CameraLog, CameraParking
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
import threading
import subprocess

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar la función de actualización de paneles
from panel_communication_service import update_parking_panels
logger.info("Función update_parking_panels importada correctamente")

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Cache para verificar duplicados recientes (últimos 5 minutos)
recent_messages = {}

def is_duplicate_message(device, line, vehicle_in, vehicle_out, timestamp):
    """
    Verificar si un mensaje es duplicado basado en device, línea y contadores.
    
    UNIFICACIÓN: Usar device + line en lugar de IP + line para mejor detección
    """
    key = f"{device}_{line}_{vehicle_in}_{vehicle_out}"
    
    # Limpiar mensajes antiguos (más de 5 minutos)
    current_time = time.time()
    recent_messages_copy = recent_messages.copy()
    for msg_key, msg_time in recent_messages_copy.items():
        if current_time - msg_time > 300:  # 5 minutos
            del recent_messages[msg_key]
    
    # Verificar si ya existe este mensaje
    if key in recent_messages:
        logger.warning(f"DUPLICATE MESSAGE DETECTED - Device: {device}, Line: {line}, In: {vehicle_in}, Out: {vehicle_out}")
        return True
    
    # Registrar este mensaje
    recent_messages[key] = current_time
    return False

def apply_duplicate_correction(session, access, delta_in, delta_out):
    """Aplicar corrección por duplicados en los conteos"""
    try:
        # Si hay duplicados, reducir el impacto del delta
        # Esto evita que los duplicados afecten significativamente la ocupación
        correction_factor = 0.5  # Reducir el impacto a la mitad
        
        corrected_delta_in = int(delta_in * correction_factor) if delta_in > 0 else 0
        corrected_delta_out = int(delta_out * correction_factor) if delta_out > 0 else 0
        
        logger.info(f"Applying duplicate correction - Original: In={delta_in}, Out={delta_out} -> Corrected: In={corrected_delta_in}, Out={corrected_delta_out}")
        
        return corrected_delta_in, corrected_delta_out
        
    except Exception as e:
        logger.error(f"Error applying duplicate correction: {e}")
        return delta_in, delta_out

def log_camera_message(session, camera_ip, camera_line, camera_name, raw_message, 
                      vehicle_in, vehicle_out, status, error_message=None, 
                      access_id=None, parking_id=None, processing_time=None,
                      previous_vehicle_in=None, previous_vehicle_out=None,
                      delta_in=None, delta_out=None, new_occupancy=None,
                      occupancy_change=None, parking_status=None):
    """Registrar mensaje de cámara en la base de datos"""
    try:
        camera_log = CameraLog(
            access_id=access_id,
            parking_id=parking_id,
            camera_ip=camera_ip,
            camera_line=camera_line,
            camera_name=camera_name,
            raw_message=raw_message,
            vehicle_in=vehicle_in,
            vehicle_out=vehicle_out,
            previous_vehicle_in=previous_vehicle_in,
            previous_vehicle_out=previous_vehicle_out,
            delta_in=delta_in,
            delta_out=delta_out,
            status=status,
            error_message=error_message,
            processing_time=processing_time,
            new_occupancy=new_occupancy,
            occupancy_change=occupancy_change,
            parking_status=parking_status,
            processed_at=datetime.now()
        )
        session.add(camera_log)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error registrando log de cámara: {e}")
        session.rollback()
        return False

def detect_camera_reset(previous_in, previous_out, new_in, new_out):
    """
    Detectar si la cámara se ha reiniciado basándose en los contadores.
    
    UNIFICACIÓN: Lógica mejorada para reinicios que evita cálculos incorrectos
    """
    # Si es la primera vez (contadores anteriores son None), no es reinicio
    if previous_in is None or previous_out is None:
        return False, 0, 0
    
    # Detectar reinicio: nuevos contadores son menores que los anteriores
    # Esto incluye cuando uno o ambos contadores van a 0
    is_reset = (new_in < previous_in) or (new_out < previous_out)
    
    if is_reset:
        logger.info(f"CAMERA RESET DETECTED - Previous: In={previous_in}, Out={previous_out} -> New: In={new_in}, Out={new_out}")
        
        # UNIFICACIÓN: En caso de reinicio, usar los nuevos valores como base
        # No ajustar a 0, sino usar los nuevos valores directamente
        adjusted_previous_in = new_in
        adjusted_previous_out = new_out
        
        logger.info(f"Reset adjustment - Using new values as base: In={adjusted_previous_in}, Out={adjusted_previous_out}")
        return True, adjusted_previous_in, adjusted_previous_out
    
    return False, previous_in, previous_out

def calculate_deltas_with_reset_handling(previous_in, previous_out, new_in, new_out):
    """
    Calcular deltas considerando posibles reinicios de cámara.
    
    UNIFICACIÓN: Lógica mejorada para evitar cálculos incorrectos
    """
    # Detectar si hay reinicio
    is_reset, adjusted_previous_in, adjusted_previous_out = detect_camera_reset(
        previous_in, previous_out, new_in, new_out
    )
    
    # Calcular deltas usando los contadores ajustados
    delta_in = new_in - adjusted_previous_in
    delta_out = new_out - adjusted_previous_out
    
    # UNIFICACIÓN: En caso de reinicio, los deltas deben ser 0
    # porque estamos usando los nuevos valores como base
    if is_reset:
        delta_in = 0
        delta_out = 0
        logger.info(f"Reset detected - Setting deltas to 0 to avoid incorrect calculations")
    
    # Validar que los deltas sean positivos (excepto en reinicios)
    if not is_reset:
        if delta_in < 0:
            logger.warning(f"Negative delta_in detected (non-reset): {delta_in}. Setting to 0.")
            delta_in = 0
        if delta_out < 0:
            logger.warning(f"Negative delta_out detected (non-reset): {delta_out}. Setting to 0.")
            delta_out = 0
    
    reset_info = {
        "is_reset": is_reset,
        "previous_in": previous_in,
        "previous_out": previous_out,
        "adjusted_previous_in": adjusted_previous_in,
        "adjusted_previous_out": adjusted_previous_out,
        "new_in": new_in,
        "new_out": new_out
    }
    
    logger.info(f"Deltas calculated - Delta In: {delta_in}, Delta Out: {delta_out}, Reset: {is_reset}")
    
    return delta_in, delta_out, is_reset, reset_info

@app.route('/camera', methods=['POST'])
def handle_camera():
    start_time = time.time()
    
    # Obtener IP del cliente al inicio para logging
    ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    
    # Log de recepción de petición
    logger.info(f"=== CAMERA MESSAGE RECEIVED ===")
    logger.info(f"Source IP: {ip}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Capturar el body raw para logging
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"Raw body received: {raw_data}")
    except Exception as e:
        logger.error(f"Error reading raw body from {ip}: {e}")
        raw_data = "Unable to read raw body"
    
    session = Session()
    
    try:
        # Intentar parsear JSON de forma robusta
        try:
            data = request.get_json(force=True)
            logger.info(f"JSON parsed successfully from {ip}")
        except Exception as e:
            logger.error(f"JSON mal formado descartado from {ip}: {e}")
            logger.error(f"Raw data that caused error: {raw_data}")
            
            # Registrar log de error
            log_camera_message(
                session=session,
                camera_ip=ip,
                camera_line=0,
                camera_name="",
                raw_message=raw_data,
                vehicle_in=0,
                vehicle_out=0,
                status="error",
                error_message=f"Invalid JSON format: {e}",
                processing_time=(time.time() - start_time) * 1000
            )
            
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        if not data:
            logger.error(f"Mensaje vacío descartado from {ip}")
            logger.error(f"Raw data was empty or null")
            
            # Registrar log de error
            log_camera_message(
                session=session,
                camera_ip=ip,
                camera_line=0,
                camera_name="",
                raw_message=raw_data,
                vehicle_in=0,
                vehicle_out=0,
                status="error",
                error_message="Empty JSON data",
                processing_time=(time.time() - start_time) * 1000
            )
            
            return jsonify({'error': 'Empty JSON data'}), 400
        
        # Extraer campos del nuevo formato
        device = data.get('device', '')
        line = data.get('line', 0)
        veh_in = data.get('Vehicle In', 0)
        veh_out = data.get('Vehicle Out', 0)
        event = data.get('event', '')
        time_str = data.get('time', '')
        
        # Log de la petición recibida
        logger.info(f"Camera data from {ip} - Device: {device}, Line: {line}, In: {veh_in}, Out: {veh_out}")
        logger.info(f"JSON received: {json.dumps(data, indent=2)}")
        
        # Validar campos requeridos
        if line is None or veh_in is None or veh_out is None:
            error_msg = f"Campos requeridos faltantes: line={line}, veh_in={veh_in}, veh_out={veh_out}"
            logger.error(f"{error_msg} from {ip}")
            logger.error(f"JSON completo que causó el error: {json.dumps(data, indent=2)}")
            
            # Registrar log de error
            log_camera_message(
                session=session,
                camera_ip=ip,
                camera_line=line or 0,
                camera_name=device,
                raw_message=raw_data,
                vehicle_in=veh_in or 0,
                vehicle_out=veh_out or 0,
                status="error",
                error_message=error_msg,
                processing_time=(time.time() - start_time) * 1000
            )
            
            return jsonify({'error': 'Missing required fields: line, Vehicle In, Vehicle Out'}), 400
        
        # Convertir a enteros de forma segura
        try:
            line = int(line)
            veh_in = int(veh_in)
            veh_out = int(veh_out)
        except (ValueError, TypeError) as e:
            error_msg = f"Valores numéricos inválidos: {e}"
            logger.error(f"{error_msg} from {ip}")
            logger.error(f"Valores problemáticos: line='{line}', veh_in='{veh_in}', veh_out='{veh_out}'")
            
            # Registrar log de error
            log_camera_message(
                session=session,
                camera_ip=ip,
                camera_line=line if isinstance(line, int) else 0,
                camera_name=device,
                raw_message=raw_data,
                vehicle_in=veh_in if isinstance(veh_in, int) else 0,
                vehicle_out=veh_out if isinstance(veh_out, int) else 0,
                status="error",
                error_message=error_msg,
                processing_time=(time.time() - start_time) * 1000
            )
            
            return jsonify({'error': 'Invalid numeric values'}), 400
        
        # Ajustar numeración de línea: cámara envía 0,1,2,3... pero BD usa 1,2,3,4...
        original_line = line
        line = line + 1
        logger.info(f"Line number adjusted - Received: {original_line}, Adjusted for DB: {line}")
        
        # UNIFICACIÓN: Verificar duplicados ANTES de buscar el acceso
        # Usar device + line en lugar de IP + line
        if is_duplicate_message(device, original_line, veh_in, veh_out, time.time()):
            logger.warning(f"DUPLICATE MESSAGE IGNORED - Device: {device}, Line: {original_line}, In: {veh_in}, Out: {veh_out}")
            
            # Registrar log de duplicado
            log_camera_message(
                session=session,
                camera_ip=ip,
                camera_line=original_line,
                camera_name=device,
                raw_message=raw_data,
                vehicle_in=veh_in,
                vehicle_out=veh_out,
                status="duplicate",
                error_message="Duplicate message ignored",
                processing_time=(time.time() - start_time) * 1000
            )
            
            return jsonify({'status': 'duplicate_ignored', 'message': 'Duplicate message ignored'}), 200
        
        # NUEVA LÓGICA: Buscar la cámara por device + línea usando la nueva relación muchos a muchos
        # Esto permite que una misma cámara esté asignada a múltiples parkings
        accesses = session.query(Access).filter(
            func.lower(Access.name) == func.lower(device),
            Access.line == line
        ).all()
        
        if not accesses:
            # Si no se encuentra por device+línea, intentar buscar por IP+línea como fallback
            accesses = session.query(Access).filter_by(ip=ip, line=line).all()
            if accesses:
                logger.info(f"Found {len(accesses)} access(es) by IP and line (fallback): {ip}, line: {line}")
            else:
                error_msg = f"Device not found in database: {device} (line: {original_line})"
                logger.warning(f"{error_msg}")
                # Log adicional para debugging - mostrar todos los dispositivos disponibles
                all_devices = session.query(Access.name).distinct().all()
                device_names = [d[0] for d in all_devices]
                logger.warning(f"Available devices in database: {device_names}")
                
                # Registrar log de error
                log_camera_message(
                    session=session,
                    camera_ip=ip,
                    camera_line=original_line,
                    camera_name=device,
                    raw_message=raw_data,
                    vehicle_in=veh_in,
                    vehicle_out=veh_out,
                    status="error",
                    error_message=error_msg,
                    processing_time=(time.time() - start_time) * 1000
                )
                
                return jsonify({'error': 'Device not found'}), 404
        else:
            logger.info(f"Found {len(accesses)} access(es) by device name and line: {device}, line: {line}")
        
        # Log de información de todos los accesos encontrados
        for access in accesses:
            # Obtener parkings asociados a esta cámara usando la nueva relación
            camera_parkings = session.query(CameraParking).filter_by(camera_id=access.id).all()
            parking_names = [cp.parking.name for cp in camera_parkings]
            logger.info(f"Access found - ID: {access.id}, Name: {access.name}, Associated parkings: {parking_names}")
            logger.info(f"Previous counters - Last In: {access.last_vehicle_in}, Last Out: {access.last_vehicle_out}")
        
        # Actualizar estado de TODAS las cámaras a ONLINE y timestamp de último mensaje
        for access in accesses:
            access.status = 'ONLINE'
            access.last_message_received = datetime.now()
        logger.info(f"Camera status updated to ONLINE for {len(accesses)} access(es) - Device: {device}, Line: {original_line}")
        
        # Usar el primer acceso para obtener contadores anteriores (todos deberían ser iguales)
        first_access = accesses[0]
        previous_vehicle_in = first_access.last_vehicle_in
        previous_vehicle_out = first_access.last_vehicle_out
        
        # Calcular deltas con manejo de reinicios
        logger.info(f"Calculating deltas - Previous: In={previous_vehicle_in}, Out={previous_vehicle_out} -> New: In={veh_in}, Out={veh_out}")
        delta_in, delta_out, is_reset, reset_info = calculate_deltas_with_reset_handling(
            previous_vehicle_in, previous_vehicle_out, veh_in, veh_out
        )
        
        # Log detallado de los deltas calculados
        logger.info(f"Delta calculation result - Delta In: {delta_in}, Delta Out: {delta_out}, Is Reset: {is_reset}")
        logger.info(f"Reset info: {reset_info}")
        
        # Si es un reinicio, logear información adicional
        if is_reset:
            logger.warning(f"CAMERA RESET PROCESSED - Device: {device}, Line: {original_line}")
            logger.warning(f"Reset details: {reset_info}")
        
        # NUEVA LÓGICA: Actualizar contadores de TODOS los accesos ANTES de calcular ocupación
        # Esto es crucial para evitar duplicados
        for access in accesses:
            access.last_vehicle_in = veh_in
            access.last_vehicle_out = veh_out
        
        # CORRECCIÓN CRÍTICA: La lógica correcta es aplicar el delta a todos los parkings asociados
        # NO sumar contadores absolutos de todas las cámaras
        updated_parkings = []
        
        for access in accesses:
            # Obtener todos los parkings asociados a esta cámara
            camera_parkings = session.query(CameraParking).filter_by(camera_id=access.id).all()
            
            for camera_parking in camera_parkings:
                parking = camera_parking.parking
                previous_occupancy = parking.current_occupancy
                
                # LÓGICA CORRECTA: Aplicar el delta calculado al parking
                # Solo aplicar deltas si NO es un reinicio
                if not is_reset:
                    # Aplicar el delta de esta cámara al parking
                    parking.current_occupancy += (delta_in - delta_out)
                    logger.info(f"Occupancy updated for parking {parking.name} - Previous: {previous_occupancy}, Delta applied: +{delta_in} -{delta_out} = {delta_in - delta_out}, New: {parking.current_occupancy}")
                else:
                    # En caso de reinicio, mantener la ocupación actual
                    logger.info(f"Reset detected for parking {parking.name} - Keeping current occupancy: {parking.current_occupancy}")
                
                # PERMITIR OCUPACIÓN POR ENCIMA DEL MÁXIMO Y VALORES NEGATIVOS
                # No limitar la ocupación al máximo de capacidad
                # Esto permite reflejar la realidad cuando hay exceso de vehículos
                
                logger.info(f"Parking occupancy updated - {parking.name}: Previous: {previous_occupancy}, New: {parking.current_occupancy}, Max Capacity: {parking.max_capacity}")
                if is_reset:
                    logger.info(f"Reset impact on occupancy for {parking.name}: +{delta_in} in, -{delta_out} out, Net change: {delta_in - delta_out}")
                
                # Calcular descuadre para estadísticas
                free_spaces = parking.max_capacity - parking.current_occupancy
                occupancy_discrepancy = None
                
                if parking.current_occupancy > parking.max_capacity:
                    # Exceso de vehículos
                    occupancy_discrepancy = f"EXCESS:{parking.current_occupancy - parking.max_capacity}"
                    logger.warning(f"OCCUPANCY EXCESS - Parking: {parking.name}, Capacity: {parking.max_capacity}, Current: {parking.current_occupancy}, Excess: {parking.current_occupancy - parking.max_capacity}")
                elif free_spaces < 0:
                    # Plazas libres negativas
                    occupancy_discrepancy = f"NEGATIVE_FREE:{abs(free_spaces)}"
                    logger.warning(f"NEGATIVE FREE SPACES - Parking: {parking.name}, Free spaces: {free_spaces}, This indicates counting errors or overflow")
                
                # Registrar histórico con información de descuadre
                hist = OccupancyHistory(
                    parking_id=parking.id,
                    occupancy=parking.current_occupancy,
                    source='camera'
                )
                session.add(hist)
                
                # Calcular estado (permitir estados especiales para descuadres)
                occ = parking.current_occupancy
                parking_name = parking.name  # Obtener el nombre antes de cerrar la sesión
                previous_status = parking.status
                free = parking.max_capacity - occ
                
                if parking.fixed_message_flag:
                    parking_status = parking.status  # Mantener estado actual
                    logger.info(f"Fixed message flag is active for {parking.name} - no status update")
                else:
                    # CORRECCIÓN: Solo actualizar el estado, NO generar el mensaje aquí
                    if free < 0:
                        # Estado especial para descuadres negativos
                        parking.status = 'COMPLETO'
                        logger.warning(f"Status set to COMPLETO (descuadre negativo) for {parking.name} - Free spaces: {free}")
                    elif occ > parking.max_capacity:
                        # Estado para exceso de ocupación
                        parking.status = 'COMPLETO'
                        logger.warning(f"Status set to COMPLETO (exceso) for {parking.name} - Occupancy: {occ}, Capacity: {parking.max_capacity}")
                    elif free <= parking.threshold_full:
                        parking.status = 'COMPLETO'
                    elif free <= parking.threshold_dense:
                        parking.status = 'DENSO'
                    else:
                        parking.status = 'LIBRE'
                    
                    parking_status = parking.status
                    logger.info(f"Status updated for {parking.name} - Previous: {previous_status}, New: {parking.status}, Free spaces: {free}")
                    logger.info(f"Thresholds evaluation for {parking.name} - Free spaces: {free}, Dense threshold: {parking.threshold_dense}, Full threshold: {parking.threshold_full}")
                    
                    # Verificar programaciones activas antes de actualizar paneles
                    from panel_schedule_service import PanelScheduleService
                    schedule_service = PanelScheduleService(session)
                    active_schedules = schedule_service.get_active_schedules_for_parking(parking.id)
                    
                    # Determinar el estado del procesamiento
                    if active_schedules:
                        logger.info(f"Active schedule found for parking {parking.name}, skipping panel update")
                        processing_status = "schedule_active"
                        error_message = f"Panel update skipped due to active schedule: {active_schedules[0].name}"
                    else:
                        # CORRECCIÓN EC-004: No actualizar paneles desde cámaras para evitar interferencias
                        # El worker se encargará de actualizar paneles cada 5 minutos respetando message_type
                        logger.info(f"Occupancy updated for {parking.name}: {parking.current_occupancy}/{parking.max_capacity} ({parking.status}) - Panel update will be handled by worker")
                        processing_status = "processed" if not is_reset else "reset_processed"
                        error_message = None
                
                # Preparar información adicional para el log en caso de reinicio
                if is_reset and error_message is None:
                    error_message = f"Camera reset detected - Previous: In={previous_vehicle_in}, Out={previous_vehicle_out} -> New: In={veh_in}, Out={veh_out}"
                
                # Registrar log de cámara para cada parking
                log_camera_message(
                    session=session,
                    camera_ip=ip,
                    camera_line=original_line,
                    camera_name=device,
                    raw_message=raw_data,
                    vehicle_in=veh_in,
                    vehicle_out=veh_out,
                    status=processing_status,
                    error_message=error_message,
                    access_id=access.id,
                    parking_id=parking.id,
                    processing_time=(time.time() - start_time) * 1000,
                    previous_vehicle_in=reset_info["adjusted_previous_in"],
                    previous_vehicle_out=reset_info["adjusted_previous_out"],
                    delta_in=delta_in,
                    delta_out=delta_out,
                    new_occupancy=occ,
                    occupancy_change=occ - previous_occupancy,
                    parking_status=parking_status
                )
                
                updated_parkings.append({
                    'name': parking.name,
                    'occupancy': occ,
                    'status': parking.status
                })
        
        session.commit()
        session.close()
        
        # Log de resumen de todos los parkings actualizados
        parking_names = [p['name'] for p in updated_parkings]
        logger.info(f"Successfully processed camera data for {len(updated_parkings)} parking(s): {', '.join(parking_names)}")
        logger.info(f"=== END CAMERA MESSAGE PROCESSING ===")
        return jsonify({
            'status': 'ok', 
            'parkings': updated_parkings,
            'total_parkings_updated': len(updated_parkings)
        })
        
    except Exception as e:
        logger.error(f"Error inesperado procesando datos de cámara from {ip}: {e}")
        logger.error(f"Raw data that caused unexpected error: {raw_data}")
        
        # Registrar log de error
        try:
            log_camera_message(
                session=session,
                camera_ip=ip,
                camera_line=0,
                camera_name="",
                raw_message=raw_data,
                vehicle_in=0,
                vehicle_out=0,
                status="error",
                error_message=f"Unexpected error: {e}",
                processing_time=(time.time() - start_time) * 1000
            )
        except:
            pass
        
        # Asegurar que la sesión se cierre en caso de error
        try:
            session.close()
        except:
            pass
        logger.info(f"=== END CAMERA MESSAGE PROCESSING (WITH ERROR) ===")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/camera', methods=['GET'])
def camera_status():
    """Endpoint para verificar el estado del servidor de cámaras"""
    return jsonify({'status': 'ok', 'service': 'camera_server_unified'})

class CameraMonitor:
    """Monitor para verificar el estado de las cámaras periódicamente"""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.running = False
        self.monitor_thread = None
        self.check_interval = 300  # 5 minutos
        
    def start(self):
        """Iniciar el monitor de cámaras"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitor de cámaras iniciado")
        
    def stop(self):
        """Detener el monitor de cámaras"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitor de cámaras detenido")
        
    def _monitor_loop(self):
        """Bucle principal del monitor"""
        while self.running:
            try:
                self._check_all_cameras()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error en monitor de cámaras: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
                
    def _check_all_cameras(self):
        """Verificar el estado de todas las cámaras"""
        session = self.session_factory()
        try:
            cameras = session.query(Access).all()
            for camera in cameras:
                self._check_camera_status(camera, session)
        except Exception as e:
            logger.error(f"Error checking cameras: {e}")
        finally:
            session.close()
            
    def _check_camera_status(self, camera, session):
        """Verificar el estado de una cámara específica"""
        try:
            # Verificar si la cámara ha enviado mensajes recientemente
            if camera.last_message_received:
                time_since_last = datetime.now() - camera.last_message_received
                if time_since_last > timedelta(minutes=10):  # 10 minutos sin mensajes
                    if camera.status != 'OFFLINE':
                        camera.status = 'OFFLINE'
                        session.commit()
                        logger.warning(f"Camera {camera.name} marked as OFFLINE - No messages for {time_since_last}")
                else:
                    if camera.status != 'ONLINE':
                        camera.status = 'ONLINE'
                        session.commit()
                        logger.info(f"Camera {camera.name} marked as ONLINE")
            
            # Verificar conectividad de red (ping)
            if camera.ip:
                is_reachable = self._ping_camera(camera.ip)
                if not is_reachable and camera.status == 'ONLINE':
                    logger.warning(f"Camera {camera.name} ({camera.ip}) not responding to ping")
                    
        except Exception as e:
            logger.error(f"Error checking camera {camera.name}: {e}")
            
    def _ping_camera(self, ip):
        """Hacer ping a una cámara para verificar conectividad"""
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', ip], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error pinging {ip}: {e}")
            return False
            
    def _check_message_status(self, camera):
        """Verificar el estado de los mensajes de una cámara"""
        try:
            # Aquí se pueden agregar verificaciones adicionales
            # como validar la integridad de los datos recibidos
            pass
        except Exception as e:
            logger.error(f"Error checking message status for {camera.name}: {e}")

# Inicializar monitor de cámaras
camera_monitor = CameraMonitor(Session)

if __name__ == '__main__':
    # Iniciar monitor de cámaras
    camera_monitor.start()
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=6400, debug=False) 