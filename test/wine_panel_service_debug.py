#!/usr/bin/env python3
import subprocess
import tempfile
import os
import json
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

class WinePanelService:
    def __init__(self):
        self.dll_path = "/opt/parking-panel-service/CP5200.dll"
        self.wine_prefix = "/opt/parking-panel-service/.wine"
        
    def create_cs_script(self, function, params):
        """Crea un script de C# temporal para ejecutar con Wine"""
        
        if function == "InitComm":
            script = f"""
using System;
using System.Runtime.InteropServices;
using System.Net;

class CP5200Test
{{
    [DllImport("CP5200.dll")]
    public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);
    
    private static uint GetIP(string strIp)
    {{
        IPAddress ipaddress = IPAddress.Parse(strIp);
        uint lIp = (uint)ipaddress.Address;
        lIp = ((lIp & 0xFF000000) >> 24) + ((lIp & 0x00FF0000) >> 8) + ((lIp & 0x0000FF00) << 8) + ((lIp & 0x000000FF) << 24);
        return lIp;
    }}
    
    static int Main()
    {{
        try
        {{
            string panelIPStr = "{params['panelIP']}";
            string idCodeStr = "255.255.255.255";
            int port = {params['port']};
            int timeout = {params['timeout']};
            
            uint panelIP = GetIP(panelIPStr);
            uint idCode = GetIP(idCodeStr);
            
            Console.WriteLine("Iniciando CP5200_Net_Init...");
            Console.WriteLine($"PanelIP String: {{panelIPStr}}");
            Console.WriteLine($"PanelIP Uint: {{panelIP}}");
            Console.WriteLine($"Port: {{port}}, IDCode: {{idCode}}, Timeout: {{timeout}}");
            int result = CP5200_Net_Init(panelIP, port, idCode, timeout);
            Console.WriteLine($"Resultado: {{result}}");
            return result;
        }}
        catch (Exception ex)
        {{
            Console.WriteLine($"Error: {{ex.Message}}");
            return -1;
        }}
    }}
}}
"""
        elif function == "SplitScreen":
            script = f"""
using System;
using System.Runtime.InteropServices;

class CP5200Test
{{
    [DllImport("CP5200.dll")]
    public static extern int CP5200_Net_SplitScreen(byte nCardID, int nWidth, int nHeight, int nWndCount, int[] pWndRect);
    
    static int Main()
    {{
        try
        {{
            byte cardID = {params['cardID']};
            int width = {params['width']};
            int height = {params['height']};
            int wndCount = {params['wndCount']};
            int[] wndRect = {params['wndRect']};
            
            Console.WriteLine("Configurando SplitScreen...");
            Console.WriteLine($"CardID: {{cardID}}, Width: {{width}}, Height: {{height}}, Windows: {{wndCount}}");
            int result = CP5200_Net_SplitScreen(cardID, width, height, wndCount, wndRect);
            Console.WriteLine($"Resultado: {{result}}");
            return result;
        }}
        catch (Exception ex)
        {{
            Console.WriteLine($"Error: {{ex.Message}}");
            return -1;
        }}
    }}
}}
"""
        elif function == "SendText":
            script = f"""
using System;
using System.Runtime.InteropServices;

class CP5200Test
{{
    [DllImport("CP5200.dll")]
    public static extern int CP5200_Net_SendTagText(byte nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);
    
    static int Main()
    {{
        try
        {{
            byte cardID = {params['cardID']};
            int wndNo = {params['wndNo']};
            string text = "{params['text']}";
            int color = {params['color']};
            int fontSize = {params['fontSize']};
            int speed = {params['speed']};
            int effect = {params['effect']};
            int stayTime = {params['stayTime']};
            int alignment = {params['alignment']};
            
            // Convertir string a IntPtr
            IntPtr textPtr = Marshal.StringToHGlobalAnsi(text);
            
            Console.WriteLine("Enviando texto con CP5200_Net_SendTagText...");
            Console.WriteLine($"CardID: {{cardID}}, Window: {{wndNo}}, Text: {{text}}");
            Console.WriteLine($"Color: {{color}}, FontSize: {{fontSize}}, Speed: {{speed}}, Effect: {{effect}}, StayTime: {{stayTime}}, Alignment: {{alignment}}");
            int result = CP5200_Net_SendTagText(cardID, wndNo, textPtr, color, fontSize, speed, effect, stayTime, alignment);
            Console.WriteLine($"Resultado: {{result}}");
            
            // Liberar memoria
            Marshal.FreeHGlobal(textPtr);
            
            return result;
        }}
        catch (Exception ex)
        {{
            Console.WriteLine($"Error: {{ex.Message}}");
            return -1;
        }}
    }}
}}
"""
        else:
            raise ValueError(f"Función no soportada: {function}")
            
        return script
    
    def execute_with_wine(self, script_content):
        """Ejecuta un script de C# con Wine"""
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as f:
                f.write(script_content)
                cs_file = f.name
            
            exe_file = cs_file.replace('.cs', '.exe')
            
            # Compilar con Mono
            compile_result = subprocess.run([
                'mcs', cs_file, '-out:' + exe_file
            ], capture_output=True, text=True)
            
            if compile_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Error compilando: {compile_result.stderr}'
                }
            
            # Ejecutar con Wine
            wine_result = subprocess.run([
                'wine', exe_file
            ], capture_output=True, text=True, cwd=os.path.dirname(self.dll_path))
            
            # Limpiar archivos temporales
            os.unlink(cs_file)
            os.unlink(exe_file)
            
            return {
                'success': True,
                'output': wine_result.stdout,
                'error': wine_result.stderr,
                'returncode': wine_result.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def init_panel(self, panel_ip, port=5200, id_code=0xFFFFFFFF, timeout=600):
        """Inicializa un panel"""
        params = {
            'panelIP': panel_ip,
            'port': port,
            'idCode': id_code,
            'timeout': timeout
        }
        
        script = self.create_cs_script("InitComm", params)
        result = self.execute_with_wine(script)
        
        dll_result = -1
        if result['success']:
            try:
                # Extraer el resultado del output
                for line in result['output'].split('\n'):
                    if line.startswith('Resultado:'):
                        dll_result = int(line.split(':')[1].strip())
                        break
            except:
                pass
        
        return {
            'success': dll_result >= 0,
            'result': dll_result,
            'wine_output': result.get('output', ''),
            'wine_error': result.get('error', ''),
            'wine_returncode': result.get('returncode', -1)
        }
    
    def split_screen(self, card_id, width=64, height=16, wnd_count=1):
        """Configura la división de pantalla"""
        # Para una pantalla 64x16, configuración simple
        wnd_rect = [0, 0, width, height]  # Una sola ventana que ocupa toda la pantalla
        
        params = {
            'cardID': card_id,
            'width': width,
            'height': height,
            'wndCount': wnd_count,
            'wndRect': wnd_rect
        }
        
        script = self.create_cs_script("SplitScreen", params)
        result = self.execute_with_wine(script)
        
        dll_result = -1
        if result['success']:
            try:
                # Extraer el resultado del output
                for line in result['output'].split('\n'):
                    if line.startswith('Resultado:'):
                        dll_result = int(line.split(':')[1].strip())
                        break
            except:
                pass
        
        return {
            'success': dll_result >= 0,
            'result': dll_result,
            'wine_output': result.get('output', ''),
            'wine_error': result.get('error', ''),
            'wine_returncode': result.get('returncode', -1)
        }
    
    def send_text(self, card_id, text, wnd_no=0, color=0xFF, fontSize=16, speed=3, effect=0, stayTime=0, alignment=5):
        """Envía texto a un panel usando el servicio Wine"""
        params = {
            'cardID': card_id,
            'wndNo': wnd_no,
            'text': text,
            'color': color,
            'fontSize': fontSize,
            'speed': speed,
            'effect': effect,
            'stayTime': stayTime,
            'alignment': alignment
        }
        
        script = self.create_cs_script("SendText", params)
        result = self.execute_with_wine(script)
        
        dll_result = -1
        if result['success']:
            try:
                # Extraer el resultado del output
                for line in result['output'].split('\n'):
                    if line.startswith('Resultado:'):
                        dll_result = int(line.split(':')[1].strip())
                        break
            except:
                pass
        
        return {
            'success': dll_result >= 0,
            'result': dll_result,
            'wine_output': result.get('output', ''),
            'wine_error': result.get('error', ''),
            'wine_returncode': result.get('returncode', -1)
        }

# Instancia global del servicio
panel_service = WinePanelService()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'wine-panel-service-debug'})

