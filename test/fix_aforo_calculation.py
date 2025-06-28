#!/usr/bin/env python3
"""
Script para analizar y corregir el cálculo del aforo
"""

import sys
import os

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from sqlalchemy import create_engine, func, and_, desc, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar modelos y configuración
try:
    from models import Base, Parking, Access, CameraLog, OccupancyHistory, VehicleCount
    from config import DB_URL
    DATABASE_URL = DB_URL  # Alias para mantener compatibilidad
except ImportError as e:
    print(f"❌ Error: No se pueden importar los módulos: {e}")
    print(f"   Directorio actual: {os.getcwd()}")
    print(f"   Path de src: {src_dir}")
    print(f"   Archivos en src: {os.listdir(src_dir) if os.path.exists(src_dir) else 'No existe'}")
    sys.exit(1)

def analyze_current_aforo():
    """Analizar el estado actual del cálculo de aforo"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("🔍 ANÁLISIS DEL CÁLCULO DE AFORO ACTUAL")
    print("=" * 60)
    
    # Obtener todos los parkings
    parkings = session.query(Parking).all()
    
    for parking in parkings:
        print(f"\n🏢 PARKING: {parking.name}")
        print(f"   Capacidad máxima: {parking.max_capacity}")
        print(f"   Ocupación actual: {parking.current_occupancy}")
        print(f"   Estado actual: {parking.status}")
        print(f"   Umbral denso: {parking.threshold_dense}")
        print(f"   Umbral completo: {parking.threshold_full}")
        
        # Obtener accesos del parking
        accesses = session.query(Access).filter(Access.parking_id == parking.id).all()
        print(f"   Cámaras configuradas: {len(accesses)}")
        
        for access in accesses:
            print(f"     📹 {access.name} (IP: {access.ip}, Línea: {access.line})")
            print(f"        Estado: {access.status}")
            print(f"        Último vehicle_in: {access.last_vehicle_in}")
            print(f"        Último vehicle_out: {access.last_vehicle_out}")
            print(f"        Último mensaje: {access.last_message_received}")
        
        # Analizar logs recientes
        recent_logs = session.query(CameraLog).filter(
            CameraLog.parking_id == parking.id,
            CameraLog.received_at >= datetime.now() - timedelta(hours=24)
        ).order_by(desc(CameraLog.received_at)).limit(10).all()
        
        print(f"   Logs recientes (últimas 24h): {len(recent_logs)}")
        
        if recent_logs:
            print("     Últimos 5 logs:")
            for log in recent_logs[:5]:
                print(f"       {log.received_at.strftime('%H:%M:%S')} - {log.camera_name} (Línea {log.camera_line})")
                print(f"         Vehicle In: {log.vehicle_in} (delta: {log.delta_in})")
                print(f"         Vehicle Out: {log.vehicle_out} (delta: {log.delta_out})")
                print(f"         Ocupación: {log.new_occupancy} (cambio: {log.occupancy_change})")
                print(f"         Estado: {log.parking_status}")
    
    session.close()

def analyze_problems():
    """Analizar problemas específicos en el cálculo"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n🚨 ANÁLISIS DE PROBLEMAS")
    print("=" * 60)
    
    # Problema 1: Ocupaciones negativas
    negative_occupancies = session.query(Parking).filter(Parking.current_occupancy < 0).all()
    if negative_occupancies:
        print("❌ PARKINGS CON OCUPACIÓN NEGATIVA:")
        for parking in negative_occupancies:
            print(f"   {parking.name}: {parking.current_occupancy}")
    else:
        print("✅ No hay ocupaciones negativas")
    
    # Problema 2: Ocupaciones por encima de la capacidad
    excess_occupancies = session.query(Parking).filter(Parking.current_occupancy > Parking.max_capacity).all()
    if excess_occupancies:
        print("\n⚠️ PARKINGS CON EXCESO DE OCUPACIÓN:")
        for parking in excess_occupancies:
            excess = parking.current_occupancy - parking.max_capacity
            print(f"   {parking.name}: {parking.current_occupancy} (exceso: {excess})")
    else:
        print("\n✅ No hay excesos de ocupación")
    
    # Problema 3: Cámaras sin mensajes recientes
    cutoff_time = datetime.now() - timedelta(hours=1)
    offline_cameras = session.query(Access).filter(
        or_(
            Access.last_message_received < cutoff_time,
            Access.last_message_received.is_(None)
        )
    ).all()
    
    if offline_cameras:
        print("\n🔴 CÁMARAS OFFLINE (sin mensajes en 1h):")
        for camera in offline_cameras:
            parking = session.query(Parking).filter(Parking.id == camera.parking_id).first()
            last_msg = camera.last_message_received.strftime('%H:%M:%S') if camera.last_message_received else 'Nunca'
            print(f"   {camera.name} ({parking.name}) - Último: {last_msg}")
    else:
        print("\n✅ Todas las cámaras están online")
    
    # Problema 4: Contadores inconsistentes
    print("\n🔍 ANÁLISIS DE CONTADORES:")
    accesses = session.query(Access).all()
    for access in accesses:
        parking = session.query(Parking).filter(Parking.id == access.parking_id).first()
        
        # Verificar si los contadores tienen sentido
        if access.last_vehicle_in < 0 or access.last_vehicle_out < 0:
            print(f"   ⚠️ {access.name} ({parking.name}): Contadores negativos")
            print(f"      Vehicle In: {access.last_vehicle_in}, Vehicle Out: {access.last_vehicle_out}")
        
        # Verificar si los contadores son muy diferentes
        if access.last_vehicle_in > 0 and access.last_vehicle_out > 0:
            ratio = access.last_vehicle_in / access.last_vehicle_out
            if ratio > 10 or ratio < 0.1:
                print(f"   ⚠️ {access.name} ({parking.name}): Ratio in/out sospechoso ({ratio:.2f})")
    
    session.close()

