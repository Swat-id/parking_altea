import requests
import subprocess
import platform
from config import DB_URL, CAMERA_PORT, API_PORT, LOG_RETENTION_DAYS

# Ejemplo usando Rotuloselect API (ajustar según zip de ejemplo)
API_ENDPOINT_TEMPLATE = 'http://{ip}/update'


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
        print(f"Error haciendo ping a {panel_ip}: {e}")
        return False


def send_to_panel(panel_ip: str, text: str) -> bool:
    """
    Enviar mensaje a un panel via HTTP
    """
    try:
        payload = {'message': text}
        r = requests.post(API_ENDPOINT_TEMPLATE.format(ip=panel_ip), json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"Error enviando mensaje a panel {panel_ip}: {e}")
        return False


def broadcast(parking, message: str):
    """
    Enviar mensaje a todos los paneles de un parking
    """
    for panel in parking.panels:
        send_to_panel(panel.ip, message)