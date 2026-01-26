"""
Servicio de Corrección Automática de Ocupación v4.5.0

Este servicio gestiona el cálculo y aplicación de correcciones automáticas
basadas en patrones históricos de ajustes manuales.

Autor: Parking Altea Team
Fecha: 2026-01-26
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models import (
    Parking, OccupancyHistory,
    ParkingCorrectionConfig, CorrectionCalculation, AutoCorrectionHistory
)

logger = logging.getLogger(__name__)

# Constantes de configuración
WEEKDAY_GROUPS = {
    'laborable': [0, 1, 2, 3],      # Lunes a Jueves
    'pre_weekend': [4],              # Viernes
    'weekend': [5, 6]                # Sábado, Domingo
}

# Grupos de fallback: si no hay datos de un grupo, usar estos
WEEKDAY_GROUP_FALLBACK = {
    'weekend': ['pre_weekend', 'laborable'],  # Fin de semana → Viernes → Laborable
    'pre_weekend': ['laborable', 'weekend'],  # Viernes → Laborable → Fin de semana
    'laborable': ['pre_weekend', 'weekend']   # Laborable → Viernes → Fin de semana
}

WEEKDAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
WEEKDAY_NAMES_SHORT = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

# Límites de seguridad
MIN_CONFIDENCE_TO_APPLY = 0.3       # 30% mínimo de confianza
MIN_CORRECTION_THRESHOLD = 2        # No aplicar correcciones menores a 2
MAX_CORRECTION_PERCENT = 0.5        # Máximo 50% de la capacidad
MAX_OCCUPANCY_PERCENT = 1.1         # Máximo 110% de ocupación

# Umbrales para clasificación de drift
DRIFT_THRESHOLD_HIGH = 0.5          # Alta desviación
DRIFT_THRESHOLD_LOW = 0.1           # Baja desviación (estable)


def get_day_group(weekday: int) -> str:
    """Obtener grupo del día de la semana"""
    for group, days in WEEKDAY_GROUPS.items():
        if weekday in days:
            return group
    return 'laborable'


def get_effective_drift_for_day(
    weekday: int,
    drift_by_weekday: Dict,
    samples_by_weekday: Dict,
    avg_hourly_drift: float,
    min_samples: int = 3
) -> Tuple[float, str, float]:
    """
    Obtener el drift efectivo para un día específico.
    
    Lógica de fallback mejorada:
    1. Si hay ≥3 muestras del día específico → usar ese drift
    2. Si no, buscar en días del mismo grupo
    3. Si no, buscar en grupos de fallback
    4. Si no, usar media global
    
    Returns:
        Tuple[float, str, float]: (drift_efectivo, fuente, confianza_dia)
    """
    day_drift = drift_by_weekday.get(str(weekday), 0)
    day_samples = samples_by_weekday.get(str(weekday), 0)
    
    # Opción 1: Suficientes muestras del día específico
    if day_samples >= min_samples:
        day_confidence = min(day_samples / 5, 1.0)
        return day_drift, 'day_specific', day_confidence
    
    # Opción 2: Buscar en el mismo grupo
    target_group = get_day_group(weekday)
    group_drifts = []
    group_samples = 0
    
    for day in WEEKDAY_GROUPS.get(target_group, []):
        d = drift_by_weekday.get(str(day), 0)
        s = samples_by_weekday.get(str(day), 0)
        if s > 0:
            group_drifts.extend([d] * s)
            group_samples += s
    
    if group_samples >= min_samples:
        effective_drift = sum(group_drifts) / len(group_drifts) if group_drifts else avg_hourly_drift
        group_confidence = min(group_samples / 10, 0.8)  # Máximo 80% confianza para grupo
        return effective_drift, f'group_{target_group}', group_confidence
    
    # Opción 3: Buscar en grupos de fallback
    fallback_groups = WEEKDAY_GROUP_FALLBACK.get(target_group, [])
    for fallback_group in fallback_groups:
        fallback_drifts = []
        fallback_samples = 0
        
        for day in WEEKDAY_GROUPS.get(fallback_group, []):
            d = drift_by_weekday.get(str(day), 0)
            s = samples_by_weekday.get(str(day), 0)
            if s > 0:
                fallback_drifts.extend([d] * s)
                fallback_samples += s
        
        if fallback_samples >= min_samples:
            effective_drift = sum(fallback_drifts) / len(fallback_drifts) if fallback_drifts else avg_hourly_drift
            fallback_confidence = min(fallback_samples / 15, 0.6)  # Máximo 60% para fallback
            return effective_drift, f'fallback_{fallback_group}', fallback_confidence
    
    # Opción 4: Media global
    return avg_hourly_drift, 'global', 0.4 if avg_hourly_drift != 0 else 0


def calculate_suggested_correction(
    session: Session,
    parking_id: int,
    target_hour: int = 6,
    target_weekday: Optional[int] = None
) -> Dict:
    """
    Calcular la corrección sugerida para un parking.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        target_hour: Hora objetivo para la corrección (default: 6)
        target_weekday: Día de la semana objetivo (0-6, None para hoy)
    
    Returns:
        Dict con corrección sugerida y métricas
    """
    if target_weekday is None:
        target_weekday = datetime.now().weekday()
    
    # Obtener parking
    parking = session.query(Parking).get(parking_id)
    if not parking:
        return {'error': 'Parking no encontrado', 'suggested_correction': 0}
    
    # Obtener configuración
    config = session.query(ParkingCorrectionConfig).filter_by(parking_id=parking_id).first()
    
    if not config:
        return {
            'error': 'Sin configuración de corrección',
            'suggested_correction': 0,
            'confidence': 0
        }
    
    # Obtener última corrección (manual o automática)
    last_correction = session.query(OccupancyHistory).filter(
        OccupancyHistory.parking_id == parking_id,
        OccupancyHistory.source.in_(['manual', 'auto_scheduled'])
    ).order_by(OccupancyHistory.timestamp.desc()).first()
    
    if not last_correction:
        # Si no hay correcciones previas, usar timestamp muy antiguo
        last_correction_time = datetime.now() - timedelta(days=1)
    else:
        last_correction_time = last_correction.timestamp
    
    # Calcular horas transcurridas
    hours_elapsed = (datetime.now() - last_correction_time).total_seconds() / 3600
    
    # Obtener drift por día de semana
    drift_by_weekday = config.drift_by_weekday or {}
    samples_by_weekday = config.samples_by_weekday or {}
    
    # Usar nueva función mejorada de cálculo de drift
    effective_drift, drift_source, day_confidence = get_effective_drift_for_day(
        target_weekday,
        drift_by_weekday,
        samples_by_weekday,
        config.avg_hourly_drift or 0
    )
    
    # Datos del día específico para referencia
    day_drift = drift_by_weekday.get(str(target_weekday), 0)
    day_samples = samples_by_weekday.get(str(target_weekday), 0)
    
    # Calcular corrección sugerida
    raw_correction = effective_drift * hours_elapsed
    suggested_correction = round(raw_correction)
    
    # Aplicar límites de seguridad
    max_correction = int(parking.max_capacity * MAX_CORRECTION_PERCENT)
    original_suggestion = suggested_correction
    was_limited = False
    limit_type = None
    
    if abs(suggested_correction) > max_correction:
        suggested_correction = max_correction if suggested_correction > 0 else -max_correction
        was_limited = True
        limit_type = 'max_correction'
    
    # Calcular confianzas combinadas
    general_confidence = config.confidence_level or 0
    overall_confidence = (general_confidence * 0.5) + (day_confidence * 0.5)
    
    # Clasificar el tipo de drift
    drift_classification = 'estable'
    if abs(effective_drift) >= DRIFT_THRESHOLD_HIGH:
        drift_classification = 'alto_positivo' if effective_drift > 0 else 'alto_negativo'
    elif abs(effective_drift) >= DRIFT_THRESHOLD_LOW:
        drift_classification = 'moderado_positivo' if effective_drift > 0 else 'moderado_negativo'
    
    # Interpretar la fuente del drift
    drift_source_explanation = {
        'day_specific': f'Basado en datos específicos del {WEEKDAY_NAMES[target_weekday]} ({day_samples} muestras)',
        'group_laborable': 'Basado en datos de días laborables (L-J)',
        'group_pre_weekend': 'Basado en datos del viernes',
        'group_weekend': 'Basado en datos de fin de semana (S-D)',
        'fallback_laborable': 'Fallback a datos laborables (sin datos del grupo)',
        'fallback_pre_weekend': 'Fallback a datos del viernes (sin datos del grupo)',
        'fallback_weekend': 'Fallback a datos de fin de semana (sin datos del grupo)',
        'global': 'Media global (datos insuficientes por día)'
    }.get(drift_source, f'Fuente: {drift_source}')
    
    return {
        'parking_id': parking_id,
        'parking_name': parking.name,
        'suggested_correction': suggested_correction,
        'original_suggestion': original_suggestion,
        'raw_correction': raw_correction,
        'was_limited': was_limited,
        'limit_type': limit_type,
        'effective_drift_per_hour': effective_drift,
        'drift_source': drift_source,
        'drift_source_explanation': drift_source_explanation,
        'drift_classification': drift_classification,
        'hours_since_last': hours_elapsed,
        'target_weekday': target_weekday,
        'target_weekday_name': WEEKDAY_NAMES[target_weekday],
        'current_occupancy': parking.current_occupancy,
        'max_capacity': parking.max_capacity,
        'occupancy_percentage': round(parking.current_occupancy / parking.max_capacity * 100, 1) if parking.max_capacity > 0 else 0,
        'confidence': {
            'overall': round(overall_confidence, 2),
            'general': round(general_confidence, 2),
            'day_specific': round(day_confidence, 2)
        },
        'sample_count': {
            'total': config.sample_count or 0,
            'same_weekday': day_samples
        },
        'weekday_data': {
            'day_drift': round(day_drift, 3),
            'day_samples': day_samples,
            'all_days': {
                WEEKDAY_NAMES_SHORT[i]: {
                    'drift': round(drift_by_weekday.get(str(i), 0), 3),
                    'samples': samples_by_weekday.get(str(i), 0)
                } for i in range(7)
            }
        },
        'auto_correction_enabled': config.auto_correction_enabled,
        'correction_hour': config.correction_hour,
        'correction_minute': config.correction_minute or 0,
        'last_calculation_at': config.last_calculation_at.isoformat() if config.last_calculation_at else None,
        'last_auto_correction': {
            'at': config.last_auto_correction_at.isoformat() if config.last_auto_correction_at else None,
            'amount': config.last_auto_correction_amount or 0
        }
    }


def apply_auto_correction(session: Session, parking_id: int) -> Optional[Dict]:
    """
    Aplicar corrección automática a un parking.
    
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
    calc = calculate_suggested_correction(
        session, 
        parking_id, 
        target_hour=config.correction_hour,
        target_weekday=datetime.now().weekday()
    )
    
    if calc.get('error'):
        logger.warning(f"Parking {parking_id}: {calc['error']}")
        return None
    
    # Verificar confianza mínima
    if calc['confidence']['overall'] < MIN_CONFIDENCE_TO_APPLY:
        logger.info(f"Parking {parking_id}: Confianza insuficiente ({calc['confidence']['overall']*100:.0f}%)")
        return {'skipped': True, 'reason': 'low_confidence', 'confidence': calc['confidence']['overall']}
    
    # Verificar corrección mínima
    if abs(calc['suggested_correction']) < MIN_CORRECTION_THRESHOLD:
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
        drift_used=calc['effective_drift_per_hour'],
        hours_elapsed=calc['hours_since_last'],
        confidence_at_time=calc['confidence']['overall'],
        day_of_week=datetime.now().weekday(),
        adjustment_type=adjustment_type,
        was_limited=was_limited,
        original_suggestion=original_suggestion
    )
    session.add(auto_history)
    
    # Actualizar configuración
    config.last_auto_correction_at = datetime.now()
    config.last_auto_correction_amount = correction_amount
    
    session.commit()
    
    logger.info(
        f"Corrección automática aplicada - Parking: {parking.name}, "
        f"Anterior: {previous_occupancy}, Nuevo: {new_occupancy}, "
        f"Corrección: {correction_amount:+d}, Tipo: {adjustment_type}"
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
        'confidence': calc['confidence']['overall'],
        'new_status': parking.status
    }


