#!/usr/bin/env python3
"""
Script de Bootstrap para Sistema de Corrección Automática v4.5.0

Este script analiza los últimos 12 meses de ajustes manuales para calcular
los parámetros iniciales del algoritmo de corrección automática.

Uso:
    python auto_correction_bootstrap.py [--days 365] [--parking-id ID]

Autor: Parking Altea Team
Fecha: 2026-01-26
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import (
    Parking, OccupancyHistory, 
    ParkingCorrectionConfig, CorrectionCalculation
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://parking_user:parking_pass@localhost:5432/parking_db')


def get_session():
    """Crear sesión de base de datos"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def calculate_drift(prev_correct_occupancy, current_wrong_occupancy, hours_between):
    """
    Calcular drift (desviación) por hora.
    
    El drift representa cuánto se desvía el sistema del valor correcto
    por cada hora transcurrida.
    
    Args:
        prev_correct_occupancy: Ocupación correcta establecida en el ajuste anterior
        current_wrong_occupancy: Ocupación incorrecta del sistema antes del ajuste actual
        hours_between: Horas transcurridas entre ajustes
    
    Returns:
        float: Desviación por hora
    """
    if hours_between <= 0:
        return 0
    
    # La desviación es la diferencia entre lo que debería ser y lo que tiene el sistema
    # Si prev_correct = 100 y current_wrong = 115, el sistema ha añadido 15 de más
    # Por tanto el drift = (115 - 100) / horas = desviación positiva (sistema suma de más)
    drift = (current_wrong_occupancy - prev_correct_occupancy) / hours_between
    return drift


