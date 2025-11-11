#!/usr/bin/env python3
"""
Módulo de integración backend para paneles LED
Funciones optimizadas para uso en aplicaciones backend
"""

from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from enum import IntEnum
import socket
import time
from panel_protocol import (
    PanelProtocol,
    TextColor,
    FontSize,
    TextAlignment,
    TextEffect
)


@dataclass
class WindowMessage:
    """Estructura para mensaje de una ventana"""
    window_number: int
    text: str
    color: TextColor = TextColor.GREEN
    font_size: FontSize = FontSize.SIZE_16
    alignment: TextAlignment = TextAlignment.CENTER_CENTER
    effect: TextEffect = TextEffect.STATIC
    speed: int = 0x03
    wait_time: int = 0x0003


@dataclass
class SendResult:
    """Resultado del envío a una ventana"""
    window_number: int
    success: bool
    error_message: Optional[str] = None
    response: Optional[bytes] = None


@dataclass
class BatchResult:
    """Resultado del envío batch a múltiples ventanas"""
    total: int
    successful: int
    failed: int
    results: List[SendResult]
    execution_time: float
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito en porcentaje"""
        return (self.successful / self.total * 100) if self.total > 0 else 0.0
    
    @property
    def all_successful(self) -> bool:
        """True si todos los envíos fueron exitosos"""
        return self.failed == 0


class PanelBackend:
    """
    Clase para integración de paneles LED en aplicaciones backend
    Optimizada para operaciones batch y manejo robusto de errores
    """
    
    def __init__(
        self,
        ip_address: str,
        port: int = 5200,
        timeout: int = 5,
        retry_attempts: int = 3,
        retry_delay: float = 0.5
    ):
        """
        Inicializa el backend de paneles
        
        Args:
            ip_address: IP del panel LED
            port: Puerto TCP (default: 5200)
            timeout: Timeout de conexión en segundos
            retry_attempts: Número de reintentos en caso de fallo
            retry_delay: Delay entre reintentos en segundos
        """
        self.panel = PanelProtocol(ip_address, port)
        self.panel.timeout = timeout
        self.ip_address = ip_address
        self.port = port
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
    
    def send_to_window(
        self,
        window_number: int,
        text: str,
        color: TextColor = TextColor.GREEN,
        font_size: FontSize = FontSize.SIZE_16,
        alignment: TextAlignment = TextAlignment.CENTER_CENTER,
        effect: TextEffect = TextEffect.STATIC,
        speed: int = 0x03,
        wait_time: int = 0x0003
    ) -> SendResult:
        """
        Envía texto a una ventana específica con reintentos automáticos
        
        Args:
            window_number: Número de ventana (0-7)
            text: Texto a enviar
            color: Color del texto
            font_size: Tamaño de fuente
            alignment: Alineación
            effect: Efecto de visualización
            speed: Velocidad del efecto
            wait_time: Tiempo de espera
            
        Returns:
            SendResult con el resultado del envío
        """
        for attempt in range(self.retry_attempts):
            try:
                packet = self.panel.build_text_packet(
                    text=text,
                    window_number=window_number,
                    color=color,
                    font_size=font_size,
                    alignment=alignment,
                    effect=effect,
                    speed=speed,
                    wait_time=wait_time
                )
                
                response = self.panel.send_packet(packet, verbose=False)
                
                if response:
                    # Validar respuesta
                    if len(response) >= 13 and response[12] == 0x00:
                        return SendResult(
                            window_number=window_number,
                            success=True,
                            response=response
                        )
                    else:
                        error_msg = f"Panel returned error code: {response[12]:02x}"
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                            continue
                        return SendResult(
                            window_number=window_number,
                            success=False,
                            error_message=error_msg,
                            response=response
                        )
                else:
                    error_msg = "No response from panel"
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return SendResult(
                        window_number=window_number,
                        success=False,
                        error_message=error_msg
                    )
                    
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                return SendResult(
                    window_number=window_number,
                    success=False,
                    error_message=error_msg
                )
        
        # Si llegamos aquí, todos los intentos fallaron
        return SendResult(
            window_number=window_number,
            success=False,
            error_message=f"Failed after {self.retry_attempts} attempts"
        )
    
    def send_batch(
        self,
        messages: List[WindowMessage],
        delay_between_sends: float = 0.1
    ) -> BatchResult:
        """
        Envía múltiples mensajes a diferentes ventanas en batch
        
        Args:
            messages: Lista de WindowMessage para enviar
            delay_between_sends: Delay entre envíos en segundos
            
        Returns:
            BatchResult con estadísticas y resultados individuales
        """
        start_time = time.time()
        results = []
        successful = 0
        failed = 0
        
        for i, msg in enumerate(messages):
            result = self.send_to_window(
                window_number=msg.window_number,
                text=msg.text,
                color=msg.color,
                font_size=msg.font_size,
                alignment=msg.alignment,
                effect=msg.effect,
                speed=msg.speed,
                wait_time=msg.wait_time
            )
            
            results.append(result)
            
            if result.success:
                successful += 1
            else:
                failed += 1
            
            # Delay entre envíos (excepto el último)
            if i < len(messages) - 1:
                time.sleep(delay_between_sends)
        
        execution_time = time.time() - start_time
        
        return BatchResult(
            total=len(messages),
            successful=successful,
            failed=failed,
            results=results,
            execution_time=execution_time
        )
    
    def send_same_to_all_windows(
        self,
        text: str,
        windows: List[int],
        color: TextColor = TextColor.GREEN,
        font_size: FontSize = FontSize.SIZE_16,
        alignment: TextAlignment = TextAlignment.CENTER_CENTER,
        effect: TextEffect = TextEffect.STATIC,
        speed: int = 0x03,
        wait_time: int = 0x0003,
        delay_between_sends: float = 0.1
    ) -> BatchResult:
        """
        Envía el mismo texto a múltiples ventanas
        Optimización de send_batch para texto idéntico
        
        Args:
            text: Texto a enviar
            windows: Lista de números de ventana
            color: Color del texto
            font_size: Tamaño de fuente
            alignment: Alineación
            effect: Efecto de visualización
            speed: Velocidad del efecto
            wait_time: Tiempo de espera
            delay_between_sends: Delay entre envíos
            
        Returns:
            BatchResult con estadísticas
        """
        messages = [
            WindowMessage(
                window_number=window,
                text=text,
                color=color,
                font_size=font_size,
                alignment=alignment,
                effect=effect,
                speed=speed,
                wait_time=wait_time
            )
            for window in windows
        ]
        
        return self.send_batch(messages, delay_between_sends)
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Prueba la conexión con el panel
        
        Returns:
            Tupla (éxito: bool, mensaje_error: Optional[str])
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.panel.timeout)
                sock.connect((self.ip_address, self.port))
                return (True, None)
        except ConnectionRefusedError:
            return (False, f"Connection refused to {self.ip_address}:{self.port}")
        except socket.timeout:
            return (False, f"Timeout connecting to {self.ip_address}:{self.port}")
        except Exception as e:
            return (False, f"Error: {str(e)}")
    
    def clear_window(
        self,
        window_number: int
    ) -> SendResult:
        """
        Limpia una ventana enviando texto vacío
        
        Args:
            window_number: Número de ventana a limpiar
            
        Returns:
            SendResult con el resultado
        """
        return self.send_to_window(
            window_number=window_number,
            text=" ",  # Espacio en blanco
            color=TextColor.GREEN,
            font_size=FontSize.SIZE_16,
            alignment=TextAlignment.CENTER_CENTER,
            effect=TextEffect.STATIC
        )
    
    def clear_all_windows(
        self,
        windows: List[int]
    ) -> BatchResult:
        """
        Limpia múltiples ventanas
        
        Args:
            windows: Lista de ventanas a limpiar
            
        Returns:
            BatchResult con estadísticas
        """
        return self.send_same_to_all_windows(
            text=" ",
            windows=windows,
            color=TextColor.GREEN
        )


# Funciones de conveniencia para uso rápido

def quick_send(
    ip: str,
    window: int,
    text: str,
    color: str = "green",
    effect: str = "static",
    speed: int = 5
) -> bool:
    """
    Función rápida para enviar texto (interfaz simplificada)
    
    Args:
        ip: IP del panel
        window: Número de ventana
        text: Texto a enviar
        color: Color como string (red, green, yellow, blue, purple, cyan, white)
        effect: Efecto como string (static, scroll_left, scroll_right, etc)
        speed: Velocidad (1-100)
        
    Returns:
        True si fue exitoso
    """
    # Mapeo de colores
    color_map = {
        "red": TextColor.RED,
        "green": TextColor.GREEN,
        "yellow": TextColor.YELLOW,
        "blue": TextColor.BLUE,
        "purple": TextColor.PURPLE,
        "cyan": TextColor.CYAN,
        "white": TextColor.WHITE
    }
    
    # Mapeo de efectos
    effect_map = {
        "static": TextEffect.STATIC,
        "scroll_left": TextEffect.SCROLL_LEFT,
        "scroll_right": TextEffect.SCROLL_RIGHT,
        "scroll_up": TextEffect.SCROLL_UP,
        "move_left": TextEffect.MOVE_LEFT,
        "move_right": TextEffect.MOVE_RIGHT,
        "flicker": TextEffect.FLICKER
    }
    
    backend = PanelBackend(ip)
    result = backend.send_to_window(
        window_number=window,
        text=text,
        color=color_map.get(color.lower(), TextColor.GREEN),
        effect=effect_map.get(effect.lower(), TextEffect.STATIC),
        speed=speed
    )
    
    return result.success


def quick_send_all(
    ip: str,
    windows: List[int],
    text: str,
    color: str = "green",
    effect: str = "static",
    speed: int = 5
) -> Dict[str, any]:
    """
    Función rápida para enviar a múltiples ventanas
    
    Args:
        ip: IP del panel
        windows: Lista de ventanas
        text: Texto a enviar
        color: Color como string
        effect: Efecto como string
        speed: Velocidad
        
    Returns:
        Dict con resultados
    """
    color_map = {
        "red": TextColor.RED,
        "green": TextColor.GREEN,
        "yellow": TextColor.YELLOW,
        "blue": TextColor.BLUE,
        "purple": TextColor.PURPLE,
        "cyan": TextColor.CYAN,
        "white": TextColor.WHITE
    }
    
    effect_map = {
        "static": TextEffect.STATIC,
        "scroll_left": TextEffect.SCROLL_LEFT,
        "scroll_right": TextEffect.SCROLL_RIGHT,
        "scroll_up": TextEffect.SCROLL_UP,
        "move_left": TextEffect.MOVE_LEFT,
        "move_right": TextEffect.MOVE_RIGHT,
        "flicker": TextEffect.FLICKER
    }
    
    backend = PanelBackend(ip)
    result = backend.send_same_to_all_windows(
        text=text,
        windows=windows,
        color=color_map.get(color.lower(), TextColor.GREEN),
        effect=effect_map.get(effect.lower(), TextEffect.STATIC),
        speed=speed
    )
    
    return {
        "success": result.all_successful,
        "total": result.total,
        "successful": result.successful,
        "failed": result.failed,
        "success_rate": result.success_rate,
        "execution_time": result.execution_time
    }


if __name__ == "__main__":
    # Ejemplos de uso
    print("Módulo de Backend para Paneles LED")
    print("=" * 60)
    print("\nEjemplos de uso:")
    print("\n1. Uso rápido:")
    print('   quick_send("192.168.10.110", 0, "HOLA", "green")')
    print("\n2. Uso con clase:")
    print('   backend = PanelBackend("192.168.10.110")')
    print('   result = backend.send_to_window(0, "HOLA")')
    print("\n3. Envío batch:")
    print('   result = backend.send_same_to_all_windows("LIBRE", [0,1,2,3,4,5,6])')