def update_correction_metrics_after_manual(session: Session, parking_id: int, adjustment: OccupancyHistory):
    """
    Actualizar métricas de corrección después de un ajuste manual.
    
    Esta función se debe llamar cada vez que se hace un ajuste manual
    para mantener actualizados los parámetros del algoritmo.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        adjustment: Registro del ajuste manual
    """
    parking = session.query(Parking).get(parking_id)
    if not parking:
        return
    
    config = session.query(ParkingCorrectionConfig).filter_by(parking_id=parking_id).first()
    if not config:
        # Crear configuración si no existe
        config = ParkingCorrectionConfig(
            parking_id=parking_id,
            auto_correction_enabled=True
        )
        session.add(config)
    
    # Obtener última corrección anterior a esta
    last_correction = session.query(OccupancyHistory).filter(
        OccupancyHistory.parking_id == parking_id,
        OccupancyHistory.source.in_(['manual', 'auto_scheduled']),
        OccupancyHistory.timestamp < adjustment.timestamp,
        OccupancyHistory.id != adjustment.id
    ).order_by(OccupancyHistory.timestamp.desc()).first()
    
    if not last_correction:
        return
    
    # Calcular métricas
    hours_between = (adjustment.timestamp - last_correction.timestamp).total_seconds() / 3600
    
    if hours_between < 1 or hours_between > 168:  # Ignorar < 1h o > 7 días
        return
    
    prev_correct = last_correction.occupancy
    occupancy_before = adjustment.previous_occupancy or 0
    occupancy_after = adjustment.occupancy
    correction = adjustment.change_amount or (occupancy_after - occupancy_before)
    
    # Calcular drift
    drift_total = occupancy_before - prev_correct
    drift_per_hour = drift_total / hours_between if hours_between > 0 else 0
    
    weekday = adjustment.timestamp.weekday()
    hour = adjustment.timestamp.hour
    
    # Guardar cálculo
    calc_record = CorrectionCalculation(
        parking_id=parking_id,
        adjustment_timestamp=adjustment.timestamp,
        hours_since_last_correction=hours_between,
        time_of_day=hour,
        day_of_week=weekday,
        occupancy_before_adjustment=occupancy_before,
        occupancy_after_adjustment=occupancy_after,
        correction_applied=correction,
        drift_per_hour=drift_per_hour,
        drift_total=drift_total,
        parking_capacity=parking.max_capacity,
        occupancy_percentage_before=(occupancy_before / parking.max_capacity * 100) if parking.max_capacity > 0 else 0,
        occupancy_percentage_after=(occupancy_after / parking.max_capacity * 100) if parking.max_capacity > 0 else 0,
        trigger_type='manual'
    )
    session.add(calc_record)
    
    # Actualizar promedios en configuración
    # Recalcular con todos los datos recientes (últimos 90 días)
    date_limit = datetime.now() - timedelta(days=90)
    recent_calcs = session.query(CorrectionCalculation).filter(
        CorrectionCalculation.parking_id == parking_id,
        CorrectionCalculation.adjustment_timestamp >= date_limit
    ).all()
    
    if recent_calcs:
        # Promedio global
        all_drifts = [c.drift_per_hour for c in recent_calcs if c.drift_per_hour is not None]
        if all_drifts:
            config.avg_hourly_drift = sum(all_drifts) / len(all_drifts)
            config.avg_daily_drift = config.avg_hourly_drift * 24
        
        # Por día de semana
        drift_by_day = {}
        samples_by_day = {}
        occupancy_by_day = {}
        
        for day in range(7):
            day_calcs = [c for c in recent_calcs if c.day_of_week == day]
            if day_calcs:
                drifts = [c.drift_per_hour for c in day_calcs if c.drift_per_hour is not None]
                occupancies = [c.occupancy_after_adjustment for c in day_calcs if c.occupancy_after_adjustment is not None]
                
                drift_by_day[str(day)] = sum(drifts) / len(drifts) if drifts else config.avg_hourly_drift
                samples_by_day[str(day)] = len(day_calcs)
                occupancy_by_day[str(day)] = sum(occupancies) / len(occupancies) if occupancies else 0
            else:
                drift_by_day[str(day)] = config.avg_hourly_drift
                samples_by_day[str(day)] = 0
                occupancy_by_day[str(day)] = 0
        
        config.drift_by_weekday = drift_by_day
        config.samples_by_weekday = samples_by_day
        config.avg_occupancy_by_weekday = occupancy_by_day
        config.sample_count = len(recent_calcs)
        config.confidence_level = min(len(recent_calcs) / 20, 1.0)
        config.last_calculation_at = datetime.now()
        
        # Actualizar corrección sugerida
        config.suggested_correction = round(config.avg_hourly_drift * 24)
    
    # Validar última corrección automática si existe
    last_auto = session.query(AutoCorrectionHistory).filter(
        AutoCorrectionHistory.parking_id == parking_id,
        AutoCorrectionHistory.validated == False
    ).order_by(AutoCorrectionHistory.applied_at.desc()).first()
    
    if last_auto:
        # Calcular error de predicción
        # La corrección real necesaria es lo que el usuario tuvo que corregir
        # más lo que la auto-corrección ya había aplicado
        actual_needed = correction + (last_auto.correction_amount or 0)
        prediction_error = actual_needed - (last_auto.original_suggestion or 0)
        
        last_auto.validated = True
        last_auto.validation_timestamp = datetime.now()
        last_auto.actual_correction_needed = actual_needed
        last_auto.prediction_error = prediction_error
    
    session.commit()
    
    logger.info(
        f"Métricas actualizadas para parking {parking.name}: "
        f"drift/h={config.avg_hourly_drift:.3f}, samples={config.sample_count}"
    )


