#!/usr/bin/env python3
"""
PanelSender_oldProtocol.py - Servicio para comunicación con paneles LED usando protocolo antiguo

Este servicio implementa la librería Java del fabricante (protocol-1.2.6.jar) para enviar
mensajes a paneles LED usando el protocolo antiguo.

Autor: Parking Altea Team
Fecha: 2025-07-04
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class PanelSenderOldProtocol:
    """
    Clase para manejar la comunicación con paneles LED usando el protocolo antiguo
    """
    
    def __init__(self):
        self.java_jar_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'docs', 'SDK_JAVA_1.2.6', 'protocol-1.2.6.jar'
        )
        self.initialized_panels = {}  # {ip: {'port': port, 'idcode': idcode}}
        self.lock = threading.Lock()
        
        # Verificar que existe la librería Java
        if not os.path.exists(self.java_jar_path):
            raise FileNotFoundError(f"Librería Java no encontrada en: {self.java_jar_path}")
        
        logger.info(f"PanelSender inicializado con librería: {self.java_jar_path}")
    
    def init_network(self, ip: str, port: int = 5200, idcode: str = "255.255.255.255") -> bool:
        """
        Inicializar la red para un panel específico
        
        Args:
            ip: IP del panel
            port: Puerto (por defecto 5200)
            idcode: Código de identificación (por defecto 255.255.255.255)
        
        Returns:
            bool: True si se inicializó correctamente
        """
        try:
            with self.lock:
                # Crear script Java temporal para inicializar la red
                java_code = f"""
import com.lumen.ledcenter3.protocol.SendUtil;

