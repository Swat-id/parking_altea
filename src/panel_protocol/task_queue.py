"""
Cola de tareas asíncrona para gestionar múltiples operaciones en paralelo
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import uuid

# Configurar logger con nivel DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass
class Task:
    """Representa una tarea en la cola"""
    task_id: str
    panel_ip: str
    panel_port: int
    operation: Callable
    args: tuple
    kwargs: dict
    created_at: datetime
    future: asyncio.Future
    metadata: Dict[str, Any]


class TaskQueue:
    """
    Cola de tareas asíncrona que permite ejecutar múltiples operaciones
    en paralelo sin bloquear.
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        """
        Inicializa la cola de tareas.
        
        Args:
            max_concurrent_tasks: Número máximo de tareas concurrentes
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"TaskQueue inicializado: max_concurrent_tasks={max_concurrent_tasks}")
    
    async def add_task(
        self,
        panel_ip: str,
        panel_port: int,
        operation: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Añade una tarea a la cola y la ejecuta en paralelo.
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            operation: Función asíncrona a ejecutar
            *args: Argumentos posicionales para la operación
            metadata: Metadatos adicionales de la tarea
            **kwargs: Argumentos con nombre para la operación
            
        Returns:
            str: ID de la tarea
        """
        logger.debug(f"Iniciando add_task para {panel_ip}:{panel_port}")
        task_id = str(uuid.uuid4())
        future = asyncio.Future()
        
        # Añadir panel_ip y panel_port a los kwargs para que la operación los reciba
        # (a menos que ya estén en kwargs)
        operation_kwargs = kwargs.copy()
        if 'panel_ip' not in operation_kwargs:
            operation_kwargs['panel_ip'] = panel_ip
        if 'panel_port' not in operation_kwargs:
            operation_kwargs['panel_port'] = panel_port
        
        task = Task(
            task_id=task_id,
            panel_ip=panel_ip,
            panel_port=panel_port,
            operation=operation,
            args=args,
            kwargs=operation_kwargs,  # Usar kwargs con panel_ip y panel_port incluidos
            created_at=datetime.now(),
            future=future,
            metadata=metadata or {}
        )
        
        logger.debug(f"Adquiriendo lock para añadir tarea {task_id}")
        async with self._lock:
            self._tasks[task_id] = task
        logger.debug(f"Lock liberado, tarea {task_id} añadida al diccionario")
        
        # Ejecutar tarea en background
        logger.debug(f"Creando task en background para {task_id}")
        asyncio.create_task(self._execute_task(task))
        logger.debug(f"Task creada en background para {task_id}")
        
        logger.info(f"✅ Tarea {task_id} añadida a la cola para {panel_ip}:{panel_port} (tipo: {metadata.get('operation_type', 'unknown')})")
        return task_id
    
    async def _execute_task(self, task: Task):
        """Ejecuta una tarea con control de concurrencia"""
        await self._semaphore.acquire()
        
        try:
            logger.info(f"Ejecutando tarea {task.task_id} para {task.panel_ip}:{task.panel_port} (tipo: {task.metadata.get('operation_type', 'unknown')})")
            
            # Ejecutar operación
            if asyncio.iscoroutinefunction(task.operation):
                result = await task.operation(*task.args, **task.kwargs)
            else:
                result = task.operation(*task.args, **task.kwargs)
            
            # Completar future
            if not task.future.done():
                task.future.set_result(result)
            
            logger.info(f"✅ Tarea {task.task_id} completada exitosamente")
            
        except Exception as e:
            import traceback
            error_msg = f"Error ejecutando tarea {task.task_id}: {e}"
            logger.error(error_msg)
            logger.debug(f"Traceback: {traceback.format_exc()}")
            if not task.future.done():
                task.future.set_exception(e)
        
        finally:
            self._semaphore.release()
            # Limpiar tarea después de un tiempo
            asyncio.create_task(self._cleanup_task(task.task_id, delay=300))
    
    async def _cleanup_task(self, task_id: str, delay: int = 300):
        """Limpia una tarea después de un delay"""
        await asyncio.sleep(delay)
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.debug(f"Tarea {task_id} eliminada de la cola")
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Obtiene el resultado de una tarea.
        
        Args:
            task_id: ID de la tarea
            timeout: Timeout en segundos (None = sin timeout)
            
        Returns:
            Resultado de la tarea
            
        Raises:
            asyncio.TimeoutError: Si se excede el timeout
            KeyError: Si la tarea no existe
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Tarea {task_id} no encontrada")
            task = self._tasks[task_id]
        
        if timeout:
            return await asyncio.wait_for(task.future, timeout=timeout)
        else:
            return await task.future
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una tarea.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Dict con información del estado de la tarea
        """
        async with self._lock:
            if task_id not in self._tasks:
                return {
                    'task_id': task_id,
                    'status': 'not_found',
                    'exists': False
                }
            
            task = self._tasks[task_id]
            
            return {
                'task_id': task_id,
                'status': 'completed' if task.future.done() else 'pending',
                'exists': True,
                'created_at': task.created_at.isoformat(),
                'panel_ip': task.panel_ip,
                'panel_port': task.panel_port,
                'metadata': task.metadata,
                'done': task.future.done(),
                'cancelled': task.future.cancelled()
            }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela una tarea pendiente.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            bool: True si se canceló, False si no existe o ya está completada
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            
            if task.future.done():
                return False
            
            cancelled = task.future.cancel()
            if cancelled:
                logger.info(f"Tarea {task_id} cancelada")
            
            return cancelled
    
    async def get_pending_tasks_count(self) -> int:
        """Retorna el número de tareas pendientes"""
        async with self._lock:
            return sum(1 for task in self._tasks.values() if not task.future.done())
    
    async def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Retorna información de todas las tareas"""
        async with self._lock:
            return {
                task_id: await self.get_task_status(task_id)
                for task_id in self._tasks.keys()
            }

