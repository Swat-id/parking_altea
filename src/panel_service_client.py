#!/usr/bin/env python3
"""
Cliente Python para el servicio de paneles C#
Integra la comunicación con paneles usando el servicio .NET
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PanelStatus:
    """Estado de un panel"""
    ip: str
    name: str
    online: bool
    status: str
    last_communication: datetime
    response_time: float

@dataclass
class PanelResponse:
    """Respuesta del servicio de paneles"""
    success: bool
    message: str
    error_code: int
    response_time: float
    timestamp: datetime

@dataclass
class BroadcastResponse:
    """Respuesta de broadcast"""
    total_panels: int
    success_count: int
    failure_count: int
    results: List[PanelResponse]
    timestamp: datetime

class PanelServiceClient:
    """Cliente para el servicio de paneles C#"""
    
    def __init__(self, base_url: str = "http://localhost:5001", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configurar headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Realizar petición HTTP al servicio"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            return response
            
        except requests.exceptions.ConnectionError:
            logger.error(f"No se puede conectar al servicio de paneles en {url}")
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al conectar con el servicio de paneles en {url}")
            raise
        except Exception as e:
            logger.error(f"Error al conectar con el servicio de paneles: {e}")
            raise
    
    def is_service_online(self) -> bool:
        """Verificar si el servicio está online"""
        try:
            response = self._make_request('GET', '/health')
            return response.status_code == 200
        except:
            return False
    
    def get_all_panels_status(self) -> List[PanelStatus]:
        """Obtener estado de todos los paneles"""
        try:
            response = self._make_request('GET', '/api/panel/status')
            response.raise_for_status()
            
            data = response.json()
            panels = []
            
            for panel_data in data:
                panel = PanelStatus(
                    ip=panel_data.get('ip', ''),
                    name=panel_data.get('name', ''),
                    online=panel_data.get('online', False),
                    status=panel_data.get('status', ''),
                    last_communication=datetime.fromisoformat(panel_data.get('lastCommunication', datetime.now().isoformat())),
                    response_time=panel_data.get('responseTime', 0.0)
                )
                panels.append(panel)
            
            return panels
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de paneles: {e}")
            return []
    
    def get_panel_status(self, panel_ip: str) -> Optional[PanelStatus]:
        """Obtener estado de un panel específico"""
        try:
            response = self._make_request('GET', f'/api/panel/status/{panel_ip}')
            response.raise_for_status()
            
            data = response.json()
            
            return PanelStatus(
                ip=data.get('ip', ''),
                name=data.get('name', ''),
                online=data.get('online', False),
                status=data.get('status', ''),
                last_communication=datetime.fromisoformat(data.get('lastCommunication', datetime.now().isoformat())),
                response_time=data.get('responseTime', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del panel {panel_ip}: {e}")
            return None
    
    def send_message(self, panel_ip: str, message: str) -> PanelResponse:
        """Enviar mensaje a un panel"""
        try:
            data = {
                'panelIP': panel_ip,
                'message': message
            }
            
            response = self._make_request('POST', '/api/panel/send', data)
            response.raise_for_status()
            
            data = response.json()
            
            return PanelResponse(
                success=data.get('success', False),
                message=data.get('message', ''),
                error_code=data.get('errorCode', 0),
                response_time=data.get('responseTime', 0.0),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Error enviando mensaje al panel {panel_ip}: {e}")
            return PanelResponse(
                success=False,
                message=f"Error: {str(e)}",
                error_code=-1,
                response_time=0.0,
                timestamp=datetime.now()
            )
    
    def send_occupancy(self, panel_ip: str, current: int, total: int, status: str) -> PanelResponse:
        """Enviar información de ocupación a un panel"""
        try:
            data = {
                'panelIP': panel_ip,
                'current': current,
                'total': total,
                'status': status
            }
            
            response = self._make_request('POST', '/api/panel/occupancy', data)
            response.raise_for_status()
            
            data = response.json()
            
            return PanelResponse(
                success=data.get('success', False),
                message=data.get('message', ''),
                error_code=data.get('errorCode', 0),
                response_time=data.get('responseTime', 0.0),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Error enviando ocupación al panel {panel_ip}: {e}")
            return PanelResponse(
                success=False,
                message=f"Error: {str(e)}",
                error_code=-1,
                response_time=0.0,
                timestamp=datetime.now()
            )
    
    def broadcast_message(self, message: str, panel_ips: Optional[List[str]] = None) -> BroadcastResponse:
        """Enviar mensaje a todos los paneles o a una lista específica"""
        try:
            data = {
                'message': message,
                'sendToAll': panel_ips is None,
                'panelIPs': panel_ips or []
            }
            
            response = self._make_request('POST', '/api/panel/broadcast', data)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for result_data in data.get('results', []):
                result = PanelResponse(
                    success=result_data.get('success', False),
                    message=result_data.get('message', ''),
                    error_code=result_data.get('errorCode', 0),
                    response_time=result_data.get('responseTime', 0.0),
                    timestamp=datetime.fromisoformat(result_data.get('timestamp', datetime.now().isoformat()))
                )
                results.append(result)
            
            return BroadcastResponse(
                total_panels=data.get('totalPanels', 0),
                success_count=data.get('successCount', 0),
                failure_count=data.get('failureCount', 0),
                results=results,
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Error en broadcast: {e}")
            return BroadcastResponse(
                total_panels=0,
                success_count=0,
                failure_count=1,
                results=[],
                timestamp=datetime.now()
            )
    
    def test_panel(self, panel_ip: str) -> PanelResponse:
        """Testear un panel"""
        try:
            response = self._make_request('POST', f'/api/panel/test/{panel_ip}')
            response.raise_for_status()
            
            data = response.json()
            
            return PanelResponse(
                success=data.get('success', False),
                message=data.get('message', ''),
                error_code=data.get('errorCode', 0),
                response_time=data.get('responseTime', 0.0),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Error testeando panel {panel_ip}: {e}")
            return PanelResponse(
                success=False,
                message=f"Error: {str(e)}",
                error_code=-1,
                response_time=0.0,
                timestamp=datetime.now()
            )
    
    def send_static_text(self, panel_ip: str, text: str, x: int = 0, y: int = 0, width: int = 64, height: int = 32) -> PanelResponse:
        """Enviar texto estático a un panel"""
        try:
            data = {
                'panelIP': panel_ip,
                'text': text,
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }
            
            response = self._make_request('POST', '/api/panel/static', data)
            response.raise_for_status()
            
            data = response.json()
            
            return PanelResponse(
                success=data.get('success', False),
                message=data.get('message', ''),
                error_code=data.get('errorCode', 0),
                response_time=data.get('responseTime', 0.0),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Error enviando texto estático al panel {panel_ip}: {e}")
            return PanelResponse(
                success=False,
                message=f"Error: {str(e)}",
                error_code=-1,
                response_time=0.0,
                timestamp=datetime.now()
            )

# Función de conveniencia para usar el cliente
def get_panel_client(base_url: str = "http://localhost:5001") -> PanelServiceClient:
    """Obtener instancia del cliente de paneles"""
    return PanelServiceClient(base_url)

# Función para reemplazar la función send_to_panel existente
def send_to_panel_via_service(panel_ip: str, text: str, service_url: str = "http://localhost:5001") -> bool:
    """Enviar mensaje a panel usando el servicio C#"""
    try:
        client = PanelServiceClient(service_url)
        response = client.send_message(panel_ip, text)
        return response.success
    except Exception as e:
        logger.error(f"Error enviando mensaje a panel {panel_ip} via servicio: {e}")
        return False 