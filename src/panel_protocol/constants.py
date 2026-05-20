"""
Constantes del protocolo de comunicación con paneles LED
"""

# ID Code común para todos los paneles (formato antiguo - NO USAR para envío)
ID_CODE_LEGACY = bytes([0xFF, 0xFF, 0xFF, 0xFF])
ID_CODE = ID_CODE_LEGACY  # Alias para compatibilidad con packet_parser

# Marcador de inicio del formato CPower (formato correcto)
CPOWER_START_MARKER = 0xA5
CPOWER_SEPARATOR = 0x00

# Puerto UDP para discovery de paneles CPower
CPOWER_DISCOVERY_PORT = 57274
CPOWER_DISCOVERY_REQUEST = b'CPower~?\x00'

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

# Subcomandos del protocolo 0x7B (General protocol commands)
SUB_CMD_CREATE_WINDOW = 0x01      # CC=0x01: División de ventanas
SUB_CMD_SEND_TEXT = 0x02          # CC=0x02: Enviar texto Rich3 a ventana
SUB_CMD_SEND_IMAGE = 0x03         # CC=0x03: Enviar imagen a ventana
SUB_CMD_STATIC_TEXT = 0x04        # CC=0x04: Texto estático con RGB
SUB_CMD_SEND_CLOCK = 0x05         # CC=0x05: Enviar reloj
SUB_CMD_EXIT_SHOW = 0x06          # CC=0x06: Salir y volver a programa interno
SUB_CMD_SAVE_CLEAR = 0x07         # CC=0x07: Guardar/limpiar datos
SUB_CMD_EXECUTE_PROGRAM = 0x08    # CC=0x08: Ejecutar programa (1 byte)
SUB_CMD_EXECUTE_PROGRAM_2B = 0x09 # CC=0x09: Ejecutar programa (2 bytes)
SUB_CMD_SET_VARIABLE = 0x0A       # CC=0x0A: Establecer valor de variable
SUB_CMD_PROGRAM_VARIABLE = 0x0B   # CC=0x0B: Programa + variable
SUB_CMD_SET_GLOBAL_AREA = 0x0C    # CC=0x0C: Establecer área global
SUB_CMD_PUSH_VARIABLE = 0x0D      # CC=0x0D: Push variable de usuario
SUB_CMD_SET_TIMER = 0x0E          # CC=0x0E: Control de temporizador
SUB_CMD_GLOBAL_AREA_VAR = 0x0F    # CC=0x0F: Área global + variables
SUB_CMD_PURE_TEXT = 0x12          # CC=0x12: Texto puro con RGB

# Subcomandos del protocolo 0x7B (Program template commands)
SUB_CMD_SET_TEMPLATE = 0x81       # CC=0x81: Establecer programa template
SUB_CMD_IN_OUT_TEMPLATE = 0x82    # CC=0x82: Entrar/salir programa template
SUB_CMD_QUERY_TEMPLATE = 0x83     # CC=0x83: Consultar programa template
SUB_CMD_DELETE_PROGRAM = 0x84     # CC=0x84: Eliminar programa
SUB_CMD_SEND_TEXT_SPECIAL = 0x85  # CC=0x85: Enviar texto a ventana especial
SUB_CMD_SEND_IMAGE_SPECIAL = 0x86 # CC=0x86: Enviar imagen a ventana especial
SUB_CMD_CLOCK_TEMP = 0x87         # CC=0x87: Reloj/temperatura en ventana
SUB_CMD_SEND_PROGRAM = 0x88       # CC=0x88: Enviar programa independiente
SUB_CMD_SET_PROGRAM_PROP = 0x8A   # CC=0x8A: Establecer propiedad de programa
SUB_CMD_SET_PLAY_PLAN = 0x8B      # CC=0x8B: Establecer plan de reproducción
SUB_CMD_DELETE_PLAY_PLAN = 0x8C   # CC=0x8C: Eliminar plan de reproducción
SUB_CMD_QUERY_PLAY_PLAN = 0x8D    # CC=0x8D: Consultar plan de reproducción

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