def get_correction_stats(session: Session, parking_id: int, days: int = 30) -> Dict:
    """
    Obtener estadísticas de corrección de un parking.
    
    Args:
        session: Sesión de BD
        parking_id: ID del parking
        days: Días hacia atrás
    
    Returns:
        Dict con estadísticas completas
    """
    parking = session.query(Parking).get(parking_id)
    if not parking:
        return {'error': 'Parking no encontrado'}
    
    config = session.query(ParkingCorrectionConfig).filter_by(parking_id=parking_id).first()
    
    date_limit = datetime.now() - timedelta(days=days)
    
    # Obtener cálculos (ajustes manuales procesados)
    calculations = session.query(CorrectionCalculation).filter(
        CorrectionCalculation.parking_id == parking_id,
        CorrectionCalculation.adjustment_timestamp >= date_limit
    ).order_by(CorrectionCalculation.adjustment_timestamp.desc()).all()
    
    # Obtener historial de auto-correcciones
    auto_corrections = session.query(AutoCorrectionHistory).filter(
        AutoCorrectionHistory.parking_id == parking_id,
        AutoCorrectionHistory.applied_at >= date_limit
    ).order_by(AutoCorrectionHistory.applied_at.desc()).all()
    
    # Obtener ajustes manuales del período
    manual_adjustments = session.query(OccupancyHistory).filter(
        OccupancyHistory.parking_id == parking_id,
        OccupancyHistory.source == 'manual',
        OccupancyHistory.timestamp >= date_limit
    ).order_by(OccupancyHistory.timestamp.desc()).all()
    
    # Estadísticas por día de semana
    weekday_stats = {}
    for day in range(7):
        day_calcs = [c for c in calculations if c.day_of_week == day]
        day_autos = [a for a in auto_corrections if a.day_of_week == day]
        
        if day_calcs:
            drifts = [c.drift_per_hour for c in day_calcs if c.drift_per_hour is not None]
            corrections = [c.correction_applied for c in day_calcs if c.correction_applied is not None]
            occupancies_before = [c.occupancy_before_adjustment for c in day_calcs if c.occupancy_before_adjustment is not None]
            occupancies_after = [c.occupancy_after_adjustment for c in day_calcs if c.occupancy_after_adjustment is not None]
            
            weekday_stats[str(day)] = {
                'name': WEEKDAY_NAMES[day],
                'short_name': WEEKDAY_NAMES_SHORT[day],
                'sample_count': len(day_calcs),
                'avg_drift_per_hour': round(sum(drifts) / len(drifts), 3) if drifts else 0,
                'avg_drift_per_day': round(sum(drifts) / len(drifts) * 24, 1) if drifts else 0,
                'avg_manual_correction': round(sum(corrections) / len(corrections), 1) if corrections else 0,
                'avg_occupancy_before': round(sum(occupancies_before) / len(occupancies_before), 1) if occupancies_before else 0,
                'avg_occupancy_after': round(sum(occupancies_after) / len(occupancies_after), 1) if occupancies_after else 0,
                'confidence': min(len(day_calcs) / 5, 1.0),
                'auto_corrections_count': len(day_autos),
                'avg_auto_correction': round(sum(a.correction_amount for a in day_autos) / len(day_autos), 1) if day_autos else 0
            }
        else:
            weekday_stats[str(day)] = {
                'name': WEEKDAY_NAMES[day],
                'short_name': WEEKDAY_NAMES_SHORT[day],
                'sample_count': 0,
                'avg_drift_per_hour': 0,
                'avg_drift_per_day': 0,
                'avg_manual_correction': 0,
                'avg_occupancy_before': 0,
                'avg_occupancy_after': 0,
                'confidence': 0,
                'auto_corrections_count': len(day_autos),
                'avg_auto_correction': round(sum(a.correction_amount for a in day_autos) / len(day_autos), 1) if day_autos else 0
            }
    
    # Estadísticas de ajustes manuales
    manual_stats = {
        'total_count': len(manual_adjustments),
        'total_corrections_sum': sum(a.change_amount or 0 for a in manual_adjustments),
        'positive_corrections': len([a for a in manual_adjustments if (a.change_amount or 0) > 0]),
        'negative_corrections': len([a for a in manual_adjustments if (a.change_amount or 0) < 0]),
        'avg_correction': round(sum(a.change_amount or 0 for a in manual_adjustments) / len(manual_adjustments), 1) if manual_adjustments else 0,
        'last_5': [{
            'timestamp': a.timestamp.isoformat() if a.timestamp else None,
            'previous': a.previous_occupancy,
            'new': a.occupancy,
            'change': a.change_amount
        } for a in manual_adjustments[:5]]
    }
    
    # Estadísticas de correcciones automáticas
    auto_stats = {
        'total_count': len(auto_corrections),
        'total_corrections_sum': sum(a.correction_amount or 0 for a in auto_corrections),
        'avg_correction': round(sum(a.correction_amount or 0 for a in auto_corrections) / len(auto_corrections), 1) if auto_corrections else 0,
        'limited_count': len([a for a in auto_corrections if a.was_limited]),
        'last_5': [{
            'timestamp': a.applied_at.isoformat() if a.applied_at else None,
            'before': a.occupancy_before,
            'after': a.occupancy_after,
            'correction': a.correction_amount,
            'drift_used': round(a.drift_used, 3) if a.drift_used else 0,
            'confidence': round(a.confidence_at_time, 2) if a.confidence_at_time else 0,
            'was_limited': a.was_limited,
            'validated': a.validated,
            'prediction_error': a.prediction_error
        } for a in auto_corrections[:5]]
    }
    
    # Precisión de auto-correcciones (validadas)
    validated_autos = [a for a in auto_corrections if a.validated]
    if validated_autos:
        prediction_errors = [abs(a.prediction_error) for a in validated_autos if a.prediction_error is not None]
        avg_error = sum(prediction_errors) / len(prediction_errors) if prediction_errors else 0
        accuracy = 1 - (avg_error / (parking.max_capacity or 100))
    else:
        avg_error = None
        accuracy = None
    
    # Calcular métricas de comparación manual vs automático
    comparison_metrics = calculate_comparison_metrics(
        manual_adjustments, auto_corrections, calculations
    )
    
    return {
        'parking_id': parking_id,
        'parking_name': parking.name,
        'period_days': days,
        'current_state': {
            'current_occupancy': parking.current_occupancy,
            'max_capacity': parking.max_capacity,
            'status': parking.status,
            'occupancy_percentage': round(parking.current_occupancy / parking.max_capacity * 100, 1) if parking.max_capacity > 0 else 0
        },
        'config': {
            'auto_correction_enabled': config.auto_correction_enabled if config else False,
            'correction_hour': config.correction_hour if config else 6,
            'correction_minute': config.correction_minute if config else 0,
            'avg_hourly_drift': round(config.avg_hourly_drift, 3) if config and config.avg_hourly_drift else 0,
            'avg_daily_drift': round(config.avg_daily_drift, 1) if config and config.avg_daily_drift else 0,
            'confidence_level': round(config.confidence_level, 2) if config and config.confidence_level else 0,
            'sample_count': config.sample_count if config else 0,
            'suggested_correction': config.suggested_correction if config else 0,
            'last_calculation_at': config.last_calculation_at.isoformat() if config and config.last_calculation_at else None,
            'last_auto_correction_at': config.last_auto_correction_at.isoformat() if config and config.last_auto_correction_at else None,
            'last_auto_correction_amount': config.last_auto_correction_amount if config else 0
        },
        'by_weekday': weekday_stats,
        'manual_stats': manual_stats,
        'auto_stats': auto_stats,
        'auto_correction_performance': {
            'total_applied': len(auto_corrections),
            'validated': len(validated_autos),
            'avg_prediction_error': round(avg_error, 1) if avg_error is not None else None,
            'estimated_accuracy': round(accuracy, 2) if accuracy is not None else None,
            'accuracy_percentage': round(accuracy * 100, 1) if accuracy is not None else None
        },
        'comparison': comparison_metrics,
        'patterns_detected': detect_patterns(weekday_stats, config.avg_hourly_drift if config else 0)
    }


