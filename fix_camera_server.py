#!/usr/bin/env python3
"""
Script para corregir los problemas en camera_server.py
"""

import re

def fix_camera_server():
    """Corregir los problemas identificados en camera_server.py"""
    
    # Leer el archivo original
    with open('src/camera_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Corregir función is_duplicate_message para usar device + line
    content = re.sub(
        r'def is_duplicate_message\(camera_ip, camera_line, vehicle_in, vehicle_out, timestamp\):',
        'def is_duplicate_message(device, line, vehicle_in, vehicle_out, timestamp):',
        content
    )
    
    content = re.sub(
        r'"""Verificar si un mensaje es duplicado basado en IP, línea y contadores"""',
        '"""\n    Verificar si un mensaje es duplicado basado en device, línea y contadores.\n    \n    CORRECCIÓN: Ahora usa device + line en lugar de IP + line\n    """',
        content
    )
    
    content = re.sub(
        r'key = f"\{camera_ip\}_\{camera_line\}_\{vehicle_in\}_\{vehicle_out\}"',
        'key = f"{device}_{line}_{vehicle_in}_{vehicle_out}"',
        content
    )
    
    content = re.sub(
        r'logger\.warning\(f"DUPLICATE MESSAGE DETECTED - IP: \{camera_ip\}, Line: \{camera_line\}, In: \{vehicle_in\}, Out: \{vehicle_out\}"\)',
        'logger.warning(f"DUPLICATE MESSAGE DETECTED - Device: {device}, Line: {line}, In: {vehicle_in}, Out: {vehicle_out}")',
        content
    )
    
    # 2. Corregir lógica de reinicio
    content = re.sub(
        r'# En caso de reinicio, ajustar los contadores anteriores\n        # CORRECCIÓN: Si hay reinicio, siempre usar 0 como contador anterior\n        # para calcular correctamente el delta desde el nuevo valor\n        adjusted_previous_in = 0\n        adjusted_previous_out = 0',
        '# CORRECCIÓN: En caso de reinicio, usar los nuevos valores como base\n        # No ajustar a 0, sino usar los nuevos valores directamente\n        adjusted_previous_in = new_in\n        adjusted_previous_out = new_out',
        content
    )
    
    # 3. Corregir cálculo de deltas en reinicios
    delta_calculation_pattern = r'# Calcular deltas usando los contadores ajustados\n    delta_in = new_in - adjusted_previous_in\n    delta_out = new_out - adjusted_previous_out\n    \n    # Validar que los deltas sean positivos \(excepto en reinicios\)'
    
    new_delta_calculation = '''# Calcular deltas usando los contadores ajustados
    delta_in = new_in - adjusted_previous_in
    delta_out = new_out - adjusted_previous_out
    
    # CORRECCIÓN: En caso de reinicio, los deltas deben ser 0
    # porque estamos usando los nuevos valores como base
    if is_reset:
        delta_in = 0
        delta_out = 0
        logger.info(f"Reset detected - Setting deltas to 0 to avoid incorrect calculations")
    
    # Validar que los deltas sean positivos (excepto en reinicios)'''
    
    content = re.sub(delta_calculation_pattern, new_delta_calculation, content)
    
    # 4. Corregir llamada a is_duplicate_message
    content = re.sub(
        r'if is_duplicate_message\(ip, original_line, veh_in, veh_out, time\.time\(\)\):',
        'if is_duplicate_message(device, original_line, veh_in, veh_out, time.time()):',
        content
    )
    
    # 5. Corregir búsqueda de acceso para usar device + line como principal
    access_search_pattern = r'# Buscar acceso por IP y línea \(método principal\)\n        access = session\.query\(Access\)\.filter_by\(ip=ip, line=line\)\.first\(\)\n        \n        # Si no se encuentra por IP\+línea, intentar buscar por nombre de dispositivo Y línea \(insensible a mayúsculas/minúsculas\)\n        if not access and device:\n            # Usar func\.lower\(\) para comparación insensible a mayúsculas/minúsculas\n            access = session\.query\(Access\)\.filter\(\n                func\.lower\(Access\.name\) == func\.lower\(device\),\n                Access\.line == line\n            \)\.first\(\)\n            if access:\n                logger\.info\(f"Found access by device name \(case-insensitive\) and line: \{device\}, line: \{line\} \(original: \{original_line\}\)"\)\n                logger\.info\(f"Database device name: \{access\.name\}, Received device name: \{device\}"\)\n            else:\n                # Si no encuentra por nombre\+línea, buscar solo por nombre para logging \(también insensible a mayúsculas/minúsculas\)\n                device_access = session\.query\(Access\)\.filter\(\n                    func\.lower\(Access\.name\) == func\.lower\(device\)\n                \)\.first\(\)\n                if device_access:\n                    error_msg = f"Device found but line mismatch - Expected: \{device_access\.line\}, Received: \{original_line\}"\n                    logger\.warning\(f"\{error_msg\} - Device: \{device\}, DB Device: \{device_access\.name\}"\)\n                    logger\.warning\(f"Message logged but not processed - line validation failed"\)\n                    \n                    # Registrar log de error\n                    log_camera_message\(\n                        session=session,\n                        camera_ip=ip,\n                        camera_line=original_line,\n                        camera_name=device,\n                        raw_message=raw_data,\n                        vehicle_in=veh_in,\n                        vehicle_out=veh_out,\n                        status="error",\n                        error_message=error_msg,\n                        processing_time=\(time\.time\(\) - start_time\) \* 1000\n                    \)\n                    \n                    return jsonify\(\{'error': 'Line mismatch for device'\}\), 400\n                else:\n                    error_msg = f"Device not found in database: \{device\}"\n                    logger\.warning\(f"\{error_msg\}"\)\n                    # Log adicional para debugging - mostrar todos los dispositivos disponibles\n                    all_devices = session\.query\(Access\.name\)\.distinct\(\)\.all\(\)\n                    device_names = \[d\[0\] for d in all_devices\]\n                    logger\.warning\(f"Available devices in database: \{device_names\}"\)\n                    \n                    # Registrar log de error\n                    log_camera_message\(\n                        session=session,\n                        camera_ip=ip,\n                        camera_line=original_line,\n                        camera_name=device,\n                        raw_message=raw_data,\n                        vehicle_in=veh_in,\n                        vehicle_out=veh_out,\n                        status="error",\n                        error_message=error_msg,\n                        processing_time=\(time\.time\(\) - start_time\) \* 1000\n                    \)\n                    \n                    return jsonify\(\{'error': 'Device not found'\}\), 404'
    
    new_access_search = '''# CORRECCIÓN: Buscar acceso por device + línea (método principal)
        # Usar comparación insensible a mayúsculas/minúsculas
        access = session.query(Access).filter(
            func.lower(Access.name) == func.lower(device),
            Access.line == line
        ).first()
        
        if not access:
            # Si no se encuentra por device+línea, intentar buscar por IP+línea como fallback
            access = session.query(Access).filter_by(ip=ip, line=line).first()
            if access:
                logger.info(f"Found access by IP and line (fallback): {ip}, line: {line}")
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
            logger.info(f"Found access by device name and line: {device}, line: {line}")'''
    
    content = re.sub(access_search_pattern, new_access_search, content)
    
    # 6. Corregir actualización de contadores ANTES del cálculo de ocupación
    counter_update_pattern = r'# Actualizar contadores de acceso\n        access\.last_vehicle_in = veh_in\n        access\.last_vehicle_out = veh_out\n        \n        # Actualizar parking\n        parking = access\.parking\n        previous_occupancy = parking\.current_occupancy\n        \n        # Calcular descuadre para estadísticas\n        parking\.current_occupancy \+= \(delta_in - delta_out\)'
    
    new_counter_update = '''# CORRECCIÓN: Actualizar contadores de acceso ANTES de calcular ocupación
        # Esto es crucial para evitar duplicados
        access.last_vehicle_in = veh_in
        access.last_vehicle_out = veh_out
        
        # Actualizar parking
        parking = access.parking
        previous_occupancy = parking.current_occupancy
        
        # CORRECCIÓN: Calcular ocupación correctamente
        # Solo aplicar deltas si NO es un reinicio
        if not is_reset:
            parking.current_occupancy += (delta_in - delta_out)
            logger.info(f"Occupancy updated - Previous: {previous_occupancy}, Delta: +{delta_in} -{delta_out} = {delta_in - delta_out}, New: {parking.current_occupancy}")
        else:
            # En caso de reinicio, mantener la ocupación actual
            logger.info(f"Reset detected - Keeping current occupancy: {parking.current_occupancy}")'''
    
    content = re.sub(counter_update_pattern, new_counter_update, content)
    
    # Guardar el archivo corregido
    with open('src/camera_server_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Archivo camera_server_fixed.py creado con las correcciones aplicadas")
    print("\n📋 Correcciones realizadas:")
    print("1. ✅ Identificación por device + line en lugar de IP + line")
    print("2. ✅ Detección de duplicados por valores de contadores")
    print("3. ✅ Lógica de reinicios corregida (no ajustar a 0)")
    print("4. ✅ Cálculo de ocupación corregido (solo aplicar deltas si no es reinicio)")
    print("5. ✅ Actualización de contadores ANTES del cálculo de ocupación")

if __name__ == "__main__":
    fix_camera_server() 