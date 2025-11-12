#!/usr/bin/env python3
"""
Script de prueba para enviar mensajes específicos a un panel Tipo 3
Envía "90" a ventana 0 y "02" a ventana 1
"""

import sys
import os
import asyncio
import logging

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from panel_protocol.panel_protocol_service import PanelProtocolService
from panel_protocol.constants import Color

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_panel_update(panel_ip: str, panel_port: int = 5200):
    """
    Envía mensajes de prueba a un panel
    
    Args:
        panel_ip: IP del panel
        panel_port: Puerto del panel (default: 5200)
    """
    logger.info(f"=== PRUEBA DE ACTUALIZACIÓN DE PANEL ===")
    logger.info(f"Panel: {panel_ip}:{panel_port}")
    logger.info(f"Ventana 0: '90'")
    logger.info(f"Ventana 1: '02'")
    logger.info("=" * 50)
    
    # Crear servicio de protocolo
    protocol_service = PanelProtocolService(
        max_concurrent_tasks=10,
        max_connections_per_panel=5,
        connection_timeout=5.0,
        read_timeout=15.0
    )
    
    try:
        # Enviar a ventana 0: "90"
        logger.info("\n📤 Enviando '90' a ventana 0...")
        task_id_0 = await protocol_service.send_text_v4(
            panel_ip=panel_ip,
            panel_port=panel_port,
            window_id=0,
            text="90",
            color=Color.GREEN,
            font_size=2,  # 16px
            alignment=5,  # CENTER_CENTER
            effect=0,  # STATIC
            speed=0x03,
            wait_time=0x0003,
            request_confirmation=True,
            wait_for_response=False
        )
        logger.info(f"✅ Tarea creada para ventana 0: {task_id_0}")
        
        # Esperar resultado de ventana 0
        logger.info("⏳ Esperando respuesta de ventana 0...")
        result_0 = await protocol_service.get_task_result(task_id_0, timeout=15.0)
        logger.info(f"📥 Resultado ventana 0: {result_0}")
        
        if result_0 and result_0.get('success'):
            logger.info("✅ Ventana 0 actualizada exitosamente")
        else:
            logger.error(f"❌ Error en ventana 0: {result_0}")
        
        # Pequeña pausa entre envíos
        await asyncio.sleep(0.5)
        
        # Enviar a ventana 1: "02"
        logger.info("\n📤 Enviando '02' a ventana 1...")
        task_id_1 = await protocol_service.send_text_v4(
            panel_ip=panel_ip,
            panel_port=panel_port,
            window_id=1,
            text="02",
            color=Color.GREEN,
            font_size=2,  # 16px
            alignment=5,  # CENTER_CENTER
            effect=0,  # STATIC
            speed=0x03,
            wait_time=0x0003,
            request_confirmation=True,
            wait_for_response=False
        )
        logger.info(f"✅ Tarea creada para ventana 1: {task_id_1}")
        
        # Esperar resultado de ventana 1
        logger.info("⏳ Esperando respuesta de ventana 1...")
        result_1 = await protocol_service.get_task_result(task_id_1, timeout=15.0)
        logger.info(f"📥 Resultado ventana 1: {result_1}")
        
        if result_1 and result_1.get('success'):
            logger.info("✅ Ventana 1 actualizada exitosamente")
        else:
            logger.error(f"❌ Error en ventana 1: {result_1}")
        
        logger.info("\n" + "=" * 50)
        logger.info("=== PRUEBA COMPLETADA ===")
        
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        await protocol_service.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Prueba de actualización de panel')
    parser.add_argument('panel_ip', help='IP del panel')
    parser.add_argument('--port', type=int, default=5200, help='Puerto del panel (default: 5200)')
    
    args = parser.parse_args()
    
    # Ejecutar prueba
    asyncio.run(test_panel_update(args.panel_ip, args.port))

