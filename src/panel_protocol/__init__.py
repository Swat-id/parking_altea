"""
Panel Protocol Service v4.3.0
Servicio de bajo nivel para comunicación directa con paneles LED
"""

__version__ = "4.3.0"

from .panel_protocol_service import PanelProtocolService
from .connection_pool import ConnectionPool
from .task_queue import TaskQueue
from .result_storage import ResultStorage
from .api_server import PanelProtocolAPIServer
from .client import PanelProtocolClient, get_panel_protocol_client
from .constants import PANEL_PROTOCOL_SERVICE_PORT

# Módulos v4 para Panel Tipo 4 (16 ventanas)
from .protocol_v4 import (
    PanelProtocolV4,
    TextColor,
    FontSize,
    TextAlignment,
    TextEffect
)
from .backend_v4 import (
    PanelBackendV4,
    WindowMessage,
    SendResult,
    BatchResult,
    quick_send_v4,
    quick_send_all_v4
)

__all__ = [
    "PanelProtocolService",
    "PanelProtocolAPIServer",
    "PanelProtocolClient",
    "get_panel_protocol_client",
    "ConnectionPool",
    "TaskQueue",
    "ResultStorage",
    "PANEL_PROTOCOL_SERVICE_PORT",
    # v4 exports
    "PanelProtocolV4",
    "TextColor",
    "FontSize",
    "TextAlignment",
    "TextEffect",
    "PanelBackendV4",
    "WindowMessage",
    "SendResult",
    "BatchResult",
    "quick_send_v4",
    "quick_send_all_v4",
]

