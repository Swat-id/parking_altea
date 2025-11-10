"""
Cliente HTTP para el Panel Protocol Service
Permite al backend comunicarse con el servicio en puerto 7110
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PanelProtocolClient:
    """
    Cliente HTTP para comunicarse con el Panel Protocol Service.
    Simplifica el uso del servicio desde el backend.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:7110",
        timeout: int = 30,
        token: Optional[str] = None
    ):
        """
        Inicializa el cliente.
        
        Args:
            base_url: URL base del servicio (default: http://localhost:7110)
            timeout: Timeout para peticiones HTTP (segundos)
            token: Token JWT para autenticación (opcional, usa el mismo sistema del backend)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.token = token
        self.session = requests.Session()
        
        # Configurar headers
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
        
        logger.info(f"PanelProtocolClient inicializado: {base_url}")
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Autentica un usuario y obtiene un token JWT.
        Usa el mismo sistema de autenticación del backend.
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Dict con token y información del usuario
            
        Raises:
            requests.RequestException: Si hay error en la petición
        """
        data = {
            'email': email,
            'password': password
        }
        
        response = self._request('POST', '/api/v1/auth/login', data=data)
        
        # Guardar token automáticamente
        if response.get('success') and response.get('token'):
            self.token = response['token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        
        return response
    
    def get_current_user(self) -> Dict[str, Any]:
        """Obtiene información del usuario autenticado"""
        return self._request('GET', '/api/v1/auth/me')
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición HTTP al servicio.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint relativo (ej: /api/v1/panels/send-text)
            data: Datos para el body (se serializa a JSON)
            params: Parámetros de query string
            
        Returns:
            Dict con la respuesta
            
        Raises:
            requests.RequestException: Si hay error en la petición
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición {method} {url}: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del servicio"""
        return self._request('GET', '/health')
    
    def create_window(
        self,
        panel_ip: str,
        windows: List[Tuple[int, int, int, int]],
        panel_port: int = 5200,
        card_id: int = 0xFF,
        wait_for_response: bool = False
    ) -> str:
        """
        Crea ventanas en un panel.
        
        Args:
            panel_ip: IP del panel
            windows: Lista de tuplas (x, y, width, height)
            panel_port: Puerto del panel (default: 5200)
            card_id: ID de la tarjeta (default: 0xFF = broadcast)
            wait_for_response: Si True, espera la respuesta
            
        Returns:
            str: ID de la tarea
        """
        data = {
            'panel_ip': panel_ip,
            'panel_port': panel_port,
            'windows': [
                {'x': x, 'y': y, 'width': w, 'height': h}
                for x, y, w, h in windows
            ],
            'card_id': card_id,
            'wait_for_response': wait_for_response
        }
        
        response = self._request('POST', '/api/v1/panels/create-window', data=data)
        return response['task_id']
    
    def send_text(
        self,
        panel_ip: str,
        window_id: int,
        text: str,
        color: int = 2,  # Verde por defecto
        font_size: int = 2,  # 16px por defecto
        effect: int = 0,  # DRAW (fijo) por defecto
        alignment: int = 5,  # CENTER_CENTER por defecto
        speed: int = 0,
        stay_time: int = 3,
        panel_port: int = 5200,
        card_id: int = 0xFF,
        wait_for_response: bool = False
    ) -> str:
        """
        Envía texto a un panel.
        
        Args:
            panel_ip: IP del panel
            window_id: ID de la ventana (0, 1, ...)
            text: Texto a enviar
            color: Color (1=Rojo, 2=Verde, 3=Amarillo, etc.)
            font_size: Tamaño de fuente (0=8px, 1=12px, 2=16px, etc.)
            effect: Efecto (0=DRAW, 11=SCROLL_LEFT, 12=SCROLL_RIGHT, etc.)
            alignment: Alineación (0=LEFT_TOP, 5=CENTER_CENTER, etc.)
            speed: Velocidad del efecto (0=más rápido)
            stay_time: Tiempo de espera en segundos
            panel_port: Puerto del panel (default: 5200)
            card_id: ID de la tarjeta (default: 0xFF)
            wait_for_response: Si True, espera la respuesta
            
        Returns:
            str: ID de la tarea
        """
        data = {
            'panel_ip': panel_ip,
            'panel_port': panel_port,
            'window_id': window_id,
            'text': text,
            'color': color,
            'font_size': font_size,
            'effect': effect,
            'alignment': alignment,
            'speed': speed,
            'stay_time': stay_time,
            'card_id': card_id,
            'wait_for_response': wait_for_response
        }
        
        response = self._request('POST', '/api/v1/panels/send-text', data=data)
        return response['task_id']
    
    def send_image(
        self,
        panel_ip: str,
        window_id: int,
        filename: str,
        panel_port: int = 5200,
        draw_mode: int = 0,
        speed: int = 1,
        stay_time: int = 3,
        x: int = 0,
        y: int = 0,
        card_id: int = 0xFF,
        wait_for_response: bool = False
    ) -> str:
        """
        Envía una imagen a un panel.
        
        Args:
            panel_ip: IP del panel
            window_id: ID de la ventana
            filename: Nombre del archivo (ej: "test.gif")
            panel_port: Puerto del panel (default: 5200)
            draw_mode: Modo de mostrar (0=Draw)
            speed: Velocidad
            stay_time: Tiempo de espera en segundos
            x: Coordenada X
            y: Coordenada Y
            card_id: ID de la tarjeta
            wait_for_response: Si True, espera la respuesta
            
        Returns:
            str: ID de la tarea
        """
        data = {
            'panel_ip': panel_ip,
            'panel_port': panel_port,
            'window_id': window_id,
            'filename': filename,
            'draw_mode': draw_mode,
            'speed': speed,
            'stay_time': stay_time,
            'x': x,
            'y': y,
            'card_id': card_id,
            'wait_for_response': wait_for_response
        }
        
        response = self._request('POST', '/api/v1/panels/send-image', data=data)
        return response['task_id']
    
    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Obtiene el resultado de una tarea.
        
        Args:
            task_id: ID de la tarea
            timeout: Timeout en segundos (opcional)
            
        Returns:
            Dict con el resultado
        """
        params = {}
        if timeout:
            params['timeout'] = timeout
        
        return self._request('GET', f'/api/v1/tasks/{task_id}', params=params)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el estado de una tarea"""
        return self._request('GET', f'/api/v1/tasks/{task_id}/status')
    
    def get_panel_results(
        self,
        panel_ip: str,
        panel_port: int = 5200,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene resultados de operaciones de un panel.
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            limit: Límite de resultados
            since: Solo resultados desde esta fecha
            
        Returns:
            Lista de resultados
        """
        params = {'port': panel_port}
        if limit:
            params['limit'] = limit
        if since:
            params['since'] = since.isoformat()
        
        response = self._request('GET', f'/api/v1/panels/{panel_ip}/results', params=params)
        return response['results']
    
    def get_panel_statistics(
        self,
        panel_ip: str,
        panel_port: int = 5200,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un panel.
        
        Args:
            panel_ip: IP del panel
            panel_port: Puerto del panel
            since: Solo considerar resultados desde esta fecha
            
        Returns:
            Dict con estadísticas
        """
        params = {'port': panel_port}
        if since:
            params['since'] = since.isoformat()
        
        response = self._request('GET', f'/api/v1/panels/{panel_ip}/statistics', params=params)
        return response['statistics']
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del servicio"""
        response = self._request('GET', '/api/v1/statistics')
        return response['statistics']


# Función helper para obtener instancia del cliente
_client_instance: Optional[PanelProtocolClient] = None


def get_panel_protocol_client(
    base_url: Optional[str] = None,
    token: Optional[str] = None
) -> PanelProtocolClient:
    """
    Obtiene una instancia singleton del cliente.
    
    Args:
        base_url: URL base del servicio (opcional, usa default si no se proporciona)
        token: Token JWT para autenticación (opcional)
        
    Returns:
        Instancia de PanelProtocolClient
    """
    global _client_instance
    
    if _client_instance is None or base_url is not None or token is not None:
        from config import PANEL_PROTOCOL_SERVICE_PORT
        url = base_url or f"http://localhost:{PANEL_PROTOCOL_SERVICE_PORT}"
        _client_instance = PanelProtocolClient(base_url=url, token=token)
    
    return _client_instance

