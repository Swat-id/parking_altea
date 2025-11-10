"""
Pool de conexiones TCP para comunicación con múltiples paneles
"""

import asyncio
import socket
import logging
from typing import Optional, Dict
from collections import defaultdict
from .constants import DEFAULT_PORT, DEFAULT_CONNECTION_TIMEOUT, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Pool de conexiones TCP para gestionar múltiples paneles en paralelo.
    Mantiene conexiones persistentes y las reutiliza para mejorar el rendimiento.
    """
    
    def __init__(
        self,
        max_connections_per_panel: int = 5,
        connection_timeout: float = DEFAULT_CONNECTION_TIMEOUT,
        read_timeout: float = DEFAULT_TIMEOUT
    ):
        """
        Inicializa el pool de conexiones.
        
        Args:
            max_connections_per_panel: Máximo de conexiones simultáneas por panel
            connection_timeout: Timeout para establecer conexión (segundos)
            read_timeout: Timeout para leer respuestas (segundos)
        """
        self.max_connections_per_panel = max_connections_per_panel
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        
        # Diccionario de pools por panel: {panel_key: [connections]}
        self._pools: Dict[str, list] = defaultdict(list)
        
        # Semáforos para limitar conexiones por panel
        self._semaphores: Dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(max_connections_per_panel)
        )
        
        # Lock para operaciones concurrentes
        self._lock = asyncio.Lock()
        
        logger.info(
            f"ConnectionPool inicializado: max_connections={max_connections_per_panel}, "
            f"connection_timeout={connection_timeout}s, read_timeout={read_timeout}s"
        )
    
    def _get_panel_key(self, ip: str, port: int) -> str:
        """Genera una clave única para un panel"""
        return f"{ip}:{port}"
    
    async def get_connection(self, ip: str, port: int = DEFAULT_PORT) -> Optional[socket.socket]:
        """
        Obtiene una conexión del pool o crea una nueva si es necesario.
        
        Args:
            ip: IP del panel
            port: Puerto del panel (por defecto 5200)
            
        Returns:
            socket.socket: Conexión TCP o None si falla
        """
        panel_key = self._get_panel_key(ip, port)
        semaphore = self._semaphores[panel_key]
        
        # Esperar a que haya disponibilidad
        await semaphore.acquire()
        
        try:
            async with self._lock:
                # Intentar reutilizar una conexión existente
                pool = self._pools[panel_key]
                while pool:
                    conn = pool.pop()
                    if self._is_connection_alive(conn):
                        logger.debug(f"Reutilizando conexión a {panel_key}")
                        return conn
                    else:
                        try:
                            conn.close()
                        except:
                            pass
            
            # Crear nueva conexión
            logger.debug(f"Creando nueva conexión a {panel_key}")
            conn = await self._create_connection(ip, port)
            return conn
            
        except Exception as e:
            logger.error(f"Error obteniendo conexión a {panel_key}: {e}")
            semaphore.release()
            return None
    
    async def _create_connection(self, ip: str, port: int) -> socket.socket:
        """
        Crea una nueva conexión TCP.
        
        Args:
            ip: IP del panel
            port: Puerto del panel
            
        Returns:
            socket.socket: Conexión TCP
            
        Raises:
            Exception: Si no se puede establecer la conexión
        """
        loop = asyncio.get_event_loop()
        
        logger.info(f"Intentando conectar a {ip}:{port} (timeout: {self.connection_timeout}s)")
        
        # Crear socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        
        try:
            # Conectar con timeout
            logger.debug(f"Conectando socket a {ip}:{port}...")
            await asyncio.wait_for(
                loop.sock_connect(sock, (ip, port)),
                timeout=self.connection_timeout
            )
            
            # Configurar opciones del socket
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            logger.info(f"✅ Conexión establecida exitosamente a {ip}:{port}")
            return sock
            
        except asyncio.TimeoutError:
            sock.close()
            error_msg = f"Timeout conectando a {ip}:{port} (timeout: {self.connection_timeout}s). El panel puede no tener el puerto {port} abierto."
            logger.error(error_msg)
            raise Exception(error_msg)
        except ConnectionRefusedError as e:
            sock.close()
            error_msg = f"Conexión rechazada por {ip}:{port}. Verificar que el panel esté encendido y el puerto {port} esté abierto."
            logger.error(f"{error_msg} Error: {e}")
            raise Exception(error_msg)
        except OSError as e:
            sock.close()
            error_msg = f"Error de red conectando a {ip}:{port}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            sock.close()
            error_msg = f"No se pudo conectar a {ip}:{port}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _is_connection_alive(self, conn: socket.socket) -> bool:
        """
        Verifica si una conexión está viva.
        
        Args:
            conn: Socket a verificar
            
        Returns:
            bool: True si la conexión está viva
        """
        try:
            # Intentar leer sin bloquear
            conn.setblocking(False)
            data = conn.recv(1, socket.MSG_PEEK)
            conn.setblocking(True)
            return True
        except (socket.error, OSError):
            return False
    
    async def return_connection(
        self,
        ip: str,
        port: int,
        conn: socket.socket,
        keep_alive: bool = True
    ):
        """
        Devuelve una conexión al pool para reutilización.
        
        Args:
            ip: IP del panel
            port: Puerto del panel
            conn: Conexión a devolver
            keep_alive: Si True, mantiene la conexión en el pool
        """
        panel_key = self._get_panel_key(ip, port)
        semaphore = self._semaphores[panel_key]
        
        try:
            if keep_alive and self._is_connection_alive(conn):
                async with self._lock:
                    self._pools[panel_key].append(conn)
                    logger.debug(f"Conexión devuelta al pool: {panel_key}")
            else:
                try:
                    conn.close()
                    logger.debug(f"Conexión cerrada: {panel_key}")
                except:
                    pass
        finally:
            semaphore.release()
    
    async def send_data(
        self,
        ip: str,
        port: int,
        data: bytes
    ) -> Optional[bytes]:
        """
        Envía datos a través de una conexión del pool y espera respuesta.
        
        Args:
            ip: IP del panel
            port: Puerto del panel
            data: Datos a enviar
            
        Returns:
            bytes: Respuesta recibida o None si falla
        """
        logger.debug(f"Obteniendo conexión para enviar datos a {ip}:{port}")
        conn = await self.get_connection(ip, port)
        if conn is None:
            logger.error(f"No se pudo obtener conexión a {ip}:{port}")
            return None
        
        try:
            # Enviar datos
            logger.info(f"📤 Enviando {len(data)} bytes a {ip}:{port}")
            logger.debug(f"Datos a enviar (hex): {data.hex()}")
            conn.sendall(data)
            logger.info(f"✅ Datos enviados exitosamente a {ip}:{port}")
            
            # Leer respuesta con timeout
            logger.info(f"⏳ Esperando respuesta de {ip}:{port} (timeout: {self.read_timeout}s)")
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                self._read_response(conn),
                timeout=self.read_timeout
            )
            
            logger.info(f"📥 Respuesta recibida de {ip}:{port} ({len(response)} bytes)")
            logger.debug(f"Respuesta recibida (hex): {response.hex()}")
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout leyendo respuesta de {ip}:{port} (timeout: {self.read_timeout}s)")
            return None
        except Exception as e:
            logger.error(f"Error enviando datos a {ip}:{port}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
        finally:
            # Devolver conexión al pool
            await self.return_connection(ip, port, conn)
    
    async def _read_response(self, conn: socket.socket) -> bytes:
        """
        Lee una respuesta completa del socket.
        
        Args:
            conn: Socket de conexión
            
        Returns:
            bytes: Respuesta completa
        """
        # Leer header mínimo (12 bytes: ID + length + reserved + packet_type)
        header = await asyncio.get_event_loop().sock_recv(conn, 12)
        
        if len(header) < 12:
            raise Exception("Respuesta incompleta")
        
        # Leer longitud de red (bytes 4-5, little-endian)
        import struct
        network_length = struct.unpack('<H', header[4:6])[0]
        
        # Leer el resto del paquete
        remaining = network_length - 4  # Ya leímos 4 bytes (packet_type + card_type + card_id + command)
        if remaining > 0:
            body = await asyncio.get_event_loop().sock_recv(conn, remaining)
            return header + body
        
        return header
    
    async def close_all(self):
        """Cierra todas las conexiones del pool"""
        async with self._lock:
            for panel_key, pool in self._pools.items():
                for conn in pool:
                    try:
                        conn.close()
                    except:
                        pass
                pool.clear()
            
            self._pools.clear()
            logger.info("Todas las conexiones del pool cerradas")
    
    async def close_panel_connections(self, ip: str, port: int = DEFAULT_PORT):
        """Cierra todas las conexiones de un panel específico"""
        panel_key = self._get_panel_key(ip, port)
        async with self._lock:
            pool = self._pools.get(panel_key, [])
            for conn in pool:
                try:
                    conn.close()
                except:
                    pass
            pool.clear()
            logger.info(f"Conexiones cerradas para {panel_key}")

