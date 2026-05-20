"""
Descubrimiento de paneles CPower via UDP

El SDK Java descubre paneles enviando "CPower~?\0" por UDP al puerto 57274.
Los paneles responden con su información incluyendo el Device ID.
"""

import socket
import logging
from typing import Optional, Dict, Any
from .constants import CPOWER_DISCOVERY_PORT, CPOWER_DISCOVERY_REQUEST

logger = logging.getLogger(__name__)


def discover_panel_device_id(panel_ip: str, timeout: float = 5.0) -> Optional[str]:
    """
    Descubre el Device ID de un panel CPower enviando una solicitud UDP.
    
    Args:
        panel_ip: IP del panel
        timeout: Timeout en segundos
        
    Returns:
        str: Device ID del panel (ej: "00606ed81e7e") o None si no se puede descubrir
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        logger.info(f"Enviando solicitud de descubrimiento a {panel_ip}:{CPOWER_DISCOVERY_PORT}")
        sock.sendto(CPOWER_DISCOVERY_REQUEST, (panel_ip, CPOWER_DISCOVERY_PORT))
        
        data, addr = sock.recvfrom(1024)
        sock.close()
        
        logger.debug(f"Respuesta de descubrimiento recibida: {data}")
        
        device_id = parse_discovery_response(data)
        if device_id:
            logger.info(f"Device ID descubierto para {panel_ip}: {device_id}")
        
        return device_id
        
    except socket.timeout:
        logger.warning(f"Timeout descubriendo panel {panel_ip}")
        return None
    except Exception as e:
        logger.error(f"Error descubriendo panel {panel_ip}: {e}")
        return None


def parse_discovery_response(data: bytes) -> Optional[str]:
    """
    Parsea la respuesta de descubrimiento para extraer el Device ID.
    
    Formato de respuesta: CP~:IP\tDeviceID\t...
    Ejemplo: CP~:172.20.4.52\t00606ed81e7e\tCPB4041061\t...
    
    Args:
        data: Bytes de la respuesta
        
    Returns:
        str: Device ID o None si no se puede parsear
    """
    try:
        response_str = data.decode('ascii', errors='ignore')
        
        if not response_str.startswith('CP~:'):
            logger.warning(f"Respuesta de descubrimiento no válida: {response_str[:50]}")
            return None
        
        parts = response_str.split('\t')
        if len(parts) >= 2:
            device_id = parts[1]
            if len(device_id) == 12 and all(c in '0123456789abcdef' for c in device_id.lower()):
                return device_id.lower()
            
        logger.warning(f"No se pudo extraer Device ID de: {response_str[:100]}")
        return None
        
    except Exception as e:
        logger.error(f"Error parseando respuesta de descubrimiento: {e}")
        return None


def discover_all_panels(network_prefix: str = "172.20", timeout: float = 2.0) -> Dict[str, str]:
    """
    Descubre todos los paneles en una red enviando solicitudes UDP.
    
    Args:
        network_prefix: Prefijo de red (ej: "172.20")
        timeout: Timeout por panel en segundos
        
    Returns:
        Dict[str, str]: Diccionario {ip: device_id}
    """
    import concurrent.futures
    
    discovered = {}
    
    def discover_single(ip: str) -> tuple:
        device_id = discover_panel_device_id(ip, timeout)
        return (ip, device_id)
    
    logger.warning("discover_all_panels no implementado completamente - usar discover_panel_device_id directamente")
    
    return discovered


async def discover_panel_device_id_async(panel_ip: str, timeout: float = 5.0) -> Optional[str]:
    """
    Versión asíncrona de discover_panel_device_id.
    
    Args:
        panel_ip: IP del panel
        timeout: Timeout en segundos
        
    Returns:
        str: Device ID del panel o None si no se puede descubrir
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, discover_panel_device_id, panel_ip, timeout)
