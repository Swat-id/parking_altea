#!/usr/bin/env python3
"""
Worker de Corrección Automática de Ocupación v4.5.0

Este worker ejecuta correcciones automáticas a la hora configurada (06:00 por defecto)
para todos los parkings con corrección automática habilitada.

Se ejecuta continuamente y verifica cada minuto si hay correcciones pendientes.

Uso:
    python auto_correction_worker.py [--interval 60]

Autor: Parking Altea Team
Fecha: 2026-01-26
"""

import os
import sys
import time
import signal
import argparse
import logging
from datetime import datetime, date
from typing import Set

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Parking, ParkingCorrectionConfig

# Usar nueva versión del servicio v4.5.1
try:
    from auto_correction_service_v2 import apply_auto_correction_v2 as apply_auto_correction
    from auto_correction_service_v2 import calculate_suggested_correction_v2 as calculate_suggested_correction
    logger = logging.getLogger('auto_correction_worker')
    logger.info("Usando algoritmo de corrección v4.5.1 (basado en ratio y transacciones)")
except ImportError:
    from auto_correction_service import apply_auto_correction, calculate_suggested_correction
    logger = logging.getLogger('auto_correction_worker')
    logger.info("Usando algoritmo de corrección v4.5.0 (basado en drift)")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auto_correction_worker')

# Configuración
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://parking_user:parking_pass@localhost:5432/parking_db')