# Efectos de texto según documentación del fabricante (códigos 0-70)
# Fuente: Rotuloselectronicos.net external calls communication protocol v1.4.7
class Effect:
    # Efectos básicos (0-15)
    DRAW = 0x00                      # 0 - Instantáneo/Fijo
    OPEN_FROM_LEFT = 0x01            # 1 - Abrir desde izquierda
    OPEN_FROM_RIGHT = 0x02           # 2 - Abrir desde derecha
    OPEN_FROM_CENTER_H = 0x03        # 3 - Abrir desde centro (horizontal)
    OPEN_FROM_CENTER_V = 0x04        # 4 - Abrir desde centro (vertical)
    SHUTTER_VERTICAL = 0x05          # 5 - Persiana vertical
    MOVE_TO_LEFT = 0x06              # 6 - Mover a izquierda
    MOVE_TO_RIGHT = 0x07             # 7 - Mover a derecha
    MOVE_UP = 0x08                   # 8 - Mover arriba
    MOVE_DOWN = 0x09                 # 9 - Mover abajo
    SCROLL_UP = 0x0A                 # 10 - Scroll arriba
    SCROLL_LEFT = 0x0B               # 11 - Scroll izquierda (con pausa al final)
    SCROLL_RIGHT = 0x0C              # 12 - Scroll derecha (con pausa al final)
    FLICKER = 0x0D                   # 13 - Parpadeo
    CONTINUOUS_SCROLL_LEFT = 0x0E    # 14 - Scroll continuo izquierda (sin pausa)
    CONTINUOUS_SCROLL_RIGHT = 0x0F   # 15 - Scroll continuo derecha (sin pausa)
    
    # Efectos adicionales (16-54)
    SHUTTER_HORIZONTAL = 0x10        # 16 - Persiana horizontal
    CLOCKWISE_OPEN = 0x11            # 17 - Abrir en sentido horario
    ANTICLOCKWISE_OPEN = 0x12        # 18 - Abrir en sentido antihorario
    WINDMILL = 0x13                  # 19 - Molino
    WINDMILL_ANTI = 0x14             # 20 - Molino (antihorario)
    RECTANGLE_FORTH = 0x15           # 21 - Rectángulo hacia fuera
    RECTANGLE_ENTAD = 0x16           # 22 - Rectángulo hacia dentro
    QUADRANGLE_FORTH = 0x17          # 23 - Cuadrilátero hacia fuera
    QUADRANGLE_ENTAD = 0x18          # 24 - Cuadrilátero hacia dentro
    CIRCLE_FORTH = 0x19              # 25 - Círculo hacia fuera
    CIRCLE_ENTAD = 0x1A              # 26 - Círculo hacia dentro
    OPEN_LEFT_UP = 0x1B              # 27 - Abrir desde esquina sup-izq
    OPEN_RIGHT_UP = 0x1C             # 28 - Abrir desde esquina sup-der
    OPEN_LEFT_BOTTOM = 0x1D          # 29 - Abrir desde esquina inf-izq
    OPEN_RIGHT_BOTTOM = 0x1E         # 30 - Abrir desde esquina inf-der
    BEVEL_OPEN = 0x1F                # 31 - Abrir en bisel
    ANTI_BEVEL_OPEN = 0x20           # 32 - Abrir anti-bisel
    ENTER_LEFT_UP = 0x21             # 33 - Entrar desde esquina sup-izq
    ENTER_RIGHT_UP = 0x22            # 34 - Entrar desde esquina sup-der
    ENTER_LEFT_BOTTOM = 0x23         # 35 - Entrar desde esquina inf-izq
    ENTER_RIGHT_BOTTOM = 0x24        # 36 - Entrar desde esquina inf-der
    BEVEL_ENTER = 0x25               # 37 - Entrar en bisel
    ANTI_BEVEL_ENTER = 0x26          # 38 - Entrar anti-bisel
    ZEBRA_HORIZONTAL = 0x27          # 39 - Paso de cebra horizontal
    ZEBRA_VERTICAL = 0x28            # 40 - Paso de cebra vertical
    MOSAIC_BIG = 0x29                # 41 - Mosaico grande
    MOSAIC_SMALL = 0x2A              # 42 - Mosaico pequeño
    RADIATION_UP = 0x2B              # 43 - Radiación arriba
    RADIATION_DOWN = 0x2C            # 44 - Radiación abajo
    AMASS = 0x2D                     # 45 - Acumular
    DROP = 0x2E                      # 46 - Gota
    COMBINATION_H = 0x2F             # 47 - Combinación horizontal
    COMBINATION_V = 0x30             # 48 - Combinación vertical
    BACKOUT = 0x31                   # 49 - Retroceder
    SCREWING_IN = 0x32               # 50 - Atornillar
    CHESSBOARD_H = 0x33              # 51 - Tablero horizontal
    CHESSBOARD_V = 0x34              # 52 - Tablero vertical
    CONTINUOUS_SCROLL_UP = 0x35      # 53 - Scroll continuo arriba
    CONTINUOUS_SCROLL_DOWN = 0x36    # 54 - Scroll continuo abajo
    
    # ⚠️ CÓDIGOS RESERVADOS - NO USAR
    # RESERVED_55 = 0x37             # 55 - RESERVADO
    # RESERVED_56 = 0x38             # 56 - RESERVADO
    
    # Efectos adicionales (57-70)
    GRADUAL_BIGGER_UP = 0x39         # 57 - Gradualmente más grande (arriba)
    GRADUAL_SMALLER_DOWN = 0x3A      # 58 - Gradualmente más pequeño (abajo)
    # RESERVED_59 = 0x3B             # 59 - RESERVADO
    GRADUAL_BIGGER_V = 0x3C          # 60 - Gradualmente más grande (vertical)
    FLICKER_H = 0x3D                 # 61 - Parpadeo horizontal
    FLICKER_V = 0x3E                 # 62 - Parpadeo vertical
    SNOW = 0x3F                      # 63 - Nieve
    SCROLL_DOWN = 0x40               # 64 - Scroll abajo
    SCROLL_LEFT_TO_RIGHT = 0x41      # 65 - Scroll izquierda a derecha
    OPEN_TOP_TO_BOTTOM = 0x42        # 66 - Abrir de arriba a abajo
    SECTOR_EXPAND = 0x43             # 67 - Expansión sectorial
    # RESERVED_68 = 0x44             # 68 - RESERVADO
    ZEBRA_H_ALT = 0x45               # 69 - Cebra horizontal (alternativo)
    ZEBRA_V_ALT = 0x46               # 70 - Cebra vertical (alternativo)
    
    # Efecto aleatorio
    RANDOM = 0xFF                    # 255 (1 byte) o 0x8000 (2 bytes)

# Alineación horizontal para CC=0x02 (solo 0-2 según documentación)
class Alignment:
    LEFT = 0x00        # Left-aligned
    CENTER = 0x01      # Horizontal center
    RIGHT = 0x02       # Right-aligned
    # Aliases para compatibilidad
    LEFT_TOP = 0x00
    LEFT_CENTER = 0x00
    CENTER_CENTER = 0x01
    RIGHT_CENTER = 0x02

# Configuración por defecto
DEFAULT_PORT = 5200  # Puerto TCP para comunicación con paneles
DEFAULT_TIMEOUT = 30.0  # segundos (aumentado para mayor latencia)
DEFAULT_CONNECTION_TIMEOUT = 10.0  # segundos (aumentado para mayor latencia)

# Puerto del servicio HTTP/REST
PANEL_PROTOCOL_SERVICE_PORT = 7110  # Puerto fijo para el servicio HTTP

# Flags de confirmación
CONFIRMATION_REQUESTED = 0x01
NO_CONFIRMATION = 0x00

