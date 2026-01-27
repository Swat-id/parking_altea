"""
Servicio de Corrección Automática de Ocupación v4.5.1

NUEVO ALGORITMO que considera:
1. Ocupación actual vs ocupación esperada histórica
2. Número de transacciones (entradas + salidas)
3. Ratio de corrección en lugar de corrección absoluta
4. Día de la semana y hora

Autor: Parking Altea Team
Fecha: 2026-01-27
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from models import (
    Parking, OccupancyHistory, CameraLog,
    ParkingCorrectionConfig, CorrectionCalculation, AutoCorrectionHistory
)

logger = logging.getLogger(__name__)

# Constantes de configuración
WEEKDAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

# Límites de seguridad
MIN_CONFIDENCE_TO_APPLY = 0.3       # 30% mínimo de confianza
MIN_SAMPLES_FOR_RATIO = 5           # Mínimo 5 muestras para usar ratio
MAX_OCCUPANCY_PERCENT = 1.1         # Máximo 110% de ocupación
OCCUPANCY_SIMILARITY_THRESHOLD = 0.25  # ±25% para considerar ocupación similar
TRANSACTION_SIMILARITY_THRESHOLD = 0.35  # ±35% para considerar transacciones similares


def make_naive(dt: datetime) -> datetime:
    """Convertir datetime a naive (sin timezone)"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def now_naive() -> datetime:
    """Obtener datetime actual sin timezone"""
    return datetime.now()


def count_transactions_since(session: Session, parking_id: int, since: datetime) -> int:
    """
    Contar transacciones (entradas + salidas) desde una fecha.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        since: Fecha desde la cual contar
    
    Returns:
        Total de entradas + salidas
    """
    since_naive = make_naive(since)
    
    # Sumar deltas de camera_logs
    result = session.query(
        func.coalesce(func.sum(CameraLog.delta_in), 0).label('total_in'),
        func.coalesce(func.sum(CameraLog.delta_out), 0).label('total_out')
    ).filter(
        CameraLog.parking_id == parking_id,
        CameraLog.processed_at >= since_naive,
        CameraLog.status.like('%processed%')
    ).first()
    
    if result:
        return abs(result.total_in or 0) + abs(result.total_out or 0)
    return 0


def get_historical_corrections(
    session: Session, 
    parking_id: int, 
    weekday: int,
    current_occupancy: int,
    transactions_count: int,
    days_back: int = 300
) -> List[CorrectionCalculation]:
    """
    Obtener correcciones históricas similares al contexto actual.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        weekday: Día de la semana (0-6)
        current_occupancy: Ocupación actual
        transactions_count: Número de transacciones desde último ajuste
        days_back: Días hacia atrás para buscar
    
    Returns:
        Lista de correcciones históricas similares
    """
    date_limit = now_naive() - timedelta(days=days_back)
    
    # Rango de ocupación similar (±25%)
    occ_min = int(current_occupancy * (1 - OCCUPANCY_SIMILARITY_THRESHOLD))
    occ_max = int(current_occupancy * (1 + OCCUPANCY_SIMILARITY_THRESHOLD))
    
    # Query base: mismo día de semana
    query = session.query(CorrectionCalculation).filter(
        CorrectionCalculation.parking_id == parking_id,
        CorrectionCalculation.day_of_week == weekday,
        CorrectionCalculation.adjustment_timestamp >= date_limit,
        CorrectionCalculation.occupancy_before_adjustment.isnot(None),
        CorrectionCalculation.occupancy_after_adjustment.isnot(None)
    )
    
    # Si tenemos ocupación, filtrar por rango similar
    if current_occupancy > 0:
        query = query.filter(
            CorrectionCalculation.occupancy_before_adjustment.between(occ_min, occ_max)
        )
    
    corrections = query.order_by(CorrectionCalculation.adjustment_timestamp.desc()).all()
    
    # Si tenemos transacciones, filtrar adicionalmente
    if transactions_count > 0 and corrections:
        trans_min = int(transactions_count * (1 - TRANSACTION_SIMILARITY_THRESHOLD))
        trans_max = int(transactions_count * (1 + TRANSACTION_SIMILARITY_THRESHOLD))
        
        filtered = [c for c in corrections 
                   if c.transactions_count and trans_min <= c.transactions_count <= trans_max]
        
        # Si hay suficientes similares, usarlos; si no, usar todos
        if len(filtered) >= MIN_SAMPLES_FOR_RATIO:
            return filtered
    
    return corrections


