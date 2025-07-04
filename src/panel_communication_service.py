#!/usr/bin/env python3
"""
Servicio de comunicación con la API REST de paneles
Diferenciado por protocolo:
- Protocolo antiguo: Servicio Java (puerto 5656)
- Protocolo nuevo: Servicio Node.js (puerto 3001)
"""

import requests
import json
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PanelCommunicationService:
    """Servicio para comunicación con paneles LED a través de API REST diferenciada por protocolo"""
    
    def __init__(self, 
                 java_api_url: str = "http://127.0.0.1:5656/api/v1/panels/sendMulti",
                 node_api_url: str = "http://127.0.0.1:3001/api/panels/send",
                 timeout: int = 30, retry_attempts: int = 3, retry_delay: int = 5):
        self.java_api_url = java_api_url
        self.node_api_url = node_api_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
    def _get_panel_protocol(self, panel_ip: str) -> str:
        """
        Obtener el protocolo de un panel desde la base de datos
        
        Args:
            panel_ip: IP del panel
            
        Returns:
            Protocolo del panel ('old' o 'new')
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models import Panel
            import config
            
            engine = create_engine(config.DB_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                panel = session.query(Panel).filter(Panel.ip == panel_ip).first()
                if panel:
                    return panel.protocol_version or 'old'  # Por defecto 'old' si es None
                else:
                    logger.warning(f"Panel {panel_ip} no encontrado en base de datos, usando protocolo antiguo")
                    return 'old'
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error obteniendo protocolo del panel {panel_ip}: {e}")
            return 'old'  # Por defecto protocolo antiguo
    
    def _send_to_java_service(self, panel_ip: str, texts: List[str], 
                             colors: List[int] = None, font_sizes: List[int] = None,
                             show_effects: List[int] = None) -> Dict:
        """
        Enviar mensaje al servicio Java (protocolo antiguo)
        """
        try:
            # Valores por defecto para protocolo antiguo
            if colors is None:
                colors = [1] * len(texts)  # Rojo por defecto
            if font_sizes is None:
                font_sizes = [16] * len(texts)  # Tamaño 16 por defecto
            if show_effects is None:
                show_effects = [0] * len(texts)  # Sin efecto por defecto
                
            # Preparar URL con parámetros de query
            url = f"{self.java_api_url}?ip={panel_ip}&itemNum={len(texts)}"
            
            # Preparar arrays como JSON en el body
            payload = {
                "texts": texts,
                "colors": colors,
                "fontSizes": font_sizes,
                "showEffects": show_effects
            }
            
            logger.info(f"Enviando a panel {panel_ip} (Java): {texts}")
            
            # Intentar envío con reintentos
            for attempt in range(self.retry_attempts):
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"✅ Texto enviado exitosamente a {panel_ip} (Java)")
                            return {
                                'success': True,
                                'message': 'Texto enviado exitosamente (Java)',
                                'panel_ip': panel_ip,
                                'protocol': 'old',
                                'texts': texts,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            logger.error(f"❌ Error en respuesta API Java: {result.get('message')}")
                            return {
                                'success': False,
                                'message': result.get('message', 'Error desconocido'),
                                'panel_ip': panel_ip,
                                'protocol': 'old',
                                'timestamp': datetime.now().isoformat()
                            }
                    else:
                        logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return {
                                'success': False,
                                'message': f'Error HTTP {response.status_code}',
                                'panel_ip': panel_ip,
                                'protocol': 'old',
                                'timestamp': datetime.now().isoformat()
                            }
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout en intento {attempt + 1} para {panel_ip} (Java)")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            'success': False,
                            'message': 'Timeout en la comunicación (Java)',
                            'panel_ip': panel_ip,
                            'protocol': 'old',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except requests.exceptions.ConnectionError:
                    logger.error(f"🔌 Error de conexión con API Java en {url}")
                    return {
                        'success': False,
                        'message': 'Error de conexión con la API Java de paneles',
                        'panel_ip': panel_ip,
                        'protocol': 'old',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error inesperado (Java): {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error inesperado: {str(e)}',
                        'panel_ip': panel_ip,
                        'protocol': 'old',
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error general (Java): {str(e)}")
            return {
                'success': False,
                'message': f'Error general: {str(e)}',
                'panel_ip': panel_ip,
                'protocol': 'old',
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_to_node_service(self, panel_ip: str, texts: List[str], 
                             colors: List[int] = None, font_sizes: List[int] = None,
                             show_effects: List[int] = None) -> Dict:
        """
        Enviar mensaje al servicio Node.js (protocolo nuevo)
        """
        try:
            # Valores por defecto para protocolo nuevo
            if colors is None:
                colors = [1] * len(texts)  # Rojo por defecto
            if font_sizes is None:
                font_sizes = [16] * len(texts)  # Tamaño 16 por defecto
            if show_effects is None:
                show_effects = [0] * len(texts)  # Sin efecto por defecto
                
            # Preparar payload para servicio Node.js
            payload = {
                "panel_ip": panel_ip,
                "messages": [
                    {
                        "text": text,
                        "color": color,
                        "font_size": font_size,
                        "effect": effect
                    }
                    for text, color, font_size, effect in zip(texts, colors, font_sizes, show_effects)
                ]
            }
            
            logger.info(f"Enviando a panel {panel_ip} (Node.js): {texts}")
            
            # Intentar envío con reintentos
            for attempt in range(self.retry_attempts):
                try:
                    response = requests.post(
                        self.node_api_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"✅ Texto enviado exitosamente a {panel_ip} (Node.js)")
                            return {
                                'success': True,
                                'message': 'Texto enviado exitosamente (Node.js)',
                                'panel_ip': panel_ip,
                                'protocol': 'new',
                                'texts': texts,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            logger.error(f"❌ Error en respuesta API Node.js: {result.get('message')}")
                            return {
                                'success': False,
                                'message': result.get('message', 'Error desconocido'),
                                'panel_ip': panel_ip,
                                'protocol': 'new',
                                'timestamp': datetime.now().isoformat()
                            }
                    else:
                        logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return {
                                'success': False,
                                'message': f'Error HTTP {response.status_code}',
                                'panel_ip': panel_ip,
                                'protocol': 'new',
                                'timestamp': datetime.now().isoformat()
                            }
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout en intento {attempt + 1} para {panel_ip} (Node.js)")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            'success': False,
                            'message': 'Timeout en la comunicación (Node.js)',
                            'panel_ip': panel_ip,
                            'protocol': 'new',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except requests.exceptions.ConnectionError:
                    logger.error(f"🔌 Error de conexión con API Node.js en {self.node_api_url}")
                    return {
                        'success': False,
                        'message': 'Error de conexión con la API Node.js de paneles',
                        'panel_ip': panel_ip,
                        'protocol': 'new',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error inesperado (Node.js): {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error inesperado: {str(e)}',
                        'panel_ip': panel_ip,
                        'protocol': 'new',
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error general (Node.js): {str(e)}")
            return {
                'success': False,
                'message': f'Error general: {str(e)}',
                'panel_ip': panel_ip,
                'protocol': 'new',
                'timestamp': datetime.now().isoformat()
            }
    
    def send_text_to_panel(self, panel_ip: str, texts: List[str], 
                          colors: List[int] = None, font_sizes: List[int] = None,
                          show_effects: List[int] = None) -> Dict:
        """
        Enviar texto a un panel específico según su protocolo
        
        Args:
            panel_ip: IP del panel destino
            texts: Lista de textos a enviar
            colors: Lista de colores (1-7)
            font_sizes: Lista de tamaños de fuente
            show_effects: Lista de efectos de visualización
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Determinar protocolo del panel
            protocol = self._get_panel_protocol(panel_ip)
            logger.info(f"Panel {panel_ip} usa protocolo: {protocol}")
            
            # Enviar según el protocolo
            if protocol == 'old':
                return self._send_to_java_service(panel_ip, texts, colors, font_sizes, show_effects)
            else:
                return self._send_to_node_service(panel_ip, texts, colors, font_sizes, show_effects)
                
        except Exception as e:
            logger.error(f"❌ Error general: {str(e)}")
            return {
                'success': False,
                'message': f'Error general: {str(e)}',
                'panel_ip': panel_ip,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_parking_status(self, panel_ip: str, parking_name: str, 
                           free_spaces: int, total_spaces: int,
                           language_code: str = 'va') -> Dict:
        """
        Enviar estado del parking a un panel
        
        Args:
            panel_ip: IP del panel
            parking_name: Nombre del parking
            free_spaces: Plazas libres
            total_spaces: Total de plazas
            language_code: Código de idioma (va, es, en, fr, de)
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Calcular porcentaje de ocupación
            occupied_spaces = total_spaces - free_spaces
            occupancy_percentage = (occupied_spaces / total_spaces) * 100 if total_spaces > 0 else 0
            
            # Determinar estado y color
            if occupancy_percentage < 50:
                status = "LLIURE" if language_code == 'va' else "LIBRE"
                color = 2  # Verde
            elif occupancy_percentage < 90:
                status = "DENS" if language_code == 'va' else "DENSO"
                color = 3  # Amarillo
            else:
                status = "COMPLET" if language_code == 'va' else "COMPLETO"
                color = 1  # Rojo
            
            # Preparar texto
            if language_code == 'va':
                text = f"{parking_name} {free_spaces} LLIURES"
            elif language_code == 'es':
                text = f"{parking_name} {free_spaces} LIBRES"
            elif language_code == 'en':
                text = f"{parking_name} {free_spaces} FREE"
            elif language_code == 'fr':
                text = f"{parking_name} {free_spaces} LIBRES"
            elif language_code == 'de':
                text = f"{parking_name} {free_spaces} FREI"
            else:
                text = f"{parking_name} {free_spaces} LLIURES"
            
            # Enviar texto
            return self.send_text_to_panel(
                panel_ip=panel_ip,
                texts=[text],
                colors=[color],
                font_sizes=[16],  # Tamaño 16
                show_effects=[1]  # Efecto centrado
            )
            
        except Exception as e:
            logger.error(f"❌ Error enviando estado de parking: {str(e)}")
            return {
                'success': False,
                'message': f'Error enviando estado: {str(e)}',
                'panel_ip': panel_ip,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_custom_text(self, panel_ip: str, text: str, 
                        color: int = 1, font_size: int = 16, 
                        effect: int = 1) -> Dict:
        """
        Enviar texto personalizado a un panel
        
        Args:
            panel_ip: IP del panel
            text: Texto a mostrar
            color: Color (1-7)
            font_size: Tamaño de fuente (siempre 16)
            effect: Efecto de visualización
            
        Returns:
            Dict con resultado de la operación
        """
        # Asegurar que el font_size sea siempre 16
        if font_size != 16:
            logger.info(f"Font size ajustado a 16 para panel {panel_ip} (requerimiento del sistema)")
            font_size = 16
        
        return self.send_text_to_panel(
            panel_ip=panel_ip,
            texts=[text],
            colors=[color],
            font_sizes=[font_size],
            show_effects=[effect]
        )
    
    def test_connection(self) -> Dict:
        """
        Probar conexión con las APIs de paneles
        
        Returns:
            Dict con resultado de la prueba
        """
        results = {}
        
        # Probar servicio Java
        try:
            response = requests.get(
                self.java_api_url.replace('/api/v1/panels/sendMulti', '/api/v1/panels/health'),
                timeout=5
            )
            results['java'] = {
                'success': response.status_code == 200,
                'message': 'Conexión exitosa' if response.status_code == 200 else 'Error de conexión',
                'status_code': response.status_code
            }
        except Exception as e:
            results['java'] = {
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            }
        
        # Probar servicio Node.js
        try:
            response = requests.get(
                self.node_api_url.replace('/api/panels/send', '/health'),
                timeout=5
            )
            results['nodejs'] = {
                'success': response.status_code == 200,
                'message': 'Conexión exitosa' if response.status_code == 200 else 'Error de conexión',
                'status_code': response.status_code
            }
        except Exception as e:
            results['nodejs'] = {
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            }
        
        return {
            'success': any(r['success'] for r in results.values()),
            'services': results,
            'timestamp': datetime.now().isoformat()
        }

# Función de utilidad para obtener el servicio
def get_panel_service() -> PanelCommunicationService:
    """Obtener instancia del servicio de paneles"""
    return PanelCommunicationService()

if __name__ == "__main__":
    # Ejemplo de uso
    service = PanelCommunicationService()
    
    # Probar conexión
    print("🔍 Probando conexión con APIs de paneles...")
    result = service.test_connection()
    print(f"Resultado: {result}")
    
    # Ejemplo de envío de texto
    print("\n📤 Enviando texto de prueba...")
    result = service.send_custom_text(
        panel_ip="172.20.4.52",
        text="EN PROVES",
        color=2,  # Verde
        font_size=16,
        effect=1  # Centrado
    )
    print(f"Resultado: {result}") 