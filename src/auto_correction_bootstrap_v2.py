#!/usr/bin/env python3
"""
Bootstrap de Corrección Automática v4.5.1

Analiza el historial de ajustes manuales y calcula:
1. Ratio de corrección por día de semana
2. Transacciones asociadas a cada ajuste
3. Error por transacción
4. Ocupación esperada

Uso:
    python auto_correction_bootstrap_v2.py --days 300

Autor: Parking Altea Team
Fecha: 2026-01-27
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from statistics import mean, stdev

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker

from models import (
    Parking, OccupancyHistory, CameraLog,
    ParkingCorrectionConfig, CorrectionCalculation
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://parking_user:parking_pass@localhost:5432/parking_db')

WEEKDAY_NAMES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']


def make_naive(dt: datetime) -> datetime:
    """Convertir datetime a naive"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def count_transactions_between(session, parking_id: int, start: datetime, end: datetime) -> int:
    """
    Contar transacciones (entradas + salidas) entre dos fechas.
    """
    start_naive = make_naive(start)
    end_naive = make_naive(end)
    
    result = session.query(
        func.coalesce(func.sum(func.abs(CameraLog.delta_in)), 0).label('total_in'),
        func.coalesce(func.sum(func.abs(CameraLog.delta_out)), 0).label('total_out')
    ).filter(
        CameraLog.parking_id == parking_id,
        CameraLog.processed_at >= start_naive,
        CameraLog.processed_at <= end_naive,
        CameraLog.status.like('%processed%')
    ).first()
    
    if result:
        return int(result.total_in or 0) + int(result.total_out or 0)
    return 0


