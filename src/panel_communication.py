"""
Panel Communication Module for CP5200 Protocol
Implements native TCP/IP communication with parking display panels
"""

import socket
import struct
import time
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PanelCommand(Enum):
    """CP5200 Panel Commands"""
    SEND_TEXT = 0x01
    SEND_IMAGE = 0x02
    SEND_CLOCK = 0x03
    CONTROL = 0x04
    QUERY_STATUS = 0x05

class PanelStatus(Enum):
    """Panel Status"""
    OFFLINE = "offline"
    ONLINE = "online"
    ERROR = "error"
    CONNECTING = "connecting"

@dataclass
class PanelConfig:
    """Panel Configuration"""
    ip: str
    port: int = 5000
    panel_id: int = 1
    timeout: float = 5.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

@dataclass
class PanelMessage:
    """Panel Message Structure"""
    command: PanelCommand
    data: bytes
    timestamp: float

class CP5200Protocol:
    """CP5200 Protocol Implementation"""
    
    # Protocol constants
    HEADER_SIZE = 8
    MAX_DATA_SIZE = 1024
    ACK_TIMEOUT = 3.0
    
    def __init__(self):
        self.sequence_number = 0
        self.lock = threading.Lock()
    
    def _get_sequence_number(self) -> int:
        """Get next sequence number"""
        with self.lock:
            self.sequence_number = (self.sequence_number + 1) % 256
            return self.sequence_number
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum for data"""
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum
    
    def build_header(self, command: PanelCommand, data_length: int) -> bytes:
        """Build message header"""
        seq = self._get_sequence_number()
        header = struct.pack('>BBHH', command.value, seq, data_length, 0)
        checksum = self._calculate_checksum(header)
        header = struct.pack('>BBHH', command.value, seq, data_length, checksum)
        return header
    
    def build_text_message(self, text: str, line: int = 1, position: int = 0) -> bytes:
        """Build text message for panel"""
        # Text format: [line][position][text]
        text_data = f"{line:02d}{position:02d}{text}".encode('utf-8')
        header = self.build_header(PanelCommand.SEND_TEXT, len(text_data))
        return header + text_data
    
    def build_occupancy_message(self, current: int, total: int, status: str = "") -> bytes:
        """Build occupancy display message"""
        # Format: "OCUPACION: XX/YY" or "OCUPACION: XX/YY - STATUS"
        if status:
            text = f"OCUPACION: {current:02d}/{total:02d} - {status}"
        else:
            text = f"OCUPACION: {current:02d}/{total:02d}"
        
        return self.build_text_message(text, line=1, position=0)
    
    def build_status_message(self, status: str) -> bytes:
        """Build status message"""
        return self.build_text_message(status, line=2, position=0)
    
    def build_clock_message(self, time_str: str) -> bytes:
        """Build clock message"""
        return self.build_text_message(time_str, line=3, position=0)
    
    def parse_response(self, response: bytes) -> Dict:
        """Parse panel response"""
        if len(response) < self.HEADER_SIZE:
            raise ValueError("Response too short")
        
        command, seq, data_length, checksum = struct.unpack('>BBHH', response[:self.HEADER_SIZE])
        
        # Verify checksum
        calculated_checksum = self._calculate_checksum(response[:6])
        if calculated_checksum != checksum:
            raise ValueError("Invalid checksum")
        
        data = response[self.HEADER_SIZE:self.HEADER_SIZE + data_length] if data_length > 0 else b''
        
        return {
            'command': command,
            'sequence': seq,
            'data_length': data_length,
            'data': data,
            'checksum': checksum
        }

class PanelConnection:
    """Panel Connection Manager"""
    
    def __init__(self, config: PanelConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.protocol = CP5200Protocol()
        self.status = PanelStatus.OFFLINE
        self.last_communication = 0
        self.lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
    
    def connect(self) -> bool:
        """Connect to panel"""
        try:
            with self.lock:
                if self.socket:
                    self.socket.close()
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.config.timeout)
                self.socket.connect((self.config.ip, self.config.port))
                
                self.status = PanelStatus.ONLINE
                self.last_communication = time.time()
                
                logger.info(f"Connected to panel {self.config.ip}:{self.config.port}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to panel {self.config.ip}:{self.config.port}: {e}")
            self.status = PanelStatus.ERROR
            return False
    
    def disconnect(self):
        """Disconnect from panel"""
        with self.lock:
            if self.socket:
                self.socket.close()
                self.socket = None
            self.status = PanelStatus.OFFLINE
            self.running = False
    
    def send_message(self, message: bytes) -> bool:
        """Send message to panel"""
        try:
            with self.lock:
                if not self.socket or self.status != PanelStatus.ONLINE:
                    if not self.connect():
                        return False
                
                self.socket.send(message)
                self.last_communication = time.time()
                
                # Wait for ACK
                try:
                    ack = self.socket.recv(1024)
                    if ack:
                        response = self.protocol.parse_response(ack)
                        logger.debug(f"Panel {self.config.ip} ACK: {response}")
                        return True
                except socket.timeout:
                    logger.warning(f"Panel {self.config.ip} ACK timeout")
                    return False
                
        except Exception as e:
            logger.error(f"Failed to send message to panel {self.config.ip}: {e}")
            self.status = PanelStatus.ERROR
            return False
    
    def send_text(self, text: str, line: int = 1, position: int = 0) -> bool:
        """Send text to panel"""
        message = self.protocol.build_text_message(text, line, position)
        return self.send_message(message)
    
    def send_occupancy(self, current: int, total: int, status: str = "") -> bool:
        """Send occupancy information to panel"""
        message = self.protocol.build_occupancy_message(current, total, status)
        return self.send_message(message)
    
    def send_status(self, status: str) -> bool:
        """Send status message to panel"""
        message = self.protocol.build_status_message(status)
        return self.send_message(message)
    
    def send_clock(self, time_str: str) -> bool:
        """Send clock information to panel"""
        message = self.protocol.build_clock_message(time_str)
        return self.send_message(message)
    
    def query_status(self) -> Optional[Dict]:
        """Query panel status"""
        try:
            header = self.protocol.build_header(PanelCommand.QUERY_STATUS, 0)
            if self.send_message(header):
                with self.lock:
                    if self.socket:
                        response = self.socket.recv(1024)
                        if response:
                            return self.protocol.parse_response(response)
        except Exception as e:
            logger.error(f"Failed to query panel {self.config.ip} status: {e}")
        return None
    
    def start_worker(self):
        """Start message processing worker"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Message processing worker loop"""
        while self.running:
            try:
                # Process queued messages
                try:
                    message = self.message_queue.get(timeout=1.0)
                    self.send_message(message)
                except queue.Empty:
                    pass
                
                # Periodic status check
                if time.time() - self.last_communication > 30:  # 30 seconds
                    if not self.query_status():
                        self.status = PanelStatus.OFFLINE
                
            except Exception as e:
                logger.error(f"Panel worker error for {self.config.ip}: {e}")
                time.sleep(1)
    
    def is_online(self) -> bool:
        """Check if panel is online"""
        return self.status == PanelStatus.ONLINE
    
    def get_status(self) -> Dict:
        """Get panel status information"""
        return {
            'ip': self.config.ip,
            'port': self.config.port,
            'panel_id': self.config.panel_id,
            'status': self.status.value,
            'last_communication': self.last_communication,
            'online': self.is_online()
        }

