"""
Servicio principal para el Panel Protocol Service
Expone la aplicación Flask para ser ejecutada con gunicorn
Similar a camera_server.py
"""

import logging
import os
import sys
import threading
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio src al path
sys.path.insert(0, os.path.dirname(__file__))

from panel_protocol.api_server import PanelProtocolAPIServer
from config import PANEL_PROTOCOL_SERVICE_PORT

# Crear instancia del servidor
# El puerto se configura en gunicorn, pero lo necesitamos para inicializar
server = PanelProtocolAPIServer(port=PANEL_PROTOCOL_SERVICE_PORT)

# Inicializar el event loop asíncrono en un thread separado
def _init_event_loop():
    """Inicializa el event loop asíncrono en un thread separado"""
    server.loop_thread = threading.Thread(target=server._run_event_loop, daemon=True)
    server.loop_thread.start()
    
    # Esperar a que el loop esté listo
    while server.loop is None:
        time.sleep(0.1)
    
    logger.info("Event loop asíncrono inicializado para Panel Protocol Service")

# Inicializar el event loop al importar el módulo
_init_event_loop()

# Exponer la aplicación Flask para gunicorn
# Gunicorn buscará la variable 'app' en este módulo
app = server.app

if __name__ == '__main__':
    # Si se ejecuta directamente, usar Flask (para desarrollo)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