def process_parking_history(session, parking_id: int, days: int) -> Dict:
    """
    Procesar historial de un parking y calcular métricas.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        days: Días hacia atrás para analizar
    
    Returns:
        Dict con métricas calculadas
    """
    parking = session.query(Parking).get(parking_id)
    if not parking:
        return {'error': 'Parking no encontrado'}
    
    date_limit = datetime.now() - timedelta(days=days)
    
    # Obtener ajustes manuales
    manual_adjustments = session.query(OccupancyHistory).filter(
        OccupancyHistory.parking_id == parking_id,
        OccupancyHistory.source == 'manual',
        OccupancyHistory.timestamp >= date_limit,
        OccupancyHistory.previous_occupancy.isnot(None)
    ).order_by(OccupancyHistory.timestamp.asc()).all()
    
    if len(manual_adjustments) < 3:
        return {
            'parking_id': parking_id,
            'parking_name': parking.name,
            'status': 'insufficient_data',
            'sample_count': len(manual_adjustments)
        }
    
    logger.info(f"Parking {parking.name}: Analizando {len(manual_adjustments)} ajustes manuales")
    
    # Procesar cada ajuste
    calculations = []
    prev_adjustment = None
    
    for adj in manual_adjustments:
        if prev_adjustment is None:
            prev_adjustment = adj
            continue
        
        # Datos básicos
        occupancy_before = adj.previous_occupancy
        occupancy_after = adj.occupancy
        correction = occupancy_after - occupancy_before
        
        # Validar datos
        if occupancy_before is None or occupancy_after is None:
            prev_adjustment = adj
            continue
        
        # Hora desde última corrección
        adj_time = make_naive(adj.timestamp)
        prev_time = make_naive(prev_adjustment.timestamp)
        hours_since = (adj_time - prev_time).total_seconds() / 3600
        
        if hours_since < 1:  # Ignorar ajustes muy cercanos
            prev_adjustment = adj
            continue
        
        # Contar transacciones entre ajustes
        transactions = count_transactions_between(session, parking_id, prev_time, adj_time)
        
        # Calcular ratio (si occupancy_before > 0)
        correction_ratio = None
        if occupancy_before > 10:
            correction_ratio = occupancy_after / occupancy_before
        
        # Calcular error por transacción
        error_per_trans = None
        if transactions > 0:
            error_per_trans = abs(correction) / transactions
        
        # Crear registro de cálculo
        calc_data = {
            'parking_id': parking_id,
            'adjustment_timestamp': adj.timestamp,
            'hours_since_last_correction': hours_since,
            'time_of_day': adj_time.hour,
            'day_of_week': adj_time.weekday(),
            'occupancy_before_adjustment': occupancy_before,
            'occupancy_after_adjustment': occupancy_after,
            'correction_applied': correction,
            'drift_per_hour': correction / hours_since if hours_since > 0 else 0,
            'drift_total': correction,
            'parking_capacity': parking.max_capacity,
            'occupancy_percentage_before': (occupancy_before / parking.max_capacity * 100) if parking.max_capacity else 0,
            'occupancy_percentage_after': (occupancy_after / parking.max_capacity * 100) if parking.max_capacity else 0,
            'trigger_type': 'bootstrap_v2',
            'transactions_count': transactions,
            'error_per_transaction': error_per_trans,
            'correction_ratio': correction_ratio,
            'expected_occupancy': occupancy_after
        }
        
        calculations.append(calc_data)
        prev_adjustment = adj
    
    if not calculations:
        return {
            'parking_id': parking_id,
            'parking_name': parking.name,
            'status': 'no_valid_calculations',
            'sample_count': 0
        }
    
    # Guardar cálculos en BD (eliminar anteriores de bootstrap)
    session.query(CorrectionCalculation).filter(
        CorrectionCalculation.parking_id == parking_id,
        CorrectionCalculation.trigger_type.in_(['bootstrap', 'bootstrap_v2'])
    ).delete(synchronize_session='fetch')
    
    for calc_data in calculations:
        calc = CorrectionCalculation(**calc_data)
        session.add(calc)
    
    session.commit()
    logger.info(f"  → {len(calculations)} cálculos guardados")
    
    # Calcular métricas agregadas por día de semana
    metrics_by_weekday = {}
    for wd in range(7):
        wd_calcs = [c for c in calculations if c['day_of_week'] == wd]
        
        if wd_calcs:
            # Ratio de corrección
            ratios = [c['correction_ratio'] for c in wd_calcs if c['correction_ratio'] is not None and 0.1 <= c['correction_ratio'] <= 2.0]
            avg_ratio = mean(ratios) if ratios else 1.0
            
            # Ocupación esperada
            expected_occs = [c['expected_occupancy'] for c in wd_calcs if c['expected_occupancy'] is not None]
            avg_expected = mean(expected_occs) if expected_occs else 0
            
            # Drift (para compatibilidad)
            drifts = [c['drift_per_hour'] for c in wd_calcs]
            avg_drift = mean(drifts)
            
            # Error por transacción
            errors = [c['error_per_transaction'] for c in wd_calcs if c['error_per_transaction'] is not None]
            avg_error = mean(errors) if errors else 0
            
            # Transacciones promedio
            trans = [c['transactions_count'] for c in wd_calcs if c['transactions_count']]
            avg_trans = mean(trans) if trans else 0
            
            metrics_by_weekday[str(wd)] = {
                'samples': len(wd_calcs),
                'avg_ratio': round(avg_ratio, 3),
                'avg_expected_occupancy': round(avg_expected, 1),
                'avg_drift': round(avg_drift, 3),
                'avg_error_per_transaction': round(avg_error, 4),
                'avg_transactions': round(avg_trans, 1)
            }
        else:
            metrics_by_weekday[str(wd)] = {
                'samples': 0,
                'avg_ratio': 1.0,
                'avg_expected_occupancy': 0,
                'avg_drift': 0,
                'avg_error_per_transaction': 0,
                'avg_transactions': 0
            }
    
    # Calcular métricas globales
    all_ratios = [c['correction_ratio'] for c in calculations if c['correction_ratio'] is not None and 0.1 <= c['correction_ratio'] <= 2.0]
    all_errors = [c['error_per_transaction'] for c in calculations if c['error_per_transaction'] is not None]
    all_trans = [c['transactions_count'] for c in calculations if c['transactions_count']]
    all_drifts = [c['drift_per_hour'] for c in calculations]
    all_expected = [c['expected_occupancy'] for c in calculations if c['expected_occupancy'] is not None]
    
    global_metrics = {
        'avg_ratio': mean(all_ratios) if all_ratios else 1.0,
        'avg_error_per_transaction': mean(all_errors) if all_errors else 0,
        'avg_transactions_per_day': mean(all_trans) if all_trans else 0,
        'avg_drift': mean(all_drifts) if all_drifts else 0,
        'avg_expected_occupancy': mean(all_expected) if all_expected else 0,
        'sample_count': len(calculations)
    }
    
    # Actualizar configuración del parking
    config = session.query(ParkingCorrectionConfig).filter_by(parking_id=parking_id).first()
    if not config:
        config = ParkingCorrectionConfig(parking_id=parking_id)
        session.add(config)
    
    # Actualizar parámetros clásicos (para compatibilidad)
    config.avg_hourly_drift = global_metrics['avg_drift']
    config.avg_daily_drift = global_metrics['avg_drift'] * 24
    config.sample_count = global_metrics['sample_count']
    config.confidence_level = min(global_metrics['sample_count'] / 20, 1.0)
    
    # Actualizar parámetros por día
    config.drift_by_weekday = {k: v['avg_drift'] for k, v in metrics_by_weekday.items()}
    config.samples_by_weekday = {k: v['samples'] for k, v in metrics_by_weekday.items()}
    config.avg_occupancy_by_weekday = {k: v['avg_expected_occupancy'] for k, v in metrics_by_weekday.items()}
    
    # Nuevos parámetros v4.5.1
    config.avg_correction_ratio_by_weekday = {k: v['avg_ratio'] for k, v in metrics_by_weekday.items()}
    config.expected_occupancy_by_weekday = {k: v['avg_expected_occupancy'] for k, v in metrics_by_weekday.items()}
    config.avg_error_per_transaction = global_metrics['avg_error_per_transaction']
    config.avg_transactions_per_day = global_metrics['avg_transactions_per_day']
    # Transacciones promedio por día de semana (para calcular factor proporcional)
    config.avg_transactions_by_weekday = {k: v['avg_transactions'] for k, v in metrics_by_weekday.items()}
    
    config.last_calculation_at = datetime.now()
    
    session.commit()
    
    return {
        'parking_id': parking_id,
        'parking_name': parking.name,
        'status': 'success',
        'sample_count': global_metrics['sample_count'],
        'global_metrics': global_metrics,
        'metrics_by_weekday': metrics_by_weekday
    }


