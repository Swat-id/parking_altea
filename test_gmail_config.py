#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de Gmail del sistema de alarmas
"""

import sys
import os
sys.path.append('.')

from src.email_service import EmailService
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_gmail_configuration():
    """Probar la configuración de Gmail"""
    print("🧪 Probando configuración de Gmail para sistema de alarmas...")
    print("=" * 60)
    
    try:
        # Crear instancia del servicio de email
        email_service = EmailService()
        
        print("📧 Configuración SMTP cargada:")
        print(f"   Host: {email_service.smtp_config['host']}")
        print(f"   Puerto: {email_service.smtp_config['port']}")
        print(f"   Usuario: {email_service.smtp_config['username']}")
        print(f"   TLS: {email_service.smtp_config['use_tls']}")
        print(f"   Desde: {email_service.from_email}")
        print()
        
        # Probar conexión
        print("🔗 Probando conexión SMTP...")
        if email_service.test_connection():
            print("✅ Conexión SMTP exitosa")
            print()
            
            # Preguntar email de destino
            test_email = input("📧 Ingrese email de destino para la prueba (o presione Enter para usar info@swat-id.com): ").strip()
            if not test_email:
                test_email = 'info@swat-id.com'
            
            print(f"📤 Enviando email de prueba a: {test_email}")
            
            # Datos de prueba
            test_alarm_data = {
                'alarm_id': 1,
                'severity': 'NORMAL',
                'message': 'Panel de prueba desconectado por 15 minutos',
                'configuration_name': 'Alarma de Prueba v3.2.0',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Enviar email de prueba
            success = email_service.send_alarm_notification(test_email, test_alarm_data)
            
            if success:
                print("✅ Email de prueba enviado exitosamente")
                print("📧 Verifique su bandeja de entrada (y carpeta de spam)")
            else:
                print("❌ Error enviando email de prueba")
                
        else:
            print("❌ Error en conexión SMTP")
            print()
            print("🔧 Solución de problemas:")
            print("1. Verificar que la verificación en dos pasos esté habilitada en Gmail")
            print("2. Generar una nueva clave de aplicación")
            print("3. Verificar que la clave no tenga espacios adicionales")
            print("4. Verificar conectividad a internet")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        print()
        print("🔧 Verificaciones adicionales:")
        print("1. Verificar que el archivo src/email_service.py existe")
        print("2. Verificar que las dependencias están instaladas")
        print("3. Verificar la configuración de la base de datos")

def show_instructions():
    """Mostrar instrucciones de configuración"""
    print()
    print("📋 Instrucciones de configuración de Gmail:")
    print("=" * 60)
    print("1. Ir a https://myaccount.google.com/security")
    print("2. Activar 'Verificación en 2 pasos'")
    print("3. Ir a https://myaccount.google.com/apppasswords")
    print("4. Seleccionar aplicación: 'Correo'")
    print("5. Seleccionar dispositivo: 'Windows'")
    print("6. Generar clave de aplicación (16 caracteres)")
    print("7. Copiar la clave y configurarla en el sistema")
    print()
    print("🔧 Configuración en el sistema:")
    print("- Editar src/email_service.py para cambiar valores por defecto")
    print("- O configurar variables de entorno:")
    print("  export SMTP_USERNAME=info@swat-id.com")
    print("  export SMTP_PASSWORD=pysn fxgf hxzl hevi")
    print()

if __name__ == "__main__":
    print("🚨 Sistema de Alarmas Parking Altea v3.2.0")
    print("📧 Prueba de configuración de Gmail")
    print()
    
    # Mostrar instrucciones
    show_instructions()
    
    # Preguntar si continuar
    response = input("¿Desea continuar con la prueba? (s/n): ").strip().lower()
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        test_gmail_configuration()
    else:
        print("❌ Prueba cancelada")
    
    print()
    print("✅ Script completado") 