def calculate_comparison_metrics(
    manual_adjustments: List,
    auto_corrections: List,
    calculations: List
) -> Dict:
    """
    Calcular métricas de comparación entre ajustes manuales y automáticos.
    
    Returns:
        Dict con métricas de comparación
    """
    # Si no hay datos, retornar métricas vacías
    if not manual_adjustments:
        return {
            'has_data': False,
            'message': 'Sin ajustes manuales en el período'
        }
    
    # Sumatorio de correcciones
    total_manual = sum(a.change_amount or 0 for a in manual_adjustments)
    total_auto = sum(a.correction_amount or 0 for a in auto_corrections)
    
    # Promedios
    avg_manual = total_manual / len(manual_adjustments) if manual_adjustments else 0
    avg_auto = total_auto / len(auto_corrections) if auto_corrections else 0
    
    # Ratio de intervención manual
    # Si hay muchas correcciones manuales después de las automáticas, el algoritmo no es preciso
    manual_after_auto = 0
    for manual in manual_adjustments:
        for auto in auto_corrections:
            if auto.applied_at and manual.timestamp:
                time_diff = (manual.timestamp - auto.applied_at).total_seconds() / 3600
                if 0 < time_diff < 12:  # Manual dentro de 12 horas de auto
                    manual_after_auto += 1
                    break
    
    # Calcular si las correcciones van en la misma dirección
    manual_positive = len([a for a in manual_adjustments if (a.change_amount or 0) > 0])
    manual_negative = len([a for a in manual_adjustments if (a.change_amount or 0) < 0])
    auto_positive = len([a for a in auto_corrections if (a.correction_amount or 0) > 0])
    auto_negative = len([a for a in auto_corrections if (a.correction_amount or 0) < 0])
    
    # Determinar tendencia dominante
    manual_tendency = 'neutral'
    if manual_positive > manual_negative * 1.5:
        manual_tendency = 'positivo'  # Sistema subestima ocupación
    elif manual_negative > manual_positive * 1.5:
        manual_tendency = 'negativo'  # Sistema sobreestima ocupación
    
    # Evaluar coherencia entre algoritmo y realidad
    coherence = 'desconocido'
    if auto_corrections:
        auto_tendency = 'positivo' if auto_positive > auto_negative else 'negativo' if auto_negative > auto_positive else 'neutral'
        if auto_tendency == manual_tendency:
            coherence = 'buena'  # El algoritmo va en la dirección correcta
        elif manual_tendency == 'neutral':
            coherence = 'aceptable'
        else:
            coherence = 'revisar'  # El algoritmo va en dirección contraria
    
    # Calcular reducción de trabajo manual potencial
    if manual_adjustments and auto_corrections:
        # Si las correcciones automáticas son similares a las manuales, hay reducción de trabajo
        work_reduction = min(len(auto_corrections) / len(manual_adjustments), 1.0)
    else:
        work_reduction = 0
    
    return {
        'has_data': True,
        'totals': {
            'manual_corrections_sum': total_manual,
            'auto_corrections_sum': total_auto,
            'difference': total_manual - total_auto
        },
        'averages': {
            'avg_manual_correction': round(avg_manual, 1),
            'avg_auto_correction': round(avg_auto, 1),
            'difference': round(avg_manual - avg_auto, 1)
        },
        'direction': {
            'manual_positive': manual_positive,
            'manual_negative': manual_negative,
            'auto_positive': auto_positive,
            'auto_negative': auto_negative,
            'manual_tendency': manual_tendency,
            'coherence': coherence
        },
        'intervention': {
            'manual_after_auto_count': manual_after_auto,
            'manual_after_auto_ratio': round(manual_after_auto / len(manual_adjustments), 2) if manual_adjustments else 0,
            'estimated_work_reduction': round(work_reduction * 100, 0)
        },
        'recommendations': generate_recommendations(
            manual_tendency, coherence, avg_manual, avg_auto, work_reduction
        )
    }


