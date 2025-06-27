#!/usr/bin/env python3
"""
Integración del Servicio de Paneles C# con Backend Python
Modifica el backend para usar el servicio .NET
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def backup_original_files():
    """Hacer backup de archivos originales"""
    print("📦 HACIENDO BACKUP DE ARCHIVOS ORIGINALES")
    print("=" * 50)
    
    files_to_backup = [
        "src/panel_client.py",
        "src/panel_communication.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ Backup creado: {backup_path}")
        else:
            print(f"   ⚠️  Archivo no encontrado: {file_path}")

def update_panel_client():
    """Actualizar panel_client.py para usar el servicio C#"""
    print("\n🔧 ACTUALIZANDO PANEL_CLIENT.PY")
    print("=" * 50)
    
    # Leer el archivo original
    original_file = "src/panel_client.py"
    if not os.path.exists(original_file):
        print(f"   ❌ Archivo no encontrado: {original_file}")
        return False
    
    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Agregar import del servicio
    service_import = """
# Import del servicio C#
try:
    from panel_service_client import send_to_panel_via_service
    PANEL_SERVICE_AVAILABLE = True
except ImportError:
    PANEL_SERVICE_AVAILABLE = False
    print("⚠️  Panel service no disponible, usando método original")
"""
    
    # Buscar la función send_to_panel y modificarla
    if "def send_to_panel" in content:
        # Reemplazar la función original
        new_function = '''
def send_to_panel(panel_ip: str, text: str) -> bool:
    """
    Enviar mensaje a un panel via HTTP
    """
    # Intentar usar el servicio C# primero
    if 'PANEL_SERVICE_AVAILABLE' in globals() and PANEL_SERVICE_AVAILABLE:
        try:
            return send_to_panel_via_service(panel_ip, text)
        except Exception as e:
            print(f"Error con servicio C#, usando método original: {e}")
    
    # Método original como fallback
    try:
        payload = {'message': text}
        r = requests.post(API_ENDPOINT_TEMPLATE.format(ip=panel_ip), json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"Error enviando mensaje a panel {panel_ip}: {e}")
        return False
'''
        
        # Reemplazar la función
        import re
        pattern = r'def send_to_panel\(panel_ip: str, text: str\) -> bool:.*?return False'
        content = re.sub(pattern, new_function, content, flags=re.DOTALL)
        
        # Agregar el import al inicio
        content = service_import + content
        
        # Guardar el archivo modificado
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Archivo actualizado: {original_file}")
        return True
    else:
        print(f"   ❌ No se encontró la función send_to_panel en {original_file}")
        return False

