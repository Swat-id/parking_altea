#!/usr/bin/env python3
"""
PanelSender Service - Servicio de gestión e integración de paneles informativos
Soporta protocolos nuevo (v1.4.7) y antiguo (v1.2.6)
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Importar los controladores de protocolos
from sender_newProtocol.panel_controller import NewProtocolController
from sender_oldProtocol.panel_controller import OldProtocolController

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('panelsender.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="PanelSender Service",
    description="Servicio de gestión e integración de paneles informativos con soporte para protocolos nuevo (v1.4.7) y antiguo (v1.2.6)",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para la API

class WindowRequest(BaseModel):
    """Modelo para solicitud de ventana"""
    id: int = Field(..., description="ID de la ventana (0 o 1)")
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (1=8px, 2=16px, 3=24px, 4=32px)")
    effect: Union[str, int] = Field("fijo", description="Efecto (fijo/scroll o número de efecto)")
    stayTime: int = Field(50, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    protocol: str = Field(None, description="Protocolo a usar (new/old). Se rellena automáticamente desde PanelRequest.")

    def get_effect_and_speed(self, protocol: str = "new") -> tuple[int, int]:
        """Obtener el código de efecto y velocidad según el tipo de efecto y protocolo"""
        if isinstance(self.effect, int):
            # Permitir efecto numérico personalizado
            return self.effect, self.speed if hasattr(self, 'speed') else 5
        effect_str = self.effect.lower() if isinstance(self.effect, str) else str(self.effect)
        if protocol == "old":
            if effect_str == "scroll":
                return 12, self.stayTime if self.stayTime else 5
            elif effect_str == "fijo":
                return 2, 0
            else:
                raise ValueError(f"Efecto no soportado en protocolo antiguo: {self.effect}. Use 'fijo', 'scroll' o un número de efecto")
        else:
            # Protocolo nuevo - códigos según SDK v1.4.7
            # 1 = Instant (fijo), 2 = Scroll_left, 55 = Scrollleft_continuously, 56 = Scroll_right_continuously
            if effect_str == "scroll":
                return 2, self.stayTime if self.stayTime else 5  # Scroll_left = 2
            elif effect_str == "scroll_left":
                return 2, self.stayTime if self.stayTime else 5  # Scroll_left = 2
            elif effect_str == "scroll_continuously" or effect_str == "scroll_left_continuously":
                return 55, self.stayTime if self.stayTime else 5  # Scrollleft_continuously = 55
            elif effect_str == "scroll_right":
                return 3, self.stayTime if self.stayTime else 5  # Scroll_right = 3
            elif effect_str == "scroll_right_continuously":
                return 56, self.stayTime if self.stayTime else 5  # Scroll_right_continuously = 56
            elif effect_str == "fijo":
                return 1, 0  # Instant = 1 (CORREGIDO: era 0 = Random)
            else:
                raise ValueError(f"Efecto no soportado: {self.effect}. Use 'fijo', 'scroll', 'scroll_left', 'scroll_right', 'scroll_left_continuously', 'scroll_right_continuously' o un número de efecto")

class PanelRequest(BaseModel):
    """Modelo para solicitud de panel"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    protocol: str = Field("new", description="Protocolo a usar (new/old)")
    windows: List[WindowRequest] = Field(..., description="Lista de ventanas a actualizar")

class SendOptions(BaseModel):
    """Opciones de envío"""
    sequential: bool = Field(False, description="Envío secuencial")
    timeout: int = Field(30000, description="Timeout en ms")
    retryAttempts: int = Field(3, description="Intentos de reintento")

class SendRequest(BaseModel):
    """Modelo para solicitud de envío"""
    panels: List[PanelRequest] = Field(..., description="Lista de paneles")
    options: Optional[SendOptions] = Field(None, description="Opciones de envío")

class WindowResult(BaseModel):
    """Resultado de ventana"""
    id: int
    success: bool
    message: str
    errorMessage: Optional[str] = None

class PanelResult(BaseModel):
    """Resultado de panel"""
    ip: str
    success: bool
    windows: List[WindowResult]
    errorMessage: Optional[str] = None

class SendResponse(BaseModel):
    """Respuesta de envío"""
    success: bool
    message: str
    data: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    """Respuesta de health check"""
    status: str
    timestamp: str
    version: str
    protocols: Dict[str, bool]