public class PanelInit {{
    public static void main(String[] args) {{
        try {{
            // Inicializar red
            SendUtil.initNetwork("{ip}", {port}, "{idcode}");
            System.out.println("SUCCESS: Network initialized for {ip}:{port}");
        }} catch (Exception e) {{
            System.err.println("ERROR: " + e.getMessage());
            System.exit(1);
        }}
    }}
}}
"""
                
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                    f.write(java_code)
                    java_file = f.name
                
                try:
                    # Compilar y ejecutar
                    class_file = java_file.replace('.java', '.class')
                    
                    # Compilar
                    compile_cmd = [
                        'javac', '-cp', self.java_jar_path, java_file
                    ]
                    result = subprocess.run(compile_cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Error compilando Java: {result.stderr}")
                        return False
                    
                    # Ejecutar
                    run_cmd = [
                        'java', '-cp', f"{os.path.dirname(java_file)}:{self.java_jar_path}", 
                        'PanelInit'
                    ]
                    result = subprocess.run(run_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.initialized_panels[ip] = {'port': port, 'idcode': idcode}
                        logger.info(f"✅ Red inicializada para panel {ip}:{port}")
                        return True
                    else:
                        logger.error(f"❌ Error inicializando red para {ip}: {result.stderr}")
                        return False
                        
                finally:
                    # Limpiar archivos temporales
                    for file_path in [java_file, class_file]:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            
        except Exception as e:
            logger.error(f"❌ Error en init_network para {ip}: {e}")
            return False
    
    def send_text(self, ip: str, window_no: int, content: str, color: int, 
                  font_size: int, speed: int, effect: int, stay_time: int,
                  alignment_hori: int = 1, alignment_vert: int = 1) -> bool:
        """
        Enviar texto a un panel
        
        Args:
            ip: IP del panel
            window_no: Número de ventana (0-7)
            content: Texto a enviar
            color: Color (1-7: rojo, verde, amarillo, azul, púrpura, azul, blanco)
            font_size: Tamaño de fuente (0=8px, 2=16px, 3=24px, etc.)
            speed: Velocidad (1-100)
            effect: Efecto de visualización
            stay_time: Tiempo de permanencia en segundos
            alignment_hori: Alineación horizontal (0=izq, 1=centro, 2=der)
            alignment_vert: Alineación vertical (0=arriba, 1=centro, 2=abajo)
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Verificar que el panel esté inicializado
            if ip not in self.initialized_panels:
                logger.warning(f"Panel {ip} no inicializado, inicializando...")
                if not self.init_network(ip):
                    return False
            
            with self.lock:
                # Crear script Java temporal para enviar texto
                java_code = f"""
import com.lumen.ledcenter3.protocol.SendUtil;

public class PanelSendText {{
    public static void main(String[] args) {{
        try {{
            // Inicializar red si no está inicializada
            SendUtil.initNetwork("{ip}", {self.initialized_panels[ip]['port']}, "{self.initialized_panels[ip]['idcode']}");
            
            // Enviar texto
            boolean result = SendUtil.sendText(
                {window_no},           // nWndNo
                "{content}",           // content
                {color},               // crColor
                {font_size},           // nFontSize
                {speed},               // nSpeed
                {effect},              // nEffect
                {stay_time},           // nStayTime
                {alignment_hori},      // nAlignmentHori
                {alignment_vert}       // nAlignmentVert
            );
            
            if (result) {{
                System.out.println("SUCCESS: Text sent to {ip}");
            }} else {{
                System.err.println("ERROR: Failed to send text to {ip}");
                System.exit(1);
            }}
        }} catch (Exception e) {{
            System.err.println("ERROR: " + e.getMessage());
            System.exit(1);
        }}
    }}
}}
"""
                
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                    f.write(java_code)
                    java_file = f.name
                
                try:
                    # Compilar y ejecutar
                    class_file = java_file.replace('.java', '.class')
                    
                    # Compilar
                    compile_cmd = [
                        'javac', '-cp', self.java_jar_path, java_file
                    ]
                    result = subprocess.run(compile_cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Error compilando Java: {result.stderr}")
                        return False
                    
                    # Ejecutar
                    run_cmd = [
                        'java', '-cp', f"{os.path.dirname(java_file)}:{self.java_jar_path}", 
                        'PanelSendText'
                    ]
                    result = subprocess.run(run_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        logger.info(f"✅ Texto enviado a {ip}: '{content}' (color: {color}, fontSize: {font_size})")
                        return True
                    else:
                        logger.error(f"❌ Error enviando texto a {ip}: {result.stderr}")
                        return False
                        
                finally:
                    # Limpiar archivos temporales
                    for file_path in [java_file, class_file]:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            
        except Exception as e:
            logger.error(f"❌ Error en send_text para {ip}: {e}")
            return False
    
    def send_multi(self, ip: str, item_num: int, texts: List[str], 
                   colors: List[int], font_sizes: List[int], 
                   show_effects: List[int]) -> bool:
        """
        Enviar múltiples textos a un panel
        
        Args:
            ip: IP del panel
            item_num: Número de elementos
            texts: Lista de textos
            colors: Lista de colores
            font_sizes: Lista de tamaños de fuente
            show_effects: Lista de efectos
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Verificar que el panel esté inicializado
            if ip not in self.initialized_panels:
                logger.warning(f"Panel {ip} no inicializado, inicializando...")
                if not self.init_network(ip):
                    return False
            
            with self.lock:
                # Preparar arrays para Java
                texts_str = '", "'.join(texts)
                colors_str = ', '.join(map(str, colors))
                font_sizes_str = ', '.join(map(str, font_sizes))
                show_effects_str = ', '.join(map(str, show_effects))
                
                # Crear script Java temporal para enviar múltiples textos
                java_code = f"""
import com.lumen.ledcenter3.protocol.SendUtil;

public class PanelSendMulti {{
    public static void main(String[] args) {{
        try {{
            // Inicializar red si no está inicializada
            SendUtil.initNetwork("{ip}", {self.initialized_panels[ip]['port']}, "{self.initialized_panels[ip]['idcode']}");
            
            // Preparar arrays
            String[] texts = {{"{texts_str}"}};
            int[] colors = {{{colors_str}}};
            int[] fontSizes = {{{font_sizes_str}}};
            int[] showEffects = {{{show_effects_str}}};
            
            // Enviar múltiples textos
            boolean result = SendUtil.sendMulti(
                {item_num},    // itemNum
                texts,         // texts
                colors,        // colors
                fontSizes,     // fontSizes
                showEffects    // showEffects
            );
            
            if (result) {{
                System.out.println("SUCCESS: Multi texts sent to {ip}");
            }} else {{
                System.err.println("ERROR: Failed to send multi texts to {ip}");
                System.exit(1);
            }}
        }} catch (Exception e) {{
            System.err.println("ERROR: " + e.getMessage());
            System.exit(1);
        }}
    }}
}}
"""
                
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                    f.write(java_code)
                    java_file = f.name
                
                try:
                    # Compilar y ejecutar
                    class_file = java_file.replace('.java', '.class')
                    
                    # Compilar
                    compile_cmd = [
                        'javac', '-cp', self.java_jar_path, java_file
                    ]
                    result = subprocess.run(compile_cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Error compilando Java: {result.stderr}")
                        return False
                    
                    # Ejecutar
                    run_cmd = [
                        'java', '-cp', f"{os.path.dirname(java_file)}:{self.java_jar_path}", 
                        'PanelSendMulti'
                    ]
                    result = subprocess.run(run_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        logger.info(f"✅ Múltiples textos enviados a {ip}: {len(texts)} elementos")
                        return True
                    else:
                        logger.error(f"❌ Error enviando múltiples textos a {ip}: {result.stderr}")
                        return False
                        
                finally:
                    # Limpiar archivos temporales
                    for file_path in [java_file, class_file]:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            
        except Exception as e:
            logger.error(f"❌ Error en send_multi para {ip}: {e}")
            return False

# Instancia global del servicio
panel_sender = None

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud del servicio"""
    try:
        return jsonify({
            'status': 'OK',
            'service': 'PanelSender Old Protocol',
            'version': '1.0.0',
            'initialized_panels': list(panel_sender.initialized_panels.keys()) if panel_sender else []
        }), 200
    except Exception as e:
        logger.error(f"Error en health endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/initNetwork', methods=['POST'])
def init_network_endpoint():
    """Endpoint para inicializar la red de un panel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip = data.get('ip')
        port = data.get('port', 5200)
        idcode = data.get('idcode', '255.255.255.255')
        
        if not ip:
            return jsonify({'error': 'IP is required'}), 400
        
        success = panel_sender.init_network(ip, port, idcode)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Network initialized for {ip}:{port}',
                'ip': ip,
                'port': port,
                'idcode': idcode
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to initialize network for {ip}:{port}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error en initNetwork endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/sendText', methods=['POST'])
def send_text_endpoint():
    """Endpoint para enviar texto a un panel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip = data.get('ip')
        window_no = data.get('windowNo', 0)
        content = data.get('content', '')
        color = data.get('color', 1)  # Rojo por defecto
        font_size = data.get('fontSize', 2)  # 16px por defecto
        speed = data.get('speed', 1)
        effect = data.get('effect', 0)
        stay_time = data.get('stayTime', 5)
        alignment_hori = data.get('alignmentHori', 1)  # Centro
        alignment_vert = data.get('alignmentVert', 1)  # Centro
        
        if not ip or not content:
            return jsonify({'error': 'IP and content are required'}), 400
        
        success = panel_sender.send_text(
            ip, window_no, content, color, font_size, speed, effect, stay_time,
            alignment_hori, alignment_vert
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Text sent to {ip}',
                'ip': ip,
                'content': content,
                'color': color,
                'fontSize': font_size
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send text to {ip}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error en sendText endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/sendMulti', methods=['POST'])
def send_multi_endpoint():
    """Endpoint para enviar múltiples textos a un panel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip = data.get('ip')
        item_num = data.get('itemNum', 1)
        texts = data.get('texts', [])
        colors = data.get('colors', [1])  # Rojo por defecto
        font_sizes = data.get('fontSizes', [2])  # 16px por defecto
        show_effects = data.get('showEffects', [0])
        
        if not ip or not texts:
            return jsonify({'error': 'IP and texts are required'}), 400
        
        # Asegurar que todos los arrays tengan la misma longitud
        max_len = max(len(texts), len(colors), len(font_sizes), len(show_effects))
        texts = texts + [texts[-1]] * (max_len - len(texts)) if len(texts) < max_len else texts[:max_len]
        colors = colors + [colors[-1]] * (max_len - len(colors)) if len(colors) < max_len else colors[:max_len]
        font_sizes = font_sizes + [font_sizes[-1]] * (max_len - len(font_sizes)) if len(font_sizes) < max_len else font_sizes[:max_len]
        show_effects = show_effects + [show_effects[-1]] * (max_len - len(show_effects)) if len(show_effects) < max_len else show_effects[:max_len]
        
        success = panel_sender.send_multi(ip, item_num, texts, colors, font_sizes, show_effects)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Multi texts sent to {ip}',
                'ip': ip,
                'itemNum': item_num,
                'texts': texts,
                'colors': colors,
                'fontSizes': font_sizes
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send multi texts to {ip}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error en sendMulti endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def main():
    """Función principal"""
    global panel_sender
    
    try:
        # Inicializar el servicio
        panel_sender = PanelSenderOldProtocol()
        logger.info("✅ PanelSender Old Protocol inicializado correctamente")
        
        # Iniciar el servidor Flask
        port = 7777
        logger.info(f"🚀 Iniciando servidor en puerto {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Error inicializando PanelSender: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 