def create_service_wrapper():
    """Crear wrapper para el servicio de paneles"""
    print("\n🔧 CREANDO WRAPPER DEL SERVICIO")
    print("=" * 50)
    
    wrapper_content = '''#!/usr/bin/env python3
"""
Wrapper para el servicio de paneles C#
Integra el servicio .NET con el backend Python
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import del cliente del servicio
try:
    from panel_service_client import PanelServiceClient, get_panel_client
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False
    print("⚠️  Panel service client no disponible")

logger = logging.getLogger(__name__)

class PanelServiceWrapper:
    """Wrapper para el servicio de paneles C#"""
    
    def __init__(self, service_url: str = "http://localhost:5001"):
        self.service_url = service_url
        self.client = None
        
        if SERVICE_AVAILABLE:
            try:
                self.client = get_panel_client(service_url)
                logger.info(f"Cliente de servicio de paneles inicializado: {service_url}")
            except Exception as e:
                logger.error(f"Error inicializando cliente de servicio: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Verificar si el servicio está disponible"""
        if not SERVICE_AVAILABLE or not self.client:
            return False
        
        try:
            return self.client.is_service_online()
        except:
            return False
    
    def send_message(self, panel_ip: str, message: str) -> bool:
        """Enviar mensaje a un panel"""
        if not self.is_available():
            logger.warning("Servicio de paneles no disponible")
            return False
        
        try:
            response = self.client.send_message(panel_ip, message)
            success = response.success
            
            if success:
                logger.info(f"Mensaje enviado a panel {panel_ip}: {message}")
            else:
                logger.error(f"Error enviando mensaje a panel {panel_ip}: {response.message}")
            
            return success
        except Exception as e:
            logger.error(f"Error enviando mensaje a panel {panel_ip}: {e}")
            return False
    
    def send_occupancy(self, panel_ip: str, current: int, total: int, status: str) -> bool:
        """Enviar información de ocupación a un panel"""
        if not self.is_available():
            logger.warning("Servicio de paneles no disponible")
            return False
        
        try:
            response = self.client.send_occupancy(panel_ip, current, total, status)
            success = response.success
            
            if success:
                logger.info(f"Ocupación enviada a panel {panel_ip}: {current}/{total} ({status})")
            else:
                logger.error(f"Error enviando ocupación a panel {panel_ip}: {response.message}")
            
            return success
        except Exception as e:
            logger.error(f"Error enviando ocupación a panel {panel_ip}: {e}")
            return False
    
    def broadcast_message(self, message: str, panel_ips: Optional[List[str]] = None) -> Dict:
        """Enviar mensaje a todos los paneles"""
        if not self.is_available():
            logger.warning("Servicio de paneles no disponible")
            return {"success": False, "message": "Servicio no disponible"}
        
        try:
            response = self.client.broadcast_message(message, panel_ips)
            
            result = {
                "success": response.success_count > 0,
                "total_panels": response.total_panels,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "message": f"Broadcast completado: {response.success_count}/{response.total_panels} exitosos"
            }
            
            logger.info(f"Broadcast completado: {response.success_count}/{response.total_panels} exitosos")
            return result
        except Exception as e:
            logger.error(f"Error en broadcast: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_panels_status(self) -> List[Dict]:
        """Obtener estado de todos los paneles"""
        if not self.is_available():
            logger.warning("Servicio de paneles no disponible")
            return []
        
        try:
            panels = self.client.get_all_panels_status()
            return [
                {
                    "ip": panel.ip,
                    "name": panel.name,
                    "online": panel.online,
                    "status": panel.status,
                    "last_communication": panel.last_communication.isoformat(),
                    "response_time": panel.response_time
                }
                for panel in panels
            ]
        except Exception as e:
            logger.error(f"Error obteniendo estado de paneles: {e}")
            return []
    
    def test_panel(self, panel_ip: str) -> Dict:
        """Testear un panel"""
        if not self.is_available():
            logger.warning("Servicio de paneles no disponible")
            return {"success": False, "message": "Servicio no disponible"}
        
        try:
            response = self.client.test_panel(panel_ip)
            return {
                "success": response.success,
                "message": response.message,
                "response_time": response.response_time
            }
        except Exception as e:
            logger.error(f"Error testeando panel {panel_ip}: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

# Instancia global del wrapper
_panel_service_wrapper = None

def get_panel_service_wrapper() -> Optional[PanelServiceWrapper]:
    """Obtener instancia del wrapper del servicio de paneles"""
    global _panel_service_wrapper
    
    if _panel_service_wrapper is None:
        _panel_service_wrapper = PanelServiceWrapper()
    
    return _panel_service_wrapper

def send_to_panel_via_service(panel_ip: str, message: str) -> bool:
    """Función de conveniencia para enviar mensaje a panel"""
    wrapper = get_panel_service_wrapper()
    if wrapper:
        return wrapper.send_message(panel_ip, message)
    return False
'''
    
    wrapper_file = "src/panel_service_wrapper.py"
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(wrapper_content)
    
    print(f"   ✅ Wrapper creado: {wrapper_file}")
    return True

def update_api_server():
    """Actualizar api_server.py para usar el servicio de paneles"""
    print("\n🔧 ACTUALIZANDO API_SERVER.PY")
    print("=" * 50)
    
    api_file = "src/api_server.py"
    if not os.path.exists(api_file):
        print(f"   ❌ Archivo no encontrado: {api_file}")
        return False
    
    # Leer el archivo
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Agregar import del wrapper
    wrapper_import = """
# Import del wrapper del servicio de paneles
try:
    from panel_service_wrapper import get_panel_service_wrapper
    PANEL_SERVICE_WRAPPER_AVAILABLE = True
except ImportError:
    PANEL_SERVICE_WRAPPER_AVAILABLE = False
    print("⚠️  Panel service wrapper no disponible")
"""
    
    # Buscar la función send_to_panel y modificarla
    if "def send_to_panel" in content:
        # Agregar el import al inicio
        content = wrapper_import + content
        
        # Buscar y modificar la función send_to_panel
        import re
        pattern = r'def send_to_panel\(panel_ip: str, text: str\) -> bool:'
        replacement = '''def send_to_panel(panel_ip: str, text: str) -> bool:
    """
    Enviar mensaje a un panel via HTTP o servicio C#
    """
    # Intentar usar el servicio C# primero
    if 'PANEL_SERVICE_WRAPPER_AVAILABLE' in globals() and PANEL_SERVICE_WRAPPER_AVAILABLE:
        try:
            wrapper = get_panel_service_wrapper()
            if wrapper and wrapper.is_available():
                return wrapper.send_message(panel_ip, text)
        except Exception as e:
            logger.warning(f"Error con servicio C#, usando método original: {e}")
    
    # Método original como fallback'''
        
        content = re.sub(pattern, replacement, content)
        
        # Guardar el archivo modificado
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Archivo actualizado: {api_file}")
        return True
    else:
        print(f"   ❌ No se encontró la función send_to_panel en {api_file}")
        return False

