#!/usr/bin/env python3
"""
Controlador para protocolo nuevo v1.4.7
Implementa comunicación con paneles LED usando protocol.jar
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class NewProtocolController:
    """Controlador para protocolo nuevo v1.4.7"""
    
    def __init__(self):
        self.java_path = None
        self.protocol_jar_path = None
        self.initialized = False
        self.java_process = None
        
        # Lista completa de efectos disponibles del nuevo protocolo
        self.available_effects = [
            "Random", "Instant", "Open_left", "Open_right", "Open_horizontal", "Open_vertical",
            "Shutter_vertical", "Shift_left", "Shift_right", "Shift_up", "Shift_down",
            "Scroll_up", "Scroll_left", "Scrollleft_continuously", "Scroll_right", "Scroll_right_continuously",
            "Blink", "Shutter_horizontal", "Open_clockwise", "Open_anticlockwise",
            "Windmill_clockwise", "Windmill_anticlockwise", "Rectangle_out", "Rectangle_in",
            "Corner_out", "Corner_in", "Round_out", "Round_in", "Open_top_left", "Open_top_right",
            "Open_bottom_left", "Open_bottom_right", "Open_slash", "Open_backslash",
            "Slide_top_left", "Slide_top_right", "Slide_bottom_left", "Slide_bottom_right",
            "Open_cross_in", "Open_cross_out", "Zebra_cross_horizontal", "Zebra_cross_vertical",
            "Mosaic_large", "Mosaic_small", "Laser_line_upward", "Laser_line_downward",
            "Scrape_up", "Drop_down", "Slide_left_right", "Slide_top_bottom",
            "Slewing_out", "Slewing_in", "Chessboard_horizontal", "Chessboard_vertical",
            "Scroll_up_continuously", "Scroll_down_continuously", "Expand_from_top",
            "Expand_from_bottom", "Expand_vertical", "Blind_horizontal", "Blind_vertical",
            "Snow_fall", "Scroll_down", "Open_left_right", "Open_up_down", "Open_2_fan",
            "Slide_zebra_horizontal", "Slide_zebra_vertical", "$VALUES"
        ]
        
        # Mapeo de efectos por defecto
        self.default_effects = {
            "fixed": "Instant",      # Para textos fijos
            "scroll": "Scroll_left"  # Para textos con scroll
        }
        
        # Efectos recomendados para diferentes casos de uso
        self.recommended_effects = {
            "instant": "Para textos fijos (efecto estático)",
            "scroll_left": "Para textos con scroll (desplazamiento hacia la izquierda)",
            "scroll_right": "Para textos con scroll (desplazamiento hacia la derecha)",
            "blink": "Para textos que parpadean",
            "open_left": "Para textos que aparecen desde la izquierda",
            "open_right": "Para textos que aparecen desde la derecha"
        }
        
    async def initialize(self):
        """Inicializar el controlador"""
        try:
            # Buscar Java
            self.java_path = self._find_java()
            if not self.java_path:
                raise Exception("Java no encontrado en el sistema")
            
            # Buscar protocol.jar
            self.protocol_jar_path = self._find_protocol_jar()
            if not self.protocol_jar_path:
                raise Exception("protocol.jar no encontrado")
            
            logger.info(f"Java encontrado: {self.java_path}")
            logger.info(f"Protocol.jar encontrado: {self.protocol_jar_path}")
            
            # Verificar que la librería funciona
            await self._test_library()
            
            self.initialized = True
            logger.info("Controlador de protocolo nuevo inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando controlador nuevo: {e}")
            raise
    
    def _find_java(self) -> Optional[str]:
        """Buscar Java en el sistema"""
        try:
            # Intentar java en PATH
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'java'
        except:
            pass
        
        # Buscar en ubicaciones comunes
        java_paths = [
            '/usr/bin/java',
            '/usr/local/bin/java',
            'C:\\Program Files\\Java\\jdk-11\\bin\\java.exe',
            'C:\\Program Files\\Java\\jre-11\\bin\\java.exe'
        ]
        
        for path in java_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_protocol_jar(self) -> Optional[str]:
        """Buscar protocol.jar"""
        # Buscar en el directorio actual y subdirectorios
        search_paths = [
            'sender_newProtocol/lib/protocol.jar',
            'lib/protocol.jar',
            'protocol.jar'
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        return None
    
    async def _test_library(self):
        """Probar que la librería funciona"""
        try:
            # Verificación simple: solo comprobar que el archivo JAR existe y es válido
            if not self.protocol_jar_path or not os.path.exists(self.protocol_jar_path):
                raise Exception("protocol.jar no encontrado")
            
            # Verificar que es un archivo JAR válido
            try:
                import zipfile
                with zipfile.ZipFile(self.protocol_jar_path, 'r') as jar:
                    # Verificar que contiene clases relacionadas con envío
                    class_files = [f.filename for f in jar.filelist if f.filename.endswith('.class')]
                    send_classes = [f for f in class_files if f.lower().endswith('.class') and ('send' in f.lower() or 'Send' in f)]
                    
                    if not send_classes:
                        raise Exception("No se encontraron clases de envío en protocol.jar")
                    
                    # Verificar específicamente ExtSendUtil
                    ext_send_classes = [f for f in class_files if 'ExtSendUtil' in f]
                    if ext_send_classes:
                        logger.info(f"Clases ExtSendUtil encontradas: {ext_send_classes}")
                    else:
                        logger.warning("ExtSendUtil.class no encontrado, pero continuando...")
                        
            except Exception as e:
                raise Exception(f"Error verificando protocol.jar: {e}")
            
            logger.info("Librería protocol.jar verificada correctamente")
            
        except Exception as e:
            logger.error(f"Error probando librería: {e}")
            raise
    
    async def send_text(self, ip: str, port: int, window_id: int, text: str,
                       color: int = 1, fontSize: int = 2, speed: int = 100,
                       effect: Any = 1, stayTime: int = 50, 
                       alignmentH: int = 0, alignmentV: int = 0,
                       panel_type: str = "single") -> Dict[str, Any]:
        """Enviar texto a un panel usando sendText (método principal)"""
        if not self.initialized:
            raise Exception("Controlador no inicializado")
        
        try:
            # Convertir efecto a código numérico si es string
            effect_code = self.get_effect_code(effect)
            effect_name = self.get_effect_name(effect_code)
            
            # Determinar el tipo de pantalla basado en panel_type
            # panel_type: "single" = pantalla única (sin dividir), "dual" = 2 ventanas separadas de 32x16 cada una
            if panel_type == "dual":
                screen_type = "dual"  # Pantalla con 2 ventanas separadas de 32x16
                logger.info(f"[NEW PROTOCOL] Pantalla dual detectada - 2 ventanas separadas de 32x16")
            else:
                screen_type = "single"  # Pantalla única sin dividir
                logger.info(f"[NEW PROTOCOL] Pantalla única detectada - sin dividir ventanas")
            
            logger.info(f"[NEW PROTOCOL] Enviando texto a {ip}:{port}, ventana {window_id} ({screen_type}): '{text}', color={color}, fontSize={fontSize}, speed={speed}, effect={effect_name}({effect_code}), stayTime={stayTime}, alignmentH={alignmentH}, alignmentV={alignmentV}")
            
            # Crear script Java para enviar texto usando sendText
            java_script = self._create_send_text_script(
                ip, port, window_id, text, color, fontSize, speed, 
                effect_code, stayTime, alignmentH, alignmentV, screen_type
            )
            
            # Ejecutar script
            result = await self._execute_java_script(java_script)
            
            if result.get("success"):
                logger.info(f"Texto enviado correctamente a {ip}:{port} (ventana {window_id}, tipo: {screen_type})")
                return {
                    "success": True,
                    "message": f"Texto enviado correctamente usando sendText a ventana {window_id} ({screen_type})",
                    "ip": ip,
                    "window_id": window_id,
                    "screen_type": screen_type,
                    "effect_used": effect_name,
                    "effect_code": effect_code
                }
            else:
                logger.error(f"Error enviando texto a {ip}:{port}: {result.get('error')}")
                return {
                    "success": False,
                    "message": "Error enviando texto",
                    "error": result.get("error"),
                    "ip": ip,
                    "window_id": window_id,
                    "screen_type": screen_type,
                    "effect_used": effect_name,
                    "effect_code": effect_code
                }
                
        except Exception as e:
            logger.error(f"Error en send_text: {e}")
            return {
                "success": False,
                "message": "Error en send_text",
                "error": str(e),
                "ip": ip,
                "window_id": window_id
            }

    async def send_text_numeric(self, ip: str, port: int, window_id: int, text: str,
                               color: int = 1, fontSize: int = 2, speed: int = 100,
                               effect: Any = 1, stayTime: int = 50, 
                               alignmentH: int = 0, alignmentV: int = 0,
                               panel_type: str = "single") -> Dict[str, Any]:
        """Enviar texto a un panel usando sendText con parámetros numéricos directos"""
        if not self.initialized:
            raise Exception("Controlador no inicializado")
        
        try:
            # Convertir efecto a código numérico si es string
            effect_code = self.get_effect_code(effect)
            effect_name = self.get_effect_name(effect_code)
            
            # Determinar el tipo de pantalla basado en panel_type
            # panel_type: "single" = pantalla única (sin dividir), "dual" = 2 ventanas separadas de 32x16 cada una
            if panel_type == "dual":
                screen_type = "dual"  # Pantalla con 2 ventanas separadas de 32x16
                logger.info(f"[NEW PROTOCOL NUMERIC] Pantalla dual detectada - 2 ventanas separadas de 32x16")
            else:
                screen_type = "single"  # Pantalla única sin dividir
                logger.info(f"[NEW PROTOCOL NUMERIC] Pantalla única detectada - sin dividir ventanas")
            
            logger.info(f"[NEW PROTOCOL NUMERIC] Enviando texto a {ip}:{port}, ventana {window_id} ({screen_type}): '{text}', color={color}, fontSize={fontSize}, speed={speed}, effect={effect_name}({effect_code}), stayTime={stayTime}, alignmentH={alignmentH}, alignmentV={alignmentV}")
            
            # Crear script Java para enviar texto usando sendText con parámetros numéricos directos
            java_script = self._create_send_text_numeric_script(
                ip, port, window_id, text, color, fontSize, speed, 
                effect_code, stayTime, alignmentH, alignmentV, screen_type
            )
            
            # Ejecutar script
            result = await self._execute_java_script(java_script)
            
            if result.get("success"):
                logger.info(f"Texto enviado correctamente a {ip}:{port} (ventana {window_id}, tipo: {screen_type})")
                return {
                    "success": True,
                    "message": f"Texto enviado correctamente usando sendText con parámetros numéricos a ventana {window_id} ({screen_type})",
                    "ip": ip,
                    "window_id": window_id,
                    "screen_type": screen_type,
                    "effect_used": effect_name,
                    "effect_code": effect_code
                }
            else:
                logger.error(f"Error enviando texto a {ip}:{port}: {result.get('error')}")
                return {
                    "success": False,
                    "message": "Error enviando texto",
                    "error": result.get("error"),
                    "ip": ip,
                    "window_id": window_id,
                    "screen_type": screen_type,
                    "effect_used": effect_name,
                    "effect_code": effect_code
                }
                
        except Exception as e:
            logger.error(f"Error en send_text_numeric: {e}")
            return {
                "success": False,
                "message": "Error en send_text_numeric",
                "error": str(e),
                "ip": ip,
                "window_id": window_id
            }

    async def get_available_effects(self) -> Dict[str, Any]:
        """Obtener todos los efectos disponibles del nuevo protocolo"""
        if not self.initialized:
            raise Exception("Controlador no inicializado")
        
        try:
            logger.info("[NEW PROTOCOL] Obteniendo efectos disponibles...")
            
            # Usar la lista almacenada de efectos disponibles
            effects = self.available_effects.copy()
            
            # Filtrar efectos especiales como $VALUES
            effects = [effect for effect in effects if not effect.startswith('$')]
            
            logger.info(f"Efectos disponibles obtenidos correctamente: {len(effects)} efectos")
            return {
                "success": True,
                "message": "Efectos disponibles obtenidos correctamente",
                "effects": effects,
                "recommended_effects": self.recommended_effects,
                "default_effects": self.default_effects,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
                
        except Exception as e:
            logger.error(f"Error en get_available_effects: {e}")
            return {
                "success": False,
                "message": "Error en get_available_effects",
                "error": str(e),
                "effects": []
            }

    def get_effect_code(self, effect_name: str) -> int:
        """Obtener el código numérico de un efecto por nombre"""
        try:
            # Mapeo de efectos a códigos numéricos
            effect_codes = {
                "Instant": 1,
                "Scroll_left": 2,
                "Scroll_right": 3,
                "Scroll_up": 4,
                "Scroll_down": 5,
                "Blink": 6,
                "Open_left": 7,
                "Open_right": 8,
                "Open_horizontal": 9,
                "Open_vertical": 10,
                "Shutter_vertical": 11,
                "Shutter_horizontal": 12,
                "Shift_left": 13,
                "Shift_right": 14,
                "Shift_up": 15,
                "Shift_down": 16,
                "Open_clockwise": 17,
                "Open_anticlockwise": 18,
                "Windmill_clockwise": 19,
                "Windmill_anticlockwise": 20,
                "Rectangle_out": 21,
                "Rectangle_in": 22,
                "Corner_out": 23,
                "Corner_in": 24,
                "Round_out": 25,
                "Round_in": 26,
                "Open_top_left": 27,
                "Open_top_right": 28,
                "Open_bottom_left": 29,
                "Open_bottom_right": 30,
                "Open_slash": 31,
                "Open_backslash": 32,
                "Slide_top_left": 33,
                "Slide_top_right": 34,
                "Slide_bottom_left": 35,
                "Slide_bottom_right": 36,
                "Open_cross_in": 37,
                "Open_cross_out": 38,
                "Zebra_cross_horizontal": 39,
                "Zebra_cross_vertical": 40,
                "Mosaic_large": 41,
                "Mosaic_small": 42,
                "Laser_line_upward": 43,
                "Laser_line_downward": 44,
                "Scrape_up": 45,
                "Drop_down": 46,
                "Slide_left_right": 47,
                "Slide_top_bottom": 48,
                "Slewing_out": 49,
                "Slewing_in": 50,
                "Chessboard_horizontal": 51,
                "Chessboard_vertical": 52,
                "Scroll_up_continuously": 53,
                "Scroll_down_continuously": 54,
                "Scrollleft_continuously": 55,
                "Scroll_right_continuously": 56,
                "Expand_from_top": 57,
                "Expand_from_bottom": 58,
                "Expand_vertical": 59,
                "Blind_horizontal": 60,
                "Blind_vertical": 61,
                "Snow_fall": 62,
                "Open_left_right": 63,
                "Open_up_down": 64,
                "Open_2_fan": 65,
                "Slide_zebra_horizontal": 66,
                "Slide_zebra_vertical": 67,
                "Random": 0
            }
            
            # Si es un número, devolverlo directamente
            if str(effect_name).isdigit():
                return int(effect_name)
            
            # Si es un nombre de efecto, buscar su código
            if effect_name in effect_codes:
                return effect_codes[effect_name]
            
            # Si no se encuentra, usar Instant por defecto
            logger.warning(f"Efecto '{effect_name}' no encontrado, usando Instant por defecto")
            return effect_codes["Instant"]
            
        except Exception as e:
            logger.error(f"Error obteniendo código de efecto '{effect_name}': {e}")
            return 1  # Instant por defecto

    def get_effect_name(self, effect_code: int) -> str:
        """Obtener el nombre de un efecto por código numérico"""
        try:
            # Mapeo inverso de códigos numéricos a efectos
            code_effects = {
                1: "Instant",
                2: "Scroll_left",
                3: "Scroll_right",
                4: "Scroll_up",
                5: "Scroll_down",
                6: "Blink",
                7: "Open_left",
                8: "Open_right",
                9: "Open_horizontal",
                10: "Open_vertical",
                11: "Shutter_vertical",
                12: "Shutter_horizontal",
                13: "Shift_left",
                14: "Shift_right",
                15: "Shift_up",
                16: "Shift_down",
                17: "Open_clockwise",
                18: "Open_anticlockwise",
                19: "Windmill_clockwise",
                20: "Windmill_anticlockwise",
                21: "Rectangle_out",
                22: "Rectangle_in",
                23: "Corner_out",
                24: "Corner_in",
                25: "Round_out",
                26: "Round_in",
                27: "Open_top_left",
                28: "Open_top_right",
                29: "Open_bottom_left",
                30: "Open_bottom_right",
                31: "Open_slash",
                32: "Open_backslash",
                33: "Slide_top_left",
                34: "Slide_top_right",
                35: "Slide_bottom_left",
                36: "Slide_bottom_right",
                37: "Open_cross_in",
                38: "Open_cross_out",
                39: "Zebra_cross_horizontal",
                40: "Zebra_cross_vertical",
                41: "Mosaic_large",
                42: "Mosaic_small",
                43: "Laser_line_upward",
                44: "Laser_line_downward",
                45: "Scrape_up",
                46: "Drop_down",
                47: "Slide_left_right",
                48: "Slide_top_bottom",
                49: "Slewing_out",
                50: "Slewing_in",
                51: "Chessboard_horizontal",
                52: "Chessboard_vertical",
                53: "Scroll_up_continuously",
                54: "Scroll_down_continuously",
                55: "Scrollleft_continuously",
                56: "Scroll_right_continuously",
                57: "Expand_from_top",
                58: "Expand_from_bottom",
                59: "Expand_vertical",
                60: "Blind_horizontal",
                61: "Blind_vertical",
                62: "Snow_fall",
                63: "Open_left_right",
                64: "Open_up_down",
                65: "Open_2_fan",
                66: "Slide_zebra_horizontal",
                67: "Slide_zebra_vertical",
                0: "Random"
            }
            
            if effect_code in code_effects:
                return code_effects[effect_code]
            else:
                logger.warning(f"Código de efecto {effect_code} no encontrado, usando Instant por defecto")
                return "Instant"
                
        except Exception as e:
            logger.error(f"Error obteniendo nombre de efecto para código {effect_code}: {e}")
            return "Instant"

    def _create_send_text_script(self, ip: str, port: int, window_id: int, text: str,
                                color: int, fontSize: int, speed: int, effect: int,
                                stayTime: int, alignmentH: int, alignmentV: int, screen_type: str = "single") -> str:
        """Crear script Java para enviar texto usando sendText (método principal)"""
        return f"""
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.lang.reflect.Constructor;

