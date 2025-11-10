"""
Ejemplo de uso del PanelProtocolService
Demuestra cómo usar el servicio para enviar múltiples operaciones en paralelo
"""

import asyncio
import logging
from panel_protocol_service import PanelProtocolService
from constants import Color, FontSize, Effect, Alignment

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def ejemplo_uso_basico():
    """Ejemplo básico de uso del servicio"""
    
    # Crear servicio
    service = PanelProtocolService(
        max_concurrent_tasks=10,
        max_connections_per_panel=5
    )
    
    try:
        # Ejemplo 1: Enviar texto a un panel (sin esperar respuesta)
        task_id1 = await service.send_text(
            panel_ip="192.168.1.221",
            panel_port=5200,
            window_id=0,
            text="PARKING LLIURE",
            color=Color.GREEN,
            font_size=FontSize.SIZE_16,
            effect=Effect.SCROLL_LEFT,
            wait_for_response=False  # No espera, retorna inmediatamente
        )
        logger.info(f"Tarea 1 enviada: {task_id1}")
        
        # Ejemplo 2: Crear ventana (sin esperar respuesta)
        task_id2 = await service.create_window(
            panel_ip="192.168.1.221",
            panel_port=5200,
            windows=[(0, 0, 64, 8)],  # Ventana de 64x8 en (0,0)
            wait_for_response=False
        )
        logger.info(f"Tarea 2 enviada: {task_id2}")
        
        # Ejemplo 3: Enviar texto a otro panel en paralelo
        task_id3 = await service.send_text(
            panel_ip="192.168.1.222",
            panel_port=5200,
            window_id=0,
            text="OCUPAT",
            color=Color.RED,
            font_size=FontSize.SIZE_24,
            wait_for_response=False
        )
        logger.info(f"Tarea 3 enviada: {task_id3}")
        
        # Esperar un poco para que las tareas se ejecuten
        await asyncio.sleep(2)
        
        # Verificar resultados
        result1 = await service.get_task_result(task_id1)
        logger.info(f"Resultado tarea 1: {result1}")
        
        result2 = await service.get_task_result(task_id2)
        logger.info(f"Resultado tarea 2: {result2}")
        
        result3 = await service.get_task_result(task_id3)
        logger.info(f"Resultado tarea 3: {result3}")
        
        # Obtener estadísticas
        stats = await service.get_statistics()
        logger.info(f"Estadísticas: {stats}")
        
    finally:
        # Cerrar servicio
        await service.close()


async def ejemplo_multiple_paneles():
    """Ejemplo de envío a múltiples paneles en paralelo"""
    
    service = PanelProtocolService(max_concurrent_tasks=20)
    
    try:
        # Lista de paneles
        panels = [
            ("192.168.1.221", 5200),
            ("192.168.1.222", 5200),
            ("192.168.1.223", 5200),
            ("192.168.1.224", 5200),
        ]
        
        # Enviar texto a todos los paneles en paralelo
        task_ids = []
        for ip, port in panels:
            task_id = await service.send_text(
                panel_ip=ip,
                panel_port=port,
                window_id=0,
                text="TEST",
                color=Color.YELLOW,
                font_size=FontSize.SIZE_16,
                wait_for_response=False
            )
            task_ids.append((ip, port, task_id))
            logger.info(f"Enviado a {ip}:{port} - Tarea: {task_id}")
        
        # Esperar a que todas las tareas se completen
        await asyncio.sleep(3)
        
        # Verificar resultados
        for ip, port, task_id in task_ids:
            try:
                result = await service.get_task_result(task_id, timeout=5)
                logger.info(f"Panel {ip}:{port} - Éxito: {result['success']}")
            except Exception as e:
                logger.error(f"Panel {ip}:{port} - Error: {e}")
        
        # Obtener tasa de éxito por panel
        for ip, port in panels:
            success_rate = await service.get_panel_success_rate(ip, port)
            logger.info(f"Panel {ip}:{port} - Tasa de éxito: {success_rate['success_rate']}%")
        
    finally:
        await service.close()


async def ejemplo_con_espera():
    """Ejemplo usando wait_for_response=True"""
    
    service = PanelProtocolService()
    
    try:
        # Enviar texto esperando respuesta
        task_id = await service.send_text(
            panel_ip="192.168.1.221",
            panel_port=5200,
            window_id=0,
            text="ESPERANDO RESPUESTA",
            color=Color.BLUE,
            font_size=FontSize.SIZE_16,
            wait_for_response=True  # Espera la respuesta antes de retornar
        )
        
        # La tarea ya está completada cuando retorna
        logger.info(f"Tarea completada: {task_id}")
        
        # Verificar resultado
        result = await service.get_task_result(task_id)
        logger.info(f"Resultado: {result}")
        
    finally:
        await service.close()


if __name__ == "__main__":
    # Ejecutar ejemplos
    print("Ejemplo 1: Uso básico")
    asyncio.run(ejemplo_uso_basico())
    
    print("\nEjemplo 2: Múltiples paneles")
    asyncio.run(ejemplo_multiple_paneles())
    
    print("\nEjemplo 3: Con espera de respuesta")
    asyncio.run(ejemplo_con_espera())

