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
# IMPORTANTE: Inicializar de forma lazy cuando se necesite, no al importar
# porque con gunicorn cada worker necesita su propio event loop
def _init_event_loop():
    """Inicializa el event loop asíncrono en un thread separado"""
    if server.loop is not None and server.loop.is_running():
        logger.debug("Event loop ya está inicializado y ejecutándose")
        return
    
    logger.info("Inicializando event loop asíncrono...")
    server.loop_thread = threading.Thread(target=server._run_event_loop, daemon=True)
    server.loop_thread.start()
    
    # Esperar a que el loop esté listo (máximo 10 segundos)
    timeout = 10
    elapsed = 0
    while server.loop is None and elapsed < timeout:
        time.sleep(0.1)
        elapsed += 0.1
    
    if server.loop is None:
        logger.error(f"Timeout inicializando event loop después de {timeout} segundos")
    else:
        logger.info("Event loop asíncrono inicializado para Panel Protocol Service")

# Exponer la aplicación Flask para gunicorn
# Gunicorn buscará la variable 'app' en este módulo
app = server.app

# Inicializar el event loop de forma lazy cuando se necesite
# Con gunicorn, cada worker necesita su propio event loop, así que lo inicializamos
# cuando se necesita en lugar de al importar el módulo
# Para desarrollo, inicializar al importar
if __name__ == '__main__':
    _init_event_loop()
else:
    # Con gunicorn, el event loop se inicializará de forma lazy cuando se necesite
    logger.info("Módulo cargado, el event loop se inicializará cuando se necesite")

if __name__ == '__main__':
    # Si se ejecuta directamente, usar Flask (para desarrollo)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

