import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')
CAMERA_PORT = int(os.getenv('CAMERA_PORT', 6400))
SPOT_DETECTION_PORT = int(os.getenv('SPOT_DETECTION_PORT', 6401))  # NUEVO v4.4.0: Puerto para cámaras detección por plaza
API_PORT = int(os.getenv('API_PORT', 6001))
PANEL_PROTOCOL_SERVICE_PORT = int(os.getenv('PANEL_PROTOCOL_SERVICE_PORT', 7110))
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 15))

# NUEVO v4.4.0: Límites para ocupación
OCCUPANCY_MAX_LIMIT_PERCENT = float(os.getenv('OCCUPANCY_MAX_LIMIT_PERCENT', 110))  # 110% = límite máximo
OCCUPANCY_MIN_LIMIT = int(os.getenv('OCCUPANCY_MIN_LIMIT', 0))  # 0 = límite mínimo