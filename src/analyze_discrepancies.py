#!/usr/bin/env python3
"""
Script para analizar descuadres en el sistema de parking
Genera estadísticas y sugerencias de corrección automática
"""

from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
import config
from models import Base, Parking, OccupancyHistory
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)

def analyze_discrepancies(days_back=7):
    """
    Analiza descuadres en los últimos N días
    """
    session = Session()
    
    # Fecha límite para el análisis
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    print(f"\n=== ANÁLISIS DE DESCUADRES - ÚLTIMOS {days_back} DÍAS ===")
    print(f"Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Período analizado: {cutoff_date.strftime('%Y-%m-%d')} hasta {datetime.now().strftime('%Y-%m-%d')}")
    
    # Obtener todos los parkings
    parkings = session.query(Parking).all()
    
    for parking in parkings:
        print(f"\n--- PARKING: {parking.name} ---")
        print(f"Capacidad máxima: {parking.max_capacity}")
        print(f"Ocupación actual: {parking.current_occupancy}")
        print(f"Estado actual: {parking.status}")
        
        # Analizar histórico reciente
        recent_history = session.query(OccupancyHistory).filter(
            OccupancyHistory.parking_id == parking.id,
            OccupancyHistory.timestamp >= cutoff_date
        ).order_by(OccupancyHistory.timestamp.desc()).all()
        
        if not recent_history:
            print("  No hay datos recientes")
            continue
        
        # Contadores de descuadres
        excess_count = 0
        negative_count = 0
        total_records = len(recent_history)
        max_excess = 0
        max_negative = 0
        
        for record in recent_history:
            free_spaces = parking.max_capacity - record.occupancy
            
            if record.occupancy > parking.max_capacity:
                excess_count += 1
                excess_amount = record.occupancy - parking.max_capacity
                max_excess = max(max_excess, excess_amount)
            elif free_spaces < 0:
                negative_count += 1
                negative_amount = abs(free_spaces)
                max_negative = max(max_negative, negative_amount)
        
        # Estadísticas
        print(f"  Total registros analizados: {total_records}")
        print(f"  Registros con exceso: {excess_count} ({excess_count/total_records*100:.1f}%)")
        print(f"  Registros con plazas negativas: {negative_count} ({negative_count/total_records*100:.1f}%)")
        
        if max_excess > 0:
            print(f"  Máximo exceso registrado: {max_excess} vehículos")
        if max_negative > 0:
            print(f"  Máximo descuadre negativo: {max_negative} vehículos")
        
        # Sugerencias de corrección
        if excess_count > total_records * 0.1:  # Más del 10% con exceso
            print(f"  ⚠️  ALERTA: Alto porcentaje de excesos - Revisar capacidad o sistema de conteo")
        
        if negative_count > total_records * 0.05:  # Más del 5% con negativos
            print(f"  ⚠️  ALERTA: Descuadres negativos frecuentes - Revisar sistema de conteo")
        
        # Análisis de tendencias
        if recent_history:
            first_record = recent_history[-1]
            last_record = recent_history[0]
            trend = last_record.occupancy - first_record.occupancy
            
            if abs(trend) > parking.max_capacity * 0.1:  # Cambio mayor al 10% de capacidad
                print(f"  📈 Tendencia significativa: {trend:+d} vehículos en el período")
                if trend > 0:
                    print(f"     → Aumento de ocupación - Considerar ajustar capacidad")
                else:
                    print(f"     → Disminución de ocupación - Posible corrección automática")

def generate_correction_suggestions():
    """
    Genera sugerencias de corrección automática basadas en descuadres
    """
    session = Session()
    
    print(f"\n=== SUGERENCIAS DE CORRECCIÓN AUTOMÁTICA ===")
    
    # Analizar parkings con descuadres actuales
    parkings_with_issues = session.query(Parking).filter(
        Parking.status.in_(['COMPLETO_EXCESO', 'DESCUADRE_NEGATIVO'])
    ).all()
    
    if not parkings_with_issues:
        print("No hay parkings con descuadres actuales")
        return
    
    for parking in parkings_with_issues:
        print(f"\n--- CORRECCIÓN SUGERIDA PARA: {parking.name} ---")
        
        free_spaces = parking.max_capacity - parking.current_occupancy
        
        if parking.status == 'COMPLETO_EXCESO':
            excess = parking.current_occupancy - parking.max_capacity
            print(f"Estado actual: COMPLETO_EXCESO (+{excess} vehículos)")
            
            # Sugerencias
            if excess <= 5:
                print(f"  💡 Sugerencia: Ajuste menor - Reducir ocupación en {excess} vehículos")
                print(f"     Comando: POST /parking/{parking.id}/occupancy")
                print(f"     Body: {{'occupancy': {parking.max_capacity}}}")
            else:
                print(f"  💡 Sugerencia: Revisar capacidad - Considerar aumentar en {excess} plazas")
                print(f"     Comando: POST /parking/{parking.id}/config")
                print(f"     Body: {{'max_capacity': {parking.max_capacity + excess}}}")
        
        elif parking.status == 'DESCUADRE_NEGATIVO':
            print(f"Estado actual: DESCUADRE_NEGATIVO ({free_spaces} plazas libres)")
            
            # Sugerencias
            if abs(free_spaces) <= 10:
                print(f"  💡 Sugerencia: Corrección de conteo - Ajustar ocupación")
                print(f"     Comando: POST /parking/{parking.id}/occupancy")
                print(f"     Body: {{'occupancy': {parking.max_capacity}}}")
            else:
                print(f"  💡 Sugerencia: Revisión urgente - Descuadre significativo")
                print(f"     Verificar sistema de conteo y cámaras")

def export_discrepancy_report(filename=None):
    """
    Exporta un reporte de descuadres a CSV
    """
    if not filename:
        filename = f"discrepancy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    session = Session()
    
    # Obtener datos de descuadres
    cutoff_date = datetime.now() - timedelta(days=30)  # Último mes
    
    query = session.query(
        Parking.name,
        Parking.max_capacity,
        OccupancyHistory.occupancy,
        OccupancyHistory.timestamp,
        OccupancyHistory.source
    ).join(OccupancyHistory).filter(
        OccupancyHistory.timestamp >= cutoff_date
    ).order_by(Parking.name, OccupancyHistory.timestamp.desc())
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Parking,Capacidad,Ocupacion,Fecha,Fuente,Plazas_Libres,Descuadre\n")
        
        for row in query.all():
            parking_name, max_cap, occupancy, timestamp, source = row
            free_spaces = max_cap - occupancy
            
            if occupancy > max_cap:
                discrepancy = f"EXCESS:{occupancy - max_cap}"
            elif free_spaces < 0:
                discrepancy = f"NEGATIVE_FREE:{abs(free_spaces)}"
            else:
                discrepancy = "NONE"
            
            f.write(f"{parking_name},{max_cap},{occupancy},{timestamp},{source},{free_spaces},{discrepancy}\n")
    
    print(f"\nReporte exportado a: {filename}")
    session.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'analyze':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            analyze_discrepancies(days)
        elif command == 'suggestions':
            generate_correction_suggestions()
        elif command == 'export':
            filename = sys.argv[2] if len(sys.argv) > 2 else None
            export_discrepancy_report(filename)
        else:
            print("Comandos disponibles:")
            print("  analyze [días] - Analizar descuadres (default: 7 días)")
            print("  suggestions    - Generar sugerencias de corrección")
            print("  export [archivo] - Exportar reporte CSV")
    else:
        # Ejecutar análisis completo por defecto
        analyze_discrepancies(7)
        generate_correction_suggestions() 