# Modelos para endpoints específicos de protocolos
class OldProtocolWindowRequest(BaseModel):
    """Modelo para solicitud de ventana con protocolo antiguo"""
    id: int = Field(..., description="ID de la ventana (0 o 1)")
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (1=8px, 2=16px, 3=24px, 4=32px)")
    effect: str = Field("fijo", description="Efecto (fijo/scroll)")
    stayTime: int = Field(50, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    speed: int = Field(5, description="Velocidad para efectos de scroll")

    def get_effect_and_speed(self, protocol: str = "old") -> tuple[int, int]:
        """Obtener el código de efecto y velocidad según el tipo de efecto y protocolo"""
        if self.effect.lower() == "scroll":
            # Para scroll, permitir stayTime 5 o 10, pero ajustar si es necesario
            if self.stayTime not in [5, 10]:
                # Ajustar al valor más cercano
                adjusted_stayTime = 5 if self.stayTime < 5 else 10
                return 12, adjusted_stayTime
            return 12, self.stayTime
        elif self.effect.lower() == "fijo":
            # Para fijo, siempre usar stayTime=0 en protocolo antiguo
            return 2, 0
        else:
            raise ValueError(f"Efecto no soportado en protocolo antiguo: {self.effect}. Use 'fijo' o 'scroll'")

class NewProtocolWindowRequest(BaseModel):
    """Modelo para solicitud de ventana con protocolo nuevo"""
    id: int = Field(..., description="ID de la ventana (0 o 1)")
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (0-7 para protocolo nuevo)")
    effect: Union[str, int] = Field("fijo", description="Efecto (fijo/scroll o nombre de efecto específico)")
    stayTime: int = Field(50, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    speed: int = Field(5, description="Velocidad para efectos de scroll")

    def get_effect_and_speed(self, protocol: str = "new") -> tuple[int, int]:
        """Obtener el código de efecto y velocidad según el tipo de efecto y protocolo"""
        if isinstance(self.effect, int):
            # Permitir efecto numérico personalizado
            return self.effect, self.speed
        effect_str = self.effect.lower() if isinstance(self.effect, str) else str(self.effect)
        # Protocolo nuevo - códigos según SDK v1.4.7
        # 1 = Instant (fijo), 2 = Scroll_left, 55 = Scrollleft_continuously, 56 = Scroll_right_continuously
        if effect_str == "scroll":
            return 2, self.speed  # Scroll_left = 2
        elif effect_str == "scroll_left":
            return 2, self.speed  # Scroll_left = 2
        elif effect_str == "scroll_continuously" or effect_str == "scroll_left_continuously":
            return 55, self.speed  # Scrollleft_continuously = 55
        elif effect_str == "scroll_right":
            return 3, self.speed  # Scroll_right = 3
        elif effect_str == "scroll_right_continuously":
            return 56, self.speed  # Scroll_right_continuously = 56
        elif effect_str == "fijo":
            return 1, 0  # Instant = 1 (CORREGIDO: era 0 = Random)
        else:
            # Por defecto usar efecto Instant si no se reconoce
            return 1, self.speed

class NewProtocolNumericWindowRequest(BaseModel):
    """Modelo para solicitud de ventana con protocolo nuevo usando parámetros numéricos directos"""
    id: int = Field(..., description="ID de la ventana (0 o 1)")
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (valor numérico directo)")
    effect: int = Field(2, description="Código de efecto numérico directo")
    stayTime: int = Field(100, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    speed: int = Field(5, description="Velocidad para efectos de scroll")

class OldProtocolPanelRequest(BaseModel):
    """Modelo para solicitud de panel con protocolo antiguo"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    windows: List[OldProtocolWindowRequest] = Field(..., description="Lista de ventanas a actualizar")

class NewProtocolPanelRequest(BaseModel):
    """Modelo para solicitud de panel con protocolo nuevo"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    panel_type: str = Field("single", description="Tipo de panel (single/dual)")
    windows: List[NewProtocolWindowRequest] = Field(..., description="Lista de ventanas a actualizar")

class NewProtocolNumericPanelRequest(BaseModel):
    """Modelo para solicitud de panel con protocolo nuevo usando parámetros numéricos directos"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    panel_type: str = Field("single", description="Tipo de panel (single/dual)")
    windows: List[NewProtocolNumericWindowRequest] = Field(..., description="Lista de ventanas a actualizar")

class OldProtocolRequest(BaseModel):
    """Modelo para solicitud de protocolo antiguo"""
    panels: List[OldProtocolPanelRequest] = Field(..., description="Lista de paneles con ventanas")

class NewProtocolRequest(BaseModel):
    """Modelo para solicitud de protocolo nuevo"""
    panels: List[NewProtocolPanelRequest] = Field(..., description="Lista de paneles con ventanas")

class NewProtocolNumericRequest(BaseModel):
    """Modelo para solicitud de protocolo nuevo con parámetros numéricos directos"""
    panels: List[NewProtocolNumericPanelRequest] = Field(..., description="Lista de paneles con ventanas")

# Nuevos modelos para endpoints específicos
class OldProtocolSingleWindowRequest(BaseModel):
    """Modelo para solicitud de ventana única con protocolo antiguo"""
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (1=8px, 2=16px, 3=24px, 4=32px)")
    effect: str = Field("fijo", description="Efecto (fijo/scroll)")
    stayTime: int = Field(50, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    speed: int = Field(5, description="Velocidad para efectos de scroll")
    
    def get_effect_and_speed(self, protocol: str = "old") -> tuple[int, int]:
        """Obtener código de efecto y velocidad según protocolo"""
        if self.effect.lower() == "fijo":
            return 2, self.speed  # Código 2 para efecto fijo en protocolo antiguo
        elif self.effect.lower() == "scroll":
            return 12, self.speed  # Código 12 para efecto scroll en protocolo antiguo
        else:
            return 2, self.speed  # Por defecto efecto fijo

class OldProtocolSinglePanelRequest(BaseModel):
    """Modelo para solicitud de panel único con protocolo antiguo"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    window: OldProtocolSingleWindowRequest = Field(..., description="Ventana única a actualizar")

class NewProtocolSingleWindowRequest(BaseModel):
    """Modelo para solicitud de ventana única con protocolo nuevo"""
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (0-7 para protocolo nuevo)")
    effect: Union[str, int] = Field("fijo", description="Efecto (fijo/scroll o nombre de efecto específico)")
    stayTime: int = Field(50, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    speed: int = Field(5, description="Velocidad para efectos de scroll")
    
    def get_effect_and_speed(self, protocol: str = "new") -> tuple[int, int]:
        """Obtener código de efecto y velocidad según protocolo - SDK v1.4.7"""
        if isinstance(self.effect, int):
            return self.effect, self.speed
        effect_str = self.effect.lower()
        # 1 = Instant (fijo), 2 = Scroll_left, 55 = Scrollleft_continuously, 56 = Scroll_right_continuously
        if effect_str == "fijo":
            return 1, self.speed  # Instant = 1 (CORREGIDO)
        elif effect_str == "scroll" or effect_str == "scroll_left":
            return 2, self.speed  # Scroll_left = 2
        elif effect_str == "scroll_continuously" or effect_str == "scroll_left_continuously":
            return 55, self.speed  # Scrollleft_continuously = 55
        elif effect_str == "scroll_right":
            return 3, self.speed  # Scroll_right = 3
        elif effect_str == "scroll_right_continuously":
            return 56, self.speed  # Scroll_right_continuously = 56
        else:
            return 1, self.speed  # Por defecto Instant

class NewProtocolSinglePanelRequest(BaseModel):
    """Modelo para solicitud de panel único con protocolo nuevo (pantalla completa)"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    window: NewProtocolSingleWindowRequest = Field(..., description="Ventana única a actualizar")

class NewProtocolDualWindowRequest(BaseModel):
    """Modelo para solicitud de ventana dual con protocolo nuevo"""
    id: int = Field(..., description="ID de la ventana (0=izquierda, 1=derecha)")
    text: str = Field(..., description="Texto a mostrar")
    color: int = Field(1, description="Color del texto (1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco)")
    fontSize: int = Field(2, description="Tamaño de fuente (0-7 para protocolo nuevo)")
    effect: Union[str, int] = Field("fijo", description="Efecto (fijo/scroll o nombre de efecto específico)")
    stayTime: int = Field(50, description="Tiempo de permanencia (ms)")
    alignmentH: int = Field(0, description="Alineación horizontal (0=Izq, 1=Centro, 2=Der) - Por defecto izquierda")
    alignmentV: int = Field(0, description="Alineación vertical (0=Arriba, 1=Centro, 2=Abajo)")
    speed: int = Field(5, description="Velocidad para efectos de scroll")
    
    def get_effect_and_speed(self, protocol: str = "new") -> tuple[int, int]:
        """Obtener código de efecto y velocidad según protocolo - SDK v1.4.7"""
        if isinstance(self.effect, int):
            return self.effect, self.speed
        effect_str = self.effect.lower()
        # 1 = Instant (fijo), 2 = Scroll_left, 55 = Scrollleft_continuously, 56 = Scroll_right_continuously
        if effect_str == "fijo":
            return 1, self.speed  # Instant = 1 (CORREGIDO)
        elif effect_str == "scroll" or effect_str == "scroll_left":
            return 2, self.speed  # Scroll_left = 2
        elif effect_str == "scroll_continuously" or effect_str == "scroll_left_continuously":
            return 55, self.speed  # Scrollleft_continuously = 55
        elif effect_str == "scroll_right":
            return 3, self.speed  # Scroll_right = 3
        elif effect_str == "scroll_right_continuously":
            return 56, self.speed  # Scroll_right_continuously = 56
        else:
            return 1, self.speed  # Por defecto Instant

class NewProtocolDualPanelRequest(BaseModel):
    """Modelo para solicitud de panel dual con protocolo nuevo (dos ventanas)"""
    ip: str = Field(..., description="IP del panel")
    port: int = Field(5200, description="Puerto del panel")
    windows: List[NewProtocolDualWindowRequest] = Field(..., description="Lista de ventanas (debe ser exactamente 2)")

# Modelos de request para los nuevos endpoints
class OldProtocolSingleRequest(BaseModel):
    """Modelo para solicitud de protocolo antiguo single"""
    panel: OldProtocolSinglePanelRequest = Field(..., description="Panel único con ventana única")

class NewProtocolSingleRequest(BaseModel):
    """Modelo para solicitud de protocolo nuevo single"""
    panel: NewProtocolSinglePanelRequest = Field(..., description="Panel único con ventana única")

class NewProtocolDualRequest(BaseModel):
    """Modelo para solicitud de protocolo nuevo dual"""
    panel: NewProtocolDualPanelRequest = Field(..., description="Panel único con dos ventanas")

# Controladores de protocolos
new_protocol_controller = None
old_protocol_controller = None

@app.on_event("startup")
async def startup_event():
    """Inicializar controladores al arrancar"""
    global new_protocol_controller, old_protocol_controller
    
    logger.info("Iniciando PanelSender Service...")
    
    try:
        # Inicializar controlador de protocolo nuevo
        new_protocol_controller = NewProtocolController()
        await new_protocol_controller.initialize()
        logger.info("Controlador de protocolo nuevo inicializado")
    except Exception as e:
        logger.error(f"Error inicializando protocolo nuevo: {e}")
        new_protocol_controller = None
    
    try:
        # Inicializar controlador de protocolo antiguo
        old_protocol_controller = OldProtocolController()
        await old_protocol_controller.initialize()
        logger.info("Controlador de protocolo antiguo inicializado")
    except Exception as e:
        logger.error(f"Error inicializando protocolo antiguo: {e}")
        old_protocol_controller = None

@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar"""
    logger.info("Cerrando PanelSender Service...")
    
    if new_protocol_controller:
        await new_protocol_controller.shutdown()
    
    if old_protocol_controller:
        await old_protocol_controller.shutdown()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de health check"""
    return HealthResponse(
        status="running",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        protocols={
            "new": new_protocol_controller is not None,
            "old": old_protocol_controller is not None
        }
    )

@app.post("/api/v1/panels/send", response_model=SendResponse)
async def send_to_panels(request: SendRequest):
    """Endpoint principal para enviar contenido a paneles"""
    try:
        logger.info(f"Recibida solicitud para {len(request.panels)} paneles")
        
        results = []
        total_panels = len(request.panels)
        total_windows = sum(len(panel.windows) for panel in request.panels)
        
        # Procesar cada panel
        for panel_request in request.panels:
            panel_result = await process_panel(panel_request)
            results.append(panel_result)
        
        # Determinar éxito general
        all_success = all(result.success for result in results)
        message = "Comandos enviados correctamente" if all_success else "Algunos comandos fallaron"
        
        return SendResponse(
            success=all_success,
            message=message,
            data={
                "totalPanels": total_panels,
                "totalWindows": total_windows,
                "results": [result.dict() for result in results]
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error procesando solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_panel(panel_request: PanelRequest) -> PanelResult:
    """Procesar un panel específico"""
    try:
        logger.info(f"Procesando panel {panel_request.ip} usando protocolo: {panel_request.protocol}")
        if panel_request.protocol.lower() == "new":
            if not new_protocol_controller:
                raise Exception("Controlador de protocolo nuevo no disponible")
            controller = new_protocol_controller
        elif panel_request.protocol.lower() == "old":
            if not old_protocol_controller:
                raise Exception("Controlador de protocolo antiguo no disponible")
            controller = old_protocol_controller
        else:
            raise Exception(f"Protocolo no soportado: {panel_request.protocol}")
        window_results = []
        for window_request in panel_request.windows:
            try:
                logger.info(f"Enviando a ventana {window_request.id} del panel {panel_request.ip} con parámetros: texto='{window_request.text}', color={window_request.color}, fontSize={window_request.fontSize}, effect={window_request.effect}, stayTime={window_request.stayTime}, alignmentH={window_request.alignmentH}, alignmentV={window_request.alignmentV}")
                
                # Ajustar parámetros según protocolo para compatibilidad
                adjusted_stayTime = window_request.stayTime
                if panel_request.protocol.lower() == "old" and window_request.effect.lower() == "fijo":
                    if window_request.stayTime != 0:
                        logger.info(f"Ajustando stayTime de {window_request.stayTime} a 0 para protocolo antiguo con efecto fijo")
                        adjusted_stayTime = 0
                
                # Validar y obtener efecto y velocidad según protocolo
                effect_code, speed = window_request.get_effect_and_speed(panel_request.protocol.lower())
                
                # Para el protocolo nuevo, usar panel_type explícito o inferir basado en window_id
                # Para el protocolo antiguo, siempre es single (una ventana)
                if panel_request.protocol.lower() == "new":
                    # Determinar panel_type basado en window_id y número de ventanas
                    # Si hay window_id > 0 o múltiples ventanas, es dual
                    # Si solo hay window_id = 0, es single
                    panel_type = "dual" if (window_request.id > 0 or len(panel_request.windows) > 1) else "single"
                    
                    result = await controller.send_text(
                        ip=panel_request.ip,
                        port=panel_request.port,
                        window_id=window_request.id,
                        text=window_request.text,
                        color=window_request.color,
                        fontSize=window_request.fontSize,
                        speed=speed,
                        effect=effect_code,
                        stayTime=adjusted_stayTime,
                        alignmentH=window_request.alignmentH,
                        alignmentV=window_request.alignmentV,
                        panel_type=panel_type
                    )
                else:
                    # Protocolo antiguo no tiene panel_type
                    result = await controller.send_text(
                        ip=panel_request.ip,
                        port=panel_request.port,
                        window_id=window_request.id,
                        text=window_request.text,
                        color=window_request.color,
                        fontSize=window_request.fontSize,
                        speed=speed,
                        effect=effect_code,
                        stayTime=adjusted_stayTime,
                        alignmentH=window_request.alignmentH,
                        alignmentV=window_request.alignmentV
                    )
                
                window_results.append(WindowResult(
                    id=window_request.id,
                    success=result.get("success", False),
                    message=result.get("message", "Operación completada"),
                    errorMessage=result.get("error")
                ))
            except Exception as e:
                logger.error(f"Error enviando a ventana {window_request.id}: {e}")
                window_results.append(WindowResult(
                    id=window_request.id,
                    success=False,
                    message="Error enviando contenido",
                    errorMessage=str(e)
                ))
        panel_success = all(w.success for w in window_results)
        return PanelResult(
            ip=panel_request.ip,
            success=panel_success,
            windows=window_results,
            errorMessage=None if panel_success else "Algunas ventanas fallaron"
        )
    except Exception as e:
        logger.error(f"Error procesando panel {panel_request.ip}: {e}")
        return PanelResult(
            ip=panel_request.ip,
            success=False,
            windows=[],
            errorMessage=str(e)
        )

@app.get("/api/v1/panels/list")
async def list_panels():
    """
    Listar paneles disponibles con sus configuraciones
    """
    return {
        "panels": [
            {
                "ip": "192.168.1.221", 
                "port": 5200,
                "protocol": "new",
                "description": "Panel 1 - 1 línea, 2 ventanas (32x16 cada una)",
                "windows": [
                    {"id": 0, "coordinates": [0, 0, 32, 16], "description": "Ventana Izquierda"},
                    {"id": 1, "coordinates": [32, 0, 32, 16], "description": "Ventana Derecha"}
                ]
            },
            {
                "ip": "192.168.1.222", 
                "port": 5200,
                "protocol": "new",
                "description": "Panel 2 - 1 línea, 2 ventanas (32x16 cada una)",
                "windows": [
                    {"id": 0, "coordinates": [0, 0, 32, 16], "description": "Ventana Izquierda"},
                    {"id": 1, "coordinates": [32, 0, 32, 16], "description": "Ventana Derecha"}
                ]
            },
            {
                "ip": "192.168.1.223",
                "port": 5200, 
                "protocol": "new",
                "description": "Panel 3 - 1 línea, 1 ventana (128x16)",
                "windows": [
                    {"id": 0, "coordinates": [0, 0, 128, 16], "description": "Ventana Completa"}
                ]
            },
            {
                "ip": "192.168.1.224",
                "port": 5200,
                "protocol": "old", 
                "description": "Panel 4 - Protocolo antiguo",
                "windows": [
                    {"id": 0, "coordinates": [0, 0, 64, 16], "description": "Ventana Completa"}
                ]
            }
        ]
    }

@app.get("/api/v1/panels/effects/new-protocol")
async def get_new_protocol_effects():
    """
    Obtener todos los efectos disponibles para el protocolo nuevo (v1.4.7)
    """
    try:
        if not new_protocol_controller:
            raise HTTPException(status_code=500, detail="Controlador de protocolo nuevo no disponible")
        
        result = await new_protocol_controller.get_available_effects()
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Error obteniendo efectos: {result.get('error', 'Error desconocido')}"
            )
            
    except Exception as e:
        logger.error(f"Error en get_new_protocol_effects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/panels/send-old-protocol")
async def send_text_old_protocol(request: OldProtocolRequest):
    """
    Enviar texto usando protocolo antiguo (v1.2.6) con parámetros completos
    """
    logger.info(f"Recibida solicitud para protocolo antiguo: {len(request.panels)} paneles")
    
    results = []
    total_panels = 0
    total_windows = 0
    
    for panel in request.panels:
        total_panels += 1
        panel_result = {
            "ip": panel.ip,
            "success": False,
            "windows": [],
            "errorMessage": None
        }
        
        try:
            logger.info(f"Procesando panel {panel.ip} usando protocolo: old")
            
            for window in panel.windows:
                total_windows += 1
                logger.info(f"Enviando a ventana {window.id} del panel {panel.ip} con parámetros: texto='{window.text}', color={window.color}, fontSize={window.fontSize}, effect={window.effect}, stayTime={window.stayTime}, alignmentH={window.alignmentH}, alignmentV={window.alignmentV}")
                
                # Validar y obtener efecto y velocidad según protocolo
                effect_code, speed = window.get_effect_and_speed("old")
                
                result = await old_protocol_controller.send_text(
                    ip=panel.ip,
                    port=panel.port,
                    window_id=window.id,
                    text=window.text,
                    color=window.color,
                    fontSize=window.fontSize,
                    speed=speed,
                    effect=effect_code,
                    stayTime=window.stayTime,
                    alignmentH=window.alignmentH,
                    alignmentV=window.alignmentV
                )
                
                window_result = {
                    "id": window.id,
                    "success": result.get("success", False),
                    "message": result.get("message", "Error desconocido"),
                    "errorMessage": result.get("error")
                }
                panel_result["windows"].append(window_result)
            
            # Determinar si el panel fue exitoso
            panel_result["success"] = all(w["success"] for w in panel_result["windows"])
            if not panel_result["success"]:
                panel_result["errorMessage"] = "Algunas ventanas fallaron"
                
        except Exception as e:
            logger.error(f"Error procesando panel {panel.ip}: {e}")
            panel_result["errorMessage"] = str(e)
        
        results.append(panel_result)
    
    # Determinar éxito general
    all_success = all(r["success"] for r in results)
    
    return {
        "success": all_success,
        "message": "Comandos enviados correctamente" if all_success else "Algunos comandos fallaron",
        "data": {
            "totalPanels": total_panels,
            "totalWindows": total_windows,
            "results": results
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/panels/send-new-protocol")
async def send_text_new_protocol(request: NewProtocolRequest):
    """
    Enviar texto usando protocolo nuevo (v1.4.7) con parámetros completos
    """
    logger.info(f"Recibida solicitud para protocolo nuevo: {len(request.panels)} paneles")
    
    results = []
    total_panels = 0
    total_windows = 0
    
    for panel in request.panels:
        total_panels += 1
        panel_result = {
            "ip": panel.ip,
            "success": False,
            "windows": [],
            "errorMessage": None
        }
        
        try:
            logger.info(f"Procesando panel {panel.ip} usando protocolo: new")
            
            for window in panel.windows:
                total_windows += 1
                logger.info(f"Enviando a ventana {window.id} del panel {panel.ip} con parámetros: texto='{window.text}', color={window.color}, fontSize={window.fontSize}, effect={window.effect}, stayTime={window.stayTime}, alignmentH={window.alignmentH}, alignmentV={window.alignmentV}")
                
                # Validar y obtener efecto y velocidad según protocolo
                effect_code, speed = window.get_effect_and_speed("new")
                
                result = await new_protocol_controller.send_text(
                    ip=panel.ip,
                    port=panel.port,
                    window_id=window.id,
                    text=window.text,
                    color=window.color,
                    fontSize=window.fontSize,
                    speed=speed,
                    effect=effect_code,
                    stayTime=window.stayTime,
                    alignmentH=window.alignmentH,
                    alignmentV=window.alignmentV,
                    panel_type=panel.panel_type
                )
                
                window_result = {
                    "id": window.id,
                    "success": result.get("success", False),
                    "message": result.get("message", "Error desconocido"),
                    "errorMessage": result.get("error")
                }
                panel_result["windows"].append(window_result)
            
            # Determinar si el panel fue exitoso
            panel_result["success"] = all(w["success"] for w in panel_result["windows"])
            if not panel_result["success"]:
                panel_result["errorMessage"] = "Algunas ventanas fallaron"
                
        except Exception as e:
            logger.error(f"Error procesando panel {panel.ip}: {e}")
            panel_result["errorMessage"] = str(e)
        
        results.append(panel_result)
    
    # Determinar éxito general
    all_success = all(r["success"] for r in results)
    
    return {
        "success": all_success,
        "message": "Comandos enviados correctamente" if all_success else "Algunos comandos fallaron",
        "data": {
            "totalPanels": total_panels,
            "totalWindows": total_windows,
            "results": results
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/panels/send-new-protocol-numeric")
async def send_text_new_protocol_numeric(request: NewProtocolNumericRequest):
    """
    Enviar texto usando protocolo nuevo (v1.4.7) con parámetros numéricos directos
    """
    logger.info(f"Recibida solicitud para protocolo nuevo con parámetros numéricos: {len(request.panels)} paneles")
    
    results = []
    total_panels = 0
    total_windows = 0
    
    for panel in request.panels:
        total_panels += 1
        panel_result = {
            "ip": panel.ip,
            "success": False,
            "windows": [],
            "errorMessage": None
        }
        
        try:
            logger.info(f"Procesando panel {panel.ip} usando protocolo: new (numérico)")
            
            for window in panel.windows:
                total_windows += 1
                logger.info(f"Enviando a ventana {window.id} del panel {panel.ip} con parámetros numéricos: texto='{window.text}', color={window.color}, fontSize={window.fontSize}, effect={window.effect}, stayTime={window.stayTime}, alignmentH={window.alignmentH}, alignmentV={window.alignmentV}")
                
                result = await new_protocol_controller.send_text_numeric(
                    ip=panel.ip,
                    port=panel.port,
                    window_id=window.id,
                    text=window.text,
                    color=window.color,
                    fontSize=window.fontSize,
                    speed=window.speed,
                    effect=window.effect,
                    stayTime=window.stayTime,
                    alignmentH=window.alignmentH,
                    alignmentV=window.alignmentV,
                    panel_type=panel.panel_type
                )
                
                window_result = {
                    "id": window.id,
                    "success": result.get("success", False),
                    "message": result.get("message", "Error desconocido"),
                    "errorMessage": result.get("error")
                }
                panel_result["windows"].append(window_result)
            
            # Determinar si el panel fue exitoso
            panel_result["success"] = all(w["success"] for w in panel_result["windows"])
            if not panel_result["success"]:
                panel_result["errorMessage"] = "Algunas ventanas fallaron"
                
        except Exception as e:
            logger.error(f"Error procesando panel {panel.ip}: {e}")
            panel_result["errorMessage"] = str(e)
        
        results.append(panel_result)
    
    # Determinar éxito general
    all_success = all(r["success"] for r in results)
    
    return {
        "success": all_success,
        "message": "Comandos enviados correctamente" if all_success else "Algunos comandos fallaron",
        "data": {
            "totalPanels": total_panels,
            "totalWindows": total_windows,
            "results": results
        },
        "timestamp": datetime.now().isoformat()
    }

# Nuevos endpoints específicos
@app.post("/api/v1/panels/send-old-protocol-single")
async def send_text_old_protocol_single(request: OldProtocolSingleRequest):
    """
    Enviar texto usando protocolo antiguo (v1.2.6) a una ventana única (64x16)
    """
    logger.info(f"Recibida solicitud para protocolo antiguo single: {request.panel.ip}")
    
    try:
        # Validar y obtener efecto y velocidad
        effect_code, speed = request.panel.window.get_effect_and_speed("old")
        
        # Ajustar parámetros según protocolo para compatibilidad
        adjusted_stayTime = request.panel.window.stayTime
        if request.panel.window.effect.lower() == "fijo":
            if request.panel.window.stayTime != 0:
                logger.info(f"Ajustando stayTime de {request.panel.window.stayTime} a 0 para protocolo antiguo con efecto fijo")
                adjusted_stayTime = 0
        
        logger.info(f"Enviando a panel {request.panel.ip} con protocolo antiguo: texto='{request.panel.window.text}', color={request.panel.window.color}, fontSize={request.panel.window.fontSize}, effect={request.panel.window.effect}, stayTime={adjusted_stayTime}")
        
        result = await old_protocol_controller.send_text(
            ip=request.panel.ip,
            port=request.panel.port,
            window_id=0,  # Protocolo antiguo siempre usa ventana 0
            text=request.panel.window.text,
            color=request.panel.window.color,
            fontSize=request.panel.window.fontSize,
            speed=speed,
            effect=effect_code,
            stayTime=adjusted_stayTime,
            alignmentH=request.panel.window.alignmentH,
            alignmentV=request.panel.window.alignmentV
        )
        
        return SendResponse(
            success=result.get("success", False),
            message=result.get("message", "Error desconocido"),
            data={
                "totalPanels": 1,
                "totalWindows": 1,
                "results": [{
                    "ip": request.panel.ip,
                    "success": result.get("success", False),
                    "windows": [{
                        "id": 0,
                        "success": result.get("success", False),
                        "message": result.get("message", "Error desconocido"),
                        "errorMessage": result.get("error")
                    }],
                    "errorMessage": result.get("error")
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"Error en send_text_old_protocol_single: {e}")
        return SendResponse(
            success=False,
            message="Error en send_text_old_protocol_single",
            data={
                "totalPanels": 1,
                "totalWindows": 1,
                "results": [{
                    "ip": request.panel.ip,
                    "success": False,
                    "windows": [{
                        "id": 0,
                        "success": False,
                        "message": "Error en send_text_old_protocol_single",
                        "errorMessage": str(e)
                    }],
                    "errorMessage": str(e)
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )

@app.post("/api/v1/panels/send-new-protocol-single")
async def send_text_new_protocol_single(request: NewProtocolSingleRequest):
    """
    Enviar texto usando protocolo nuevo (v1.4.7) a una ventana única (64x16, sin dividir)
    """
    logger.info(f"Recibida solicitud para protocolo nuevo single: {request.panel.ip}")
    
    try:
        # Validar y obtener efecto y velocidad
        effect_code, speed = request.panel.window.get_effect_and_speed("new")
        
        logger.info(f"Enviando a panel {request.panel.ip} con protocolo nuevo single: texto='{request.panel.window.text}', color={request.panel.window.color}, fontSize={request.panel.window.fontSize}, effect={request.panel.window.effect}, stayTime={request.panel.window.stayTime}")
        
        result = await new_protocol_controller.send_text(
            ip=request.panel.ip,
            port=request.panel.port,
            window_id=0,  # Siempre ventana 0 para pantalla única
            text=request.panel.window.text,
            color=request.panel.window.color,
            fontSize=request.panel.window.fontSize,
            speed=speed,
            effect=effect_code,
            stayTime=request.panel.window.stayTime,
            alignmentH=request.panel.window.alignmentH,
            alignmentV=request.panel.window.alignmentV,
            panel_type="single"  # Forzar tipo single
        )
        
        return SendResponse(
            success=result.get("success", False),
            message=result.get("message", "Error desconocido"),
            data={
                "totalPanels": 1,
                "totalWindows": 1,
                "results": [{
                    "ip": request.panel.ip,
                    "success": result.get("success", False),
                    "windows": [{
                        "id": 0,
                        "success": result.get("success", False),
                        "message": result.get("message", "Error desconocido"),
                        "errorMessage": result.get("error")
                    }],
                    "errorMessage": result.get("error")
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"Error en send_text_new_protocol_single: {e}")
        return SendResponse(
            success=False,
            message="Error en send_text_new_protocol_single",
            data={
                "totalPanels": 1,
                "totalWindows": 1,
                "results": [{
                    "ip": request.panel.ip,
                    "success": False,
                    "windows": [{
                        "id": 0,
                        "success": False,
                        "message": "Error en send_text_new_protocol_single",
                        "errorMessage": str(e)
                    }],
                    "errorMessage": str(e)
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )

@app.post("/api/v1/panels/send-new-protocol-dual")
async def send_text_new_protocol_dual(request: NewProtocolDualRequest):
    """
    Enviar texto usando protocolo nuevo (v1.4.7) a dos ventanas separadas (32x16 cada una)
    """
    logger.info(f"Recibida solicitud para protocolo nuevo dual: {request.panel.ip}")
    
    # Validar que hay exactamente 2 ventanas
    if len(request.panel.windows) != 2:
        return SendResponse(
            success=False,
            message="El endpoint dual requiere exactamente 2 ventanas",
            data={
                "totalPanels": 1,
                "totalWindows": len(request.panel.windows),
                "results": [{
                    "ip": request.panel.ip,
                    "success": False,
                    "windows": [],
                    "errorMessage": f"Se requieren exactamente 2 ventanas, se proporcionaron {len(request.panel.windows)}"
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
    
    try:
        window_results = []
        
        for window in request.panel.windows:
            # Validar que el ID de ventana sea 0 o 1
            if window.id not in [0, 1]:
                return SendResponse(
                    success=False,
                    message="Los IDs de ventana deben ser 0 o 1",
                    data={
                        "totalPanels": 1,
                        "totalWindows": 2,
                        "results": [{
                            "ip": request.panel.ip,
                            "success": False,
                            "windows": [],
                            "errorMessage": f"ID de ventana inválido: {window.id}. Debe ser 0 o 1"
                        }]
                    },
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
                )
            
            # Validar y obtener efecto y velocidad
            effect_code, speed = window.get_effect_and_speed("new")
            
            logger.info(f"Enviando a ventana {window.id} del panel {request.panel.ip} con protocolo nuevo dual: texto='{window.text}', color={window.color}, fontSize={window.fontSize}, effect={window.effect}, stayTime={window.stayTime}")
            
            result = await new_protocol_controller.send_text(
                ip=request.panel.ip,
                port=request.panel.port,
                window_id=window.id,
                text=window.text,
                color=window.color,
                fontSize=window.fontSize,
                speed=speed,
                effect=effect_code,
                stayTime=window.stayTime,
                alignmentH=window.alignmentH,
                alignmentV=window.alignmentV,
                panel_type="dual"  # Forzar tipo dual
            )
            
            window_results.append({
                "id": window.id,
                "success": result.get("success", False),
                "message": result.get("message", "Error desconocido"),
                "errorMessage": result.get("error")
            })
        
        # Determinar éxito general
        all_success = all(w["success"] for w in window_results)
        
        return SendResponse(
            success=all_success,
            message="Comandos enviados correctamente" if all_success else "Algunos comandos fallaron",
            data={
                "totalPanels": 1,
                "totalWindows": 2,
                "results": [{
                    "ip": request.panel.ip,
                    "success": all_success,
                    "windows": window_results,
                    "errorMessage": None if all_success else "Algunas ventanas fallaron"
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"Error en send_text_new_protocol_dual: {e}")
        return SendResponse(
            success=False,
            message="Error en send_text_new_protocol_dual",
            data={
                "totalPanels": 1,
                "totalWindows": 2,
                "results": [{
                    "ip": request.panel.ip,
                    "success": False,
                    "windows": [],
                    "errorMessage": str(e)
                }]
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=False,
        log_level="info"
    ) 