def analyze_parking_adjustments(session, parking_id, days=365):
    """
    Analizar ajustes manuales de un parking para calcular patrones.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        days: Días hacia atrás a analizar
    
    Returns:
        dict: Estadísticas calculadas
    """
    date_limit = datetime.now() - timedelta(days=days)
    
    # Obtener parking
    parking = session.query(Parking).get(parking_id)
    if not parking:
        logger.warning(f"Parking {parking_id} no encontrado")
        return None
    
    # Obtener todos los ajustes manuales ordenados por timestamp
    adjustments = session.query(OccupancyHistory).filter(
        OccupancyHistory.parking_id == parking_id,
        OccupancyHistory.source == 'manual',
        OccupancyHistory.timestamp >= date_limit
    ).order_by(OccupancyHistory.timestamp.asc()).all()
    
    if len(adjustments) < 2:
        logger.info(f"Parking {parking.name}: Insuficientes ajustes ({len(adjustments)})")
        return {
            'parking_id': parking_id,
            'parking_name': parking.name,
            'sample_count': len(adjustments),
            'insufficient_data': True
        }
    
    logger.info(f"Parking {parking.name}: Analizando {len(adjustments)} ajustes manuales")
    
    # Estructuras para acumular datos
    calculations = []
    drift_by_weekday = defaultdict(list)
    occupancy_by_weekday = defaultdict(list)
    all_drifts = []
    
    # Procesar pares de ajustes consecutivos
    for i in range(1, len(adjustments)):
        prev_adj = adjustments[i - 1]
        curr_adj = adjustments[i]
        
        # Calcular horas entre ajustes
        time_diff = curr_adj.timestamp - prev_adj.timestamp
        hours_between = time_diff.total_seconds() / 3600
        
        # Ignorar ajustes muy cercanos (< 1 hora)
        if hours_between < 1:
            continue
        
        # Ignorar períodos muy largos (> 7 días) - podrían distorsionar
        if hours_between > 168:  # 7 días
            continue
        
        # Datos del ajuste actual
        occupancy_before = curr_adj.previous_occupancy if curr_adj.previous_occupancy is not None else 0
        occupancy_after = curr_adj.occupancy
        correction = curr_adj.change_amount if curr_adj.change_amount is not None else (occupancy_after - occupancy_before)
        
        # El valor correcto del ajuste anterior
        prev_correct = prev_adj.occupancy
        
        # Calcular drift
        # Si prev_correct=100 y ahora el sistema dice occupancy_before=115,
        # el sistema se ha desviado +15 en X horas
        drift = calculate_drift(prev_correct, occupancy_before, hours_between)
        drift_total = occupancy_before - prev_correct
        
        # Datos temporales
        weekday = curr_adj.timestamp.weekday()  # 0=Lunes, 6=Domingo
        hour = curr_adj.timestamp.hour
        
        # Crear registro de cálculo
        calc = {
            'parking_id': parking_id,
            'adjustment_timestamp': curr_adj.timestamp,
            'hours_since_last_correction': hours_between,
            'time_of_day': hour,
            'day_of_week': weekday,
            'occupancy_before_adjustment': occupancy_before,
            'occupancy_after_adjustment': occupancy_after,
            'correction_applied': correction,
            'drift_per_hour': drift,
            'drift_total': drift_total,
            'parking_capacity': parking.max_capacity,
            'occupancy_percentage_before': (occupancy_before / parking.max_capacity * 100) if parking.max_capacity > 0 else 0,
            'occupancy_percentage_after': (occupancy_after / parking.max_capacity * 100) if parking.max_capacity > 0 else 0,
            'trigger_type': 'bootstrap'
        }
        
        calculations.append(calc)
        
        # Acumular por día de semana
        drift_by_weekday[weekday].append(drift)
        occupancy_by_weekday[weekday].append(occupancy_after)
        all_drifts.append(drift)
    
    if not calculations:
        logger.info(f"Parking {parking.name}: No hay cálculos válidos")
        return {
            'parking_id': parking_id,
            'parking_name': parking.name,
            'sample_count': 0,
            'insufficient_data': True
        }
    
    # Calcular promedios globales
    avg_hourly_drift = sum(all_drifts) / len(all_drifts)
    avg_daily_drift = avg_hourly_drift * 24
    
    # Calcular promedios por día de semana
    weekday_drifts = {}
    weekday_samples = {}
    weekday_occupancy = {}
    
    for day in range(7):
        if drift_by_weekday[day]:
            weekday_drifts[str(day)] = sum(drift_by_weekday[day]) / len(drift_by_weekday[day])
            weekday_samples[str(day)] = len(drift_by_weekday[day])
        else:
            weekday_drifts[str(day)] = avg_hourly_drift  # Usar promedio global si no hay datos
            weekday_samples[str(day)] = 0
        
        if occupancy_by_weekday[day]:
            weekday_occupancy[str(day)] = sum(occupancy_by_weekday[day]) / len(occupancy_by_weekday[day])
        else:
            weekday_occupancy[str(day)] = 0
    
    # Calcular confianza
    confidence = min(len(calculations) / 20, 1.0)  # 20 muestras = 100% confianza
    
    # Corrección sugerida para próximas 24 horas
    suggested_correction = round(avg_hourly_drift * 24)
    
    return {
        'parking_id': parking_id,
        'parking_name': parking.name,
        'sample_count': len(calculations),
        'insufficient_data': False,
        'calculations': calculations,
        'avg_hourly_drift': avg_hourly_drift,
        'avg_daily_drift': avg_daily_drift,
        'confidence_level': confidence,
        'drift_by_weekday': weekday_drifts,
        'samples_by_weekday': weekday_samples,
        'avg_occupancy_by_weekday': weekday_occupancy,
        'suggested_correction': suggested_correction
    }


def save_calculations(session, calculations):
    """Guardar cálculos en la base de datos"""
    for calc in calculations:
        record = CorrectionCalculation(
            parking_id=calc['parking_id'],
            adjustment_timestamp=calc['adjustment_timestamp'],
            hours_since_last_correction=calc['hours_since_last_correction'],
            time_of_day=calc['time_of_day'],
            day_of_week=calc['day_of_week'],
            occupancy_before_adjustment=calc['occupancy_before_adjustment'],
            occupancy_after_adjustment=calc['occupancy_after_adjustment'],
            correction_applied=calc['correction_applied'],
            drift_per_hour=calc['drift_per_hour'],
            drift_total=calc['drift_total'],
            parking_capacity=calc['parking_capacity'],
            occupancy_percentage_before=calc['occupancy_percentage_before'],
            occupancy_percentage_after=calc['occupancy_percentage_after'],
            trigger_type=calc['trigger_type']
        )
        session.add(record)
    
    session.commit()


def update_parking_config(session, stats):
    """Actualizar o crear configuración del parking"""
    config = session.query(ParkingCorrectionConfig).filter_by(
        parking_id=stats['parking_id']
    ).first()
    
    if not config:
        config = ParkingCorrectionConfig(
            parking_id=stats['parking_id'],
            auto_correction_enabled=True  # Habilitado por defecto
        )
        session.add(config)
    
    # Actualizar parámetros
    config.avg_hourly_drift = stats['avg_hourly_drift']
    config.avg_daily_drift = stats['avg_daily_drift']
    config.confidence_level = stats['confidence_level']
    config.sample_count = stats['sample_count']
    config.drift_by_weekday = stats['drift_by_weekday']
    config.samples_by_weekday = stats['samples_by_weekday']
    config.avg_occupancy_by_weekday = stats['avg_occupancy_by_weekday']
    config.suggested_correction = stats['suggested_correction']
    config.last_calculation_at = datetime.now()
    
    session.commit()