@app.route('/init', methods=['POST'])
def init_panel():
    try:
        data = request.get_json()
        panel_ip = data.get('panelIP')
        port = data.get('port', 5200)
        id_code = data.get('idCode', 0xFFFFFFFF)
        timeout = data.get('timeout', 600)
        
        if not panel_ip:
            return jsonify({'error': 'panelIP es requerido'}), 400
        
        result = panel_service.init_panel(panel_ip, port, id_code, timeout)
        
        return jsonify({
            'success': result['success'],
            'result': result['result'],
            'panelIP': panel_ip,
            'wine_output': result['wine_output'],
            'wine_error': result['wine_error'],
            'wine_returncode': result['wine_returncode']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/splitscreen', methods=['POST'])
def split_screen():
    try:
        data = request.get_json()
        card_id = data.get('cardID')
        width = data.get('width', 64)
        height = data.get('height', 16)
        wnd_count = data.get('wndCount', 1)
        
        if not card_id:
            return jsonify({'error': 'cardID es requerido'}), 400
        
        result = panel_service.split_screen(card_id, width, height, wnd_count)
        
        return jsonify({
            'success': result['success'],
            'result': result['result'],
            'cardID': card_id,
            'width': width,
            'height': height,
            'wndCount': wnd_count,
            'wine_output': result['wine_output'],
            'wine_error': result['wine_error'],
            'wine_returncode': result['wine_returncode']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sendtext', methods=['POST'])
def send_text():
    try:
        data = request.get_json()
        card_id = data.get('cardID')
        text = data.get('text')
        wnd_no = data.get('wndNo', 0)
        color = data.get('color', 0xFF)  # Rojo por defecto
        fontSize = data.get('fontSize', 16)
        speed = data.get('speed', 3)
        effect = data.get('effect', 0)
        stayTime = data.get('stayTime', 0)
        alignment = data.get('alignment', 5)  # Centro por defecto
        
        if not card_id or not text:
            return jsonify({'error': 'cardID y text son requeridos'}), 400
        
        result = panel_service.send_text(card_id, text, wnd_no, color, fontSize, speed, effect, stayTime, alignment)
        
        return jsonify({
            'success': result['success'],
            'result': result['result'],
            'cardID': card_id,
            'wndNo': wnd_no,
            'text': text,
            'wine_output': result['wine_output'],
            'wine_error': result['wine_error'],
            'wine_returncode': result['wine_returncode']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando Wine Panel Service (Debug)...")
    print(f"📁 DLL Path: {panel_service.dll_path}")
    print(f"🍷 Wine Prefix: {panel_service.wine_prefix}")
    
    app.run(host='0.0.0.0', port=5002, debug=True) 