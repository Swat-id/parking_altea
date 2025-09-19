#!/usr/bin/env python3
"""
Servicio de comunicación con la API REST unificada de paneles
Usa el servicio PanelSender en puerto 8888 que soporta ambos protocolos
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

def get_old_protocol_parameters(color=None, font_size_pixels=None, effect=None):
    """
    Obtener parámetros correctos para protocolo antiguo (v1.2.6)
    
    Args:
        color: Color (1=Rojo, 2=Verde, 3=Amarillo, etc.)
        font_size_pixels: Tamaño en píxeles (8, 12, 16, 24, 32, 40, 48, 56)
        effect: Efecto (2=fijo, 12=scroll)
    
    Returns:
        Tuple (color_code, font_size_code, effect_code)
    """
    # Color por defecto: Verde
    color_code = color if color in [1, 2, 3, 4, 5, 6, 7] else 2
    
    # Convertir píxeles a código de fuente
    font_map = {8: 0, 12: 1, 16: 2, 24: 3, 32: 4, 40: 5, 48: 6, 56: 7}
    font_size_code = font_map.get(font_size_pixels, 2)  # 16px por defecto
    
    # Efecto por defecto: Fijo
    effect_code = effect if effect in [2, 12] else 2
    
    return color_code, font_size_code, effect_code

def pixels_to_font_code(pixels):
    """
    Convertir píxeles a código de fuente para protocolo antiguo
    
    Args:
        pixels: Tamaño en píxeles (8, 12, 16, 24, 32, 40, 48, 56)
    
    Returns:
        Código de fuente para protocolo antiguo
    """
    font_map = {
        8: 0,    # 8px -> 0
        12: 1,   # 12px -> 1
        16: 2,   # 16px -> 2
        24: 3,   # 24px -> 3
        32: 4,   # 32px -> 4
        40: 5,   # 40px -> 5
        48: 6,   # 48px -> 6
        56: 7    # 56px -> 7
    }
    return font_map.get(pixels, 2)  # 16px por defecto

class PanelCommunicationService:
    """Servicio para comunicación con paneles LED a través de API REST unificada"""
    
    def __init__(self, 
                 api_url: str = "http://localhost:8888/api/v1/panels/send",
                 timeout: int = 45, retry_attempts: int = 2, retry_delay: int = 3):
        self.api_url = api_url
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
    
    def _send_to_unified_api(self, panel_ip: str, texts: List[str], 
                            colors: List[int] = None, font_sizes: List[int] = None,
                            show_effects: List[int] = None, protocol: str = None) -> Dict:
        """
        Enviar mensaje a la API unificada de paneles
        """
        try:
            # Determinar protocolo si no se especifica
            if protocol is None:
                protocol = self._get_panel_protocol(panel_ip)
            
            # Valores por defecto
            if colors is None:
                colors = [1] * len(texts)  # Rojo por defecto
            if font_sizes is None:
                font_sizes = [2] * len(texts)  # Tamaño 16 (valor 2) por defecto
            if show_effects is None:
                show_effects = [2] * len(texts)  # Fijo por defecto (valor 2) - CORREGIDO
                
            # Preparar ventanas para la API
            windows = []
            for i, text in enumerate(texts):
                # Convertir efecto numérico a string descriptivo y ajustar parámetros según protocolo
                effect_value = show_effects[i] if i < len(show_effects) else 2
                
                # Determinar efecto string y stayTime según protocolo
                if protocol == "old":
                    # Protocolo antiguo: usar valores específicos
                    if effect_value == 2:  # Fijo
                        effect_string = "fijo"
                        stay_time = 0  # Requerido para protocolo antiguo
                    elif effect_value == 12:  # Scroll
                        effect_string = "scroll"
                        stay_time = 5  # Requerido para protocolo antiguo
                    else:
                        # Fallback a fijo
                        effect_string = "fijo"
                        stay_time = 0
                else:
                    # Protocolo nuevo: usar valores estándar
                    if effect_value == 1:  # Fijo
                        effect_string = "fijo"
                        stay_time = 50
                    elif effect_value == 12:  # Scroll
                        effect_string = "scroll"
                        stay_time = 50
                    else:
                        # Fallback a fijo
                        effect_string = "fijo"
                        stay_time = 50
                
                window = {
                    "id": i,
                    "text": text,
                    "color": colors[i] if i < len(colors) else 1,
                    "fontSize": font_sizes[i] if i < len(font_sizes) else 2,
                    "effect": effect_string,  # Usar string descriptivo
                    "stayTime": stay_time,  # Ajustado según protocolo
                    "alignmentH": 0,  # Centrado horizontal
                    "alignmentV": 0   # Centrado vertical
                }
                windows.append(window)
            
            # Preparar payload para la API unificada
            payload = {
                "panels": [
                    {
                        "ip": panel_ip,
                        "port": 5200,  # Puerto estándar del fabricante
                        "protocol": protocol,
                        "windows": windows
                    }
                ]
            }
            
            logger.info(f"Enviando a panel {panel_ip} ({protocol}): {texts} con stayTime={stay_time}")
            
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
                            logger.info(f"✅ Texto enviado exitosamente a {panel_ip} ({protocol})")
                            return {
                                'success': True,
                                'message': f'Texto enviado exitosamente ({protocol})',
                                'panel_ip': panel_ip,
                                'protocol': protocol,
                                'texts': texts,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            logger.error(f"❌ Error en respuesta API: {result.get('message')}")
                            return {
                                'success': False,
                                'message': result.get('message', 'Error desconocido'),
                                'panel_ip': panel_ip,
                                'protocol': protocol,
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
                                'protocol': protocol,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout en intento {attempt + 1} para {panel_ip} ({protocol})")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            'success': False,
                            'message': 'Timeout en la comunicación',
                            'panel_ip': panel_ip,
                            'protocol': protocol,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except requests.exceptions.ConnectionError:
                    logger.error(f"🔌 Error de conexión con API en {self.api_url}")
                    return {
                        'success': False,
                        'message': 'Error de conexión con la API de paneles',
                        'panel_ip': panel_ip,
                        'protocol': protocol,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error inesperado: {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error inesperado: {str(e)}',
                        'panel_ip': panel_ip,
                        'protocol': protocol,
                    'timestamp': datetime.now().isoformat()
                }
                    
        except Exception as e:
            logger.error(f"❌ Error general: {str(e)}")
            return {
                'success': False,
                'message': f'Error general: {str(e)}',
                'panel_ip': panel_ip,
                'protocol': protocol,
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_to_unified_api_with_window(self, panel_ip: str, text: str, 
                                        color: int, font_size: int, effect: int,
                                        window_id: int) -> Dict:
        """
        NUEVO v4.1.0: Enviar mensaje a ventana específica usando API unificada
        
        Args:
            panel_ip: IP del panel
            text: Texto a enviar
            color: Color del texto
            font_size: Tamaño de fuente
            effect: Efecto del texto
            window_id: ID de la ventana (0 o 1)
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            protocol = "new"  # Paneles Tipo 3 usan protocolo new
            stay_time = 30000  # 30 segundos por defecto
            
            # Crear payload específico para ventana
            window = {
                "id": window_id,
                "text": text,
                "fontColor": color,
                "fontSize": font_size,
                "showEffect": effect,
                "stayTime": stay_time,
                "positionX": 0,
                "positionY": 0
            }
            
            payload = {
                "panels": [
                    {
                        "ip": panel_ip,
                        "port": 5200,
                        "protocol": protocol,
                        "windows": [window]  # Solo la ventana especificada
                    }
                ]
            }
            
            logger.info(f"Enviando a panel {panel_ip} ventana {window_id}: {text}")
            
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
                        if result.get('success', False):
                            logger.info(f"✅ Texto enviado exitosamente a ventana {window_id} de {panel_ip}")
                            return {
                                'success': True,
                                'message': f'Texto enviado exitosamente a ventana {window_id} ({protocol})',
                                'panel_ip': panel_ip,
                                'window_id': window_id,
                                'protocol': protocol,
                                'text': text,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            logger.error(f"❌ Error en respuesta API: {result.get('message')}")
                            return {
                                'success': False,
                                'message': result.get('message', 'Error desconocido'),
                                'panel_ip': panel_ip,
                                'window_id': window_id,
                                'protocol': protocol,
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
                                'window_id': window_id,
                                'protocol': protocol,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout en intento {attempt + 1} para ventana {window_id} de {panel_ip}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            'success': False,
                            'message': 'Timeout en la comunicación',
                            'panel_ip': panel_ip,
                            'window_id': window_id,
                            'protocol': protocol,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except requests.exceptions.ConnectionError:
                    logger.error(f"🔌 Error de conexión con API en {self.api_url}")
                    return {
                        'success': False,
                        'message': 'Error de conexión con la API de paneles',
                        'panel_ip': panel_ip,
                        'window_id': window_id,
                        'protocol': protocol,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error inesperado: {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error inesperado: {str(e)}',
                        'panel_ip': panel_ip,
                        'window_id': window_id,
                        'protocol': protocol,
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error general: {str(e)}")
            return {
                'success': False,
                'message': f'Error general: {str(e)}',
                'panel_ip': panel_ip,
                'window_id': window_id,
                'protocol': 'new',
                'timestamp': datetime.now().isoformat()
            }
    
    def send_text_to_panel(self, panel_ip: str, texts: List[str], 
                          colors: List[int] = None, font_sizes: List[int] = None,
                          show_effects: List[int] = None) -> Dict:
        """
        Enviar texto a un panel específico
        
        Args:
            panel_ip: IP del panel
            texts: Lista de textos a enviar
            colors: Lista de colores (opcional)
            font_sizes: Lista de tamaños de fuente (opcional)
            show_effects: Lista de efectos (opcional)
            
        Returns:
            Diccionario con el resultado de la operación
        """
        return self._send_to_unified_api(panel_ip, texts, colors, font_sizes, show_effects)
    
    def send_parking_status(self, panel_ip: str, parking_name: str, 
                           free_spaces: int, total_spaces: int,
                           language_code: str = 'va') -> Dict:
        """
        Enviar estado de ocupación del parking a un panel
        
        Args:
            panel_ip: IP del panel
            parking_name: Nombre del parking
            free_spaces: Plazas libres
            total_spaces: Total de plazas
            language_code: Código de idioma ('va' para valenciano)
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Determinar estado y color según ocupación
            occupancy_percentage = ((total_spaces - free_spaces) / total_spaces) * 100
            
            if free_spaces > 0:
                if occupancy_percentage < 70:
                    status_text = "LLIURE" if language_code == 'va' else "LIBRE"
                    color = 2  # Verde
                elif occupancy_percentage < 90:
                    status_text = "DENS" if language_code == 'va' else "DENSO"
                    color = 3  # Amarillo
                else:
                    status_text = "COMPLET" if language_code == 'va' else "COMPLETO"
                    color = 1  # Rojo
            else:
                status_text = "COMPLET" if language_code == 'va' else "COMPLETO"
                color = 1  # Rojo
            
            # Crear mensaje
            message = f"{parking_name}\n{status_text}\n{free_spaces}/{total_spaces}"
            
            return self.send_custom_text(panel_ip, message, color, 2, 2)  # Fijo por defecto (valor 2) - CORREGIDO
            
        except Exception as e:
            logger.error(f"Error enviando estado de parking a {panel_ip}: {e}")
            return {
                'success': False,
                'message': f'Error enviando estado: {str(e)}',
                'panel_ip': panel_ip,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_custom_text(self, panel_ip: str, text: str, 
                        color: int = 1, font_size: int = 2, 
                        effect: int = 2) -> Dict:  # Fijo por defecto (valor 2) - CORREGIDO
        """
        Enviar texto personalizado a un panel
        
        Args:
            panel_ip: IP del panel
            text: Texto a enviar
            color: Color del texto (1=Rojo, 2=Verde, 3=Amarillo, etc.)
            font_size: Tamaño de fuente (0=8px, 1=12px, 2=16px, etc.)
            effect: Efecto (2=fijo, 12=scroll) - CORREGIDO
            
        Returns:
            Diccionario con el resultado de la operación
        """
        return self._send_to_unified_api(
            panel_ip, 
            [text], 
            [color], 
            [font_size], 
            [effect]
        )
    
    def send_custom_text_to_window(self, panel_ip: str, text: str, 
                                  color: int = 1, font_size: int = 2, 
                                  effect: int = 2, window_id: int = 0) -> Dict:
        """
        NUEVO v4.1.0: Enviar texto personalizado a una ventana específica de un panel Tipo 3
        
        Args:
            panel_ip: IP del panel
            text: Texto a enviar
            color: Color del texto (1=Rojo, 2=Verde, 3=Amarillo, etc.)
            font_size: Tamaño de fuente (0=8px, 1=12px, 2=16px, etc.)
            effect: Efecto (2=fijo, 12=scroll)
            window_id: ID de la ventana (0 o 1)
            
        Returns:
            Diccionario con el resultado de la operación
        """
        return self._send_to_unified_api_with_window(
            panel_ip, 
            text, 
            color, 
            font_size, 
            effect,
            window_id
        )
    
    def test_connection(self) -> Dict:
        """
        Probar la conexión con la API de paneles
        
        Returns:
            Diccionario con el resultado de la prueba
        """
        try:
            health_url = self.api_url.replace('/api/v1/panels/send', '/health')
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': 'Conexión exitosa con API de paneles',
                    'status': result.get('status', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'message': f'Error HTTP {response.status_code}',
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'No se puede conectar con la API de paneles',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error probando conexión: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

def get_panel_service() -> PanelCommunicationService:
    """
    Obtener instancia del servicio de comunicación con paneles
    
    Returns:
        Instancia de PanelCommunicationService
    """
    return PanelCommunicationService()

def update_parking_panels(parking_id: int, current_occupancy: int, max_capacity: int, status: str, db_session=None) -> Dict:
    """
    Actualiza todos los paneles de un parking con la información de ocupación
    
    Args:
        parking_id: ID del parking
        current_occupancy: Ocupación actual
        max_capacity: Capacidad máxima
        status: Estado del parking (COMPLETO, DENSO, LIBRE)
        db_session: Sesión de base de datos (opcional)
    
    Returns:
        Dict con el resultado de la operación
    """
    try:
        # Si no se proporciona sesión, crear una nueva
        if db_session is None:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models import Parking, Panel
            import config
            
            engine = create_engine(config.DB_URL)
            Session = sessionmaker(bind=engine)
            db_session = Session()
            should_close_session = True
        else:
            from models import Parking, Panel
            should_close_session = False
        
        try:
            # Obtener el parking y sus paneles
            parking = db_session.query(Parking).filter(Parking.id == parking_id).first()
            if not parking:
                return {
                    'success': False,
                    'error': f'Parking {parking_id} no encontrado'
                }
            
            panels = db_session.query(Panel).filter(Panel.parking_id == parking_id).all()
            if not panels:
                return {
                    'success': True,
                    'message': f'No hay paneles configurados para el parking {parking_id}',
                    'panels_updated': 0
                }
            
            # VERIFICAR SI HAY PROGRAMACIONES ACTIVAS ANTES DE ACTUALIZAR PANELES
            from panel_schedule_service import PanelScheduleService
            schedule_service = PanelScheduleService(db_session)
            active_schedules = schedule_service.get_active_schedules_for_parking(parking_id)
            
            if active_schedules:
                logger.info(f"Active schedules found for parking {parking_id}, skipping panel update for occupancy change")
                return "SCHEDULE_ACTIVE"  # NO actualizar paneles si hay programación activa
            
            # Calcular porcentaje de ocupación
            if max_capacity > 0:
                occupancy_percentage = int((current_occupancy / max_capacity) * 100)
            else:
                occupancy_percentage = 0
            
            # Determinar el mensaje y color según el estado
            if status.lower() == 'closed':
                message = "PARKING TANCAT"
                color = 1  # Rojo para parking cerrado
            else:
                # Usar el estado del parking (COMPLETO, DENSO, LIBRE)
                if status.upper() == 'COMPLETO':
                    status_text = "COMPLET"  # CORREGIDO: sin "PARKING"
                    color = 1  # Rojo para estado completo
                elif status.upper() == 'DENSO':
                    status_text = "DENS"  # CORREGIDO: sin "PARKING"
                    color = 3  # Amarillo para estado denso
                else:
                    status_text = "LLIURE"  # CORREGIDO: sin "PLACES LLIURES"
                    color = 2  # Verde para estado libre
                
                # CORRECCIÓN: Solo mostrar el estado en valenciano
                message = status_text
            
            # Usar el PanelCommunicationService para enviar mensajes
            panel_service = PanelCommunicationService()
            updated_panels = 0
            errors = []
            
            for panel in panels:
                try:
                    result = panel_service.send_custom_text(
                        panel_ip=panel.ip,
                        text=message,
                        color=color,  # Color dinámico según estado
                        font_size=2,  # Tamaño 16 píxeles (código 2)
                        effect=2  # Fijo (valor correcto)
                    )
                    
                    if result.get('success'):
                        updated_panels += 1
                        # NUEVO v4.1.0: Actualizar el último mensaje del panel solo si fue exitoso
                        current_time = datetime.now()
                        panel.last_message = message  # Mantener compatibilidad
                        panel.last_update = current_time
                        
                        # NUEVO v4.1.0: Actualizar ventanas específicas según tipo de panel
                        panel.last_message_window_0 = message  # Todos los paneles tienen ventana 0
                        panel.last_update_window_0 = current_time
                        
                        # Solo actualizar ventana 1 para paneles Tipo 3 (múltiples ventanas)
                        if panel.supports_multiple_windows():
                            # Para paneles Tipo 3, el mensaje automático va a ambas ventanas
                            panel.last_message_window_1 = message
                            panel.last_update_window_1 = current_time
                            logger.info(f"Panel Tipo 3 {panel.ip} actualizado en ambas ventanas: '{message}'")
                        else:
                            # Para paneles Tipo 1 y 2, no tocar ventana 1
                            logger.info(f"Panel Tipo 1/2 {panel.ip} actualizado solo en ventana 0: '{message}'")
                        
                        panel.status = 'ONLINE'
                    else:
                        error_msg = result.get('message', 'Error desconocido')
                        errors.append(f"Panel {panel.ip}: {error_msg}")
                        # Solo actualizar estado y timestamp, preservar último mensaje válido
                        panel.last_update = datetime.now()
                        panel.status = 'OFFLINE'
                        logger.error(f"Error actualizando panel {panel.ip}: {error_msg}")
                        
                except Exception as e:
                    error_msg = f"Error inesperado: {str(e)}"
                    errors.append(f"Panel {panel.ip}: {error_msg}")
                    logger.error(f"Error inesperado con panel {panel.ip}: {str(e)}")
            
            # Preparar respuesta
            result = {
                'success': True,
                'parking_id': parking_id,
                'message': message,
                'occupancy_percentage': occupancy_percentage,
                'panels_updated': updated_panels,
                'total_panels': len(panels)
            }
            
            if errors:
                result['errors'] = errors
                result['partial_success'] = updated_panels > 0
            
            logger.info(f"Actualización de paneles completada para parking {parking_id}: {updated_panels}/{len(panels)} paneles actualizados")
            return result
            
        finally:
            if should_close_session:
                db_session.close()
                
    except Exception as e:
        logger.error(f"Error general en update_parking_panels: {str(e)}")
        return {
            'success': False,
            'error': f'Error general: {str(e)}'
        }

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