def run_bootstrap(days: int = 300):
    """
    Ejecutar bootstrap para todos los parkings.
    
    Args:
        days: Días hacia atrás para analizar
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los parkings
        parkings = session.query(Parking).all()
        
        logger.info("=" * 60)
        logger.info("BOOTSTRAP DE CORRECCIÓN AUTOMÁTICA v4.5.1")
        logger.info(f"Parkings a procesar: {len(parkings)}")
        logger.info(f"Período de análisis: últimos {days} días")
        logger.info("=" * 60)
        
        results = []
        success_count = 0
        
        for parking in parkings:
            logger.info(f"\n--- Procesando: {parking.name} (ID: {parking.id}) ---")
            
            result = process_parking_history(session, parking.id, days)
            results.append(result)
            
            if result.get('status') == 'success':
                success_count += 1
                metrics = result['global_metrics']
                logger.info(f"  → Ratio corrección promedio: {metrics['avg_ratio']:.3f}")
                logger.info(f"  → Error por transacción: {metrics['avg_error_per_transaction']:.4f}")
                logger.info(f"  → Transacciones promedio/día: {metrics['avg_transactions_per_day']:.1f}")
                logger.info(f"  → Muestras: {metrics['sample_count']}")
                
                # Mostrar por día de semana
                logger.info("  → Por día de semana:")
                for wd in range(7):
                    wd_data = result['metrics_by_weekday'].get(str(wd), {})
                    if wd_data.get('samples', 0) > 0:
                        logger.info(f"      {WEEKDAY_NAMES[wd]}: ratio={wd_data['avg_ratio']:.2f}, "
                                  f"occ_esp={wd_data['avg_expected_occupancy']:.0f}, "
                                  f"trans={wd_data['avg_transactions']:.0f}, "
                                  f"muestras={wd_data['samples']}")
            else:
                logger.info(f"  → {result.get('status', 'error')} ({result.get('sample_count', 0)} muestras)")
        
        # Resumen final
        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN DEL BOOTSTRAP v4.5.1")
        logger.info("=" * 60)
        logger.info(f"Total parkings procesados: {len(parkings)}")
        logger.info(f"  ✓ Con datos suficientes: {success_count}")
        logger.info(f"  ✗ Datos insuficientes: {len(parkings) - success_count}")
        
        # Mostrar parkings ordenados por confianza
        successful = [r for r in results if r.get('status') == 'success']
        successful.sort(key=lambda x: x['sample_count'], reverse=True)
        
        if successful:
            logger.info("\nParkings con corrección configurada:")
            for r in successful[:10]:
                metrics = r['global_metrics']
                logger.info(f"  • {r['parking_name']}: ratio={metrics['avg_ratio']:.2f}, "
                          f"error/trans={metrics['avg_error_per_transaction']:.3f}, "
                          f"{metrics['sample_count']} muestras")
        
        logger.info("\n✓ Bootstrap v4.5.1 completado")
        
    except Exception as e:
        logger.error(f"Error en bootstrap: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Bootstrap de corrección automática v4.5.1'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=300,
        help='Días hacia atrás para analizar (default: 300)'
    )
    
    args = parser.parse_args()
    run_bootstrap(days=args.days)


if __name__ == '__main__':
    main()