def create_integration_test():
    """Crear test de integración"""
    print("\n🧪 CREANDO TEST DE INTEGRACIÓN")
    print("=" * 50)
    
    test_content = '''#!/usr/bin/env python3
"""
Test de Integración - Servicio C# + Backend Python
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from panel_service_wrapper import get_panel_service_wrapper
from panel_service_client import get_panel_client

def test_integration():
    """Test de integración completa"""
    print("🚦 TEST DE INTEGRACIÓN - SERVICIO C# + PYTHON")
    print("=" * 60)
    
    # Test del wrapper
    print("1. Testeando wrapper del servicio...")
    wrapper = get_panel_service_wrapper()
    
    if wrapper:
        print("   ✅ Wrapper creado")
        
        # Test de disponibilidad
        available = wrapper.is_available()
        print(f"   Servicio disponible: {'✅' if available else '❌'}")
        
        if available:
            # Test de envío de mensaje
            print("2. Testeando envío de mensaje...")
            success = wrapper.send_message("172.20.17.50", "TEST INTEGRACIÓN")
            print(f"   Envío: {'✅ OK' if success else '❌ FAIL'}")
            
            # Test de estado de paneles
            print("3. Testeando estado de paneles...")
            status = wrapper.get_panels_status()
            print(f"   Paneles encontrados: {len(status)}")
            
            for panel in status[:3]:  # Mostrar solo los primeros 3
                status_icon = "✅" if panel['online'] else "❌"
                print(f"   {status_icon} {panel['ip']}: {panel['status']}")
        else:
            print("   ⚠️  Servicio no disponible, verificar que esté ejecutándose")
    else:
        print("   ❌ No se pudo crear el wrapper")
    
    # Test del cliente directo
    print("\\n4. Testeando cliente directo...")
    try:
        client = get_panel_client()
        if client.is_service_online():
            print("   ✅ Cliente directo funciona")
            
            # Test de broadcast
            print("5. Testeando broadcast...")
            result = wrapper.broadcast_message("BROADCAST TEST INTEGRACIÓN")
            print(f"   Broadcast: {'✅ OK' if result['success'] else '❌ FAIL'}")
            print(f"   Mensaje: {result['message']}")
        else:
            print("   ❌ Cliente directo no funciona")
    except Exception as e:
        print(f"   ❌ Error con cliente directo: {e}")
    
    print("\\n" + "=" * 60)
    print("📊 RESUMEN DE INTEGRACIÓN")
    print("=" * 60)
    print("Si todos los tests son exitosos, la integración está funcionando.")
    print("El backend Python ahora usa el servicio C# para comunicación con paneles.")

if __name__ == "__main__":
    test_integration()
'''
    
    test_file = "test_integration.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"   ✅ Test de integración creado: {test_file}")
    return True

def main():
    """Función principal"""
    print("🔧 INTEGRANDO SERVICIO DE PANELES C# CON BACKEND PYTHON")
    print("=" * 70)
    print("Este script integra el servicio .NET con el backend Python existente")
    print("=" * 70)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("src"):
        print("❌ Error: No se encontró el directorio 'src'")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return
    
    steps = [
        ("Backup de archivos originales", backup_original_files),
        ("Crear wrapper del servicio", create_service_wrapper),
        ("Actualizar panel_client.py", update_panel_client),
        ("Actualizar api_server.py", update_api_server),
        ("Crear test de integración", create_integration_test)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*70}")
        print(f"PASO: {step_name}")
        print(f"{'='*70}")
        
        try:
            result = step_func()
            results.append((step_name, result))
            
            if result:
                print(f"✅ {step_name}: EXITOSO")
            else:
                print(f"❌ {step_name}: FALLIDO")
                
        except Exception as e:
            print(f"❌ {step_name}: ERROR - {e}")
            results.append((step_name, False))
    
    # Resumen final
    print(f"\n{'='*70}")
    print("📊 RESUMEN DE INTEGRACIÓN")
    print(f"{'='*70}")
    
    total_steps = len(results)
    successful_steps = sum(1 for _, result in results if result)
    
    print(f"Total pasos: {total_steps}")
    print(f"Exitosos: {successful_steps}")
    print(f"Fallidos: {total_steps - successful_steps}")
    
    print(f"\n📋 RESULTADOS DETALLADOS:")
    for step_name, result in results:
        status = "✅ EXITOSO" if result else "❌ FALLIDO"
        print(f"  {step_name}: {status}")
    
    if successful_steps == total_steps:
        print(f"\n🎉 ¡INTEGRACIÓN COMPLETADA!")
        print("   - El backend Python ahora usa el servicio C#")
        print("   - Ejecuta 'python test_integration.py' para verificar")
        print("   - El servicio C# debe estar ejecutándose en http://localhost:5001")
    else:
        print(f"\n⚠️  ALGUNOS PASOS FALLARON")
        print("   - Revisar los errores anteriores")
        print("   - Verificar que los archivos existan")
        print("   - Intentar ejecutar los pasos fallidos manualmente")

if __name__ == "__main__":
    main() 