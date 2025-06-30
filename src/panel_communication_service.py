#!/usr/bin/env python3
"""
Servicio de comunicación con la API REST de paneles
Puerto 5656 - sendMulti endpoint
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
    """Servicio para comunicación con paneles LED a través de API REST"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:5656/sendMulti", 
                 timeout: int = 30, retry_attempts: int = 3, retry_delay: int = 5):
        self.api_url = api_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
    def send_text_to_panel(self, panel_ip: str, texts: List[str], 
                          colors: List[int] = None, font_sizes: List[int] = None,
                          show_effects: List[int] = None) -> Dict:
        """
        Enviar texto a un panel específico
        
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
            # Valores por defecto
            if colors is None:
                colors = [1] * len(texts)  # Rojo por defecto
            if font_sizes is None:
                font_sizes = [2] * len(texts)  # Tamaño 2 por defecto
            if show_effects is None:
                show_effects = [0] * len(texts)  # Sin efecto por defecto
                
            # Preparar payload
            payload = {
                "ip": panel_ip,
                "itemNum": len(texts),
                "texts": texts,
                "colors": colors,
                "fontSizes": font_sizes,
                "showEffects": show_effects
            }
            
            logger.info(f"Enviando a panel {panel_ip}: {texts}")
            
            # Intentar envío con reintentos
            for attempt in range(self.retry_attempts):
                try:
                    response = requests.post(
                        self.api_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"✅ Texto enviado exitosamente a {panel_ip}")
                            return {
                                'success': True,
                                'message': 'Texto enviado exitosamente',
                                'panel_ip': panel_ip,
                                'texts': texts,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            logger.error(f"❌ Error en respuesta API: {result.get('message')}")
                            return {
                                'success': False,
                                'message': result.get('message', 'Error desconocido'),
                                'panel_ip': panel_ip,
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
                                'timestamp': datetime.now().isoformat()
                            }
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout en intento {attempt + 1} para {panel_ip}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            'success': False,
                            'message': 'Timeout en la comunicación',
                            'panel_ip': panel_ip,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except requests.exceptions.ConnectionError:
                    logger.error(f"🔌 Error de conexión con API en {self.api_url}")
                    return {
                        'success': False,
                        'message': 'Error de conexión con la API de paneles',
                        'panel_ip': panel_ip,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error inesperado: {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error inesperado: {str(e)}',
                        'panel_ip': panel_ip,
                        'timestamp': datetime.now().isoformat()
                    }
                    
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
                font_sizes=[2],  # Tamaño 2
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
                        color: int = 1, font_size: int = 2, 
                        effect: int = 1) -> Dict:
        """
        Enviar texto personalizado a un panel
        
        Args:
            panel_ip: IP del panel
            text: Texto a mostrar
            color: Color (1-7)
            font_size: Tamaño de fuente
            effect: Efecto de visualización
            
        Returns:
            Dict con resultado de la operación
        """
        return self.send_text_to_panel(
            panel_ip=panel_ip,
            texts=[text],
            colors=[color],
            font_sizes=[font_size],
            show_effects=[effect]
        )
    
    def test_connection(self) -> Dict:
        """
        Probar conexión con la API de paneles
        
        Returns:
            Dict con resultado de la prueba
        """
        try:
            response = requests.get(
                self.api_url.replace('/sendMulti', '/health'),
                timeout=5
            )
            return {
                'success': response.status_code == 200,
                'message': 'Conexión exitosa' if response.status_code == 200 else 'Error de conexión',
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error de conexión: {str(e)}',
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
    print("🔍 Probando conexión con API de paneles...")
    result = service.test_connection()
    print(f"Resultado: {result}")
    
    # Ejemplo de envío de texto
    print("\n📤 Enviando texto de prueba...")
    result = service.send_custom_text(
        panel_ip="172.20.4.52",
        text="PROVA PANEL",
        color=2,  # Verde
        font_size=2,
        effect=1  # Centrado
    )
    print(f"Resultado: {result}") 