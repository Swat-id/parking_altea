#!/usr/bin/env python3
"""
Servicio de email para notificaciones de alarmas v3.2.0_alarms
Maneja el envío de notificaciones por email para alarmas del sistema
"""

import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de notificaciones por email"""
    
    def __init__(self):
        self.smtp_config = self._load_smtp_config()
        self.from_email = self.smtp_config.get('from_email', 'alarmas@parking-altea.com')
        self.from_name = self.smtp_config.get('from_name', 'Sistema de Alarmas Parking Altea')
    
    def _load_smtp_config(self) -> Dict[str, Any]:
        """Cargar configuración SMTP desde variables de entorno"""
        return {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', 'info@swat-id.com'),
            'password': os.getenv('SMTP_PASSWORD', 'pysn fxgf hxzl hevi'),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
            'from_email': os.getenv('SMTP_FROM_EMAIL', 'info@swat-id.com'),
            'from_name': os.getenv('SMTP_FROM_NAME', 'Sistema de Alarmas Parking Altea')
        }
    
    def send_alarm_notification(self, user_email: str, alarm_data: Dict[str, Any]) -> bool:
        """Enviar notificación de alarma por email"""
        try:
            subject = f"🚨 ALARMA {alarm_data['severity']} - {alarm_data['configuration_name']}"
            
            # Crear plantilla de email
            html_content = self._create_alarm_email_template(alarm_data)
            text_content = self._create_alarm_text_template(alarm_data)
            
            return self._send_email(user_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error enviando notificación de alarma: {e}")
            return False
    
    def send_alarm_resolution_notification(self, user_email: str, alarm_data: Dict[str, Any]) -> bool:
        """Enviar notificación de resolución de alarma por email"""
        try:
            subject = f"✅ ALARMA RESUELTA - {alarm_data['configuration_name']}"
            
            # Crear plantilla de email
            html_content = self._create_resolution_email_template(alarm_data)
            text_content = self._create_resolution_text_template(alarm_data)
            
            return self._send_email(user_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error enviando notificación de resolución: {e}")
            return False
    
    def _create_alarm_email_template(self, alarm_data: Dict[str, Any]) -> str:
        """Crear plantilla HTML para email de alarma"""
        severity_colors = {
            'LEVE': '#FFA500',    # Naranja
            'NORMAL': '#FF6B35',  # Naranja rojizo
            'GRAVE': '#FF0000'    # Rojo
        }
        
        severity_color = severity_colors.get(alarm_data['severity'], '#FF0000')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alarma del Sistema</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {severity_color};
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 8px 8px;
                }}
                .alarm-details {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid {severity_color};
                }}
                .severity-badge {{
                    display: inline-block;
                    background-color: {severity_color};
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                .timestamp {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 10px;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 ALARMA DEL SISTEMA</h1>
                <p>Sistema de Monitorización Parking Altea</p>
            </div>
            
            <div class="content">
                <h2>Se ha generado una nueva alarma</h2>
                
                <div class="alarm-details">
                    <h3>Detalles de la Alarma</h3>
                    <p><strong>Configuración:</strong> {alarm_data['configuration_name']}</p>
                    <p><strong>Severidad:</strong> <span class="severity-badge">{alarm_data['severity']}</span></p>
                    <p><strong>Mensaje:</strong> {alarm_data['message']}</p>
                    <p><strong>ID de Alarma:</strong> {alarm_data['alarm_id']}</p>
                    <div class="timestamp">
                        <strong>Fecha y Hora:</strong> {self._format_datetime(alarm_data['created_at'])}
                    </div>
                </div>
                
                <p><strong>Acciones Recomendadas:</strong></p>
                <ul>
                    <li>Verificar el estado del equipo afectado</li>
                    <li>Comprobar la conectividad de red</li>
                    <li>Revisar logs del sistema</li>
                    <li>Contactar con soporte técnico si es necesario</li>
                </ul>
                
                <p>Para más información, acceda al panel de administración del sistema.</p>
            </div>
            
            <div class="footer">
                <p>Este es un mensaje automático del Sistema de Alarmas Parking Altea v3.2.0</p>
                <p>No responda a este email. Para soporte técnico, contacte con el administrador del sistema.</p>
            </div>
        </body>
        </html>
        """
    
    def _create_alarm_text_template(self, alarm_data: Dict[str, Any]) -> str:
        """Crear plantilla de texto plano para email de alarma"""
        return f"""
ALARMA DEL SISTEMA - Parking Altea
==================================

Se ha generado una nueva alarma en el sistema de monitorización.

DETALLES DE LA ALARMA:
- Configuración: {alarm_data['configuration_name']}
- Severidad: {alarm_data['severity']}
- Mensaje: {alarm_data['message']}
- ID de Alarma: {alarm_data['alarm_id']}
- Fecha y Hora: {self._format_datetime(alarm_data['created_at'])}

ACCIONES RECOMENDADAS:
1. Verificar el estado del equipo afectado
2. Comprobar la conectividad de red
3. Revisar logs del sistema
4. Contactar con soporte técnico si es necesario

Para más información, acceda al panel de administración del sistema.

---
Este es un mensaje automático del Sistema de Alarmas Parking Altea v3.2.0
No responda a este email. Para soporte técnico, contacte con el administrador del sistema.
        """
    
    def _create_resolution_email_template(self, alarm_data: Dict[str, Any]) -> str:
        """Crear plantilla HTML para email de resolución de alarma"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alarma Resuelta</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #28a745;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 8px 8px;
                }}
                .resolution-details {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #28a745;
                }}
                .timestamp {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 10px;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ ALARMA RESUELTA</h1>
                <p>Sistema de Monitorización Parking Altea</p>
            </div>
            
            <div class="content">
                <h2>Se ha resuelto una alarma del sistema</h2>
                
                <div class="resolution-details">
                    <h3>Detalles de la Resolución</h3>
                    <p><strong>Configuración:</strong> {alarm_data['configuration_name']}</p>
                    <p><strong>Mensaje Original:</strong> {alarm_data['message']}</p>
                    <p><strong>ID de Alarma:</strong> {alarm_data['alarm_id']}</p>
                    <p><strong>Descripción de la Resolución:</strong> {alarm_data.get('resolution_description', 'No especificada')}</p>
                    <div class="timestamp">
                        <strong>Fecha y Hora de Resolución:</strong> {self._format_datetime(alarm_data.get('resolved_at', datetime.utcnow().isoformat()))}
                    </div>
                </div>
                
                <p>La alarma ha sido marcada como resuelta en el sistema.</p>
                <p>Gracias por su atención y rápida respuesta.</p>
            </div>
            
            <div class="footer">
                <p>Este es un mensaje automático del Sistema de Alarmas Parking Altea v3.2.0</p>
                <p>No responda a este email. Para soporte técnico, contacte con el administrador del sistema.</p>
            </div>
        </body>
        </html>
        """
    
    def _create_resolution_text_template(self, alarm_data: Dict[str, Any]) -> str:
        """Crear plantilla de texto plano para email de resolución de alarma"""
        return f"""
ALARMA RESUELTA - Parking Altea
===============================

Se ha resuelto una alarma del sistema de monitorización.

DETALLES DE LA RESOLUCIÓN:
- Configuración: {alarm_data['configuration_name']}
- Mensaje Original: {alarm_data['message']}
- ID de Alarma: {alarm_data['alarm_id']}
- Descripción de la Resolución: {alarm_data.get('resolution_description', 'No especificada')}
- Fecha y Hora de Resolución: {self._format_datetime(alarm_data.get('resolved_at', datetime.utcnow().isoformat()))}

La alarma ha sido marcada como resuelta en el sistema.
Gracias por su atención y rápida respuesta.

---
Este es un mensaje automático del Sistema de Alarmas Parking Altea v3.2.0
No responda a este email. Para soporte técnico, contacte con el administrador del sistema.
        """
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Enviar email usando la configuración SMTP de Gmail"""
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Reply-To'] = self.from_email
            
            # Adjuntar contenido
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Conectar al servidor SMTP de Gmail
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            
            # Configurar TLS (requerido para Gmail)
            server.starttls()
            
            # Autenticación con clave de aplicación
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            # Enviar email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado exitosamente a {to_email} desde {self.from_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP para {to_email}: {e}")
            logger.error("Verificar que la clave de aplicación sea correcta y esté habilitada en Gmail")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Destinatario rechazado {to_email}: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"Servidor SMTP desconectado: {e}")
            return False
        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {e}")
            return False
    
    def _format_datetime(self, datetime_str: str) -> str:
        """Formatear fecha y hora para mostrar en emails"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except Exception as e:
            logger.error(f"Error formateando fecha: {e}")
            return datetime_str
    
    def test_connection(self) -> bool:
        """Probar la conexión SMTP con Gmail"""
        try:
            # Conectar al servidor SMTP de Gmail
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            
            # Configurar TLS (requerido para Gmail)
            server.starttls()
            
            # Autenticación con clave de aplicación
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            server.quit()
            logger.info(f"Conexión SMTP con Gmail probada exitosamente para {self.from_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {e}")
            logger.error("Verificar que la clave de aplicación sea correcta y esté habilitada en Gmail")
            return False
        except Exception as e:
            logger.error(f"Error probando conexión SMTP: {e}")
            return False

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Probar el servicio
    email_service = EmailService()
    
    # Probar conexión
    if email_service.test_connection():
        print("✅ Conexión SMTP exitosa")
        
        # Probar envío de email de prueba
        test_alarm_data = {
            'alarm_id': 1,
            'severity': 'NORMAL',
            'message': 'Panel de prueba desconectado por 15 minutos',
            'configuration_name': 'Alarma de Prueba',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Usar un email real para la prueba
        test_email = input("Ingrese email de destino para la prueba (o presione Enter para usar info@swat-id.com): ").strip()
        if not test_email:
            test_email = 'info@swat-id.com'
        
        success = email_service.send_alarm_notification(test_email, test_alarm_data)
        if success:
            print(f"✅ Email de prueba enviado exitosamente a {test_email}")
        else:
            print("❌ Error enviando email de prueba")
    else:
        print("❌ Error en conexión SMTP") 