def run_bootstrap(days=365, parking_id=None):
    """
    Ejecutar bootstrap del sistema de corrección automática.
    
    Args:
        days: Días hacia atrás a analizar
        parking_id: ID específico de parking (None para todos)
    """
    session = get_session()
    
    try:
        # Obtener parkings a procesar
        if parking_id:
            parkings = session.query(Parking).filter_by(id=parking_id).all()
        else:
            parkings = session.query(Parking).all()
        
        logger.info(f"=" * 60)
        logger.info(f"BOOTSTRAP DE CORRECCIÓN AUTOMÁTICA")
        logger.info(f"Parkings a procesar: {len(parkings)}")
        logger.info(f"Período de análisis: últimos {days} días")
        logger.info(f"=" * 60)
        
        results_summary = []
        
        for parking in parkings:
            logger.info(f"\n--- Procesando: {parking.name} (ID: {parking.id}) ---")
            
            # Analizar ajustes
            stats = analyze_parking_adjustments(session, parking.id, days)
            
            if stats is None:
                continue
            
            if stats.get('insufficient_data'):
                logger.info(f"  → Datos insuficientes ({stats.get('sample_count', 0)} muestras)")
                results_summary.append({
                    'parking': parking.name,
                    'status': 'insufficient_data',
                    'samples': stats.get('sample_count', 0)
                })
                continue
            
            # Guardar cálculos
            if stats.get('calculations'):
                save_calculations(session, stats['calculations'])
                logger.info(f"  → {len(stats['calculations'])} cálculos guardados")
            
            # Actualizar configuración
            update_parking_config(session, stats)
            
            # Mostrar resultados
            logger.info(f"  → Drift promedio/hora: {stats['avg_hourly_drift']:.3f}")
            logger.info(f"  → Drift promedio/día: {stats['avg_daily_drift']:.1f}")
            logger.info(f"  → Corrección sugerida (24h): {stats['suggested_correction']}")
            logger.info(f"  → Confianza: {stats['confidence_level']*100:.0f}%")
            logger.info(f"  → Drift por día de semana:")
            
            weekday_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            for day in range(7):
                drift = stats['drift_by_weekday'].get(str(day), 0)
                samples = stats['samples_by_weekday'].get(str(day), 0)
                logger.info(f"      {weekday_names[day]}: {drift:+.3f}/h ({samples} muestras)")
            
            results_summary.append({
                'parking': parking.name,
                'status': 'success',
                'samples': stats['sample_count'],
                'drift_daily': stats['avg_daily_drift'],
                'confidence': stats['confidence_level']
            })
        
        # Resumen final
        logger.info(f"\n" + "=" * 60)
        logger.info("RESUMEN DEL BOOTSTRAP")
        logger.info("=" * 60)
        
        success_count = sum(1 for r in results_summary if r['status'] == 'success')
        insufficient_count = sum(1 for r in results_summary if r['status'] == 'insufficient_data')
        
        logger.info(f"Total parkings procesados: {len(results_summary)}")
        logger.info(f"  ✓ Con datos suficientes: {success_count}")
        logger.info(f"  ✗ Datos insuficientes: {insufficient_count}")
        
        if success_count > 0:
            logger.info(f"\nParkings con corrección automática configurada:")
            for r in sorted(results_summary, key=lambda x: x.get('drift_daily', 0), reverse=True):
                if r['status'] == 'success':
                    logger.info(f"  • {r['parking']}: {r['drift_daily']:+.1f}/día, {r['samples']} muestras, {r['confidence']*100:.0f}% conf.")
        
        logger.info(f"\n✓ Bootstrap completado")
        
    except Exception as e:
        logger.error(f"Error en bootstrap: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Bootstrap del sistema de corrección automática'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=365,
        help='Días hacia atrás a analizar (default: 365)'
    )
    parser.add_argument(
        '--parking-id',
        type=int,
        default=None,
        help='ID de parking específico (default: todos)'
    )
    
    args = parser.parse_args()
    
    run_bootstrap(days=args.days, parking_id=args.parking_id)


if __name__ == '__main__':
    main()
