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

# v5.0.1: Reenvío de ingestión a parking-monitor (no bloquea el proceso local)
INGEST_FORWARD_ENABLED = os.getenv('INGEST_FORWARD_ENABLED', 'true').lower() in ('1', 'true', 'yes')
INGEST_FORWARD_TIMEOUT = float(os.getenv('INGEST_FORWARD_TIMEOUT', '3'))
INGEST_FORWARD_LINE_COUNT_URL = os.getenv(
    'INGEST_FORWARD_LINE_COUNT_URL',
    'https://parking-monitor.swat-id.com/api/ingest/line-count'
)
INGEST_FORWARD_SPOT_URL = os.getenv(
    'INGEST_FORWARD_SPOT_URL',
    'https://parking-monitor.swat-id.com/api/ingest/spot'
)
INGEST_FORWARD_SENSOR_URL = os.getenv(
    'INGEST_FORWARD_SENSOR_URL',
    'https://parking-monitor.swat-id.com/api/ingest/sensor'
)