"""
Servicio principal de protocolo de paneles LED
Gestiona comunicación asíncrona, paralela y almacenamiento de resultados
"""

import asyncio
import logging
from typing import List, Tuple, Optional, Dict, Any, Callable
from datetime import datetime

from .connection_pool import ConnectionPool
from .task_queue import TaskQueue
from .result_storage import ResultStorage, OperationResult
from .packet_builder import PacketBuilder
from .packet_parser import PacketParser
from .constants import (
    DEFAULT_PORT, Color, FontSize, Effect, Alignment,
    CARD_ID_BROADCAST
)

logger = logging.getLogger(__name__)


class PanelProtocolService:
    """
    Servicio principal para comunicación con paneles LED.
    Gestiona múltiples operaciones en paralelo sin bloquear.
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        max_connections_per_panel: int = 5,
        connection_timeout: float = 5.0,
        read_timeout: float = 10.0,
        max_results: int = 1000,
        retention_hours: int = 24
    ):
        """
        Inicializa el servicio de protocolo de paneles.
        
        Args:
            max_concurrent_tasks: Máximo de tareas concurrentes
            max_connections_per_panel: Máximo de conexiones por panel
            connection_timeout: Timeout para conexión (segundos)
            read_timeout: Timeout para lectura (segundos)
            max_results: Máximo de resultados a almacenar
            retention_hours: Horas de retención de resultados
        """
        self.connection_pool = ConnectionPool(
            max_connections_per_panel=max_connections_per_panel,
            connection_timeout=connection_timeout,
            read_timeout=read_timeout
        )
        
        self.task_queue = TaskQueue(max_concurrent_tasks=max_concurrent_tasks)
        self.result_storage = ResultStorage(
            max_results=max_results,
            retention_hours=retention_hours
        )
        
        logger.info("PanelProtocolService inicializado")
    
    async def create_window(
        self,
        panel_ip: str,
        panel_port: int,
        windows: List[Tuple[int, int, int, int]],
        card_id: int = CARD_ID_BROADCAST,
        request_confirmation: bool = True,
        wait_for_response: bool = False
    ) -> str:
        """
        Crea ventanas en un panel (operación asíncrona).
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            windows: Lista de tuplas (x, y, width, height)
            card_id: ID de la tarjeta (por defecto broadcast)
            request_confirmation: Si solicita confirmación
            wait_for_response: Si True, espera la respuesta antes de retornar
            
        Returns:
            str: ID de la tarea
        """
        packet = PacketBuilder.build_create_window_packet(
            card_id=card_id,
            windows=windows,
            request_confirmation=request_confirmation
        )
        
        task_id = await self.task_queue.add_task(
            panel_ip=panel_ip,
            panel_port=panel_port,
            operation=self._send_packet_operation,
            packet=packet,
            operation_type="create_window",
            metadata={
                'windows': windows,
                'card_id': card_id
            }
        )
        
        if wait_for_response:
            await self.task_queue.get_task_result(task_id)
        
        return task_id
    
    async def send_text(
        self,
        panel_ip: str,
        panel_port: int,
        window_id: int,
        text: str,
        color: int = Color.GREEN,
        font_size: int = FontSize.SIZE_16,
        effect: int = Effect.DRAW,
        alignment: int = Alignment.CENTER_CENTER,
        speed: int = 0x00,
        stay_time: int = 3,
        card_id: int = CARD_ID_BROADCAST,
        request_confirmation: bool = True,
        wait_for_response: bool = False
    ) -> str:
        """
        Envía texto directamente a una ventana del panel (operación asíncrona).
        
        La ventana debe existir previamente en el panel.
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            window_id: ID de la ventana (debe existir previamente)
            text: Texto a enviar
            color: Color del texto (Color.RED, Color.GREEN, etc.)
            font_size: Tamaño de fuente (FontSize.SIZE_8, etc.)
            effect: Efecto de texto (Effect.DRAW, Effect.SCROLL_LEFT, etc.)
            alignment: Alineación (Alignment.CENTER_CENTER, etc.)
            speed: Velocidad del efecto (0x00 = más rápido)
            stay_time: Tiempo de espera en segundos
            card_id: ID de la tarjeta
            request_confirmation: Si solicita confirmación
            wait_for_response: Si True, espera la respuesta antes de retornar
            
        Returns:
            str: ID de la tarea
        """
        logger.info(f"Enviando texto '{text}' a ventana {window_id} en {panel_ip}:{panel_port}")
        logger.debug(f"send_text iniciado en event loop: {asyncio.get_event_loop()}")
        
        # Construir paquete para enviar texto
        logger.debug("Construyendo paquete...")
        packet = PacketBuilder.build_send_text_packet(
            card_id=card_id,
            window_id=window_id,
            text=text,
            color=color,
            font_size=font_size,
            effect=effect,
            alignment=alignment,
            speed=speed,
            stay_time=stay_time,
            request_confirmation=request_confirmation
        )
        
        # Crear tarea de envío de texto y obtener task_id inmediatamente
        logger.debug("Llamando a add_task...")
        task_id = await self.task_queue.add_task(
            panel_ip=panel_ip,
            panel_port=panel_port,
            operation=self._send_packet_operation,
            packet=packet,
            operation_type="send_text",
            metadata={
                'window_id': window_id,
                'text': text,
                'color': color,
                'font_size': font_size,
                'effect': effect
            }
        )
        
        logger.info(f"✅ Tarea {task_id} creada para enviar texto a ventana {window_id}")
        
        if wait_for_response:
            await self.task_queue.get_task_result(task_id)
        
        return task_id
    
    async def send_image(
        self,
        panel_ip: str,
        panel_port: int,
        window_id: int,
        filename: str,
        draw_mode: int = 0x00,
        speed: int = 0x01,
        stay_time: int = 3,
        x: int = 0,
        y: int = 0,
        card_id: int = CARD_ID_BROADCAST,
        request_confirmation: bool = True,
        wait_for_response: bool = False
    ) -> str:
        """
        Envía una imagen a una ventana del panel (operación asíncrona).
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            window_id: ID de la ventana
            filename: Nombre del archivo (ej: "test.gif")
            draw_mode: Modo de mostrar (0x00 = Draw)
            speed: Velocidad de mostrar
            stay_time: Tiempo de espera en segundos
            x: Coordenada X
            y: Coordenada Y
            card_id: ID de la tarjeta
            request_confirmation: Si solicita confirmación
            wait_for_response: Si True, espera la respuesta antes de retornar
            
        Returns:
            str: ID de la tarea
        """
        packet = PacketBuilder.build_send_image_packet(
            card_id=card_id,
            window_id=window_id,
            filename=filename,
            draw_mode=draw_mode,
            speed=speed,
            stay_time=stay_time,
            x=x,
            y=y,
            request_confirmation=request_confirmation
        )
        
        task_id = await self.task_queue.add_task(
            panel_ip=panel_ip,
            panel_port=panel_port,
            operation=self._send_packet_operation,
            packet=packet,
            operation_type="send_image",
            metadata={
                'window_id': window_id,
                'filename': filename
            }
        )
        
        if wait_for_response:
            await self.task_queue.get_task_result(task_id)
        
        return task_id
    
    async def execute_program(
        self,
        panel_ip: str,
        panel_port: int,
        program_number: int,
        program_count: int = 1,
        card_id: int = CARD_ID_BROADCAST,
        request_confirmation: bool = True,
        wait_for_response: bool = False
    ) -> str:
        """
        Ejecuta un programa guardado en el panel (operación asíncrona).
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            program_number: Número del programa a ejecutar
            program_count: Cantidad de programas
            card_id: ID de la tarjeta
            request_confirmation: Si solicita confirmación
            wait_for_response: Si True, espera la respuesta antes de retornar
            
        Returns:
            str: ID de la tarea
        """
        packet = PacketBuilder.build_execute_program_packet(
            card_id=card_id,
            program_number=program_number,
            program_count=program_count,
            request_confirmation=request_confirmation
        )
        
        task_id = await self.task_queue.add_task(
            panel_ip=panel_ip,
            panel_port=panel_port,
            operation=self._send_packet_operation,
            packet=packet,
            operation_type="execute_program",
            metadata={
                'program_number': program_number
            }
        )
        
        if wait_for_response:
            await self.task_queue.get_task_result(task_id)
        
        return task_id
    
    async def _send_packet_operation(
        self,
        packet: bytes,
        operation_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Operación interna para enviar un paquete y procesar la respuesta.
        
        Args:
            packet: Paquete a enviar
            operation_type: Tipo de operación
            **kwargs: Debe incluir panel_ip y panel_port
            
        Returns:
            Dict con resultado de la operación
        """
        panel_ip = kwargs.get('panel_ip')
        panel_port = kwargs.get('panel_port', DEFAULT_PORT)
        metadata = kwargs.get('metadata', {})
        
        try:
            # Enviar paquete y recibir respuesta
            response = await self.connection_pool.send_data(
                ip=panel_ip,
                port=panel_port,
                data=packet
            )
            
            if response is None:
                raise Exception("No se recibió respuesta del panel")
            
            # Parsear respuesta
            parsed = PacketParser.parse_response(response)
            
            if parsed is None:
                raise Exception("Respuesta inválida del panel")
            
            # Crear resultado
            result = OperationResult(
                task_id=kwargs.get('task_id', ''),
                panel_ip=panel_ip,
                panel_port=panel_port,
                operation_type=operation_type,
                success=parsed['success'],
                timestamp=datetime.now(),
                response_data=response,
                error_message=None if parsed['success'] else f"Error code: {parsed['return_value']}",
                metadata=metadata
            )
            
            # Almacenar resultado
            await self.result_storage.store_result(result)
            
            return {
                'success': parsed['success'],
                'return_value': parsed['return_value'],
                'response_data': response,
                'parsed': parsed
            }
            
        except Exception as e:
            logger.error(f"Error en operación {operation_type}: {e}")
            
            # Crear resultado de error
            result = OperationResult(
                task_id=kwargs.get('task_id', ''),
                panel_ip=panel_ip,
                panel_port=panel_port,
                operation_type=operation_type,
                success=False,
                timestamp=datetime.now(),
                response_data=None,
                error_message=str(e),
                metadata=metadata
            )
            
            # Almacenar resultado
            await self.result_storage.store_result(result)
            
            raise
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Obtiene el resultado de una tarea.
        
        Args:
            task_id: ID de la tarea
            timeout: Timeout en segundos
            
        Returns:
            Dict con resultado de la tarea
        """
        return await self.task_queue.get_task_result(task_id, timeout=timeout)
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el estado de una tarea"""
        return await self.task_queue.get_task_status(task_id)
    
    async def get_panel_results(
        self,
        panel_ip: str,
        panel_port: int,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[OperationResult]:
        """Obtiene resultados de operaciones de un panel"""
        return await self.result_storage.get_panel_results(
            ip=panel_ip,
            port=panel_port,
            limit=limit,
            since=since
        )
    
    async def get_panel_success_rate(
        self,
        panel_ip: str,
        panel_port: int,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtiene la tasa de éxito de un panel"""
        return await self.result_storage.get_success_rate(
            ip=panel_ip,
            port=panel_port,
            since=since
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del servicio"""
        return await self.result_storage.get_statistics()
    
    async def close(self):
        """Cierra todas las conexiones y limpia recursos"""
        await self.connection_pool.close_all()
        logger.info("PanelProtocolService cerrado")