def calculate_correction_ratio(corrections: List[CorrectionCalculation]) -> Tuple[float, float, int]:
    """
    Calcular el ratio de corrección promedio.
    
    Ratio = occupancy_after / occupancy_before
    Ejemplo: Si antes era 350 y después 150, ratio = 150/350 = 0.43
    
    Returns:
        Tuple[ratio_promedio, desviación_estándar, num_muestras]
    """
    ratios = []
    
    for c in corrections:
        if c.occupancy_before_adjustment and c.occupancy_before_adjustment > 10:
            ratio = c.occupancy_after_adjustment / c.occupancy_before_adjustment
            # Filtrar ratios extremos (0.1 - 2.0)
            if 0.1 <= ratio <= 2.0:
                ratios.append(ratio)
    
    if not ratios:
        return 1.0, 0.0, 0
    
    avg_ratio = mean(ratios)
    std_ratio = stdev(ratios) if len(ratios) > 1 else 0.0
    
    return avg_ratio, std_ratio, len(ratios)


def calculate_expected_occupancy(
    corrections: List[CorrectionCalculation]
) -> Tuple[float, float, int]:
    """
    Calcular la ocupación esperada después de corrección.
    
    Usa el promedio de occupancy_after_adjustment histórico.
    
    Returns:
        Tuple[ocupación_esperada, desviación_estándar, num_muestras]
    """
    occupancies = [c.occupancy_after_adjustment for c in corrections 
                   if c.occupancy_after_adjustment is not None and c.occupancy_after_adjustment >= 0]
    
    if not occupancies:
        return 0, 0, 0
    
    avg_occ = mean(occupancies)
    std_occ = stdev(occupancies) if len(occupancies) > 1 else 0.0
    
    return avg_occ, std_occ, len(occupancies)


def calculate_error_per_transaction(corrections: List[CorrectionCalculation]) -> float:
    """
    Calcular el error promedio por transacción.
    
    error_per_trans = abs(correction) / transactions
    
    Returns:
        Error promedio por transacción
    """
    errors = []
    
    for c in corrections:
        if c.transactions_count and c.transactions_count > 0 and c.correction_applied:
            error = abs(c.correction_applied) / c.transactions_count
            errors.append(error)
    
    return mean(errors) if errors else 0.0