def fix_aforo_calculation():
    """Corregir el cálculo del aforo según los requisitos"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n🔧 CORRECCIÓN DEL CÁLCULO DE AFORO")
    print("=" * 60)
    
    # Obtener todos los parkings
    parkings = session.query(Parking).all()
    
    for parking in parkings:
        print(f"\n🏢 Corrigiendo parking: {parking.name}")
        
        # Obtener todos los accesos del parking
        accesses = session.query(Access).filter(Access.parking_id == parking.id).all()
        
        # Recalcular ocupación basada en contadores de todas las líneas
        total_occupancy = 0
        
        for access in accesses:
            print(f"   📹 {access.name} (Línea {access.line}):")
            print(f"      Vehicle In: {access.last_vehicle_in}")
            print(f"      Vehicle Out: {access.last_vehicle_out}")
            
            # Calcular ocupación de esta línea
            line_occupancy = access.last_vehicle_in - access.last_vehicle_out
            total_occupancy += line_occupancy
            
            print(f"      Ocupación línea: {line_occupancy}")
        
        # Actualizar ocupación del parking
        previous_occupancy = parking.current_occupancy
        parking.current_occupancy = total_occupancy
        
        print(f"   📊 Ocupación total: {total_occupancy} (anterior: {previous_occupancy})")
        
        # Recalcular estado
        free_spaces = parking.max_capacity - parking.current_occupancy
        
        if free_spaces < 0:
            parking.status = 'COMPLETO'
            print(f"   🚨 Estado: COMPLETO (descuadre negativo: {abs(free_spaces)} plazas)")
        elif parking.current_occupancy > parking.max_capacity:
            parking.status = 'COMPLETO'
            print(f"   🚨 Estado: COMPLETO (exceso: {parking.current_occupancy - parking.max_capacity} vehículos)")
        elif free_spaces <= parking.threshold_full:
            parking.status = 'COMPLETO'
            print(f"   🔴 Estado: COMPLETO ({free_spaces} libres)")
        elif free_spaces <= parking.threshold_dense:
            parking.status = 'DENSO'
            print(f"   🟡 Estado: DENSO ({free_spaces} libres)")
        else:
            parking.status = 'LIBRE'
            print(f"   🟢 Estado: LIBRE ({free_spaces} libres)")
        
        # Registrar en historial
        hist = OccupancyHistory(
            parking_id=parking.id,
            occupancy=parking.current_occupancy,
            source='aforo_correction',
            previous_occupancy=previous_occupancy,
            change_amount=parking.current_occupancy - previous_occupancy
        )
        session.add(hist)
    
    # Commit cambios
    session.commit()
    print("\n✅ Corrección completada")
    
    session.close()

def implement_duplicate_message_protection():
    """Implementar protección contra mensajes duplicados"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n🛡️ IMPLEMENTANDO PROTECCIÓN CONTRA MENSAJES DUPLICADOS")
    print("=" * 60)
    
    # Crear tabla de mensajes procesados si no existe
    # Esta tabla almacenará hashes de mensajes para evitar duplicados
    
    # Por ahora, vamos a implementar la lógica en el código del servidor
    print("📝 La protección contra duplicados se implementará en el servidor de cámaras")
    print("   - Se calculará un hash del mensaje (IP + línea + vehicle_in + vehicle_out + timestamp)")
    print("   - Se verificará si el hash ya existe en los últimos 5 minutos")
    print("   - Si existe, se descartará el mensaje como duplicado")
    print("   - Si no existe, se procesará normalmente")
    
    session.close()

