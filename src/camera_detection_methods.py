#!/usr/bin/env python3
"""
Métodos de detección y validación para CameraMessageProcessor
Incluye detección inteligente de reinicios y validación reforzada de deltas
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Access, Parking, CameraParking, OccupancyHistory
from camera_message_processor import ResetInfo, DeltaValidation

logger = logging.getLogger(__name__)


class CameraDetectionMethods:
    """Métodos de detección y validación para el procesador de mensajes"""
    
    @staticmethod
    def detect_reset_intelligent(camera: Access, message_data: Dict[str, Any]) -> ResetInfo:
        """
        Detección inteligente de reinicios con múltiples criterios
        
        Args:
            camera: Objeto Access de la cámara
            message_data: Datos del mensaje recibido
            
        Returns:
            ResetInfo con información sobre el reinicio detectado
        """
        previous_in = camera.last_vehicle_in or 0
        previous_out = camera.last_vehicle_out or 0
        new_in = message_data.get('vehicle_in', 0)
        new_out = message_data.get('vehicle_out', 0)
        
        # Criterios para detección de reinicio
        criteria = {
            'significant_decrease': False,
            'zero_reset': False,
            'time_gap': False,
            'magnitude_check': False,
            'both_counters_decrease': False
        }
        
        # 1. Disminución significativa (>90% en ambos contadores)
        if previous_in > 10 and previous_out > 10:  # Solo si hay valores significativos
            in_decrease_pct = ((previous_in - new_in) / previous_in) * 100 if new_in < previous_in else 0
            out_decrease_pct = ((previous_out - new_out) / previous_out) * 100 if new_out < previous_out else 0
            
            if in_decrease_pct > 90 and out_decrease_pct > 90:
                criteria['significant_decrease'] = True
                logger.info(f"Criterio 1: Disminución significativa - IN: {in_decrease_pct:.1f}%, OUT: {out_decrease_pct:.1f}%")
        
        # 2. Reset a cero desde valores altos
        if (new_in == 0 and previous_in > 100) or (new_out == 0 and previous_out > 100):
            criteria['zero_reset'] = True
            logger.info(f"Criterio 2: Reset a cero - Previous IN: {previous_in}, OUT: {previous_out} -> New IN: {new_in}, OUT: {new_out}")
        
        # 3. Verificación de tiempo (si ha pasado mucho tiempo sin mensajes)
        if camera.last_message_received:
            time_gap_hours = (datetime.now(timezone.utc) - camera.last_message_received).total_seconds() / 3600
            if time_gap_hours > 12:  # Más de 12 horas sin mensajes
                criteria['time_gap'] = True
                logger.info(f"Criterio 3: Gap temporal - {time_gap_hours:.1f} horas sin mensajes")
        
        # 4. Verificación de magnitud del cambio total
        total_previous = previous_in + previous_out
        total_new = new_in + new_out
        if total_previous > 1000 and total_new < 100:
            criteria['magnitude_check'] = True
            logger.info(f"Criterio 4: Magnitud - Total anterior: {total_previous}, nuevo: {total_new}")
        
        # 5. Ambos contadores disminuyen simultáneamente (criterio adicional)
        if new_in < previous_in and new_out < previous_out and (previous_in > 50 or previous_out > 50):
            criteria['both_counters_decrease'] = True
            logger.info(f"Criterio 5: Ambos contadores disminuyen - IN: {previous_in}->{new_in}, OUT: {previous_out}->{new_out}")
        
        # DECISIÓN: Es reinicio si se cumplen múltiples criterios
        # Criterios fuertes: significant_decrease, zero_reset
        # Criterios de apoyo: time_gap, magnitude_check, both_counters_decrease
        strong_criteria = criteria['significant_decrease'] or criteria['zero_reset']
        support_criteria = sum([
            criteria['time_gap'],
            criteria['magnitude_check'], 
            criteria['both_counters_decrease']
        ])
        
        is_reset = strong_criteria or (support_criteria >= 2)
        confidence = CameraDetectionMethods._calculate_reset_confidence(criteria)
        
        # Determinar razón del reinicio
        if criteria['zero_reset']:
            reason = "Reset a cero detectado"
        elif criteria['significant_decrease']:
            reason = "Disminución significativa en ambos contadores"
        elif support_criteria >= 2:
            reason = f"Múltiples criterios de soporte ({support_criteria}/3)"
        else:
            reason = "Sin reinicio detectado"
        
        reset_info = ResetInfo(
            is_reset=is_reset,
            criteria_met=criteria,
            confidence=confidence,
            previous_in=previous_in,
            previous_out=previous_out,
            new_in=new_in,
            new_out=new_out,
            reason=reason
        )
        
        if is_reset:
            logger.warning(f"REINICIO DETECTADO - {reason} (Confianza: {confidence}%)")
            logger.warning(f"Detalles: {criteria}")
        
        return reset_info
    
    @staticmethod
    def _calculate_reset_confidence(criteria: Dict[str, bool]) -> float:
        """
        Calcular nivel de confianza del reinicio detectado
        
        Args:
            criteria: Diccionario con criterios evaluados
            
        Returns:
            Nivel de confianza de 0-100%
        """
        weights = {
            'significant_decrease': 40,  # Criterio más fuerte
            'zero_reset': 45,           # Criterio más fuerte
            'time_gap': 10,            # Criterio de apoyo
            'magnitude_check': 15,      # Criterio de apoyo
            'both_counters_decrease': 10  # Criterio de apoyo
        }
        
        confidence = sum(weights[criterion] for criterion, met in criteria.items() if met)
        return min(confidence, 100)  # Máximo 100%
    
    @staticmethod
    def calculate_and_validate_deltas(camera: Access, message_data: Dict[str, Any], reset_info: ResetInfo) -> DeltaValidation:
        """
        Cálculo y validación reforzada de deltas con múltiples controles
        
        Args:
            camera: Objeto Access de la cámara
            message_data: Datos del mensaje
            reset_info: Información sobre reinicio detectado
            
        Returns:
            DeltaValidation con resultado de la validación
        """
        if reset_info.is_reset:
            return DeltaValidation(
                valid=True,
                delta_in=0,
                delta_out=0,
                validations=[],
                reason='reset_detected_deltas_zeroed'
            )
        
        # Calcular deltas normales
        previous_in = reset_info.previous_in
        previous_out = reset_info.previous_out
        new_in = reset_info.new_in
        new_out = reset_info.new_out
        
        # Deltas base (no permitir negativos en operación normal)
        delta_in = max(0, new_in - previous_in)
        delta_out = max(0, new_out - previous_out)
        
        # VALIDACIONES MÚLTIPLES
        validations = []
        
        # 1. Validación de magnitud máxima por mensaje
        max_delta_per_message = 50  # Máximo 50 vehículos por mensaje
        if delta_in > max_delta_per_message:
            validations.append(f"delta_in excesivo: {delta_in} > {max_delta_per_message}")
        
        if delta_out > max_delta_per_message:
            validations.append(f"delta_out excesivo: {delta_out} > {max_delta_per_message}")
        
        # 2. Validación de frecuencia de mensajes (velocidad de cambio)
        if camera.last_message_received:
            time_diff_minutes = (datetime.now(timezone.utc) - camera.last_message_received).total_seconds() / 60
            
            if time_diff_minutes > 0:
                # Calcular tasa de cambio por minuto
                total_delta = delta_in + delta_out
                delta_rate = total_delta / time_diff_minutes
                max_delta_per_minute = 30  # Máximo 30 vehículos por minuto
                
                if delta_rate > max_delta_per_minute:
                    validations.append(f"tasa de cambio excesiva: {delta_rate:.1f} veh/min > {max_delta_per_minute}")
        
        # 3. Validación de patrones anómalos
        if delta_in == 0 and delta_out > 15:
            validations.append(f"patrón anómalo: solo salidas masivas ({delta_out}) sin entradas")
        
        if delta_in > 20 and delta_out == 0:
            validations.append(f"patrón anómalo: solo entradas masivas ({delta_in}) sin salidas")
        
        # 4. Validación de consistencia temporal
        # Si pasa mucho tiempo entre mensajes, permitir deltas más grandes
        if camera.last_message_received:
            time_diff_hours = (datetime.now(timezone.utc) - camera.last_message_received).total_seconds() / 3600
            if time_diff_hours > 2:  # Más de 2 horas
                # Ser más permisivo con deltas grandes si ha pasado mucho tiempo
                logger.info(f"Gap temporal de {time_diff_hours:.1f}h - siendo más permisivo con deltas")
                # Remover validaciones de magnitud si hay gap temporal significativo
                validations = [v for v in validations if 'excesivo' not in v]
        
        # 5. Validación de límites físicos de parkings
        # Esta validación se hará a nivel de parking, no aquí
        
        # RESULTADO
        is_valid = len(validations) == 0
        
        # Si hay validaciones fallidas, poner deltas a 0 para seguridad
        final_delta_in = delta_in if is_valid else 0
        final_delta_out = delta_out if is_valid else 0
        
        validation_result = DeltaValidation(
            valid=is_valid,
            delta_in=final_delta_in,
            delta_out=final_delta_out,
            validations=validations,
            reason='; '.join(validations) if validations else 'valid'
        )
        
        if not is_valid:
            logger.warning(f"Validación de deltas fallida: {validation_result.reason}")
        else:
            logger.debug(f"Deltas validados: IN={final_delta_in}, OUT={final_delta_out}")
        
        return validation_result
    
    @staticmethod
    def validate_parking_occupancy(new_occupancy: int, max_capacity: int, current_occupancy: int, 
                                 delta_in: int, delta_out: int) -> Dict[str, Any]:
        """
        Validación final de ocupación a nivel de parking
        
        Args:
            new_occupancy: Nueva ocupación calculada
            max_capacity: Capacidad máxima del parking
            current_occupancy: Ocupación actual
            delta_in: Delta de entradas
            delta_out: Delta de salidas
            
        Returns:
            Diccionario con resultado de validación
        """
        # Permitir ocupación negativa limitada (errores de conteo)
        min_allowed = -15  # Máximo 15 vehículos negativos permitidos
        
        # Permitir exceso limitado (hasta 200% de capacidad en casos extremos)
        max_allowed = int(max_capacity * 2.0)
        
        corrected_occupancy = new_occupancy
        validations = []
        
        # Verificar límites extremos
        if new_occupancy < min_allowed:
            corrected_occupancy = min_allowed
            validations.append(f"ocupación muy negativa: {new_occupancy} < {min_allowed}, corregido a {min_allowed}")
        
        if new_occupancy > max_allowed:
            corrected_occupancy = max_allowed
            validations.append(f"ocupación excesiva: {new_occupancy} > {max_allowed}, corregido a {max_allowed}")
        
        # Verificar consistencia de salidas (no más salidas que vehículos disponibles)
        available_vehicles = current_occupancy + delta_in
        if delta_out > (available_vehicles + 10):  # Margen de 10 vehículos
            validations.append(f"más salidas que vehículos disponibles: out={delta_out}, disponible={available_vehicles}")
        
        # Alertar sobre ocupación excesiva pero permitirla
        if new_occupancy > max_capacity * 1.2:  # Más del 120% de capacidad
            validations.append(f"ocupación alta: {new_occupancy} > {int(max_capacity * 1.2)} (120% capacidad)")
        
        is_valid = len(validations) == 0
        
        return {
            'valid': is_valid,
            'corrected_occupancy': corrected_occupancy,
            'validations': validations,
            'reason': '; '.join(validations) if validations else 'valid',
            'needs_correction': corrected_occupancy != new_occupancy
        }