def calculate_suggested_correction_v2(
    session: Session,
    parking_id: int,
    target_weekday: int = None
) -> Dict:
    """
    Calcular corrección sugerida usando el nuevo algoritmo v2.
    
    El algoritmo considera:
    1. Ocupación actual vs ocupación esperada histórica para el día
    2. Ratio de corrección histórico (no corrección absoluta)
    3. Número de transacciones y error por transacción
    4. Día de la semana
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        target_weekday: Día de la semana objetivo (0-6, default: hoy)
    
    Returns:
        Dict con sugerencia de corrección y métricas
    """
    if target_weekday is None:
        target_weekday = now_naive().weekday()
    
    # Obtener parking y configuración
    parking = session.query(Parking).get(parking_id)
    if not parking:
        return {'error': 'Parking no encontrado'}
    
    config = session.query(ParkingCorrectionConfig).filter_by(parking_id=parking_id).first()
    if not config:
        return {'error': 'Sin configuración de corrección'}
    
    current_occupancy = parking.current_occupancy
    max_capacity = parking.max_capacity
    
    # Obtener última corrección para calcular transacciones
    last_correction = session.query(OccupancyHistory).filter(
        OccupancyHistory.parking_id == parking_id,
        OccupancyHistory.source.in_(['manual', 'auto_scheduled'])
    ).order_by(OccupancyHistory.timestamp.desc()).first()
    
    if last_correction:
        last_correction_time = make_naive(last_correction.timestamp)
        hours_since_last = (now_naive() - last_correction_time).total_seconds() / 3600
    else:
        last_correction_time = now_naive() - timedelta(days=1)
        hours_since_last = 24.0
    
    # Contar transacciones desde última corrección
    transactions_count = count_transactions_since(session, parking_id, last_correction_time)
    
    # Obtener correcciones históricas similares
    historical = get_historical_corrections(
        session, parking_id, target_weekday,
        current_occupancy, transactions_count
    )
    
    # Calcular métricas
    correction_ratio, ratio_std, ratio_samples = calculate_correction_ratio(historical)
    expected_occ, expected_std, expected_samples = calculate_expected_occupancy(historical)
    error_per_trans = calculate_error_per_transaction(historical)
    
    # Determinar estrategia de corrección
    if ratio_samples >= MIN_SAMPLES_FOR_RATIO:
        # ESTRATEGIA 1: Usar ratio de corrección
        # Si ratio = 0.5, significa que históricamente se corrige al 50% de lo reportado
        
        if current_occupancy > 0:
            # Calcular ocupación esperada basada en ratio
            estimated_real = int(current_occupancy * correction_ratio)
            
            # Comparar con ocupación esperada histórica
            if expected_samples >= MIN_SAMPLES_FOR_RATIO:
                # Promediar entre ratio y valor esperado
                weight_ratio = 0.6
                weight_expected = 0.4
                estimated_real = int(estimated_real * weight_ratio + expected_occ * weight_expected)
            
            suggested_correction = estimated_real - current_occupancy
            method = 'ratio_based'
        else:
            # Si ocupación actual es 0, usar ocupación esperada
            suggested_correction = int(expected_occ) if expected_samples >= MIN_SAMPLES_FOR_RATIO else 0
            method = 'expected_occupancy'
        
    elif expected_samples >= MIN_SAMPLES_FOR_RATIO:
        # ESTRATEGIA 2: Usar ocupación esperada directamente
        suggested_correction = int(expected_occ - current_occupancy)
        method = 'expected_occupancy'
        
    else:
        # ESTRATEGIA 3: Usar drift por hora (fallback al método anterior)
        drift_by_weekday = config.drift_by_weekday or {}
        drift = drift_by_weekday.get(str(target_weekday), config.avg_hourly_drift or 0)
        suggested_correction = int(drift * hours_since_last)
        method = 'drift_fallback'
    
    # Ajustar por transacciones si tenemos datos
    if error_per_trans > 0 and transactions_count > 0:
        expected_error = error_per_trans * transactions_count
        # Si la corrección sugerida es menor que el error esperado, ajustar
        if abs(suggested_correction) < expected_error * 0.5:
            # Aumentar corrección basada en transacciones
            sign = 1 if suggested_correction >= 0 else -1
            suggested_correction = int(sign * max(abs(suggested_correction), expected_error * 0.7))
    
    # Calcular confianza
    confidence_factors = []
    if ratio_samples >= MIN_SAMPLES_FOR_RATIO:
        confidence_factors.append(min(ratio_samples / 20, 1.0))
    if expected_samples >= MIN_SAMPLES_FOR_RATIO:
        confidence_factors.append(min(expected_samples / 20, 1.0))
    if config.sample_count:
        confidence_factors.append(min(config.sample_count / 50, 1.0))
    
    overall_confidence = mean(confidence_factors) if confidence_factors else 0.0
    
    return {
        'parking_id': parking_id,
        'parking_name': parking.name,
        'current_occupancy': current_occupancy,
        'max_capacity': max_capacity,
        'suggested_correction': suggested_correction,
        'estimated_real_occupancy': current_occupancy + suggested_correction,
        'method': method,
        'weekday': target_weekday,
        'weekday_name': WEEKDAY_NAMES[target_weekday],
        'hours_since_last': round(hours_since_last, 2),
        'transactions_count': transactions_count,
        'metrics': {
            'correction_ratio': round(correction_ratio, 3),
            'ratio_std': round(ratio_std, 3),
            'ratio_samples': ratio_samples,
            'expected_occupancy': round(expected_occ, 1),
            'expected_std': round(expected_std, 1),
            'expected_samples': expected_samples,
            'error_per_transaction': round(error_per_trans, 4)
        },
        'confidence': {
            'overall': round(overall_confidence, 2),
            'has_enough_data': ratio_samples >= MIN_SAMPLES_FOR_RATIO or expected_samples >= MIN_SAMPLES_FOR_RATIO
        }
    }