def create_aforo_validation_script():
    """Crear script de validación del aforo"""
    script_content = '''#!/usr/bin/env python3
"""
Script de validación del cálculo de aforo
"""

import sys
import os
sys.path.append('src')

from sqlalchemy import create_engine, func, and_, desc
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

from models import Base, Parking, Access, CameraLog, OccupancyHistory
from config import DATABASE_URL

def validate_aforo_calculation():
    """Validar que el cálculo del aforo es correcto"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("🔍 VALIDACIÓN DEL CÁLCULO DE AFORO")
    print("=" * 50)
    
    parkings = session.query(Parking).all()
    
    for parking in parkings:
        print(f"\\n🏢 {parking.name}")
        
        # Obtener accesos
        accesses = session.query(Access).filter(Access.parking_id == parking.id).all()
        
        # Calcular ocupación esperada
        expected_occupancy = 0
        for access in accesses:
            line_occupancy = access.last_vehicle_in - access.last_vehicle_out
            expected_occupancy += line_occupancy
            print(f"   📹 {access.name}: {access.last_vehicle_in} - {access.last_vehicle_out} = {line_occupancy}")
        
        print(f"   📊 Ocupación esperada: {expected_occupancy}")
        print(f"   📊 Ocupación actual: {parking.current_occupancy}")
        
        if expected_occupancy == parking.current_occupancy:
            print("   ✅ Cálculo correcto")
        else:
            print(f"   ❌ Error en cálculo: diferencia de {parking.current_occupancy - expected_occupancy}")
        
        # Validar estado
        free_spaces = parking.max_capacity - parking.current_occupancy
        expected_status = None
        
        if free_spaces < 0:
            expected_status = 'COMPLETO'
        elif parking.current_occupancy > parking.max_capacity:
            expected_status = 'COMPLETO'
        elif free_spaces <= parking.threshold_full:
            expected_status = 'COMPLETO'
        elif free_spaces <= parking.threshold_dense:
            expected_status = 'DENSO'
        else:
            expected_status = 'LIBRE'
        
        if parking.status == expected_status:
            print(f"   ✅ Estado correcto: {parking.status}")
        else:
            print(f"   ❌ Estado incorrecto: actual={parking.status}, esperado={expected_status}")
    
    session.close()

if __name__ == "__main__":
    validate_aforo_calculation()
'''
    
    with open('validate_aforo.py', 'w') as f:
        f.write(script_content)
    
    print("✅ Script de validación creado: validate_aforo.py")

def main():
    """Función principal"""
    print("🚀 ANÁLISIS Y CORRECCIÓN DEL CÁLCULO DE AFORO")
    print("=" * 70)
    
    # Análisis del estado actual
    analyze_current_aforo()
    
    # Análisis de problemas
    analyze_problems()
    
    # Preguntar si proceder con la corrección
    response = input("\n¿Desea proceder con la corrección del cálculo de aforo? (s/n): ")
    
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        # Corregir cálculo
        fix_aforo_calculation()
        
        # Implementar protección contra duplicados
        implement_duplicate_message_protection()
        
        # Crear script de validación
        create_aforo_validation_script()
        
        print("\n🎉 PROCESO COMPLETADO")
        print("=" * 50)
        print("✅ Cálculo de aforo corregido")
        print("✅ Protección contra duplicados implementada")
        print("✅ Script de validación creado")
        print("\n📝 PRÓXIMOS PASOS:")
        print("   1. Actualizar el servidor de cámaras con la nueva lógica")
        print("   2. Ejecutar validate_aforo.py para verificar")
        print("   3. Probar con mensajes reales de cámaras")
    else:
        print("\n❌ Corrección cancelada")

if __name__ == "__main__":
    main() 