public class SendText {{
    public static void main(String[] args) {{
        try {{
            // Cargar librería
            URL jarUrl = new URL("file://{self.protocol_jar_path}");
            URLClassLoader classLoader = new URLClassLoader(new URL[]{{jarUrl}});
            
            // Cargar clases
            Class<?> extSendUtilClass = classLoader.loadClass("com.lumen.ledcenter3.protocol.ExtSendUtil");
            Class<?> listenerClass = classLoader.loadClass("com.lumen.ledcenter3.protocol.ExternalNetworkSendProtocol$OnTcpNetWorkListener");
            
            // Crear instancia de ExtSendUtil
            Constructor<?> constructor = extSendUtilClass.getDeclaredConstructor();
            Object extSendUtil = constructor.newInstance();
            
            // Inicializar red
            Method initNetwork = extSendUtilClass.getMethod("initNetwork", String.class, int.class, String.class);
            initNetwork.invoke(extSendUtil, "{ip}", {port}, "255.255.255.255");
            System.out.println("Red inicializada");
            
            // Crear listener (implementación simple)
            Object listener = java.lang.reflect.Proxy.newProxyInstance(
                listenerClass.getClassLoader(),
                new Class[]{{listenerClass}},
                (proxy, method, args2) -> {{
                    if (method.getName().equals("onTcpNetWorkListener")) {{
                        System.out.println("Listener llamado: " + args2[0]);
                    }}
                    return null;
                }}
            );
            
            // Configurar listener
            Method setListener = extSendUtilClass.getMethod("setListener", listenerClass);
            setListener.invoke(extSendUtil, listener);
            System.out.println("Listener configurado");
            
            // Configurar pantalla según el tipo de ventana
            // screen_type: "single" = pantalla única (sin dividir), "dual" = 2 ventanas separadas de 32x16 cada una
            if ("{screen_type}".equals("dual")) {{
                // Dividir pantalla en 2 ventanas de 32x16
                Method splitScreen = extSendUtilClass.getMethod("splitScreen", int.class, int[][].class);
                int[] rect1 = new int[]{{0, 0, 32, 16}};
                int[] rect2 = new int[]{{32, 0, 32, 16}};
                int[][] winRects = new int[][]{{rect1, rect2}};
                splitScreen.invoke(extSendUtil, 2, (Object) winRects);
                System.out.println("Pantalla dividida en 2 ventanas de 32x16");
            }} else {{
                // Pantalla única - NO dividir, usar pantalla completa sin splitScreen
                System.out.println("Usando pantalla única sin dividir - ventana 0");
            }}
            
            // Usar sendText (método principal para protocolo nuevo)
            // boolean sendText(int nWndNo, String content, int crColor, int nFontSize, 
            //                  int nSpeed, int nEffect, int nStayTime, int nAlignmentHori, 
            //                  int nAlignmentVert)
            Method sendText = extSendUtilClass.getMethod("sendText", 
                int.class, String.class, int.class, int.class, int.class, 
                int.class, int.class, int.class, int.class);
            
            // Ajustar fontSize: 2 = letra 16px
            int fontSize = {fontSize};
            if (fontSize != 2) fontSize = 2;
            // Ajustar stayTime para efectos fijos (Instant = 1)
            int stay = {stayTime};
            if ({effect} == 1 && stay < 500) stay = 500; // Aumentar stayTime para efectos fijos
            
            boolean result = (Boolean) sendText.invoke(extSendUtil, 
                {window_id}, "{text}", {color}, fontSize, {speed}, 
                {effect}, stay, 0, {alignmentV});
            
            if (result) {{
                System.out.println("Texto enviado correctamente usando sendText a ventana {window_id}");
            }} else {{
                System.out.println("Error enviando texto usando sendText a ventana {window_id}");
            }}
            
            // Esperar un poco para asegurar que el mensaje se procese
            Thread.sleep(1000);
            System.out.println("Mensaje enviado y procesado");
            
            // NO cerrar conexión para mantener el texto visible
            System.out.println("Conexión mantenida abierta");
            
            System.exit(result ? 0 : 1);
            
        }} catch (Exception e) {{
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
"""

    def _create_send_text_numeric_script(self, ip: str, port: int, window_id: int, text: str,
                                        color: int, fontSize: int, speed: int, effect: int,
                                        stayTime: int, alignmentH: int, alignmentV: int, screen_type: str = "single") -> str:
        """Crear script Java para enviar texto usando sendText con parámetros numéricos directos"""
        return f"""
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.lang.reflect.Constructor;

public class SendTextNumeric {{
    public static void main(String[] args) {{
        try {{
            // Cargar librería
            URL jarUrl = new URL("file://{self.protocol_jar_path}");
            URLClassLoader classLoader = new URLClassLoader(new URL[]{{jarUrl}});
            
            // Cargar clases
            Class<?> extSendUtilClass = classLoader.loadClass("com.lumen.ledcenter3.protocol.ExtSendUtil");
            Class<?> listenerClass = classLoader.loadClass("com.lumen.ledcenter3.protocol.ExternalNetworkSendProtocol$OnTcpNetWorkListener");
            
            // Crear instancia de ExtSendUtil
            Constructor<?> constructor = extSendUtilClass.getDeclaredConstructor();
            Object extSendUtil = constructor.newInstance();
            
            // Inicializar red
            Method initNetwork = extSendUtilClass.getMethod("initNetwork", String.class, int.class, String.class);
            initNetwork.invoke(extSendUtil, "{ip}", {port}, "255.255.255.255");
            System.out.println("Red inicializada");
            
            // Crear listener (implementación simple)
            Object listener = java.lang.reflect.Proxy.newProxyInstance(
                listenerClass.getClassLoader(),
                new Class[]{{listenerClass}},
                (proxy, method, args2) -> {{
                    if (method.getName().equals("onTcpNetWorkListener")) {{
                        System.out.println("Listener llamado: " + args2[0]);
                    }}
                    return null;
                }}
            );
            
            // Configurar listener
            Method setListener = extSendUtilClass.getMethod("setListener", listenerClass);
            setListener.invoke(extSendUtil, listener);
            System.out.println("Listener configurado");
            
            // Configurar pantalla según el tipo de ventana
            // screen_type: "single" = pantalla completa (sin dividir), "dual" = 2 ventanas separadas de 32x16 cada una
            if ("{screen_type}".equals("dual")) {{
                // Dividir pantalla en 2 ventanas de 32x16
                Method splitScreen = extSendUtilClass.getMethod("splitScreen", int.class, int[][].class);
                int[] rect1 = new int[]{{0, 0, 32, 16}};
                int[] rect2 = new int[]{{32, 0, 32, 16}};
                int[][] winRects = new int[][]{{rect1, rect2}};
                splitScreen.invoke(extSendUtil, 2, (Object) winRects);
                System.out.println("Pantalla dividida en 2 ventanas de 32x16");
            }} else {{
                // Pantalla única - NO dividir, usar pantalla completa sin splitScreen
                System.out.println("Usando pantalla única sin dividir - ventana 0");
            }}
            
            // Usar sendText con parámetros numéricos directos (sin conversiones)
            // boolean sendText(int nWndNo, String content, int crColor, int nFontSize, 
            //                  int nSpeed, int nEffect, int nStayTime, int nAlignmentHori, 
            //                  int nAlignmentVert)
            Method sendText = extSendUtilClass.getMethod("sendText", 
                int.class, String.class, int.class, int.class, int.class, 
                int.class, int.class, int.class, int.class);
            
            // Usar parámetros exactos sin ajustes
            boolean result = (Boolean) sendText.invoke(extSendUtil, 
                {window_id}, "{text}", {color}, {fontSize}, {speed}, 
                {effect}, {stayTime}, 0, {alignmentV});
            
            if (result) {{
                System.out.println("Texto enviado correctamente usando sendText con parámetros numéricos a ventana {window_id}");
            }} else {{
                System.out.println("Error enviando texto usando sendText con parámetros numéricos a ventana {window_id}");
            }}
            
            // Esperar un poco para asegurar que el mensaje se procese
            Thread.sleep(1000);
            System.out.println("Mensaje enviado y procesado");
            
            // NO cerrar conexión para mantener el texto visible
            System.out.println("Conexión mantenida abierta");
            
            System.exit(result ? 0 : 1);
            
        }} catch (Exception e) {{
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
"""

    def _create_get_effects_script(self) -> str:
        """Crear script Java para obtener efectos disponibles"""
        return f"""
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

public class GetEffects {{
    public static void main(String[] args) {{
        try {{
            // Cargar librería
            URL jarUrl = new URL("file://{self.protocol_jar_path}");
            URLClassLoader classLoader = new URLClassLoader(new URL[]{{jarUrl}});
            
            // Cargar clase ShowEffect
            Class<?> showEffectClass = classLoader.loadClass("com.lumen.ledcenter3.protocol.ShowEffect");
            System.out.println("Clase ShowEffect cargada correctamente");
            
            // Obtener todos los campos estáticos (efectos)
            Field[] fields = showEffectClass.getDeclaredFields();
            List<String> effects = new ArrayList<>();
            
            System.out.println("Efectos disponibles:");
            for (Field field : fields) {{
                if (java.lang.reflect.Modifier.isStatic(field.getModifiers())) {{
                    String effectName = field.getName();
                    effects.add(effectName);
                    System.out.println("- " + effectName);
                }}
            }}
            
            // Intentar obtener efecto usando Random.getEffect()
            try {{
                Class<?> randomClass = showEffectClass.getDeclaredClasses()[0]; // Asumiendo que Random es una clase interna
                Method getEffectMethod = randomClass.getMethod("getEffect");
                Object randomInstance = randomClass.newInstance();
                Object randomEffect = getEffectMethod.invoke(randomInstance);
                System.out.println("Efecto aleatorio obtenido: " + randomEffect);
            }} catch (Exception e) {{
                System.out.println("No se pudo obtener efecto aleatorio: " + e.getMessage());
            }}
            
            // Crear respuesta JSON
            StringBuilder jsonResponse = new StringBuilder();
            jsonResponse.append("{{\\n");
            jsonResponse.append("  \\"success\\": true,\\n");
            jsonResponse.append("  \\"effects\\": [\\n");
            for (int i = 0; i < effects.size(); i++) {{
                jsonResponse.append("    \\"" + effects.get(i) + "\\"");
                if (i < effects.size() - 1) {{
                    jsonResponse.append(",");
                }}
                jsonResponse.append("\\n");
            }}
            jsonResponse.append("  ]\\n");
            jsonResponse.append("}}");
            
            System.out.println("JSON Response:");
            System.out.println(jsonResponse.toString());
            
            System.exit(0);
            
        }} catch (Exception e) {{
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
"""

    async def _execute_java_script(self, script: str) -> Dict[str, Any]:
        """Ejecutar script Java con logs detallados"""
        try:
            # Determinar el nombre de la clase basado en el contenido del script
            if 'public class SendTextRGB' in script:
                script_file = 'SendTextRGB.java'
                class_name = 'SendTextRGB'
            elif 'public class SendTextNumeric' in script:
                script_file = 'SendTextNumeric.java'
                class_name = 'SendTextNumeric'
            elif 'public class GetEffects' in script:
                script_file = 'GetEffects.java'
                class_name = 'GetEffects'
            else:
                script_file = 'SendText.java'
                class_name = 'SendText'

            with open(script_file, 'w') as f:
                f.write(script)
            
            # Compilar
            if not self.java_path:
                return {"success": False, "error": "Java no encontrado"}
            javac_path = self.java_path.replace('java', 'javac')
            compile_result = subprocess.run([
                javac_path,
                script_file
            ], capture_output=True, text=True, timeout=30)
            
            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Error compilando: {compile_result.stderr}",
                    "compile_stdout": compile_result.stdout
                }
            
            # Ejecutar con logs detallados
            class_file = script_file.replace('.java', '.class')
            run_result = subprocess.run([
                self.java_path,
                '-cp', '.',
                class_name
            ], capture_output=True, text=True, timeout=60)
            
            # Limpiar archivos temporales
            if os.path.exists(script_file):
                os.remove(script_file)
            if os.path.exists(class_file):
                os.remove(class_file)
            
            # Log detallado del proceso Java
            logger.info(f"Java stdout: {run_result.stdout}")
            if run_result.stderr:
                logger.warning(f"Java stderr: {run_result.stderr}")
            
            if run_result.returncode == 0:
                # Para GetEffects, intentar extraer la lista de efectos del output
                if class_name == 'GetEffects':
                    effects = []
                    for line in run_result.stdout.split('\n'):
                        if line.strip().startswith('- '):
                            effect_name = line.strip()[2:]  # Remover "- "
                            effects.append(effect_name)
                    
                    return {
                        "success": True,
                        "output": run_result.stdout,
                        "stderr": run_result.stderr,
                        "effects": effects
                    }
                else:
                    return {
                        "success": True,
                        "output": run_result.stdout,
                        "stderr": run_result.stderr
                    }
            else:
                return {
                    "success": False,
                    "error": run_result.stderr,
                    "stdout": run_result.stdout
                }
                
        except Exception as e:
            logger.error(f"Error en _execute_java_script: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def shutdown(self):
        """Cerrar el controlador"""
        logger.info("Cerrando controlador de protocolo nuevo")
        if self.java_process:
            self.java_process.terminate()
            await asyncio.sleep(1)
            if self.java_process.poll() is None:
                self.java_process.kill() 