class PanelManager:
    """Panel Manager for multiple panels"""
    
    def __init__(self):
        self.panels: Dict[str, PanelConnection] = {}
        self.lock = threading.Lock()
    
    def add_panel(self, config: PanelConfig) -> PanelConnection:
        """Add panel to manager"""
        with self.lock:
            panel = PanelConnection(config)
            self.panels[config.ip] = panel
            panel.start_worker()
            return panel
    
    def remove_panel(self, ip: str):
        """Remove panel from manager"""
        with self.lock:
            if ip in self.panels:
                self.panels[ip].disconnect()
                del self.panels[ip]
    
    def get_panel(self, ip: str) -> Optional[PanelConnection]:
        """Get panel by IP"""
        return self.panels.get(ip)
    
    def send_to_panel(self, ip: str, message: bytes) -> bool:
        """Send message to specific panel"""
        panel = self.get_panel(ip)
        if panel:
            return panel.send_message(message)
        return False
    
    def send_text_to_panel(self, ip: str, text: str, line: int = 1, position: int = 0) -> bool:
        """Send text to specific panel"""
        panel = self.get_panel(ip)
        if panel:
            return panel.send_text(text, line, position)
        return False
    
    def send_occupancy_to_panel(self, ip: str, current: int, total: int, status: str = "") -> bool:
        """Send occupancy to specific panel"""
        panel = self.get_panel(ip)
        if panel:
            return panel.send_occupancy(current, total, status)
        return False
    
    def broadcast_occupancy(self, current: int, total: int, status: str = ""):
        """Broadcast occupancy to all panels"""
        for panel in self.panels.values():
            panel.send_occupancy(current, total, status)
    
    def get_all_status(self) -> List[Dict]:
        """Get status of all panels"""
        return [panel.get_status() for panel in self.panels.values()]
    
    def get_online_panels(self) -> List[str]:
        """Get list of online panel IPs"""
        return [ip for ip, panel in self.panels.items() if panel.is_online()]
    
    def shutdown(self):
        """Shutdown all panels"""
        for panel in self.panels.values():
            panel.disconnect()

# Global panel manager instance
panel_manager = PanelManager()

def init_panels_from_config(panel_configs: List[Dict]) -> PanelManager:
    """Initialize panels from configuration"""
    for config_data in panel_configs:
        config = PanelConfig(
            ip=config_data['ip'],
            port=config_data.get('port', 5000),
            panel_id=config_data.get('panel_id', 1),
            timeout=config_data.get('timeout', 5.0),
            retry_attempts=config_data.get('retry_attempts', 3),
            retry_delay=config_data.get('retry_delay', 1.0)
        )
        panel_manager.add_panel(config)
    
    return panel_manager

def update_parking_panels(parking_id: int, current_occupancy: int, total_spaces: int, status: str = ""):
    """Update all panels for a specific parking"""
    # This would be called when parking occupancy changes
    # For now, broadcast to all panels
    panel_manager.broadcast_occupancy(current_occupancy, total_spaces, status) 