def apply_auto_correction_v2(session: Session, parking_id: int) -> Optional[Dict]:
    """
    Aplicar corrección automática usando el algoritmo v2.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
    
    Returns:
        Dict con resultado de la corrección o None si no se aplicó
    """
    # Obtener configuración
    config = session.query(ParkingCorrectionConfig).filter_by(parking_id=parking_id).first()
    
    if not config or not config.auto_correction_enabled:
        logger.info(f"Parking {parking_id}: Corrección automática deshabilitada")
        return None
    
    # Calcular corrección sugerida
    calc = calculate_suggested_correction_v2(
        session, 
        parking_id, 
        target_weekday=now_naive().weekday()
    )
    
    if calc.get('error'):
        logger.warning(f"Parking {parking_id}: {calc['error']}")
        return None
    
    # Verificar confianza mínima
    if calc['confidence']['overall'] < MIN_CONFIDENCE_TO_APPLY:
        logger.info(f"Parking {parking_id}: Confianza insuficiente ({calc['confidence']['overall']*100:.0f}%)")
        return {'skipped': True, 'reason': 'low_confidence', 'confidence': calc['confidence']['overall']}
    
    # Verificar si hay corrección significativa
    if abs(calc['suggested_correction']) < 2:
        logger.info(f"Parking {parking_id}: Corrección muy pequeña ({calc['suggested_correction']})")
        return {'skipped': True, 'reason': 'small_correction', 'suggested': calc['suggested_correction']}
    
    # Obtener parking
    parking = session.query(Parking).get(parking_id)
    if not parking:
        return None
    
    previous_occupancy = parking.current_occupancy
    original_suggestion = calc['suggested_correction']
    
    # Calcular nueva ocupación
    new_occupancy = previous_occupancy + original_suggestion
    
    # Aplicar límites
    adjustment_type = 'auto_scheduled'
    was_limited = False
    
    if new_occupancy < 0:
        new_occupancy = 0
        adjustment_type = 'limit_floor'
        was_limited = True
        logger.warning(f"Parking {parking_id}: Límite inferior aplicado (ocupación negativa)")
    elif new_occupancy > parking.max_capacity * MAX_OCCUPANCY_PERCENT:
        new_occupancy = int(parking.max_capacity * MAX_OCCUPANCY_PERCENT)
        adjustment_type = 'limit_ceiling'
        was_limited = True
        logger.warning(f"Parking {parking_id}: Límite superior aplicado (>{MAX_OCCUPANCY_PERCENT*100:.0f}%)")
    
    correction_amount = new_occupancy - previous_occupancy
    
    # Aplicar corrección
    parking.current_occupancy = new_occupancy
    
    # Recalcular estado
    free = parking.max_capacity - new_occupancy
    if free < 0:
        parking.status = 'COMPLETO'
    elif free <= parking.threshold_full:
        parking.status = 'COMPLETO'
    elif free <= parking.threshold_dense:
        parking.status = 'DENSO'
    else:
        parking.status = 'LIBRE'
    
    # Registrar en occupancy_history
    history = OccupancyHistory(
        parking_id=parking_id,
        occupancy=new_occupancy,
        source='auto_scheduled',
        previous_occupancy=previous_occupancy,
        change_amount=correction_amount,
        adjustment_type=adjustment_type
    )
    session.add(history)
    
    # Registrar en auto_correction_history
    auto_history = AutoCorrectionHistory(
        parking_id=parking_id,
        occupancy_before=previous_occupancy,
        occupancy_after=new_occupancy,
        correction_amount=correction_amount,
        drift_used=calc['metrics']['correction_ratio'],  # Usamos ratio en lugar de drift
        hours_elapsed=calc['hours_since_last'],
        confidence_at_time=calc['confidence']['overall'],
        day_of_week=calc['weekday'],
        adjustment_type=adjustment_type,
        was_limited=was_limited,
        original_suggestion=original_suggestion
    )
    session.add(auto_history)
    
    # Actualizar configuración
    config.last_auto_correction_at = now_naive()
    config.last_auto_correction_amount = correction_amount
    
    session.commit()
    
    logger.info(
        f"Corrección automática v2 aplicada - Parking: {parking.name}, "
        f"Anterior: {previous_occupancy}, Nuevo: {new_occupancy}, "
        f"Corrección: {correction_amount:+d}, Método: {calc['method']}"
    )
    
    return {
        'applied': True,
        'parking_id': parking_id,
        'parking_name': parking.name,
        'previous_occupancy': previous_occupancy,
        'new_occupancy': new_occupancy,
        'correction_amount': correction_amount,
        'original_suggestion': original_suggestion,
        'adjustment_type': adjustment_type,
        'was_limited': was_limited,
        'method': calc['method'],
        'confidence': calc['confidence']['overall'],
        'metrics': calc['metrics'],
        'new_status': parking.status
    }
