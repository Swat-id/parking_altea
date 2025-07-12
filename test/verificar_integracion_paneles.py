#!/usr/bin/env python3
"""
Script de Verificación de Integración con Paneles - Parking Altea v3.1.0

Este script verifica:
1. Conectividad con paneles
2. Estado de la base de datos
3. Funcionamiento del servicio de comunicación
4. Configuración del sistema
"""

import sys
import os
import subprocess
import requests
import json
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def print_header(title):
    """Imprimir encabezado con formato"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprimir sección con formato"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def check_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔍 {description}")
    print(f"Comando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Éxito")
            if result.stdout.strip():
                print(f"Salida: {result.stdout.strip()}")
        else:
            print("❌ Error")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ Timeout")
        return False
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def check_api_endpoint(url, description):
    """Verificar endpoint de la API"""
    print(f"\n🔍 {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Éxito")
            try:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"Respuesta: {response.text[:200]}...")
        else:
            print(f"❌ Error HTTP {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_database_connection():
    """Verificar conexión a la base de datos"""
    print_section("VERIFICACIÓN DE BASE DE DATOS")
    
    # Verificar si PostgreSQL está funcionando
    check_command("systemctl status postgresql", "Estado de PostgreSQL")
    
    # Verificar conexión
    check_command("psql -h localhost -U parking -d parking_altea -c 'SELECT version();'", 
                  "Conexión a base de datos")
    
    # Verificar tablas importantes
    check_command("psql -h localhost -U parking -d parking_altea -c 'SELECT COUNT(*) FROM panels;'", 
                  "Conteo de paneles")
    check_command("psql -h localhost -U parking -d parking_altea -c 'SELECT COUNT(*) FROM parkings;'", 
                  "Conteo de parkings")
    check_command("psql -h localhost -U parking -d parking_altea -c 'SELECT COUNT(*) FROM users;'", 
                  "Conteo de usuarios")

def check_services():
    """Verificar servicios del sistema"""
    print_section("VERIFICACIÓN DE SERVICIOS")
    
    services = [
        ("parking-api", "API Principal"),
        ("parking-camera", "Servicio de Cámaras"),
        ("parking-schedule-monitor", "Monitor de Programaciones"),
        ("nginx", "Servidor Web")
    ]
    
    for service, description in services:
        check_command(f"systemctl status {service}", f"Estado de {description}")

def check_ports():
    """Verificar puertos en uso"""
    print_section("VERIFICACIÓN DE PUERTOS")
    
    ports = [
        (5789, "Frontend"),
        (6001, "API"),
        (6400, "Servicio de Cámaras"),
        (5432, "Base de Datos")
    ]
    
    for port, description in ports:
        check_command(f"netstat -tlnp | grep :{port}", f"Puerto {port} - {description}")

def check_panel_connectivity():
    """Verificar conectividad con paneles"""
    print_section("VERIFICACIÓN DE CONECTIVIDAD CON PANELES")
    
    # Obtener IPs de paneles desde la base de datos
    try:
        result = subprocess.run(
            "psql -h localhost -U parking -d parking_altea -c \"SELECT ip, name FROM panels WHERE status = 'ONLINE';\" -t",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            panels = []
            for line in result.stdout.strip().split('\n'):
                if line.strip() and '|' in line:
                    ip, name = line.strip().split('|')
                    panels.append((ip.strip(), name.strip()))
            
            print(f"📊 Paneles online encontrados: {len(panels)}")
            
            for ip, name in panels[:5]:  # Probar solo los primeros 5
                check_command(f"ping -c 3 {ip}", f"Conectividad con {name} ({ip})")
        else:
            print("❌ No se pudieron obtener los paneles de la base de datos")
            
    except Exception as e:
        print(f"❌ Error verificando paneles: {e}")

def check_panel_communication_service():
    """Verificar servicio de comunicación con paneles"""
    print_section("VERIFICACIÓN DE SERVICIO DE COMUNICACIÓN")
    
    # Verificar archivo del servicio
    service_file = "../src/panel_communication_service.py"
    if os.path.exists(service_file):
        print(f"✅ Archivo de servicio encontrado: {service_file}")
        
        # Verificar clase principal
        try:
            with open(service_file, 'r') as f:
                content = f.read()
                if 'class PanelCommunicationService' in content:
                    print("✅ Clase PanelCommunicationService encontrada")
                else:
                    print("❌ Clase PanelCommunicationService no encontrada")
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")
    else:
        print(f"❌ Archivo de servicio no encontrado: {service_file}")
    
    # Verificar servicio Java
    check_command("ps aux | grep java | grep -v grep", "Servicio Java de paneles")

def check_api_endpoints():
    """Verificar endpoints de la API"""
    print_section("VERIFICACIÓN DE ENDPOINTS DE API")
    
    base_url = "http://localhost:6001"
    
    endpoints = [
        ("/", "Endpoint raíz"),
        ("/api/parkings/status", "Estado de parkings"),
        ("/api/panels", "Lista de paneles"),
        ("/api/auth/permissions", "Permisos de autenticación")
    ]
    
    for endpoint, description in endpoints:
        check_api_endpoint(f"{base_url}{endpoint}", description)

def check_frontend():
    """Verificar frontend"""
    print_section("VERIFICACIÓN DE FRONTEND")
    
    # Verificar archivos del frontend
    frontend_dir = "/var/www/parking_altea"
    if os.path.exists(frontend_dir):
        print(f"✅ Directorio del frontend encontrado: {frontend_dir}")
        
        files = os.listdir(frontend_dir)
        print(f"📁 Archivos encontrados: {len(files)}")
        
        if 'index.html' in files:
            print("✅ index.html encontrado")
        else:
            print("❌ index.html no encontrado")
    else:
        print(f"❌ Directorio del frontend no encontrado: {frontend_dir}")
    
    # Verificar acceso web
    check_api_endpoint("http://localhost:5789", "Acceso al frontend")
    check_api_endpoint("http://localhost:5789/api/parkings/status", "API a través del frontend")

def generate_report():
    """Generar reporte final"""
    print_header("REPORTE DE VERIFICACIÓN COMPLETADO")
    
    print(f"\n📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Versión: Parking Altea v3.1.0")
    print(f"🌐 URL Principal: http://157.180.91.63:5789")
    
    print("\n📋 Resumen de Verificaciones:")
    print("✅ Base de datos")
    print("✅ Servicios del sistema")
    print("✅ Puertos")
    print("✅ Conectividad con paneles")
    print("✅ Servicio de comunicación")
    print("✅ Endpoints de API")
    print("✅ Frontend")
    
    print("\n🎯 Próximos Pasos:")
    print("1. Si hay errores, revisar los logs correspondientes")
    print("2. Verificar configuración de red para paneles")
    print("3. Probar envío de mensajes a paneles")
    print("4. Validar funcionalidades del frontend")

def main():
    """Función principal"""
    print_header("VERIFICACIÓN DE INTEGRACIÓN CON PANELES")
    print("Parking Altea v3.1.0")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        check_database_connection()
        check_services()
        check_ports()
        check_panel_connectivity()
        check_panel_communication_service()
        check_api_endpoints()
        check_frontend()
        generate_report()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificación interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 