#!/usr/bin/env python3
"""
Servicio independiente para el worker de actualización de paneles
Ejecuta como proceso separado y actualiza paneles cada 2 minutos
"""

import logging
import signal
import sys
import time
import json
from datetime import datetime
from panel_update_worker import PanelUpdateWorker

# Configurar logging específico para el servicio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/panel_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PanelWorkerService:
    """Servicio principal para el worker de paneles"""
    
    def __init__(self, update_interval: int = 120):
        """
        Inicializar el servicio
        
        Args:
            update_interval: Intervalo de actualización en segundos (default: 2 minutos)
        """
        self.worker = PanelUpdateWorker(update_interval=update_interval)
        self.shutdown_requested = False
        
        # Configurar señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Panel Worker Service inicializado - Intervalo: {update_interval}s")
    
    def _signal_handler(self, signum: int, frame):
        """
        Manejar señales de shutdown
        
        Args:
            signum: Número de señal recibida
            frame: Frame actual (no usado)
        """
        signal_names = {
            signal.SIGINT: 'SIGINT (Ctrl+C)',
            signal.SIGTERM: 'SIGTERM'
        }
        
        signal_name = signal_names.get(signum, f'Signal {signum}')
        logger.info(f"Señal {signal_name} recibida, iniciando shutdown graceful...")
        
        self.shutdown_requested = True
    
    def start(self):
        """Iniciar el servicio"""
        logger.info("=== Iniciando Panel Worker Service ===")
        
        try:
            # Iniciar el worker
            self.worker.start()
            logger.info("Panel Worker iniciado correctamente")
            
            # Mostrar estadísticas iniciales
            self._log_startup_info()
            
            # Mantener el servicio corriendo
            stats_log_interval = 300  # Log de estadísticas cada 5 minutos
            last_stats_log = time.time()
            
            while not self.shutdown_requested:
                time.sleep(1)
                
                # Log de estadísticas periódico
                current_time = time.time()
                if current_time - last_stats_log >= stats_log_interval:
                    self._log_statistics()
                    last_stats_log = current_time
        
        except Exception as e:
            logger.error(f"Error crítico en Panel Worker Service: {e}")
            return False
            
        finally:
            self._shutdown()
        
        return True
    
    def _log_startup_info(self):
        """Log de información de startup"""
        stats = self.worker.get_stats()
        
        logger.info("Panel Worker Service configuración:")
        logger.info(f"  - Intervalo de actualización: {self.worker.update_interval}s")
        logger.info(f"  - Máximo workers paralelos: {self.worker.max_panel_workers}")
        logger.info(f"  - Servicio de paneles: {'✓ OK' if self.worker.panel_service else '✗ Error'}")
        logger.info(f"  - Estado inicial: {stats}")
    
    def _log_statistics(self):
        """Log de estadísticas del worker"""
        try:
            stats = self.worker.get_stats()
            
            logger.info("=== Estadísticas Panel Worker ===")
            logger.info(f"Uptime: {stats.get('uptime_formatted', 'N/A')}")
            logger.info(f"Ciclos completados: {stats['cycles_completed']}")
            logger.info(f"Paneles actualizados: {stats['panels_updated']}")
            logger.info(f"Paneles fallidos: {stats['panels_failed']}")
            logger.info(f"Programaciones activas procesadas: {stats['active_schedules_processed']}")
            logger.info(f"Actualizaciones de ocupación enviadas: {stats['occupancy_updates_sent']}")
            logger.info(f"Tiempo promedio por ciclo: {stats['average_cycle_time']:.2f}s")
            logger.info(f"Errores: {stats['errors']}")
            
            if stats['panels_updated'] > 0:
                success_rate = (stats['panels_updated'] / (stats['panels_updated'] + stats['panels_failed'])) * 100
                logger.info(f"Tasa de éxito: {success_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"Error logging estadísticas: {e}")
    
    def _shutdown(self):
        """Realizar shutdown limpio del servicio"""
        logger.info("Iniciando shutdown del Panel Worker Service...")
        
        try:
            # Log de estadísticas finales
            self._log_final_statistics()
            
            # Detener el worker
            self.worker.stop()
            logger.info("Panel Worker detenido correctamente")
            
        except Exception as e:
            logger.error(f"Error durante shutdown: {e}")
        
        logger.info("Panel Worker Service detenido")
    
    def _log_final_statistics(self):
        """Log de estadísticas finales"""
        try:
            stats = self.worker.get_stats()
            
            logger.info("=== Estadísticas Finales ===")
            logger.info(f"Tiempo total de ejecución: {stats.get('uptime_formatted', 'N/A')}")
            logger.info(f"Total ciclos: {stats['cycles_completed']}")
            logger.info(f"Total paneles actualizados: {stats['panels_updated']}")
            logger.info(f"Total errores: {stats['errors']}")
            
            # Guardar estadísticas en archivo JSON para análisis posterior
            self._save_final_stats_to_file(stats)
            
        except Exception as e:
            logger.error(f"Error generando estadísticas finales: {e}")
    
    def _save_final_stats_to_file(self, stats: dict):
        """Guardar estadísticas finales en archivo JSON"""
        try:
            # Preparar datos para JSON (convertir datetime a string)
            json_stats = {}
            for key, value in stats.items():
                if isinstance(value, datetime):
                    json_stats[key] = value.isoformat()
                else:
                    json_stats[key] = value
            
            # Añadir metadata
            json_stats['shutdown_time'] = datetime.now().isoformat()
            json_stats['service_version'] = 'v3.4.0'
            
            # Guardar en archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/panel_worker_stats_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(json_stats, f, indent=2)
            
            logger.info(f"Estadísticas guardadas en: {filename}")
            
        except Exception as e:
            logger.error(f"Error guardando estadísticas: {e}")
    
    def get_status(self) -> dict:
        """
        Obtener estado actual del servicio
        
        Returns:
            Diccionario con estado del servicio
        """
        worker_stats = self.worker.get_stats()
        
        return {
            'service_running': not self.shutdown_requested,
            'worker_stats': worker_stats,
            'service_version': 'v3.4.0',
            'current_time': datetime.now().isoformat()
        }


def main():
    """Función principal del servicio"""
    # Configurar argumentos de línea de comandos
    import argparse
    
    parser = argparse.ArgumentParser(description='Panel Worker Service v3.4.0')
    parser.add_argument(
        '--interval', 
        type=int, 
        default=120, 
        help='Intervalo de actualización en segundos (default: 120)'
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='Ejecutar en modo test (intervalo corto de 30s)'
    )
    parser.add_argument(
        '--stats', 
        action='store_true', 
        help='Mostrar estadísticas del worker y salir'
    )
    
    args = parser.parse_args()
    
    # Ajustar intervalo para modo test
    if args.test:
        interval = 30
        logger.info("Modo TEST activado - Intervalo: 30 segundos")
    else:
        interval = args.interval
    
    # Modo estadísticas
    if args.stats:
        try:
            # Intentar conectar y obtener estadísticas
            worker = PanelUpdateWorker(update_interval=interval)
            stats = worker.get_stats()
            
            print("=== Panel Worker Service Stats ===")
            print(json.dumps(stats, indent=2, default=str))
            
            worker.shutdown()
            return 0
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return 1
    
    # Iniciar servicio normal
    service = PanelWorkerService(update_interval=interval)
    
    try:
        success = service.start()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Servicio interrumpido por usuario")
        return 0
    
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