class AutoCorrectionWorker:
    """
    Worker que ejecuta correcciones automáticas de ocupación.
    
    Características:
    - Se ejecuta continuamente verificando cada minuto
    - Solo aplica correcciones a la hora configurada de cada parking
    - Mantiene registro de correcciones aplicadas hoy para evitar duplicados
    - Puede ser detenido gracefully con SIGINT/SIGTERM
    """
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.running = True
        self.corrections_today: Set[int] = set()  # parking_ids corregidos hoy
        self.current_date = date.today()
        
        # Configurar signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de terminación"""
        logger.info(f"Recibida señal {signum}. Deteniendo worker...")
        self.running = False
    
    def _reset_daily_tracking(self):
        """Resetear tracking diario si cambió el día"""
        today = date.today()
        if today != self.current_date:
            logger.info(f"Nuevo día detectado ({today}). Reseteando tracking.")
            self.corrections_today.clear()
            self.current_date = today
    
    def _get_parkings_for_correction(self, session, current_hour: int, current_minute: int):
        """
        Obtener parkings que necesitan corrección en este momento.
        
        Args:
            session: Sesión de BD
            current_hour: Hora actual (0-23)
            current_minute: Minuto actual (0-59)
        
        Returns:
            Lista de configuraciones de parkings a corregir
        """
        configs = session.query(ParkingCorrectionConfig).filter(
            ParkingCorrectionConfig.auto_correction_enabled == True,
            ParkingCorrectionConfig.correction_hour == current_hour,
            ParkingCorrectionConfig.correction_minute == current_minute
        ).all()
        
        # Filtrar los que ya se corrigieron hoy
        configs = [c for c in configs if c.parking_id not in self.corrections_today]
        
        return configs
    
    def run_cycle(self):
        """Ejecutar un ciclo de verificación"""
        self._reset_daily_tracking()
        
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        session = self.Session()
        
        try:
            # Obtener parkings para corregir
            configs = self._get_parkings_for_correction(session, current_hour, current_minute)
            
            if not configs:
                return
            
            logger.info(f"Procesando {len(configs)} parkings para corrección automática")
            
            results = {
                'applied': 0,
                'skipped': 0,
                'errors': 0
            }
            
            for config in configs:
                parking = session.query(Parking).get(config.parking_id)
                if not parking:
                    continue
                
                try:
                    logger.info(f"Procesando parking: {parking.name} (ID: {parking.id})")
                    
                    # Calcular y mostrar sugerencia
                    calc = calculate_suggested_correction(
                        session,
                        config.parking_id,
                        target_hour=current_hour,
                        target_weekday=current_time.weekday()
                    )
                    
                    logger.info(
                        f"  Sugerencia: {calc.get('suggested_correction', 0):+d}, "
                        f"Drift/h: {calc.get('effective_drift_per_hour', 0):.3f}, "
                        f"Confianza: {calc.get('confidence', {}).get('overall', 0)*100:.0f}%"
                    )
                    
                    # Aplicar corrección
                    result = apply_auto_correction(session, config.parking_id)
                    
                    if result:
                        if result.get('applied'):
                            logger.info(
                                f"  ✓ Aplicada: {result['previous_occupancy']} → {result['new_occupancy']} "
                                f"({result['correction_amount']:+d})"
                            )
                            results['applied'] += 1
                            self.corrections_today.add(config.parking_id)
                        elif result.get('skipped'):
                            logger.info(f"  → Omitida: {result.get('reason', 'unknown')}")
                            results['skipped'] += 1
                            # También marcar como procesado para no reintentar
                            self.corrections_today.add(config.parking_id)
                    else:
                        results['skipped'] += 1
                        self.corrections_today.add(config.parking_id)
                    
                except Exception as e:
                    logger.error(f"  ✗ Error procesando parking {parking.name}: {e}")
                    results['errors'] += 1
            
            logger.info(
                f"Ciclo completado: {results['applied']} aplicadas, "
                f"{results['skipped']} omitidas, {results['errors']} errores"
            )
            
        except Exception as e:
            logger.error(f"Error en ciclo de corrección: {e}")
        finally:
            session.close()
    
    def start(self, interval_seconds: int = 60):
        """
        Iniciar el worker.
        
        Args:
            interval_seconds: Intervalo entre verificaciones (default: 60s)
        """
        logger.info("=" * 60)
        logger.info("INICIANDO WORKER DE CORRECCIÓN AUTOMÁTICA v4.5.0")
        logger.info(f"Intervalo de verificación: {interval_seconds}s")
        logger.info("=" * 60)
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Error inesperado en worker: {e}")
            
            # Esperar hasta el próximo ciclo
            for _ in range(interval_seconds):
                if not self.running:
                    break
                time.sleep(1)
        
        logger.info("Worker detenido correctamente")
    
    def run_manual(self, parking_id: int = None):
        """
        Ejecutar corrección manual (para testing).
        
        Args:
            parking_id: ID específico de parking (None para todos con corrección habilitada)
        """
        session = self.Session()
        
        try:
            if parking_id:
                configs = session.query(ParkingCorrectionConfig).filter_by(
                    parking_id=parking_id,
                    auto_correction_enabled=True
                ).all()
            else:
                configs = session.query(ParkingCorrectionConfig).filter_by(
                    auto_correction_enabled=True
                ).all()
            
            logger.info(f"Ejecutando corrección manual para {len(configs)} parkings")
            
            for config in configs:
                parking = session.query(Parking).get(config.parking_id)
                if not parking:
                    continue
                
                logger.info(f"\nProcesando: {parking.name}")
                
                # Calcular
                calc = calculate_suggested_correction(
                    session,
                    config.parking_id,
                    target_weekday=datetime.now().weekday()
                )
                
                logger.info(f"  Ocupación actual: {parking.current_occupancy}")
                logger.info(f"  Sugerencia: {calc.get('suggested_correction', 0):+d}")
                logger.info(f"  Confianza: {calc.get('confidence', {}).get('overall', 0)*100:.0f}%")
                
                # Aplicar
                result = apply_auto_correction(session, config.parking_id)
                
                if result and result.get('applied'):
                    logger.info(f"  ✓ Nueva ocupación: {result['new_occupancy']}")
                else:
                    reason = result.get('reason', 'unknown') if result else 'no result'
                    logger.info(f"  → No aplicada: {reason}")
            
        finally:
            session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Worker de corrección automática de ocupación'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalo de verificación en segundos (default: 60)'
    )
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Ejecutar corrección manual una vez y salir'
    )
    parser.add_argument(
        '--parking-id',
        type=int,
        default=None,
        help='ID de parking específico (solo con --manual)'
    )
    
    args = parser.parse_args()
    
    worker = AutoCorrectionWorker()
    
    if args.manual:
        worker.run_manual(parking_id=args.parking_id)
    else:
        worker.start(interval_seconds=args.interval)


if __name__ == '__main__':
    main()
