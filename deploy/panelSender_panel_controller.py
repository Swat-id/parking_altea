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
                    send_classes = [f for f in class_files if 'send' in f.lower() or 'Send' in f]
                    
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
                       effect: int = 1, stayTime: int = 50, 
                       alignmentH: int = 0, alignmentV: int = 0) -> Dict[str, Any]:
        """Enviar texto a un panel usando sendText (más simple para colores)"""
        if not self.initialized:
            raise Exception("Controlador no inicializado")
        
        try:
            logger.info(f"Enviando texto a {ip}:{port}, ventana {window_id}: {text}")
            
            # Crear script Java para enviar texto usando sendText
            java_script = self._create_send_text_script(
                ip, port, window_id, text, color, fontSize, speed, 
                effect, stayTime, alignmentH, alignmentV
            )
            
            # Ejecutar script
            result = await self._execute_java_script(java_script)
            
            if result.get("success"):
                logger.info(f"Texto enviado correctamente a {ip}:{port}")
                return {
                    "success": True,
                    "message": "Texto enviado correctamente usando sendText",
                    "ip": ip,
                    "window_id": window_id
                }
            else:
                logger.error(f"Error enviando texto a {ip}:{port}: {result.get('error')}")
                return {
                    "success": False,
                    "message": "Error enviando texto",
                    "error": result.get("error"),
                    "ip": ip,
                    "window_id": window_id
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

    async def send_text_rgb(self, ip: str, port: int, window_id: int, text: str,
                           color: int = 1, fontSize: int = 2, speed: int = 100,
                           effect: int = 1, stayTime: int = 50, 
                           alignmentH: int = 0, alignmentV: int = 0) -> Dict[str, Any]:
        """Enviar texto a un panel usando sendTextRGB (método alternativo con coordenadas)"""
        if not self.initialized:
            raise Exception("Controlador no inicializado")
        
        try:
            logger.info(f"Enviando texto RGB a {ip}:{port}, ventana {window_id}: {text}")
            
            # Crear script Java para enviar texto usando sendTextRGB
            java_script = self._create_send_script(
                ip, port, window_id, text, color, fontSize, speed, 
                effect, stayTime, alignmentH, alignmentV
            )
            
            # Ejecutar script
            result = await self._execute_java_script(java_script)
            
            if result.get("success"):
                logger.info(f"Texto RGB enviado correctamente a {ip}:{port}")
                return {
                    "success": True,
                    "message": "Texto enviado correctamente usando sendTextRGB",
                    "ip": ip,
                    "window_id": window_id
                }
            else:
                logger.error(f"Error enviando texto RGB a {ip}:{port}: {result.get('error')}")
                return {
                    "success": False,
                    "message": "Error enviando texto RGB",
                    "error": result.get("error"),
                    "ip": ip,
                    "window_id": window_id
                }
                
        except Exception as e:
            logger.error(f"Error en send_text_rgb: {e}")
            return {
                "success": False,
                "message": "Error en send_text_rgb",
                "error": str(e),
                "ip": ip,
                "window_id": window_id
            }
    
    def _create_send_text_script(self, ip: str, port: int, window_id: int, text: str,
                                color: int, fontSize: int, speed: int, effect: int,
                                stayTime: int, alignmentH: int, alignmentV: int) -> str:
        """Crear script Java para enviar texto usando sendText (más simple para colores)"""
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
            Class<?> listenerClass = classLoader.loadClass("OnTcpNetWorkListener");
            
            // Crear instancia de ExtSendUtil
            Constructor<?> constructor = extSendUtilClass.getDeclaredConstructor();
            Object extSendUtil = constructor.newInstance();
            
            // Inicializar red
            Method initNetwork = extSendUtilClass.getMethod("initNetwork", String.class, int.class);
            initNetwork.invoke(extSendUtil, "{ip}", {port});
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
            
            // Dividir pantalla si es necesario
            if ({window_id} > 0) {{
                // splitScreen(int windowCount, int[]... winRects) según SDK
                // Para 2 ventanas de 32x16: windowCount=2, winRects=[{0,0,32,16}, {32,0,64,16}]
                Method splitScreen = extSendUtilClass.getMethod("splitScreen", int.class, int[][].class);
                int[] rect1 = new int[]{{0, 0, 32, 16}};
                int[] rect2 = new int[]{{32, 0, 64, 16}};
                int[][] winRects = new int[][]{{rect1, rect2}};
                splitScreen.invoke(extSendUtil, 2, (Object) winRects);
                System.out.println("Pantalla dividida en 2 ventanas de 32x16");
            }}
            
            // Usar sendText (más simple para colores)
            // boolean sendText(int nWndNo, String content, int crColor, int nFontSize, 
            //                  int nSpeed, int nEffect, int nStayTime, int nAlignmentHori, 
            //                  int nAlignmentVert, boolean isExt)
            Method sendText = extSendUtilClass.getMethod("sendText", 
                int.class, String.class, int.class, int.class, int.class, 
                int.class, int.class, int.class, int.class, boolean.class);
            
            boolean result = (Boolean) sendText.invoke(extSendUtil, 
                {window_id}, "{text}", {color}, {fontSize}, {speed}, 
                {effect}, {stayTime}, {alignmentH}, {alignmentV}, true);
            
            if (result) {{
                System.out.println("Texto enviado correctamente usando sendText");
            }} else {{
                System.out.println("Error enviando texto usando sendText");
            }}
            
            // Cerrar conexión
            Method quitExternalScreen = extSendUtilClass.getMethod("quitExternalScreen");
            quitExternalScreen.invoke(extSendUtil);
            System.out.println("Conexión cerrada");
            
            System.exit(result ? 0 : 1);
            
        }} catch (Exception e) {{
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
"""

    def _create_send_script(self, ip: str, port: int, window_id: int, text: str,
                           color: int, fontSize: int, speed: int, effect: int,
                           stayTime: int, alignmentH: int, alignmentV: int) -> str:
        """Crear script Java para enviar texto usando sendTextRGB (método alternativo)"""
        return f"""
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.lang.reflect.Constructor;

public class SendTextRGB {{
    public static void main(String[] args) {{
        try {{
            // Cargar librería
            URL jarUrl = new URL("file://{self.protocol_jar_path}");
            URLClassLoader classLoader = new URLClassLoader(new URL[]{{jarUrl}});
            
            // Cargar clases
            Class<?> extSendUtilClass = classLoader.loadClass("com.lumen.ledcenter3.protocol.ExtSendUtil");
            Class<?> listenerClass = classLoader.loadClass("OnTcpNetWorkListener");
            
            // Crear instancia de ExtSendUtil
            Constructor<?> constructor = extSendUtilClass.getDeclaredConstructor();
            Object extSendUtil = constructor.newInstance();
            
            // Inicializar red
            Method initNetwork = extSendUtilClass.getMethod("initNetwork", String.class, int.class);
            initNetwork.invoke(extSendUtil, "{ip}", {port});
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
            
            // Dividir pantalla si es necesario
            if ({window_id} > 0) {{
                // splitScreen(int windowCount, int[]... winRects) según SDK
                // Para 2 ventanas de 32x16: windowCount=2, winRects=[{0,0,32,16}, {32,0,64,16}]
                Method splitScreen = extSendUtilClass.getMethod("splitScreen", int.class, int[][].class);
                int[] rect1 = new int[]{{0, 0, 32, 16}};
                int[] rect2 = new int[]{{32, 0, 64, 16}};
                int[][] winRects = new int[][]{{rect1, rect2}};
                splitScreen.invoke(extSendUtil, 2, (Object) winRects);
                System.out.println("Pantalla dividida en 2 ventanas de 32x16");
            }}
            
            // Calcular coordenadas según ventana
            int x, y, width, height;
            if ({window_id} == 0) {{
                x = 0; y = 0; width = 32; height = 16;
            }} else {{
                x = 32; y = 0; width = 32; height = 16;
            }}
            
            // Enviar texto usando sendTextRGB
            Method sendTextRGB = extSendUtilClass.getMethod("sendTextRGB", 
                String.class, int.class, int.class, int.class, int.class, int.class);
            sendTextRGB.invoke(extSendUtil, "{text}", x, y, width, height, {color});
            System.out.println("Texto enviado usando sendTextRGB");
            
            // Cerrar conexión
            Method quitExternalScreen = extSendUtilClass.getMethod("quitExternalScreen");
            quitExternalScreen.invoke(extSendUtil);
            System.out.println("Conexión cerrada");
            
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
        """Ejecutar script Java"""
        try:
            # Escribir script temporal
            script_file = f"SendText.java"
            class_name = "SendText"
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
                    "error": f"Error compilando: {compile_result.stderr}"
                }
            
            # Ejecutar
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
            
            if run_result.returncode == 0:
                return {
                    "success": True,
                    "output": run_result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": run_result.stderr
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def shutdown(self):
        """Cerrar controlador"""
        logger.info("Cerrando controlador de protocolo nuevo")
        self.initialized = False 