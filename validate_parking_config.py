#!/usr/bin/env python3
import os
import sys
import csv
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno y DB_URL
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

# Importar modelos
from models import Parking, Access, Panel, User

# Crear engine y sesión
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def ping_device(ip, count=1, timeout=1):
    try:
        # Usar timeout más largo y mejor manejo de errores
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), ip], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=timeout + 2  # Timeout adicional para el proceso
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"    [DEBUG] Timeout pinging {ip}")
        return False
    except Exception as e:
        print(f"    [DEBUG] Error pinging {ip}: {e}")
        return False

def generate_report():
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_parkings": 0,
            "parkings_with_cameras": 0,
            "parkings_with_panels": 0,
            "online_cameras": 0,
            "offline_cameras": 0,
            "online_panels": 0,
            "offline_panels": 0,
            "total_users": 0
        },
        "parkings": [],
        "csv_comparison": {},
        "issues": [],
        "recommendations": []
    }

    # Validar parkings
    print("\n=== PARKINGS EN BASE DE DATOS ===")
    for parking in session.query(Parking).all():
        parking_data = {
            "id": parking.id,
            "name": parking.name,
            "capacity": parking.max_capacity,
            "threshold_dense": parking.threshold_dense,
            "threshold_full": parking.threshold_full,
            "current_occupancy": parking.current_occupancy,
            "status": parking.status,
            "cameras": [],
            "panels": []
        }
        
        print(f"Parking {parking.id}: {parking.name}")
        print(f"  - Capacidad: {parking.max_capacity}")
        print(f"  - Umbral denso: {parking.threshold_dense}")
        print(f"  - Umbral completo: {parking.threshold_full}")
        print(f"  - Ocupación actual: {parking.current_occupancy}")
        print(f"  - Estado: {parking.status}")
        
        # Cámaras
        accesses = session.query(Access).filter_by(parking_id=parking.id).all()
        if not accesses:
            print("    * Sin cámaras asociadas")
        else:
            for access in accesses:
                online = ping_device(access.ip)
                estado = "ONLINE" if online else "OFFLINE"
                print(f"    * Cámara: {access.name} (IP: {access.ip}, Línea: {access.line}) - {estado}")
                
                camera_data = {
                    "name": access.name,
                    "ip": access.ip,
                    "line": access.line,
                    "online": online
                }
                parking_data["cameras"].append(camera_data)
                
                if online:
                    report["summary"]["online_cameras"] += 1
                else:
                    report["summary"]["offline_cameras"] += 1
        
        # Paneles
        panels = session.query(Panel).filter_by(parking_id=parking.id).all()
        if not panels:
            print("    * Sin paneles asociados")
        else:
            for panel in panels:
                online = ping_device(panel.ip)
                estado = "ONLINE" if online else "OFFLINE"
                print(f"    * Panel: {panel.name} (IP: {panel.ip}, Estado: {panel.status}, Ping: {estado})")
                
                panel_data = {
                    "name": panel.name,
                    "ip": panel.ip,
                    "status": panel.status,
                    "online": online
                }
                parking_data["panels"].append(panel_data)
                
                if online:
                    report["summary"]["online_panels"] += 1
                else:
                    report["summary"]["offline_panels"] += 1
        
        report["parkings"].append(parking_data)
        report["summary"]["total_parkings"] += 1
        
        if parking_data["cameras"]:
            report["summary"]["parkings_with_cameras"] += 1
        if parking_data["panels"]:
            report["summary"]["parkings_with_panels"] += 1
        
        print("-")

    # Validar usuarios
    users = session.query(User).all()
    report["summary"]["total_users"] = len(users)
    print(f"\n=== USUARIOS EN BASE DE DATOS ===")
    print(f"Total usuarios: {len(users)}")
    for user in users:
        print(f"  - {user.name} ({user.email}) - Activo: {user.is_active}")

    # Leer accesses.csv
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv_templates', 'accesses.csv')
    print("\n=== CÁMARAS ESPERADAS SEGÚN accesses.csv ===")
    csv_accesses = []
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(f"Parking {row['parking_id']}: {row['name']} (IP: {row['ip']}, Línea: {row['line']})")
                csv_accesses.append((int(row['parking_id']), row['ip'], int(row['line']), row['name']))
    else:
        print("No se encontró accesses.csv")
        report["issues"].append("No se encontró el archivo accesses.csv")

    # Comparar cámaras en DB vs CSV
    print("\n=== COMPARATIVA CÁMARAS DB vs CSV ===")
    db_accesses = set((a.parking_id, a.ip, a.line, a.name) for a in session.query(Access).all())
    csv_accesses_set = set(csv_accesses)

    faltan_en_db = csv_accesses_set - db_accesses
    sobran_en_db = db_accesses - csv_accesses_set

    report["csv_comparison"] = {
        "missing_in_db": list(faltan_en_db),
        "extra_in_db": list(sobran_en_db),
        "csv_total": len(csv_accesses),
        "db_total": len(db_accesses)
    }

    if faltan_en_db:
        print("Cámaras en CSV pero NO en DB:")
        for acc in faltan_en_db:
            print(f"  - Parking {acc[0]}: {acc[3]} (IP: {acc[1]}, Línea: {acc[2]})")
            report["issues"].append(f"Cámara en CSV pero no en DB: Parking {acc[0]} - {acc[3]}")
    else:
        print("Todas las cámaras del CSV están en la base de datos.")

    if sobran_en_db:
        print("Cámaras en DB pero NO en CSV:")
        for acc in sobran_en_db:
            print(f"  - Parking {acc[0]}: {acc[3]} (IP: {acc[1]}, Línea: {acc[2]})")
            report["issues"].append(f"Cámara en DB pero no en CSV: Parking {acc[0]} - {acc[3]}")
    else:
        print("No hay cámaras extra en la base de datos respecto al CSV.")

    # Generar recomendaciones
    if report["summary"]["offline_cameras"] > 0:
        report["recommendations"].append(f"Hay {report['summary']['offline_cameras']} cámaras offline. Verificar conectividad de red y estado de los dispositivos.")
    
    if report["summary"]["offline_panels"] > 0:
        report["recommendations"].append(f"Hay {report['summary']['offline_panels']} paneles offline. Verificar conectividad de red y estado de los dispositivos.")
    
    if report["summary"]["offline_cameras"] == report["summary"]["online_cameras"] + report["summary"]["offline_cameras"]:
        report["recommendations"].append("TODAS las cámaras están offline. Verificar configuración de red o firewall.")
    
    if report["summary"]["offline_panels"] == report["summary"]["online_panels"] + report["summary"]["offline_panels"]:
        report["recommendations"].append("TODOS los paneles están offline. Verificar configuración de red o firewall.")

    # Guardar informe
    report_filename = f"parking_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== INFORME GENERADO ===")
    print(f"Archivo: {report_filename}")
    print(f"Resumen:")
    print(f"  - Total parkings: {report['summary']['total_parkings']}")
    print(f"  - Parkings con cámaras: {report['summary']['parkings_with_cameras']}")
    print(f"  - Parkings con paneles: {report['summary']['parkings_with_panels']}")
    print(f"  - Cámaras online: {report['summary']['online_cameras']}")
    print(f"  - Cámaras offline: {report['summary']['offline_cameras']}")
    print(f"  - Paneles online: {report['summary']['online_panels']}")
    print(f"  - Paneles offline: {report['summary']['offline_panels']}")
    print(f"  - Total usuarios: {report['summary']['total_users']}")
    
    if report["issues"]:
        print(f"\nProblemas detectados: {len(report['issues'])}")
        for issue in report["issues"]:
            print(f"  - {issue}")
    
    if report["recommendations"]:
        print(f"\nRecomendaciones: {len(report['recommendations'])}")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

    session.close()
    return report

if __name__ == "__main__":
    generate_report() 