import requests
from config import {}

# Ejemplo usando Rotuloselect API (ajustar según zip de ejemplo)
API_ENDPOINT = 'http://{ip}/update'


def send_to_panel(panel_ip: str, text: str) -> bool:
    try:
        payload = {{'message': text}}
        r = requests.post(API_ENDPOINT.format(ip=panel_ip), json=payload, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def broadcast(parking, message: str):
    for panel in parking.panels:
        send_to_panel(panel.ip, message)