def generate_recommendations(
    manual_tendency: str,
    coherence: str,
    avg_manual: float,
    avg_auto: float,
    work_reduction: float
) -> List[str]:
    """Generar recomendaciones basadas en las métricas"""
    recommendations = []
    
    if coherence == 'revisar':
        recommendations.append(
            "⚠️ El algoritmo está aplicando correcciones en dirección contraria a las manuales. "
            "Considere revisar los datos históricos o desactivar temporalmente."
        )
    
    if abs(avg_manual - avg_auto) > 10:
        if avg_manual > avg_auto:
            recommendations.append(
                f"📈 Las correcciones manuales son mayores (+{abs(avg_manual - avg_auto):.0f} promedio). "
                "El algoritmo podría ser más agresivo."
            )
        else:
            recommendations.append(
                f"📉 Las correcciones automáticas son mayores (+{abs(avg_auto - avg_manual):.0f} promedio). "
                "El algoritmo podría estar sobrecorrigiendo."
            )
    
    if manual_tendency == 'positivo':
        recommendations.append(
            "📊 Tendencia: El sistema subestima la ocupación real. "
            "Posible causa: salidas no detectadas o errores de cámaras."
        )
    elif manual_tendency == 'negativo':
        recommendations.append(
            "📊 Tendencia: El sistema sobreestima la ocupación real. "
            "Posible causa: entradas duplicadas o falsas detecciones."
        )
    
    if work_reduction < 0.3 and avg_manual != 0:
        recommendations.append(
            "💡 El sistema podría beneficiarse de más datos históricos para mejorar la precisión."
        )
    
    if not recommendations:
        recommendations.append(
            "✅ El sistema funciona correctamente. Continue monitoreando las métricas."
        )
    
    return recommendations


