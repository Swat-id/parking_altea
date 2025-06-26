#!/usr/bin/env python3
"""
Script para corregir el estado de los paneles en la base de datos
- Actualizar estado basándose en conectividad real (ping)
- Corregir inconsistencias entre BD y conectividad
"""

import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno y DB_URL
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

# Importar modelos
from models import Panel

# Crear engine y sesión
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def ping_device(ip, count=1, timeout=1):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), ip], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=timeout + 2
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        return False

def fix_panels_status():
    """Corregir el estado de todos los paneles basándose en conectividad real"""
    
    print("🔧 CORRECCIÓN DE ESTADO DE PANELES")
    print("=" * 60)
    
    # Obtener todos los paneles
    panels = session.query(Panel).all()
    
    print(f"Total paneles a verificar: {len(panels)}")
    print()
    
    corrected_count = 0
    online_count = 0
    offline_count = 0
    
    for panel in panels:
        print(f"Panel: {panel.name}")
        print(f"  - IP: {panel.ip}")
        print(f"  - Estado actual en BD: {panel.status}")
        
        # Verificar conectividad real
        online = ping_device(panel.ip)
        print(f"  - Conectividad real: {'✅ ONLINE' if online else '❌ OFFLINE'}")
        
        # Determinar estado correcto
        correct_status = 'ONLINE' if online else 'OFFLINE'
        
        # Verificar si necesita corrección
        if panel.status != correct_status:
            print(f"  - ⚠️  NECESITA CORRECCIÓN: {panel.status} → {correct_status}")
            
            # Actualizar estado en la base de datos
            panel.status = correct_status
            panel.last_update = datetime.now()
            
            corrected_count += 1
            print(f"  - ✅ CORREGIDO")
        else:
            print(f"  - ✅ Estado correcto")
        
        # Contar estados finales
        if correct_status == 'ONLINE':
            online_count += 1
        else:
            offline_count += 1
        
        print("-" * 40)
    
    # Guardar cambios en la base de datos
    try:
        session.commit()
        print(f"\n💾 Cambios guardados en la base de datos")
    except Exception as e:
        print(f"\n❌ Error guardando cambios: {e}")
        session.rollback()
        return
    
    print(f"\n📊 RESUMEN DE CORRECCIÓN:")
    print(f"  - Paneles corregidos: {corrected_count}")
    print(f"  - Paneles ONLINE: {online_count}")
    print(f"  - Paneles OFFLINE: {offline_count}")
    print(f"  - Total: {len(panels)}")
    
    if corrected_count == 0:
        print(f"  🎉 Todos los paneles ya tenían el estado correcto")
    else:
        print(f"  ✅ Se corrigieron {corrected_count} paneles")
    
    session.close()

def verify_correction():
    """Verificar que las correcciones se aplicaron correctamente"""
    
    print(f"\n🔍 VERIFICACIÓN POST-CORRECCIÓN")
    print("=" * 60)
    
    session = Session()
    panels = session.query(Panel).all()
    
    inconsistencies = 0
    
    for panel in panels:
        online = ping_device(panel.ip)
        correct_status = 'ONLINE' if online else 'OFFLINE'
        
        if panel.status != correct_status:
            print(f"  ⚠️  {panel.name}: Estado incorrecto ({panel.status} vs {correct_status})")
            inconsistencies += 1
        else:
            print(f"  ✅ {panel.name}: Estado correcto ({panel.status})")
    
    print(f"\n📈 RESULTADO:")
    print(f"  - Inconsistencias restantes: {inconsistencies}")
    
    if inconsistencies == 0:
        print(f"  🎉 Todos los paneles tienen el estado correcto")
    else:
        print(f"  ⚠️  Aún hay {inconsistencies} inconsistencias")
    
    session.close()

def test_panel_api():
    """Probar que la API refleja los cambios"""
    
    print(f"\n🌐 VERIFICACIÓN DE API")
    print("=" * 60)
    
    import requests
    
    try:
        response = requests.get("http://157.180.91.63:6001/panels", timeout=5)
        if response.status_code == 200:
            panels_api = response.json()
            
            online_api = sum(1 for p in panels_api if p.get('status') == 'ONLINE')
            offline_api = sum(1 for p in panels_api if p.get('status') == 'OFFLINE')
            
            print(f"✅ API de paneles disponible")
            print(f"  - Paneles en API: {len(panels_api)}")
            print(f"  - ONLINE en API: {online_api}")
            print(f"  - OFFLINE en API: {offline_api}")
            
            # Mostrar algunos paneles como ejemplo
            print(f"  - Ejemplos:")
            for panel in panels_api[:3]:
                print(f"    * {panel.get('name', 'N/A')}: {panel.get('status', 'N/A')}")
                
        else:
            print(f"❌ Error en API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error conectando a API: {e}")

if __name__ == "__main__":
    print(f"🚀 Iniciando corrección de estado de paneles - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar corrección
    fix_panels_status()
    
    # Verificar corrección
    verify_correction()
    
    # Probar API
    test_panel_api()
    
    print(f"\n✅ Proceso completado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 