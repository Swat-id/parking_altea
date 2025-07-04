import requests
import subprocess
import platform
import logging
from typing import Dict, List
from config import DB_URL, CAMERA_PORT, API_PORT, LOG_RETENTION_DAYS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nueva API unificada de paneles
PANEL_API_URL = "http://127.0.0.1:8888/api/v1/panels/send"


def ping_panel(panel_ip: str) -> bool:
    """
    Hacer ping real a un panel usando ICMP
    """
    try:
        # Determinar el comando de ping según el sistema operativo
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", panel_ip]
        else:
            # Usar rutas completas para ping en sistemas Unix
            ping_paths = ["/bin/ping", "/usr/bin/ping", "/sbin/ping"]
            ping_cmd = None
            
            for path in ping_paths:
                try:
                    import os
                    if os.path.exists(path):
                        ping_cmd = path
                        break
                except:
                    continue
            
            if not ping_cmd:
                # Si no encontramos ping, intentar con el PATH
                ping_cmd = "ping"
            
            cmd = [ping_cmd, "-c", "1", "-W", "1", panel_ip]
        
        # Ejecutar ping
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        # Verificar si el ping fue exitoso
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Error haciendo ping a {panel_ip}: {e}")
        return False


def send_to_panels(panels: List[Dict], text: str, color: int = 1, font_size: int = 2, effect: int = 2) -> Dict:
    """
    Enviar mensaje a múltiples paneles usando la API unificada
    
    Args:
        panels: Lista de diccionarios con información de paneles
        text: Texto a enviar
        color: Color del texto
        font_size: Tamaño de fuente
        effect: Efecto (2=fijo, 12=scroll)
        
    Returns:
        Diccionario con resultados del envío
    """
    try:
        # Preparar payload para múltiples paneles
        panel_configs = []
        for panel in panels:
            panel_config = {
                "ip": panel.get('ip'),
                "port": 5200,
                "protocol": panel.get('protocol', 'old'),
                "windows": [
                    {
                        "id": 0,
                        "text": text,
                        "color": color,
                        "fontSize": font_size,
                        "speed": 100,
                        "effect": effect,
                        "stayTime": 50,
                        "alignmentH": 1,
                        "alignmentV": 1
                    }
                ]
            }
            panel_configs.append(panel_config)
        
        payload = {"panels": panel_configs}
        
        logger.info(f"Enviando mensaje a {len(panels)} paneles: {text}")
        
        response = requests.post(
            PANEL_API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Mensaje enviado exitosamente a {len(panels)} paneles")
                return {
                    'success': True,
                    'message': 'Mensaje enviado exitosamente',
                    'panels_affected': len(panels)
                }
            else:
                logger.error(f"❌ Error en respuesta API: {result.get('message')}")
                return {
                    'success': False,
                    'message': result.get('message', 'Error desconocido'),
                    'panels_affected': 0
                }
        else:
            logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
            return {
                'success': False,
                'message': f'Error HTTP {response.status_code}',
                'panels_affected': 0
            }
            
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 Error de conexión con API de paneles")
        return {
            'success': False,
            'message': 'Error de conexión con la API de paneles',
            'panels_affected': 0
        }
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a paneles: {e}")
        return {
            'success': False,
            'message': f'Error inesperado: {str(e)}',
            'panels_affected': 0
        }


def broadcast(parking, message: str, color: int = 1, font_size: int = 2, effect: int = 2):  # Fijo por defecto (valor 2) - CORREGIDO
    """
    Enviar mensaje a todos los paneles de un parking usando la nueva API
    """
    try:
        # Preparar lista de paneles
        panels = []
        for panel in parking.panels:
            panels.append({
                'ip': panel.ip,
                'protocol': getattr(panel, 'protocol_version', 'old')
            })
        
        # Enviar usando la nueva función
        result = send_to_panels(panels, message, color, font_size, effect)
        
        if result['success']:
            logger.info(f"✅ Broadcast exitoso a {result['panels_affected']} paneles del parking {parking.name}")
        else:
            logger.error(f"❌ Error en broadcast: {result['message']}")
            
    except Exception as e:
        logger.error(f"❌ Error en broadcast para parking {parking.name}: {e}")


def test_panel_api_connection() -> bool:
    """
    Probar la conexión con la API de paneles
    
    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        health_url = PANEL_API_URL.replace('/api/v1/panels/send', '/health')
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Conexión exitosa con API de paneles: {result.get('status', 'unknown')}")
            return True
        else:
            logger.error(f"❌ Error HTTP {response.status_code} al probar API de paneles")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("🔌 No se puede conectar con la API de paneles")
        return False
    except Exception as e:
        logger.error(f"❌ Error probando conexión con API de paneles: {e}")
        return False