import struct

class CP5200Protocol:
    """Implementación del protocolo CP5200 según la documentación oficial"""
    
    # Constantes del protocolo
    HEADER_START = 0xAA
    HEADER_END = 0x55
    
    # Comandos del protocolo
    CONNECT = 0x01
    DISCONNECT = 0x02
    PING = 0x03
    SEND_TEXT = 0x10
    CLEAR_TEXT = 0x11
    SEND_IMAGE = 0x20
    SEND_CLOCK = 0x30
    RESTART = 0x40
    GET_STATUS = 0x42
    
    # Respuestas
    ACK = 0x80
    NACK = 0x81
    
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """Calcula checksum del mensaje"""
        checksum = 0
        for byte in data:
            checksum += byte
        return checksum & 0xFFFF
    
    @staticmethod
    def build_message(card_id: int, command: int, data: bytes = b'') -> bytes:
        """Construye mensaje según protocolo CP5200"""
        length = len(data)
        
        # Estructura: [START][END][CARD_ID][COMMAND][LENGTH][DATA][CHECKSUM]
        header = struct.pack('<BBBBH', 
            CP5200Protocol.HEADER_START,  # 0xAA
            CP5200Protocol.HEADER_END,    # 0x55
            card_id,                      # ID del panel
            command,                      # Comando
            length                        # Longitud de datos
        )
        
        # Calcular checksum
        checksum_data = header[2:] + data  # card_id + command + length + data
        checksum = CP5200Protocol.calculate_checksum(checksum_data)
        checksum_bytes = struct.pack('<H', checksum)
        
        return header + data + checksum_bytes
    
    @staticmethod
    def make_send_text_payload(text: str, window_no: int = 0, color: int = 0xFFFFFF, 
                              font_size: int = 16, speed: int = 5, effect: int = 0, 
                              stay_time: int = 5, alignment: int = 1) -> bytes:
        """Crea payload para comando SEND_TEXT"""
        # Parámetros del texto
        params = struct.pack('<BBBBBBBBB', 
            window_no,                    # Ventana
            (color >> 16) & 0xFF,        # Color R
            (color >> 8) & 0xFF,         # Color G
            color & 0xFF,                # Color B
            font_size,                   # Tamaño de fuente
            speed,                       # Velocidad
            effect,                      # Efecto
            stay_time,                   # Tiempo de permanencia
            alignment                    # Alineación
        )
        # Texto en UTF-8
        text_bytes = text.encode('utf-8')
        return params + text_bytes

# Funciones de compatibilidad para mantener la API existente
def calculate_checksum(data: bytes) -> int:
    return CP5200Protocol.calculate_checksum(data)

def build_packet(network_id: int, card_id: int, command_code: int, payload: bytes, need_confirmation: bool = True) -> bytes:
    """Función de compatibilidad - usa el protocolo CP5200 correcto"""
    return CP5200Protocol.build_message(card_id, command_code, payload)

def make_send_text_payload(window_no: int, mode: int, alignment: int, speed: int, stay_time: int, text: str) -> bytes:
    """Función de compatibilidad - mapea parámetros al protocolo CP5200"""
    # Mapear parámetros: mode -> effect, alignment -> alignment
    return CP5200Protocol.make_send_text_payload(
        text=text,
        window_no=window_no,
        color=0xFFFFFF,  # Blanco por defecto
        font_size=16,
        speed=speed,
        effect=mode,
        stay_time=stay_time,
        alignment=alignment
    ) 