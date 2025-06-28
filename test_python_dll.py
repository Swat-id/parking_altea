#!/usr/bin/env python3
import ctypes
import ctypes.util
import sys
import os

def test_cp5200_dll():
    print("🔍 Probando carga de DLL CP5200 con Python ctypes...")
    
    try:
        # Intentar cargar la DLL
        dll_path = "/opt/parking-panel-service/CP5200.dll"
        
        if not os.path.exists(dll_path):
            print(f"❌ DLL no encontrada en: {dll_path}")
            return False
            
        print(f"✅ DLL encontrada en: {dll_path}")
        
        # Intentar cargar la DLL
        try:
            cp5200 = ctypes.CDLL(dll_path)
            print("✅ DLL cargada exitosamente con ctypes")
            
            # Definir las funciones
            cp5200.CP5200_Net_Init.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32, ctypes.c_int32]
            cp5200.CP5200_Net_Init.restype = ctypes.c_int32
            
            cp5200.CP5200_Net_SendText.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
            cp5200.CP5200_Net_SendText.restype = ctypes.c_int32
            
            print("✅ Funciones definidas correctamente")
            
            # Probar inicialización
            panel_ip = 0x321412AC  # 172.20.17.50
            id_code = 0xFFFFFFFF   # 255.255.255.255
            
            print(f"📡 Probando inicialización con IP: {panel_ip:08X}")
            result = cp5200.CP5200_Net_Init(panel_ip, 5200, id_code, 600)
            print(f"📊 Resultado de inicialización: {result}")
            
            if result == 1:
                print("✅ Inicialización exitosa")
                
                # Probar envío de texto
                text = b"TEST PYTHON"
                print(f"📝 Probando envío de texto: {text}")
                send_result = cp5200.CP5200_Net_SendText(panel_ip, text, 3000, 16, 3, 0, 0, 0)
                print(f"📊 Resultado de envío: {send_result}")
                
                return True
            else:
                print(f"❌ Error en inicialización: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error cargando DLL: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    success = test_cp5200_dll()
    if success:
        print("🎉 ¡Prueba exitosa! Python puede usar la DLL CP5200")
    else:
        print("💥 Prueba fallida")
    sys.exit(0 if success else 1) 