def detect_patterns(weekday_stats: Dict, avg_drift: float) -> List[str]:
    """Detectar patrones en los datos"""
    patterns = []
    
    if not weekday_stats or avg_drift == 0:
        return patterns
    
    # Encontrar máximo y mínimo
    max_day = None
    min_day = None
    max_drift = -float('inf')
    min_drift = float('inf')
    
    for day, stats in weekday_stats.items():
        if stats['sample_count'] > 0:
            drift = stats['avg_drift_per_hour']
            if drift > max_drift:
                max_drift = drift
                max_day = stats['name']
            if drift < min_drift:
                min_drift = drift
                min_day = stats['name']
    
    if max_day and max_drift > avg_drift * 1.2:
        percent = ((max_drift / avg_drift) - 1) * 100
        patterns.append(f"Mayor desviación los {max_day} (+{percent:.0f}% sobre media)")
    
    if min_day and min_drift < avg_drift * 0.8 and avg_drift > 0:
        percent = (1 - (min_drift / avg_drift)) * 100
        patterns.append(f"Menor desviación los {min_day} (-{percent:.0f}% bajo media)")
    
    # Detectar patrón laboral vs fin de semana
    laborable_drifts = [weekday_stats[str(d)]['avg_drift_per_hour'] 
                       for d in range(5) if weekday_stats[str(d)]['sample_count'] > 0]
    weekend_drifts = [weekday_stats[str(d)]['avg_drift_per_hour'] 
                     for d in [5, 6] if weekday_stats[str(d)]['sample_count'] > 0]
    
    if laborable_drifts and weekend_drifts:
        avg_laborable = sum(laborable_drifts) / len(laborable_drifts)
        avg_weekend = sum(weekend_drifts) / len(weekend_drifts)
        
        if abs(avg_laborable - avg_weekend) > abs(avg_drift) * 0.3:
            if avg_laborable > avg_weekend:
                patterns.append("Patrón detectado: Mayor desviación días laborables")
            else:
                patterns.append("Patrón detectado: Mayor desviación fines de semana")
    
    if not patterns:
        patterns.append("Patrón estable sin variaciones significativas por día")
    
    return patterns
