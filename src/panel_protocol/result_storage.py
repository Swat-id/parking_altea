"""
Almacenamiento de resultados de operaciones con paneles
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class OperationResult:
    """Resultado de una operación con un panel"""
    task_id: str
    panel_ip: str
    panel_port: int
    operation_type: str
    success: bool
    timestamp: datetime
    response_data: Optional[bytes] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> dict:
        """Convierte el resultado a diccionario"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        if self.response_data:
            result['response_data'] = self.response_data.hex()
        return result


class ResultStorage:
    """
    Almacenamiento de resultados de operaciones con paneles.
    Mantiene un historial de operaciones con capacidad de limpieza automática.
    """
    
    def __init__(self, max_results: int = 1000, retention_hours: int = 24):
        """
        Inicializa el almacenamiento de resultados.
        
        Args:
            max_results: Número máximo de resultados a mantener
            retention_hours: Horas de retención de resultados
        """
        self.max_results = max_results
        self.retention_hours = retention_hours
        
        # Almacenamiento por panel: {panel_key: [results]}
        self._results: Dict[str, List[OperationResult]] = defaultdict(list)
        
        # Almacenamiento por task_id para búsqueda rápida
        self._results_by_task: Dict[str, OperationResult] = {}
        
        # Lock para operaciones concurrentes
        self._lock = None  # Se inicializará en métodos async
        
        logger.info(
            f"ResultStorage inicializado: max_results={max_results}, "
            f"retention_hours={retention_hours}"
        )
    
    def _get_panel_key(self, ip: str, port: int) -> str:
        """Genera una clave única para un panel"""
        return f"{ip}:{port}"
    
    async def store_result(self, result: OperationResult):
        """
        Almacena un resultado de operación.
        
        Args:
            result: Resultado a almacenar
        """
        import asyncio
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            panel_key = self._get_panel_key(result.panel_ip, result.panel_port)
            
            # Añadir resultado
            self._results[panel_key].append(result)
            self._results_by_task[result.task_id] = result
            
            # Limitar tamaño por panel
            if len(self._results[panel_key]) > self.max_results:
                # Eliminar el más antiguo
                removed = self._results[panel_key].pop(0)
                if removed.task_id in self._results_by_task:
                    del self._results_by_task[removed.task_id]
            
            logger.debug(
                f"Resultado almacenado: task_id={result.task_id}, "
                f"panel={panel_key}, success={result.success}"
            )
            
            # Limpiar resultados antiguos periódicamente
            if len(self._results_by_task) % 100 == 0:
                await self._cleanup_old_results()
    
    async def get_result(self, task_id: str) -> Optional[OperationResult]:
        """
        Obtiene un resultado por task_id.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            OperationResult o None si no existe
        """
        import asyncio
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            return self._results_by_task.get(task_id)
    
    async def get_panel_results(
        self,
        ip: str,
        port: int,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[OperationResult]:
        """
        Obtiene resultados de un panel específico.
        
        Args:
            ip: IP del panel
            port: Puerto del panel
            limit: Límite de resultados a retornar
            since: Solo resultados desde esta fecha
            
        Returns:
            Lista de resultados ordenados por timestamp (más reciente primero)
        """
        import asyncio
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            panel_key = self._get_panel_key(ip, port)
            results = self._results.get(panel_key, [])
            
            # Filtrar por fecha si se especifica
            if since:
                results = [r for r in results if r.timestamp >= since]
            
            # Ordenar por timestamp (más reciente primero)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Limitar resultados
            if limit:
                results = results[:limit]
            
            return results
    
    async def get_success_rate(
        self,
        ip: str,
        port: int,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calcula la tasa de éxito de operaciones para un panel.
        
        Args:
            ip: IP del panel
            port: Puerto del panel
            since: Solo considerar resultados desde esta fecha
            
        Returns:
            Dict con estadísticas de éxito
        """
        results = await self.get_panel_results(ip, port, since=since)
        
        if not results:
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        
        total = len(results)
        success = sum(1 for r in results if r.success)
        failed = total - success
        success_rate = (success / total) * 100 if total > 0 else 0.0
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': round(success_rate, 2)
        }
    
    async def _cleanup_old_results(self):
        """Limpia resultados más antiguos que el tiempo de retención"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        for panel_key in list(self._results.keys()):
            original_count = len(self._results[panel_key])
            
            # Filtrar resultados antiguos
            self._results[panel_key] = [
                r for r in self._results[panel_key]
                if r.timestamp >= cutoff_time
            ]
            
            removed_count = original_count - len(self._results[panel_key])
            
            # Limpiar también del índice por task_id
            if removed_count > 0:
                for result in self._results[panel_key]:
                    if result.task_id in self._results_by_task:
                        if self._results_by_task[result.task_id].timestamp < cutoff_time:
                            del self._results_by_task[result.task_id]
            
            # Si el panel no tiene resultados, eliminarlo
            if not self._results[panel_key]:
                del self._results[panel_key]
        
        logger.debug(f"Limpieza de resultados antiguos completada")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales del almacenamiento.
        
        Returns:
            Dict con estadísticas
        """
        import asyncio
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            total_results = sum(len(results) for results in self._results.values())
            total_panels = len(self._results)
            
            total_success = sum(
                1 for results in self._results.values()
                for r in results if r.success
            )
            
            total_failed = total_results - total_success
            
            return {
                'total_results': total_results,
                'total_panels': total_panels,
                'total_success': total_success,
                'total_failed': total_failed,
                'overall_success_rate': round((total_success / total_results * 100) if total_results > 0 else 0, 2),
                'panels': list(self._results.keys())
            }

