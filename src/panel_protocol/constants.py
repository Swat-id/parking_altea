"""
Constantes del protocolo de comunicación con paneles LED
"""

# ID Code común para todos los paneles
ID_CODE = bytes([0xFF, 0xFF, 0xFF, 0xFF])

# Tipos de paquetes
PACKET_TYPE_SEND = 0x68
PACKET_TYPE_RESPONSE = 0xE8

# Tipo de tarjeta fijo
CARD_TYPE = 0x32

# Card ID especiales
CARD_ID_BROADCAST = 0xFF

# Comandos principales
CMD_PROTOCOL_CONTROL = 0x7B  # Protocolo de control de ventanas y contenido
CMD_STATIC_TEXT = 0x04       # Texto estático alternativo

# Subcomandos del protocolo 0x7B
SUB_CMD_CREATE_WINDOW = 0x01
SUB_CMD_SEND_TEXT = 0x02
SUB_CMD_SEND_IMAGE = 0x03
SUB_CMD_EXECUTE_PROGRAM = 0x08

# Respuestas
RESPONSE_SUCCESS = 0x00
RESPONSE_FAILURE_MIN = 0x01
RESPONSE_FAILURE_MAX = 0xFF

# Colores predefinidos (1 byte)
class Color:
    RED = 0x01
    GREEN = 0x02
    YELLOW = 0x03
    BLUE = 0x04
    PURPLE = 0x05
    CYAN = 0x06
    WHITE = 0x07

# Tamaños de fuente
class FontSize:
    SIZE_8 = 0x00
    SIZE_12 = 0x01
    SIZE_16 = 0x02
    SIZE_24 = 0x03
    SIZE_32 = 0x04
    SIZE_40 = 0x05
    SIZE_48 = 0x06
    SIZE_56 = 0x07

# Efectos de texto
class Effect:
    DRAW = 0x00              # Instantáneo
    OPEN_FROM_LEFT = 0x01
    OPEN_FROM_RIGHT = 0x02
    MOVE_TO_LEFT = 0x06
    MOVE_TO_RIGHT = 0x07
    SCROLL_UP = 0x0A
    SCROLL_LEFT = 0x0B
    SCROLL_RIGHT = 0x0C
    FLICKER = 0x0D
    CONTINUOUS_SCROLL_LEFT = 0x0E
    CONTINUOUS_SCROLL_RIGHT = 0x0F

# Alineación
class Alignment:
    LEFT_TOP = 0x00
    LEFT_CENTER = 0x04
    CENTER_CENTER = 0x05
    RIGHT_CENTER = 0x06

# Configuración por defecto
DEFAULT_PORT = 5200  # Puerto TCP para comunicación con paneles
DEFAULT_TIMEOUT = 10.0  # segundos
DEFAULT_CONNECTION_TIMEOUT = 5.0  # segundos

# Puerto del servicio HTTP/REST
PANEL_PROTOCOL_SERVICE_PORT = 7110  # Puerto fijo para el servicio HTTP

# Flags de confirmación
CONFIRMATION_REQUESTED = 0x01
NO_CONFIRMATION = 0x00

