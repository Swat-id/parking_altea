import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')
CAMERA_PORT = int(os.getenv('CAMERA_PORT', 6400))
API_PORT = int(os.getenv('API_PORT', 6001))
PANEL_PROTOCOL_SERVICE_PORT = int(os.getenv('PANEL_PROTOCOL_SERVICE_PORT', 7110))
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 15))