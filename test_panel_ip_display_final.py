#!/usr/bin/env python3
"""
Test Final - Enviar IP de cada panel
Prueba que cada panel muestre su propia IP
"""

import requests
import time
import json
from datetime import datetime

def test_panel_ip_display():
    """Test para enviar la IP de cada panel"""
    print("🎯 TEST FINAL: ENVIAR IP DE CADA PANEL")
    print("=" * 60)
    print("Este test envía la IP de cada panel para verificar")
    print("que los paneles muestran correctamente los mensajes")
    print("=" * 60)
    
    # Configuración del servicio
    service_url = "http://localhost:5001"
    
    # Lista de paneles con sus nombres
    panels = [
        {"ip": "172.20.17.50", "name": "PANEL C. ESPORTIVA"},
        {"ip": "172.20.5.50", "name": "PANEL BASSETA 1"},
        {"ip": "172.20.5.51", "name": "PANEL BASSETA 2"},
        {"ip": "172.20.8.50", "name": "PANEL PITERES"},
        {"ip": "172.20.4.50", "name": "PANEL PALAU"},
        {"ip": "172.20.4.51", "name": "PANEL COCOLISO"},
        {"ip": "172.20.4.52", "name": "BELLES ARTS 2"},
        {"ip": "172.20.4.53", "name": "BELLES ARTS"},
        {"ip": "172.20.2.50", "name": "PANEL RENFE"},
        {"ip": "172.20.1.50", "name": "PANEL ALTEA VELLA"}
    ]
    
    results = []
    
    print(f"📡 Enviando IP a {len(panels)} paneles...")
    print()
    
    for i, panel in enumerate(panels, 1):
        print(f"🔸 Panel {i}: {panel['name']} ({panel['ip']})")
        
        # Crear mensaje con la IP
        message = f"IP: {panel['ip']}"
        
        try:
            # Enviar mensaje al panel
            response = requests.post(
                f"{service_url}/api/panel/send",
                json={
                    "panelIP": panel['ip'],
                    "message": message
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result_data = response.json()
                success = result_data.get('success', False)
                
                if success:
                    print(f"   ✅ Enviado: '{message}'")
                    print(f"   ⏱️  Tiempo: {result_data.get('responseTime', 0):.2f}ms")
                    results.append({"panel": panel, "success": True, "message": message})
                else:
                    print(f"   ❌ Error: {result_data.get('message', 'Error desconocido')}")
                    results.append({"panel": panel, "success": False, "error": result_data.get('message')})
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                results.append({"panel": panel, "success": False, "error": f"HTTP {response.status_code}"})
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results.append({"panel": panel, "success": False, "error": str(e)})
        
        print()
        time.sleep(1)  # Pausa entre envíos
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN DEL TEST")
    print("=" * 60)
    
    total_panels = len(panels)
    successful = sum(1 for r in results if r['success'])
    failed = total_panels - successful
    
    print(f"Total paneles: {total_panels}")
    print(f"Exitosos: {successful}")
    print(f"Fallidos: {failed}")
    print(f"Porcentaje éxito: {successful/total_panels*100:.1f}%")
    
    print()
    print("📋 RESULTADOS DETALLADOS:")
    for i, result in enumerate(results, 1):
        panel = result['panel']
        status = "✅ EXITOSO" if result['success'] else "❌ FALLIDO"
        print(f"  {i:2d}. {panel['name']} ({panel['ip']}): {status}")
        if result['success']:
            print(f"      📺 Mensaje: '{result['message']}'")
        else:
            print(f"      ❌ Error: {result['error']}")
    
    print()
    print("🎯 INSTRUCCIONES PARA VERIFICACIÓN:")
    print("1. Verificar físicamente cada panel")
    print("2. Confirmar que muestra su IP correspondiente")
    print("3. Si algún panel no muestra la IP, verificar:")
    print("   - Conectividad de red")
    print("   - Configuración del panel")
    print("   - Estado del servicio")
    
    if successful == total_panels:
        print()
        print("🎉 ¡TEST COMPLETADO EXITOSAMENTE!")
        print("   Todos los paneles deberían mostrar su IP")
        print("   Verificar físicamente que los mensajes se ven correctamente")
    else:
        print()
        print("⚠️  ALGUNOS PANELES FALLARON")
        print("   Revisar los errores anteriores")
        print("   Verificar conectividad y configuración")
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"panel_ip_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_panels": total_panels,
            "successful": successful,
            "failed": failed,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {filename}")

if __name__ == "__main__":
    test_panel_ip_display() 